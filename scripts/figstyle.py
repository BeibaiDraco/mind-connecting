"""Shared look for the paper figures: palette, fonts and drawing primitives for schematics.

A is blue, B (the partner) vermillion, Robin grey. "Claiming" is drawn in B's colour because it means
B's content showing up as A's own. Sizes follow a 5.5 in text width (NeurIPS/ICLR single column).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402,F401

A, B, ROBIN = "#0072B2", "#D55E00", "#8C8C8C"
A_LIGHT, B_LIGHT, GREY_LIGHT = "#DCEAF5", "#F9E0CF", "#EFEFEF"
CLAIM, NOW, ACC, CUT, INK = B, "#E69F00", "#009E73", "#A6A6A6", "#1A1A1A"
FULL_W, HALF_W = 5.5, 2.65

plt.rcParams.update({
    "font.family": "Arial", "font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5, "legend.fontsize": 6.2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
    "ytick.major.size": 2.5, "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.dpi": 300, "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic",
})


def canvas(width: float, height: float, xmax: float = 100.0):
    """A blank axes in drawing units: x runs 0..xmax across the width, y keeps the same scale."""
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, xmax * height / width)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text="", fc="white", ec=INK, lw=0.7, fs=6.5, color=INK, ha="center", va="center",
        pad=0.6, radius=1.2, weight="normal", family=None, ls="-", zorder=2, alpha=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}", fc=fc, ec=ec, lw=lw,
                                ls=ls, zorder=zorder, alpha=alpha))
    if text:
        tx = {"center": x + w / 2, "left": x + pad, "right": x + w - pad}[ha]
        ty = {"center": y + h / 2, "top": y + h - pad, "bottom": y + pad}[va]
        ax.text(tx, ty, text, ha=ha, va=va, fontsize=fs, color=color, weight=weight, family=family,
                zorder=zorder + 1, linespacing=1.25)


def arrow(ax, p0, p1, color=INK, lw=0.9, style="-|>", ms=6, ls="-", rad=0.0, zorder=3, shrink=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=zorder, shrinkA=shrink, shrinkB=shrink))


def tokens(ax, x, y, n, size, gap, fc, ec="white", lw=0.4, zorder=2):
    """A row of n token squares starting at (x, y); returns the x after the last one."""
    for i in range(n):
        ax.add_patch(Rectangle((x + i * (size + gap), y), size, size, fc=fc, ec=ec, lw=lw, zorder=zorder))
    return x + n * (size + gap)


def label(ax, x, y, text, fs=6.5, color=INK, ha="left", va="center", weight="normal", style="normal", **kw):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va=va, weight=weight, style=style, **kw)


def panel_letter(ax_or_fig, x, y, letter, fs=9):
    ax_or_fig.text(x, y, letter, fontsize=fs, weight="bold", ha="left", va="top")


def save(fig, out_dir, name):
    fig.savefig(out_dir / f"{name}.pdf")
    fig.savefig(out_dir / f"{name}.png", dpi=300)
    plt.close(fig)
