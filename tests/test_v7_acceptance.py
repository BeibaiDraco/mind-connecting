"""Prospective engineering admission rules; no torch and no scientific readouts."""
import copy
import json

import pytest

from mb import v7_acceptance as a, v7_run


def row(value):
    return dict.fromkeys(a.METRICS, value)


def test_bf16_limits_are_measured_before_comparison_with_no_fixed_floor():
    limits = a.envelope([row(.125), row(.25)])
    assert limits == row(.25)
    assert a.within_envelope([row(.25)], limits)
    assert not a.within_envelope([row(.250001)], limits)
    assert not a.within_envelope([row(1e-12)], row(0))
    assert a.within_envelope([row(0)], row(0))
    assert not a.within_envelope([], limits)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.])
def test_nonfinite_or_negative_baseline_and_test_errors_fail_closed(bad):
    with pytest.raises(ValueError):
        a.envelope([row(bad)])
    assert not a.within_envelope([row(bad)], row(.25))
    assert not a.within_envelope([row(0)], row(bad))


def test_each_error_metric_must_pass_independently():
    for metric in a.METRICS:
        compared = row(0)
        compared[metric] = .251
        assert not a.within_envelope([compared], row(.25))


def timings():
    return [{"batch": b, "passed": True, "seconds_per_episode_token": 1 / b} for b in a.BATCHES]


def test_selection_uses_only_measured_throughput_and_requires_all_pass():
    original = timings()
    assert a.choose_batch(original) == 12
    tied = copy.deepcopy(original)
    for r in tied:
        r["seconds_per_episode_token"] = 1
    assert a.choose_batch(tied) == 1
    for index in range(len(original)):
        failed = copy.deepcopy(original)
        failed[index]["passed"] = False
        with pytest.raises(ValueError):
            a.choose_batch(failed)
    for partial in (original[:-1], original + original[:1]):
        with pytest.raises(ValueError):
            a.choose_batch(partial)


def test_receipts_cannot_be_replaced(tmp_path):
    path = tmp_path / "recipe.json"
    a.write_once(path, a.RECIPE)
    assert json.loads(path.read_text()) == a.RECIPE
    with pytest.raises(FileExistsError):
        a.write_once(path, {"passed": True})


def test_wrong_approval_cannot_create_output_or_load_model(tmp_path):
    output = tmp_path / "acceptance"
    with pytest.raises(ValueError, match="approved"):
        a.main([str(output), "--approved-protocol-sha256", "wrong"])
    assert not output.exists()


def test_smoke_scope_and_pilot_are_separate_and_formal_not_dispatched():
    assert a.RECIPE["split"] == "v7_dev" and a.RECIPE["episodes"] == 12
    cfg = v7_run.V7Config("v7_dev", "base", 12)
    expected = [key for key in v7_run.expected_trials(cfg) if key[3] == "CAP0"]
    assert len(expected) == 336 and {key[3] for key in expected} == {"CAP0"}
    assert len(v7_run.expected_trials(v7_run.V7Config("v7_pilot", "base", 80))) == 20880
