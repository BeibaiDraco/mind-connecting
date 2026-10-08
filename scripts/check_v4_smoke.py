#!/usr/bin/env python3
"""Torch-free audit of the four-episode/six-arm Llama correctness smoke.

    python scripts/check_v4_smoke.py RUN_DIR --output AUDIT.json
    python scripts/check_v4_smoke.py RUN_DIR --capture-resume BEFORE.json
    # Run the completed-run resume separately, then sync its files:
    python scripts/check_v4_smoke.py RUN_DIR --before-resume BEFORE.json --output AFTER.json

Only identities, completeness, finite readouts and resource measurements are
reported. No attribution/claiming scores or research gate is computed. Optional
--runtime-metadata JSON must identify purpose='v4_smoke' and identity_sha256, then
may provide measured elapsed_seconds/peak_allocated_bytes/peak_reserved_bytes.
Missing measurements remain unavailable; an acceptance-test peak is not a smoke peak.
All output files are created exclusively; prior evidence is never overwritten.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime as dt
import json
import math
from pathlib import Path
import re
from typing import Any

from mb import ledger, run, v4
from mb.conditions import ArmConfig
from mb.model_profiles import LLAMA31


class AuditError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AuditError(message)


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def expected_arms() -> list[ArmConfig]:
    common = {"layer": 21, "model_profile": LLAMA31.key}
    return [ArmConfig("C0", **common),
            ArmConfig("ONE", interface="kv", kv_scope="P", gain=1.0, **common),
            ArmConfig("ONE", interface="kv", kv_scope="P", gain=1.0, readout_mode="RF", **common),
            ArmConfig("CF", interface="kv", kv_scope="P", gain=1.0, **common),
            ArmConfig("LANG_TAG", **common), ArmConfig("LANG_UNTAG", **common)]


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def valid_readout(record: dict) -> bool:
    logits, logprobs, mass = (record.get(k) for k in ("label_logits", "label_logprobs", "label_mass"))
    if not all(isinstance(values, list) and len(values) == 4 and all(map(numeric, values))
               for values in (logits, logprobs)):
        return False
    if "r_kv_mass_mean" in record and not (numeric(record["r_kv_mass_mean"])
                                           and 0 <= record["r_kv_mass_mean"] <= 1 + 1e-6):
        return False
    if "r_inj_ratio_mean" in record and not numeric(record["r_inj_ratio_mean"]):
        return False
    return bool(numeric(mass) and 0 <= mass <= 1 + 1e-6 and all(p <= 1e-6 for p in logprobs)
                and math.isclose(sum(math.exp(p) for p in logprobs), mass, rel_tol=1e-5, abs_tol=1e-7))


def ledger_snapshot(root: Path) -> dict:
    loaded = ledger.load_records(root)
    hashes = read(root / "arm_hashes.json")
    identity = read(root / "identity.json")
    keys = sorted(ledger.done_keys(loaded.records, hashes))
    sidecars = [root / name for name in ("notes.jsonl", "lang.jsonl", "snapshots.jsonl", "ticks.jsonl")]
    sidecars += list((root / "ticks").glob("**/*"))
    return {"version": 1, "identity_sha256": ledger.file_sha256(root / "identity.json"),
            "source_hash": identity.get("source_hash"), "raw_record_count": len(loaded.records),
            "successful_record_count": sum(r.get("status") == "ok" for r in loaded.records),
            "successful_unique_count": len(keys), "successful_keys_sha256": ledger.canonical_hash(keys, 64),
            "records_sha256": ledger.canonical_hash(loaded.records, 64),
            "immutable_files": {name: ledger.file_sha256(root / name)
                                for name in ("identity.json", "manifest.json", "config.yaml", "arm_hashes.json")},
            "scientific_sidecars": {str(p.relative_to(root)): ledger.file_sha256(p)
                                    for p in sorted(sidecars) if p.is_file()},
            "shards": {p.name: {"bytes": p.stat().st_size, "sha256": ledger.file_sha256(p)}
                       for p in ledger.shard_paths(root)},
            "truncated_tails": loaded.truncated_tails,
            "finished_before_resume": read(root / "run_status.json").get("finished"),
            "resume_log_lines": len((root / "resume_log.jsonl").read_text().splitlines())
                                if (root / "resume_log.jsonl").exists() else 0}


def compare_resume(root: Path, before: dict) -> dict:
    after = ledger_snapshot(root)
    fields = ("identity_sha256", "source_hash", "raw_record_count", "successful_record_count",
              "successful_unique_count", "successful_keys_sha256", "records_sha256", "immutable_files",
              "scientific_sidecars")
    differences = [field for field in fields if before.get(field) != after[field]]
    require(before.get("version") == 1 and before.get("audit_passed") is True,
            "before-resume snapshot must come from a passing smoke audit")
    require(not differences, "completed-run resume changed ledger or identity: " + ", ".join(differences))
    require(not after["truncated_tails"], "resume left a truncated record shard")
    require(after["resume_log_lines"] > before.get("resume_log_lines", -1), "no completed-run resume was recorded")
    require(all(after["shards"].get(name) == value for name, value in before["shards"].items()),
            "resume changed an existing immutable record shard")
    new = set(after["shards"]) - set(before["shards"])
    require(all(after["shards"][name]["bytes"] == 0 for name in new), "completed-run resume wrote new records")
    require(bool(new), "resume did not create its expected empty attempt shard")
    return {"passed": True, "new_records": 0, "new_successful_records": 0,
            "new_empty_shards": sorted(new), "immutable_identity_unchanged": True}


def timings(root: Path, manifest: dict, finished: str | None) -> dict:
    pattern = re.compile(r"^\[[^]]+\] pass (\d+) \[(.+)\] chunk (\d+): (\d+) episodes in ([0-9.]+)s$")
    arms: dict[str, dict] = defaultdict(lambda: {"logged_seconds": 0.0, "chunk_entries": 0,
                                                "max_chunk_seconds": 0.0,
                                                "episode_visits": 0, "passes": set()})
    resumed, ignored = False, 0
    path = root / "log.txt"
    for line in path.read_text().splitlines() if path.exists() else []:
        if re.match(r"^\[[^]]+\] resumed ", line):
            resumed = True
        match = pattern.match(line)
        if match:
            if resumed:
                ignored += 1
                continue
            attempt, arm, chunk, count, seconds = match.groups()
            item = arms[arm]
            item["logged_seconds"] += float(seconds)
            item["max_chunk_seconds"] = max(item["max_chunk_seconds"], float(seconds))
            item["chunk_entries"] += 1
            item["episode_visits"] += int(count)
            item["passes"].add(int(attempt))
    wall = None
    try:
        seconds = (dt.datetime.fromisoformat(finished) - dt.datetime.fromisoformat(manifest["started"])).total_seconds()
        if seconds >= 0:
            wall = seconds
    except (KeyError, TypeError, ValueError):
        pass
    return {"source": "runner log.txt pass/chunk durations; manifest/run_status timestamps",
            "per_arm": {name: dict(value, passes=sorted(value["passes"])) for name, value in sorted(arms.items())},
            "per_arm_available": bool(arms), "recorded_wall_span_seconds": wall,
            "all_six_arms_logged": set(arms) == {arm.name for arm in expected_arms()},
            "missing_arm_timings": sorted({arm.name for arm in expected_arms()} - set(arms)),
            "wall_span_available": wall is not None, "resume_chunk_entries_excluded": ignored,
            "note": "Durations are rounded to 0.1 s; shared C48 and first-use note costs follow execution order. "
                    "Chunk counts must be checked before projection. Missing entries are unavailable, not zero. "
                    "The six-arm smoke omits STATIC."}


def audit(root: Path, *, asset_manifest: Path | None = None, tokenizer_dir: Path | None = None,
          before_resume: dict | None = None, runtime_metadata: dict | None = None) -> dict:
    root = Path(root)
    manifest_path = asset_manifest or LLAMA31.manifest_path
    LLAMA31.validate_manifest(manifest_path, tokenizer_dir)
    assets_sha = ledger.file_sha256(manifest_path)
    identity, manifest, status = (read(root / name) for name in ("identity.json", "manifest.json", "run_status.json"))
    cfg = run.StageConfig(**identity["stage_config"])
    require(cfg.stage == cfg.split == "v4_llama31_smoke" and cfg.n_episodes == 4 and cfg.seed == 0
            and cfg.materials == "v1" and cfg.model_profile == LLAMA31.key and cfg.all_rotations_first == 0,
            "wrong smoke stage/split/model/materials/count/seed")
    require(identity.get("limit") == 4 and manifest.get("smoke") is True and status.get("status") == "complete",
            "smoke is not a completed explicitly limited four-episode run")
    require(cfg.calibration is None and not cfg.calibration_layers and not cfg.post
            and (cfg.params or {}).get("smoke_only") is True, "smoke config contains research calibration/postprocessing")
    require(len(cfg.qids) == 10 and set(cfg.qids) == set(v4.FORMAL_QIDS), "wrong smoke readouts")
    wanted = expected_arms()
    require(set(cfg.arm_configs()) == set(wanted) and len(cfg.arm_configs()) == 6,
            "smoke must contain exactly the six fixed w1 arms")
    # Identity preserves JSON number types even when equivalent arm values compare equal.
    expected_hashes = {arm.name: arm.config_hash("none", "none", identity["template_hash"])
                       for arm in cfg.arm_configs()}
    require(read(root / "arm_hashes.json") == expected_hashes, "arm identities do not reproduce")
    require(identity.get("model_profile") == LLAMA31.identity() and identity.get("model_revision") == LLAMA31.revision,
            "wrong checkpoint identity")
    require(identity.get("tokenizer_manifest_sha") == assets_sha
            and (cfg.params or {}).get("model_assets", {}).get("sha256") == assets_sha, "model assets differ")
    for field in ("model_profile", "tokenizer_manifest_sha", "template_hash", "prefix_hash"):
        require(manifest.get(field) == identity.get(field), f"manifest identity mismatch: {field}")
    tokenizer = run.chat.load_tokenizer(tokenizer_dir, profile=LLAMA31, manifest_path=manifest_path)
    require(identity["template_hash"] == run.template_hash(tokenizer, cfg.materials, LLAMA31)
            and identity["prefix_hash"] == run.prefix_hash(tokenizer, cfg.materials, LLAMA31),
            "stored template/prefix hashes do not reproduce from the verified tokenizer")
    rebuilt = run.build_identity(cfg, 4, identity["template_hash"], {}, prefix=identity["prefix_hash"])
    require(identity == rebuilt, "run identity/source differs from the audited checkout")
    input_cfg = run.StageConfig.load(root / "config.yaml")
    require(json.loads(json.dumps(input_cfg.resolved())) == identity["stage_config"], "saved input config differs from identity")
    env = manifest.get("env", {})
    require(env.get("torch") == "2.6.0+cu124" and env.get("transformers") == "4.57.1"
            and env.get("tokenizers") == "0.22.1" and env.get("cuda") == "12.4"
            and str(env.get("python", "")).startswith("3.12."), "recorded runtime differs from pinned versions")
    loaded = ledger.load_records(root)
    require(not loaded.truncated_tails, "smoke has truncated record shards")
    expected = run.stage_expected(cfg, 4)
    expected_set = set(expected)
    require(len(expected) == len(expected_set) == 480, "wrong expected smoke trial count")
    require(all(ledger.trial_key(r) in expected_set and r.get("config_hash") == expected_hashes.get(r["arm"])
                for r in loaded.records), "unexpected trial key or record identity")
    successful = [r for r in loaded.records if r.get("status") == "ok"]
    require(len(successful) == 480 and {ledger.trial_key(r) for r in successful} == expected_set,
            "smoke successful records are missing or duplicated")
    require(all(valid_readout(r) for r in successful), "non-finite or inconsistent label logits/probabilities")
    require(all(r.get("model_revision") == LLAMA31.revision and r.get("template_hash") == identity["template_hash"]
                for r in successful), "successful record model/template identity differs")
    recomputed = ledger.completeness(loaded.records, expected, expected_hashes)
    stored = read(root / "completeness.json")
    require(all(stored.get(k) == recomputed[k] for k in ("status", "n_expected", "n_ok", "n_missing")),
            "stored completeness does not reproduce")
    by_episode = defaultdict(dict)
    for rec in successful:
        state_id = (rec.get("c48_snapshot_key"), rec.get("c48_snapshot_sha256"))
        require(all(isinstance(v, str) and v for v in state_id), "missing C48 snapshot provenance")
        previous = by_episode[rec["episode_id"]].setdefault(rec["arm"], state_id)
        require(previous == state_id, "readout branches have inconsistent C48 provenance")
    full, rf = wanted[1].name, wanted[2].name
    require(all(states[full] == states[rf] for states in by_episode.values()), "FULL/RF did not share C48")
    snapshot = ledger_snapshot(root)
    result = {"passed": True, "purpose": "engineering smoke only; no attribution summaries",
              "consumable_research_data": False, "identity_sha256": snapshot["identity_sha256"],
              "source_hash": identity["source_hash"], "tokenizer_manifest_sha256": assets_sha,
              "episodes": 4, "unique_arms": 6, "successful_readouts": 480,
              "raw_record_count": len(loaded.records), "failed_attempt_records": len(loaded.records) - 480,
              "successful_by_arm": dict(sorted(Counter(r["arm"] for r in successful).items())),
              "finite_readouts": True, "shared_full_rf_c48": True,
              "resume": compare_resume(root, before_resume) if before_resume is not None else {"checked": False},
              "resources": {"available": False, "reason": "mb.run does not record peak GPU memory"}}
    finished = before_resume.get("finished_before_resume") if before_resume else status.get("finished")
    result["timing"] = timings(root, manifest, finished)
    if before_resume is None and snapshot["resume_log_lines"]:
        result["timing"]["note"] += " Wall span includes resume/idle gaps because no before-resume snapshot was supplied."
    if runtime_metadata is not None:
        require(runtime_metadata.get("purpose") == "v4_smoke"
                and runtime_metadata.get("identity_sha256") == snapshot["identity_sha256"],
                "runtime measurements do not identify this smoke run")
        measured = {k: runtime_metadata.get(k) for k in ("elapsed_seconds", "peak_allocated_bytes", "peak_reserved_bytes")}
        require(all(v is None or numeric(v) and v >= 0 for v in measured.values()), "invalid runtime measurements")
        result["resources"] = {"available": any(v is not None for v in measured.values()),
                               "source": "caller-supplied measurements tied to this identity", **measured}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--tokenizer-dir", type=Path)
    parser.add_argument("--before-resume", type=Path)
    parser.add_argument("--runtime-metadata", type=Path)
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--capture-resume", type=Path)
    destination.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(args.run_dir, asset_manifest=args.asset_manifest, tokenizer_dir=args.tokenizer_dir,
                       before_resume=read(args.before_resume) if args.before_resume else None,
                       runtime_metadata=read(args.runtime_metadata) if args.runtime_metadata else None)
        if args.capture_resume:
            result = {**ledger_snapshot(args.run_dir), "audit_passed": True}
        target = args.capture_resume or args.output
        if target:
            with target.open("x") as output:
                output.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc), "error_type": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
