"""Generate the new bounded STATIC stages from independently audited source runs.

No model is loaded. Generating configs does not freeze them or authorize a paid run.
Each source run must be available at its recorded execution-host path.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from typing import Any

import yaml

from mb import ledger, tasks, v5_static as study
from mb.model_profiles import resolve_profile

ROOT = study.ROOT


def split_manifest(existing_configs: Path | None = None) -> dict:
    """Reject scientific episode reuse, excluding ID/split/index from the fingerprint."""
    prior = {}
    if existing_configs is not None:
        for path in sorted(existing_configs.rglob("*.yaml")):
            cfg = yaml.safe_load(path.read_text())
            if not isinstance(cfg, dict) or "split" not in cfg or "n_episodes" not in cfg:
                continue
            if str(cfg["split"]).startswith(study.PREFIX):
                continue
            key = (cfg["split"], cfg.get("seed", 0))
            prior[key] = max(prior.get(key, 0), int(cfg["n_episodes"]))
    seen = {}
    for (split, seed), n in prior.items():
        for ep in tasks.make_episodes(n, split, seed):
            obj = dataclasses.asdict(ep)
            for key in ("episode_id", "split", "index"):
                obj.pop(key)
            seen[ledger.canonical_hash(obj, n=64)] = split
    splits = {}
    for suffix, n in study.SIZES.items():
        values = study.episode_fingerprints(suffix)
        for value in values:
            if value in seen:
                raise ValueError(f"scientific episode overlap: {suffix} and {seen[value]}")
            seen[value] = study.PREFIX + suffix
        splits[study.PREFIX + suffix] = {"n": n, "seed": 0, "fingerprints": values}
    return {"protocol": "v5", "profile": study.PROFILE,
            "prior_splits_checked": len(prior), "splits": splits}


def config(phase: str, assets: dict, sources: dict, *, calibration: dict | None = None,
           history: list[dict] | None = None, selected: dict | None = None,
           validity: dict | None = None, next_point: dict | None = None) -> dict:
    """Pure construction; source acceptance belongs to the audited CLI path below."""
    suffix = "match" if phase.startswith("refine") else phase
    if phase not in ("cal", "match", "refine1", "refine2", "validity", "confirm"):
        raise ValueError("unknown STATIC phase")
    arms, cal_paths, rr = [], None, {}
    if phase != "cal":
        if not calibration or not calibration["available_layers"]:
            raise ValueError("no calibrated available layer: STATIC branch unavailable")
        if phase == "match":
            arms = [study.arm("C0"), study.arm("ONE"),
                    *[study.arm("STATIC", l, g) for l in calibration["available_layers"] for g in study.GAINS]]
        elif phase.startswith("refine"):
            if not next_point or len(history or []) != int(phase[-1]):
                raise ValueError("a deterministic next midpoint and exact history are required")
            arms = [study.arm("STATIC", next_point["layer"], next_point["gain"])]
        else:
            if not selected or not history:
                raise ValueError("a frozen matched selection is required")
            arms = [study.arm("C0"), study.arm("ONE"),
                    study.arm("STATIC", selected["layer"], selected["gain"])]
            if phase == "validity":
                arms.append(study.arm("CF"))
            rr = study.roles(selected, phase == "validity")
            if phase == "confirm" and not validity:
                raise ValueError("independent passing validity is required before formal generation")
        cal_paths = {a["layer"]: calibration["metadata"][str(a["layer"])]["path"]
                     for a in arms if a["condition"] == "STATIC"}
    params = {"protocol": "v5", "phase": phase, "model_assets": assets, "sources": sources,
              "episode_fingerprint": ledger.canonical_hash(study.episode_fingerprints(suffix), n=64)}
    if phase != "cal":
        params.update(calibration_run=calibration["run_dir"], history=history or [], roles=rr)
    if selected is not None:
        params["selected"] = {key: selected[key] for key in ("layer", "gain", "arm")}
    if validity is not None:
        params["validity"] = validity
    post = [] if phase == "cal" else [study.POST_NAMES[2] if phase == "confirm" else
             study.POST_NAMES[1] if phase == "validity" else study.POST_NAMES[0]]
    return {"stage": "calibrate" if phase == "cal" else study.PREFIX + phase,
            "tag": "v5_static_" + phase, "split": study.PREFIX + suffix,
            "n_episodes": study.SIZES[suffix], "seed": 0, "model_profile": study.PROFILE,
            "materials": "v1", "arms": arms,
            "qids": list(study.FORMAL_QIDS if phase == "confirm" else study.ACCESS_QIDS),
            "all_rotations_first": 0, "episodes_per_batch": 2, "max_rows": 16,
            "calibration": cal_paths, "calibration_layers": list(study.LAYERS) if phase == "cal" else [],
            "post": post, "params": params}


def prepare(phase: str, assets: dict, *, calibration_run: Path | None = None,
            match_run: Path | None = None, refine_runs: list[Path] | None = None,
            validity_run: Path | None = None) -> tuple[str | None, dict | None, dict]:
    """Audit all predecessors before producing any config or authorizing the next branch."""
    study.read_pin(assets)
    if phase == "initial":
        if any((calibration_run, match_run, refine_runs, validity_run)):
            raise ValueError("initial calibration must not consume selection outcomes")
        return "cal", config("cal", assets, {}), {"decision": "calibrate"}
    if calibration_run is None:
        raise ValueError("completed multilayer calibration is required")
    cal = study.read_calibration(calibration_run, assets["sha256"])
    sources = {"cal_" + key: value for key, value in cal["pins"].items()}
    sources["calibration_metadata"] = study.pin(Path(cal["run_dir"]) / "calibration_metadata.json")
    for layer in study.LAYERS:
        sources[f"calibration_L{layer}"] = study.pin(cal["metadata"][str(layer)]["path"])
    if not cal["available_layers"]:
        return None, None, {"decision": "stop", "reason": "all three raw calibration layers unavailable"}
    if phase == "match":
        if any((match_run, refine_runs, validity_run)):
            raise ValueError("coarse matching cannot consume previous selection or validity")
        return "match", config("match", assets, sources, calibration=cal), {"decision": "coarse_selection"}
    if phase not in ("next", "confirm") or match_run is None:
        raise ValueError("next/confirm requires the complete coarse match")
    if len(refine_runs or []) > 2:
        raise ValueError("at most two completed refinement runs")
    history, outputs = [], []
    for i, path in enumerate([match_run, *(refine_runs or [])]):
        doc = study.read_completed(path, assets["sha256"])
        if doc["phase"] != ("match" if i == 0 else f"refine{i}"):
            raise ValueError("wrong phase or order in search history")
        if (doc["cfg"].params["history"] != history
                or doc["cfg"].params["calibration_run"] != cal["run_dir"]):
            raise ValueError("source uses a different calibration or refinement history")
        for key, value in doc["pins"].items():
            sources[f"history_{i}_{key}"] = value
        source_key = f"history_{i}_{doc['cfg'].post[0]}.json"
        history.append({"run_dir": str(doc["run"]), "output_source": source_key})
        outputs.append(doc)
    last = outputs[-1]["output"]
    decision = {"decision": last["gate"], "reason": last["reason"],
                "selection": last["selection"], "next": last["next"], "history": history}
    if phase == "next":
        if validity_run:
            raise ValueError("no reselection after independent validation")
        if last["gate"] == "stop":
            return None, None, decision
        if last["gate"] == "refine":
            suffix = f"refine{len(history)}"
            sources["reuse_notes"] = study.pin(outputs[0]["run"] / "notes.jsonl")
            return suffix, config(suffix, assets, sources, calibration=cal, history=history,
                                  next_point=last["next"]), decision
        return "validity", config("validity", assets, sources, calibration=cal, history=history,
                                  selected=last["selection"]), decision
    if last["gate"] != "matched" or validity_run is None:
        raise ValueError("formal study requires a matched search and independently passing validation")
    validated = study.read_completed(validity_run, assets["sha256"])
    selected = {key: last["selection"][key] for key in ("layer", "gain", "arm")}
    if (validated["phase"] != "validity" or validated["output"].get("gate") != "pass"
            or validated["cfg"].params["history"] != history
            or validated["cfg"].params["calibration_run"] != cal["run_dir"]
            or validated["cfg"].params["selected"] != selected):
        raise ValueError("validity failed or used different frozen selection; no runner-up")
    for key, value in validated["pins"].items():
        sources["validity_" + key] = value
    descriptor = {"run_dir": str(validated["run"]), "output_source": "validity_v5_static_validity.json"}
    return "confirm", config("confirm", assets, sources, calibration=cal, history=history,
                              selected=last["selection"], validity=descriptor), decision


def write_once(path: Path, contents: str) -> None:
    if path.exists():
        if path.read_text() != contents:
            raise ValueError(f"refusing to overwrite existing artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        handle.write(contents)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=("initial", "match", "next", "confirm"))
    ap.add_argument("--out", type=Path, default=ROOT / "configs" / "v5" / "static")
    ap.add_argument("--calibration-run", type=Path)
    ap.add_argument("--match-run", type=Path)
    ap.add_argument("--refine-run", type=Path, action="append", default=[])
    ap.add_argument("--validity-run", type=Path)
    args = ap.parse_args()
    profile = resolve_profile(study.PROFILE)
    profile.validate_manifest()
    assets = study.pin(profile.manifest_path)
    suffix, cfg, decision = prepare(args.phase, assets, calibration_run=args.calibration_run,
                                   match_run=args.match_run, refine_runs=args.refine_run,
                                   validity_run=args.validity_run)
    if cfg is not None:
        from mb.run import StageConfig

        study.verify_config_contract(StageConfig(**cfg))
    splits = split_manifest(ROOT / "configs")
    # All validation precedes the first write. Existing generation artifacts are immutable.
    files = {args.out / "split_manifest.json": json.dumps(splits, indent=2) + "\n"}
    label = suffix or "stop_after_" + str(len(args.refine_run)) + "_refinements"
    files[args.out / f"decision_{label}.json"] = json.dumps(decision, indent=2, allow_nan=False) + "\n"
    if cfg is not None:
        files[args.out / f"v5_static_{suffix}.yaml"] = (
            "# Generated by make_v5_static.py; freeze the approved phase before execution.\n"
            + yaml.safe_dump(cfg, sort_keys=False))
    for path, text in files.items():
        if path.exists() and path.read_text() != text:
            raise ValueError(f"refusing to overwrite existing artifact: {path}")
    for path, text in files.items():
        write_once(path, text)
    print(json.dumps({"decision": decision["decision"], "next_config":
                      str(args.out / f"v5_static_{suffix}.yaml") if suffix else None,
                      "paid_execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
