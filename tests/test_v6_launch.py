import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mb import v6_launch as launch
from mb.v6_contract import canonical_digest


@pytest.fixture
def package(tmp_path, monkeypatch):
    def save(name, value):
        path = tmp_path/(name+".json")
        path.write_text(json.dumps(value, sort_keys=True))
        return {"path": str(path), "sha256": launch.file_sha256(path)}
    src = tmp_path/"module.py"
    src.write_text("# frozen fixture\n")
    source = {src.name: launch.file_sha256(src)}
    monkeypatch.setattr(launch, "ROOT", tmp_path)
    import mb.v6_run
    monkeypatch.setattr(mb.v6_run, "source_manifest", lambda: source)
    monkeypatch.setattr(launch, "PROFILES", {"profile": SimpleNamespace(validate_manifest=lambda: {})})
    monkeypatch.setattr(launch.shutil, "disk_usage", lambda p: SimpleNamespace(free=10000))
    monkeypatch.setattr(launch.time, "time", lambda: 1000)
    plan = {"version": "v6-native-stage-1", "stage": "smoke", "model_profile": "profile", "n": 1,
            "material_pin": save("materials", [{"episode_id": "synthetic-test-only"}]),
            "runtime": {"gain": .5}, "text_episode_ids": [], "output_dir": str(tmp_path/"output"),
            "source_manifest": source, "prerequisites": {},
            "admission_contract_pin": save("contract", {"status": "test-only-proposal"})}
    auth = {"version": "v6-approval-1", "approved": True, "approved_at_epoch": 800,
            "evidence_note": "unit-test fixture; never execution authorization",
            "admission_contract_sha256": plan["admission_contract_pin"]["sha256"],
            "source_manifest_sha256": canonical_digest(source), "allowed_stages": ["smoke", "formal"],
            "allowed_models": ["profile"], "total_cap_usd": 100, "initial_cap_usd": 12, "hourly_cap_usd": 1.6}
    prepared = {"version": "v6-prepared-package-1", "source_manifest": source,
                "admission_contract_pin": plan["admission_contract_pin"], "runtime": {},
                "materials": {"profile": {stage: {"stage": stage, "n": 1,
                    "gain": .5 if stage == "smoke" else None,
                    "material_pin": plan["material_pin"], "text_episode_ids": []}
                    for stage in ("smoke", "formal")}}}
    auth["prepared_package_pin"] = save("prepared", prepared)
    auth_pin = save("approval", auth)
    budget = {"session_id": "v6-test", "started_at_epoch": 900, "total_cap_usd": 100,
              "initial_cap_usd": 12, "hourly_cap_usd": 1.6, "bandwidth_reserve_usd": .5,
              "prior_spend_usd": 0, "accrued_bandwidth_usd": 0,
              "shutdown_reserve_seconds": 300, "hard_deadline_epoch": 3000}
    binding = "a"*64
    anchor = {"budget": budget, "authorization_sha256": auth_pin["sha256"],
              "instance_binding_sha256": binding}
    anchor_pin = save("anchor", anchor)
    proof = {"version": "v6-execution-admission-1", "plan_sha256": canonical_digest(plan),
             "authorization_pin": auth_pin, "instance_binding_sha256": binding,
             "issued_at_epoch": 1000, "expires_at_epoch": 1200, "phase": "initial",
             "budget": copy.deepcopy(budget), "budget_anchor_pin": anchor_pin, "projection_pin": None}
    for role in ("local", "remote"):
        proof[role+"_guard_pin"] = save(role+"_guard", {"version": "v6-guard-proof-1", "role": role,
            "alive": True, "identity_verified": True, "budget_anchor_sha256": anchor_pin["sha256"],
            "instance_binding_sha256": binding, "observed_at_epoch": 1000, "pid": 1,
            "process_identity_sha256": "b"*64, "stop_deadline_epoch": 3000})
    proof["backup_pin"] = save("backup", {"version": "v6-backup-proof-1", "verified": True,
        "source_manifest_sha256": canonical_digest(source), "instance_binding_sha256": binding,
        "inventory_sha256": "c"*64, "observed_at_epoch": 1000})
    proof["storage_pin"] = save("storage", {"version": "v6-storage-proof-1",
        "instance_binding_sha256": binding, "backup_mounted": True, "observed_at_epoch": 1000,
        "remote_free_bytes": 100, "remote_required_bytes": 50, "backup_free_bytes": 100,
        "backup_required_bytes": 50})
    plan_path = Path(save("plan", plan)["path"])
    proof_path = Path(save("admission", proof)["path"])
    return SimpleNamespace(plan=plan, proof=proof, plan_path=plan_path, proof_path=proof_path,
                           save=save, root=tmp_path, auth=auth, anchor=anchor)


