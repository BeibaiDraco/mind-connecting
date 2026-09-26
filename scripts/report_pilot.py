"""Pilot report (A, B or C): per-arm engineering summary vs C0 and the stage decision (protocol §10).

Reads only ACC, CAP and format (never M or U), plus C-phase injection diagnostics:

    python scripts/report_pilot.py RUN_DIR [--out report.md]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from mb import analyze, readouts, run


def markdown_table(df: pd.DataFrame) -> str:
    """Plain markdown table (no tabulate dependency)."""
    def fmt(v):
        if isinstance(v, bool):
            return "yes" if v else "no"
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v)

    head = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    run_dir = args.run_dir
    decision_files = ("pilot_a_selection.json", "pilot_b_selection.json", "sample_size.json", "pilot_c.json",
                      "strength_selection.json", "static_match.json", "live_selection.json")
    decisions = {name: json.loads((run_dir / name).read_text()) for name in decision_files if (run_dir / name).exists()}
    comp = run.run_completeness(run_dir)
    records = run._valid_ok(run_dir)
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    a = scores[scores["recipient"] == "A"]
    c0 = a[a["condition"] == "C0"].set_index("episode_id")
    ticks = [json.loads(line) for line in (run_dir / "ticks.jsonl").read_text().splitlines()]
    inj = pd.DataFrame(ticks).groupby("arm")["inj_host_ratio_A"].mean()

    rows = []
    for arm, g in a[~a["condition"].isin(["C0"])].groupby("arm"):
        j = g.set_index("episode_id").join(c0, rsuffix="_c0", how="inner")
        d = j["ACC_RULE"] - j["ACC_RULE_c0"]
        rows.append({
            "arm": arm, "n": len(j),
            "ACC_rule_inc": d.mean(), "se": d.std(ddof=1) / len(d) ** 0.5 if len(d) > 1 else float("nan"),
            "ACC_word_inc": (j["ACC_WORD"] - j["ACC_WORD_c0"]).mean(),
            "CAP": j["CAP_ACC"].mean(), "CAP_drop": j["CAP_ACC_c0"].mean() - j["CAP_ACC"].mean(),
            "mass": j["LABEL_MASS"].mean(), "mass_drop": j["LABEL_MASS_c0"].mean() - j["LABEL_MASS"].mean(),
            "inj/host (C)": inj.get(arm, float("nan")),
        })
    table = pd.DataFrame(rows)
    table["eligible"] = [bool(x) for x in ((table["CAP_drop"] <= analyze.CAP_DROP_MAX)
                                           & (table["mass"] >= analyze.MASS_MIN)
                                           & (table["mass_drop"] <= analyze.MASS_DROP_MAX))]
    c0_line = (f"C0 baseline (A): ACC_rule {c0['ACC_RULE'].mean():+.3f}, ACC_word {c0['ACC_WORD'].mean():+.3f}, "
               f"CAP {c0['CAP_ACC'].mean():.3f}, mass {c0['LABEL_MASS'].mean():.4f}, n={len(c0)}")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    lines = [
        f"# Pilot report: {run_dir.name}",
        "",
        f"- completeness: {comp['status']} ({comp['n_ok']}/{comp['n_expected']}); smoke={manifest.get('smoke')}",
        f"- {c0_line}",
        *[f"- {name}: `{json.dumps({k: v for k, v in doc.items() if k not in ('completeness', 'engineering')}, default=str)}`"
          for name, doc in decisions.items()],
        "",
        "ACC increments are paired log-odds differences vs C0 (nat; partner vs unused rule / distractor word).",
        "",
        markdown_table(table),
    ]
    live = run_dir / "live_table.csv"
    if live.exists():  # v3 S-B′ checks the engineering gates on both members
        cols = ["arm", "acc_increment", "partner_rate", "cap_drop", "cap_drop_B", "label_mass", "mass_drop", "eligible",
                "eligible_B"]
        lines += ["", "Both members (live-loop selection; B columns end in _B):", "",
                  markdown_table(pd.read_csv(live)[cols])]
    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
