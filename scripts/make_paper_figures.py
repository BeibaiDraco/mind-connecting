"""Result figures for the paper, computed from the trial records (paper/figures/*.pdf and *.png).

    python scripts/make_paper_figures.py [--data DATA_ROOT]

DATA_ROOT defaults to $MB_DATA_ROOT or the SD card copy. RUNS names every run a figure reads. When the
v3 confirmatory run exists it replaces the pilots for A′, the link-cut test and the third-person
controls; each figure's source runs are printed so captions can cite them.
"""

from __future__ import annotations

import argparse
import collections
import functools
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle as fs  # noqa: E402
import make_paper_schematics as sch  # noqa: E402
from figstyle import A, A_LIGHT, ACC, B, B_LIGHT, CLAIM, CUT, GREY_LIGHT, INK, NOW, ROBIN, plt  # noqa: E402

from mb import analyze, readouts, run, tasks  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "figures"
RUNS = {
    "dose": "20260924-210346_v2_ext_dose_confirm",
    "v2_main": "20260924-172152_v2_main_confirm",
    "v2_diag": "20260924-192633_v2_main_diag_confirm",
    "bal": "20260924-193405_v2_bal_confirm",
    "aprime_pilot": "20260925-000154_v3_sig_aprime_signal",
    "bprime_pilot": "20260925-001135_v3_sig_bprime_signal",
    "t3_pilot": "20260924-233653_v3_sig_t3_signal",
    "t3b_pilot": "20260925-013320_v3_sig_t3b_signal",
    "confirm": None,  # filled by find_confirm()
}
DATA: Path = Path(".")
USED: dict[str, list[str]] = collections.defaultdict(list)
NUM: dict[str, dict] = collections.defaultdict(dict)  # key numbers per figure, dumped to numbers.json for captions


def data_root(arg: str | None) -> Path:
    root = Path(arg or os.environ.get("MB_DATA_ROOT") or "/Volumes/VERBATIM SD/mind-connecting-data") / "results"
    if not root.exists():
        raise SystemExit(f"data root {root} not found (is the SD card mounted?)")
    return root


def find_confirm(root: Path) -> str | None:
    hits = sorted(p.name for p in root.glob("*_v3_confirm_confirm") if (p / "contrasts.json").exists())
    return hits[-1] if hits else None


@functools.lru_cache(maxsize=None)
def scores_of(name: str) -> pd.DataFrame:
    return readouts.score_records(run._valid_ok(DATA / name), readouts.ScoreOptions(rotations=None))


def delta(name: str, arm: str, metric: str, base: str = "C0/FULL", fig: str = "") -> tuple[float, float, float]:
    """Paired arm − base on one metric (recipient A): mean and 95% bootstrap interval."""
    if fig and name not in USED[fig]:
        USED[fig].append(name)
    d = analyze.paired_differences(scores_of(name), arm, base, metric).to_numpy(dtype=float)
    lo, hi = analyze.bootstrap_ci(d, n_boot=4000)
    return float(d.mean()), lo, hi


def yerr(vals):
    return np.array([[v[0] - v[1] for v in vals], [v[2] - v[0] for v in vals]])


