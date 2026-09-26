"""Protocol-v3 B′ signal-pilot report: go/no-go per study, pair outcomes, then both members' tables.

    python scripts/report_v3_pair_signal.py RUN_DIR [--out report.md]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from mb import readouts, run

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def comparison_rows(study: str, comps: list[dict], st: dict | None = None) -> list[dict]:
    rows = []
    for i, c in enumerate(comps):
        lo, hi = c.get("ci90_lo"), c.get("ci90_hi")
        rows.append({"study": study, "decides": st is not None and i == 0,
                     "comparison": f"{c['arm1']} − {c['arm2'] or '0'}", "qid": c["qid"], "outcome": c["outcome"],
                     "n": c["n"], "mean": c["mean"], "ci90": "NA" if lo is None or np.isnan(lo) else f"[{lo:.3f}, {hi:.3f}]",
                     "arm1 excess": c.get("arm1_excess"), "arm2 excess": c.get("arm2_excess"),
                     "arm1 rate": c.get("arm1_rate"), "arm2 rate": c.get("arm2_rate"),
                     "GO": st["go"] if st is not None and i == 0 else "",
                     "N": st["N"] if st is not None and i == 0 else ""})
    return rows


def outcome_table(pairs: pd.DataFrame, qid: str) -> pd.DataFrame:
    sub = pairs[pairs["qid"] == qid]
    g = sub.groupby("arm")[[*run.PAIR_OUTCOMES, *run.PAIR_MARGINALS]].mean()
    x = {arm: s[list(run.EXCESS_COLUMNS)].to_numpy(dtype=float) for arm, s in sub.groupby("arm")}
    g["expected one_wins"] = g["a_partner"] * g["b_own"] + g["a_own"] * g["b_partner"]
    g["excess"] = [float(run.one_wins_excess(x[arm])) for arm in g.index]
    g["n"] = sub.groupby("arm").size()
    return g.reset_index()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rf, ex = _load("report_formal"), _load("explore_formal")
    d = args.run_dir
    sig = json.loads((d / "pair_signal.json").read_text())
    comp = sig["completeness"]
    L = [f"# B′ signal pilot: {d.name}", "",
         f"- completeness: {comp['status']} ({comp['n_ok']}/{comp['n_expected']}); consumable={sig['consumable']}", "",
         "## Go / no-go (first comparison of each study decides; 90% bootstrap CI, episodes resampled)", ""]
    rows = [r for name, st in (sig["studies"] or {}).items() for r in comparison_rows(name, st["comparisons"], st)]
    L += [rf.md_table(pd.DataFrame(rows)), "", "## Descriptive comparisons (not in the gate or N)", ""]
    rows = [r for name, comps in sig.get("descriptive", {}).items() for r in comparison_rows(name, comps)]
    L += [rf.md_table(pd.DataFrame(rows)) if rows else "(none)", ""]
    pairs = pd.read_csv(d / "pair_outcomes.csv")
    for qid in ("START", "NOW"):
        L += [f"## Pair outcomes on {qid} (share of rotations, episodes weigh equally)", "",
              rf.md_table(outcome_table(pairs, qid)), ""]
    records = run._valid_ok(d)
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    for side in ("A", "B"):
        arms = sorted(set(scores[scores["recipient"] == side]["arm"]) - {"C0/FULL"})
        L += [f"## Member {side}: arm − C0", "",
              rf.md_table(rf.delta_table(scores, arms, ("M", "M_NOW", "ACC_RULE", "ACC_WORD"), recipient=side)), "",
              rf.md_table(rf.engineering(scores, arms, recipient=side)), ""]
    kv = [r for r in records if r.get("r_kv_mass_mean") is not None]
    if kv:
        by = pd.DataFrame(kv).groupby(["arm", "recipient"])[["r_kv_mass_mean"]].mean().reset_index()
        L += ["KV partner attention mass during FULL readouts:", "", rf.md_table(by), ""]
    text = "\n".join(L) + "\n"
    print(text)
    if args.out:
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