def validate(p, *, now=1000, **kwargs):
    p.plan_path.write_text(json.dumps(p.plan, sort_keys=True))
    p.proof["plan_sha256"] = canonical_digest(p.plan)
    p.proof_path.write_text(json.dumps(p.proof, sort_keys=True))
    return launch.validate_execution(p.plan_path, p.proof_path, now=now, **kwargs)


def test_admission_is_read_only_and_accepts_neutral_list(package):
    p = package
    before = {x.name: x.read_bytes() for x in p.root.iterdir() if x.is_file()}
    admitted = launch.validate_execution(p.plan_path, p.proof_path)
    assert admitted["_admission"]["historical_only"] is False
    assert admitted["plan_sha256"] == canonical_digest(p.plan)
    assert before == {x.name: x.read_bytes() for x in p.root.iterdir() if x.is_file()}
    assert not (p.root/"output").exists()


@pytest.mark.parametrize("case", ["source", "approval", "phase", "anchor", "instance", "guard", "disk", "budget"])
def test_invalid_admission_never_creates_output(package, case):
    p = package
    if case == "source":
        (p.root/"module.py").write_text("# altered\n")
    elif case == "approval":
        p.auth["approved"] = False
        p.proof["authorization_pin"] = p.save("approval-denied", p.auth)
    elif case == "phase":
        p.proof["phase"] = "full"
    elif case == "anchor":
        p.proof["budget"]["started_at_epoch"] += 50
    elif case == "instance":
        p.proof["instance_binding_sha256"] = "d"*64
    elif case == "guard":
        g = launch.read(p.proof["remote_guard_pin"]["path"])
        g["stop_deadline_epoch"] = 100000
        p.proof["remote_guard_pin"] = p.save("guard-too-late", g)
    elif case == "disk":
        s = launch.read(p.proof["storage_pin"]["path"])
        s["backup_free_bytes"] = 1
        p.proof["storage_pin"] = p.save("disk-full", s)
    elif case == "budget":
        p.proof["budget"]["accrued_bandwidth_usd"] = 12
    with pytest.raises(ValueError):
        validate(p)
    assert not (p.root/"output").exists()


@pytest.mark.parametrize("now", [999, 1091, 1200])
def test_future_stale_or_expired_evidence_fails(package, now):
    with pytest.raises(ValueError):
        validate(package, now=now)


def test_full_stage_needs_whole_remaining_measured_forecast(package):
    p = package
    p.plan["stage"], p.proof["phase"] = "formal", "full"
    with pytest.raises((ValueError, TypeError)):
        validate(p)
    forecast = {"version": "v6-measured-projection-1",
        "source_manifest_sha256": canonical_digest(p.plan["source_manifest"]),
        "instance_binding_sha256": p.proof["instance_binding_sha256"],
        "whole_approved_remaining_work": True, "timing_evidence_sha256": "e"*64,
        "remaining_seconds": 1000}
    p.proof["projection_pin"] = p.save("forecast", forecast)
    assert validate(p)["stage"] == "formal"
    forecast["remaining_seconds"] = 2500
    p.proof["projection_pin"] = p.save("forecast-too-slow", forecast)
    with pytest.raises(ValueError, match="cannot contain"):
        validate(p)


