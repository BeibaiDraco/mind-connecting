"""Launch contracts: failure paths never spend or silently weaken a freeze."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


launcher = module("run_v5_stage")
freeze = module("freeze_v5")


def budget(**changes):
    value = {"approved": True, "scope": "v5", "cap_usd": 20., "hourly_usd": 2.,
             "prior_spend_usd": 3., "bandwidth_reserve_usd": 1.,
             "shutdown_reserve_usd": 1., "started_at_epoch": 1000.}
    return value | changes


def test_budget_uses_original_anchor_and_all_reserves():
    assert launcher.budget_deadline(budget(), now=1200) == 1000 + 15 * 1800
    assert launcher.budget_deadline(budget(), now=2000) == launcher.budget_deadline(budget(), now=1200)


@pytest.mark.parametrize("changes", [{"approved": False}, {"scope": "v4"}, {"hourly_usd": 0},
    {"cap_usd": float("nan")}, {"started_at_epoch": 5000}, {"prior_spend_usd": 30},
    {"shutdown_reserve_usd": 0}, {"hourly_usd": True}])
def test_invalid_or_expired_budget_refused(changes):
    with pytest.raises(ValueError):
        launcher.budget_deadline(budget(**changes), now=1200)


def test_private_control_rejects_shell_string_and_repo_paths(tmp_path):
    path = tmp_path / "argv.json"
    path.write_text(json.dumps("echo unsafe"))
    with pytest.raises(ValueError, match="argv"):
        launcher.private_argv({"cmd": str(path)}, "cmd")
    with pytest.raises(ValueError, match="repository"):
        launcher.private_argv({"cmd": str(ROOT / "secret.json")}, "cmd")


def test_shutdown_requires_verified_state_not_only_request(tmp_path, monkeypatch):
    for name in ("stop", "verify"):
        (tmp_path / f"{name}.json").write_text(json.dumps([name]))
    doc = {"stop_command_file": str(tmp_path / "stop.json"),
           "verify_stopped_command_file": str(tmp_path / "verify.json")}
    monkeypatch.setattr(launcher, "quiet_command", lambda argv: argv == ["stop"])
    monkeypatch.setattr(launcher.time, "sleep", lambda *_: None)
    assert not launcher.stop_provider(doc, tmp_path, "test")
    assert json.loads((tmp_path / "shutdown.json").read_text())["verified_stopped"] is False


def test_failed_request_can_still_have_verified_stopped_state(tmp_path, monkeypatch):
    for name in ("stop", "verify"):
        (tmp_path / f"{name}.json").write_text(json.dumps([name]))
    doc = {"stop_command_file": str(tmp_path / "stop.json"),
           "verify_stopped_command_file": str(tmp_path / "verify.json")}
    monkeypatch.setattr(launcher, "quiet_command", lambda argv: argv == ["verify"])
    assert launcher.stop_provider(doc, tmp_path, "test")


def test_local_launch_is_blocked_before_private_inputs(monkeypatch):
    monkeypatch.setattr(launcher.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(sys, "argv", ["run_v5_stage.py", "--budget-file", "/absent", "--control-dir", "/absent"])
    with pytest.raises(SystemExit):
        launcher.main()


def test_freeze_rejects_changed_dependency(tmp_path):
    dep = tmp_path / "dep"
    dep.write_text("original")
    doc = {"protocol": "v5", "kind": "stage", "files": {str(dep): "0" * 64}}
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="changed"):
        freeze.verify(path)


def test_freeze_write_never_replaces_existing_evidence(tmp_path):
    path = tmp_path / "freeze.json"
    path.write_text("original")
    with pytest.raises(FileExistsError):
        freeze.write_once(path, {"changed": True})
    assert path.read_text() == "original"


def test_shutdown_continues_when_logs_and_lock_cannot_be_written(tmp_path, monkeypatch):
    for name in ("stop", "verify"):
        (tmp_path / f"{name}.json").write_text(json.dumps([name]))
    doc = {"stop_command_file": str(tmp_path / "stop.json"),
           "verify_stopped_command_file": str(tmp_path / "verify.json")}
    calls = []
    def fake(argv):
        calls.append(argv)
        return len(calls) >= 4
    monkeypatch.setattr(launcher, "quiet_command", fake)
    monkeypatch.setattr(launcher.time, "sleep", lambda *_: None)
    assert launcher.stop_provider(doc, tmp_path / "not-created", "disk_failure")
    assert calls == [["stop"], ["verify"], ["stop"], ["verify"]]


def test_active_child_receipt_refuses_duplicate_launch(tmp_path, monkeypatch):
    receipt = tmp_path / "active.json"
    receipt.write_text(json.dumps({"active": True, "state": "launch_intent"}))
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(RuntimeError, match="unresolved"):
        launcher.guarded_child(["no-model"], 9000, receipt, "stage")


def test_prelaunch_failure_still_requests_provider_stop(tmp_path, monkeypatch):
    doc = {"stop_command_file": str(tmp_path / "stop.json"),
           "verify_stopped_command_file": str(tmp_path / "verify.json")}
    for key, path in doc.items():
        Path(path).write_text(json.dumps([key]))
    budget_file = tmp_path / "budget.json"
    budget_file.write_text(json.dumps(doc))
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    monkeypatch.setattr(sys, "argv", ["launcher", "--budget-file", str(budget_file),
                                      "--control-dir", str(tmp_path / "control")])
    monkeypatch.setattr(launcher, "_main", lambda: (_ for _ in ()).throw(ValueError("bad freeze")))
    calls = []
    monkeypatch.setattr(launcher, "stop_provider", lambda *args: calls.append(args[2]) or True)
    with pytest.raises(ValueError, match="bad freeze"):
        launcher.main()
    assert calls == ["launch_or_execution_failure"]


def test_monotonic_timeout_survives_wall_clock_rollback(tmp_path, monkeypatch):
    class Fake:
        pid = 123
        returncode = None
        def poll(self):
            return self.returncode
    process = Fake()
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: process)
    monkeypatch.setattr(launcher, "terminate_process", lambda p: setattr(p, "returncode", -15))
    monkeypatch.setattr(launcher.time, "time", lambda: 1000)
    ticks = iter((100, 120))
    monkeypatch.setattr(launcher.time, "monotonic", lambda: next(ticks))
    with pytest.raises(RuntimeError, match="deadline"):
        launcher.guarded_child(["fake"], 1010, tmp_path / "active.json", "test")
    assert json.loads((tmp_path / "active.json").read_text())["active"] is False


def synthetic_smoke(root):
    from mb import chat, tasks, provenance_tasks as p, run
    from make_v5_provenance import build_config
    import yaml
    cfg = run.StageConfig(**build_config("qwen", "smoke"))
    tok = chat.load_tokenizer(profile=cfg.model_profile)
    identity = run.build_identity(cfg, 4, run.template_hash(tok, profile=cfg.model_profile, provenance=True),
                                  {}, prefix=run.prefix_hash(tok, profile=cfg.model_profile))
    arms = cfg.arm_configs()
    hashes = {a.name: a.config_hash("none", "none", identity["template_hash"]) for a in arms}
    for name, data in (("identity.json", identity), ("manifest.json", {"smoke": True}),
                       ("run_status.json", {"status": "complete"}), ("arm_hashes.json", hashes)):
        (root / name).write_text(json.dumps(data))
    (root / "config.yaml").write_text(yaml.safe_dump(build_config("qwen", "smoke")))
    records, notes = [], {}
    for ep in tasks.make_episodes(4, cfg.split, 0):
        for record, side in ((ep, "A"), (ep, "B"), (p.donor_episode(ep), "B")):
            notes[tasks.note_key(record, side)] = {"key": tasks.note_key(record, side), "ids": [1, 2]}
        for arm in arms:
            for side in arm.recipients:
                for qid in cfg.qids:
                    for rot in ep.rotations:
                        q = p.render_question(tok, ep, side, qid, rot, arm.donor_robin_conflict)
                        records.append({"episode_id": ep.episode_id, "arm": arm.name, "recipient": side,
                            "qid": qid, "rotation_id": rot, "config_hash": hashes[arm.name], "status": "ok",
                            "options": list(q.options), "label_meaning": list(q.label_meaning),
                            "label_logits": [1., 2., 3., 4.], "label_logprobs": [-2.]*4, "label_mass": .99,
                            "text_hash": q.text_hash, "provenance": p.record_metadata(ep, side, q, arm.donor_robin_conflict),
                            "c48_snapshot_key": ep.episode_id + arm.name, "c48_snapshot_sha256": "a" * 64})
    (root / "notes.jsonl").write_text("".join(json.dumps(x)+"\n" for x in notes.values()))
    (root / "snapshots.jsonl").write_text("")
    (root / "records").mkdir()
    (root / "records/attempt-001.jsonl").write_text("".join(json.dumps(x)+"\n" for x in records))
    return records


def test_smoke_audit_and_resume_reject_mutation(tmp_path):
    from check_v5_smoke import audit
    records = synthetic_smoke(tmp_path)
    before = audit(tmp_path)
    assert before["passed"] and before["n_records"] == 768 and not before["resume_verified"]
    (tmp_path / "records/attempt-002.jsonl").write_text("")
    assert audit(tmp_path, before)["resume_verified"]
    records[0]["c48_snapshot_key"] = "a-new-question-specific-state"
    (tmp_path / "records/attempt-001.jsonl").write_text("".join(json.dumps(x)+"\n" for x in records))
    with pytest.raises(ValueError, match="one C48"):
        audit(tmp_path)


def test_native_acceptance_skips_or_wrong_source_cannot_pass(tmp_path):
    from check_v5_acceptance import Evidence, verify
    from mb.model_profiles import LLAMA31
    from types import SimpleNamespace
    evidence = Evidence(tmp_path / "native.json", LLAMA31.key)
    evidence.pytest_collection_finish(SimpleNamespace(items=list(range(8))))
    for index in range(8):
        evidence.pytest_runtest_logreport(SimpleNamespace(nodeid=f"test-{index}", when="call", outcome="passed"))
    assert evidence.finish(0)
    assert verify(evidence.path, LLAMA31.key)["status"] == "passed"
    evidence.doc["reports"][0]["outcome"] = "skipped"
    evidence.save()
    with pytest.raises(ValueError, match="acceptance"):
        verify(evidence.path, LLAMA31.key)


def test_formal_completion_never_gates_on_matching_or_effect(tmp_path, monkeypatch):
    from types import SimpleNamespace
    cfg = SimpleNamespace(stage="formal", post=["v5_static_contrasts"])
    monkeypatch.setattr(launcher.run, "run_post", lambda *args: {
        "consumable": True, "formal_matched": False, "effect": -1})
    passed, detail = launcher.scientific_gate(cfg, tmp_path)
    assert passed and detail["effect_based_gate"] is False
    monkeypatch.setattr(launcher.run, "run_post", lambda *args: {"consumable": False})
    assert launcher.scientific_gate(cfg, tmp_path)[0] is False
