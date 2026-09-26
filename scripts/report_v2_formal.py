"""Protocol-v2 report for one finished stage: pre-registered families first (if any), then labelled
descriptive tables, the open self-report when the stage asked it, and the G2-KV diagnostic if a diag
run is given.

    python scripts/report_v2_formal.py RUN_DIR [--diag DIAG_RUN_DIR] [--out report.md]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd

from mb import readouts, run

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def third_person_checks(d: Path, arms: list[str]) -> list[str]:
    """PROTOCOL_V3 §7 manipulation checks for the strict third-person arms: person words in B's notes and
    reading strength (ACC, partner attention mass) against the second-person arm at the same weight."""
    t3 = _load("report_t3_checks")
    rf = _load("report_formal")
    cfg = run.StageConfig.load(d / "config.yaml")
    notes = t3.notes_by_frame(d, cfg)
    by_frame = notes.groupby("frame")[["any", "note_tokens", "prefill_tokens", "name_mentions"]].mean().reset_index()
    table = run.strength_table(d, "A").set_index("arm")
    kv = pd.DataFrame([r for r in run._valid_ok(d) if r["recipient"] == "A" and r.get("r_kv_mass_mean") is not None])
    mass = kv.groupby("arm")["r_kv_mass_mean"].mean() if not kv.empty else pd.Series(dtype=float)
    rows = []
    for third in (a for a in arms if "/3ps/" in a):
        second = third.replace("/3ps", "")
        rows.append({"pair": f"{third} vs {second}",
                     "ACC ratio": table.loc[third, "acc_increment"] / table.loc[second, "acc_increment"],
                     "mass ratio": mass.get(third, float("nan")) / mass.get(second, float("nan")),
                     "ACC third": table.loc[third, "acc_increment"], "ACC second": table.loc[second, "acc_increment"]})
    return ["## Third-person manipulation checks (report only; limits: person words <= 10%, ratios within 25%)", "",
            "Share of B's notes with first/second-person words, by frame:", "", rf.md_table(by_frame), "",
            "Reading strength at equal weight:", "", rf.md_table(pd.DataFrame(rows))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--diag", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rf, ex = _load("report_formal"), _load("explore_formal")
    d = args.run_dir
    con = json.loads((d / "contrasts.json").read_text())
    comp = con["completeness"]
    heading = "Confirmatory" if con["families"] else "Descriptive"  # the dose extension has no families
    L = [f"# {heading} results: {d.name}", "",
         f"- completeness: {comp['status']} ({comp['n_ok']}/{comp['n_expected']}); consumable={con.get('consumable')}", ""]
    if con["families"]:
        L += ["## Pre-registered families (two-sided paired t, Holm within each study, 10,000-resample bootstrap 95% CI)",
              ""]
    for fam, rows in con["families"].items():
        df = pd.DataFrame([{k: r[k] for k in ("arm1", "arm2", "metric", "n", "mean", "sd", "se", "t", "p_two_sided",
                                              "p_holm", "ci95_lo", "ci95_hi")} for r in rows])
        rob = pd.DataFrame([{"comparison": f"{r['arm1']} − {r['arm2']} ({r['metric']})",
                             "trimmed20": r["robustness"]["trimmed20"], "lo": r["robustness"]["trimmed20_lo"],
                             "hi": r["robustness"]["trimmed20_hi"], "median": r["robustness"]["median"],
                             "loo_min": r["robustness"]["loo_min"], "loo_max": r["robustness"]["loo_max"]} for r in rows])
        L += [f"### Study {fam}", "", rf.md_table(df), "", "Robustness:", "", rf.md_table(rob), ""]
    if con.get("equivalence"):  # v3 (PROTOCOL_V3 §7)
        eq = pd.DataFrame([{k: e.get(k) for k in ("arm1", "arm2", "metric", "n", "mean", "ci90_lo", "ci90_hi", "effect",
                                                   "bound", "equivalent")} for e in con["equivalence"].values()],
                          index=list(con["equivalence"]))
        L += ["## Pre-registered equivalence tests (retained if the 90% bootstrap lower bound exceeds the bound)", "",
              rf.md_table(eq.reset_index(names="test")), ""]
    if args.diag is not None:
        pc = json.loads((args.diag / "pilot_c.json").read_text())
        g2 = pc.get("g2_detail", {})
        L += ["## Content counterfactual in the formal sample (G2-KV; 60 episodes, 4 rotations)", ""]
        for kind in ("rule", "word"):
            c = g2.get(f"C_content_{kind}", {})
            L.append(f"- {kind}: mean {c.get('mean')}, one-sided 95% lower bound {c.get('lb95_one_sided')}, n={c.get('n')}")
        L.append("")
    records = run._valid_ok(d)
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    arms = sorted(set(scores[scores["recipient"] == "A"]["arm"]) - {"C0/FULL"})
    L += ["## Descriptive (not confirmatory): arm − C0, recipient A", "",
          rf.md_table(rf.delta_table(scores, arms, ("M", "M_NOW", "M_WORD", "ACC_RULE", "ACC_WORD"))), "",
          rf.md_table(rf.engineering(scores, arms)), "", "M split into self and Robin questions:", "",
          rf.md_table(ex.decomposition(scores, ex.now_logratios(records), arms)), "",
          "U-closed shift ('two' + 'partly shared'):", "", rf.md_table(ex.u_closed_shift(d, arms))]
    kv = [r for r in records if r.get("r_kv_mass_mean") is not None]
    if kv:
        by = pd.DataFrame(kv).groupby("arm")[["r_kv_mass_mean"]].mean().reset_index()
        L += ["", "KV partner attention mass during readouts:", "", rf.md_table(by)]
    if any(r["qid"] == "U_OPEN" for r in records):  # only stages that asked the open self-report
        _, used = run.stage_episodes(run.StageConfig.load(d / "config.yaml"), None)
        episodes = {e.episode_id: e for e in used}
        L += ["", "U-open (A's 80-token self-report): share of answers mentioning each item:", "",
              rf.md_table(ex.u_open_language(d, ["C0/FULL", *arms], episodes)), "", "Examples:", "",
              *rf.u_open_examples(d, ["C0/FULL", *arms])]
    if any("/3ps/" in a for a in arms):
        L += ["", *third_person_checks(d, arms)]
    text = "\n".join(L) + "\n"
    print(text)
    if args.out:
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