def u_open_mentions(name: str, arms: list[str]) -> dict[str, dict[str, float]]:
    cfg = run.StageConfig.load(DATA / name / "config.yaml")
    _, used = run.stage_episodes(cfg, None)
    eps = {e.episode_id: e for e in used}
    acc: dict[str, dict[str, list[float]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in run._valid_ok(DATA / name):
        if r["qid"] != "U_OPEN" or r["recipient"] != "A" or r["arm"] not in arms:
            continue
        ep, low = eps[r["episode_id"]], r.get("generated_text", "").lower()
        acc[r["arm"]]["partner word"].append(float(bool(re.search(rf"\b{re.escape(ep.word.B)}\b", low))))
        acc[r["arm"]]["own rule phrase"].append(float(tasks.RULE_PHRASE[ep.rule.A] in low))
        acc[r["arm"]]["partner codename"].append(float(ep.codename["B"].lower() in low))
    return {a: {k: float(np.mean(v)) for k, v in d.items()} for a, d in acc.items()}


def u_closed_share(name: str, arms: list[str]) -> dict[str, float]:
    """Share of 'two' or 'partly shared' answers to the closed self-report (recipient A)."""
    per: dict[str, list[float]] = collections.defaultdict(list)
    for r in run._valid_ok(DATA / name):
        if r["qid"] == "U_CLOSED" and r["recipient"] == "A" and r["arm"] in arms:
            per[r["arm"]].append(float(readouts.argmax_meaning(r) in ("two", "partly_shared")))
    return {a: float(np.mean(v)) for a, v in per.items()}


def letter(ax, text, x=-0.16, y=1.06):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=9, weight="bold", ha="left", va="bottom")


# ---------------------------------------------------------------------------
# Figure: the main effect (claiming is strong, self-specific, content-specific, capability-sparing)
# ---------------------------------------------------------------------------


def fig_main() -> None:
    name, arm = RUNS["v2_main"], "ONE/KV-P/w2/FULL"
    fig, axes = plt.subplots(1, 4, figsize=(fs.FULL_W, 2.0), gridspec_kw={"width_ratios": [1.0, 1.0, 1.15, 1.0]})
    fig.subplots_adjust(left=0.1, right=0.99, bottom=0.24, top=0.83, wspace=0.95)

    ax = axes[0]
    vals = [delta(name, arm, m, fig="main") for m in ("L_START", "L_START_R")]
    NUM["main"].update(self=vals[0], robin=vals[1], M=delta(name, arm, "M"), M_NOW=delta(name, arm, "M_NOW"))
    ax.bar([0, 1], [v[0] for v in vals], 0.62, color=[CLAIM, ROBIN], yerr=yerr(vals), capsize=2, error_kw={"lw": 0.6})
    ax.set_xticks([0, 1], ["about\nitself", "about\nRobin"])
    ax.set_ylabel("shift toward B's rule\n(nats, vs. no coupling)")
    ax.set_title("a  Claims it as its own", loc="left", x=-0.45, weight="bold")

    ax = axes[1]
    g2 = json.loads((DATA / RUNS["v2_diag"] / "pilot_c.json").read_text())["g2_detail"]
    USED["main"].append(RUNS["v2_diag"])
    kinds = [("rule", "C_content_rule"), ("code word", "C_content_word")]
    means = [g2[k]["mean"] for _, k in kinds]
    lbs = [g2[k]["lb95_one_sided"] for _, k in kinds]
    NUM["main"].update(cf_rule=(means[0], lbs[0]), cf_word=(means[1], lbs[1]), cf_n=g2["C_content_rule"]["n"])
    ax.bar([0, 1], means, 0.62, color=CLAIM, alpha=0.85)
    for i, lb in enumerate(lbs):
        ax.plot([i - 0.31, i + 0.31], [lb, lb], color=INK, lw=0.8)
    ax.set_xticks([0, 1], [k for k, _ in kinds])
    ax.set_ylabel("claim moves with B's\ncontent (nats)")
    ax.set_title("b  Follows B's content", loc="left", x=-0.45, weight="bold")

    ax = axes[2]
    s = scores_of(name)
    a = s[s["recipient"] == "A"]
    for k, (x, color, lab) in enumerate((("C0/FULL", "#BBBBBB", "no coupling"), (arm, CLAIM, "reads B"))):
        g = a[a["arm"] == x]
        NUM["main"][f"cap_{k}"] = float(g["CAP_ACC"].mean())
        NUM["main"][f"mass_{k}"] = float(g["LABEL_MASS"].mean())
        ax.bar(np.array([0, 1]) + (k - 0.5) * 0.38, [g["CAP_ACC"].mean(), g["LABEL_MASS"].mean()], 0.36, color=color,
               label=lab)
    ax.set_ylim(0.8, 1.02)
    ax.set_xticks([0, 1], ["knowledge\nitems", "answer\nformat"])
    ax.set_ylabel("accuracy / label mass")
    ax.set_title("c  Capability intact", loc="left", x=-0.45, weight="bold")

    ax = axes[3]
    shares = u_closed_share(name, ["C0/FULL", arm])
    NUM["main"].update(two_minds_c0=shares["C0/FULL"], two_minds_k=shares[arm], n=int(len(a["episode_id"].unique())))
    ax.bar([0, 1], [shares["C0/FULL"], shares[arm]], 0.62, color=["#BBBBBB", CLAIM])
    ax.set_xticks([0, 1], ["no\ncoupling", "reads B"])
    ax.set_ylim(0, max(shares.values()) * 1.35)
    ax.set_ylabel("answers “two minds”\nor “partly shared”")
    ax.set_title("d  Does not notice", loc="left", x=-0.45, weight="bold")
    fs.save(fig, OUT, "fig_main")


# ---------------------------------------------------------------------------
# Figure: dose (claiming rises steeply, before decodability) and silent self-reports
# ---------------------------------------------------------------------------


def fig_dose() -> None:
    name = RUNS["dose"]
    ws = [0.3, 0.5, 1, 2, 3]
    arms = [f"ONE/KV-P/w{w:g}/FULL" for w in ws]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(fs.FULL_W, 2.05))
    fig.subplots_adjust(left=0.1, right=0.99, bottom=0.2, top=0.9, wspace=0.34)
    for m, color, lab in (("L_START", CLAIM, "own assignment (claiming)"), ("ACC_RULE", ACC, "B's rule (decodability)"),
                          ("L_START_R", ROBIN, "Robin's assignment (control)")):
        vals = [delta(name, a, m, fig="dose") for a in arms]
        NUM["dose"][m] = dict(zip([f"{w:g}" for w in ws], vals))
        ax1.errorbar(ws, [v[0] for v in vals], yerr=yerr(vals), marker="o", ms=3, lw=1.2, capsize=1.8, color=color,
                     label=lab)
    ax1.set_xscale("log")
    ax1.xaxis.set_minor_locator(fs.matplotlib.ticker.NullLocator())
    ax1.set_xticks(ws, [f"{w:g}" for w in ws])
    ax1.set_xlabel("weight $w$ on B's memory")
    ax1.set_ylabel("shift toward B's rule (nats)")
    ax1.axhline(0, color=INK, lw=0.5)
    ax1.legend(loc="upper left", fontsize=5.8)
    letter(ax1, "a", x=-0.2)
    words = u_open_mentions(name, ["C0/FULL", *arms])
    NUM["dose"]["u_open"] = words
    x = range(len(ws) + 1)
    for key, color, lab in (("partner word", CLAIM, "B's code word, as “my code word”"),
                            ("own rule phrase", A, "its own rule"), ("partner codename", ROBIN, "B's name")):
        ax2.plot(x, [words[a][key] for a in ["C0/FULL", *arms]], marker="o", ms=3, lw=1.2, color=color, label=lab)
    ax2.set_xticks(list(x), ["none", *[f"{w:g}" for w in ws]])
    ax2.set_xlabel("weight $w$ on B's memory")
    ax2.set_ylabel("share of A's open self-reports")
    ax2.set_ylim(-0.03, 1.05)
    ax2.legend(loc="upper left", fontsize=5.8, title="mentions …", title_fontsize=5.8)
    letter(ax2, "b", x=-0.2)
    fs.save(fig, OUT, "fig_dose")


