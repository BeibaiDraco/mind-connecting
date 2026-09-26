"""Formal-stage report (protocol-v1): pre-registered results first, then labelled descriptive analyses.

    python scripts/report_formal.py [RESULTS_DIR] [--out docs/results/formal_report.md]

Finds the newest ``*_main_v1``, ``*_main_diag_v1``, ``*_ext_layers_v1`` and ``*_ext_masks_v1`` runs.
Section 1 reproduces the §9 confirmatory analysis (post_confirmatory); everything after it is
descriptive or exploratory and says so. Missing trials stay missing (pairs are dropped, counts shown).
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from mb import analyze, ledger, readouts, run

DEFAULT_RESULTS = Path("/Volumes/VERBATIM SD/mind-connecting-data/results")


def md_table(df: pd.DataFrame, digits: int = 3) -> str:
    def fmt(v):
        if isinstance(v, (bool, np.bool_)):
            return "yes" if v else "no"
        if isinstance(v, (float, np.floating)):
            return "NA" if not math.isfinite(float(v)) else f"{float(v):.{digits}f}"
        return str(v)

    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    return "\n".join([head, sep, *("| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False))])


def newest(results: Path, suffix: str) -> Path | None:
    runs = sorted(p for p in results.glob(f"*_{suffix}") if p.is_dir() and not p.name.endswith("smoke"))
    return runs[-1] if runs else None


def scores_of(run_dir: Path) -> pd.DataFrame:
    return readouts.score_records(run._valid_ok(run_dir), readouts.ScoreOptions(rotations=None))


def delta_table(scores: pd.DataFrame, arms: list[str], metrics: tuple[str, ...], recipient: str = "A",
                base: str | None = None) -> pd.DataFrame:
    """Paired arm - C0 differences with 95% bootstrap intervals (descriptive)."""
    sub = scores[scores["recipient"] == recipient]
    if base is None:
        c0 = sub[sub["condition"] == "C0"]["arm"].unique()
        if len(c0) != 1:
            return pd.DataFrame()
        base = str(c0[0])
    rows = []
    for arm in arms:
        if arm not in set(sub["arm"]):
            continue
        row: dict = {"arm": arm}
        for metric in metrics:
            d = analyze.paired_differences(scores, arm, base, metric, recipient)
            lo, hi = analyze.bootstrap_ci(d, n_boot=4000) if len(d) > 1 else (math.nan, math.nan)
            row[f"Δ{metric}"] = float(d.mean()) if len(d) else math.nan
            row[f"{metric} 95% CI"] = f"[{lo:.2f}, {hi:.2f}]" if math.isfinite(lo) else "NA"
        row["n"] = int(len(analyze.paired_differences(scores, arm, base, metrics[0], recipient)))
        rows.append(row)
    return pd.DataFrame(rows)


def engineering(scores: pd.DataFrame, arms: list[str], recipient: str = "A") -> pd.DataFrame:
    sub = scores[scores["recipient"] == recipient]
    c0 = sub[sub["condition"] == "C0"].set_index("episode_id")
    rows = []
    for arm in arms:
        g = sub[sub["arm"] == arm].set_index("episode_id")
        if g.empty:
            continue
        j = g.join(c0, rsuffix="_c0", how="inner")
        rows.append({"arm": arm, "CAP": j["CAP_ACC"].mean(), "CAP drop": j["CAP_ACC_c0"].mean() - j["CAP_ACC"].mean(),
                     "label mass": j["LABEL_MASS"].mean(), "n": len(j)})
    return pd.DataFrame(rows)


def completeness_lines(stage: str, run_dir: Path | None) -> list[str]:
    if run_dir is None:
        return [f"- {stage}: not found"]
    comp = run.run_completeness(run_dir)
    miss = ", ".join(f"{k}: {v}" for k, v in comp["missing_by_arm"].items()) or "none"
    return [f"- {stage} `{run_dir.name}`: {comp['status']} ({comp['n_ok']}/{comp['n_expected']}); missing by arm: {miss}"]


def u_closed_table(run_dir: Path, arms: list[str]) -> pd.DataFrame:
    counts: dict[str, collections.Counter] = {a: collections.Counter() for a in arms}
    for r in run._valid_ok(run_dir):
        if r["qid"] == "U_CLOSED" and r["recipient"] == "A" and r["arm"] in counts:
            counts[r["arm"]][readouts.argmax_meaning(r)] += 1
    rows = []
    for arm, c in counts.items():
        n = sum(c.values())
        if n:
            rows.append({"arm": arm, **{k: c.get(k, 0) / n for k in ("one", "two", "partly_shared", "hard_to_say")}, "n": n})
    return pd.DataFrame(rows)


def mention_table(run_dir: Path) -> pd.DataFrame:
    ticks = [json.loads(line) for line in (run_dir / "ticks.jsonl").read_text().splitlines()]
    agg: dict[str, list] = collections.defaultdict(list)
    for t in ticks:
        m = t.get("mentions_A") or {}
        agg[t["arm"]].append((m.get("word_B", 0) > 0, m.get("rule_B", 0) > 0, m.get("word_A", 0) > 0,
                              t.get("inj_host_ratio_A", math.nan), t.get("unmatched_ticks_A", 0)))
    rows = []
    for arm, vals in sorted(agg.items()):
        v = np.array(vals, dtype=float)
        rows.append({"arm": arm, "A says B's word": v[:, 0].mean(), "A says B's rule phrase": v[:, 1].mean(),
                     "A says own word": v[:, 2].mean(), "inj/host (C)": np.nanmean(v[:, 3]),
                     "unmatched C ticks (mean)": v[:, 4].mean(), "n": len(v)})
    return pd.DataFrame(rows)


def u_open_examples(run_dir: Path, arms: list[str], k: int = 2) -> list[str]:
    out = []
    by_arm: dict[str, list[str]] = collections.defaultdict(list)
    for r in run._valid_ok(run_dir):
        if r["qid"] == "U_OPEN" and r["recipient"] == "A" and r["arm"] in arms and len(by_arm[r["arm"]]) < k:
            by_arm[r["arm"]].append(r.get("generated_text", "").replace("\n", " ").strip())
    for arm in arms:
        for text in by_arm.get(arm, []):
            out.append(f"- `{arm}`: {text[:400]}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=Path, nargs="?", default=DEFAULT_RESULTS)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    R = args.results
    main_dir, diag_dir = newest(R, "main_v1"), newest(R, "main_diag_v1")
    layers_dir, masks_dir = newest(R, "ext_layers_v1"), newest(R, "ext_masks_v1")
    L: list[str] = ["# Formal results (protocol-v1)", ""]
    L += ["## 0. Completeness", ""]
    for stage, d in (("main", main_dir), ("main_diag", diag_dir), ("ext_layers", layers_dir), ("ext_masks", masks_dir)):
        L += completeness_lines(stage, d)

    if main_dir is not None:
        conf_path = main_dir / "confirmatory.json"
        conf = json.loads(conf_path.read_text()) if conf_path.exists() else run.post_confirmatory(main_dir)
        fz = conf["frozen"]
        L += ["", "## 1. Confirmatory (pre-registered, §9): recipient A, FULL, metric M", "",
              f"Frozen: form={fz['form']} layer={fz['layer']} g*={fz['g_star']} g_s*={fz.get('g_static')} "
              f"(STATIC matched={fz.get('static_matched')}) N={fz['N']}. Two-sided paired t, Holm within the family; "
              "10,000-resample episode bootstrap 95% CI. M = L_START − L_START-R; positive D means arm1 attributes "
              "the partner's rule to itself more than arm2 does.", ""]
        prim = pd.DataFrame(conf["primary"])[["arm1", "arm2", "n", "mean", "sd", "se", "t", "p_two_sided", "p_holm",
                                              "ci95_lo", "ci95_hi"]]
        L += [md_table(prim), "", "Robustness (20% trimmed mean with bootstrap CI; leave-one-out range):", ""]
        rob = pd.DataFrame([{"contrast": k, "trimmed20": v["trimmed20"], "lo": v["trimmed20_lo"], "hi": v["trimmed20_hi"],
                             "median": v["median"], "loo_min": v["loo_min"], "loo_max": v["loo_max"],
                             "max_abs": v["max_abs"]} for k, v in conf["robustness"].items()])
        L += [md_table(rob), "", "Access (ACC) difference within each contrast (arm1 − arm2):", "",
              md_table(pd.DataFrame(conf["access_in_contrasts"])), "",
              "## 2. Secondary family (M_NOW, M_WORD; one Holm family)", "",
              md_table(pd.DataFrame(conf["secondary"])[["arm1", "arm2", "metric", "n", "mean", "se", "t", "p_two_sided",
                                                        "p_holm", "ci95_lo", "ci95_hi"]])]

        sc = scores_of(main_dir)
        arms_a = sorted(set(sc[sc["recipient"] == "A"]["arm"]) - set(sc[sc["condition"] == "C0"]["arm"]))
        metrics = ("M", "M_NOW", "M_WORD", "ACC_RULE", "ACC_WORD")
        L += ["", "## 3. Descriptive: every arm minus C0 (recipient A)", "",
              "Not confirmatory. Dose-response over gains, RF/RO, LANG tag vs untag, MISMATCH, SCRAM.", "",
              md_table(delta_table(sc, arms_a, metrics)), "", "Engineering (capability and format):", "",
              md_table(engineering(sc, arms_a))]
        arms_b = sorted(a for a in set(sc[sc["recipient"] == "B"]["arm"]) if not a.startswith("C0"))
        if arms_b:
            L += ["", "Recipient B in two-way arms (descriptive, §9):", "", md_table(delta_table(sc, arms_b, metrics, "B"))]
        L += ["", "Self-report U-closed (share of argmax answers, recipient A; descriptive):", "",
              md_table(u_closed_table(main_dir, ["C0/FULL", *arms_a])), "",
              "C-phase reflections: how often A's own reflection names B's word / rule phrase (content leak into text):", "",
              md_table(mention_table(main_dir)), "", "U-open examples (first two per arm):", ""]
        L += u_open_examples(main_dir, ["C0/FULL", f"ONE/L{fz['layer']}/{fz['form']}/g{fz['g_star']:g}/FULL",
                                        f"TWO/L{fz['layer']}/{fz['form']}/g{fz['g_star']:g}/FULL", "LANG_TAG/FULL"])

    if diag_dir is not None:
        pc_path = diag_dir / "pilot_c.json"
        pc = json.loads(pc_path.read_text()) if pc_path.exists() else run.post_pilot_c(diag_dir)
        g2 = pc.get("g2_detail", {})
        L += ["", "## 4. Diagnostic subset: content counterfactual in the formal sample (60 episodes, 4 rotations)", ""]
        for kind in ("rule", "word"):
            c = g2.get(f"C_content_{kind}", {})
            L.append(f"- {kind}: C_content mean {c.get('mean')}, one-sided 95% lower bound {c.get('lb95_one_sided')}, "
                     f"n={c.get('n')}")
    for title, d in (("## 5. Extension A: injection effect by layer (each at its own g*_l; descriptive)", layers_dir),
                     ("## 6. Extension B: injection support size k (nested masks; descriptive)", masks_dir)):
        if d is None:
            continue
        sc = scores_of(d)
        arms = sorted(set(sc[sc["recipient"] == "A"]["arm"]) - set(sc[sc["condition"] == "C0"]["arm"]))
        L += ["", title, "", md_table(delta_table(sc, arms, ("M", "ACC_RULE", "ACC_WORD"))), "",
              md_table(engineering(sc, arms)), "", md_table(mention_table(d))]
        if d is masks_dir:
            unmatched = collections.Counter()
            for r in run._valid_ok(d):
                if r.get("r_unmatched_ticks"):
                    unmatched[r["arm"]] += int(r["r_unmatched_ticks"])
            L += ["", f"R-phase energy-matching failures (ticks, summed): {dict(unmatched) or 'none'}"]
    text = "\n".join(L) + "\n"
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
