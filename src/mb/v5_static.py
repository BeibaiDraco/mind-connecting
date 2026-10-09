"""Bounded, access-only STATIC feasibility and independently validated inference.

This is a new study. No v4 selector, result, or frozen setting is changed.
All scientific decisions are reconstructed from complete raw run ledgers.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from mb import analyze, ledger, readouts, tasks, v4
from mb.conditions import ArmConfig
from mb.model_profiles import resolve_profile

ROOT = Path(__file__).resolve().parents[2]
PROFILE = "llama31_8b_instruct"
PREFIX = "v5_llama_static_"
LAYERS = (16, 21, 27)
GAINS = (0.1, 0.3, 0.5, 0.7, 1.0)
SIZES = {"cal": 60, "match": 40, "validity": 80, "confirm": 600}
POST_NAMES = ("v5_static_match", "v5_static_validity", "v5_static_contrasts")
ACCESS_QIDS = v4.ACCESS_QIDS
FORMAL_QIDS = v4.FORMAL_QIDS


def arm(condition: str, layer: int = 21, gain: float = 0.0) -> dict:
    out = {"condition": condition, "layer": layer, "gain": gain, "form": "raw"}
    if condition in ("ONE", "CF"):
        out.update(interface="kv", kv_scope="P", gain=1.0)
    return out


def name(spec: Mapping[str, Any]) -> str:
    return ArmConfig(**dict(spec)).name


def roles(selected: Mapping[str, Any], include_cf: bool = False) -> dict:
    out = {"C0": name(arm("C0")), "K1": name(arm("ONE")),
           "STATIC": name(arm("STATIC", int(selected["layer"]), float(selected["gain"])))}
    if include_cf:
        out["CF"] = name(arm("CF"))
    return out


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def matched(target: Any, candidate: Any) -> bool:
    return bool(finite(target) and finite(candidate) and target > 0 and candidate > 0
                and abs(candidate - target) <= 0.25 * target + 1e-12)


def _decision(rows: list[dict], target: dict, count: int, n: int) -> dict:
    gain = target["acc_increment"]
    if not finite(gain) or gain <= 0:
        return {"gate": "stop", "matched": False, "selection": None, "next": None,
                "reason": "nonpositive or nonfinite fixed K1 access gain"}
    eligible = [r for r in rows if v4.engineering_eligible(r, n) and finite(r["acc_increment"])
                and r["acc_increment"] > 0]
    best = min(eligible, key=lambda r: (abs(r["acc_increment"] - gain), r["gain"],
                                       abs(r["layer"] - 21), r["layer"])) if eligible else None
    if best and matched(gain, best["acc_increment"]):
        return {"gate": "matched", "matched": True, "selection": best, "next": None, "reason": None}
    brackets = []
    if count < 2:
        for layer in LAYERS:
            tested = sorted((r for r in rows if r["layer"] == layer), key=lambda r: r["gain"])
            # Ineligible tested points stay in the sequence and break their enclosing bracket.
            for left, right in zip(tested, tested[1:]):
                if not all(v4.engineering_eligible(r, n) and finite(r["acc_increment"]) and r["acc_increment"] > 0
                           for r in (left, right)):
                    continue
                a, b = left["acc_increment"], right["acc_increment"]
                if not min(a, b) < gain < max(a, b):
                    continue
                mid = (left["gain"] + right["gain"]) / 2
                if any(r["gain"] == mid for r in tested):
                    continue
                key = (max(abs(a - gain), abs(b - gain)) / gain,
                       right["gain"] - left["gain"], abs(layer - 21), layer,
                       left["gain"], right["gain"])
                brackets.append((key, {"layer": layer, "gain": mid,
                                       "bracket": [left["gain"], right["gain"]]}))
    next_point = min(brackets, key=lambda item: item[0])[1] if brackets else None
    return {"gate": "refine" if next_point else "stop", "matched": False, "selection": None,
            "next": next_point, "reason": None if next_point else
            "two refinements exhausted" if count >= 2 else "no eligible bracket or matched candidate"}


def select(rows: Sequence[Mapping[str, Any]], available_layers: Sequence[int],
           refinements: Sequence[Mapping[str, Any]] = (), expected_n: int = 40) -> dict:
    """Replay the finite search; extra, missing, duplicated, or outcome-bearing inputs fail."""
    v4._selector_rows(rows)
    layers = tuple(sorted(available_layers))
    if not layers or len(set(layers)) != len(layers) or not set(layers) <= set(LAYERS):
        raise ValueError("invalid or unavailable STATIC layers")
    if len(refinements) > 2:
        raise ValueError("at most two refinements are allowed")
    by_name = {r["arm"]: dict(r) for r in rows}
    if len(by_name) != len(rows):
        raise ValueError("duplicate selector arms")
    required = [arm("C0"), arm("ONE"), *[arm("STATIC", l, g) for l in layers for g in GAINS]]
    required += [arm("STATIC", int(r["layer"]), float(r["gain"])) for r in refinements]
    if len({name(a) for a in required}) != len(required) or set(by_name) != {name(a) for a in required}:
        raise ValueError("selector requires exactly the complete prescribed grid and refinement history")
    for spec in required:
        row = by_name[name(spec)]
        for field in ("condition", "layer", "gain"):
            if row.get(field) != spec[field]:
                raise ValueError("selector arm metadata differs from the prescribed configuration")
        if row.get("n") != expected_n:
            raise ValueError("incomplete selector summaries")
        if row.get("interface", "residual") != spec.get("interface", "residual") or row.get("kv_scope") != spec.get("kv_scope"):
            raise ValueError("selector interface differs from the prescribed configuration")
    target = by_name[name(arm("ONE"))]
    tested = [by_name[name(arm("STATIC", l, g))] for l in layers for g in GAINS]
    decision = _decision(tested, target, 0, expected_n)
    for i, refinement in enumerate(refinements):
        point = decision["next"]
        if point is None or (refinement["layer"], refinement["gain"]) != (point["layer"], point["gain"]):
            raise ValueError("refinement does not follow the deterministic search; no runner-up or reselection")
        tested.append(by_name[name(arm("STATIC", int(point["layer"]), float(point["gain"])))] )
        decision = _decision(tested, target, i + 1, expected_n)
    return {**decision, "target": target, "available_layers": list(layers),
            "refinements": [{"layer": int(r["layer"]), "gain": float(r["gain"])} for r in refinements],
            "candidates": [{**r, "engineering_eligible": v4.engineering_eligible(r, expected_n)} for r in tested]}


def validity(records: Sequence[dict], selected: Mapping[str, Any], expected_n: int = 80,
             n_boot: int = 10_000) -> dict:
    """Four-arm independent validation; no ownership questions or means are accepted."""
    if any(r.get("qid") not in ACCESS_QIDS for r in records):
        raise ValueError("validity accepts only access/CAP/format records")
    rr = roles(selected, True)
    if {r["arm"] for r in records} != set(rr.values()):
        raise ValueError("validity needs exactly C0, K1, selected STATIC and CF-w1")
    out = v4.validity_summary(records, {**rr, "K*": rr["K1"]}, expected_n, n_boot)
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    c0 = scores[scores.arm == rr["C0"]]
    cap = float(c0.CAP_ACC.mean())
    mass = float(c0.LABEL_MASS.mean())
    base_ok = bool(len(c0) == expected_n and finite(cap) and cap >= 0.90 - 1e-12
                   and finite(mass) and mass >= 0.90 - 1e-12)
    k = v4._paired(scores, rr["K1"], rr["C0"], "ACC_RULE")
    s = v4._paired(scores, rr["STATIC"], rr["C0"], "ACC_RULE")
    uncertainty = {}
    if len(k) != expected_n or len(s) != expected_n:
        raise ValueError("incomplete paired validity access")
    for label, values in (("static_minus_0.75_kv", s - 0.75 * k),
                          ("1.25_kv_minus_static", 1.25 * k - s)):
        lo, hi = analyze.bootstrap_ci(values, n_boot=n_boot)
        uncertainty[label] = {"mean": float(values.mean()), "ci95_lo": lo, "ci95_hi": hi}
    passed = bool(base_ok and out["route_validated"] and out["engineering"]["CF"])
    return {"gate": "pass" if passed else "fail", "baseline": {"CAP_ACC": cap, "LABEL_MASS": mass, "pass": base_ok},
            "engineering": {key: out["engineering"][key] for key in rr},
            "K1_access": out["K1_access"], "content_K1": out["content_K1"],
            "matched": out["matched"], "match_gap": out["match_gap"],
            "access_table": out["access_table"], "paired_uncertainty": uncertainty,
            "equivalence_test": False}


def access_by_rule(records: Sequence[dict], split: str, n: int) -> dict:
    """Descriptive strata only; every rule remains in the pooled selector and analyses."""
    mapping = {ep.episode_id: ep.rule.B for ep in tasks.make_episodes(n, split, 0)}
    scores = readouts.score_records([r for r in records if r["qid"] in ACCESS_QIDS],
                                    readouts.ScoreOptions(rotations=None))
    scores["donor_rule"] = scores.episode_id.map(mapping)
    out = {}
    for (arm_name, rule), group in scores.groupby(["arm", "donor_rule"]):
        out.setdefault(str(arm_name), {})[str(rule)] = {
            "n_episodes": len(group), "ACC_RULE": float(group.ACC_RULE.mean()),
            "ACC_WORD": float(group.ACC_WORD.mean()), "CAP_ACC": float(group.CAP_ACC.mean()),
            "LABEL_MASS": float(group.LABEL_MASS.mean())}
    return out


def episode_fingerprints(suffix: str) -> list[str]:
    out = []
    for ep in tasks.make_episodes(SIZES[suffix], PREFIX + suffix, 0):
        obj = dataclasses.asdict(ep)
        for key in ("episode_id", "split", "index"):
            obj.pop(key)
        out.append(ledger.canonical_hash(obj, n=64))
    return out


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()


def pin(path: str | Path) -> dict:
    p = resolve(path)
    portable = p.relative_to(ROOT) if p.is_relative_to(ROOT) else p
    return {"path": str(portable), "sha256": ledger.file_sha256(p)}


def read_pin(value: Mapping[str, Any]) -> Path:
    if set(value) != {"path", "sha256"} or not isinstance(value["path"], str):
        raise ValueError("invalid source pin")
    p = resolve(value["path"])
    if not p.is_file() or ledger.file_sha256(p) != value["sha256"]:
        raise ValueError(f"tampered or missing source: {p.name}")
    return p


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _base_contract(cfg: Any, suffix: str, phase: str) -> None:
    split_suffix = "match" if phase.startswith("refine") else suffix
    if (cfg.model_profile != PROFILE or cfg.materials != "v1" or cfg.seed != 0
            or cfg.split != PREFIX + split_suffix or cfg.n_episodes != SIZES[split_suffix]
            or cfg.all_rotations_first != 0 or cfg.episodes_per_batch != 2 or cfg.max_rows != 16):
        raise ValueError("wrong split, size, model, materials, ordering, seed or batch contract")
    if cfg.stage != ("calibrate" if phase == "cal" else PREFIX + phase):
        raise ValueError("wrong stage identity")
    wanted = FORMAL_QIDS if phase == "confirm" else ACCESS_QIDS
    if list(cfg.qids) != list(wanted):
        raise ValueError("wrong or ownership-leaking readout set")
    params = cfg.params or {}
    if params.get("protocol") != "v5" or params.get("phase") != phase:
        raise ValueError("wrong protocol or phase")
    if params.get("episode_fingerprint") != ledger.canonical_hash(episode_fingerprints(split_suffix), n=64):
        raise ValueError("episode scientific fingerprints differ")
    expected_post = [] if phase == "cal" else [POST_NAMES[2] if phase == "confirm" else
                     POST_NAMES[1] if phase == "validity" else POST_NAMES[0]]
    if cfg.post != expected_post:
        raise ValueError("wrong post-processing contract")


def _identity_contract(identity: dict, cfg: Any, asset_sha: str) -> None:
    from mb.run import source_hash

    profile = resolve_profile(PROFILE)
    if (identity.get("stage_config") != json.loads(json.dumps(cfg.resolved()))
            or identity.get("model_profile") != profile.identity()
            or identity.get("model_revision") != profile.revision
            or identity.get("tokenizer_manifest_sha") != asset_sha
            or identity.get("cap_bank_hash") != tasks.cap_bank_hash()
            or identity.get("source_hash") != source_hash()
            or not all(isinstance(identity.get(k), str) and identity[k] for k in
                       ("source_hash", "template_hash", "prefix_hash"))):
        raise ValueError("run identity differs from the pinned model/config/materials")


def run_pins(run_dir: str | Path, output: str | None = None) -> dict:
    run = resolve(run_dir)
    paths = [run / p for p in ("identity.json", "manifest.json", "run_status.json")]
    if output:
        paths.extend([run / "arm_hashes.json", run / output, run / "notes.jsonl", *ledger.shard_paths(run)])
    else:
        paths.append(run / "calibration_metadata.json")
    return {p.name if p.parent == run else "records_" + p.name: pin(p) for p in paths}


def read_calibration(run_dir: str | Path, asset_sha: str) -> dict:
    """Verify the immutable multi-layer calibration without importing torch."""
    from mb.run import StageConfig

    run = resolve(run_dir)
    identity = _json(run / "identity.json")
    cfg = StageConfig(**identity["stage_config"])
    _base_contract(cfg, "cal", "cal")
    _identity_contract(identity, cfg, asset_sha)
    if (identity.get("limit") is not None or _json(run / "manifest.json").get("smoke", True)
            or _json(run / "run_status.json").get("status") != "complete"):
        raise ValueError("incomplete or smoke calibration")
    if cfg.arms or cfg.calibration is not None or cfg.calibration_layers != list(LAYERS):
        raise ValueError("calibration must passively record the three prescribed layers")
    metadata = _json(run / "calibration_metadata.json")
    if set(metadata) != {str(l) for l in LAYERS}:
        raise ValueError("calibration metadata must cover all three layers")
    available = []
    for layer in LAYERS:
        info = metadata[str(layer)]
        if any(info.get(k) != identity[k] for k in
               ("model_profile", "model_revision", "tokenizer_manifest_sha", "prefix_hash", "template_hash")):
            raise ValueError("calibration metadata has a foreign identity")
        if (info.get("split") != PREFIX + "cal" or info.get("n_episodes") != 60
                or info.get("smoke") is not False or resolve(info.get("run_dir", "")) != run
                or resolve(info.get("path", "")) != run / f"calibration_L{layer}.pt"
                or not isinstance(info.get("hash"), str) or not info["hash"]
                or info.get("hidden_size") != resolve_profile(PROFILE).hidden_size
                or not isinstance(info.get("static_unusable"), list)):
            raise ValueError("calibration metadata is incomplete or inconsistent")
        read_pin({"path": info["path"], "sha256": info["file_sha256"]})
        if not any(str(key).startswith("raw:") for key in info["static_unusable"]):
            available.append(layer)
    return {"run_dir": str(run), "identity": identity, "metadata": metadata,
            "available_layers": available, "pins": run_pins(run)}


def _notes(run: Path) -> dict:
    out = {}
    for line in (run / "notes.jsonl").read_text().splitlines():
        r = json.loads(line)
        if not isinstance(r.get("key"), str) or not isinstance(r.get("ids"), list):
            raise ValueError("invalid sealed note cache")
        if any(not isinstance(x, int) or x < 0 for x in r["ids"]) or r["key"] in out:
            raise ValueError("duplicate or invalid sealed note cache")
        out[r["key"]] = r["ids"]
    return out


def _checked_records(run: Path, cfg: Any, status: Mapping[str, Any]) -> tuple[list[dict], dict]:
    identity = _json(run / "identity.json")
    hashes = _json(run / "arm_hashes.json")
    expected_hashes = {a.name: a.config_hash(identity["calibration"][str(a.layer)]["hash"]
                        if a.needs_calibration else "none", "none", identity["template_hash"])
                       for a in cfg.arm_configs()}
    if hashes != expected_hashes:
        raise ValueError("registered arm hashes differ from the stored scientific identity")
    raw = ledger.load_records(run)
    for rec in raw.records:
        if rec.get("status") == "ok":
            logits = rec.get("label_logits")
            logprobs = rec.get("label_logprobs")
            if (not isinstance(logits, list) or len(logits) != 4 or not all(finite(x) for x in logits)
                    or not isinstance(logprobs, list) or len(logprobs) != 4
                    or not all(finite(x) for x in logprobs)
                    or not finite(rec.get("label_mass")) or not 0 <= rec["label_mass"] <= 1 + 1e-6):
                raise ValueError("nonfinite or malformed successful raw readout")
    records, out = v4._checked_records(run, cfg, status)
    all_records = raw
    by_arm = {a.name: a for a in cfg.arm_configs()}
    episodes = {ep.episode_id: ep for ep in tasks.make_episodes(cfg.n_episodes, cfg.split, cfg.seed)}
    expected = ledger.expected_trials([ledger.ArmSpec(a.name, a.recipients) for a in by_arm.values()],
        [(ep.episode_id, ep.rotations) for ep in tasks.make_episodes(cfg.n_episodes, cfg.split, cfg.seed)], cfg.qids, set())
    keys = set(expected)
    for r in all_records.records:
        if r.get("status") == "ok" and ledger.trial_key(r) not in keys:
            raise ValueError("unexpected successful record or ownership leakage")
    for r in records:
        a = by_arm[r["arm"]]
        for key in ("condition", "layer", "gain", "interface", "kv_scope"):
            if r.get(key, "residual" if key == "interface" else None) != getattr(a, key):
                raise ValueError("record arm metadata differs from the configured arm")
        ep = episodes[r["episode_id"]]
        text, options, meanings, cap_id = tasks._question_body(ep, "A", r["qid"], r["rotation_id"])
        expected_fields = {"split": cfg.split, "materials": "v1", "options": list(options),
                           "label_meaning": list(meanings), "cap_item_id": cap_id,
                           "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
                           "template_hash": identity["template_hash"], "model_revision": identity["model_revision"],
                           "readout_mode": a.readout_mode, "message_form": a.form,
                           "calibration_hash": identity["calibration"][str(a.layer)]["hash"] if a.needs_calibration else "none",
                           "mask_hash": "none"}
        if a.condition == "CF":
            expected_fields.update(cf_r0_rule=ep.rule.B, cf_r1_rule=ep.rule.spare,
                                   cf_r0_word=ep.word.B, cf_r1_word=ep.word.spare)
        if any(r.get(key) != value for key, value in expected_fields.items()):
            raise ValueError("raw question, physical content or identity differs from its deterministic episode")
    if out["truncated_tails"]:
        out["consumable"] = False
    return records, out


def _expected_arms(specs: list[dict], cfg: Any) -> None:
    wanted = [dataclasses.asdict(ArmConfig(**{**spec, "model_profile": PROFILE})) for spec in specs]
    actual = [dataclasses.asdict(a) for a in cfg.arm_configs()]
    if actual != wanted:
        raise ValueError("run arms differ from the deterministic frozen plan")


def _history(cfg: Any, assets: str, seen: set[Path]) -> list[dict]:
    params = cfg.params
    history = params.get("history", [])
    if not isinstance(history, list) or len(history) > 3:
        raise ValueError("invalid bounded search history")
    outputs = []
    for index, item in enumerate(history):
        if set(item) != {"run_dir", "output_source"}:
            raise ValueError("invalid history descriptor")
        expected_phase = "match" if index == 0 else f"refine{index}"
        output = read_completed(item["run_dir"], assets, seen=seen)
        source = read_pin(params["sources"][item["output_source"]])
        if _json(source) != output["output"] or output["phase"] != expected_phase:
            raise ValueError("history output differs from the complete raw source")
        if output["cfg"].params.get("history", []) != history[:index]:
            raise ValueError("history is not the exact prefix used for this refinement")
        if output["cfg"].params["calibration_run"] != params["calibration_run"]:
            raise ValueError("history uses a different calibration")
        for key, value in output["pins"].items():
            if params["sources"].get(f"history_{index}_{key}") != value:
                raise ValueError("raw history fingerprints are missing or changed")
        outputs.append(output)
    return outputs


def verify_config_contract(cfg: Any, *, seen: set[Path] | None = None) -> dict:
    """Public pre-launch/freeze audit; validate all consumed raw source runs, without writes."""
    seen = set() if seen is None else set(seen)
    params = cfg.params or {}
    phase = params.get("phase", "")
    suffix = "match" if phase.startswith("refine") else phase
    if phase not in ("cal", "match", "refine1", "refine2", "validity", "confirm"):
        raise ValueError("unknown STATIC phase")
    _base_contract(cfg, suffix, phase)
    sources = params.get("sources", {})
    for value in sources.values():
        read_pin(value)
    assets = params.get("model_assets", {})
    read_pin(assets)
    if assets["sha256"] != ledger.file_sha256(resolve_profile(PROFILE).manifest_path):
        raise ValueError("pinned assets differ from the selected profile manifest")
    if phase == "cal":
        if cfg.arms or cfg.calibration is not None or cfg.calibration_layers != list(LAYERS):
            raise ValueError("calibration must passively record the three prescribed layers")
        return {"phase": phase, "assets": assets}
    cal = read_calibration(params["calibration_run"], assets["sha256"])
    if not cal["available_layers"] or cfg.calibration_layers:
        raise ValueError("no usable layer or unexpected calibration recording in a scientific stage")
    if _json(read_pin(sources["calibration_metadata"])) != cal["metadata"]:
        raise ValueError("pinned calibration metadata differs from the original calibration")
    for key, value in cal["pins"].items():
        if sources.get("cal_" + key) != value:
            raise ValueError("calibration source fingerprints are missing or changed")
    for layer in LAYERS:
        if sources.get(f"calibration_L{layer}") != pin(cal["metadata"][str(layer)]["path"]):
            raise ValueError("calibration blob fingerprint missing or changed")
    history = _history(cfg, assets["sha256"], seen)
    if phase == "match":
        if history:
            raise ValueError("coarse selection cannot consume earlier search outcomes")
        specs = [arm("C0"), arm("ONE"), *[arm("STATIC", l, g) for l in cal["available_layers"] for g in GAINS]]
    elif phase.startswith("refine"):
        if len(history) != int(phase[-1]) or history[-1]["output"].get("gate") != "refine":
            raise ValueError("no authorized next midpoint in this exact history")
        point = history[-1]["output"]["next"]
        specs = [arm("STATIC", point["layer"], point["gain"])]
        if pin(read_pin(sources["reuse_notes"])) != pin(history[0]["run"] / "notes.jsonl"):
            raise ValueError("refinement must reuse the original match notes")
    else:
        if not history or history[-1]["output"].get("gate") != "matched":
            raise ValueError("a frozen matched selection is required; no runner-up")
        selected = history[-1]["output"]["selection"]
        if params.get("selected") != {key: selected[key] for key in ("layer", "gain", "arm")}:
            raise ValueError("selected setting differs from the complete frozen search")
        specs = [arm("C0"), arm("ONE"), arm("STATIC", selected["layer"], selected["gain"])]
        if phase == "validity":
            specs.append(arm("CF"))
        if params.get("roles") != roles(selected, phase == "validity"):
            raise ValueError("roles differ from the selected arms")
    _expected_arms(specs, cfg)
    used = {str(a["layer"]) for a in specs if a["condition"] == "STATIC"}
    expected_cal = {l: cal["metadata"][l]["path"] for l in sorted(used)}
    if {str(k): v for k, v in (cfg.calibration or {}).items()} != expected_cal:
        raise ValueError("calibration paths do not match the selected layers")
    if phase == "confirm":
        prior = params.get("validity", {})
        validated = read_completed(prior["run_dir"], assets["sha256"], seen=seen)
        if (_json(read_pin(sources[prior["output_source"]])) != validated["output"]
                or validated["phase"] != "validity" or validated["output"].get("gate") != "pass"
                or validated["cfg"].params["history"] != params["history"]
                or validated["cfg"].params["selected"] != params["selected"]):
            raise ValueError("independent validity did not pass for this frozen selection")
        for key, value in validated["pins"].items():
            if sources.get("validity_" + key) != value:
                raise ValueError("raw validity fingerprints are missing or changed")
    return {"phase": phase, "assets": assets, "calibration": cal, "history": history, "specs": specs}


def evaluate(run_dir: str | Path, cfg: Any, status: Mapping[str, Any], *, seen: set[Path] | None = None) -> dict:
    """No writes; called by both the runner and provenance-checking config generation."""
    run = resolve(run_dir)
    seen = set() if seen is None else set(seen)
    if run in seen:
        raise ValueError("cyclic stage provenance")
    seen.add(run)
    context = verify_config_contract(cfg, seen=seen)
    phase, assets = context["phase"], context["assets"]
    if phase == "cal":
        raise ValueError("calibration has no scientific post step")
    cal, history, specs = context["calibration"], context["history"], context["specs"]
    params = cfg.params
    identity = _json(run / "identity.json")
    _identity_contract(identity, cfg, assets["sha256"])
    for field in ("source_hash", "template_hash", "prefix_hash"):
        if identity[field] != cal["identity"][field]:
            raise ValueError(f"{field} changed since calibration")
    used = {str(a["layer"]) for a in specs if a["condition"] == "STATIC"}
    if set(identity.get("calibration", {})) != used:
        raise ValueError("identity has missing or extra calibration layers")
    for layer in used:
        info = cal["metadata"][layer]
        if identity["calibration"][layer] != {"path": info["path"], "hash": info["hash"],
                                              "smoke": False, "file_sha256": info["file_sha256"]}:
            raise ValueError("run used different calibration contents")
    records, out = _checked_records(run, cfg, status)
    out.update(step=cfg.post[0], phase=phase, split=cfg.split, n_episodes=cfg.n_episodes,
               episode_fingerprint=params["episode_fingerprint"])
    if not out["consumable"]:
        return {**out, "reason": "smoke, incomplete, nonfinite or truncated run: no scientific decision"}
    if phase in ("match", "refine1", "refine2"):
        previous = [r for h in history for r in h["records"]]
        if history and _notes(run) != _notes(history[0]["run"]):
            raise ValueError("refinement notes differ from the original match")
        combined = previous + records
        refinements = [{"layer": h["cfg"].arm_configs()[0].layer, "gain": h["cfg"].arm_configs()[0].gain}
                       for h in history[1:]]
        if phase.startswith("refine"):
            refinements.append({"layer": specs[0]["layer"], "gain": specs[0]["gain"]})
        table = v4.access_table(combined, SIZES["match"])
        out.update(select(table, cal["available_layers"], refinements))
        out["access_table"] = table
    elif phase == "validity":
        out.update(validity(records, params["selected"]))
        out["access_by_original_donor_rule"] = access_by_rule(records, cfg.split, cfg.n_episodes)
    else:
        out.update(formal_summary(records, params["selected"]))
        out["access_by_original_donor_rule"] = access_by_rule(records, cfg.split, cfg.n_episodes)
    return ledger.sanitize(out)


def read_completed(run_dir: str | Path, asset_sha: str, *, seen: set[Path] | None = None) -> dict:
    from mb.run import StageConfig

    run = resolve(run_dir)
    identity = _json(run / "identity.json")
    cfg = StageConfig(**identity["stage_config"])
    if identity.get("tokenizer_manifest_sha") != asset_sha:
        raise ValueError("source run uses different model assets")
    status = _json(run / "run_status.json")
    result = evaluate(run, cfg, status, seen=seen)
    if not result["consumable"]:
        raise ValueError("incomplete, nonfinite or smoke source run")
    path = run / f"{cfg.post[0]}.json"
    if _json(path) != result:
        raise ValueError("saved output does not reproduce from complete raw records")
    records = _checked_records(run, cfg, status)[0]
    return {"run": run, "cfg": cfg, "phase": cfg.params["phase"], "output": result,
            "records": records, "pins": run_pins(run, path.name)}


def formal_summary(records: Sequence[dict], selected: Mapping[str, Any], n_boot: int = 10_000) -> dict:
    rr = roles(selected)
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    families = {}
    for family, metrics in (("primary", ("M",)), ("secondary", ("M_NOW", "M_WORD"))):
        rows = []
        for metric in metrics:
            values = v4._paired(scores, rr["K1"], rr["STATIC"], metric)
            if len(values) != SIZES["confirm"]:
                raise ValueError("incomplete fixed-N formal contrast")
            t = analyze.paired_t(values)
            lo, hi = analyze.bootstrap_ci(values, n_boot=n_boot)
            rows.append({"arm1": rr["K1"], "arm2": rr["STATIC"], "metric": metric,
                         "n": t.n, "mean": t.mean, "sd": t.sd, "se": t.se,
                         "p_two_sided": t.p_two_sided, "ci95_lo": lo, "ci95_hi": hi})
        for row, p in zip(rows, analyze.holm([r["p_two_sided"] for r in rows])):
            row["p_holm"] = p
        families[family] = rows
    table = v4.access_table(records, SIZES["confirm"])
    by_arm = {r["arm"]: r for r in table}
    return {"families": families, "descriptive": v4.descriptive(records), "access_table": table,
            "formal_matched": matched(by_arm[rr["K1"]]["acc_increment"], by_arm[rr["STATIC"]]["acc_increment"]),
            "formal_engineering": {key: v4.engineering_eligible(by_arm[value], SIZES["confirm"]) for key, value in rr.items()},
            "equivalence_test": False}


def postprocess(run_dir: Path, cfg: Any, status: Mapping[str, Any]) -> dict:
    if status.get("post_step", cfg.post[0]) != cfg.post[0]:
        raise ValueError("post step differs from the stored config")
    result = evaluate(run_dir, cfg, status)
    path = Path(run_dir) / f"{cfg.post[0]}.json"
    path.write_text(json.dumps(ledger.sanitize(result), indent=2, allow_nan=False) + "\n")
    return result