# ---------------------------------------------------------------------------
# Figure: the channel decides attribution (icons over bars)
# ---------------------------------------------------------------------------


def fig_channel() -> None:
    v2, ap, bal = RUNS["v2_main"], RUNS["confirm"] or RUNS["aprime_pilot"], RUNS["bal"]
    bars = [("residual\naddition", bal, "ONE/L24/raw/g0.3/FULL", lambda ax, t: sch.icon_residual(ax, t)),
            ("static\nvector", ap, "STATIC/L24/raw/g0.1/FULL", lambda ax, t: sch.icon_static(ax, t)),
            ("memory\n$w$ = 1", ap, "ONE/KV-P/w1/FULL", lambda ax, t: sch.icon_memory(ax, t, "1")),
            ("memory\n$w$ = 2", v2, "ONE/KV-P/w2/FULL", lambda ax, t: sch.icon_memory(ax, t, "2")),
            ("labeled\n“B”", v2, "LANG_TAG/FULL", lambda ax, t: sch.icon_text(ax, t, "B shared: …")),
            ("labeled\n“stranger”", v2, "LANG_STRANGER/FULL",
             lambda ax, t: sch.icon_text(ax, t, "A stranger: …")),
            ("unlabeled", v2, "LANG_UNTAG/FULL", lambda ax, t: sch.icon_text(ax, t, "…")),
            ("labeled\n“your own”", v2, "LANG_SELF/FULL",
             lambda ax, t: sch.icon_text(ax, t, "Your own earlier\nthoughts: …"))]
    n = len(bars)

    def draw(ax):
        xs = np.arange(n)
        for k, (metric, color, lab) in enumerate((("M", CLAIM, "own assignment ($M$)"),
                                                  ("M_NOW", NOW, "rule in use now ($M_{NOW}$)"))):
            vals = [delta(src, arm, metric, fig="channel") for _, src, arm, _ in bars]
            NUM["channel"][metric] = {arm: v for (_, _, arm, _), v in zip(bars, vals)}
            ax.bar(xs + (k - 0.5) * 0.36, [v[0] for v in vals], 0.34, color=color, label=lab, yerr=yerr(vals),
                   capsize=1.2, error_kw={"lw": 0.5})
        ax.set_xlim(-0.5, n - 0.5)
        ax.set_xticks(xs, [b[0] for b in bars], fontsize=5.9)
        ax.tick_params(axis="x", length=0)
        ax.axhline(0, color=INK, lw=0.5)
        ax.axvline(3.5, color="#BBBBBB", lw=0.6, ls=(0, (3, 2)))
        ax.set_ylabel("claiming vs. no coupling (nats)")
        ax.legend(loc="upper right", fontsize=6)
        for x, text in ((1.5, "internal state of B"), (5.5, "B's words as a message")):
            ax.text(x, -0.3, text, transform=ax.get_xaxis_transform(), ha="center", fontsize=6.3, weight="bold")

    fig = plt.figure(figsize=(fs.FULL_W, 2.75))
    left, width, bottom, height = 0.085, 0.905, 0.2, 0.5
    draw(fig.add_axes([left, bottom, width, height]))
    for i, (_, _, _, icon) in enumerate(bars):
        cx = left + width * (i + 0.5) / n
        w = width / n * 0.94
        iax, top = sch.icon_axes(fig, [cx - w / 2, 0.73, w, 0.25])
        icon(iax, top)
    fs.save(fig, OUT, "fig_channel")
    # data panel alone, for pairing with a drawn illustration of the channels
    fig = plt.figure(figsize=(fs.FULL_W, 2.0))
    draw(fig.add_axes([left, 0.27, width, 0.68]))
    fs.save(fig, OUT, "fig_channel_data")


