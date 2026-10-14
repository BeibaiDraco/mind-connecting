"""No cloud calls: financial bounds and provenance failure cases."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mb import v6_finance as finance


@pytest.fixture
def recovery(tmp_path):
    def save(name, value):
        path = tmp_path / (name + ".json")
        raw = json.dumps(value, sort_keys=True, allow_nan=False).encode()
        path.write_bytes(raw)
        return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}

    binding = "a" * 64
    auth = {"version": "v6-approval-1", "approved": True, "approved_at_epoch": 900,
            "evidence_note": "synthetic financial fixture", "total_cap_usd": 100,
            "initial_cap_usd": 12, "hourly_cap_usd": 1.6}
    auth_pin = save("old-auth", auth)
    old_budget = {"session_id": "v6-test", "started_at_epoch": 1000,
        "total_cap_usd": 100, "initial_cap_usd": 12, "hourly_cap_usd": 1.6,
        "bandwidth_reserve_usd": 3, "prior_spend_usd": 1, "accrued_bandwidth_usd": .1,
        "shutdown_reserve_seconds": 300, "hard_deadline_epoch": 210000}
    old = {"version": "v6-budget-anchor-1", "budget": old_budget,
           "authorization_sha256": auth_pin["sha256"], "instance_binding_sha256": binding}
    old_pin = save("old-anchor", old)
    amendment = {"version": "v6-financial-amendment-1", "approved": True,
        "approved_at_epoch": 39500, "original_anchor_sha256": old_pin["sha256"],
        "original_authorization_sha256": auth_pin["sha256"], "instance_binding_sha256": binding,
        "initial_cap_usd": 25, "total_cap_usd": 100, "hourly_cap_usd": 1.6,
        "include_all_prior_charges": True, "extend_only_verified_stopped_time": True,
        "evidence_note": "synthetic PI amendment"}
    raw_pin = save("raw-evidence", {"fixture": "synthetic; not operational evidence"})
    bound = {"version": "v6-stopped-bound-evidence-1", "method": "corroborated_controlled_stop",
        "issuer_id": "issuer", "instance_binding_sha256": binding,
        "interval_start_epoch": 2000, "interval_end_epoch": 39000,
        "stopped_seconds_lower_bound": 33300, "storage_hourly_upper_usd": .25,
        "observations": {"stop_confirmed_at_epoch": 2040, "latest_stopped_at_epoch": 39000,
            "gpu_billed_hours_before": .22, "gpu_billed_hours_after": .22,
            "runtime_uncertainty_seconds": 3660, "local_start_requests_between": 0,
            "storage_rate_upper_covers_interval": True,
            "inference_limitations": "Corroboration, not official provider transition history."},
        "source_pins": {key: raw_pin for key in ("stop_receipt", "stopped_snapshot", "billing_before",
                        "billing_after", "control_history", "rate_coverage")}}
    review = {"version": "v6-stopped-bound-review-1", "accepted": True,
        "reviewer_id": "independent", "evidence_body_sha256": finance.digest(bound),
        "reviewed_at_epoch": 39600, "rationale": "Synthetic fixture bounds checked."}
    bound["independent_review_pin"] = save("review", review)
    ledger = {"version": "v6-cost-ledger-1", "instance_binding_sha256": binding,
        "original_anchor_sha256": old_pin["sha256"], "started_at_epoch": 1000,
        "checkpoint_epoch": 40000, "intervals": [
            {"start_epoch": 1000, "end_epoch": 2000, "kind": "running", "stopped_bound_pin": None},
            {"start_epoch": 2000, "end_epoch": 39000, "kind": "corroborated_stop", "stopped_bound_pin": save("bound", bound)},
            {"start_epoch": 39000, "end_epoch": 40000, "kind": "unknown", "stopped_bound_pin": None}],
        "known_posted_total_usd": 6, "other_obligations_usd": .2, "accrued_bandwidth_usd": .1,
        "host_end_epoch": 300000, "billing_evidence_pins": [raw_pin]}
    budget = {**old_budget, "initial_cap_usd": 25, "hard_deadline_epoch": 243300,
        "reconciliation": {"version": "v6-cost-checkpoint-1", "checkpoint_epoch": 40000,
            "compute_storage_upper_usd": 6, "other_obligations_usd": .2,
            "verified_stopped_seconds": 33300, "original_hard_deadline_epoch": 210000,
            "host_end_epoch": 300000}}
    anchor = {"version": "v6-budget-recovery-1", "authorization_sha256": "b"*64,
        "instance_binding_sha256": binding, "budget": budget,
        "recovery": {"original_anchor_pin": old_pin, "original_authorization_pin": auth_pin,
                     "amendment_pin": save("amendment", amendment), "ledger_pin": save("ledger", ledger)}}
    return SimpleNamespace(anchor=anchor, old=old, auth=auth, bound=bound, review=review,
                           ledger=ledger, amendment=amendment, save=save)


def validate(case):
    return finance.validate_anchor(case.anchor, authorization_sha256="b"*64,
                                   instance_binding_sha256="a"*64, now=40100)


def repin(case, name):
    if name in ("ledger", "amendment"):
        case.anchor["recovery"][name + "_pin"] = case.save(name + "-changed", getattr(case, name))
    elif name == "bound":
        body = {k: v for k, v in case.bound.items() if k != "independent_review_pin"}
        case.review["evidence_body_sha256"] = finance.digest(body)
        case.bound["independent_review_pin"] = case.save("review-changed", case.review)
        case.ledger["intervals"][1]["stopped_bound_pin"] = case.save("bound-changed", case.bound)
        repin(case, "ledger")


def test_recovery_preserves_start_charges_stopped_disk_and_future_wall_time(recovery):
    assert validate(recovery) == {"initial_cap_usd": 25, "total_cap_usd": 100, "hourly_cap_usd": 1.6}
    budget = recovery.anchor["budget"]
    first = finance.budget_projection(budget, now=40000, phase="initial")
    later = finance.budget_projection(budget, now=43600, phase="initial")
    assert first["estimated_spend_usd"] == pytest.approx(9.2)
    assert later["estimated_spend_usd"] == pytest.approx(10.8)
    assert first["effective_deadline_epoch"] == pytest.approx(later["effective_deadline_epoch"])
    assert budget["started_at_epoch"] == 1000


def test_module_imports_standalone_without_package(tmp_path):
    path = tmp_path / "finance.py"
    path.write_bytes(Path(finance.__file__).read_bytes())
    spec = importlib.util.spec_from_file_location("standalone_finance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.BUDGET_FIELDS == finance.BUDGET_FIELDS


def test_legacy_budget_retains_wall_clock_and_no_amendment_needed(recovery):
    old = recovery.old
    assert finance.validate_anchor(old)["initial_cap_usd"] == 12
    projection = finance.budget_projection(old["budget"], now=4600, phase="initial")
    assert projection["estimated_spend_usd"] == pytest.approx(5.6)
    with pytest.raises(ValueError, match="cannot contain"):
        finance.budget_projection(old["budget"], now=40000, phase="initial")


@pytest.mark.parametrize("field,value", [
    ("session_id", "v6-reset"), ("started_at_epoch", 2000), ("prior_spend_usd", 0),
    ("total_cap_usd", 101), ("hourly_cap_usd", 1.5), ("bandwidth_reserve_usd", 2),
    ("shutdown_reserve_seconds", 0), ("initial_cap_usd", 26), ("hard_deadline_epoch", 243301),
    ("accrued_bandwidth_usd", 0)])
def test_recovery_cannot_reset_history_raise_caps_or_release_reserves(recovery, field, value):
    recovery.anchor["budget"][field] = value
    with pytest.raises(ValueError):
        validate(recovery)


@pytest.mark.parametrize("kind", ["gap", "overlap", "omitted_tail", "wrong_instance", "wrong_original", "no_billing"])
def test_ledger_must_cover_full_original_session(recovery, kind):
    ledger = recovery.ledger
    if kind == "gap":
        ledger["intervals"][1]["start_epoch"] += 1
    elif kind == "overlap":
        ledger["intervals"][1]["start_epoch"] -= 1
    elif kind == "omitted_tail":
        ledger["intervals"].pop()
    elif kind == "wrong_instance":
        ledger["instance_binding_sha256"] = "c"*64
    elif kind == "wrong_original":
        ledger["original_anchor_sha256"] = "c"*64
    else:
        ledger["billing_evidence_pins"] = []
    repin(recovery, "ledger")
    with pytest.raises(ValueError):
        validate(recovery)


@pytest.mark.parametrize("kind", ["endpoints_only", "unreviewed", "same_reviewer", "review_changed_body",
    "increased_gpu_time", "missing_uncertainty", "restored", "free_disk", "rate_not_covered", "missing_raw_pin"])
def test_stop_credit_requires_corroborated_reviewed_bound(recovery, kind):
    bound = recovery.bound
    obs = bound["observations"]
    if kind == "endpoints_only":
        bound["method"] = "two_endpoints"
    elif kind == "same_reviewer":
        recovery.review["reviewer_id"] = bound["issuer_id"]
    elif kind == "increased_gpu_time":
        obs["gpu_billed_hours_after"] += 1
    elif kind == "missing_uncertainty":
        obs.pop("runtime_uncertainty_seconds")
    elif kind == "restored":
        obs["local_start_requests_between"] = 1
    elif kind == "free_disk":
        bound["storage_hourly_upper_usd"] = 0
    elif kind == "rate_not_covered":
        obs["storage_rate_upper_covers_interval"] = False
    elif kind == "missing_raw_pin":
        bound["source_pins"].pop("control_history")
    repin(recovery, "bound")
    if kind in ("unreviewed", "review_changed_body"):
        path = Path(bound["independent_review_pin"]["path"])
        if kind == "unreviewed":
            path.unlink()
        else:
            path.write_text("{}")
    with pytest.raises(ValueError):
        validate(recovery)


@pytest.mark.parametrize("kind", ["posted", "interval", "other", "bandwidth"])
def test_spending_cannot_fall_below_known_or_modeled_obligations(recovery, kind):
    if kind == "posted":
        recovery.ledger["known_posted_total_usd"] = 7
    elif kind == "interval":
        recovery.ledger["known_posted_total_usd"] = 0
        recovery.anchor["budget"]["reconciliation"]["compute_storage_upper_usd"] = 1
    elif kind == "other":
        recovery.ledger["other_obligations_usd"] = 2
    else:
        recovery.ledger["accrued_bandwidth_usd"] = 5
    repin(recovery, "ledger")
    with pytest.raises(ValueError):
        validate(recovery)


def test_host_end_shutdown_and_transfer_growth_bound_both_phases(recovery):
    budget = recovery.anchor["budget"]
    budget["reconciliation"]["host_end_epoch"] = 41000
    assert finance.budget_projection(budget, now=40000, phase="full")["effective_deadline_epoch"] == 40700
    budget["accrued_bandwidth_usd"] = 24
    with pytest.raises(ValueError, match="cannot contain"):
        finance.budget_projection(budget, now=40000, phase="initial")


@pytest.mark.parametrize("kind", ["unapproved", "wrong_original", "exclude_prior", "unbounded_extension", "future"])
def test_explicit_amendment_cannot_be_inferred_from_a_budget(recovery, kind):
    amendment = recovery.amendment
    if kind == "unapproved":
        amendment["approved"] = False
    elif kind == "wrong_original":
        amendment["original_anchor_sha256"] = "c"*64
    elif kind == "exclude_prior":
        amendment["include_all_prior_charges"] = False
    elif kind == "unbounded_extension":
        amendment["extend_only_verified_stopped_time"] = False
    else:
        amendment["approved_at_epoch"] = 50000
    repin(recovery, "amendment")
    with pytest.raises(ValueError):
        validate(recovery)


def test_forged_recovery_cannot_use_old_anchor_shape(recovery):
    recovery.anchor.pop("version")
    with pytest.raises(ValueError, match="recovery authority"):
        validate(recovery)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, -1])
def test_invalid_numbers_rejected(recovery, value):
    recovery.anchor["budget"]["reconciliation"]["compute_storage_upper_usd"] = value
    with pytest.raises(ValueError):
        validate(recovery)


def test_stop_credit_cannot_be_reused_for_another_restore_interval(recovery):
    tail = recovery.ledger["intervals"][-1]
    tail["kind"] = "corroborated_stop"
    tail["stopped_bound_pin"] = recovery.ledger["intervals"][1]["stopped_bound_pin"]
    repin(recovery, "ledger")
    with pytest.raises(ValueError, match="another interval"):
        validate(recovery)


def test_later_distinct_stopped_interval_does_not_reset_prior_charges(recovery):
    later = copy.deepcopy(recovery.bound)
    later.update(interval_start_epoch=39000, interval_end_epoch=40000, stopped_seconds_lower_bound=500)
    later["observations"].update(stop_confirmed_at_epoch=39000, latest_stopped_at_epoch=40000,
                                 runtime_uncertainty_seconds=500)
    review = copy.deepcopy(recovery.review)
    review.update(reviewed_at_epoch=40000,
                  evidence_body_sha256=finance.digest({k: v for k, v in later.items() if k != "independent_review_pin"}))
    later["independent_review_pin"] = recovery.save("later-review", review)
    recovery.ledger["intervals"][-1].update(kind="corroborated_stop",
                                           stopped_bound_pin=recovery.save("later-stop", later))
    repin(recovery, "ledger")
    recovery.anchor["budget"]["reconciliation"]["verified_stopped_seconds"] = 33800
    assert validate(recovery)["initial_cap_usd"] == 25
    assert finance.budget_projection(recovery.anchor["budget"], now=40000,
                                     phase="initial")["estimated_spend_usd"] == pytest.approx(9.2)
