"""Scoring, integrity and inferential counterexamples for the v6 draft analysis."""

import copy
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from mb import v6_analysis as v

SPEC = importlib.util.spec_from_file_location("v6_simulations", Path(__file__).parents[1] / "scripts/v6_simulate_analysis.py")
SIM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SIM)


@pytest.fixture
def data():
    return SIM.synthetic_records(6, mode="alternative")


def endpoint(result, name, model=v.MODELS[0], family="primary"):
    return next(item for item in result[family] if item["model_profile"] == model and item["endpoint"] == name)


def find(records, **fields):
    return next(row for row in records if all(row.get(k) == value for k, value in fields.items()))


def change_choice(row, choice):
    row["choice"] = choice
    row["correct"] = choice == row["correct_choice"]


def test_fixed_candidate_scores_invalid_and_minimum():
    assert [v.signed_choice(c, 0, 1) for c in (0, 1, 2, 3, None)] == [-1, 1, 0, 0, 0]
    assert [v.quality_score(c, 0, 1) for c in (0, 1, 2, 3, None)] == [0, 1, -.5, -.5, 0]
    assert sum(v.quality_score(c, 0, 1) for c in (1, 2, 3)) == 0
    for x, y in itertools.product((-.5, 0, 1), repeat=2):
        assert min(x, y) <= x and min(x, y) <= y
    pairs = [(1, -.5), (-.5, 1)]
    assert np.mean([x for x, _ in pairs]) == np.mean([y for _, y in pairs]) == .25
    assert np.mean([min(x, y) for x, y in pairs]) == -.5


def test_expected_schedule_has_full_pulse_actions_and_diagnostics():
    keys = v.expected_keys("e", v.MODELS[0])
    assert len(keys) == 328
    assert sum(k[2] == "pulse" for k in keys) == 64
    assert sum(k[2] == "goal" for k in keys) == 144
    assert sum(k[2] == "natural" for k in keys) == 120
    assert len(v.expected_keys("e", v.MODELS[0], text=True)) == 352


def test_exact_families_episode_unit_and_error_scale(data):
    records, expected = data
    result = v.analyze(records, expected, n_boot=30)
    assert result["completeness"]["complete"] and not result["consumable"]
    assert result["synthetic_input"] and not result["scientific_source_verified"]
    assert len(result["primary"]) == 22 and len(result["secondary"]) == 4
    assert all(item["n"] == 6 for item in result["primary"] + result["secondary"])
    assert endpoint(result, "pulse2_forward")["mean"] == 1
    assert endpoint(result, "goal_cross")["mean"] == 1
    assert endpoint(result, "goal_return")["mean"] == 1
    assert endpoint(result, "goal_cross_latest_error", family="secondary")["mean"] == 1
    assert endpoint(result, "goal_return_latest_error", family="secondary")["mean"] == -1
    assert all(result["sustained_response"].values())
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("missing", ["deleted", "technical_failure"])
def test_one_missing_required_episode_disables_entire_endpoint_not_complete_case(data, missing):
    records, expected = data
    row = find(records, model_profile=v.MODELS[0], kind="pulse", checkpoint=2,
               arm="Fcut", version=1, round_id=2, side=1)
    if missing == "deleted":
        records.remove(row)
    else:
        row.update(status="technical_failure", choice=None, correct=None)
    result = v.analyze(records, expected, n_boot=20)
    item = endpoint(result, "pulse2_forward")
    assert not result["consumable"] and not item["available"]
    assert item["n_complete"] == 5 and item["n_expected"] == 6
    assert item["n"] is None and item["mean"] is None and item["ci95"] is None
    assert item["p_two_sided"] == item["p_holm"] == 1
    assert endpoint(result, "pulse5_forward")["available"]
    assert not result["sustained_response"][v.MODELS[0]]


def test_invalid_is_observed_failure_not_missing(data):
    records, expected = data
    row = find(records, model_profile=v.MODELS[0], kind="pulse", checkpoint=2,
               arm="L", version=1, round_id=2, side=1)
    change_choice(row, None)
    result = v.analyze(records, expected, n_boot=20)
    assert result["completeness"]["complete"]
    assert endpoint(result, "pulse2_chain_quality")["mean"] == pytest.approx(5 / 6)
    assert endpoint(result, "pulse2_chain_quality")["n"] == 6