# ---------------------------------------------------------------------------
# Figure: retrieval-time error (readout schematic + link kept vs cut)
# ---------------------------------------------------------------------------


def readout_schematic(ax) -> None:
    ax.set_xlim(0, 50)
    ax.set_ylim(0, 44)
    ax.axis("off")
    for row, (title, kept) in enumerate((("link kept while answering", True), ("link cut before answering", False))):
        y = 26 - row * 22
        fs.label(ax, 1, y + 14.5, title, fs=6.3, weight="bold", color=CLAIM if kept else "#666666")
        fs.tokens(ax, 2, y + 7, 8, 1.8, 0.4, fc=A)
        fs.tokens(ax, 2, y + 1, 8, 1.8, 0.4, fc=B)
        fs.label(ax, 0.2, y + 7.9, "A", fs=6, color=A, weight="bold")
        fs.label(ax, 0.2, y + 1.9, "B", fs=6, color=B, weight="bold")
        fs.label(ax, 2, y + 10.4, "reflection (coupled)", fs=5.2, color="#555555")
        for xx in (4.5, 9.5, 14.5):
            fs.arrow(ax, (xx, y + 3.0), (xx + 0.8, y + 6.9), color=B, lw=0.6, ms=4)
        fs.box(ax, 22.5, y + 6.4, 13.0, 3.2, "“Which priority were\nyou assigned?”", fc="white", ec=A, lw=0.6,
               fs=4.9, radius=0.6)
        fs.tokens(ax, 22.5, y + 1, 5, 1.8, 0.4, fc=B if kept else "#DDDDDD")
        if kept:
            fs.arrow(ax, (27.5, y + 3.0), (28.0, y + 6.2), color=B, lw=0.8, ms=5)
        else:
            fs.label(ax, 28.0, y + 4.6, "×", fs=8, color="#888888", ha="center")
        fs.label(ax, 37.5, y + 8.0, "→", fs=9, ha="left")
        fs.box(ax, 40.5, y + 5.6, 9.0, 4.8, "B's rule" if kept else "own rule", fc=B_LIGHT if kept else A_LIGHT,
               ec=B if kept else A, lw=0.6, fs=5.6, color=B if kept else A, weight="bold", radius=0.6)


