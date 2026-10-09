"""Audit a real four-episode provenance smoke and optionally a no-op resume."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from mb import chat, ledger, run, provenance_tasks as p, tasks, v4
from make_v5_provenance import build_config, PROFILES


def audit(root: Path, before: dict | None = None) -> dict:
    identity = json.loads((root / "identity.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    status = json.loads((root / "run_status.json").read_text())
    cfg = run.StageConfig(**identity["stage_config"])
    model = next((key for key, value in PROFILES.items() if value == cfg.model_profile), None)
    if model is None or cfg.resolved() != run.StageConfig(**build_config(model, "smoke")).resolved():
        raise ValueError("not the prescribed provenance smoke")
    if identity["limit"] != 4 or manifest.get("smoke") is not True or status.get("status") != "complete":
        raise ValueError("smoke must be explicitly limited, complete, and nonconsumable")
    tok = chat.load_tokenizer(profile=cfg.model_profile)
    expected_identity = run.build_identity(cfg, 4, run.template_hash(tok, provenance=True, profile=cfg.model_profile),
                                          {}, prefix=run.prefix_hash(tok, profile=cfg.model_profile))
    if identity != expected_identity:
        raise ValueError("smoke does not reproduce current pinned source/assets/serialization")
    records, checked = v4._checked_records(root, cfg, status)
    expected_keys = set(run.stage_expected(cfg, 4))
    if any(ledger.trial_key(r) not in expected_keys for r in ledger.load_records(root).records):
        raise ValueError("smoke contains unexpected trial records")
    if checked["completeness"]["status"] != "complete" or checked["invalid_records"] or checked["truncated_tails"]:
        raise ValueError("smoke raw ledger is incomplete or malformed")
    expected_hashes = {a.name: a.config_hash("none", "none", identity["template_hash"]) for a in cfg.arm_configs()}
    if json.loads((root / "arm_hashes.json").read_text()) != expected_hashes:
        raise ValueError("arm hashes differ")
    episodes = {ep.episode_id: ep for ep in tasks.make_episodes(4, cfg.split, 0)}
    arms = {arm.name: arm for arm in cfg.arm_configs()}
    snapshots, episode_snapshots = {}, {}
    for rec in records:
        ep, arm = episodes[rec["episode_id"]], arms[rec["arm"]]
        question = p.render_question(tok, ep, rec["recipient"], rec["qid"], rec["rotation_id"], arm.donor_robin_conflict)
        if (rec["provenance"] != p.record_metadata(ep, rec["recipient"], question, arm.donor_robin_conflict)
                or rec["text_hash"] != question.text_hash or rec["options"] != list(question.options)):
            raise ValueError("smoke records disagree with original-card truth or fixed question")
        key, sha = rec.get("c48_snapshot_key"), rec.get("c48_snapshot_sha256")
        if not key or not sha or snapshots.setdefault(key, sha) != sha:
            raise ValueError("readout branch snapshot identity is absent or inconsistent")
        episode_key = (rec["episode_id"], rec["arm"])
        if episode_snapshots.setdefault(episode_key, (key, sha)) != (key, sha):
            raise ValueError("one episode/arm did not reuse one C48 across every readout")
        values = rec.get("label_logprobs", [])
        if len(values) != 4 or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in values):
            raise ValueError("smoke has missing or non-finite label log probabilities")
    notes = {}
    for line in (root / "notes.jsonl").read_text().splitlines():
        item = json.loads(line)
        if notes.setdefault(item["key"], item["ids"]) != item["ids"]:
            raise ValueError("one private card has conflicting note tokens")
    required_notes = {tasks.note_key(ep, "A") for ep in episodes.values()}
    required_notes |= {tasks.note_key(ep, "B") for ep in episodes.values()}
    required_notes |= {tasks.note_key(p.donor_episode(ep), "B") for ep in episodes.values()}
    if set(notes) != required_notes:
        raise ValueError("original and conflict donor note identities are incomplete")
    shards = {path.name: {"sha256": ledger.file_sha256(path), "bytes": path.stat().st_size}
              for path in sorted((root / "records").glob("attempt-*.jsonl"))}
    output = {"passed": True, "model_profile": cfg.model_profile, "source_hash": run.source_hash(),
              "identity_sha256": ledger.file_sha256(root / "identity.json"), "n_records": len(records),
              "snapshots": snapshots, "shards": shards, "note_keys": len(notes),
              "immutable_sha256": {name: ledger.file_sha256(root / name) for name in
                  ("config.yaml", "identity.json", "manifest.json", "arm_hashes.json", "notes.jsonl", "snapshots.jsonl")},
              "resume_verified": False, "scientific_gate": False}
    if before is not None:
        for field in ("model_profile", "source_hash", "identity_sha256", "n_records", "snapshots", "note_keys", "immutable_sha256"):
            if before.get(field) != output[field]:
                raise ValueError(f"no-op resume changed {field}")
        if not all(shards.get(k) == v for k, v in before["shards"].items()):
            raise ValueError("resume changed a prior immutable shard")
        new = set(shards) - set(before["shards"])
        if not new or any(shards[k]["bytes"] != 0 for k in new):
            raise ValueError("completed resume must write only an empty new shard")
        output["resume_verified"] = True
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run_dir, json.loads(args.before.read_text()) if args.before else None)
    with args.output.open("x") as fh:
        json.dump(result, fh, indent=2, allow_nan=False)
        fh.write("\n")
    print(json.dumps({"passed": True, "resume_verified": result["resume_verified"],
                      "n_records": result["n_records"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
