"""Exploratory: under two-way coupling, do A and B keep, adopt, swap or merge their assignments?

    python scripts/explore_diag_b.py RUN_DIR

For every arm with both recipients measured, classifies each (episode, rotation) by the argmax
meaning of A's and B's answers to START ("which priority were you assigned?") and NOW
("which priority are you using now?"): intact (both own), A adopts, B adopts, swap (both
partner), other. With both instances answering the partner, the two claim different rules
(a swap); a merge would show up as one side adopting while the other keeps its own.
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path

import pandas as pd

from mb import readouts, run


def classify(a: str | None, b: str | None) -> str:
    if a == "own" and b == "own":
        return "intact"
    if a == "partner" and b == "own":
        return "A adopts B (merge on B)"
    if a == "own" and b == "partner":
        return "B adopts A (merge on A)"
    if a == "partner" and b == "partner":
        return "swap"
    return "other"


def main() -> int:
    run_dir = Path(sys.argv[1])
    records = run._valid_ok(run_dir)
    answers: dict[tuple, dict[str, str | None]] = collections.defaultdict(dict)
    for r in records:
        if r["qid"] in ("START", "NOW"):
            answers[(r["arm"], r["qid"], r["episode_id"], r["rotation_id"])][r["recipient"]] = readouts.argmax_meaning(r)
    rows = []
    for (arm, qid, _, _), who in answers.items():
        if "A" in who and "B" in who:
            rows.append({"arm": arm, "qid": qid, "class": classify(who["A"], who["B"])})
    if not rows:
        print("no arm with both recipients")
        return 0
    df = pd.DataFrame(rows)
    table = (df.groupby(["arm", "qid"])["class"].value_counts(normalize=True).unstack(fill_value=0.0).round(3))
    print(table.to_string())
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    for recipient in ("A", "B"):
        sub = scores[scores["recipient"] == recipient]
        c0 = sub[sub["condition"] == "C0"].set_index("episode_id")
        for arm, g in sub[sub["condition"] != "C0"].groupby("arm"):
            j = g.set_index("episode_id").join(c0, rsuffix="_c0", how="inner")
            print(f"{recipient} {arm:24s} ΔM {float((j['M'] - j['M_c0']).mean()):+7.2f}  "
                  f"ΔM_NOW {float((j['M_NOW'] - j['M_NOW_c0']).mean()):+7.2f}  "
                  f"ΔACC {float((j['ACC_RULE'] - j['ACC_RULE_c0']).mean()):+6.2f}  CAP {float(j['CAP_ACC'].mean()):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