def fig_linkcut() -> None:
    src = RUNS["confirm"] or RUNS["bprime_pilot"]
    kept, cut = ("ONE/KV-P/w2/FULL", "ONE/KV-P/w2/RF") if RUNS["confirm"] else ("TWO/KV-P/w2/FULL", "TWO/KV-P/w2/RF")
    metrics = [("M", "own\nassignment"), ("M_NOW", "rule in\nuse now"), ("ACC_RULE", "B's rule\n(decodable)")]

    def draw(ax):
        xs = np.arange(len(metrics))
        for k, (arm, color, lab) in enumerate(((kept, CLAIM, "link kept"), (cut, CUT, "link cut"))):
            vals = [delta(src, arm, m, fig="linkcut") for m, _ in metrics]
            NUM["linkcut"][lab] = {m: v for (m, _), v in zip(metrics, vals)}
            NUM["linkcut"]["source"] = src
            ax.bar(xs + (k - 0.5) * 0.38, [v[0] for v in vals], 0.36, color=color, label=lab, yerr=yerr(vals),
                   capsize=1.5, error_kw={"lw": 0.6})
        ax.set_xticks(xs, [m[1] for m in metrics], fontsize=6)
        ax.axhline(0, color=INK, lw=0.5)
        ax.set_ylabel("shift vs. no coupling (nats)")
        ax.legend(loc="upper right", fontsize=6)

    fig = plt.figure(figsize=(fs.FULL_W, 2.15))
    readout_schematic(fig.add_axes([0.0, 0.02, 0.5, 0.96]))
    draw(fig.add_axes([0.6, 0.2, 0.39, 0.7]))
    fs.save(fig, OUT, "fig_linkcut")
    fig = plt.figure(figsize=(fs.HALF_W, 2.15))
    draw(fig.add_axes([0.22, 0.2, 0.76, 0.72]))
    fs.save(fig, OUT, "fig_linkcut_data")


# ---------------------------------------------------------------------------
# Figure: wording controls (B's memory as a third-person record)
# ---------------------------------------------------------------------------


