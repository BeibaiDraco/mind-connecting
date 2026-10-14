"""Pure cumulative V6 finance, also copied byte-for-byte into private guards.

A recovery is an append-only, reviewed accounting checkpoint, not a new spending
session. Old budgets retain their original elapsed-wall-time interpretation.
This module intentionally has no imports from ``mb`` or third-party packages.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

BUDGET_FIELDS = frozenset({"session_id", "started_at_epoch", "total_cap_usd", "initial_cap_usd",
    "hourly_cap_usd", "bandwidth_reserve_usd", "prior_spend_usd", "accrued_bandwidth_usd",
    "shutdown_reserve_seconds", "hard_deadline_epoch"})
CHECKPOINT_FIELDS = frozenset({"version", "checkpoint_epoch", "compute_storage_upper_usd",
    "other_obligations_usd", "verified_stopped_seconds", "original_hard_deadline_epoch",
    "host_end_epoch"})
CAP_FIELDS = ("total_cap_usd", "initial_cap_usd", "hourly_cap_usd")
PinLoader = Callable[[dict], dict]


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def number(value: Any, name: str, *, positive: bool = False) -> float:
    require(type(value) in (float, int) and math.isfinite(value)
            and (value > 0 if positive else value >= 0), f"Invalid {name}")
    return float(value)


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def read_pin(pin: dict) -> dict:
    """Read-only default pin resolver; historical audits supply their resolver."""
    require(type(pin) is dict and set(pin) == {"path", "sha256"}, "Invalid finance pin")
    path = Path(pin["path"])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), "Finance evidence unavailable")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin["sha256"], "Finance evidence changed")
    value = json.loads(raw)
    require(type(value) is dict, "Finance evidence must be an object")
    digest(value)
    return value


def _budget(budget: dict) -> dict | None:
    require(type(budget) is dict and set(budget) in (BUDGET_FIELDS, BUDGET_FIELDS | {"reconciliation"}),
            "Incomplete cumulative budget")
    require(type(budget["session_id"]) is str and budget["session_id"].startswith("v6-"),
            "V6 requires an explicit financial session")
    for key in BUDGET_FIELDS - {"session_id"}:
        number(budget[key], key, positive=key in CAP_FIELDS)
    require(budget["initial_cap_usd"] <= budget["total_cap_usd"], "Initial cap exceeds total")
    checkpoint = budget.get("reconciliation")
    if checkpoint is not None:
        require(type(checkpoint) is dict and set(checkpoint) == CHECKPOINT_FIELDS
                and checkpoint["version"] == "v6-cost-checkpoint-1", "Invalid reconciliation checkpoint")
        for key in CHECKPOINT_FIELDS - {"version"}:
            number(checkpoint[key], key)
        require(checkpoint["checkpoint_epoch"] >= budget["started_at_epoch"], "Checkpoint resets financial start")
        require(checkpoint["compute_storage_upper_usd"] >= budget["prior_spend_usd"], "Prior spend disappeared")
        require(checkpoint["verified_stopped_seconds"] <= checkpoint["checkpoint_epoch"] - budget["started_at_epoch"],
                "Stopped duration exceeds elapsed history")
        require(budget["hard_deadline_epoch"] <= checkpoint["original_hard_deadline_epoch"]
                + checkpoint["verified_stopped_seconds"], "Deadline extension exceeds evidenced stop")
    return checkpoint


def budget_projection(budget: dict, *, now: float, phase: str,
                      projected_seconds: float = 0) -> dict[str, float]:
    """Project all future time at the hourly ceiling, even if a stage stops."""
    checkpoint = _budget(budget)
    require(phase in ("initial", "full"), "Unknown spending phase")
    current = number(now, "now")
    seconds = number(projected_seconds, "projected_seconds")
    start = budget["started_at_epoch"] if checkpoint is None else checkpoint["checkpoint_epoch"]
    require(start <= current, "Financial start/checkpoint cannot be in the future")
    base = budget["prior_spend_usd"] if checkpoint is None else (
        checkpoint["compute_storage_upper_usd"] + checkpoint["other_obligations_usd"])
    rate, reserve = budget["hourly_cap_usd"], budget["shutdown_reserve_seconds"]
    spent = base + max(budget["bandwidth_reserve_usd"], budget["accrued_bandwidth_usd"]) + (current-start)*rate/3600
    cap = budget["initial_cap_usd"] if phase == "initial" else budget["total_cap_usd"]
    fixed_charges = base + max(budget["bandwidth_reserve_usd"], budget["accrued_bandwidth_usd"])
    deadline = min(start + (cap-fixed_charges)*3600/rate-reserve, budget["hard_deadline_epoch"])
    if checkpoint is not None:
        deadline = min(deadline, checkpoint["host_end_epoch"]-reserve)
    require(current + seconds < deadline, "Budget or deadline cannot contain planned work and shutdown")
    return {"estimated_spend_usd": spent, "remaining_seconds": deadline-current,
            "effective_deadline_epoch": deadline, "applicable_cap_usd": cap}


def _bound(evidence: dict, *, binding: str, start: float, end: float,
           rate: float, load_pin: PinLoader, now: float | None) -> tuple[float, float]:
    """Validate independently reviewed bounds without inventing provider history.

    The named method is a corroborated operational inference. Its review must
    reference the exact body and inspect the raw stop, billing, rate and local
    control evidence. Two stopped endpoints alone are never sufficient.
    """
    required = {"version", "method", "issuer_id", "instance_binding_sha256", "interval_start_epoch",
        "interval_end_epoch", "stopped_seconds_lower_bound", "storage_hourly_upper_usd", "observations",
        "source_pins", "independent_review_pin"}
    require(type(evidence) is dict and set(evidence) == required
            and evidence["version"] == "v6-stopped-bound-evidence-1"
            and evidence["method"] == "corroborated_controlled_stop", "Unsupported stopped evidence")
    require(evidence["instance_binding_sha256"] == binding
            and evidence["interval_start_epoch"] == start and evidence["interval_end_epoch"] == end,
            "Stopped evidence names another interval or instance")
    stopped = number(evidence["stopped_seconds_lower_bound"], "stopped bound", positive=True)
    storage = number(evidence["storage_hourly_upper_usd"], "stopped storage rate", positive=True)
    require(stopped <= end-start and storage <= rate, "Invalid stopped duration/rate bound")
    obs = evidence["observations"]
    fields = {"stop_confirmed_at_epoch", "latest_stopped_at_epoch", "gpu_billed_hours_before",
              "gpu_billed_hours_after", "runtime_uncertainty_seconds", "local_start_requests_between",
              "storage_rate_upper_covers_interval", "inference_limitations"}
    require(type(obs) is dict and set(obs) == fields, "Stopped corroboration incomplete")
    for key in fields - {"storage_rate_upper_covers_interval", "inference_limitations"}:
        number(obs[key], key)
    require(type(obs["local_start_requests_between"]) is int and obs["local_start_requests_between"] == 0,
            "Restoration exists inside claimed stopped interval")
    require(obs["storage_rate_upper_covers_interval"] is True and bool(obs["inference_limitations"]),
            "Historical storage rate or inference limitations missing")
    require(start <= obs["stop_confirmed_at_epoch"] <= obs["latest_stopped_at_epoch"] <= end,
            "Stopped observations exceed interval")
    require(obs["gpu_billed_hours_after"] >= obs["gpu_billed_hours_before"], "Billed GPU history decreased")
    running = (obs["gpu_billed_hours_after"]-obs["gpu_billed_hours_before"])*3600 + obs["runtime_uncertainty_seconds"]
    available = obs["latest_stopped_at_epoch"]-obs["stop_confirmed_at_epoch"]-running
    require(stopped <= available, "Stopped credit exceeds corroborated conservative duration")
    pins = evidence["source_pins"]
    require(type(pins) is dict and set(pins) == {"stop_receipt", "stopped_snapshot", "billing_before",
            "billing_after", "control_history", "rate_coverage"}, "Concrete stopped evidence pins required")
    for pin in pins.values():
        load_pin(pin)
    review = load_pin(evidence["independent_review_pin"])
    body = {key: value for key, value in evidence.items() if key != "independent_review_pin"}
    require(review.get("version") == "v6-stopped-bound-review-1" and review.get("accepted") is True
            and review.get("evidence_body_sha256") == digest(body)
            and bool(review.get("reviewer_id")) and bool(evidence["issuer_id"])
            and review["reviewer_id"] != evidence["issuer_id"] and bool(review.get("rationale")),
            "Independent exact-body stopped-bound review missing")
    reviewed = number(review.get("reviewed_at_epoch"), "reviewed_at_epoch")
    require(reviewed >= end and (now is None or reviewed <= now), "Stopped review time invalid")
    return stopped, storage


def validate_anchor(anchor: dict, load_pin: PinLoader = read_pin, *,
                    authorization_sha256: str | None = None,
                    instance_binding_sha256: str | None = None,
                    now: float | None = None) -> dict[str, float]:
    """Check old anchors or one explicit recovery against immutable history.

    ``load_pin`` must check content hashes, including in historical audits.
    New execution approval may postdate the original start; the original
    approval and financial anchor remain mandatory, independently pinned facts.
    """
    require(type(anchor) is dict and type(anchor.get("budget")) is dict, "Budget anchor missing")
    if anchor.get("version") == "v6-budget-transfer-1":
        return _validate_transfer_anchor(anchor, load_pin,
            authorization_sha256=authorization_sha256,
            instance_binding_sha256=instance_binding_sha256, now=now)
    budget = anchor["budget"]
    checkpoint = _budget(budget)
    if authorization_sha256 is not None:
        require(anchor.get("authorization_sha256") == authorization_sha256, "Anchor has another authorization")
    if instance_binding_sha256 is not None:
        require(anchor.get("instance_binding_sha256") == instance_binding_sha256, "Anchor has another instance")
    if checkpoint is None:
        require(anchor.get("version") != "v6-budget-recovery-1" and "recovery" not in anchor,
                "Recovery cannot discard reconciliation")
        return {key: budget[key] for key in CAP_FIELDS}
    require(anchor.get("version") == "v6-budget-recovery-1", "Reconciliation requires recovery authority")
    recovery = anchor.get("recovery")
    require(type(recovery) is dict and set(recovery) == {"original_anchor_pin", "original_authorization_pin",
            "amendment_pin", "ledger_pin"}, "Recovery authority chain incomplete")
    original = load_pin(recovery["original_anchor_pin"])
    authorization = load_pin(recovery["original_authorization_pin"])
    amendment = load_pin(recovery["amendment_pin"])
    ledger = load_pin(recovery["ledger_pin"])
    old = original.get("budget")
    require(_budget(old) is None, "Nested recovery cannot erase original history")
    binding = anchor.get("instance_binding_sha256")
    require(original.get("instance_binding_sha256") == binding
            and original.get("authorization_sha256") == recovery["original_authorization_pin"]["sha256"],
            "Original instance/approval does not match")
    require(authorization.get("version") == "v6-approval-1" and authorization.get("approved") is True
            and bool(authorization.get("evidence_note")), "Original approval absent")
    approved = number(authorization.get("approved_at_epoch"), "original approval time")
    require(old["started_at_epoch"] >= approved, "Original start predates approval")
    for key in CAP_FIELDS:
        require(old[key] <= number(authorization.get(key), key, positive=True), "Original budget exceeded approval")
    preserved = BUDGET_FIELDS - {"initial_cap_usd", "hard_deadline_epoch", "accrued_bandwidth_usd"}
    require(all(budget[key] == old[key] for key in preserved), "Financial history or immutable cap reset")
    require(budget["accrued_bandwidth_usd"] >= old["accrued_bandwidth_usd"], "Bandwidth history decreased")
    require(checkpoint["original_hard_deadline_epoch"] == old["hard_deadline_epoch"], "Original deadline reset")
    require(amendment.get("version") == "v6-financial-amendment-1" and amendment.get("approved") is True
            and amendment.get("original_anchor_sha256") == recovery["original_anchor_pin"]["sha256"]
            and amendment.get("original_authorization_sha256") == recovery["original_authorization_pin"]["sha256"]
            and amendment.get("instance_binding_sha256") == binding
            and amendment.get("include_all_prior_charges") is True
            and amendment.get("extend_only_verified_stopped_time") is True
            and bool(amendment.get("evidence_note")), "Explicit PI financial amendment absent or mismatched")
    changed = number(amendment.get("approved_at_epoch"), "amendment approval time")
    require(changed >= approved and (now is None or changed <= now), "Amendment approval time invalid")
    require(budget["initial_cap_usd"] == amendment.get("initial_cap_usd") == 25
            and budget["total_cap_usd"] == amendment.get("total_cap_usd") == 100
            and budget["hourly_cap_usd"] == amendment.get("hourly_cap_usd") == 1.6,
            "Recovery exceeds the explicit USD25/100/1.60 amendment")
    require(budget["bandwidth_reserve_usd"] >= 3 and budget["shutdown_reserve_seconds"] >= 300,
            "Recovery removed original reserves")
    fields = {"version", "instance_binding_sha256", "original_anchor_sha256", "started_at_epoch",
              "checkpoint_epoch", "intervals", "known_posted_total_usd", "other_obligations_usd",
              "accrued_bandwidth_usd", "host_end_epoch", "billing_evidence_pins"}
    require(type(ledger) is dict and set(ledger) == fields and ledger["version"] == "v6-cost-ledger-1"
            and ledger["instance_binding_sha256"] == binding
            and ledger["original_anchor_sha256"] == recovery["original_anchor_pin"]["sha256"]
            and ledger["started_at_epoch"] == old["started_at_epoch"]
            and ledger["checkpoint_epoch"] == checkpoint["checkpoint_epoch"], "Cost ledger identity mismatch")
    end = number(ledger["checkpoint_epoch"], "checkpoint time")
    require(changed <= end and (now is None or end <= now), "Cost checkpoint predates amendment or is future")
    require(type(ledger["billing_evidence_pins"]) is list and ledger["billing_evidence_pins"], "Billing evidence missing")
    for pin in ledger["billing_evidence_pins"]:
        load_pin(pin)
    intervals = ledger["intervals"]
    require(type(intervals) is list and intervals, "Full elapsed-session interval ledger required")
    cursor, modeled, stopped_total = old["started_at_epoch"], old["prior_spend_usd"], 0.0
    for interval in intervals:
        require(type(interval) is dict and set(interval) == {"start_epoch", "end_epoch", "kind", "stopped_bound_pin"},
                "Invalid financial interval")
        left, right = interval["start_epoch"], number(interval["end_epoch"], "interval end")
        require(left == cursor and left < right <= end, "Cost intervals have a gap, overlap or invalid endpoint")
        kind, stopped, storage = interval["kind"], 0.0, 0.0
        require(kind in ("running", "unknown", "corroborated_stop"), "Unknown financial interval kind")
        if kind == "corroborated_stop":
            stopped, storage = _bound(load_pin(interval["stopped_bound_pin"]), binding=binding,
                start=left, end=right, rate=old["hourly_cap_usd"], load_pin=load_pin, now=now)
        else:
            require(interval["stopped_bound_pin"] is None, "Unproven interval cannot subtract stopped time")
        modeled += ((right-left-stopped)*old["hourly_cap_usd"] + stopped*storage)/3600
        stopped_total += stopped
        cursor = right
    require(cursor == end, "Cost ledger omits elapsed time")
    posted = number(ledger["known_posted_total_usd"], "known posted total")
    other = number(ledger["other_obligations_usd"], "other obligations")
    transfers = number(ledger["accrued_bandwidth_usd"], "accrued bandwidth")
    host_end = number(ledger["host_end_epoch"], "host end")
    require(checkpoint["compute_storage_upper_usd"] >= max(modeled, posted), "Recovery undercounts known/interval spending")
    require(checkpoint["other_obligations_usd"] >= other and budget["accrued_bandwidth_usd"] >= transfers,
            "Recovery omits charges or obligations")
    require(checkpoint["verified_stopped_seconds"] <= stopped_total
            and checkpoint["host_end_epoch"] <= host_end, "Recovery exceeds stopped/host bounds")
    return {key: amendment[key] for key in CAP_FIELDS}


TRANSFER_HISTORY_PINS = frozenset({"prior_anchor_pin", "prior_authorization_pin",
                                   "replacement_authorization_pin", "destruction_receipt_pin"})


def _transfer_history(authority: dict, load_pin: PinLoader, *, now: float | None) -> tuple[dict, dict, dict]:
    """A first replacement inherits every dollar and second of the approved anchor."""
    transfer = authority.get("transfer")
    require(type(transfer) is dict and TRANSFER_HISTORY_PINS <= set(transfer), "Replacement history pins missing")
    prior = load_pin(transfer["prior_anchor_pin"])
    prior_auth = load_pin(transfer["prior_authorization_pin"])
    approval = load_pin(transfer["replacement_authorization_pin"])
    destroyed = load_pin(transfer["destruction_receipt_pin"])
    require(prior.get("version") == "v6-budget-recovery-1", "Only the first approved replacement is supported")
    validate_anchor(prior, load_pin, authorization_sha256=transfer["prior_authorization_pin"]["sha256"], now=now)
    require(prior_auth.get("version") == "v6-approval-1" and prior_auth.get("approved") is True,
            "Prior execution approval missing")
    prior_time = number(prior_auth.get("approved_at_epoch"), "prior execution approval time")
    require(authority.get("budget") == prior["budget"], "Replacement changed cumulative budget or deadline")
    require(approval.get("version") == "v6-instance-replacement-approval-1"
            and approval.get("approved") is True and approval.get("preserve_entire_budget") is True
            and type(approval.get("maximum_new_instances")) is int and approval["maximum_new_instances"] == 1
            and approval.get("prior_anchor_sha256") == transfer["prior_anchor_pin"]["sha256"]
            and approval.get("prior_authorization_sha256") == transfer["prior_authorization_pin"]["sha256"]
            and approval.get("old_binding_sha256") == prior["instance_binding_sha256"]
            and bool(approval.get("evidence_note")), "Explicit exact replacement approval missing")
    approved = number(approval.get("approved_at_epoch"), "replacement approval time")
    require(prior_time <= approved and (now is None or approved <= now), "Replacement approval time invalid")
    require(destroyed.get("version") == "v6-old-instance-destroyed-1"
            and destroyed.get("old_binding_sha256") == prior["instance_binding_sha256"]
            and all(destroyed.get(key) is True for key in (
                "api_success", "inventory_complete", "inventory_absent", "destroyed_verified"))
            and destroyed.get("error_type") is None, "Old instance destruction is not confirmed")
    observed = number(destroyed.get("observed_at_epoch"), "destruction observation time")
    require(approved <= observed and (now is None or observed <= now), "Destruction predates approval or is future")
    intent = load_pin(destroyed.get("destroy_intent_pin"))
    backup = load_pin(destroyed.get("backup_rehash_pin"))
    old_binding = load_pin(intent.get("old_binding_pin"))
    require(digest(old_binding) == prior["instance_binding_sha256"]
            and intent.get("old_binding_sha256") == prior["instance_binding_sha256"]
            and intent.get("backup_rehash_sha256") == destroyed["backup_rehash_pin"]["sha256"],
            "Destruction intent names another instance, approval or backup")
    issued = number(intent.get("issued_at_epoch"), "destruction intent time")
    require(approved <= issued <= observed, "Destruction intent time invalid")
    if intent.get("authorization_sha256") != transfer["replacement_authorization_pin"]["sha256"]:
        consent_pin = approval.get("pi_message_pin")
        consent = load_pin(consent_pin)
        require(intent.get("authorization_sha256") == consent_pin["sha256"]
                and consent.get("version") == "v6-pi-replacement-message-1"
                and consent.get("approved") is True and bool(consent.get("message"))
                and bool(consent.get("question_scope")), "Destruction lacks the pinned explicit PI consent")
        recorded = number(consent.get("recorded_at_epoch"), "PI replacement consent time")
        require(recorded <= issued, "PI consent was recorded after destruction intent")
    require(backup.get("version") == "v6-destroy-backup-rehash-1" and backup.get("verified") is True
            and type(backup.get("files")) is int and backup["files"] > 0, "Pre-destruction backup absent")
    return prior, approval, old_binding


def validate_transfer_precreate(authority: dict, load_pin: PinLoader = read_pin, *,
                                authorization_sha256: str | None = None,
                                now: float | None = None) -> dict[str, float]:
    """Admit a protected one-label creation intent before any new instance ID exists.

    This is not worker admission. A final bound anchor additionally needs the
    exact provider creation receipt, new binding and sufficient host duration.
    """
    require(type(authority) is dict and authority.get("version") == "v6-budget-transfer-precreate-1"
            and type(authority.get("transfer")) is dict
            and set(authority["transfer"]) == TRANSFER_HISTORY_PINS
            and "instance_binding_sha256" not in authority, "Invalid replacement precreation authority")
    if authorization_sha256 is not None:
        require(authority.get("authorization_sha256") == authorization_sha256, "Precreation has another approval")
    prior, _, old_binding = _transfer_history(authority, load_pin, now=now)
    label = authority.get("creation_label")
    require(type(label) is str and 1 <= len(label) <= 128
            and all(c.isascii() and (c.isalnum() or c in "_-") for c in label)
            and label != old_binding.get("creation_label"), "Replacement needs a new exact creation label")
    return {key: prior["budget"][key] for key in CAP_FIELDS}


def _validate_transfer_anchor(anchor: dict, load_pin: PinLoader, *,
                              authorization_sha256: str | None,
                              instance_binding_sha256: str | None,
                              now: float | None) -> dict[str, float]:
    transfer = anchor.get("transfer")
    extra = {"precreate_authority_pin", "creation_intent_pin", "new_binding_pin", "creation_receipt_pin"}
    require(type(transfer) is dict and set(transfer) == TRANSFER_HISTORY_PINS | extra,
            "Final replacement authority incomplete")
    if authorization_sha256 is not None:
        require(anchor.get("authorization_sha256") == authorization_sha256, "Replacement has another approval")
    if instance_binding_sha256 is not None:
        require(anchor.get("instance_binding_sha256") == instance_binding_sha256, "Replacement has another binding")
    precreate = load_pin(transfer["precreate_authority_pin"])
    caps = validate_transfer_precreate(precreate, load_pin,
        authorization_sha256=anchor.get("authorization_sha256"), now=now)
    require(anchor.get("budget") == precreate["budget"]
            and all(transfer[key] == precreate["transfer"][key] for key in TRANSFER_HISTORY_PINS),
            "Final replacement reset or substituted creation authority")
    binding = load_pin(transfer["new_binding_pin"])
    intent = load_pin(transfer["creation_intent_pin"])
    receipt = load_pin(transfer["creation_receipt_pin"])
    require(set(binding) == {"version", "provider", "instance_id", "creation_label", "creation_intent_sha256"}
            and binding.get("version") == "v6-instance-binding-1" and binding.get("provider") == "vast"
            and type(binding.get("instance_id")) is int and binding["instance_id"] > 0
            and digest(binding) == anchor.get("instance_binding_sha256")
            and binding.get("creation_label") == precreate["creation_label"]
            and binding.get("creation_intent_sha256") == transfer["creation_intent_pin"]["sha256"],
            "New exact binding does not match the creation intent")
    prior = load_pin(transfer["prior_anchor_pin"])
    require(anchor["instance_binding_sha256"] != prior["instance_binding_sha256"], "Replacement reused old binding")
    require(intent.get("version") == "v6-rental-intent-1"
            and intent.get("creation_label") == precreate["creation_label"]
            and intent.get("precreate_budget_sha256") == transfer["precreate_authority_pin"]["sha256"]
            and intent.get("authorization_sha256") == anchor.get("authorization_sha256"),
            "Creation intent changed financial or execution authority")
    created = number(intent.get("created_at_epoch"), "creation intent time")
    destroyed = load_pin(transfer["destruction_receipt_pin"])
    old_intent = load_pin(destroyed["destroy_intent_pin"])
    old_binding = load_pin(old_intent["old_binding_pin"])
    require(binding["instance_id"] != old_binding.get("instance_id"), "Replacement reused the old instance ID")
    require(created >= destroyed["observed_at_epoch"], "Replacement creation preceded verified destruction")
    require(receipt.get("version") == "v6-replacement-created-1"
            and receipt.get("instance_binding_sha256") == anchor["instance_binding_sha256"]
            and receipt.get("creation_intent_sha256") == transfer["creation_intent_pin"]["sha256"]
            and receipt.get("precreate_authority_sha256") == transfer["precreate_authority_pin"]["sha256"],
            "Creation receipt names another target or authority")
    observed = number(receipt.get("observed_at_epoch"), "creation observation time")
    require(created <= observed and (now is None or observed <= now), "Creation receipt time invalid")
    raw = load_pin(receipt.get("provider_response_pin"))
    require(raw.get("success") is True and str(raw.get("new_contract")) == str(binding["instance_id"]),
            "Provider creation success does not identify the new instance")
    hourly = number(receipt.get("actual_hourly_usd"), "new actual hourly rate", positive=True)
    disk = number(receipt.get("actual_disk_units"), "new actual disk", positive=True)
    require(hourly <= anchor["budget"]["hourly_cap_usd"] and disk >= number(intent.get("disk"), "requested disk", positive=True),
            "Replacement rate or storage exceeds the approved offer")
    host_end = number(receipt.get("host_end_epoch"), "new host end")
    deadline = budget_projection(anchor["budget"], now=observed, phase="full")["effective_deadline_epoch"]
    require(host_end >= deadline + anchor["budget"]["shutdown_reserve_seconds"],
            "Replacement host cannot contain the existing full deadline")
    return caps
