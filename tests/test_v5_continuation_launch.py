"""Continuation funding, isolation, preservation and outcome-blind completion."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_v5_continuation as chain
import run_v5_stage as stage
from mb import ledger


def proposal(tmp_path, study="provenance"):
    return chain.plan(study, tmp_path / study, tmp_path / "budget.json",
                      tmp_path / "proof.json", tmp_path / "remote_controls.py",
                      sum(chain.ENGINEERING_SECONDS) + chain.FORMAL_SECONDS["static"]
                      if study == "provenance" else 0)


def approved_budget(tmp_path):
    original = {"scope": "v5", "approved": True, "cap_usd": 60., "hourly_usd": 1.4,
                "prior_spend_usd": 0., "bandwidth_reserve_usd": 2.,
                "shutdown_reserve_usd": 1.4/12, "started_at_epoch": 1000.}
    path = tmp_path / "original.json"
    path.write_text(json.dumps({"budget": original, "container_id_sha256": "a" * 64}))
    sha = ledger.file_sha256(path)
    receipt = {"approved": True, "scope": "v5_llama_fixed_continuations",
               "studies": ["provenance", "static"], "cumulative_cap_usd": 100.,
               "original_full_plan_sha256": sha, "authorization_text": "PI authorizes this package and cap",
               "approved_at_epoch": 2000.}
    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps(receipt))
    return {**original, "cap_usd": 100., "continuation_approval_file": str(approval),
            "continuation_approval_sha256": ledger.file_sha256(approval),
            "original_full_plan_file": str(path), "original_full_plan_sha256": sha}


def test_plan_is_inert_and_preserves_fixed_order_and_workload(tmp_path):
    doc = proposal(tmp_path)
    chain.validate_plan(doc)
    assert doc["paid_start_authorized_by_this_plan"] is False
    assert doc["phases"] == ["native", "smoke", "resume", "formal"]
    assert doc["remaining_other_seconds"] >= chain.FORMAL_SECONDS["static"]
    assert not (tmp_path / "provenance").exists()


@pytest.mark.parametrize("field,value", [("phases", ["formal"]), ("remaining_other_seconds", 0),
    ("controller_sha256", "0"*64), ("config", "configs/v5/provenance/llama31_base.yaml")])
def test_changed_or_underreserved_plan_rejected(tmp_path, field, value):
    with pytest.raises(ValueError):
        chain.validate_plan(proposal(tmp_path) | {field: value})


def test_funding_promotion_retains_original_anchor(tmp_path):
    doc, budget = proposal(tmp_path), approved_budget(tmp_path)
    assert chain.admission(doc, budget, now=2200) == stage.budget_deadline(budget, now=2200)
    for key in ("started_at_epoch", "prior_spend_usd", "hourly_usd", "bandwidth_reserve_usd"):
        with pytest.raises(ValueError, match="anchor"):
            chain.admission(doc, budget | {key: budget[key] + 1}, now=2200)


def test_missing_or_changed_approval_rejected(tmp_path):
    doc, budget = proposal(tmp_path), approved_budget(tmp_path)
    with pytest.raises(ValueError):
        chain.admission(doc, budget | {"approved": False}, now=2200)
    with pytest.raises(ValueError, match="numerical cap"):
        chain.admission(doc, budget | {"cap_usd": 200.}, now=2200)
    Path(budget["continuation_approval_file"]).write_text('{}')
    with pytest.raises(ValueError, match="receipt changed"):
        chain.admission(doc, budget, now=2200)


def test_entire_remaining_package_must_fit(tmp_path):
    doc = proposal(tmp_path)
    with pytest.raises(ValueError, match="package"):
        chain.require_room(doc, 3, deadline=70_000, now=1000)
    chain.require_room(doc, 3, deadline=150_000, now=1000)


def test_formal_argv_never_keeps_session_or_limits_n(tmp_path):
    doc = proposal(tmp_path)
    argv = chain.stage_argv(doc, 3, tmp_path / "smoke")
    assert "--keep-session" not in argv and "--limit" not in argv
    assert "--smoke-run" in argv and "--native-evidence" in argv
    with pytest.raises(ValueError):
        chain.stage_argv(doc, 3, None)


def test_local_execute_refuses_before_any_file_or_process(tmp_path, monkeypatch):
    monkeypatch.setattr(chain.platform, "system", lambda: "Darwin")
    with pytest.raises(ValueError, match="Linux"):
        chain.execute(proposal(tmp_path))
    assert not list(tmp_path.iterdir())


def test_failed_postprocessing_still_preserves_raw_run(tmp_path, monkeypatch):
    control = tmp_path / "control"
    control.mkdir()
    backup = tmp_path / "backup.json"
    backup.write_text(json.dumps(["verified-backup"]))
    monkeypatch.setattr(stage, "collected_run", lambda *a: tmp_path / "rawrun")
    calls = []
    monkeypatch.setattr(stage, "quiet_command", lambda argv, **kw: calls.append(argv) or True)
    stage.preserve_failure(SimpleNamespace(stage="formal", split="fixed600"), control,
                           {"backup_command_file": str(backup)}, set(), None, ValueError("bad metadata"))
    result = json.loads((control / "last_stage.json").read_text())
    assert result["run_dir"] == str(tmp_path / "rawrun")
    assert result["backup_verified"] and not result["gate_passed"]
    assert calls == [["verified-backup"]]


def test_continuation_completion_uses_integrity_not_effect_or_match(tmp_path, monkeypatch):
    from mb import v5_continuation
    result = {"consumable": True, "summary": {"formal_matched": False, "effect": -999}}
    monkeypatch.setattr(v5_continuation, "analyze_run", lambda root: result)
    cfg = SimpleNamespace(params={"continuation": {"version": "v5-continuation"}})
    passed, detail = stage.scientific_gate(cfg, tmp_path)
    assert passed and not detail["effect_based_gate"]
    assert json.loads((tmp_path / "v5_continuation_summary.json").read_text()) == result
    result["summary"]["effect"] = 999
    with pytest.raises(ValueError, match="replace"):
        stage.scientific_gate(cfg, tmp_path)


def test_static_requires_prior_provenance_backup_and_stop_receipt(tmp_path):
    doc, budget = proposal(tmp_path, "static"), approved_budget(tmp_path)
    with pytest.raises(FileNotFoundError):
        chain.prior_completion(doc, budget)
    prior = tmp_path / "provenance"
    prior.mkdir()
    last = {"collection_complete": True, "gate_passed": True, "backup_verified": True,
            "stage": "v5_llama31_provenance_confirm", "at_epoch": 2000,
            "run_dir": "/workspace/mb-data/results/test"}
    request = {"run_dir": last["run_dir"], "nonce": "n", "inventory_sha256": "i", "identity_sha256": "h"}
    ack = {"verified": True, **request}
    for name, value in (("last_stage.json", last), ("backup_request.json", request), ("backup_ack.json", ack)):
        (prior / name).write_text(json.dumps(value))
    receipt = {"provider_stopped_verified": True, "target_sha256": "a" * 64,
               "prior_control_dir": str(prior), "checked_epoch": 2200,
               **{name.removesuffix('.json') + '_sha256': ledger.file_sha256(prior / name)
                  for name in ("last_stage.json", "backup_request.json", "backup_ack.json")}}
    path = tmp_path / "provenance_stopped_backup.json"
    path.write_text(json.dumps(receipt))
    chain.prior_completion(doc, budget)
    path.write_text(json.dumps(receipt | {"provider_stopped_verified": False}))
    with pytest.raises(ValueError, match="prior provider stop"):
        chain.prior_completion(doc, budget)


def test_detach_log_race_does_not_stop_the_winning_controller(tmp_path, monkeypatch):
    doc = proposal(tmp_path)
    plan_path = tmp_path / "plan.json"
    monkeypatch.setattr(chain.platform, "system", lambda: "Linux")
    monkeypatch.setattr(chain, "admission", lambda *a: 999999)
    monkeypatch.setattr(chain, "prior_completion", lambda *a: None)
    monkeypatch.setattr(chain, "guard_proof", lambda *a: None)
    monkeypatch.setattr(stage, "read", lambda p: doc if p == plan_path else {})
    stopped = []
    monkeypatch.setattr(stage, "stop_provider", lambda *a: stopped.append(True))
    original = Path.open
    def raced_open(path, mode="r", *args, **kwargs):
        if path.name == "controller.log" and mode == "xb":
            raise FileExistsError("other controller won exclusive create")
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", raced_open)
    monkeypatch.setattr(sys, "argv", ["run_v5_continuation.py", "execute", "--plan", str(plan_path), "--detach"])
    with pytest.raises(stage.StageBusy):
        chain.main()
    assert not stopped