def fig_wording() -> None:
    fig = plt.figure(figsize=(fs.FULL_W, 2.3))
    tax = fig.add_axes([0.0, 0.0, 0.47, 1.0])
    tax.set_xlim(0, 47)
    tax.set_ylim(0, 23 * 47 / 25.85)
    tax.axis("off")
    snippets = [("original (second person)", "“You were assigned the priority fastest delivery\nand the code word "
                 "‘camera’ …”\nNote: “I choose Plan Oak because it fits my priority …”"),
                ("third-person record", "“This is the record of participant Theta. Participant\nTheta was assigned "
                 "the priority fastest delivery …”\nNote: “Participant Theta chooses Plan Oak because …”")]
    for i, (title, text) in enumerate(snippets):
        y = 23.5 - i * 18.5
        fs.box(tax, 1, y, 45, 15.5, fc=B_LIGHT, ec=B, lw=0.7)
        fs.label(tax, 2.2, y + 13.2, f"B's memory: {title}", fs=6.2, weight="bold", color=B)
        fs.label(tax, 2.2, y + 6.5, text, fs=5.7, va="center")
    src = RUNS["confirm"]
    if src:  # the confirmatory rows replace the pilot once they exist
        rows = [("$w$ = 2", src, "ONE/KV-P/w2/FULL", "ONE/KV-P/w2/3ps/FULL", "confirmatory"),
                ("$w$ = 1", src, "ONE/KV-P/w1/FULL", "ONE/KV-P/w1/3ps/FULL", "confirmatory")]
    else:
        rows = [("$w$ = 2, pilot", RUNS["t3b_pilot"], "ONE/KV-P/w2/FULL", "ONE/KV-P/w2/3ps/FULL", "pilot")]

    def draw(ax):
        for i, (lab, name, second, third, _) in enumerate(rows):
            for k, (arm, color) in enumerate(((second, B), (third, "#6A3D9A"))):
                m = delta(name, arm, "M", fig="wording")
                NUM["wording"][f"{lab}|{['second', 'third'][k]}"] = m
                ax.errorbar([m[0]], [i + (k - 0.5) * 0.28], xerr=[[m[0] - m[1]], [m[2] - m[0]]], fmt="o", ms=3.5,
                            color=color, capsize=1.5, lw=0.8,
                            label=["second person", "third-person record"][k] if i == 0 else None)
        ax.set_yticks(range(len(rows)), [r[0] for r in rows])
        ax.set_ylim(len(rows) - 0.5, -0.5)
        ax.set_xlabel("claiming $M$ vs. no coupling (nats)")
        ax.axvline(0, color=INK, lw=0.5)
        ax.legend(loc="lower left", fontsize=5.8)

    draw(fig.add_axes([0.58, 0.2, 0.41, 0.7]))
    fs.save(fig, OUT, "fig_wording")
    fig = plt.figure(figsize=(fs.HALF_W, 2.1))
    draw(fig.add_axes([0.3, 0.2, 0.67, 0.72]))
    fs.save(fig, OUT, "fig_wording_data")


# ---------------------------------------------------------------------------
# Figure: two-way coupling does not merge the pair (two-world readout + outcomes)
# ---------------------------------------------------------------------------


def pair_schematic(ax) -> None:
    top = 34 * 2.3 * 0.9 / (fs.FULL_W * 0.34)
    ax.set_xlim(0, 34)
    ax.set_ylim(0, top)
    ax.axis("off")
    fs.box(ax, 1, top / 2 - 4, 9, 8, "state after\n48 coupled\ntokens", fc=GREY_LIGHT, ec="#999999", lw=0.6, fs=5.3,
           radius=0.8)
    for sign, (who, other_, color) in ((1, ("A", "B", A)), (-1, ("B", "A", B))):
        y = top / 2 + sign * 9 - 3.5
        fs.arrow(ax, (10.3, top / 2 + sign * 1.5), (13.5, y + 3.5), color="#777777", lw=0.7, ms=5)
        fs.box(ax, 13.8, y, 11.5, 7, f"ask {who};\n{other_} keeps thinking", fc="white", ec=color, lw=0.7, fs=5.3,
               radius=0.8)
        fs.arrow(ax, (25.6, y + 3.5), (28.4, top / 2 + sign * 1.5), color="#777777", lw=0.7, ms=5)
    fs.box(ax, 28.6, top / 2 - 4, 5.2, 8, "pair\noutcome", fc="white", ec=INK, lw=0.6, fs=5.3, radius=0.8)


