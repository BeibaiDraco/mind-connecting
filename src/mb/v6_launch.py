"""Read-only admission of a separately authorized V6 execution plan.

No provider SDK, credentials, torch, subprocess or network operation is used here.
Private supervisors supply fresh, hash-bound observations; booleans alone are not
accepted as source, budget, guard or backup evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import shutil
import time
from typing import Any

from mb.model_profiles import PROFILES
from mb.v6_contract import canonical_digest
from mb.v6_finance import budget_projection, validate_anchor

ROOT = Path(__file__).resolve().parents[2]
STAGES = frozenset(("acceptance", "smoke", "baseline", "calibration", "validation", "formal"))
PLAN_FIELDS = frozenset(("version", "stage", "model_profile", "n", "material_pin", "runtime",
                        "text_episode_ids", "output_dir", "source_manifest", "prerequisites",
                        "admission_contract_pin"))


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def number(value: Any, name: str, *, positive: bool = False) -> float:
    require(type(value) in (float, int) and math.isfinite(value)
            and (value > 0 if positive else value >= 0), f"Invalid {name}")
    return float(value)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: str | Path) -> dict:
    value = json.loads(Path(path).read_text())
    require(type(value) is dict, "Expected a JSON object")
    canonical_digest(value)
    return value


def pin_value(pin: dict, *, root: Path | None = None, evidence_dir: Path | None = None,
              require_object: bool = True) -> tuple[Path, Any]:
    require(type(pin) is dict and set(pin) == {"path", "sha256"}, "Invalid evidence pin")
    path = Path(pin["path"]) if evidence_dir is None else evidence_dir/(pin["sha256"]+".json")
    if evidence_dir is None and not path.is_absolute():
        require(root is not None, "Evidence paths must be absolute")
        path = root / path
    require(path.is_file() and not path.is_symlink(), "Evidence file unavailable or aliased")
    require(file_sha256(path) == pin["sha256"], "Pinned evidence changed")
    if require_object:
        return path, read(path)
    value = json.loads(path.read_text())
    canonical_digest(value)
    return path, value


def check_source(manifest: dict[str, str]) -> str:
    from mb.v6_run import source_manifest

    require(type(manifest) is dict and manifest == source_manifest(), "Execution source differs")
    for name, sha in manifest.items():
        path = ROOT / name
        require(not Path(name).is_absolute() and ".." not in Path(name).parts
                and not path.is_symlink() and file_sha256(path) == sha, "Invalid source identity")
    return canonical_digest(manifest)


def validate_execution(plan_path: str | Path, admission_path: str | Path, *,
                       now: float | None = None, evidence_dir: str | Path | None = None) -> dict:
    """Verify immutable source/approval and fresh exact-instance observations.

    The supervisor must regenerate the admission envelope as evidence ages.
    A successful call is permission to attempt this stage, not scientific success.
    """
    require(evidence_dir is None or now is not None, "Historical audit requires its recorded launch time")
    evidence = None if evidence_dir is None else Path(evidence_dir)
    current = time.time() if now is None else number(now, "now")
    def pinned(pin: dict, **kwargs: Any) -> tuple[Path, Any]:
        return pin_value(pin, evidence_dir=evidence, **kwargs)
    plan_file, proof_file = Path(plan_path).resolve(), Path(admission_path).resolve()
    plan, proof = read(plan_file), read(proof_file)
    require(set(plan) == PLAN_FIELDS and plan["version"] == "v6-native-stage-1", "Invalid V6 stage plan")
    require(plan["stage"] in STAGES and plan["model_profile"] in PROFILES, "Unknown V6 stage/profile")
    require(type(plan["n"]) is int and plan["n"] > 0, "Positive fixed sample count required")
    source_sha = check_source(plan["source_manifest"])
    pinned(plan["admission_contract_pin"], root=ROOT)
    pinned(plan["material_pin"], require_object=False)
    # The stage-specific collector validates complete contents and stage identity.
    require(type(plan["prerequisites"]) is dict, "Stage prerequisites must be pinned")
    for pin in plan["prerequisites"].values():
        pinned(pin)
    require(type(plan["text_episode_ids"]) is list
            and all(type(x) is str for x in plan["text_episode_ids"])
            and len(set(plan["text_episode_ids"])) == len(plan["text_episode_ids"]), "Invalid text subset")
    require(type(plan["runtime"]) is dict, "Runtime contract missing")
    output = Path(plan["output_dir"])
    require(output.is_absolute() and not output.is_symlink(), "Output must be an explicit absolute directory")
    # Verify actual local tokenizer bytes without importing torch or loading weights.
    PROFILES[plan["model_profile"]].validate_manifest()

    required = {"version", "plan_sha256", "authorization_pin", "instance_binding_sha256",
                "issued_at_epoch", "expires_at_epoch", "phase", "budget", "budget_anchor_pin",
                "local_guard_pin", "remote_guard_pin", "backup_pin", "storage_pin",
                "projection_pin"}
    require(set(proof) == required and proof["version"] == "v6-execution-admission-1", "Invalid admission envelope")
    plan_sha = canonical_digest(plan)
    require(proof["plan_sha256"] == plan_sha, "Admission names another stage plan")
    issued, expiry = proof["issued_at_epoch"], proof["expires_at_epoch"]
    number(issued, "issued_at_epoch"); number(expiry, "expires_at_epoch")
    require(issued <= current < expiry <= issued + 300, "Execution admission is expired or future-dated")
    binding = proof["instance_binding_sha256"]
    require(type(binding) is str and len(binding) == 64
            and all(c in "0123456789abcdef" for c in binding), "Missing exact instance binding")
    auth_file, auth = pinned(proof["authorization_pin"])
    require(auth.get("version") == "v6-approval-1" and auth.get("approved") is True,
            "PI approval is absent")
    require(auth.get("admission_contract_sha256") == plan["admission_contract_pin"]["sha256"]
            and auth.get("source_manifest_sha256") == source_sha, "Approval names another scientific/source package")
    _, prepared = pinned(auth.get("prepared_package_pin"))
    require(prepared.get("version") == "v6-prepared-package-1"
            and prepared.get("source_manifest") == plan["source_manifest"]
            and prepared.get("admission_contract_pin", {}).get("sha256")
            == plan["admission_contract_pin"]["sha256"], "Prepared package differs from approved source/contract")
    entries = prepared.get("materials", {}).get(plan["model_profile"], {})
    require(type(entries) is dict, "Prepared material catalog missing")
    matches = [entry for entry in entries.values() if entry.get("stage") == plan["stage"]
               and entry.get("material_pin", {}).get("sha256") == plan["material_pin"]["sha256"]]
    require(len(matches) == 1, "Material cohort is outside the approved fixed package")
    entry = matches[0]
    require(entry.get("n") == plan["n"]
            and entry.get("text_episode_ids") == plan["text_episode_ids"], "Approved sample count/text subset changed")
    expected_runtime = prepared.get("runtime")
    require(type(expected_runtime) is dict and set(plan["runtime"]) == set(expected_runtime) | {"gain"}
            and all(plan["runtime"][key] == value for key, value in expected_runtime.items()),
            "Runtime clock/labels differ from the approved package")
    gain = plan["runtime"]["gain"]
    require((entry.get("gain") is not None and gain == entry["gain"])
            or (entry.get("gain") is None and plan["stage"] in ("validation", "formal")
                and gain in (.25, .5, 1.)), "Gain is outside the approved stage candidates")
    require(plan["stage"] in auth.get("allowed_stages", [])
            and plan["model_profile"] in auth.get("allowed_models", []), "Stage exceeds approved scope")
    number(auth.get("approved_at_epoch"), "approved_at_epoch")
    require(auth["approved_at_epoch"] <= current and bool(auth.get("evidence_note")), "Approval evidence missing")
    for k in ("total_cap_usd", "initial_cap_usd", "hourly_cap_usd"):
        number(auth.get(k), k, positive=True)

    _, anchor = pinned(proof["budget_anchor_pin"])
    budget = proof["budget"]
    require(type(budget) is dict and type(anchor.get("budget")) is dict, "Budget anchor missing")
    immutable = set(budget) - {"accrued_bandwidth_usd"}
    require(set(anchor["budget"]) == set(budget)
            and all(budget[k] == anchor["budget"][k] for k in immutable), "Financial start/cap was reset")
    require(anchor.get("authorization_sha256") == file_sha256(auth_file)
            and anchor.get("instance_binding_sha256") == binding, "Budget anchor has another authority/instance")
    require(budget["accrued_bandwidth_usd"] >= anchor["budget"]["accrued_bandwidth_usd"], "Bandwidth charge cannot decrease")
    require(budget["total_cap_usd"] <= auth.get("total_cap_usd", 0)
            and budget["initial_cap_usd"] <= auth.get("initial_cap_usd", 0)
            and budget["hourly_cap_usd"] <= auth.get("hourly_cap_usd", 0), "Financial scope exceeds PI approval")
    validate_anchor(anchor, lambda pin: pinned(pin)[1],
                    authorization_sha256=file_sha256(auth_file),
                    instance_binding_sha256=binding, now=current)
    if "reconciliation" not in budget:
        require(budget["started_at_epoch"] >= auth["approved_at_epoch"], "Budget start predates V6 approval")
    expected_phase = "initial" if plan["stage"] in ("acceptance", "smoke") else "full"
    require(proof["phase"] == expected_phase, "Stage cannot bypass its initial or full financial phase")
    remaining = budget_projection(budget, now=current, phase=proof["phase"])

    for role in ("local", "remote"):
        _, guard = pinned(proof[f"{role}_guard_pin"])
        require(guard.get("version") == "v6-guard-proof-1" and guard.get("role") == role
                and guard.get("alive") is True and guard.get("identity_verified") is True,
                "Live identified dual budget guards required")
        require(guard.get("budget_anchor_sha256") == proof["budget_anchor_pin"]["sha256"]
                and guard.get("instance_binding_sha256") == binding, "Guard protects another budget/instance")
        number(guard.get("observed_at_epoch"), "guard observed_at_epoch")
        require(0 <= current-guard["observed_at_epoch"] <= 90, "Guard observation is stale")
        require(type(guard.get("pid")) is int and guard["pid"] > 0
                and bool(guard.get("process_identity_sha256")), "Guard process identity missing")
        number(guard.get("stop_deadline_epoch"), "guard stop_deadline_epoch")
        require(current < guard["stop_deadline_epoch"] <= remaining["effective_deadline_epoch"],
                "Guard deadline exceeds the active financial phase")

    _, backup = pinned(proof["backup_pin"])
    require(backup.get("version") == "v6-backup-proof-1" and backup.get("verified") is True
            and backup.get("source_manifest_sha256") == source_sha
            and backup.get("instance_binding_sha256") == binding, "Verified backup prerequisite missing")
    require(type(backup.get("inventory_sha256")) is str and len(backup["inventory_sha256"]) == 64,
            "Backup inventory digest missing")
    number(backup.get("observed_at_epoch"), "backup observed_at_epoch")
    require(0 <= current-backup["observed_at_epoch"] <= 900, "Backup observation is stale")

    _, storage = pinned(proof["storage_pin"])
    require(storage.get("version") == "v6-storage-proof-1"
            and storage.get("instance_binding_sha256") == binding
            and storage.get("backup_mounted") is True, "Storage/mount evidence missing")
    number(storage.get("observed_at_epoch"), "storage observed_at_epoch")
    require(0 <= current-storage["observed_at_epoch"] <= 300, "Storage observation is stale")
    for side in ("remote", "backup"):
        free = number(storage.get(f"{side}_free_bytes"), f"{side}_free_bytes")
        needed = number(storage.get(f"{side}_required_bytes"), f"{side}_required_bytes", positive=True)
        require(free >= needed, f"Insufficient {side} disk reservation")
    if evidence is None:
        parent = output
        while not parent.exists():
            parent = parent.parent
        require(shutil.disk_usage(parent).free >= storage["remote_required_bytes"], "Actual execution disk is insufficient")

    projection = 0.0
    if proof["phase"] == "full":
        _, forecast = pinned(proof["projection_pin"])
        require(forecast.get("version") == "v6-measured-projection-1"
                and forecast.get("source_manifest_sha256") == source_sha
                and forecast.get("instance_binding_sha256") == binding
                and forecast.get("whole_approved_remaining_work") is True,
                "Measured remaining-work cost forecast required")
        require(bool(forecast.get("timing_evidence_sha256")), "Measured timing source missing")
        projection = number(forecast.get("remaining_seconds"), "remaining_seconds", positive=True)
    else:
        require(proof["projection_pin"] is None, "Initial stage cannot claim a formal throughput forecast")
    budget_projection(budget, now=current, phase=proof["phase"], projected_seconds=projection)
    return {**plan, "plan_sha256": plan_sha,
            "_admission": {"authorization_sha256": file_sha256(auth_file),
                           "source_manifest_sha256": source_sha,
                           "admission_contract_sha256": plan["admission_contract_pin"]["sha256"],
                           "admission_path": str(proof_file), "plan_path": str(plan_file),
                           "historical_only": evidence is not None or now is not None,
                           "validated_at_epoch": current}}
