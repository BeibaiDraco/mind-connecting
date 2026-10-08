"""No provider, model, network, or torch: budget and fail-closed process supervision."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "supervise_v4.py"
spec = importlib.util.spec_from_file_location("v4_supervisor_test", SCRIPT)
supervisor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = supervisor
spec.loader.exec_module(supervisor)


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def stage(name="first", kind="command", root=None):
    return supervisor.Stage(name, kind, ["synthetic-command", name], 20, root)


def artifacts(root, kind, *, consumable=True, gate="pass", core_gate="pass", smoke=False, update=1):
    root.mkdir(parents=True, exist_ok=True)
    split = "v4_llama31_" + supervisor.SUFFIXES[kind]
    identity = {"stage_config": {"model_profile": "llama31_8b_instruct",
                                  "n_episodes": supervisor.SIZES[kind], "seed": 0, "materials": "v1",
                                  "split": split, "stage": "calibrate" if kind == "calibration" else split},
                "limit": 4 if smoke else None, "model_profile": {"key": "llama31_8b_instruct"},
                "model_revision": "pinned", "tokenizer_manifest_sha": "assets",
                "prefix_hash": "prefix", "template_hash": "template"}
    payload = json.dumps(identity).encode()
    (root / "identity.json").write_bytes(payload)
    (root / "manifest.json").write_text(json.dumps({"smoke": smoke}))
    (root / "run_status.json").write_text(json.dumps({"status": "complete", "updated": update}))
    (root / "completeness.json").write_text(json.dumps({"status": "complete", "n_expected": 480,
                                                       "n_ok": 480, "n_missing": 0}))
    if kind in supervisor.POST_FILES:
        (root / supervisor.POST_FILES[kind]).write_text(json.dumps({
            "consumable": consumable, "gate": gate, "core_gate": core_gate,
            "step": supervisor.POST_FILES[kind].removesuffix(".json"),
            "identity_sha256": hashlib.sha256(payload).hexdigest(),
            "available": False, "matched": False, "route_validated": False,
            "families": {"primary": [{"mean": 0.0, "p": 1.0}]}}))
    if kind == "calibration":
        (root / "calibration_metadata.json").write_text(json.dumps({"21": {
            "smoke": False, "n_episodes": 60, "model_profile": {"key": "llama31_8b_instruct"},
            "model_revision": "pinned", "tokenizer_manifest_sha": "assets", "split": split,
            "prefix_hash": "prefix", "template_hash": "template",
            "hash": "calibration", "file_sha256": "a" * 64, "static_unusable": ["raw:cost"]}}))


def test_cost_is_cumulative_monotonic_and_includes_bandwidth():
    clock, bandwidth = Clock(), [0.0]
    budget = supervisor.Budget(3.6, 2, .5, clock=clock, bandwidth_reader=lambda: bandwidth[0])
    clock.now = 100
    assert budget.spent() == pytest.approx(2.6)
    bandwidth[0] = .3
    assert budget.spent() == pytest.approx(2.9)
    clock.now = 50
    bandwidth[0] = .1
    assert budget.spent() == pytest.approx(2.9)
    assert budget.remaining_seconds(70) == pytest.approx(7030)


def test_initial_cap_includes_prior_spend_and_stops_before_launch():
    calls = []
    budget = supervisor.Budget(1, 9.9, .2)
    result = supervisor.supervise([stage()], budget, stop=lambda: calls.append("stop"),
                                  command_runner=lambda *args: calls.append("command"), reserve_seconds=0)
    assert calls == ["stop"] and result["exit_code"] == 3


def test_later_phase_requires_feasible_measured_projection():
    for estimate in (None, 7200):
        calls = []
        budget = supervisor.Budget(2, 59, 0, "later")
        result = supervisor.supervise([stage()], budget, stop=lambda: calls.append("stop"),
                                      command_runner=lambda *args: calls.append("command"), reserve_seconds=0,
                                      estimated_remaining_seconds=estimate)
        assert calls == ["stop"] and result["exit_code"] != 0


def test_success_stops_once_and_budget_does_not_reset_between_stages():
    clock, calls, events = Clock(), [], []
    budget = supervisor.Budget(3600, 0, 0, clock=clock)
    def command(argv, timeout, remaining):
        calls.append(argv[-1])
        clock.now += 3
        assert remaining() == pytest.approx(10 - clock.now)
        return 0
    result = supervisor.supervise([stage(), stage("second")], budget, stop=lambda: calls.append("stop"),
                                  command_runner=command, reserve_seconds=0, emit=events.append)
    assert calls == ["first", "second", "stop"] and result["exit_code"] == 0
    assert result["spent_estimate_usd"] == 6 and result["provider_state_verified"] is False
    assert events[-1]["stop_command_succeeded"] is True


def test_nonzero_command_or_exception_never_launches_next_stage():
    for failure in (3, RuntimeError("private instance details"), KeyboardInterrupt()):
        calls = []
        def command(argv, *args):
            calls.append(argv[-1])
            if isinstance(failure, BaseException):
                raise failure
            return failure
        result = supervisor.supervise([stage(), stage("never")], supervisor.Budget(1, 0, 0),
                                      stop=lambda: calls.append("stop"), command_runner=command)
        assert calls == ["first", "stop"] and result["exit_code"] != 0
        assert "private" not in json.dumps(result)


@pytest.mark.parametrize("kind, changes", [
    ("baseline", {"gate": "fail"}), ("strength", {"gate": "fail"}),
    ("match", {"consumable": False}), ("validity", {"core_gate": "fail"}),
    ("formal", {"consumable": False}), ("baseline", {"smoke": True}),
])
def test_failed_or_nonconsumable_gate_stops_pipeline(tmp_path, kind, changes):
    calls = []
    def command(*args):
        calls.append("run")
        artifacts(tmp_path, kind, **changes)
        return 0
    result = supervisor.supervise([stage(kind=kind, root=tmp_path), stage("never")],
                                  supervisor.Budget(1, 0, 0, "later"), stop=lambda: calls.append("stop"),
                                  command_runner=command, estimated_remaining_seconds=100)
    assert calls == ["run", "stop"] and result["reason"] == "GateFailed"


@pytest.mark.parametrize("kind", ["match", "validity", "formal", "calibration", "smoke"])
def test_allowed_null_or_unavailable_branch_does_not_veto_core(tmp_path, kind):
    artifacts(tmp_path, kind, smoke=kind == "smoke")
    supervisor.check_gate(stage(kind=kind, root=tmp_path))


def test_incomplete_stale_or_wrong_identity_evidence_fails(tmp_path):
    selected = stage(kind="baseline", root=tmp_path)
    artifacts(tmp_path, "baseline")
    with pytest.raises(supervisor.GateFailed, match="fresh"):
        supervisor.check_gate(selected, supervisor.evidence(selected))
    (tmp_path / "completeness.json").write_text('{"status":"incomplete"}')
    with pytest.raises(supervisor.GateFailed, match="incomplete"):
        supervisor.check_gate(selected)
    artifacts(tmp_path, "baseline")
    identity = json.loads((tmp_path / "identity.json").read_text())
    identity["unrelated_change"] = True
    (tmp_path / "identity.json").write_text(json.dumps(identity))
    with pytest.raises(supervisor.GateFailed, match="another run identity"):
        supervisor.check_gate(selected)


def test_smoke_cannot_accept_wrong_split_or_zero_readout_calibration(tmp_path):
    selected = stage(kind="smoke", root=tmp_path)
    artifacts(tmp_path, "smoke", smoke=True)
    (tmp_path / "completeness.json").write_text('{"status":"complete","n_expected":0,"n_ok":0,"n_missing":0}')
    with pytest.raises(supervisor.GateFailed, match="480 readouts"):
        supervisor.check_gate(selected)
    artifacts(tmp_path, "smoke", smoke=True)
    identity = json.loads((tmp_path / "identity.json").read_text())
    identity["stage_config"]["stage"] = "calibrate"
    (tmp_path / "identity.json").write_text(json.dumps(identity))
    with pytest.raises(supervisor.GateFailed, match="stage identity"):
        supervisor.check_gate(selected)


def test_calibration_metadata_must_match_its_run_identity(tmp_path):
    artifacts(tmp_path, "calibration")
    path = tmp_path / "calibration_metadata.json"
    metadata = json.loads(path.read_text())
    metadata["21"]["tokenizer_manifest_sha"] = "other-assets"
    path.write_text(json.dumps(metadata))
    with pytest.raises(supervisor.GateFailed, match="calibration metadata"):
        supervisor.check_gate(stage(kind="calibration", root=tmp_path))


def test_budget_poll_can_interrupt_a_running_command():
    with pytest.raises(supervisor.BudgetExhausted):
        supervisor.run_command([sys.executable, "-c", "import time; time.sleep(10)"], 5, lambda: 0)


def test_real_command_timeout_is_bounded():
    started = time.monotonic()
    with pytest.raises(supervisor.CommandTimeout):
        supervisor.run_command([sys.executable, "-c", "import time; time.sleep(10)"], .05)
    assert time.monotonic() - started < 2


def test_stop_failure_is_reported_and_missing_stop_forbids_launch():
    def fail():
        raise RuntimeError("provider stop rejected")
    result = supervisor.supervise([stage()], supervisor.Budget(1, 0, 0), stop=fail,
                                  command_runner=lambda *args: 0)
    assert result["exit_code"] == 4 and result["stop_command_succeeded"] is False
    with pytest.raises(ValueError, match="provider stop"):
        supervisor.supervise([stage()], supervisor.Budget(1, 0, 0), stop=None)
    rejected = supervisor.supervise([stage()], supervisor.Budget(1, 0, 0), stop=lambda: False,
                                     command_runner=lambda *args: 0)
    assert rejected["exit_code"] == 4 and rejected["stop_command_succeeded"] is False


def test_acceptance_cannot_launch_research_pilots_without_cost_transition(tmp_path):
    calls = []
    result = supervisor.supervise([stage(kind="strength", root=tmp_path)], supervisor.Budget(1, 0, 0),
                                  stop=lambda: calls.append("stop"),
                                  command_runner=lambda *args: calls.append("never"))
    assert calls == ["stop"] and result["exit_code"] != 0


def test_broken_bandwidth_feed_stops_and_keeps_last_cost_estimate():
    calls = []
    def broken():
        raise ValueError("unreadable billing update")
    budget = supervisor.Budget(1, 2, .5, bandwidth_reader=broken)
    result = supervisor.supervise([stage()], budget, stop=lambda: calls.append("stop"),
                                  command_runner=lambda *args: calls.append("never"))
    assert calls == ["stop"] and result["exit_code"] != 0
    assert result["spent_estimate_usd"] >= 2.5


def test_cli_runs_private_argv_and_journals_without_connection_details(tmp_path):
    marker, plan, stop_file, journal = (tmp_path / name for name in ("stopped", "plan.json", "stop.json", "journal.jsonl"))
    private_value = "private-test-instance-never-journal"
    plan.write_text(json.dumps([{"name": "acceptance", "kind": "command", "timeout_seconds": 2,
                                 "command": [sys.executable, "-c", "pass", private_value]}]))
    stop_file.write_text(json.dumps([sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('stopped')", str(marker)]))
    completed = subprocess.run([sys.executable, str(SCRIPT), "--plan", str(plan), "--phase", "acceptance",
                                "--hourly-usd", "1", "--prior-spend-usd", ".2", "--bandwidth-usd", ".1",
                                "--stop-command-file", str(stop_file), "--journal", str(journal)],
                               capture_output=True, text=True, timeout=10)
    assert completed.returncode == 0 and marker.read_text() == "stopped"
    assert private_value not in journal.read_text() + completed.stdout + completed.stderr
    assert json.loads(completed.stdout)["stop_command_succeeded"] is True