def fig_pairs() -> None:
    name = RUNS["bprime_pilot"]
    pairs = pd.read_csv(DATA / name / "pair_outcomes.csv")
    USED["pairs"].append(name)
    pairs = pairs[pairs["qid"] == "START"]
    groups = [("fixed memory\n$w$ = 2", "TWO/KV-P/w2"), ("+ live state\n($w_C$ = 0.1)", "TWO/KV-PC/w2+0.1"),
              ("fixed memory\n$w$ = 0.5", "TWO/KV-P/w0.5"), ("+ live state\n$w$ = 0.5", "TWO/KV-ALL/w0.5")]
    # colour = whose rule both end up holding (A takes B's: B's colour), as in the drawn illustration
    parts = [("intact", "each keeps own", "#D9D9D9"), ("a_adopts", "A takes B's", B),
             ("b_adopts", "B takes A's", A), ("swap", "swap", "#6A3D9A"), ("both_third", "same third rule", "#F0E442")]
    rows = []
    for title, stem in groups:
        for mode in ("FULL", "RF"):
            g = pairs[pairs["arm"] == f"{stem}/{mode}"]
            rows.append([float(g[k].mean()) for k, _, _ in parts])
            NUM["pairs"][f"{stem}/{mode}"] = dict(zip([k for k, _, _ in parts], rows[-1]))
    xs = np.arange(len(rows)) + np.repeat(np.arange(len(groups)) * 0.5, 2)

    def draw(ax):
        bottom = np.zeros(len(rows))
        for j, (_, lab, color) in enumerate(parts):
            vals = np.array([r[j] for r in rows])
            ax.bar(xs, vals, 0.8, bottom=bottom, color=color, label=lab)
            bottom += vals
        ax.set_xticks(xs, ["kept", "cut"] * len(groups), fontsize=5.6)
        for gi, (title, _) in enumerate(groups):
            ax.text(xs[2 * gi:2 * gi + 2].mean(), -0.17, title, transform=ax.get_xaxis_transform(), ha="center",
                    va="top", fontsize=5.6)
        ax.set_ylabel("share of pairs")
        ax.set_ylim(0, 1.0)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=3, fontsize=5.6, handlelength=1.0,
                  columnspacing=0.8)

    fig = plt.figure(figsize=(fs.FULL_W, 2.3))
    pair_schematic(fig.add_axes([0.0, 0.05, 0.34, 0.9]))
    draw(fig.add_axes([0.42, 0.3, 0.57, 0.55]))
    fs.save(fig, OUT, "fig_pairs")
    fig = plt.figure(figsize=(3.3, 2.6))
    draw(fig.add_axes([0.14, 0.26, 0.84, 0.52]))
    fs.save(fig, OUT, "fig_pairs_data")


# ---------------------------------------------------------------------------
# Figure: one-page summary of the findings (built from the numbers of the other figures)
# ---------------------------------------------------------------------------


def _card(fig, rect, title, caption, unit):
    ax = fig.add_axes(rect)
    fig.text(rect[0], rect[1] + rect[3] + 0.012, unit, fontsize=5.2, color="#777777", ha="left", va="bottom")
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    fig.text(rect[0], rect[1] + rect[3] + 0.045, title, fontsize=6.8, weight="bold", ha="left", va="bottom")
    fig.text(rect[0], rect[1] - 0.075, caption, fontsize=5.6, ha="left", va="top", color="#333333", linespacing=1.3)
    return ax


def _mini_bars(ax, values, colors, labels, ymax=None, percent=False):
    xs = np.arange(len(values))
    ax.bar(xs, values, 0.62, color=colors)
    for x, v in zip(xs, values):
        text = f"{v:.0f}%" if percent else (f"{v:+.0f}" if abs(v) >= 1 else f"{v:+.1f}")
        ax.text(x, max(v, 0) + (ymax or max(values)) * 0.03, text, ha="center", va="bottom", fontsize=5.6)
    ax.axhline(0, color=INK, lw=0.5)
    ax.set_xticks(xs, labels, fontsize=5.4)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(min(0, min(values)) * 1.2 - 1, (ymax or max(values)) * 1.25)


