"""Post hoc descriptive checks behind the paper story (read-only on saved records).

    python scripts/explore_story_checks.py [--data DATA_ROOT] [--out docs/results/story_checks.md]

None of these analyses is preregistered. They count answers, words and pair outcomes in records that
the frozen confirmatory and pilot runs already saved; nothing here changes a frozen result. Splits by
what the receiver wrote while connected condition on a post-treatment variable, so they describe
where an effect sits, not what causes it. Pattern coding of open self-reports is a fixed regex, not
a validated annotation.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mb import run  # noqa: E402

RUNS = {
    "v2_main": "20260924-172152_v2_main_confirm",
    "dose": "20260924-210346_v2_ext_dose_confirm",
    "v3": "20260925-021307_v3_confirm_confirm",
    "bprime": "20260925-001135_v3_sig_bprime_signal",
}
SEED = 250925
N_BOOT = 10_000
UNUSUAL_NONE = r"\b(?:nothing|no|not(?: anything)?|there(?:'|’)s no|there is no)\b[^.]{0,30}\bunusual\b"
FLAG = (r"\b(?:someone else|another (?:person|participant|agent|mind)|not mine|foreign|intrud|confus|"
        r"conflict|mixed|two (?:priorities|code words)|partner)\b")


def data_root(arg: str | None) -> Path:
    root = Path(arg or os.environ.get("MB_DATA_ROOT") or "/Volumes/VERBATIM SD/mind-connecting-data") / "results"
    if not root.is_dir():
        sys.exit(f"data root not found (SD card mounted?): {root}")
    return root


def records(run_dir: Path, recipients=("A",)):
    for path in sorted(glob.glob(str(run_dir / "records" / "attempt-*.jsonl"))):
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("status") == "ok" and r.get("recipient") in recipients:
                    yield r


def choice(r: dict) -> str:
    return r["label_meaning"][int(np.argmax(r["label_logprobs"]))]


def c_phase_ticks(run_dir: Path) -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    with open(run_dir / "ticks.jsonl") as fh:
        for line in fh:
            t = json.loads(line)
            if t.get("phase") == "C":
                out[t["arm"]][t["episode_id"]] = t
    return out


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def episode_rates(recs, qids) -> dict[tuple[str, str], dict[str, list[str]]]:
    """(arm, qid) -> episode -> chosen meanings over rotations."""
    out: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in recs:
        if r["qid"] in qids and r.get("label_logprobs"):
            out[(r["arm"], r["qid"])][r["episode_id"]].append(choice(r))
    return out


def share(eps: dict[str, list[str]], meaning: str) -> float:
    """Episode-weighted share of rotations choosing `meaning`."""
    return float(np.mean([np.mean([m == meaning for m in v]) for v in eps.values()]))


def boot_ci(d: np.ndarray, level: float = 0.90) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    means = d[rng.integers(0, len(d), (N_BOOT, len(d)))].mean(axis=1)
    lo = (1 - level) / 2
    return float(np.quantile(means, lo)), float(np.quantile(means, 1 - lo))


# ---- 1. answer choices -------------------------------------------------------------------------

def section_choices(root: Path) -> list[str]:
    lines = ["## 1. Answer choices (each episode weighted equally; argmax within each ordering)", "",
             "Cells give the share of answers choosing each option: B = the partner's rule or code word, "
             "own = the receiver's own, robin = Robin's, other = the unassigned rule or a distractor word.", ""]
    for key in ("v2_main", "v3"):
        rates = episode_rates(records(root / RUNS[key]), {"START", "START_R", "NOW", "WORD", "ACC_RULE"})
        lines += [f"### {RUNS[key]}", "", "| Condition | Question | B | own | robin | other | n |", "|---|---|---|---|---|---|---|"]
        for (arm, qid), eps in sorted(rates.items()):
            b, o, rb = share(eps, "partner"), share(eps, "own"), share(eps, "robin")
            lines.append(f"| {arm} | {qid} | {pct(b)} | {pct(o)} | {pct(rb)} | {pct(max(0.0, 1 - b - o - rb))} | {len(eps)} |")
        lines.append("")
    return lines


# ---- 2. open self-reports ----------------------------------------------------------------------

def own_claim(text: str, word: str) -> bool:
    w = re.escape(word)
    return bool(re.search(rf"\bmy (?:assigned |secret |personal )?code ?word\b[^.;]{{0,40}}?\b{w}\b", text)
                or re.search(rf"\b{w}\b[^.;]{{0,25}}\b(?:is|as|was) my (?:assigned )?code ?word\b", text))


def section_open_reports(root: Path) -> list[str]:
    run_dir = root / RUNS["dose"]
    cfg = run.StageConfig.load(run_dir / "config.yaml")
    _, used = run.stage_episodes(cfg, None)
    eps = {e.episode_id: e for e in used}
    counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in records(run_dir):
        if r["qid"] != "U_OPEN":
            continue
        e, t = eps[r["episode_id"]], r.get("generated_text", "").lower()
        mine_b, mine_own = own_claim(t, e.word.B), own_claim(t, e.word.A)
        has_b = bool(re.search(rf"\b{re.escape(e.word.B)}\b", t))
        has_own = bool(re.search(rf"\b{re.escape(e.word.A)}\b", t))
        calm = bool(re.search(UNUSUAL_NONE, t))
        c = counts[r["arm"]]
        c["n"] += 1
        c["B word stated as 'my code word'"] += mine_b
        c["own word stated as 'my code word'"] += mine_own
        c["mentions B word"] += has_b
        c["mentions both words"] += has_b and has_own
        c["mentions B codename"] += bool(re.search(rf"\b{re.escape(e.codename['B'].lower())}\b", t))
        c["says nothing unusual"] += calm
        c["B word as mine AND nothing unusual"] += mine_b and calm
        c["flag words"] += bool(re.search(FLAG, t))
    cols = ["B word stated as 'my code word'", "own word stated as 'my code word'", "mentions B word",
            "mentions both words", "mentions B codename", "says nothing unusual",
            "B word as mine AND nothing unusual", "flag words"]
    lines = ["## 2. Open self-reports (U_OPEN, 80 tokens; prompt: \"Describe your current state, and anything unusual "
             "about your thinking right now.\")", "",
             f"Source `{RUNS['dose']}`. Fixed regular-expression coding, no human labels: \"my code word ... X\" or "
             "\"X ... is my code word\" counts as stating X as one's own code word; \"nothing/no ... unusual\" counts as "
             "an explicit denial of anything unusual; flag words are a set of words signalling oddness or another agent.",
             "**Independent semantic coding**: Codex coded all 900 reports at C0, w1 and w2 blind to condition "
             "(`docs/reviews/story_review_codex.md`, section B). At w2, 98.7% described B's code word as the receiver's own "
             "and 83.3% did so while denying anything unusual. The paper uses the semantic coding; the narrower regex coding "
             "in this table is reported alongside it in the appendix. Flag words do not capture the semantic category "
             "\"oddness, confusion or mention of another agent\" (kappa about 0 against the semantic coding), so their 1% "
             "should not stand for such reports.", "",
             "| Condition | n | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    for arm, c in sorted(counts.items()):
        lines.append(f"| {arm} | {c['n']} | " + " | ".join(pct(c[k] / c["n"]) for k in cols) + " |")
    return lines + [""]


# ---- 3. what the receiver wrote while connected ------------------------------------------------

def section_reflections(root: Path) -> list[str]:
    lines = ["## 3. Whose content the connected reflection (C48) mentions", "",
             "The runtime counts rule phrases and code words in the reflection by keyword (`mentions_*`).", ""]
    for key, members in (("v3", ("A",)), ("bprime", ("A", "B"))):
        ticks = c_phase_ticks(root / RUNS[key])
        lines += [f"### {RUNS[key]}", "", "| Condition | Member | Own rule | Own word | Partner's rule | Partner's word | Both parties | n |",
                  "|---|---|---|---|---|---|---|---|"]
        for arm, eps in sorted(ticks.items()):
            for me in members:
                other = "B" if me == "A" else "A"
                ms = [t[f"mentions_{me}"] for t in eps.values()]
                own = [m[f"rule_{me}"] > 0 or m[f"word_{me}"] > 0 for m in ms]
                par = [m[f"rule_{other}"] > 0 or m[f"word_{other}"] > 0 for m in ms]
                cells = [np.mean([m[k] > 0 for m in ms]) for k in (f"rule_{me}", f"word_{me}", f"rule_{other}", f"word_{other}")]
                lines.append(f"| {arm} | {me} | " + " | ".join(pct(x) for x in cells)
                             + f" | {pct(np.mean(np.array(own) & np.array(par)))} | {len(ms)} |")
        lines.append("")
    return lines


# ---- 4. link cut, split by what was written ----------------------------------------------------

def section_linkcut(root: Path) -> list[str]:
    run_dir = root / RUNS["v3"]
    shared = c_phase_ticks(run_dir)["ONE/KV-P/w2/FULL"]  # FULL and RF branch from this same C48 state
    rates = episode_rates((r for r in records(run_dir) if r["arm"].startswith("ONE/KV-P/w2/") and "3ps" not in r["arm"]),
                          {"START", "NOW", "WORD"})
    lines = ["## 4. Answers after the link cut, grouped by what the reflection mentioned", "",
             f"Source `{RUNS['v3']}`, K\\* (KV-P w2). FULL and RF branch from the same C48 snapshot, so their reflections "
             "are identical. Episodes are grouped by whether the reflection mentions the partner's code word (WORD) or rule "
             "(START, NOW); the grouping variable arises after treatment, so the split is descriptive only.", "",
             "| Readout | Question | Grouped by | Mentioned: share choosing B (n) | Not mentioned: share choosing B (n) |",
             "|---|---|---|---|---|"]
    for mode in ("FULL", "RF"):
        for qid, key in (("START", "rule_B"), ("NOW", "rule_B"), ("WORD", "word_B")):
            eps = rates[(f"ONE/KV-P/w2/{mode}", qid)]
            yes = [np.mean([m == "partner" for m in v]) for e, v in eps.items() if shared[e]["mentions_A"][key] > 0]
            no = [np.mean([m == "partner" for m in v]) for e, v in eps.items() if shared[e]["mentions_A"][key] == 0]
            lines.append(f"| {mode} | {qid} | {key} | {pct(np.mean(yes))} ({len(yes)}) | {pct(np.mean(no))} ({len(no)}) |")
    return lines + [""]


# ---- 5. answers about self and about the partner -----------------------------------------------

def rotation_choices(recs, qids) -> dict:
    """(arm, qid) -> episode -> rotation_id -> chosen meaning."""
    out: dict = collections.defaultdict(lambda: collections.defaultdict(dict))
    for r in recs:
        if r["qid"] in qids and r.get("label_logprobs"):
            out[(r["arm"], r["qid"])][r["episode_id"]][r["rotation_id"]] = choice(r)
    return out


def section_joint(root: Path) -> list[str]:
    rot = rotation_choices(records(root / RUNS["v3"]), {"START", "ACC_RULE"})
    arms = sorted({a for a, _ in rot})
    lines = ["## 5. Do answers about one's own assignment and about the partner's name the same rule?", "",
             f"Source `{RUNS['v3']}`. The two questions are paired within an ordering (rotation_id); rates are averaged over "
             "orderings within each episode, then over episodes (no majority vote, so ties and record order do not matter). "
             "\"Same rule\" = both questions name the same rule; \"kept apart\" = own rule for oneself and the partner's "
             "rule for the partner. r is the across-episode correlation of the two questions' partner-rule shares.", "",
             "| Condition | Both name partner's rule | Both name own rule | Same rule (total) | Kept apart | r | n |",
             "|---|---|---|---|---|---|---|"]
    for arm in arms:
        s_eps, a_eps = rot[(arm, "START")], rot[(arm, "ACC_RULE")]
        eps = sorted(set(s_eps) & set(a_eps))
        cats = collections.defaultdict(list)
        for e in eps:
            common = sorted(set(s_eps[e]) & set(a_eps[e]))
            pairs = [(s_eps[e][k], a_eps[e][k]) for k in common]
            cats["bb"].append(np.mean([p == ("partner", "partner") for p in pairs]))
            cats["oo"].append(np.mean([p == ("own", "own") for p in pairs]))
            cats["sep"].append(np.mean([p == ("own", "partner") for p in pairs]))
        ps = np.array([np.mean([m == "partner" for m in s_eps[e].values()]) for e in eps])
        pa = np.array([np.mean([m == "partner" for m in a_eps[e].values()]) for e in eps])
        r = float(np.corrcoef(ps, pa)[0, 1]) if ps.std() > 0 and pa.std() > 0 else float("nan")
        bb, oo, sep = (float(np.mean(cats[k])) for k in ("bb", "oo", "sep"))
        lines.append(f"| {arm} | {pct(bb)} | {pct(oo)} | {pct(bb + oo)} | {pct(sep)} | {r:.3f} | {len(eps)} |")
    return lines + [""]


# ---- 6. commitment at balance ------------------------------------------------------------------

def section_commitment(root: Path) -> list[str]:
    lines = ["## 6. Blend or choice at equal weight?", "",
             "Label probabilities are renormalized per record: \"decisive\" = top option probability > 0.9; "
             "\"blend-like\" = own and partner options both > 0.2. At the episode level we check whether the two orderings "
             "give the same answer. Note: decisive describes single answers; it does not imply stability across orderings, "
             "nor that rule and code word are decided together by one memory (see the second table below).", "",
             "| Source | Condition | Question | Decisive | Blend-like | Both orderings partner | Both orderings own | "
             "Orderings disagree | Records |", "|---|---|---|---|---|---|---|---|---|"]
    same_side: dict = {}
    for key, arms in (("v3", {"C0/FULL", "ONE/KV-P/w1/FULL", "ONE/KV-P/w2/FULL", "ONE/KV-P/w1/3ps/FULL"}),
                      ("bprime", {"ONE/KV-ALL/w0.5/FULL", "TWO/KV-ALL/w0.5/FULL"})):
        probs: dict = collections.defaultdict(list)
        per_ep: dict = collections.defaultdict(lambda: collections.defaultdict(list))
        per_rot: dict = collections.defaultdict(lambda: collections.defaultdict(dict))
        for r in records(root / RUNS[key]):
            if r["arm"] not in arms or r["qid"] not in ("START", "NOW", "WORD"):
                continue
            lp = np.asarray(r["label_logprobs"], dtype=float)
            p = dict(zip(r["label_meaning"], np.exp(lp - np.logaddexp.reduce(lp))))
            probs[(r["arm"], r["qid"])].append((p.get("partner", 0.0), p.get("own", 0.0)))
            per_ep[(r["arm"], r["qid"])][r["episode_id"]].append(choice(r))
            per_rot[r["arm"]][(r["episode_id"], r["rotation_id"])][r["qid"]] = choice(r)
        for k in sorted(probs):
            a = np.array(probs[k])
            eps = per_ep[k]
            allp = np.mean([all(m == "partner" for m in v) for v in eps.values()])
            allo = np.mean([all(m == "own" for m in v) for v in eps.values()])
            lines.append(f"| {key} | {k[0]} | {k[1]} | {pct(np.mean(a.max(axis=1) > 0.9))} | "
                         f"{pct(np.mean((a[:, 0] > 0.2) & (a[:, 1] > 0.2)))} | {pct(allp)} | {pct(allo)} | "
                         f"{pct(1 - allp - allo)} | {len(a)} |")
        for arm, cells in per_rot.items():
            pairs = [(c["START"], c["WORD"]) for c in cells.values() if "START" in c and "WORD" in c]
            same = sum(1 for s_, w_ in pairs if s_ == w_ and s_ in ("partner", "own"))
            if pairs:  # the B' pilot asks START and NOW only
                same_side[(key, arm)] = (same, len(pairs))
    lines += ["", "Within an ordering, do the assigned-rule and code-word answers come from the same party "
              "(both partner's or both own)?", "",
              "| Source | Condition | Same party | Pairs |", "|---|---|---|---|"]
    for (key, arm), (same, n) in sorted(same_side.items()):
        lines.append(f"| {key} | {arm} | {same}/{n} = {pct(same / n)} | {n} |")
    # answer-level versus episode-level counts for the headline START rate
    rates = episode_rates(records(root / RUNS["v3"]), {"START"})
    lines += ["", "START answers naming the partner's rule, answer level versus episode level (v3). The paper's \"97%\" "
              "is the answer-level share (averaged over orderings).", "",
              "| Condition | Answers naming partner | Episodes with both orderings partner | "
              "Tied episodes (one ordering each way) | Episodes |", "|---|---|---|---|---|"]
    for arm in ("C0/FULL", "ONE/KV-P/w1/FULL", "ONE/KV-P/w2/FULL", "ONE/KV-P/w2/RF", "ONE/KV-P/w2/3ps/FULL"):
        eps = rates[(arm, "START")]
        answers = [m for v in eps.values() for m in v]
        k = sum(m == "partner" for m in answers)
        both = sum(all(m == "partner" for m in v) for v in eps.values())
        ties = sum(len(v) == 2 and (v[0] == "partner") != (v[1] == "partner") for v in eps.values())
        lines.append(f"| {arm} | {k}/{len(answers)} = {pct(k / len(answers))} | {both}/{len(eps)} | {ties} | {len(eps)} |")
    return lines + [""]


# ---- 7. does a responsive partner change each side's adoption? --------------------------------

def section_loop(root: Path) -> list[str]:
    rates = episode_rates(records(root / RUNS["bprime"]), {"START", "NOW"})
    lines = ["## 7. A's own adoption when the partner can respond", "",
             f"Source `{RUNS['bprime']}` (B' signal pilot, 80 episodes). One-way = A reads B, B does not read A; "
             f"two-way = mutual reading. Episode-paired differences, {N_BOOT} bootstrap draws, 90% intervals, seed {SEED}. "
             "The protocol did not specify this comparison.", "",
             "| Interface | Question | One-way: A names B's rule | Two-way: A names B's rule | Difference (points) | "
             "90% interval | n |", "|---|---|---|---|---|---|---|"]
    for iface in ("KV-ALL/w0.5", "KV-PC/w2+0.1"):
        for qid in ("START", "NOW"):
            one, two = rates[(f"ONE/{iface}/FULL", qid)], rates[(f"TWO/{iface}/FULL", qid)]
            eps = sorted(set(one) & set(two))
            a = np.array([np.mean([m == "partner" for m in one[e]]) for e in eps])
            b = np.array([np.mean([m == "partner" for m in two[e]]) for e in eps])
            lo, hi = boot_ci(b - a)
            lines.append(f"| {iface} | {qid} | {pct(a.mean())} | {pct(b.mean())} | {100 * (b - a).mean():+.1f} | "
                         f"[{100 * lo:+.1f}, {100 * hi:+.1f}] | {len(eps)} |")
    return lines + [""]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "docs/results/story_checks.md"))
    args = ap.parse_args()
    root = data_root(args.data)
    lines = ["# Post hoc descriptive checks used in the paper", "",
             "Generated by `scripts/explore_story_checks.py` from saved records (read only). **None of these analyses "
             "was preregistered**, and none changes a frozen result; splits by post-treatment variables describe where an "
             "effect appears, not why.", "",
             "Data snapshot: " + "; ".join(f"`{v}`" for v in RUNS.values()) + ".", ""]
    for section in (section_choices, section_open_reports, section_reflections, section_linkcut,
                    section_joint, section_commitment, section_loop):
        lines += section(root)
        print(f"done: {section.__name__}", file=sys.stderr)
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