def test_missing_nonfeeding_diagnostic_does_not_change_primary_denominator(data):
    records, expected = data
    records.remove(find(records, kind="natural", qid="partner_beacon"))
    result = v.analyze(records, expected, n_boot=20)
    assert not result["consumable"]
    assert all(item["available"] for item in result["primary"])
    assert any(not row["complete"] and row["accuracy"] is None for row in result["descriptive"])


def test_missing_entire_branch_family_preserves_component_episode_alignment(data):
    records, expected = data
    absent = expected[v.MODELS[0]][0]
    records = [row for row in records if not (row["model_profile"] == v.MODELS[0]
               and row["episode_id"] == absent and row["kind"] in ("pulse", "goal"))]
    result = v.analyze(records, expected, n_boot=20)
    scores = result["episode_scores"][v.MODELS[0]]
    assert all(len(values) == 6 and values[0] is None for values in scores["components"].values())
    assert endpoint(result, "live_minus_fresh")["available"]
    assert not endpoint(result, "goal_cross")["available"]


def test_audit_is_json_safe_complete_boolean_and_empty_scope_cannot_pass(data):
    records, expected = data
    audit = v.validate_records(records, expected)
    assert audit["complete"] and audit["consumable"]
    assert audit["ok_records"] == 328 * 12
    json.dumps(audit, allow_nan=False)
    assert not v.validate_records([], {})["complete"]
    assert not v.validate_records([], expected)["complete"]


def test_whole_unavailable_model_keeps_all_family_slots(data):
    records, expected = data
    records = [row for row in records if row["model_profile"] == v.MODELS[0]]
    result = v.analyze(records, expected, n_boot=20)
    absent = [item for item in result["primary"] if item["model_profile"] == v.MODELS[1]]
    assert len(absent) == 11 and all(item["p_holm"] == 1 and not item["available"] for item in absent)
    absent_declared = v.analyze(records, {v.MODELS[0]: expected[v.MODELS[0]]}, n_boot=20)
    assert len(absent_declared["primary"]) == 22 and not absent_declared["consumable"]


@pytest.mark.parametrize("mutation,match", [
    (lambda rs: rs.append(copy.deepcopy(rs[0])), "duplicate"),
    (lambda rs: rs[0].update(choice=float("nan")), "nonfinite"),
    (lambda rs: rs[0].update(logits=[0, float("inf")]), "nonfinite"),
    (lambda rs: rs[0].update(choice=True), "semantic choice"),
    (lambda rs: rs[0].update(correct=not rs[0]["correct"]), "correct disagrees"),
    (lambda rs: rs[0].update(version=True), "integer"),
    (lambda rs: rs[0].update(policy="UNDECLARED"), "unexpected"),
    (lambda rs: rs[0].update(status="failed"), "unknown record status"),
    (lambda rs: rs[0].pop("correct_choice"), "lacks"),
])
def test_malformed_duplicate_and_nonfinite_rows_rejected(data, mutation, match):
    records, expected = data
    mutation(records)
    with pytest.raises(ValueError, match=match):
        v.validate_records(records, expected)


def test_fixed_candidate_relabeling_and_role_drift_rejected(data):
    records, expected = data
    row = find(records, kind="pulse", checkpoint=2, arm="Rcut", version=1, round_id=3, side=0)
    row["new_candidate"] = 3
    with pytest.raises(ValueError, match="fixed physical candidates"):
        v.validate_records(records, expected)
    row["new_candidate"] = 2
    row["focal_side"] = 1
    with pytest.raises(ValueError, match="physical focal roles"):
        v.validate_records(records, expected)


def test_actual_world_truth_is_not_replaced_by_ideal_pulse_candidate(data):
    records, expected = data
    row = find(records, kind="pulse", checkpoint=2, arm="Rcut", version=1, round_id=3, side=0)
    # A deviated downstream world may make the old candidate task-correct.
    row.update(choice=0, correct_choice=0, correct=True)
    result = v.analyze(records, expected, n_boot=20)
    assert result["completeness"]["complete"]
    assert endpoint(result, "pulse2_return")["mean"] == 1


