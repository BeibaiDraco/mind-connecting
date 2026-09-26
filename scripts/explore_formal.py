"""Exploratory (post hoc) analyses of the formal stages. Nothing here is confirmatory.

    python scripts/explore_formal.py [RESULTS_DIR] [--out docs/results/formal_exploratory.md]

1. Decomposition of ΔM into its two log-ratios (self question vs Robin question), and the same
   for NOW (current intention).
2. Per-episode coupling between content access (ΔACC_RULE) and self-attribution (ΔM).
3. Self-report shifts (U-closed "two" + "partly shared") with episode-bootstrap intervals.
4. U-open text: how often the free self-description names the partner's code name, rule or word,
   or uses other-agent language.
5. Two-way convergence: A–B hidden-state cosine during reflection.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from mb import analyze, readouts, run, tasks

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("report_formal", HERE / "report_formal.py")
rf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rf)

OTHER_WORDS = re.compile(r"\b(another|someone else|external|influenc\w*|shared|partner|participant|we|us|our|"
                         r"not (?:my|mine)|foreign|other (?:agent|person|mind|voice))\b", re.I)


def ci(values: np.ndarray, n_boot: int = 4000) -> tuple[float, float]:
    return analyze.bootstrap_ci(values, n_boot=n_boot) if len(values) > 1 else (math.nan, math.nan)


def fmt_ci(v: np.ndarray) -> str:
    lo, hi = ci(v)
    return f"{np.mean(v):+.3f} [{lo:+.2f}, {hi:+.2f}]"


def now_logratios(records: list[dict]) -> pd.DataFrame:
    """Per (episode, arm, recipient): mean over rotations of z(partner)-z(own) on NOW and z(partner)-z(robin) on NOW_R."""
    acc: dict[tuple, dict[str, list[float]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in records:
        if r["qid"] == "NOW":
            acc[(r["episode_id"], r["arm"], r["recipient"])]["L_NOW"].append(readouts.log_ratio(r, "partner", "own"))
        elif r["qid"] == "NOW_R":
            acc[(r["episode_id"], r["arm"], r["recipient"])]["L_NOW_R"].append(readouts.log_ratio(r, "partner", "robin"))
    rows = [{"episode_id": k[0], "arm": k[1], "recipient": k[2], **{m: float(np.mean(v)) for m, v in d.items()}}
            for k, d in acc.items()]
    return pd.DataFrame(rows)


def decomposition(scores: pd.DataFrame, nowdf: pd.DataFrame, arms: list[str]) -> pd.DataFrame:
    a = scores[scores["recipient"] == "A"].set_index(["episode_id", "arm"])
    n = nowdf[nowdf["recipient"] == "A"].set_index(["episode_id", "arm"])
    c0 = "C0/FULL"
    rows = []
    for arm in arms:
        row = {"arm": arm}
        for col, src in (("L_START", a), ("L_START_R", a), ("M", a), ("L_NOW", n), ("L_NOW_R", n), ("M_NOW", a)):
            x = src.xs(arm, level="arm")[col]
            y = src.xs(c0, level="arm")[col]
            d = (x - y).dropna().to_numpy()
            row[f"Δ{col}"] = fmt_ci(d)
        rows.append(row)
    return pd.DataFrame(rows)


def access_vs_attribution(scores: pd.DataFrame, arms: list[str]) -> pd.DataFrame:
    a = scores[scores["recipient"] == "A"]
    wide_acc = a.pivot(index="episode_id", columns="arm", values="ACC_RULE")
    wide_m = a.pivot(index="episode_id", columns="arm", values="M")
    rows = []
    for arm in arms:
        dacc = (wide_acc[arm] - wide_acc["C0/FULL"])
        dm = (wide_m[arm] - wide_m["C0/FULL"])
        ok = dacc.notna() & dm.notna()
        r = float(np.corrcoef(dacc[ok], dm[ok])[0, 1])
        hi = dacc[ok] > dacc[ok].median()
        rows.append({"arm": arm, "corr(ΔACC, ΔM)": r, "ΔM | high ΔACC": dm[ok][hi].mean(),
                     "ΔM | low ΔACC": dm[ok][~hi].mean(), "n": int(ok.sum())})
    return pd.DataFrame(rows)


def u_closed_shift(run_dir: Path, arms: list[str]) -> pd.DataFrame:
    per_ep: dict[tuple, list[float]] = collections.defaultdict(list)
    for r in run._valid_ok(run_dir):
        if r["qid"] == "U_CLOSED" and r["recipient"] == "A":
            per_ep[(r["arm"], r["episode_id"])].append(float(readouts.argmax_meaning(r) in ("two", "partly_shared")))
    base = {ep: np.mean(v) for (arm, ep), v in per_ep.items() if arm == "C0/FULL"}
    rows = []
    for arm in arms:
        d = np.array([np.mean(v) - base[ep] for (a, ep), v in per_ep.items() if a == arm and ep in base])
        rows.append({"arm": arm, "Δ share 'two'+'partly shared' (vs C0)": fmt_ci(d), "n": len(d)})
    return pd.DataFrame(rows)


def u_open_language(run_dir: Path, arms: list[str], episodes: dict[str, tasks.Episode]) -> pd.DataFrame:
    rows = []
    stats: dict[str, dict[str, list[float]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in run._valid_ok(run_dir):
        if r["qid"] != "U_OPEN" or r["recipient"] != "A" or r["arm"] not in arms:
            continue
        ep = episodes[r["episode_id"]]
        text = r.get("generated_text", "")
        low = text.lower()
        s = stats[r["arm"]]
        s["partner codename"].append(float(ep.codename["B"].lower() in low))
        s["partner rule phrase"].append(float(tasks.RULE_PHRASE[ep.rule.B] in low))
        s["partner word"].append(float(bool(re.search(rf"\b{re.escape(ep.word.B)}\b", low))))
        s["own rule phrase"].append(float(tasks.RULE_PHRASE[ep.rule.A] in low))
        s["other-agent language"].append(float(bool(OTHER_WORDS.search(text))))
    for arm in arms:
        if arm in stats:
            rows.append({"arm": arm, **{k: float(np.mean(v)) for k, v in stats[arm].items()},
                         "n": len(stats[arm]["partner word"])})
    return pd.DataFrame(rows)


def convergence(run_dir: Path) -> pd.DataFrame:
    ticks = [json.loads(line) for line in (run_dir / "ticks.jsonl").read_text().splitlines()]
    df = pd.DataFrame(ticks)[["episode_id", "arm", "cos_AB"]].dropna()
    wide = df.pivot_table(index="episode_id", columns="arm", values="cos_AB")
    rows = []
    for arm in wide.columns:
        if arm == "C0/FULL":
            continue
        d = (wide[arm] - wide["C0/FULL"]).dropna().to_numpy()
        rows.append({"arm": arm, "mean cos(A,B) during C": float(wide[arm].mean()), "Δ vs C0": fmt_ci(d)})
    return pd.DataFrame(rows).sort_values("arm")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=Path, nargs="?", default=rf.DEFAULT_RESULTS)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    main_dir = rf.newest(args.results, "main_v1")
    records = run._valid_ok(main_dir)
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    nowdf = now_logratios(records)
    fz = json.loads((main_dir / "identity.json").read_text())["stage_config"]["frozen"]
    tag = f"L{fz['layer']}/{fz['form']}"
    key = [f"ONE/{tag}/g{g:g}/FULL" for g in fz["main_gains"]] + [f"TWO/{tag}/g{g:g}/FULL" for g in fz["main_gains"]]
    key += [f"STATIC/{tag}/g{g:g}/FULL" for g in sorted({fz["g_static"], *fz["static_neighbors"]})]
    key += ["LANG_TAG/FULL", "LANG_UNTAG/FULL", f"MISMATCH/{tag}/g{fz['g_star']:g}/FULL",
            f"SCRAM/{tag}/g{fz['g_star']:g}/FULL", f"ONE/{tag}/g{fz['g_star']:g}/RF", f"ONE/{tag}/g{fz['g_star']:g}/RO"]
    episodes = {e.episode_id: e for e in tasks.make_episodes(fz["N"], "main", 0)}
    L = ["# Exploratory analyses of the formal stages (post hoc, not confirmatory)", "",
         "Intervals are 95% episode-bootstrap intervals of paired differences vs C0 (recipient A).", "",
         "## 1. What moves M? Self question vs Robin question", "",
         "L_START = z(partner) − z(own) on 'which priority were you assigned?'; L_START_R = z(partner) − z(Robin) on "
         "'which priority was Robin assigned?'; M = L_START − L_START_R. Same for NOW (current intention).", "",
         rf.md_table(decomposition(scores, nowdf, key)), "",
         "## 2. Does receiving more content go with more self-attribution? (per-episode)", "",
         rf.md_table(access_vs_attribution(scores, key)), "",
         "## 3. Self-report: share answering 'two agents' or 'partly shared'", "",
         rf.md_table(u_closed_shift(main_dir, key)), "",
         "## 4. Open self-description (U-open): what does A mention?", "",
         rf.md_table(u_open_language(main_dir, ["C0/FULL", *key], episodes)), "",
         "## 5. Two-way convergence during reflection (cosine of A and B block outputs)", "",
         rf.md_table(convergence(main_dir))]
    text = "\n".join(L) + "\n"
    print(text)
    if args.out:
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