def test_historical_proofs_retain_bytes_and_cannot_be_launch_permission(package, monkeypatch):
    p = package
    archive = p.root/"history"; archive.mkdir()
    for file in list(p.root.glob("*.json")):
        (archive/(launch.file_sha256(file)+".json")).write_bytes(file.read_bytes())
    Path(p.proof["local_guard_pin"]["path"]).write_text("{}")
    monkeypatch.setattr(launch.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    historical = launch.validate_execution(p.plan_path, p.proof_path, now=1000, evidence_dir=archive)
    assert historical["_admission"]["historical_only"] is True
    with pytest.raises(ValueError):
        launch.validate_execution(p.plan_path, p.proof_path, now=1000)
    with pytest.raises(ValueError, match="recorded launch time"):
        launch.validate_execution(p.plan_path, p.proof_path, evidence_dir=archive)


def test_budget_uses_original_anchor_and_reserves_shutdown(package):
    budget = package.proof["budget"]
    early = launch.budget_projection(budget, now=1000, phase="initial")
    later = launch.budget_projection(budget, now=2000, phase="initial")
    assert later["estimated_spend_usd"] > early["estimated_spend_usd"]
    assert later["remaining_seconds"] < early["remaining_seconds"]
    with pytest.raises(ValueError):
        launch.budget_projection(budget, now=3000, phase="initial")


@pytest.mark.parametrize("change", ["cohort", "n", "text", "clock", "gain"])
def test_fixed_prepared_package_rejects_unapproved_changes(package, change):
    p = package
    if change == "cohort":
        p.plan["material_pin"] = p.save("replacement", [{"episode_id": "replacement"}])
    elif change == "n":
        p.plan["n"] = 2
    elif change == "text":
        p.plan["text_episode_ids"] = ["replacement"]
    elif change == "clock":
        p.plan["runtime"]["work_tokens"] = 63
    elif change == "gain":
        p.plan["runtime"]["gain"] = .25
    with pytest.raises(ValueError):
        validate(p)


def test_unverified_recovery_cannot_bypass_original_approval_time(package):
    p = package
    p.auth["approved_at_epoch"] = 950
    p.auth["initial_cap_usd"] = 25
    p.proof["authorization_pin"] = p.save("new-execution-approval", p.auth)
    budget = p.proof["budget"]
    budget["initial_cap_usd"] = 25
    budget["reconciliation"] = {"version": "v6-cost-checkpoint-1", "checkpoint_epoch": 990,
        "compute_storage_upper_usd": 1, "other_obligations_usd": 0,
        "verified_stopped_seconds": 10, "original_hard_deadline_epoch": 3000,
        "host_end_epoch": 4000}
    p.anchor.update(version="v6-budget-recovery-1", budget=copy.deepcopy(budget),
                    authorization_sha256=p.proof["authorization_pin"]["sha256"])
    p.proof["budget_anchor_pin"] = p.save("forged-recovery", p.anchor)
    with pytest.raises(ValueError, match="Recovery authority chain incomplete"):
        validate(p)
    assert not (p.root / "output").exists()


def test_verified_financial_recovery_admits_new_source_approval_without_backdating(package):
    p = package
    original_auth_pin = copy.deepcopy(p.proof["authorization_pin"])
    original_anchor_pin = copy.deepcopy(p.proof["budget_anchor_pin"])
    # The original synthetic budget has a smaller reserve; recovery cannot
    # weaken its history, so this separate fixture starts with the real reserve.
    p.anchor["budget"]["bandwidth_reserve_usd"] = 3
    original_anchor_pin = p.save("original-anchor-reserved", p.anchor)
    p.auth.update(approved_at_epoch=950, initial_cap_usd=25)
    p.proof["authorization_pin"] = p.save("new-source-approval", p.auth)
    amendment = {"version": "v6-financial-amendment-1", "approved": True,
        "approved_at_epoch": 960, "original_anchor_sha256": original_anchor_pin["sha256"],
        "original_authorization_sha256": original_auth_pin["sha256"],
        "instance_binding_sha256": p.proof["instance_binding_sha256"],
        "initial_cap_usd": 25, "total_cap_usd": 100, "hourly_cap_usd": 1.6,
        "include_all_prior_charges": True, "extend_only_verified_stopped_time": True,
        "evidence_note": "synthetic amended budget; no live authority"}
    ledger = {"version": "v6-cost-ledger-1", "instance_binding_sha256": p.proof["instance_binding_sha256"],
        "original_anchor_sha256": original_anchor_pin["sha256"], "started_at_epoch": 900,
        "checkpoint_epoch": 990, "intervals": [
            {"start_epoch": 900, "end_epoch": 990, "kind": "unknown", "stopped_bound_pin": None}],
        "known_posted_total_usd": 1, "other_obligations_usd": 0, "accrued_bandwidth_usd": 0,
        "host_end_epoch": 4000, "billing_evidence_pins": [p.save("billing", {"synthetic": True})]}
    budget = {**copy.deepcopy(p.anchor["budget"]), "initial_cap_usd": 25,
        "reconciliation": {"version": "v6-cost-checkpoint-1", "checkpoint_epoch": 990,
            "compute_storage_upper_usd": 1, "other_obligations_usd": 0,
            "verified_stopped_seconds": 0, "original_hard_deadline_epoch": 3000,
            "host_end_epoch": 4000}}
    anchor = {"version": "v6-budget-recovery-1", "budget": budget,
        "authorization_sha256": p.proof["authorization_pin"]["sha256"],
        "instance_binding_sha256": p.proof["instance_binding_sha256"],
        "recovery": {"original_anchor_pin": original_anchor_pin, "original_authorization_pin": original_auth_pin,
                     "amendment_pin": p.save("amendment", amendment), "ledger_pin": p.save("ledger", ledger)}}
    p.proof["budget_anchor_pin"] = p.save("valid-recovery", anchor)
    p.proof["budget"] = copy.deepcopy(budget)
    for role in ("local", "remote"):
        guard = launch.read(p.proof[role + "_guard_pin"]["path"])
        guard["budget_anchor_sha256"] = p.proof["budget_anchor_pin"]["sha256"]
        p.proof[role + "_guard_pin"] = p.save(role + "-recovery-guard", guard)
    assert validate(p)["stage"] == "smoke"
    assert budget["started_at_epoch"] == 900 < p.auth["approved_at_epoch"]
    assert not (p.root / "output").exists()