def test_transfer_row_shared_across_participants_and_path_truth_fixed(data):
    records, expected = data
    row = find(records, kind="goal", checkpoint=3, qid="transfer_action", side=1, arm="L", version=1)
    row["old_candidate"] = 3
    with pytest.raises(ValueError, match="fixed physical candidates"):
        v.validate_records(records, expected)
    row["old_candidate"] = 0
    row = find(records, kind="goal", checkpoint=3, qid="partner_beacon", side=1, arm="L", version=1)
    row.update(correct_choice=1, choice=1, correct=True)
    with pytest.raises(ValueError, match="goal-probe truth"):
        v.validate_records(records, expected)


def test_assignment_truth_cannot_change_partner_goal_or_original_record(data):
    records, expected = data
    for row in records:
        if row["kind"] == "goal" and row["checkpoint"] == 6 and row["qid"] == "original_goal":
            row["correct_choice"] = (row["correct_choice"] + 1) % 4
            row["correct"] = row["choice"] == row["correct_choice"]
    with pytest.raises(ValueError, match="original assignment"):
        v.validate_records(records, expected)


def test_goal_means_average_both_epochs_inside_episode(data):
    records, expected = data
    for row in records:
        if row["kind"] == "goal" and row["checkpoint"] == 6 and row["qid"] == "transfer_action":
            change_choice(row, row["correct_choice"])
    result = v.analyze(records, expected, n_boot=20)
    assert endpoint(result, "goal_cross")["mean"] == .5
    assert endpoint(result, "goal_return")["mean"] == .5
    assert endpoint(result, "goal_cross")["n"] == 6


def test_natural_accuracy_uses_only_rounds_two_through_six_and_both_sides(data):
    records, expected = data
    for row in records:
        if row["kind"] == "natural" and row["qid"] == "action":
            change_choice(row, row["correct_choice"])
            if row["arm"] == "FRESH" and row["round_id"] == 2 and row["side"] == 0:
                change_choice(row, 1)
            if row["arm"] == "LIVE" and row["round_id"] == 1:
                change_choice(row, None)
    result = v.analyze(records, expected, n_boot=20)
    assert endpoint(result, "live_minus_fresh")["mean"] == pytest.approx(.1)


def test_random_switch_can_pass_path_tests_but_not_joint_quality():
    records, expected = SIM.synthetic_records(60, mode="nonspecific")
    result = v.analyze(records, expected, n_boot=40)
    for cp in (2, 5):
        for name in ("forward", "return", "replay"):
            item = endpoint(result, f"pulse{cp}_{name}")
            assert item["mean"] == pytest.approx(2 / 3)
            assert item["p_holm"] < .05
        assert endpoint(result, f"pulse{cp}_chain_quality")["mean"] == 0
    assert not any(result["sustained_response"].values())
    # Equal 10/10 trajectory accuracies must give exact zero, not summation residue.
    natural = endpoint(result, "live_minus_fresh")
    assert natural["mean"] == 0 and natural["p_two_sided"] == natural["p_holm"] == 1


def test_early_success_cannot_rescue_late_failure(data):
    records, expected = data
    for row in records:
        if row["kind"] == "pulse" and row["checkpoint"] == 5 and row["arm"] == "L":
            change_choice(row, 0)
    result = v.analyze(records, expected, n_boot=20)
    assert endpoint(result, "pulse2_chain_quality")["mean"] == 1
    assert endpoint(result, "pulse5_chain_quality")["mean"] == 0
    assert not any(result["sustained_response"].values())


def test_t_test_matches_independent_scipy_and_bootstrap_by_episode():
    x = [-1., -.5, 0., .5, 1., 1.]
    result = v.test_scores(x, n_boot=1000, seed=7)
    reference = stats.ttest_1samp(x, 0)
    assert result["t"] == pytest.approx(reference.statistic)
    assert result["p_two_sided"] == pytest.approx(reference.pvalue)
    rng = np.random.default_rng(7)
    boots = np.asarray(x)[rng.integers(0, len(x), size=(1000, len(x)))].mean(axis=1)
    assert result["ci95"] == np.quantile(boots, [.025, .975]).tolist()
    assert v.test_scores([0, 0], n_boot=10)["p_two_sided"] == 1
    assert v.test_scores([1, 1], n_boot=10)["p_two_sided"] == 0
    assert not v.test_scores([1, None], n_boot=10)["available"]
    with pytest.raises(ValueError, match="finite"):
        v.test_scores([1, float("nan")])


