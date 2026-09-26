"""Offline tests for paired statistics, sample size and the pilot selector (protocol v0.5 §9-10)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from mb import analyze


def test_paired_t_matches_scipy():
    d = np.array([1.0, 2.0, 3.0, 4.0, 2.5, -0.5])
    res = analyze.paired_t(d)
    ref = stats.ttest_1samp(d, 0.0)
    assert res.t == pytest.approx(ref.statistic)
    assert res.p_two_sided == pytest.approx(ref.pvalue)
    assert res.n == 6


def test_holm_example():
    assert analyze.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert analyze.holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])  # monotone after sorting
    assert analyze.holm([0.001, 0.2, 0.03]) == pytest.approx([0.003, 0.2, 0.06])


def test_bootstrap_interval_contains_mean_and_is_deterministic():
    rng = np.random.default_rng(0)
    d = rng.normal(0.4, 1.0, size=300)
    lo, hi = analyze.bootstrap_ci(d, n_boot=2000, seed=1)
    assert lo < d.mean() < hi
    assert analyze.bootstrap_ci(d, n_boot=2000, seed=1) == (lo, hi)
    assert analyze.one_sided_lower_bound(d, n_boot=2000, seed=1) < d.mean()


def test_robustness_report_fields():
    rep = analyze.robustness_report(np.array([0.0, 1.0, 2.0, 3.0, 100.0]), n_boot=500)
    assert rep["max_abs"] == 100.0 and rep["loo_min"] < rep["loo_max"]
    assert rep["trimmed20"] == pytest.approx(2.0)


def test_plan_sample_size_rounding_and_cap():
    n, mde = analyze.plan_sample_size([2.0, 1.0])
    assert n == 300 and mde == pytest.approx(analyze.Z_POWER_PLAN * 2.0 / math.sqrt(300))
    assert analyze.plan_sample_size([3.0])[0] == 380  # 377 rounded up to a multiple of 4
    n5, mde5 = analyze.plan_sample_size([5.0])
    assert n5 == 600 and mde5 == pytest.approx(analyze.Z_POWER_PLAN * 5.0 / math.sqrt(600))


def _scores(effects: dict[str, float], n: int = 200, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 1, size=n)
    rows = []
    for arm, eff in effects.items():
        noise = rng.normal(0, 0.5, size=n)
        for i in range(n):
            rows.append({"episode_id": f"e{i}", "recipient": "A", "arm": arm, "M": base[i] + eff + noise[i]})
    return pd.DataFrame(rows)


def test_contrast_family_pairs_by_episode_and_applies_holm():
    scores = _scores({"ONE": 0.0, "TWO": 0.6, "STATIC": 0.0, "LANG_TAG": -0.05})
    res = analyze.contrast_family(scores, analyze.CONFIRMATORY, "M", n_boot=1000)
    by = {(r.arm1, r.arm2): r for r in res}
    assert by[("TWO", "ONE")].test.mean == pytest.approx(0.6, abs=0.15)
    assert by[("TWO", "ONE")].p_holm < 0.001
    assert all(r.p_holm >= r.test.p_two_sided for r in res)
    d = analyze.paired_differences(scores, "TWO", "ONE", "M")
    assert len(d) == 200


# --- selector ------------------------------------------------------------------------


def _row(form, layer, gain, acc, cap=0.0, mass=0.97, mdrop=0.0, cond="ONE"):
    return {"form": form, "layer": layer, "gain": gain, "condition": cond, "acc_increment": acc,
            "cap_drop": cap, "label_mass": mass, "mass_drop": mdrop, "n": 16}


def test_selector_refuses_attribution_columns():
    df = pd.DataFrame([_row("raw", 18, 0.3, 1.0)]).assign(M=0.2)
    with pytest.raises(analyze.SelectorInputError):
        analyze.select_pilot_a(df)


def test_pilot_a_eligibility_and_tie_breaks():
    df = pd.DataFrame([
        _row("raw", 12, 0.3, 0.8), _row("raw", 12, 0.7, 2.0, cap=0.2),  # 0.7 ineligible
        _row("raw", 18, 0.3, 1.1), _row("raw", 18, 0.7, 1.1),           # tie within group -> 0.3
        _row("ema", 18, 0.3, 1.1),                                        # tie across forms -> raw
        _row("ema", 24, 0.1, 0.9), _row("raw", 24, 1.5, 0.5, mass=0.8),
    ])
    sel = analyze.select_pilot_a(df)
    assert sel.ok and (sel.form, sel.layer, sel.gain) == ("raw", 18, 0.3)
    assert sel.per_layer_gain == {12: 0.3, 18: 0.3, 24: None}


def test_pilot_a_screening_failures():
    none_ok = pd.DataFrame([_row("raw", 18, 0.3, 2.0, cap=0.5)])
    assert not analyze.select_pilot_a(none_ok).ok
    weak = pd.DataFrame([_row("raw", 18, 0.3, 0.08), _row("ema", 18, 0.3, 0.1)])
    sel = analyze.select_pilot_a(weak)
    assert not sel.ok and "screening failure" in sel.reason


def test_pilot_b_selection_rules():
    rows = []
    for g, acc in zip(analyze.PILOT_B_GRID, (0.1, 0.2, 0.4, 0.7, 1.0, 1.2, 1.3, 1.4)):
        rows.append(_row("raw", 18, g, acc, cond="ONE", cap=0.1 if g >= 1.0 else 0.0))
        rows.append(_row("raw", 18, g, acc * 0.8, cond="TWO"))
    for g, acc in zip(analyze.STATIC_GRID, (0.2, 0.5, 0.9, 1.25, 1.6, 2.0, 2.2, 2.4)):
        rows.append(_row("raw", 18, g, acc, cond="STATIC"))
    sel = analyze.select_pilot_b(pd.DataFrame(rows))
    assert sel.ok and sel.g_star == 0.7  # 1.0+ ineligible for ONE
    assert sel.main_gains == (0.1, 0.2, 0.3, 0.5, 0.7, 1.0)  # up to next grid point, max 6 (drop 0.05)
    assert sel.g_static == 0.5 and sel.static_matched  # |1.25 - 1.2| = 0.05
    assert sel.static_neighbors == (0.3, 0.7)
    assert sel.static_executable


def test_pilot_b_static_unmatched_and_not_executable():
    rows = [_row("raw", 18, 0.3, 1.0, cond="ONE"), _row("raw", 18, 0.3, 0.9, cond="TWO"),
            _row("raw", 18, 0.1, 0.2, cond="STATIC"), _row("raw", 18, 2.0, 3.0, cond="STATIC")]
    sel = analyze.select_pilot_b(pd.DataFrame(rows))
    assert sel.g_static == 0.1 and not sel.static_matched
    assert sel.static_neighbors == (0.2, 0.3)  # boundary: two nearest by grid index
    no_static = pd.DataFrame(rows[:2] + [_row("raw", 18, 0.1, 0.2, cond="STATIC", cap=0.3)])
    sel2 = analyze.select_pilot_b(no_static)
    assert sel2.ok and not sel2.static_executable
    assert not analyze.select_pilot_b(pd.DataFrame([_row("raw", 18, 0.3, 1.0, cond="ONE")])).ok


def test_selector_summary_reads_only_allowed_metrics():
    rows = []
    for i in range(10):
        rows.append({"episode_id": f"e{i}", "recipient": "A", "arm": "C0", "ACC_RULE": 0.0,
                     "CAP_ACC": 1.0, "LABEL_MASS": 0.98, "M": 99.0})
        rows.append({"episode_id": f"e{i}", "recipient": "A", "arm": "ONE@0.3", "ACC_RULE": 1.5,
                     "CAP_ACC": 0.5 if i < 2 else 1.0, "LABEL_MASS": 0.95, "M": -99.0})
    meta = pd.DataFrame([{"arm": "ONE@0.3", "form": "raw", "layer": 18, "gain": 0.3, "condition": "ONE"}])
    summ = analyze.selector_summary(pd.DataFrame(rows), "C0", meta)
    assert set(summ.columns) <= analyze.SELECTOR_COLUMNS
    row = summ.iloc[0]
    assert row["acc_increment"] == pytest.approx(1.5)
    assert row["cap_drop"] == pytest.approx(0.1)
    assert row["mass_drop"] == pytest.approx(0.03)


def test_holm_ignores_nan():
    from mb import analyze

    out = analyze.holm([0.01, float("nan"), 0.04])
    assert out[0] == pytest.approx(0.02) and out[2] == pytest.approx(0.04) and math.isnan(out[1])
    assert all(math.isnan(x) for x in analyze.holm([float("nan")]))
