"""Paired statistics, sample-size planning and the deterministic pilot selector.

Implements protocol v0.5 §9 (analysis) and §10 (selector). The unit of analysis is the
episode: every contrast is a per-episode paired difference D between two arms, and all
resampling is over episodes. The selector functions refuse inputs that carry any
attribution or self-report metric, so parameter choice can only see ACC, CAP and format.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from scipy import stats

Z_POWER_PLAN = 2.394 + 0.842  # two-sided alpha 0.05/3 (strictest Holm step) + 80% power
CONFIRMATORY = (("TWO", "ONE"), ("ONE", "STATIC"), ("ONE", "LANG_TAG"))


# ---------------------------------------------------------------------------
# Paired contrasts
# ---------------------------------------------------------------------------


def paired_differences(scores: pd.DataFrame, arm1: str, arm2: str, metric: str,
                       recipient: str = "A") -> pd.Series:
    """D = metric(arm1) - metric(arm2) per episode; episodes missing either side are dropped."""
    sub = scores[scores["recipient"] == recipient]
    wide = sub.pivot(index="episode_id", columns="arm", values=metric)
    missing = [a for a in (arm1, arm2) if a not in wide.columns]
    if missing:
        raise KeyError(f"arms not found: {missing}")
    d = wide[arm1] - wide[arm2]
    return d.dropna()


@dataclass(frozen=True)
class PairedTest:
    n: int
    mean: float
    sd: float
    se: float
    t: float
    p_two_sided: float


def paired_t(d: Sequence[float]) -> PairedTest:
    x = np.asarray(d, dtype=np.float64)
    n = x.size
    if n < 2:
        return PairedTest(n, math.nan, math.nan, math.nan, math.nan, math.nan)
    mean, sd = float(x.mean()), float(x.std(ddof=1))
    se = sd / math.sqrt(n)
    t = mean / se if se > 0 else math.inf * np.sign(mean) if mean else 0.0
    p = float(2 * stats.t.sf(abs(t), df=n - 1)) if math.isfinite(t) else 0.0
    return PairedTest(n, mean, sd, se, float(t), p)


def holm(pvalues: Sequence[float]) -> list[float]:
    """Holm step-down adjustment; NaN p-values stay NaN and are not counted in the family."""
    p = np.asarray(pvalues, dtype=np.float64)
    out = np.full(p.shape, np.nan)
    finite = np.flatnonzero(np.isfinite(p))
    m = finite.size
    if m == 0:
        return out.tolist()
    order = finite[np.argsort(p[finite], kind="stable")]
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        out[i] = running
    return out.tolist()


def bootstrap_ci(d: Sequence[float], n_boot: int = 10_000, seed: int = 0, level: float = 0.95,
                 statistic: Callable[[np.ndarray], float] = np.mean) -> tuple[float, float]:
    """Percentile interval from resampling episodes (the entries of ``d``)."""
    x = np.asarray(d, dtype=np.float64)
    if x.size < 2:
        return (math.nan, math.nan)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, x.size, size=(n_boot, x.size))
    boots = np.apply_along_axis(statistic, 1, x[idx]) if statistic is not np.mean else x[idx].mean(axis=1)
    alpha = (1 - level) / 2
    return (float(np.quantile(boots, alpha)), float(np.quantile(boots, 1 - alpha)))


def trimmed_mean(x: np.ndarray, proportion: float = 0.2) -> float:
    return float(stats.trim_mean(x, proportion))


def one_sided_lower_bound(d: Sequence[float], n_boot: int = 10_000, seed: int = 0,
                          level: float = 0.95) -> float:
    """Lower bound of a one-sided bootstrap interval for the mean (used by G2)."""
    x = np.asarray(d, dtype=np.float64)
    if x.size < 2:
        return math.nan
    rng = np.random.default_rng(seed)
    boots = x[rng.integers(0, x.size, size=(n_boot, x.size))].mean(axis=1)
    return float(np.quantile(boots, 1 - level))


def robustness_report(d: Sequence[float], n_boot: int = 10_000, seed: int = 0) -> dict[str, float]:
    x = np.asarray(d, dtype=np.float64)
    loo = (x.sum() - x) / (x.size - 1) if x.size > 1 else np.array([math.nan])
    q = np.quantile(x, [0.05, 0.25, 0.5, 0.75, 0.95]) if x.size else [math.nan] * 5
    lo, hi = bootstrap_ci(x, n_boot, seed, statistic=lambda v: trimmed_mean(v, 0.2))
    return {
        "n": float(x.size), "mean": float(x.mean()) if x.size else math.nan,
        "sd": float(x.std(ddof=1)) if x.size > 1 else math.nan,
        "q05": float(q[0]), "q25": float(q[1]), "median": float(q[2]), "q75": float(q[3]), "q95": float(q[4]),
        "max_abs": float(np.abs(x).max()) if x.size else math.nan,
        "loo_min": float(loo.min()), "loo_max": float(loo.max()),
        "trimmed20": trimmed_mean(x, 0.2) if x.size else math.nan,
        "trimmed20_lo": lo, "trimmed20_hi": hi,
    }


@dataclass(frozen=True)
class ContrastResult:
    arm1: str
    arm2: str
    metric: str
    test: PairedTest
    ci: tuple[float, float]
    p_holm: float = math.nan


def contrast_family(scores: pd.DataFrame, contrasts: Sequence[tuple[str, str]], metric: str,
                    recipient: str = "A", n_boot: int = 10_000, seed: int = 0) -> list[ContrastResult]:
    """Paired t per contrast, Holm within the family, episode-bootstrap 95% intervals."""
    results = []
    for arm1, arm2 in contrasts:
        d = paired_differences(scores, arm1, arm2, metric, recipient)
        results.append(ContrastResult(arm1, arm2, metric, paired_t(d), bootstrap_ci(d, n_boot, seed)))
    adjusted = holm([r.test.p_two_sided for r in results])
    return [ContrastResult(r.arm1, r.arm2, r.metric, r.test, r.ci, p) for r, p in zip(results, adjusted)]


# ---------------------------------------------------------------------------
# Sample size (protocol v0.5 §9)
# ---------------------------------------------------------------------------


def plan_sample_size(sds: Sequence[float], delta: float = 0.5, n_min: int = 300,
                     n_max: int = 600) -> tuple[int, float]:
    """N from the largest paired-D SD, rounded up to a multiple of 4; returns (N, MDE at N)."""
    sd = max(float(s) for s in sds)
    raw = math.ceil((Z_POWER_PLAN * sd / delta) ** 2)
    n = min(n_max, max(n_min, raw))
    n = min(n_max, int(math.ceil(n / 4) * 4))
    return n, Z_POWER_PLAN * sd / math.sqrt(n)


# ---------------------------------------------------------------------------
# Deterministic pilot selector (protocol v0.5 §10)
# ---------------------------------------------------------------------------

SELECTOR_COLUMNS = {"form", "layer", "gain", "condition", "acc_increment", "cap_drop",
                    "label_mass", "mass_drop", "n"}
CAP_DROP_MAX = 0.05
MASS_MIN = 0.90
MASS_DROP_MAX = 0.05
MIN_SCORE = 0.1
MATCH_TOL = 0.25
PILOT_B_GRID = (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5)
STATIC_GRID = (0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0)
MAX_MAIN_GAINS = 6


class SelectorInputError(ValueError):
    pass


def _check_selector_input(df: pd.DataFrame) -> None:
    extra = set(df.columns) - SELECTOR_COLUMNS
    if extra:
        raise SelectorInputError(f"selector may only see ACC/CAP/format summaries; got {sorted(extra)}")


def eligible(df: pd.DataFrame) -> pd.Series:
    return (df["cap_drop"] <= CAP_DROP_MAX) & (df["label_mass"] >= MASS_MIN) & (df["mass_drop"] <= MASS_DROP_MAX)


@dataclass(frozen=True)
class PilotASelection:
    ok: bool
    form: str | None
    layer: int | None
    gain: float | None
    score: float | None
    per_layer_gain: dict[int, float | None] = field(default_factory=dict)
    reason: str = ""


def select_pilot_a(summary: pd.DataFrame) -> PilotASelection:
    """Rows: one per (form, layer, gain) for condition ONE. Score = ACC-rule increment vs C0."""
    _check_selector_input(summary)
    df = summary[eligible(summary)].copy()
    if df.empty:
        return PilotASelection(False, None, None, None, None, reason="no eligible (form, layer, gain)")
    groups = []
    for (form, layer), g in df.groupby(["form", "layer"]):
        best = g.sort_values(["acc_increment", "gain"], ascending=[False, True]).iloc[0]
        groups.append((form, int(layer), float(best["gain"]), float(best["acc_increment"])))
    form_rank = {"raw": 0, "ema": 1}
    groups.sort(key=lambda t: (-t[3], form_rank.get(t[0], 9), t[2], t[1]))
    form, layer, gain, score = groups[0]
    if score <= MIN_SCORE:
        return PilotASelection(False, None, None, None, score,
                               reason=f"best eligible score {score:.3f} <= {MIN_SCORE} nat (screening failure)")
    per_layer: dict[int, float | None] = {}
    for lay in sorted(summary["layer"].unique()):
        g = df[(df["form"] == form) & (df["layer"] == lay)]
        per_layer[int(lay)] = (float(g.sort_values(["acc_increment", "gain"], ascending=[False, True]).iloc[0]["gain"])
                               if not g.empty else None)
    return PilotASelection(True, form, layer, gain, score, per_layer)


@dataclass(frozen=True)
class PilotBSelection:
    ok: bool
    g_star: float | None
    main_gains: tuple[float, ...]
    g_static: float | None
    static_matched: bool
    static_neighbors: tuple[float, ...]
    static_executable: bool
    reason: str = ""


def _neighbors(grid: Sequence[float], center: float, k: int = 2) -> tuple[float, ...]:
    i = list(grid).index(center)
    others = [(abs(j - i), g) for j, g in enumerate(grid) if j != i]
    others.sort(key=lambda t: (t[0], t[1]))
    return tuple(sorted(g for _, g in others[:k]))


def select_pilot_b(summary: pd.DataFrame) -> PilotBSelection:
    """Rows: one per (condition in {ONE, TWO, STATIC}, gain) at the selected form/layer."""
    _check_selector_input(summary)
    ok = summary[eligible(summary)]
    one = ok[ok["condition"] == "ONE"].set_index("gain")
    two = ok[ok["condition"] == "TWO"].set_index("gain")
    both = sorted(set(one.index) & set(two.index))
    if not both:
        return PilotBSelection(False, None, (), None, False, (), False, "no gain eligible for both ONE and TWO")
    cand = one.loc[both].reset_index().sort_values(["acc_increment", "gain"], ascending=[False, True])
    g_star = float(cand.iloc[0]["gain"])
    score_star = float(cand.iloc[0]["acc_increment"])
    above = [g for g in PILOT_B_GRID if g > g_star]
    cutoff = min(above[0], max(PILOT_B_GRID)) if above else max(PILOT_B_GRID)
    main = [g for g in PILOT_B_GRID if g <= cutoff]
    while len(main) > MAX_MAIN_GAINS:
        main.pop(0)
    static = ok[ok["condition"] == "STATIC"].copy()
    if static.empty:
        return PilotBSelection(True, g_star, tuple(main), None, False, (), False,
                               "no eligible STATIC point: signal-type contrast not executable")
    static["dist"] = (static["acc_increment"] - score_star).abs()
    best = static.sort_values(["dist", "gain"]).iloc[0]
    g_s = float(best["gain"])
    return PilotBSelection(True, g_star, tuple(main), g_s, bool(best["dist"] <= MATCH_TOL),
                           _neighbors(STATIC_GRID, g_s), True)


def selector_summary(scores: pd.DataFrame, baseline_arm: str, arm_meta: pd.DataFrame,
                     recipient: str = "A") -> pd.DataFrame:
    """ACC-rule increment, CAP drop and format per arm, paired against the C0 arm.

    ``arm_meta`` has columns arm, form, layer, gain, condition. Only ACC_RULE, CAP_ACC
    and LABEL_MASS are read from ``scores``.
    """
    cols = ["episode_id", "recipient", "arm", "ACC_RULE", "CAP_ACC", "LABEL_MASS"]
    sub = scores.loc[scores["recipient"] == recipient, cols]
    base = sub[sub["arm"] == baseline_arm].set_index("episode_id")
    rows = []
    for _, meta in arm_meta.iterrows():
        arm = sub[sub["arm"] == meta["arm"]].set_index("episode_id")
        joined = arm.join(base, rsuffix="_c0", how="inner").dropna(
            subset=["ACC_RULE", "ACC_RULE_c0", "CAP_ACC", "CAP_ACC_c0", "LABEL_MASS", "LABEL_MASS_c0"])
        rows.append({
            "form": meta["form"], "layer": int(meta["layer"]), "gain": float(meta["gain"]),
            "condition": meta["condition"], "n": int(len(joined)),
            "acc_increment": float((joined["ACC_RULE"] - joined["ACC_RULE_c0"]).mean()),
            "cap_drop": float(joined["CAP_ACC_c0"].mean() - joined["CAP_ACC"].mean()),
            "label_mass": float(joined["LABEL_MASS"].mean()),
            "mass_drop": float(joined["LABEL_MASS_c0"].mean() - joined["LABEL_MASS"].mean()),
        })
    return pd.DataFrame(rows)
