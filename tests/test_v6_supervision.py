"""Operational protocol tests only: no SSH, provider, model or network use."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from mb import v6_supervision as s
from mb.v6_contract import canonical_digest


class Clock:
    def __init__(self):
        self.wall = 1000.0
        self.mono = 50.0
    def time(self):
        return self.wall
    def monotonic(self):
        return self.mono
    def sleep(self, seconds):
        self.wall += seconds
        self.mono += seconds


def pin(path, value):
    path.write_text(json.dumps(value, sort_keys=True))
    return {"path": str(path), "sha256": s.file_sha256(path)}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    clock = Clock()
    budget = {"session_id": "v6-test", "started_at_epoch": 900., "total_cap_usd": 100.,
        "initial_cap_usd": 12., "hourly_cap_usd": 1.6, "bandwidth_reserve_usd": 1.,
        "prior_spend_usd": 0., "accrued_bandwidth_usd": 0., "shutdown_reserve_seconds": 300.,
        "hard_deadline_epoch": 10000.}
    binding = {"private_test_target": "not-a-real-host"}
    anchor = {"budget": budget, "instance_binding_sha256": canonical_digest(binding),
              "authorization_sha256": "a" * 64}
    plan = {"version": "v6-native-stage-1", "stage": "smoke", "n": 2,
            "model_profile": "qwen3_4b_instruct_2507", "source_manifest": {"source": "b" * 64},
            "output_dir": "/remote/results/smoke"}
    adapter = tmp_path / "adapter.py"
    adapter.write_text("# self-contained private adapter fixture\n")
    spec = {"version": s.VERSION, "plan_pin": pin(tmp_path / "plan.json", plan),
        "adapter_pin": {"path": str(adapter), "sha256": s.file_sha256(adapter)},
        "binding_pin": pin(tmp_path / "binding.json", binding),
        "budget_anchor_pin": pin(tmp_path / "anchor.json", anchor),
        "remote_repository": "/remote/repo", "remote_python": "/remote/repo/.venv/bin/python",
        "remote_plan_path": "/remote/plan.json", "remote_admission_path": "/remote/admission.json"}
    control = tmp_path / "control"; control.mkdir()
    calls = []
    responses = {}
    def adapter(request, timeout):
        calls.append((request["action"], copy.deepcopy(request), timeout))
        result = responses.get(request["action"], {})
        if callable(result):
            result = result(request, timeout)
        if isinstance(result, BaseException):
            raise result
        return {k: v for k, v in {**request, "version": "v6-operational-response-1",
            "observed_at_epoch": clock.time(), "result": result}.items() if k != "payload"}
    obj = s.Supervisor(spec, plan, anchor, control, adapter,
        clock=clock.time, sleep=clock.sleep, monotonic=clock.monotonic)
    def validation(plan_path, admission_path, *, now, evidence_dir):
        return {**plan, "plan_sha256": canonical_digest(plan), "_admission": {"historical_only": True}}
    monkeypatch.setattr(s, "validate_execution", validation)
    proof = {"phase": "initial", "budget": budget, "instance_binding_sha256": anchor["instance_binding_sha256"],
        "budget_anchor_pin": spec["budget_anchor_pin"], "expires_at_epoch": clock.time()+300}
    responses["refresh"] = {"admission_pin": pin(tmp_path / "admission.json", proof),
        "evidence_dir": str(tmp_path), "remote_validation": {"version": "v6-native-execution-1",
        "status": "admitted_not_executed", "plan_sha256": canonical_digest(plan), "stage": "smoke",
        "model_or_gpu_used": False}}
    responses["launch_detached"] = {"detached": True, "independent_deadline_guard": True,
        "exclusive_intent_persisted": True, "competing_workers_absent": True, "worker_exit_or_lease_expiry_stop": True, "worker_id_sha256": "c" * 64}
    responses["status"] = {"actual_status": "exited", "intended_status": "stopped",
                           "cur_state": "stopped", "next_state": "stopped"}
    return obj, responses, calls, clock, tmp_path


def backup_response(obj, tmp_path, *, omit_data=False, changed_completion=False, wrong_nonce=False):
    root = tmp_path / "sd"; root.mkdir(exist_ok=True)
    run = root / "run"; run.mkdir(exist_ok=True)
    data = run / "records.jsonl"; data.write_text("retained scientific bytes\n")
    identity = {"plan": {**obj.plan, "plan_sha256": obj.context["plan_sha256"]}}
    identity_file = run / "identity.json"; identity_file.write_text(json.dumps(identity, sort_keys=True))
    pins = {p.name: {"bytes": p.stat().st_size, "sha256": s.file_sha256(p)} for p in (data, identity_file)}
    completion = {"version": "v6-native-completion-1", "status": "complete", "backend_kind": "native",
        "stage": "smoke", "model_profile": obj.plan["model_profile"], "n": 2,
        "source_manifest_sha256": canonical_digest(obj.plan["source_manifest"]),
        "validation": {"complete": True}, "file_pins": pins, "identity_sha256": canonical_digest(identity)}
    cp = run / "completion.json"; cp.write_text(json.dumps(completion, sort_keys=True))
    obj.completion_sha = s.file_sha256(cp)
    obj.remote_complete = True
    def response(request, timeout):
        files = [cp] if omit_data else [data, identity_file, cp]
        inv = {"version": "v6-backup-inventory-1", **obj.context, "launch_nonce": obj.launch_nonce,
            "backup_nonce": "wrong" if wrong_nonce else request["payload"]["backup_nonce"],
            "complete_run": True, "completion_sha256": "e" * 64 if changed_completion else obj.completion_sha,
            "files": [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size,
                       "sha256": s.file_sha256(p)} for p in files]}
        ip = pin(tmp_path / "inventory.json", inv)
        ack = {"version": "v6-backup-ack-1", **obj.context, "launch_nonce": obj.launch_nonce,
               "backup_nonce": inv["backup_nonce"], "inventory_sha256": ip["sha256"],
               "verified": True, "file_count": len(files)}
        return {"inventory_pin": ip, "ack_pin": pin(tmp_path / "ack.json", ack),
                "local_root": str(root), "mount_verified": True}
    return response


def test_refresh_accepts_actual_validate_only_schema(setup):
    obj, _, _, _, _ = setup
    obj.refresh()
    assert obj.proof_expires == 1060


@pytest.mark.parametrize("mutation", ["lower_charge", "new_start", "wrong_phase", "wrong_target", "old_schema"])
def test_refresh_rejects_financial_or_producer_changes(setup, mutation):
    obj, responses, _, _, tmp = setup
    result = responses["refresh"]
    proof = s.read(result["admission_pin"]["path"])
    if mutation == "lower_charge": proof["budget"]["accrued_bandwidth_usd"] = -1
    if mutation == "new_start": proof["budget"]["started_at_epoch"] += 1
    if mutation == "wrong_phase": proof["phase"] = "full"
    if mutation == "wrong_target": proof["instance_binding_sha256"] = "f" * 64
    if mutation == "old_schema": result["remote_validation"].pop("version")
    result["admission_pin"] = pin(tmp / "changed-admission.json", proof)
    with pytest.raises(ValueError): obj.refresh()


def test_ambiguous_launch_is_never_reissued(setup):
    obj, responses, calls, _, _ = setup
    responses["launch_detached"] = TimeoutError()
    obj.refresh()
    with pytest.raises(TimeoutError): obj.launch(resume=False)
    with pytest.raises(ValueError): obj.launch(resume=False)
    assert [x[0] for x in calls].count("launch_detached") == 1
    assert (obj.control / "launch_intent.json").is_file()


def test_launch_uses_only_exact_native_command_and_explicit_resume(setup):
    obj, _, calls, _, _ = setup
    obj.refresh(); obj.launch(resume=True)
    command = next(x[1]["payload"]["command"] for x in calls if x[0] == "launch_detached")
    assert command == ["/remote/repo/.venv/bin/python", "/remote/repo/scripts/v6_execute.py",
                       "--plan", "/remote/plan.json", "--admission", "/remote/admission.json", "--resume"]
    assert "--allow-code-change" not in command


def test_provider_acceptance_does_not_mean_stopped(setup):
    obj, responses, calls, _, _ = setup
    responses["stop_instance"] = {"accepted": True}
    responses["status"]["actual_status"] = "running"
    assert obj.stop() is False
    assert [x[0] for x in calls].count("status") == 4


def test_stop_survives_backup_and_journal_failures(setup, monkeypatch):
    obj, _, calls, _, _ = setup
    monkeypatch.setattr(obj, "refresh", lambda: (_ for _ in ()).throw(ValueError("initial refusal")))
    monkeypatch.setattr(obj, "backup", lambda **k: (_ for _ in ()).throw(OSError("disk")))
    monkeypatch.setattr(obj, "event", lambda *a, **k: (_ for _ in ()).throw(OSError("journal")))
    result = obj.run()
    assert result["provider_stopped"] and result["status"] == "failed"
    assert "stop_instance" in [x[0] for x in calls]


def test_monotonic_deadline_prevents_clock_rollback(setup):
    obj, _, _, clock, _ = setup
    end = obj.monotonic_deadline
    clock.wall = 950
    clock.mono = end
    with pytest.raises(ValueError, match="Monotonic"): obj.deadline()


@pytest.mark.parametrize("kwargs", [{"omit_data": True}, {"changed_completion": True}, {"wrong_nonce": True}])
def test_final_backup_rejects_subset_wrong_completion_or_nonce(setup, kwargs):
    obj, responses, _, _, tmp = setup
    responses["backup"] = backup_response(obj, tmp, **kwargs)
    with pytest.raises(ValueError): obj.backup(final=True)
    assert not obj.backup_verified


def test_final_backup_rehashes_all_closed_files(setup):
    obj, responses, _, _, tmp = setup
    responses["backup"] = backup_response(obj, tmp)
    obj.backup(final=True)
    assert obj.backup_copied and not obj.backup_verified and len(obj.retained_files) == 3
    obj.final_rehash(provider_stopped=True)
    assert obj.backup_verified


def test_retained_prefix_mutation_rejected(setup):
    obj, responses, _, _, tmp = setup
    responses["backup"] = backup_response(obj, tmp)
    obj.backup(final=True)
    (tmp / "sd/run/records.jsonl").write_text("replaced scientific bytes\n")
    with pytest.raises(ValueError, match="Previously retained"): obj.backup(final=True)


def test_deadline_checked_between_backup_chunks(setup):
    obj, _, _, clock, tmp = setup
    path = tmp / "large"; path.write_bytes(b"x" * (1024 * 1024 + 1))
    with pytest.raises(ValueError, match="window"): obj._hash_backup(path, path.stat().st_size, clock.mono, final=True)


def test_live_backup_tick_refreshes_instead_of_starving_proof(setup, monkeypatch):
    obj, _, _, clock, _ = setup
    obj.last_refresh = clock.time()
    refreshed = []
    monkeypatch.setattr(obj, "refresh", lambda: refreshed.append(clock.time()))
    clock.sleep(31)
    obj._backup_tick(clock.mono + 60, final=False)
    assert refreshed == [1031.]


def test_complete_lifecycle_never_reads_effects(setup):
    obj, responses, calls, _, tmp = setup
    responses["backup"] = backup_response(obj, tmp)
    obj.remote_complete = False
    responses["observe"] = {"worker_id_sha256": "c" * 64, "state": "complete", "completed_episodes": 2,
        "expected_episodes": 2, "exit_code": 0, "completion_sha256": obj.completion_sha,
        "effects": "deliberately ignored"}
    result = obj.run()
    assert result["status"] == "complete"
    assert [x[0] for x in calls].count("launch_detached") == 1
    assert "terminate_child" not in [x[0] for x in calls]
    assert "effects" not in (obj.control / "journal.jsonl").read_text()


def test_bound_stop_deadline(setup):
    obj, responses, calls, clock, _ = setup
    start = clock.mono
    def failure(request, timeout):
        clock.sleep(timeout)
        raise TimeoutError()
    responses["stop_instance"] = failure
    responses["status"] = failure
    assert obj.stop() is False
    assert clock.mono - start <= 180


def test_adapter_checks_hash_and_kills_process_group(tmp_path, monkeypatch):
    source = tmp_path / "adapter.py"; source.write_text("pass\n")
    a = s.PrivateAdapter(source, s.file_sha256(source))
    killed = []
    class Process:
        pid = 12345
        def communicate(self, *args, **kwargs): raise subprocess.TimeoutExpired("fake", 1)
    monkeypatch.setattr(s.subprocess, "Popen", lambda *a, **kw: Process())
    monkeypatch.setattr(s.os, "killpg", lambda *a: killed.append(a))
    with pytest.raises(subprocess.TimeoutExpired): a({}, 1)
    assert killed == [(12345, s.signal.SIGKILL)]
    source.write_text("changed\n")
    with pytest.raises(ValueError, match="copy changed"): a({}, 1)


def test_final_hash_is_only_after_actual_stop(setup):
    obj, responses, calls, _, tmp = setup
    responses["backup"] = backup_response(obj, tmp)
    obj.backup(final=True)
    with pytest.raises(ValueError, match="actual provider stop"): obj.final_rehash(provider_stopped=False)
    (tmp / "sd/run/records.jsonl").write_text("replaced scientific bytes\n")
    with pytest.raises(ValueError, match="rehash"): obj.final_rehash(provider_stopped=True)
    assert not obj.backup_verified


def test_unchanged_receipt_cached_but_same_size_mutation_rehashed(setup):
    obj, responses, _, _, tmp = setup
    responses["backup"] = backup_response(obj, tmp)
    obj.backup(final=True)
    obj.backup(final=True)
    last = s.read(obj.control / "last_backup.json")
    assert last["cached_files"] == 3 and last["freshly_rehashed_files"] == 0
    path = tmp / "sd/run/records.jsonl"
    path.write_bytes(b"x" * path.stat().st_size)
    with pytest.raises(ValueError): obj.backup(final=True)


def test_closed_failed_gate_still_requires_full_backup(setup):
    obj, responses, _, _, tmp = setup
    responses["backup"] = backup_response(obj, tmp, omit_data=True)
    obj.remote_complete = False
    with pytest.raises(ValueError, match="omits"): obj.backup(final=True)


def test_missing_worker_exit_guard_refuses_launch(setup):
    obj, responses, _, _, _ = setup
    responses["launch_detached"]["worker_exit_or_lease_expiry_stop"] = False
    obj.refresh()
    with pytest.raises(ValueError): obj.launch(resume=False)


def test_expired_budget_still_attempts_fail_safe_stop(setup, monkeypatch):
    obj, _, calls, clock, _ = setup
    obj._preflight_error = ValueError("expired initial budget")
    result = obj.run()
    assert result["provider_stopped"] and result["status"] == "failed"
    assert "launch_detached" not in [x[0] for x in calls]


def test_load_spec_rejects_changed_private_binding(setup):
    obj, _, _, _, tmp = setup
    spec_path = tmp / "spec.json"; spec_path.write_text(json.dumps(obj.spec))
    s.load_spec(spec_path)
    obj.spec["binding_pin"] = pin(tmp / "other-binding.json", {"other": True})
    spec_path.write_text(json.dumps(obj.spec))
    with pytest.raises(ValueError, match="another private target"): s.load_spec(spec_path)


def test_cancel_backup_does_not_kill_stop_or_status(tmp_path, monkeypatch):
    source = tmp_path / "adapter.py"; source.write_text("pass\n")
    adapter = s.PrivateAdapter(source, s.file_sha256(source))
    class P:
        def __init__(self, pid): self.pid = pid
    adapter._pending = {"a": ("backup", P(10)), "b": ("status", P(11)), "c": ("stop_instance", P(12))}
    killed = []
    monkeypatch.setattr(s.os, "killpg", lambda *args: killed.append(args))
    adapter.cancel_pending("backup")
    assert killed == [(10, s.signal.SIGKILL)]


def test_final_backup_validates_closed_failed_run_without_observe_receipt(setup):
    obj, responses, _, _, tmp = setup
    responses["backup"] = backup_response(obj, tmp, omit_data=True)
    obj.remote_complete = False
    obj.completion_sha = None
    # The adapter can discover a closed gate-failed run after observation failed.
    closed = s.file_sha256(tmp / "sd/run/completion.json")
    previous = responses["backup"]
    def response(request, timeout):
        obj.completion_sha = closed
        result = previous(request, timeout)
        obj.completion_sha = None
        return result
    responses["backup"] = response
    with pytest.raises(ValueError, match="omits"): obj.backup(final=True)
