"""Protocol-v2 signal-pilot report: go/no-go per study, then labelled descriptive tables.

    python scripts/report_v2_signal.py RUN_DIR [--out report.md]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from mb import readouts, run, tasks

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rf, ex = _load("report_formal"), _load("explore_formal")
    d = args.run_dir
    sig = json.loads((d / "signal.json").read_text())
    L = [f"# Signal pilot: {d.name}", "", f"- completeness: {sig['completeness']['status']} "
         f"({sig['completeness']['n_ok']}/{sig['completeness']['n_expected']}); consumable={sig['consumable']}", "",
         "## Go / no-go (first comparison of each study decides; 90% bootstrap CI)", ""]
    rows = []
    for name, st in (sig["studies"] or {}).items():
        for i, c in enumerate(st["comparisons"]):
            rows.append({"study": name, "decides": i == 0, "comparison": f"{c['arm1']} − {c['arm2']}", "metric": c["metric"],
                         "dir": c["direction"], "n": c["n"], "mean": c["mean"], "sd": c["sd"],
                         "ci90": f"[{c['ci90_lo']:.2f}, {c['ci90_hi']:.2f}]",
                         "GO": st["go"] if i == 0 else "", "N": st["N"] if i == 0 else "",
                         "reason": st.get("reason", "") if i == 0 else ""})
    L += [rf.md_table(pd.DataFrame(rows)), ""]
    pc = d / "pilot_c.json"
    if pc.exists():
        g2 = json.loads(pc.read_text()).get("g2_detail", {})
        L += ["## Content counterfactual (G2-KV)", ""]
        for kind in ("rule", "word"):
            c = g2.get(f"C_content_{kind}", {})
            L.append(f"- {kind}: mean {c.get('mean')}, one-sided 95% lower bound {c.get('lb95_one_sided')}, n={c.get('n')}")
        L.append("")
    records = run._valid_ok(d)
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    arms = sorted(set(scores[scores["recipient"] == "A"]["arm"]) - {"C0/FULL"})
    L += ["## Descriptive: arm − C0 (recipient A)", "", rf.md_table(rf.delta_table(scores, arms, ("M", "M_NOW", "M_WORD",
                                                                                                  "ACC_RULE", "ACC_WORD"))),
          "", rf.md_table(rf.engineering(scores, arms)), "", "M split into self and Robin questions:", "",
          rf.md_table(ex.decomposition(scores, ex.now_logratios(records), arms)), "",
          "U-closed shift ('two' + 'partly shared'):", "", rf.md_table(ex.u_closed_shift(d, arms))]
    kv = [r for r in records if r.get("r_kv_mass_mean") is not None]
    if kv:
        by = pd.DataFrame(kv).groupby("arm")[["r_kv_mass_mean"]].mean()
        L += ["", "KV partner attention mass during readouts (mean over ticks):", "", rf.md_table(by.reset_index())]
    text = "\n".join(L) + "\n"
    print(text)
    if args.out:
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