def test_fixed_holm_counts_unavailable_and_preserves_monotonicity():
    ps = [.001, .002, .04] + [1.] * 19
    adjusted = v.holm_fixed(ps, 22)
    assert adjusted[:3] == pytest.approx([.022, .042, .8])
    assert adjusted[3:] == [1.] * 19
    with pytest.raises(ValueError):
        v.holm_fixed(ps[:3], 22)
    with pytest.raises(ValueError):
        v.holm_fixed([float("nan")] + ps[1:], 22)


def test_declared_text_subset_only_and_missing_text_is_not_formal_imputation(data):
    records, expected = data
    model, ep = v.MODELS[0], expected[v.MODELS[0]][0]
    text_keys = v.expected_keys(ep, model, text=True) - v.expected_keys(ep, model)
    text_rows = [{**dict(zip(v.KEY_FIELDS, key)), "status": "ok", "choice": 0,
                  "correct_choice": 0, "correct": True} for key in text_keys]
    with pytest.raises(ValueError, match="unexpected"):
        v.analyze(records + text_rows, expected, n_boot=10)
    result = v.analyze(records + text_rows, expected, text_episodes={model: [ep]}, n_boot=10)
    assert result["completeness"]["complete"]
    partial = v.analyze(records, expected, text_episodes={model: [ep]}, n_boot=10)
    assert partial["completeness"]["missing_records"] == 24
    assert all(item["available"] for item in partial["primary"])


def test_exact_code_simulation_outputs_calibration_and_counterexamples():
    result = SIM.simulate(repetitions=2, n=12, n_boot=10, seed=71)
    assert result["repetitions"] == 2
    assert len(result["null"]["endpoint_false_rejections"]) == 22
    assert all(result["checks"]["alternative"]["sustained_response"].values())
    assert not any(result["checks"]["nonspecific"]["sustained_response"].values())
    json.dumps(result, allow_nan=False)


def test_native_choice_map_checks_actual_top_token_without_reargmax(data):
    records, expected = data
    row = records[0]
    choice = row["choice"]
    row.update(token_ids=[10, 11, 12, 13], candidate_map=[0, 1, 2, 3],
               top_token=10 + choice, legal_logits=[100., 0., 0., 0.],
               legal_mass=.9, top_probability=.6)
    # Deliberately do not require the archived FP32 logits' argmax to match native greedy.
    assert v.validate_records(records, expected)["complete"]
    row["top_token"] = 99
    with pytest.raises(ValueError, match="actual native top token"):
        v.validate_records(records, expected)


def test_absent_scientific_marker_does_not_attest_provenance(data):
    records, expected = data
    for row in records:
        row.pop("backend_kind")
        row.pop("scientific_data")
    result = v.analyze(records, expected, n_boot=10)
    assert not result["synthetic_input"]
    assert not result["scientific_source_verified"]


def test_neutral_gate_refuses_to_invent_pass_even_with_perfect_complete_scores():
    for stage in ("baseline", "calibration", "validity"):
        empty = v.neutral_gate_readiness(stage)
        assert not empty["ready"] and not empty["consumable"]
        assert empty["reason"] == "neutral_contract_unratified"
        result = v.neutral_gate_readiness(stage, {
            "episode_ids": ["one", "two"],
            "scores": {metric: {"0": [1., 1.], "1": [1., 1.]} for metric in v.NEUTRAL_METRICS}})
        assert result["input_validated"] and result["n_episodes"] == 2
        assert not result["ready"] and result["gate"] is None and result["selected_gain"] is None
        json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("scores", [
    {"goal_cross": {"0": [1.], "1": [1.]}},
    {"M": {"0": [1.], "1": [1.]}},
    {"cap_accuracy": {"0": [1.]}},
    {"cap_accuracy": {"0": [1.], "1": [None]}},
    {"cap_accuracy": {"0": [1.], "1": [float("nan")]}},
    {"cap_accuracy": {"0": [1.], "1": [1., 1.]}},
])
def test_neutral_gate_rejects_leakage_missing_unpaired_or_nonfinite(scores):
    with pytest.raises(ValueError):
        v.neutral_gate_readiness("calibration", {"episode_ids": ["one"], "scores": scores})
