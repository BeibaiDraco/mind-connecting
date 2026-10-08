"""Generate staged protocol-v4 configs without loading a model or inspecting M.

Initial files require verified pinned assets. Later phases consume completed
baseline/calibration/selection artifacts, copy their immutable snapshots into
the config directory, and pin their hashes. Generation does not freeze a plan
or authorize execution; use freeze_protocol.py before the relevant run phase.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from typing import Any

import yaml

from mb import ledger, tasks, v4
from mb.conditions import ArmConfig

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "llama31_8b_instruct"
PREFIX = "v4_llama31_"
SPLITS = {"smoke": 4, "base": 60, "cal": 60, "strength": 40, "match": 40, "validity": 80, "confirm": 600}


def _arm(condition: str, **kwargs: Any) -> dict:
    return {"condition": condition, "layer": 21, **kwargs}


def _kv(weight: float, condition: str = "ONE", mode: str = "FULL") -> dict:
    return _arm(condition, interface="kv", kv_scope="P", gain=float(weight), readout_mode=mode)


def _name(spec: dict) -> str:
    return ArmConfig(**spec).name


def _config(suffix: str, arms: list[dict], assets: dict, sources: dict,
            post: str | None = None, roles: dict | None = None, calibration: str | None = None) -> dict:
    return {"stage": "calibrate" if suffix == "cal" else PREFIX + suffix,
            "tag": "v4_" + suffix, "split": PREFIX + suffix, "n_episodes": SPLITS[suffix], "seed": 0,
            "model_profile": PROFILE, "arms": arms,
            "qids": list(v4.FORMAL_QIDS if suffix in ("base", "confirm", "smoke") else v4.ACCESS_QIDS),
            "episodes_per_batch": 2, "max_rows": 16,
            "calibration": {21: calibration} if calibration else None,
            "calibration_layers": [21] if suffix == "cal" else [], "post": [post] if post else [],
            "params": {"protocol": "v4", "model_assets": assets, "sources": sources,
                       "roles": roles or {}, "smoke_only": suffix == "smoke"}}


def formal_arms(weight: float, static_gain: float | None) -> tuple[list[dict], dict]:
    if weight not in v4.KV_GRID or (static_gain is not None and static_gain not in v4.STATIC_GRID):
        raise ValueError("selected setting is outside the prespecified grid")
    specs = {"C0": _arm("C0"), "K1": _kv(1), "K*": _kv(weight), "RF": _kv(weight, mode="RF"),
             "CF": _kv(weight, "CF"), "TAG": _arm("LANG_TAG"), "UNTAG": _arm("LANG_UNTAG")}
    if static_gain is not None:
        specs["STATIC"] = _arm("STATIC", gain=float(static_gain), form="raw")
    roles = {role: _name(spec) for role, spec in specs.items()}
    roles.setdefault("STATIC", None)
    unique = {_name(spec): spec for spec in specs.values()}
    return list(unique.values()), roles


def build_configs(phase: str, assets: dict, sources: dict | None = None, *,
                  baseline: dict | None = None, calibration: str | None = None,
                  calibration_metadata: dict | None = None, strength: dict | None = None,
                  match: dict | None = None, validity: dict | None = None) -> dict[str, dict]:
    """Pure construction; the CLI validates provenance before calling this."""
    sources = sources or {}
    if phase == "initial":
        smoke_arms, smoke_roles = formal_arms(1, None)
        return {
            "smoke": _config("smoke", smoke_arms, assets, sources, roles=smoke_roles),
            "base": _config("base", [_arm("C0", recipients=["A", "B"])], assets, sources, "v4_baseline"),
            "cal": _config("cal", [], assets, sources),
            "strength": _config("strength", [_arm("C0"), *[_kv(w) for w in v4.KV_GRID]],
                                assets, sources, "v4_strength"),
        }
    if not baseline or not baseline.get("consumable") or baseline.get("gate") != "pass":
        raise ValueError("a completed passing side-specific baseline is required")
    if not strength or not strength.get("consumable") or strength.get("gate") != "pass":
        raise ValueError("a completed passing access-only strength selection is required")
    if not calibration_metadata:
        raise ValueError("completed new-model calibration metadata is required")
    info = calibration_metadata.get("21")
    if not info:
        raise ValueError("missing layer-21 calibration metadata")
    unusable = info.get("static_unusable")
    if unusable is None:
        raise ValueError("calibration metadata must report unusable directions")
    static_available = not any(str(key).startswith("raw:") for key in unusable)
    if phase == "match":
        if not static_available:
            raise ValueError("raw STATIC direction unavailable: record unavailable branch, do not run matching")
        if not calibration:
            raise ValueError("a pinned calibration file path is required for STATIC")
        arms = [_arm("C0"), _kv(1), *[_arm("STATIC", gain=g, form="raw") for g in v4.STATIC_GRID]]
        return {"match": _config("match", arms, assets, sources, "v4_match", {"K1": _name(_kv(1))}, calibration)}
    selected = strength.get("selection")
    if not selected:
        raise ValueError("strength output has no selected setting")
    static_gain = None
    if static_available:
        if not match or not match.get("consumable"):
            raise ValueError("consume the completed STATIC match even if no point is eligible")
        if match.get("selection"):
            static_gain = float(match["selection"]["gain"])
            if not calibration:
                raise ValueError("selected STATIC requires the calibration path")
    arms, roles = formal_arms(float(selected["gain"]), static_gain)
    if phase == "validity":
        cf1 = _kv(1, "CF")
        roles["CF1"] = _name(cf1)
        if roles["CF1"] not in {_name(spec) for spec in arms}:
            arms.append(cf1)
        return {"validity": _config("validity", arms, assets, sources, "v4_validity", roles,
                                    calibration if static_gain is not None else None)}
    if phase != "confirm":
        raise ValueError(f"unknown phase {phase}")
    if not validity or not validity.get("consumable") or validity.get("core_gate") != "pass":
        raise ValueError("independent rule-content and engineering validity must pass")
    cfg = _config("confirm", arms, assets, sources, "v4_contrasts", roles,
                  calibration if static_gain is not None else None)
    cfg["params"]["route_validated"] = bool(validity.get("route_validated", False))
    cfg["params"]["static_unavailable_reason"] = ("raw direction unavailable" if not static_available else
                                                    "no eligible point" if static_gain is None else None)
    return {"confirm": cfg}


def split_manifest(existing_configs: Path | None = None) -> dict:
    """Compare semantic episode fingerprints, not just split-prefixed IDs."""
    def fingerprint(ep: tasks.Episode) -> str:
        obj = dataclasses.asdict(ep)
        for field in ("episode_id", "split", "index"):
            obj.pop(field)
        return ledger.canonical_hash(obj, n=64)

    old = {}
    if existing_configs is not None:
        for path in sorted(existing_configs.rglob("*.yaml")):
            if "v4" in path.relative_to(existing_configs).parts:
                continue
            cfg = yaml.safe_load(path.read_text())
            if isinstance(cfg, dict) and "split" in cfg and "n_episodes" in cfg:
                key = (cfg["split"], cfg.get("seed", 0))
                old[key] = max(old.get(key, 0), int(cfg["n_episodes"]))
    seen = {fingerprint(ep): f"prior:{split}" for (split, seed), n in old.items()
            for ep in tasks.make_episodes(n, split, seed)}
    out = {}
    for suffix, n in SPLITS.items():
        split = PREFIX + suffix
        episodes = tasks.make_episodes(n, split, 0)
        fingerprints = [fingerprint(ep) for ep in episodes]
        for value in fingerprints:
            if value in seen:
                raise ValueError(f"episode overlap: {split} and {seen[value]}")
            seen[value] = split
        out[split] = {"n": n, "seed": 0, "episode_ids": [ep.episode_id for ep in episodes],
                      "fingerprints": fingerprints}
    return {"protocol": "v4", "profile": PROFILE, "prior_splits_checked": len(old), "splits": out}


def _read_completed(path: Path, expected_step: str | None, assets_sha: str | None = None) -> dict:
    doc = json.loads(path.read_text())
    run = path.parent
    identity_path = run / "identity.json"
    identity = json.loads(identity_path.read_text())
    manifest = json.loads((run / "manifest.json").read_text())
    status = json.loads((run / "run_status.json").read_text())
    if manifest.get("smoke", True) or identity.get("limit") is not None or status.get("status") != "complete":
        raise ValueError(f"{run}: incomplete or smoke source")
    if identity["stage_config"].get("model_profile") != PROFILE:
        raise ValueError("source artifact belongs to another model profile")
    if identity["stage_config"].get("materials") != "v1":
        raise ValueError("v4 source artifact must use the original v1 materials")
    if assets_sha is not None and identity.get("tokenizer_manifest_sha") != assets_sha:
        raise ValueError("source artifact uses different model assets")
    if expected_step is not None:
        if not doc.get("consumable") or doc.get("step") != expected_step:
            raise ValueError(f"{path}: wrong or nonconsumable post output")
        if doc.get("identity_sha256") != ledger.file_sha256(identity_path):
            raise ValueError("post output identity changed")
        from mb.run import StageConfig

        cfg = StageConfig(**identity["stage_config"])
        records, checked = v4._checked_records(run, cfg, status)
        suffix = {"v4_baseline": "base", "v4_strength": "strength", "v4_match": "match", "v4_validity": "validity"}[expected_step]
        if not checked["consumable"] or cfg.split != PREFIX + suffix or cfg.n_episodes != SPLITS[suffix]:
            raise ValueError("source artifact fails current completeness or prescribed stage identity")
        wanted_qids = v4.FORMAL_QIDS if suffix == "base" else v4.ACCESS_QIDS
        if cfg.seed != 0 or set(cfg.qids) != set(wanted_qids):
            raise ValueError("source artifact has different readouts or seed")
        names = {a.name for a in cfg.arm_configs()}
        if suffix == "base":
            expected = {_name(_arm("C0"))}
            recomputed = v4.baseline_gate(records, cfg.n_episodes)
            keys = ("gate", "sides")
        elif suffix == "strength":
            expected = {_name(_arm("C0")), *[_name(_kv(w)) for w in v4.KV_GRID]}
            recomputed = v4.select_strength(v4.access_table(records, cfg.n_episodes), cfg.n_episodes)
            keys = ("gate", "selection")
        elif suffix == "match":
            expected = {_name(_arm("C0")), _name(_kv(1)), *[_name(_arm("STATIC", gain=g)) for g in v4.STATIC_GRID]}
            recomputed = v4.select_static(v4.access_table(records, cfg.n_episodes), _name(_kv(1)), cfg.n_episodes)
            keys = ("selection", "matched", "available")
        else:
            expected = names
            recomputed = v4.validity_summary(records, cfg.params["roles"], cfg.n_episodes)
            keys = ("core_gate", "route_validated")
        if names != expected or any(doc.get(k) != ledger.sanitize(recomputed[k]) for k in keys):
            raise ValueError("source output does not reproduce from the prescribed arm grid and raw records")
        wanted_recipients = ("A", "B") if suffix == "base" else ("A",)
        if any(a.recipients != wanted_recipients for a in cfg.arm_configs()):
            raise ValueError("source has the wrong measured recipients")
    else:
        cfg = identity["stage_config"]
        if cfg.get("stage") != "calibrate" or cfg.get("split") != PREFIX + "cal" or cfg.get("n_episodes") != 60:
            raise ValueError("calibration must use the fresh 60-episode v4 calibration split")
    return doc


def _write_once(path: Path, text: str) -> None:
    if path.exists():
        if path.read_text() != text:
            raise ValueError(f"refusing to overwrite {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as fh:
        fh.write(text)


def _portable(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=("initial", "match", "validity", "confirm"))
    ap.add_argument("--out", type=Path, default=ROOT / "configs" / "v4")
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--calibration-metadata", type=Path)
    ap.add_argument("--calibration", help="exact calibration .pt path on the execution host; never 'latest'")
    ap.add_argument("--strength", type=Path)
    ap.add_argument("--match", type=Path)
    ap.add_argument("--validity", type=Path)
    args = ap.parse_args()
    from mb.model_profiles import resolve_profile

    profile = resolve_profile(PROFILE)
    profile.validate_manifest()
    manifest_path = ROOT / "materials" / f"tokenizer_{PROFILE}_manifest.json"
    assets = {"path": _portable(manifest_path), "sha256": ledger.file_sha256(manifest_path)}
    docs, pins, copies = {}, {}, {}
    for name, step in (("baseline", "v4_baseline"), ("strength", "v4_strength"), ("match", "v4_match"),
                       ("validity", "v4_validity"), ("calibration_metadata", None)):
        path = getattr(args, name)
        if path is not None:
            docs[name] = _read_completed(path, step, assets["sha256"])
            destination = args.out / "artifacts" / f"{name}.json"
            copies[destination] = path.read_text()
            pins[name] = {"path": _portable(destination), "sha256": ledger.file_sha256(path)}
    if args.calibration == "latest":
        raise ValueError("v4 requires an explicitly pinned new-model calibration")
    calmeta = docs.get("calibration_metadata", {}).get("21")
    if calmeta is not None:
        if (calmeta.get("smoke", True) or calmeta.get("split") != PREFIX + "cal"
                or calmeta.get("n_episodes") != 60 or calmeta.get("model_revision") != profile.revision
                or calmeta.get("tokenizer_manifest_sha") != assets["sha256"]):
            raise ValueError("calibration metadata differs from the approved new-model calibration")
        if args.calibration and str(Path(args.calibration)) != str(Path(calmeta["path"])):
            raise ValueError("--calibration must name the exact file in calibration_metadata")
    # Independent validity must have used these exact frozen selection snapshots.
    if args.validity:
        identity = json.loads((args.validity.parent / "identity.json").read_text())
        consumed = (identity["stage_config"].get("params") or {}).get("sources", {})
        for name in ("baseline", "strength", "match", "calibration_metadata"):
            if name in pins and consumed.get(name, {}).get("sha256") != pins[name]["sha256"]:
                raise ValueError(f"validity used a different {name} artifact")
    configs = build_configs(args.phase, assets, pins, calibration=args.calibration, **docs)
    if args.validity:
        # Matching source hashes alone does not certify that they were used in the run.
        expected = build_configs("validity", assets, pins, calibration=args.calibration, **docs)["validity"]
        actual = identity["stage_config"]
        if ((actual.get("params") or {}).get("roles") != expected["params"]["roles"]
                or {_name(a) for a in actual["arms"]} != {_name(a) for a in expected["arms"]}
                or json.dumps(actual.get("calibration"), sort_keys=True) != json.dumps(expected["calibration"], sort_keys=True)):
            raise ValueError("validity ran different roles, arms or calibration from the frozen selection")
    splits = split_manifest(ROOT / "configs")
    for path, text in copies.items():
        _write_once(path, text)
    _write_once(args.out / "split_manifest.json", json.dumps(splits, indent=2) + "\n")
    for suffix, cfg in configs.items():
        path = args.out / f"v4_{suffix}.yaml"
        _write_once(path, "# Generated by scripts/make_v4_configs.py; verify the applicable v4 freeze before running.\n"
                    + yaml.safe_dump(cfg, sort_keys=False))
        print(f"wrote {path}: {cfg['n_episodes']} episodes, {len(cfg['arms'])} unique arms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
