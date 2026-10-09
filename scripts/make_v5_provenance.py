"""Generate provenance stages; later stages require reproduced, complete gates.

No model is loaded. Existing configs are never replaced. GPU execution and its
separate budget remain outside this command.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

import yaml

from mb import ledger, run, tasks, v5_provenance as prov
from mb.conditions import ArmConfig
from mb.model_profiles import QWEN, LLAMA31, resolve_profile

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {"qwen": QWEN.key, "llama31": LLAMA31.key}
SIZES = {"smoke": 4, "base": 60, "validity": 80, "confirm": 600}
POSTS = {"base": "v5_provenance_baseline", "validity": "v5_provenance_validity",
         "confirm": "v5_provenance_contrasts"}


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def pin(path: Path) -> dict:
    return {"path": portable(path), "sha256": ledger.file_sha256(path)}


def write_once(path: Path, text: str) -> None:
    if path.exists():
        if path.read_text() != text:
            raise ValueError(f"refusing to replace {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as fh:
        fh.write(text)


def build_config(model: str, suffix: str, sources: dict | None = None) -> dict:
    profile = resolve_profile(PROFILES[model])
    profile.validate_manifest()
    if suffix not in SIZES:
        raise ValueError("unsupported provenance phase")
    prefix = f"v5_{model}_provenance_"
    layer = 21 if model == "llama31" else 24
    recipients = ["A", "B"] if suffix in ("base", "smoke") else ["A"]
    common = {"layer": layer, "recipients": recipients}
    c0 = {"condition": "C0", **common}
    c0_cf = {**c0, "donor_robin_conflict": True}
    kv = {"condition": "ONE", "interface": "kv", "kv_scope": "P", "gain": 1.0, **common}
    kv_cf = {**kv, "donor_robin_conflict": True}
    arms = [c0, c0_cf] if suffix == "base" else [c0, kv, kv_cf]
    if suffix == "smoke":
        arms.append(c0_cf)
    roles = {"C0": ArmConfig(**c0).name,
             "CONFLICT": ArmConfig(**(c0_cf if suffix == "base" else kv_cf)).name}
    if suffix != "base":
        roles["KV"] = ArmConfig(**kv).name
    qids = (prov.BASELINE_QIDS if suffix == "base" else
            prov.ACCESS_QIDS if suffix == "validity" else prov.FORMAL_QIDS)
    cfg = dict(stage=prefix + suffix, tag=prefix + suffix, split=prefix + suffix,
               n_episodes=SIZES[suffix], seed=0, model_profile=profile.key, materials="v1",
               arms=arms, qids=list(qids), episodes_per_batch=2, max_rows=16,
               calibration=None, calibration_layers=[],
               post=[] if suffix == "smoke" else [POSTS[suffix]],
               params={"protocol": "v5", "provenance_contract": "v5-provenance-v1",
                       "model_assets": pin(profile.manifest_path), "sources": sources or {},
                       "roles": roles, "smoke_only": suffix == "smoke"})
    run.StageConfig(**cfg)
    return cfg


def source_evidence(path: Path, model: str, suffix: str) -> dict:
    path = path.resolve()
    identity = json.loads((path / "identity.json").read_text())
    cfg = run.StageConfig(**identity["stage_config"])
    expected = build_config(model, suffix, (cfg.params or {}).get("sources", {}))
    # Runtime resolves defaults; compare semantic canonical configuration.
    if cfg.resolved() != run.StageConfig(**expected).resolved():
        raise ValueError("source run is not the exact prescribed provenance stage")
    if suffix == "validity":
        verify_config_contract(cfg)  # Revalidate its baseline rather than trusting pinned bytes alone.
    run.validate_stage_sources(cfg)
    status = run.run_completeness(path)
    status["post_step"] = POSTS[suffix]
    output = prov.postprocess(path, cfg, status)
    if not output.get("consumable") or output.get("gate") != "pass":
        raise ValueError("source gate is incomplete or failed; no next-stage config")
    sources = {}
    files = [path / n for n in ("identity.json", "manifest.json", "arm_hashes.json", "run_status.json")]
    files += sorted((path / "records").glob("attempt-*.jsonl"))
    files += [path / (POSTS[suffix] + ".json")]
    for i, file in enumerate(files):
        sources[f"{suffix}_{i:04d}"] = pin(file)
    return sources


def verify_config_contract(cfg: run.StageConfig) -> None:
    """Reproduce the stage and its prerequisite from pinned raw evidence."""
    model = next((name for name, profile in PROFILES.items() if profile == cfg.model_profile), None)
    if model is None:
        raise ValueError("unregistered provenance checkpoint")
    suffix = cfg.stage.removeprefix(f"v5_{model}_provenance_")
    sources = (cfg.params or {}).get("sources", {})
    if suffix in ("validity", "confirm"):
        prior = "base" if suffix == "validity" else "validity"
        identity_pin = sources.get(f"{prior}_0000", {})
        path = Path(identity_pin.get("path", ""))
        path = path if path.is_absolute() else ROOT / path
        if path.name != "identity.json":
            raise ValueError("missing prerequisite identity")
        if sources != source_evidence(path.parent, model, prior):
            raise ValueError("stage source set differs from reproduced prerequisite")
    elif sources:
        raise ValueError("initial provenance stages do not take prior study outcomes")
    if cfg.resolved() != run.StageConfig(**build_config(model, suffix, sources)).resolved():
        raise ValueError("configuration differs from the frozen provenance contract")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("initial", "validity", "confirm"))
    parser.add_argument("--model", choices=PROFILES, required=True)
    parser.add_argument("--source-run", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "configs" / "v5" / "provenance")
    args = parser.parse_args()
    sources = {}
    suffixes = ("smoke", "base") if args.phase == "initial" else (args.phase,)
    if args.phase == "initial" and args.source_run is not None:
        parser.error("initial stages must not consume previous outcomes")
    if args.phase != "initial":
        if args.source_run is None:
            parser.error("later stages require --source-run")
        sources = source_evidence(args.source_run, args.model,
                                  "base" if args.phase == "validity" else "validity")
    for suffix in suffixes:
        cfg = build_config(args.model, suffix, sources)
        path = args.out / f"{args.model}_{suffix}.yaml"
        write_once(path, yaml.safe_dump(cfg, sort_keys=False))
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
