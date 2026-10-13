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
