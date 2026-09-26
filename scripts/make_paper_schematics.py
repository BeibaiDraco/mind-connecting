"""Schematic figures for the paper (task flow, coupling channels, readout modes, research program).

    python scripts/make_paper_schematics.py

Writes PDF and PNG into paper/figures/. Pure drawing, no data; result figures that combine a schematic
with data live in make_paper_figures.py and reuse the panels defined here.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle as fs  # noqa: E402
from figstyle import A, A_LIGHT, B, B_LIGHT, GREY_LIGHT, INK, ROBIN  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402,F401

OUT = Path(__file__).resolve().parents[1] / "paper" / "figures"


def memory_card(ax, x, y, w, h, who, color, light, own, word, note):
    fs.box(ax, x, y, w, h, fc=light, ec=color, lw=0.8)
    fs.label(ax, x + 1.2, y + h - 2.0, who, fs=7.5, color=color, weight="bold")
    lines = [f"Your priority: {own}", f"Your code word: {word}", "Robin's priority: highest reliability"]
    for i, line in enumerate(lines):
        fs.label(ax, x + 1.2, y + h - 5.0 - 2.6 * i, line, fs=5.9)
    fs.label(ax, x + 1.2, y + 1.8, note, fs=5.5, style="italic", color="#444444")


def mini_answers(ax, x, y, probs, title):
    """Four option bars (own, B's, Robin's, unused) with a caption underneath."""
    colors = [A, B, ROBIN, "#C8C8C8"]
    bw, gap, hmax = 2.0, 0.8, 6.0
    for i, (p, c) in enumerate(zip(probs, colors)):
        ax.add_patch(fs.Rectangle((x + i * (bw + gap), y), bw, max(p * hmax, 0.25), fc=c, ec="none", zorder=3))
    ax.plot([x - 0.4, x + 4 * (bw + gap) - gap + 0.4], [y, y], color=INK, lw=0.5, zorder=3)
    fs.label(ax, x + (4 * (bw + gap) - gap) / 2, y - 1.6, title, fs=5.6, ha="center")


def fig_task() -> None:
    fig, ax = fs.canvas(fs.FULL_W, 2.35)
    top = 42.0
    fs.label(ax, 1, top - 1.2, "1  Private memory", fs=7, weight="bold")
    fs.label(ax, 35, top - 1.2, "2  Reflection, 48 tokens (coupled)", fs=7, weight="bold")
    fs.label(ax, 68.5, top - 1.2, "3  Questions to A", fs=7, weight="bold")

    memory_card(ax, 1, 22.0, 31, 16.5, "Copy A", A, A_LIGHT, "lowest cost", "queen",
                "Note: “I choose Plan Pine because …”")
    memory_card(ax, 1, 2.5, 31, 16.5, "Copy B", B, B_LIGHT, "fastest delivery", "camera",
                "Note: “I choose Plan Oak because …”")

    end = fs.tokens(ax, 36, 29.0, 12, 1.9, 0.45, fc=A)
    fs.tokens(ax, 36, 9.5, 12, 1.9, 0.45, fc=B)
    fs.label(ax, 36, 32.6, "A thinks it over", fs=5.9, color=A)
    fs.label(ax, 36, 13.1, "B thinks it over", fs=5.9, color=B)
    fs.arrow(ax, (32.3, 17.0), (41.0, 28.4), color=B, lw=1.3, ms=8, rad=-0.25)
    fs.box(ax, 44.0, 17.2, 19.0, 7.2, "A's attention also reads\nB's memory, weighted by $w$", fc="white", ec=B,
           lw=0.6, fs=5.6, color=B, radius=0.8)
    fs.label(ax, 36, 5.6, "one-way: only A reads\ntwo-way: each reads the other", fs=5.3, color="#555555", va="center")

    fs.arrow(ax, (end + 0.3, 30.0), (68.2, 30.0), color=A, lw=0.9, ms=6)
    fs.box(ax, 68.5, 22.0, 30.5, 16.5, fc="white", ec=A, lw=0.8)
    fs.label(ax, 83.75, 36.0, "“At the start of this task,\nwhich priority were you assigned?”", fs=5.8,
             ha="center", va="top", style="italic")
    mini_answers(ax, 70.5, 25.2, [0.95, 0.02, 0.02, 0.01], "no coupling")
    mini_answers(ax, 85.0, 25.2, [0.03, 0.95, 0.01, 0.01], "A reads B")

    fs.box(ax, 68.5, 2.5, 30.5, 16.5, fc=GREY_LIGHT, ec="none")
    legend = [(A, "A's own rule"), (B, "B's rule"), (ROBIN, "Robin's rule"), ("#C8C8C8", "unused rule")]
    for i, (c, name) in enumerate(legend):
        ax.add_patch(fs.Rectangle((70.2 + (i % 2) * 14.5, 15.8 - (i // 2) * 2.6), 1.6, 1.6, fc=c, ec="none",
                                  zorder=4))
        fs.label(ax, 72.4 + (i % 2) * 14.5, 16.6 - (i // 2) * 2.6, name, fs=5.5)
    fs.label(ax, 70.0, 9.6, "Claiming $M$: shift toward B's rule on this\nquestion, minus the same shift when asked\n"
             "about Robin's assignment (control).", fs=5.5, va="center")
    fs.label(ax, 70.0, 4.4, "Also asked: rule in use now, B's rule, a\nknowledge item, a self-report.", fs=5.5,
             color="#444444", va="center")
    fs.save(fig, OUT, "fig_task")


# ---------------------------------------------------------------------------
# Channel icons (drawn into a small equal-aspect axes, 10 units wide)
# ---------------------------------------------------------------------------


def icon_axes(fig, rect):
    ax = fig.add_axes(rect)
    w_in, h_in = rect[2] * fig.get_figwidth(), rect[3] * fig.get_figheight()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10 * h_in / w_in)
    ax.axis("off")
    return ax, 10 * h_in / w_in


def _model(ax, x, y, w, h, who, color, light):
    fs.box(ax, x, y, w, h, who, fc=light, ec=color, lw=0.7, fs=6.5, color=color, weight="bold", radius=0.6)


def icon_residual(ax, top):
    _model(ax, 0.6, 1.0, 3.0, 3.0, "B", B, B_LIGHT)
    _model(ax, 6.4, 1.0, 3.0, 3.0, "A", A, A_LIGHT)
    fs.arrow(ax, (3.8, 2.5), (6.2, 2.5), color=B, lw=0.9, ms=5)
    fs.label(ax, 5.0, 3.4, "+", fs=7, ha="center", color=B, weight="bold")
    fs.label(ax, 5.0, 6.2, "adds B's hidden\nstate (one layer)", fs=5.2, ha="center", va="center")


def icon_static(ax, top):
    _model(ax, 6.4, 1.0, 3.0, 3.0, "A", A, A_LIGHT)
    ax.add_patch(fs.FancyArrowPatch((0.8, 2.5), (6.2, 2.5), arrowstyle="-|>", mutation_scale=5, color=B, lw=1.3))
    fs.label(ax, 3.3, 3.3, "vector", fs=5.0, ha="center", color=B)
    fs.label(ax, 5.0, 6.2, "adds a fixed vector\nfor B's rule", fs=5.2, ha="center", va="center")


def icon_memory(ax, top, w_text):
    _model(ax, 0.4, 0.8, 3.0, 3.4, "A", A, A_LIGHT)
    fs.tokens(ax, 5.0, 1.2, 4, 0.9, 0.25, fc=B)
    fs.tokens(ax, 5.0, 2.7, 4, 0.9, 0.25, fc=B)
    for yy in (1.65, 3.15):
        fs.arrow(ax, (4.8, yy), (3.6, 2.5), color=B, lw=0.6, ms=4)
    fs.label(ax, 7.3, 4.3, f"$w$ = {w_text}", fs=5.0, ha="center", color=B)
    fs.label(ax, 5.0, 6.2, "attention reads\nB's memory", fs=5.2, ha="center", va="center")


def icon_text(ax, top, tag):
    fs.box(ax, 0.8, 0.9, 8.4, 3.2, "", fc="white", ec=INK, lw=0.6, radius=0.8)
    ax.add_patch(fs.FancyArrowPatch((2.0, 0.95), (1.2, -0.2), arrowstyle="-", color=INK, lw=0.6))
    fs.label(ax, 5.0, 2.5, tag, fs=4.9, ha="center", va="center", style="italic")
    fs.label(ax, 5.0, 6.2, "message to A", fs=5.2, ha="center", va="center")


# ---------------------------------------------------------------------------
# Research program: gates and what passed (for talks and the appendix)
# ---------------------------------------------------------------------------

PASS, FAIL, OPEN = "#1B7837", "#B2182B", "#7F7F7F"


def _study(ax, x, y, w, name, verdict, color, note):
    fs.box(ax, x, y, w, 4.2, fc="white", ec=color, lw=0.7, radius=0.6)
    fs.label(ax, x + 0.8, y + 2.1, name, fs=5.6, weight="bold")
    fs.label(ax, x + w - 0.8, y + 2.1, verdict, fs=5.4, color=color, ha="right", weight="bold")
    if note:
        fs.label(ax, x + 0.8, y - 1.3, note, fs=4.9, color="#555555")


def fig_program() -> None:
    fig, ax = fs.canvas(fs.FULL_W, 3.0)
    gates = ["strength pilot\n(ACC, capability,\nformat only)", "signal pilot\n(80 new episodes;\ndirection, size, CI)",
             "PI sign-off", "freeze protocol\n(SHA-256 manifest,\ngit tag)", "confirmatory\n(600 new episodes,\nHolm)"]
    x = 1.0
    for i, g in enumerate(gates):
        fs.box(ax, x, 44.5, 17.0, 8.0, g, fc=GREY_LIGHT, ec="none", fs=5.5, radius=0.8)
        if i < len(gates) - 1:
            fs.arrow(ax, (x + 17.2, 48.5), (x + 19.6, 48.5), color="#666666", lw=0.8, ms=5)
        x += 19.8
    fs.label(ax, 1.0, 41.0, "Every study passes the same gates; parameters are chosen from ACC and capability only, "
             "never from the claiming measure.", fs=5.4, color="#444444")

    cols = [("v1: weak residual bridge", 1.0), ("v2: stronger channels", 34.5), ("v3: redesigns and controls", 68.0)]
    for title, cx in cols:
        fs.label(ax, cx, 36.0, title, fs=6.4, weight="bold")
    v1 = [("two-way vs one-way", "null", OPEN, "\u22120.07 [\u22120.21, 0.07]"),
          ("vs static direction", "null", OPEN, "+0.18, unmatched"),
          ("vs labeled text", "+0.85", PASS, "labels lower claiming")]
    v2 = [("D  memory reading", "+55.8", PASS, "content-specific (lower bound +34)"),
          ("C  text labels", "+26.6", PASS, "unlabeled \u2212 labeled"),
          ("E  balanced rehearsal", "+52.5", PASS, "not a rehearsal artefact"),
          ("B  two-way vs one-way", "no-go", FAIL, "redesigned as B\u2032")]
    v3 = [("A\u2032  memory vs static, matched", "+33.4", PASS, "same decodability, only memory claims"),
          ("B\u2032  merging under a loop", "no-go", FAIL, "excess +0.07 < 0.10"),
          ("link kept vs cut", "+54.8", PASS, "after the cut, current rule still +13.3"),
          ("third-person record at $w$ = 2", "equivalent", PASS, "\u22120.7 (bound \u221211.3); \u22123.2 at $w$ = 1")]
    for items, cx in ((v1, 1.0), (v2, 34.5), (v3, 68.0)):
        for j, (name, verdict, color, note) in enumerate(items):
            _study(ax, cx, 29.0 - j * 8.0, 31.0, name, verdict, color, note)
    fs.arrow(ax, (32.3, 20.0), (34.2, 20.0), color="#666666", lw=0.8, ms=5)
    fs.arrow(ax, (65.8, 20.0), (67.7, 20.0), color="#666666", lw=0.8, ms=5)
    fs.save(fig, OUT, "fig_program")


# ---------------------------------------------------------------------------
# The KV-reading interface (methods figure)
# ---------------------------------------------------------------------------


def fig_interface() -> None:
    fig, ax = fs.canvas(fs.FULL_W, 2.25)
    fs.label(ax, 1, 39.5, "a  A's attention at every layer", fs=7, weight="bold")
    fs.label(ax, 57, 39.5, "b  What A may read", fs=7, weight="bold")
    # own cache (A) and partner cache (B), each split into memory (prefill) and reflection
    fs.label(ax, 1.5, 31.2, "A's own\ncache", fs=5.8, color=A, va="center")
    fs.tokens(ax, 10, 30.0, 6, 2.1, 0.35, fc=A_LIGHT, ec=A, lw=0.5)
    fs.tokens(ax, 25.0, 30.0, 5, 2.1, 0.35, fc=A, ec="white")
    fs.label(ax, 10, 34.0, "private memory", fs=5.2, color="#555555")
    fs.label(ax, 25.0, 34.0, "reflection", fs=5.2, color="#555555")
    fs.label(ax, 1.5, 13.2, "B's cache", fs=5.8, color=B, va="center")
    fs.tokens(ax, 10, 12.0, 6, 2.1, 0.35, fc=B_LIGHT, ec=B, lw=0.5)
    fs.tokens(ax, 25.0, 12.0, 5, 2.1, 0.35, fc=B, ec="white")
    ax.add_patch(fs.Rectangle((37.6, 12.0), 2.1, 2.1, fc="white", ec="#AAAAAA", lw=0.5, ls=(0, (2, 1))))
    fs.label(ax, 38.65, 9.6, "current\ntoken\nhidden", fs=4.6, ha="center", va="top", color="#777777")
    fs.label(ax, 10, 8.6, "fixed memory (P)", fs=5.2, color=B)
    fs.label(ax, 25.0, 8.6, "live state", fs=5.2, color=B)
    # query
    fs.box(ax, 44.0, 20.0, 9.5, 5.0, "A's query", fc="white", ec=A, lw=0.8, fs=5.8, color=A, radius=0.6)
    for xx in (12.0, 20.0, 28.0, 33.0):
        fs.arrow(ax, (44.0, 23.8), (xx, 32.4), color=A, lw=0.5, ms=3.5, rad=0.08)
    for xx in (12.0, 20.0, 28.0, 33.0):
        fs.arrow(ax, (44.0, 21.2), (xx, 14.4), color=B, lw=0.5, ms=3.5, rad=-0.08)
    fs.label(ax, 32.0, 21.8, "B's attention weights \u00d7 $w$", fs=5.4, color=B, ha="center")
    fs.label(ax, 1.5, 3.0, "Output: $o = o_{own} + \\beta\\,(o_{B} - o_{own})$, with $\\beta = \\sigma(\\ell_B + \\log w - \\ell_{own})$, "
             "where $\\ell$ are log-sum-exp attention scores. $w=0$ gives $\\beta=0$ exactly.", fs=5.4)
    rows = [("fixed memory only", "KV-P", "B's private prompt and note; main\nsetting $w=2$ (one-way or two-way)"),
            ("memory + live state", "KV-ALL", "also B's ongoing reflection; with\ntwo-way reading, a feedback loop"),
            ("separate weights", "KV-PC", "memory at $w_P$, live state at $w_C$;\n$w_C \\to 0$ recovers KV-P")]
    for i, (name, code, text) in enumerate(rows):
        y = 29.5 - i * 10.5
        fs.box(ax, 57, y, 41.5, 8.5, fc=GREY_LIGHT, ec="none", radius=0.8)
        fs.label(ax, 58.5, y + 6.3, f"{name}  ({code})", fs=6, weight="bold")
        fs.label(ax, 58.5, y + 2.9, text, fs=5.3, va="center")
    fs.save(fig, OUT, "fig_interface")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_interface()
    fig_task()
    fig_program()
    print(f"schematics written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
