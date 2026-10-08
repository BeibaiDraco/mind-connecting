"""Synthetic ledgers exercise smoke auditing without model, torch, or network."""

from dataclasses import asdict
import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest
import yaml

from mb import model_profiles


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_v4_smoke.py"
spec = importlib.util.spec_from_file_location("smoke_audit_test", SCRIPT)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)
generator_spec = importlib.util.spec_from_file_location("smoke_generator_test", SCRIPT.with_name("make_v4_configs.py"))
generator = importlib.util.module_from_spec(generator_spec)
generator_spec.loader.exec_module(generator)


def save(root, name, data):
    (root / name).write_text(json.dumps(data))


def records(root):
    return [json.loads(line) for line in (root / "records/attempt-000.jsonl").read_text().splitlines()]


def save_records(root, rows):
    (root / "records/attempt-000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))


@pytest.fixture
def complete(tmp_path, monkeypatch):
    # Asset integrity has its own real-asset tests; this fixture has no model assets.
    assets = tmp_path / "synthetic-assets"
    (assets / "materials").mkdir(parents=True)
    monkeypatch.setattr(model_profiles, "REPO_ROOT", assets)
    monkeypatch.setattr(model_profiles.ModelProfile, "validate_manifest", lambda *a, **k: {})
    monkeypatch.setattr(smoke.run.chat, "load_tokenizer", lambda *a, **k: object())
    monkeypatch.setattr(smoke.run, "template_hash", lambda *a, **k: "template")
    monkeypatch.setattr(smoke.run, "prefix_hash", lambda *a, **k: "prefix")
    smoke.LLAMA31.manifest_path.write_text('{"synthetic":true}')
    root = tmp_path / "run"
    (root / "records").mkdir(parents=True)
    generated = generator.build_configs("initial", {
        "path": str(smoke.LLAMA31.manifest_path),
        "sha256": smoke.ledger.file_sha256(smoke.LLAMA31.manifest_path)})["smoke"]
    # Use the actual generator/YAML path so numeric identity differences cannot hide
    # behind a fixture built from the auditor's own expected_arms implementation.
    cfg = smoke.run.StageConfig(**yaml.safe_load(yaml.safe_dump(generated)))
    arms = cfg.arm_configs()
    identity = smoke.run.build_identity(cfg, 4, "template", {}, prefix="prefix")
    save(root, "identity.json", identity)
    (root / "config.yaml").write_text(yaml.safe_dump(asdict(cfg)))
    save(root, "manifest.json", {"smoke": True, "started": "2026-10-08T12:00:00",
                               **{key: identity[key] for key in ("model_profile", "tokenizer_manifest_sha",
                                                               "template_hash", "prefix_hash")},
                               "env": {"python": "3.12.12", "torch": "2.6.0+cu124",
                                       "transformers": "4.57.1", "tokenizers": "0.22.1", "cuda": "12.4"}})
    save(root, "run_status.json", {"status": "complete", "finished": "2026-10-08T12:00:10"})
    hashes = {arm.name: arm.config_hash("none", "none", "template") for arm in arms}
    save(root, "arm_hashes.json", hashes)
    expected = smoke.run.stage_expected(cfg, 4)
    rows = []
    for episode, arm, recipient, qid, rotation in expected:
        family = "shared" if arm in (arms[1].name, arms[2].name) else arm
        rows.append({"episode_id": episode, "arm": arm, "recipient": recipient, "qid": qid,
                     "rotation_id": rotation, "config_hash": hashes[arm], "status": "ok",
                     "label_logits": [0., 0., 0., 0.], "label_logprobs": [-math.log(8)] * 4,
                     "label_mass": .5, "model_revision": smoke.LLAMA31.revision,
                     "template_hash": "template", "c48_snapshot_key": f"{episode}:{family}",
                     "c48_snapshot_sha256": f"{episode}:{family}:checksum"})
    save_records(root, rows)
    save(root, "completeness.json", smoke.ledger.completeness(rows, expected, hashes))
    (root / "log.txt").write_text("".join(
        f"[12:00:00] pass 0 [{arm.name}] chunk {chunk}: 2 episodes in 1.2s\n"
        for arm in arms for chunk in range(2)))
    return root


def test_exact_complete_smoke_reports_counts_and_only_measured_resources(complete):
    result = smoke.audit(complete)
    assert result["successful_readouts"] == 480
    assert result["episodes"] == 4 and result["unique_arms"] == 6
    assert set(result["successful_by_arm"].values()) == {80}
    assert result["consumable_research_data"] is False
    assert result["resources"]["available"] is False
    assert result["timing"]["recorded_wall_span_seconds"] == 10
    assert result["timing"]["all_six_arms_logged"] is True
    assert all(v["logged_seconds"] == pytest.approx(2.4) for v in result["timing"]["per_arm"].values())
    assert all(v["max_chunk_seconds"] == pytest.approx(1.2) for v in result["timing"]["per_arm"].values())


@pytest.mark.parametrize("damage", ["missing", "duplicate", "infinite", "nan", "mass", "kv_mass", "checkpoint", "c48"])
def test_corrupt_or_incomplete_smoke_cannot_pass(complete, damage):
    rows = records(complete)
    if damage == "missing":
        rows.pop()
    elif damage == "duplicate":
        rows.append(dict(rows[0]))
    elif damage in ("infinite", "nan"):
        rows[0]["label_logits"][0] = float("inf" if damage == "infinite" else "nan")
    elif damage == "mass":
        rows[0]["label_mass"] = .7
    elif damage == "kv_mass":
        rows[0]["r_kv_mass_mean"] = float("nan")
    elif damage == "checkpoint":
        rows[0]["model_revision"] = "other"
    else:
        rf = smoke.expected_arms()[2].name
        for row in rows:
            if row["arm"] == rf:
                row["c48_snapshot_sha256"] = "different"
    save_records(complete, rows)
    with pytest.raises(smoke.AuditError):
        smoke.audit(complete)


def test_consistent_but_wrong_template_identity_is_rejected(complete, monkeypatch):
    monkeypatch.setattr(smoke.run, "template_hash", lambda *a, **k: "actual-template-differs")
    with pytest.raises(smoke.AuditError, match="verified tokenizer"):
        smoke.audit(complete)


def test_failed_attempts_are_retained_but_do_not_replace_successes(complete):
    rows = records(complete)
    rows.insert(0, dict(rows[0], status="failed", label_logits=None, label_logprobs=None, label_mass=None))
    save_records(complete, rows)
    result = smoke.audit(complete)
    assert result["failed_attempt_records"] == 1 and result["raw_record_count"] == 481


def resume(root):
    (root / "records/attempt-001.jsonl").touch()
    (root / "resume_log.jsonl").write_text('{"allow_code_change":false}\n')
    save(root, "run_status.json", {"status": "complete", "finished": "2026-10-08T13:00:10"})
    with (root / "log.txt").open("a") as output:
        output.write("[13:00:00] resumed v4_llama31_smoke run fixture (smoke=True)\n")
        output.write(f"[13:00:00] pass 0 [{smoke.expected_arms()[0].name}] chunk 0: 2 episodes in 0.0s\n")


def test_completed_resume_is_noop_and_excluded_from_throughput(complete):
    smoke.audit(complete)
    before = dict(smoke.ledger_snapshot(complete), audit_passed=True)
    resume(complete)
    result = smoke.audit(complete, before_resume=before)
    assert result["resume"]["new_records"] == 0
    assert result["resume"]["new_empty_shards"] == ["attempt-001.jsonl"]
    assert result["timing"]["recorded_wall_span_seconds"] == 10
    assert result["timing"]["resume_chunk_entries_excluded"] == 1


@pytest.mark.parametrize("damage", ["record", "identity", "shard", "sidecar"])
def test_completed_resume_rejects_new_records_or_mutation(complete, damage):
    before = dict(smoke.ledger_snapshot(complete), audit_passed=True)
    resume(complete)
    if damage == "record":
        extra = dict(records(complete)[0], status="failed")
        (complete / "records/attempt-001.jsonl").write_text(json.dumps(extra) + "\n")
    elif damage == "identity":
        identity = smoke.read(complete / "identity.json")
        identity["source_hash"] = "changed"
        save(complete, "identity.json", identity)
    elif damage == "sidecar":
        (complete / "notes.jsonl").write_text('{"new_note":true}\n')
    else:
        with (complete / "records/attempt-000.jsonl").open("a") as output:
            output.write("\n")
    with pytest.raises(smoke.AuditError):
        smoke.compare_resume(complete, before)


def test_resource_metadata_requires_this_run_and_missing_logs_are_unavailable(complete):
    (complete / "log.txt").unlink()
    result = smoke.audit(complete)
    assert result["timing"]["per_arm_available"] is False and result["timing"]["per_arm"] == {}
    assert result["timing"]["all_six_arms_logged"] is False and len(result["timing"]["missing_arm_timings"]) == 6
    metadata = {"purpose": "v4_smoke", "identity_sha256": result["identity_sha256"],
                "elapsed_seconds": 10.5, "peak_allocated_bytes": 12_000}
    assert smoke.audit(complete, runtime_metadata=metadata)["resources"]["peak_allocated_bytes"] == 12_000
    metadata["identity_sha256"] = "acceptance-run"
    with pytest.raises(smoke.AuditError, match="measurements"):
        smoke.audit(complete, runtime_metadata=metadata)


def test_cli_never_overwrites_existing_evidence(complete, tmp_path, capsys):
    destination = tmp_path / "before.json"
    argv = [str(complete), "--capture-resume", str(destination)]
    assert smoke.main(argv) == 0
    original = destination.read_bytes()
    assert smoke.main(argv) == 1 and destination.read_bytes() == original
    assert smoke.read(destination)["audit_passed"] is True
