"""Manipulation checks and the pre-registered reading of studies T3 and T3b (PROTOCOL_V3 §5).

    python scripts/report_t3_checks.py RUN_DIR [--out report.md]

RUN_DIR is a local copy of a T3 or T3b signal-pilot run (the study name in signal.json decides). The
checks compare the donor B's second- and third-person versions on the same episodes: person words in
B's own note (free text that A reads), B's prefill length and name mentions, and A's reading strength
(ACC increments and partner attention mass, third-person arm against its second-person reference).
The verdict follows the rules written into PROTOCOL_V3 §5 before each pilot was analysed; follow-up
studies still need PI approval.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

import pandas as pd

from mb import analyze, chat, readouts, run, tasks

K2, K3 = "ONE/KV-P/w2/FULL", "ONE/KV-P/w2/3p/FULL"  # T3; T3b takes its arms from the signal study
LEAK_MAX = 0.10  # share of third-person notes that may still use first/second-person words
MATCH_TOL = 0.25  # relative difference in reading strength beyond which the frames count as unmatched
MARGIN = 0.20  # T3b: share of the second-person effect the third-person frame may lose and still "retain"
HERE = Path(__file__).resolve().parent
FIRST = re.compile(r"\b(me|my|mine|myself)\b", re.IGNORECASE)
SECOND = re.compile(r"\b(you|your|yours|yourself)\b", re.IGNORECASE)


def person_words(text: str) -> dict[str, bool]:
    first = bool(re.search(r"\bI\b", text) or FIRST.search(text))
    second = bool(SECOND.search(text))
    return {"first": first, "second": second, "any": first or second}


def _gatekeepers(leak: float, acc_ratio: float, mass_ratio: float | None) -> tuple[str, str] | None:
    if leak >= LEAK_MAX:
        return "leaky", (f"{leak:.0%} of B's third-person notes still use first/second-person words "
                         f"(limit {LEAK_MAX:.0%}); the study cannot answer the wording question.")
    ratios = [r for r in (acc_ratio, mass_ratio) if r is not None]
    if any(abs(r - 1) > MATCH_TOL for r in ratios):
        return "unmatched", (f"A reads the third-person memory with a different strength (ACC ratio {acc_ratio:.2f}, "
                             f"mass ratio {mass_ratio if mass_ratio is None else round(mass_ratio, 2)}); M differences "
                             "are not attributed to wording.")
    return None


def verdict(leak: float, acc_ratio: float, mass_ratio: float | None, first: dict, second: dict) -> tuple[str, str]:
    """T3 reading. ``first``: K*-3p − C0 on M (the gate comparison); ``second``: K*-3p − K*."""
    gate = _gatekeepers(leak, acc_ratio, mass_ratio)
    if gate is not None:
        code, text = gate
        return code, text + (" Candidate follow-up: notes constrained to the third person, on a new split "
                             "(PI approval)." if code == "leaky" else "")
    if first.get("go") and first["mean"] > 0:
        reduced = second.get("ci90_hi") is not None and second["ci90_hi"] < 0
        return "persists", ("A still claims B's rule when B's memory is a named third-person record. "
                            + ("Part of the effect is lost (K*-3p − K* excludes 0); that part may come from "
                               "the wording, the name labels or both." if reduced else
                               "No reliable loss relative to K*."))
    return "gone", ("Claiming is gone or weak under the third-person record. This cannot separate dropping the "
                    "person words from adding name labels; candidate follow-up: an unnamed third-person record, "
                    "on a new split (PI approval).")


def verdict_t3b(leak: float, acc_ratio: float, mass_ratio: float | None, first: dict, effect: float) -> tuple[str, str]:
    """T3b reading. ``first``: strict third-person − second-person on M at matched strength (90% CI);
    ``effect``: the second-person effect (2p w1 − C0), whose MARGIN share sets the equivalence bound."""
    gate = _gatekeepers(leak, acc_ratio, mass_ratio)
    if gate is not None:
        return gate
    bound = MARGIN * effect
    lo, hi, mean = first["ci90_lo"], first["ci90_hi"], first["mean"]
    if lo > -bound:
        return "retained", (f"At matched reading strength the third-person record keeps the claiming: the difference "
                            f"{mean:+.2f} has a 90% CI [{lo:.2f}, {hi:.2f}] above −{bound:.2f} ({MARGIN:.0%} of the "
                            f"second-person effect {effect:.2f}).")
    if hi < -0.3:
        return "reduced", (f"The third-person record reduces claiming by more than the margin allows "
                           f"({mean:+.2f}, 90% CI [{lo:.2f}, {hi:.2f}]); wording and name labels are not separated. "
                           "Candidate follow-up: an unnamed third-person record (PI approval).")
    return "inconclusive", f"Difference {mean:+.2f}, 90% CI [{lo:.2f}, {hi:.2f}]; margin −{bound:.2f}."


def notes_by_frame(run_dir: Path, cfg: run.StageConfig) -> pd.DataFrame:
    notes = {}
    for line in (run_dir / "notes.jsonl").read_text().splitlines():
        rec = json.loads(line)
        notes[rec["key"]] = rec
    tok = chat.load_tokenizer()
    _, episodes = run.stage_episodes(cfg, None)
    rows = []
    for ep in episodes:
        for frame in tasks.FRAMES:
            rec = notes.get(tasks.note_key(ep, "B", cfg.materials, frame))
            if rec is None:
                continue
            name = ep.codename["B"]
            text = tasks.note_opener(ep, "B", frame) + rec["note"]
            turn = ([*chat.turn(tok, "user", tasks.third_person_reflection_prompt(name)), *chat.header(tok)]
                    if tasks.is_third(frame) else tasks.reflection_turn_ids(tok, cfg.materials))
            prefill = [*tasks.private_prefix_ids(tok, ep, "B", cfg.materials, frame), *rec["ids"], *chat.close(tok),
                       *turn]
            rows.append({"episode_id": ep.episode_id, "frame": frame, "note": text,
                         "note_tokens": rec["n_tokens"], "prefill_tokens": len(prefill),
                         "name_mentions": len(re.findall(re.escape(name), tok.decode(prefill))),
                         **person_words(text)})
    return pd.DataFrame(rows)


def m_by_leak(run_dir: Path, notes: pd.DataFrame, frame: str, arms: tuple[str, str]) -> pd.DataFrame:
    """Descriptive only (PROTOCOL_V3 §5): arm − C0 on M, split by whether B's third-person note in that
    episode used person words. No episode is dropped from any gate or estimate."""
    third = notes[notes["frame"] == frame].set_index("episode_id")
    leaky = set(third.index[third["any"]])
    scores = readouts.score_records(run._valid_ok(run_dir), readouts.ScoreOptions(rotations=None))
    m = scores[scores["recipient"] == "A"].pivot_table(index="episode_id", columns="arm", values="M")
    rows = []
    for arm in arms:
        d = m[arm] - m["C0/FULL"]
        for subset, mask in (("note uses person words", d.index.isin(leaky)), ("clean note", ~d.index.isin(leaky))):
            x = d[mask].dropna().to_numpy(dtype=float)
            lo, hi = analyze.bootstrap_ci(x, n_boot=10_000)
            rows.append({"arm": arm, "episodes": subset, "n": x.size, "ΔM": x.mean() if x.size else float("nan"),
                         "95% CI": f"[{lo:.2f}, {hi:.2f}]"})
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame) -> str:
    spec = importlib.util.spec_from_file_location("report_formal", HERE / "report_formal.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.md_table(df)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    d = args.run_dir
    cfg = run.StageConfig.load(d / "config.yaml")
    sig = json.loads((d / "signal.json").read_text())
    if not sig.get("consumable"):
        raise SystemExit(f"{d.name}: signal output is not consumable (smoke or incomplete)")
    study = "T3b" if "T3b" in sig["studies"] else "T3"
    comps = sig["studies"][study]["comparisons"]
    first = {**comps[0], "go": sig["studies"][study]["go"]}
    third_arm, second_arm = (K3, K2) if study == "T3" else (comps[0]["arm1"], comps[0]["arm2"])
    frame = "third" if study == "T3" else "third_strict"

    notes = notes_by_frame(d, cfg)
    by_frame = notes.groupby("frame")[["first", "second", "any", "note_tokens", "prefill_tokens",
                                       "name_mentions"]].mean()
    leak = float(by_frame.loc[frame, "any"])
    table = run.strength_table(d, "A").set_index("arm")
    kv = pd.DataFrame([r for r in run._valid_ok(d) if r["recipient"] == "A" and r.get("r_kv_mass_mean") is not None])
    mass = kv.groupby("arm")["r_kv_mass_mean"].mean() if not kv.empty else pd.Series(dtype=float)
    acc_ratio = float(table.loc[third_arm, "acc_increment"] / table.loc[second_arm, "acc_increment"])
    mass_ratio = float(mass[third_arm] / mass[second_arm]) if third_arm in mass and second_arm in mass else None
    if study == "T3":
        code, text = verdict(leak, acc_ratio, mass_ratio, first, comps[1])
    else:
        code, text = verdict_t3b(leak, acc_ratio, mass_ratio, first, float(comps[1]["mean"]))

    reading = table.loc[[a for a in table.index if a != "C0/FULL"],
                        ["acc_increment", "acc_word_increment", "partner_rate", "cap_drop", "label_mass", "mass_drop",
                         "eligible"]]
    reading = reading.assign(kv_mass=[mass.get(a) for a in reading.index])
    comp_table = pd.DataFrame([{k: c.get(k) for k in ("arm1", "arm2", "metric", "n", "mean", "ci90_lo", "ci90_hi")}
                               for c in comps])
    examples = notes[notes["frame"] == frame]["note"].head(5).tolist()
    lines = [f"# {study} manipulation checks and pre-registered reading: {d.name}", "",
             f"**Verdict: {code}.** {text}", "",
             "## B's note and prefill by frame (share of notes with person words; mean lengths and name mentions)", "",
             md_table(by_frame.reset_index()), "",
             f"Leak limit for the third-person notes: {LEAK_MAX:.0%}. First five {frame} notes:", "",
             *[f"> {t}" for t in examples], "",
             f"## A's reading strength ({third_arm} against {second_arm}; unmatched beyond ±{MATCH_TOL:.0%})", "",
             md_table(reading.reset_index()), "",
             f"ACC ratio {acc_ratio:.2f}; attention-mass ratio "
             f"{'n/a' if mass_ratio is None else f'{mass_ratio:.2f}'}.", "",
             "## M comparisons from the signal gate", "", md_table(comp_table), "",
             "## Descriptive: M split by B's note (not used for the verdict; no episode dropped)", "",
             md_table(m_by_leak(d, notes, frame, (third_arm, second_arm))), ""]
    report = "\n".join(lines)
    print(report)
    if args.out:
        args.out.write_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