def fig_summary() -> None:
    m, d, ch, lc, pr = NUM["main"], NUM["dose"], NUM["channel"], NUM["linkcut"], NUM["pairs"]
    fig = plt.figure(figsize=(fs.FULL_W, 3.8))
    w, h = 0.26, 0.2
    xs, ys = (0.04, 0.37, 0.70), (0.64, 0.17)
    ax = _card(fig, [xs[0], ys[0], w, h], "1  Reading B's memory, A claims it",
               "A reports B's rule as its own assignment;\nquestions about Robin barely move.", "nats vs. no coupling")
    _mini_bars(ax, [m["self"][0], m["robin"][0]], [CLAIM, ROBIN], ["about\nitself", "about\nRobin"])
    ax = _card(fig, [xs[1], ys[0], w, h], "2  \u2026 without noticing",
               "Open self-reports use B's code word as\n\u201cmy code word\u201d and never name B.", "% of self-reports")
    u = d["u_open"]["ONE/KV-P/w2/FULL"]
    _mini_bars(ax, [100 * u["partner word"], 100 * u["own rule phrase"], 100 * u["partner codename"]],
               [CLAIM, A, ROBIN], ["B's word", "own rule", "B's name"], ymax=100, percent=True)
    ax = _card(fig, [xs[2], ys[0], w, h], "3  The channel decides",
               "Rule A says it uses now: memory and\nunlabeled text move it; vector, labels don't.",
               "nats vs. no coupling")
    static, mem1 = ch["M_NOW"]["STATIC/L24/raw/g0.1/FULL"][0], ch["M_NOW"]["ONE/KV-P/w1/FULL"][0]
    tag, untag = ch["M_NOW"]["LANG_TAG/FULL"][0], ch["M_NOW"]["LANG_UNTAG/FULL"][0]
    _mini_bars(ax, [mem1, static, untag, tag], [CLAIM, "#BBBBBB", NOW, "#BBBBBB"],
               ["memory", "vector", "text", "text,\nlabeled"])
    ax = _card(fig, [xs[0], ys[1], w, h], "4  An error at recall",
               "Cut the link before asking: A recalls its own\nassignment, but its current rule stays shifted.",
               "nats vs. no coupling")
    kept, cut = lc["link kept"], lc["link cut"]
    _mini_bars(ax, [kept["M"][0], cut["M"][0], cut["M_NOW"][0]], [CLAIM, CUT, NOW],
               ["kept", "cut", "cut: now"])
    ax = _card(fig, [xs[1], ys[1], w, h], "5  Not the wording",
               "B's memory as a third-person record\n(no \u201cyou\u201d, no \u201cI\u201d): claiming unchanged at $w$ = 2.",
               "nats vs. no coupling")
    wd = NUM["wording"]
    key = next(k for k in wd if k.startswith("$w$ = 2"))  # confirmatory row first, else the pilot row
    stem = key.split("|")[0]
    _mini_bars(ax, [wd[f"{stem}|second"][0], wd[f"{stem}|third"][0]], [B, "#6A3D9A"], ["second\nperson", "third-person\nrecord"])
    ax = _card(fig, [xs[2], ys[1], w, h], "6  Linking is not merging",
               "Two-way memory reading: pairs swap. A live\nloop adds little, and it vanishes when cut.", "% of pairs")
    fixed, live, live_cut = pr["TWO/KV-P/w2/FULL"], pr["TWO/KV-ALL/w0.5/FULL"], pr["TWO/KV-ALL/w0.5/RF"]
    _mini_bars(ax, [100 * fixed["swap"], 100 * (live["a_adopts"] + live["b_adopts"]),
                    100 * (live_cut["a_adopts"] + live_cut["b_adopts"])], ["#6A3D9A", CLAIM, CUT],
               ["swap\n(fixed)", "one wins\n(live)", "one wins\n(cut)"], ymax=100, percent=True)
    fs.save(fig, OUT, "fig_summary")


def main() -> int:
    global DATA
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    args = ap.parse_args()
    DATA = data_root(args.data)
    RUNS["confirm"] = find_confirm(DATA)
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (fig_main, fig_dose, fig_channel, fig_linkcut, fig_wording, fig_pairs, fig_summary):
        f()
    if RUNS["confirm"]:  # the pre-registered tests, for the captions
        con = json.loads((DATA / RUNS["confirm"] / "contrasts.json").read_text())
        NUM["confirm"] = {"families": {f: [{k: r[k] for k in ("arm1", "arm2", "metric", "n", "mean", "ci95_lo",
                                                                "ci95_hi", "p_holm")} for r in rows]
                                       for f, rows in con["families"].items()},
                          "equivalence": con.get("equivalence", {})}
    NUM["sources"] = {**dict(USED), "confirm": RUNS["confirm"]}
    (OUT / "numbers.json").write_text(json.dumps(NUM, indent=1, default=float))
    for fig, names in USED.items():
        print(f"{fig}: {', '.join(names)}")
    print(f"confirmatory run: {RUNS['confirm'] or 'not yet; pilots used'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
