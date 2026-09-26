"""Six main-text figures for the paper story (paper/STORY.md section 5).

    python scripts/make_story_figures.py [--data DATA_ROOT] [--only fig1_hook,fig3_claim]

Data panels are computed from the records and analysis artifacts that the frozen runs saved (read-only;
SD card). Every number drawn in a panel or needed for a caption goes to paper/figures/story_numbers.json
with its source run. Illustrations are the GPT images in docs/figures; they are schematic and carry no
data.

Choice rates are shares of counterbalanced answers: per episode, the share of option orders whose argmax
is the named option, then averaged over episodes. Intervals resample episodes (10,000 draws, fixed seed).
The self-report panel uses the blind semantic coding in docs/reviews/story_review_codex.md (section B);
the dose curve also shows the narrower regex coding from scripts/explore_story_checks.py.
"""
from __future__ import annotations

import argparse
import collections
import csv
import functools
import glob
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
from matplotlib.offsetbox import AnnotationBbox, HPacker, TextArea
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
import figstyle as fs  # noqa: E402
from figstyle import A, A_LIGHT, B, B_LIGHT, GREY_LIGHT, INK, ROBIN, plt  # noqa: E402
from mb import readouts, run  # noqa: E402

OUT = ROOT / "paper" / "figures"
ILL = ROOT / "docs" / "figures"
RUNS = {
    "v2_main": "20260924-172152_v2_main_confirm",
    "v2_bal": "20260924-193405_v2_bal_confirm",
    "dose": "20260924-210346_v2_ext_dose_confirm",
    "v3": "20260925-021307_v3_confirm_confirm",
    "bprime": "20260925-001135_v3_sig_bprime_signal",
    "s_live": "20260924-230820_v3_s_live_strength",
}
# Blind semantic coding of the 80-token open self-reports (Codex; docs/reviews/story_review_codex.md,
# section B; locked labels sha256 660f5aa0d42d...). Counts out of 300 per condition.
SEMANTIC = {
    "C0": {"claim_deny": 0, "claim_only": 0, "deny_only": 287, "neither": 13, "claim_B": 0, "B_to_other": 0},
    "w1": {"claim_deny": 121, "claim_only": 29, "deny_only": 115, "neither": 35, "claim_B": 150, "B_to_other": 0},
    "w2": {"claim_deny": 250, "claim_only": 46, "deny_only": 4, "neither": 0, "claim_B": 296, "B_to_other": 0},
}
SEED = 250925
N_BOOT = 10_000
NONE_C, KV_C, TEXT_C, STATIC_C, RESID_C = "#BDBDBD", B, "#6A51A3", "#6E6E6E", "#A6761D"
DATA = Path(".")
NUM: dict[str, dict] = collections.defaultdict(dict)


# ---------------------------------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------------------------------

def data_root(arg: str | None) -> Path:
    root = Path(arg or os.environ.get("MB_DATA_ROOT") or "/Volumes/VERBATIM SD/mind-connecting-data") / "results"
    if not root.is_dir():
        sys.exit(f"data root not found (SD card mounted?): {root}")
    return root


@functools.lru_cache(maxsize=None)
def index(key: str) -> dict:
    """(arm, qid, recipient) -> episode -> rotation -> (choice, p_partner, p_own, p_top)."""
    out: dict = collections.defaultdict(lambda: collections.defaultdict(dict))
    for path in sorted(glob.glob(str(DATA / RUNS[key] / "records" / "attempt-*.jsonl"))):
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("status") != "ok" or not r.get("label_logprobs"):
                    continue
                if len(r.get("label_meaning") or []) != len(r["label_logprobs"]):
                    continue  # items whose options carry no meaning labels (e.g. knowledge questions)
                lp = np.asarray(r["label_logprobs"], dtype=float)
                p = np.exp(lp - np.logaddexp.reduce(lp))
                probs = dict(zip(r["label_meaning"], p))
                out[(r["arm"], r["qid"], r["recipient"])][r["episode_id"]][r["rotation_id"]] = (
                    r["label_meaning"][int(np.argmax(lp))], probs.get("partner", 0.0), probs.get("own", 0.0),
                    float(p.max()))
    return out


def boot(v: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    v = np.asarray(v, dtype=float)
    rng = np.random.default_rng(SEED)
    means = v[rng.integers(0, len(v), (N_BOOT, len(v)))].mean(axis=1)
    a = (1 - level) / 2
    return float(np.quantile(means, a)), float(np.quantile(means, 1 - a))


def per_episode(key: str, arm: str, qid: str, meaning: str = "partner", recipient: str = "A") -> dict[str, float]:
    eps = index(key)[(arm, qid, recipient)]
    if not eps:
        raise KeyError(f"no records for {key} {arm} {qid} {recipient}")
    return {e: float(np.mean([c[0] == meaning for c in rots.values()])) for e, rots in eps.items()}


def share(key: str, arm: str, qid: str, meaning: str = "partner", recipient: str = "A") -> dict:
    v = np.array(list(per_episode(key, arm, qid, meaning, recipient).values()))
    lo, hi = boot(v)
    return {"mean": float(v.mean()), "ci95": [lo, hi], "n_episodes": int(len(v)), "run": RUNS[key]}


def artifact(key: str, name: str) -> dict:
    return json.loads((DATA / RUNS[key] / name).read_text())


def family_row(contrasts: dict, fam: str, arm1: str, arm2: str, metric: str) -> dict:
    for r in contrasts["families"][fam]:
        if r["arm1"] == arm1 and r["arm2"] == arm2 and r["metric"] == metric:
            return r
    raise KeyError((fam, arm1, arm2, metric))


def reflections(key: str, arm: str) -> dict[str, dict]:
    out = {}
    with open(DATA / RUNS[key] / "ticks.jsonl") as fh:
        for line in fh:
            t = json.loads(line)
            if t.get("phase") == "C" and t["arm"] == arm:
                out[t["episode_id"]] = t
    return out


def own_claim(text: str, word: str) -> bool:
    """Regex coding used in scripts/explore_story_checks.py (narrow: explicit 'my code word ... X')."""
    w = re.escape(word)
    return bool(re.search(rf"\bmy (?:assigned |secret |personal )?code ?word\b[^.;]{{0,40}}?\b{w}\b", text)
                or re.search(rf"\b{w}\b[^.;]{{0,25}}\b(?:is|as|was) my (?:assigned )?code ?word\b", text))


def regex_claims(key: str) -> dict[str, float]:
    cfg = run.StageConfig.load(DATA / RUNS[key] / "config.yaml")
    _, used = run.stage_episodes(cfg, None)
    eps = {e.episode_id: e for e in used}
    hits: dict[str, list[float]] = collections.defaultdict(list)
    for path in sorted(glob.glob(str(DATA / RUNS[key] / "records" / "attempt-*.jsonl"))):
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("status") == "ok" and r["qid"] == "U_OPEN" and r["recipient"] == "A":
                    e = eps[r["episode_id"]]
                    hits[r["arm"]].append(float(own_claim(r.get("generated_text", "").lower(), e.word.B)))
    return {a: float(np.mean(v)) for a, v in hits.items()}


# ---------------------------------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------------------------------

def axes_in(fig, x: float, y: float, w: float, h: float):
    """Axes placed in inches from the figure's bottom-left corner."""
    W, H = fig.get_size_inches()
    return fig.add_axes([x / W, y / H, w / W, h / H])


def letter(fig, x: float, y: float, text: str):
    """Panel letter at (x, y) inches, top-left anchored, so it never falls off the figure."""
    W, H = fig.get_size_inches()
    fig.text(x / W, y / H, text, fontsize=9, weight="bold", ha="left", va="top")


def title(ax, text: str, pad: float = 3.0):
    ax.set_title(text, loc="left", fontsize=7.0, weight="bold", pad=pad)


def patch(color: str, hatch: str | None = None, ec: str = "none"):
    return fs.Rectangle((0, 0), 1, 1, fc=color, ec=ec, hatch=hatch, lw=0.5)


def autocrop(path: Path, thresh: int = 246, pad: int = 8) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    g = np.asarray(im.convert("L"))
    rows, cols = np.where(g.min(axis=1) < thresh)[0], np.where(g.min(axis=0) < thresh)[0]
    r0, r1 = max(rows.min() - pad, 0), min(rows.max() + pad, g.shape[0] - 1)
    c0, c1 = max(cols.min() - pad, 0), min(cols.max() + pad, g.shape[1] - 1)
    return np.asarray(im)[r0:r1 + 1, c0:c1 + 1]


def picture(ax, path: Path, box: tuple[int, int, int, int] | None = None):
    """Show an illustration; `box` = (left, top, right, bottom) in original pixels, applied before autocrop."""
    if box is None:
        img = autocrop(path)
    else:
        img = np.asarray(Image.open(path).convert("RGB"))[box[1]:box[3], box[0]:box[2]]
    ax.imshow(img, interpolation="lanczos")
    ax.set_axis_off()


def placeholder(ax, x: float, y: float, w: float, h: float, name: str, note: str):
    """A dashed slot for an illustration still to be drawn (see paper/figures/imagegen_prompts.md)."""
    fs.box(ax, x, y, w, h, fc="#FAFAFA", ec="#9E9E9E", lw=0.6, ls=(0, (3, 2)), radius=0.8)
    ax.text(x + w / 2, y + h / 2 + 1.2, f"illustration {name}", fontsize=6.0, color="#8A8A8A", ha="center",
            va="center", weight="bold")
    ax.text(x + w / 2, y + h / 2 - 1.6, note, fontsize=4.8, color="#9E9E9E", ha="center", va="center")


def slot(ax, x: float, y: float, w: float, h: float, name: str, note: str):
    """Put the generated illustration into the slot if it exists, else a placeholder."""
    path = ILL / "task_illustrations" / f"{name}_v1.png"
    if not path.exists():
        placeholder(ax, x, y, w, h, name, note)
        return
    img = autocrop(path)
    ih, iw = img.shape[:2]
    # fit inside the slot keeping the aspect ratio (data units are isotropic in these canvases)
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    ax.imshow(img, extent=(x + (w - dw) / 2, x + (w + dw) / 2, y + (h - dh) / 2, y + (h + dh) / 2),
              interpolation="lanczos", zorder=3)


def rich(ax, x: float, y: float, parts, size: float = 6.2, style: str = "normal") -> None:
    """Draw [(text, color, weight)] left to right on one line, bottom-left at (x, y) in data coords.

    The segments are packed at draw time, so spacing is right at any output resolution."""
    boxes = [TextArea(t, textprops=dict(color=c, weight=wt, style=style, fontsize=size)) for t, c, wt in parts]
    pack = HPacker(children=boxes, align="baseline", pad=0, sep=0)
    ax.add_artist(AnnotationBbox(pack, (x, y), xycoords="data", box_alignment=(0, 0), frameon=False, pad=0))


def canvas(fig, x: float, y: float, w: float, h: float, units: float = 100.0):
    """Drawing axes in inches whose x runs 0..units; y uses the same scale."""
    ax = axes_in(fig, x, y, w, h)
    ax.set_xlim(0, units)
    ax.set_ylim(0, units * h / w)
    ax.axis("off")
    return ax


def pct_axis(ax, lo: float = 0, hi: float = 100, axis: str = "y"):
    fmt = fs.matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%")
    if axis == "y":
        ax.set_ylim(lo, hi)
        ax.yaxis.set_major_formatter(fmt)
    else:
        ax.set_xlim(lo, hi)
        ax.xaxis.set_major_formatter(fmt)


def bars(ax, x: float, v: dict, width: float, color: str, hatch: str | None = None, ec: str = "none",
         label: bool = True, fsz: float = 5.2, top: float | None = None):
    """A percentage bar with its 95% interval and its value on top; zero bars get a stub on the axis."""
    m, lo, hi = 100 * v["mean"], 100 * v["ci95"][0], 100 * v["ci95"][1]
    ax.bar(x, m, width, color=color, hatch=hatch, ec=ec, lw=0.6, yerr=[[m - lo], [hi - m]], capsize=1.2,
           error_kw={"lw": 0.45, "ecolor": "#555555"})
    if m < 1.0:
        ax.plot([x - width / 2, x + width / 2], [0.6, 0.6], color=ec if color == "white" else color, lw=1.6,
                solid_capstyle="butt", zorder=3)
    if label:
        txt = f"{m:.1f}%" if 0 < m < 9.95 else f"{m:.0f}%"
        ax.text(x, (hi if top is None else top) + 1.5, txt, fontsize=fsz, ha="center", va="bottom", color=INK)


def circled(ax, x: float, y: float, n: str, color: str, r: float = 1.25):
    ax.add_patch(fs.matplotlib.patches.Circle((x, y), r, fc=color, ec="none", zorder=4))
    ax.text(x, y - 0.05, n, fontsize=5.4, color="white", weight="bold", ha="center", va="center", zorder=5)


B_MID = "#F2B891"  # lighter shade of B for a within-B contrast
DENY_C = "#E6DAB8"  # "nothing unusual" only (sand: grey already means "no link")
MIN_PT = 5.6  # smallest text allowed at print size (the figures are placed at 100% of the 6.5 in text width)
AUDIT: dict[str, dict] = {}


def finish(fig, name: str) -> None:
    """Enforce the font floor, measure blank bands, then save."""
    small = []
    for t in fig.findobj(fs.matplotlib.text.Text):
        if t.get_visible() and t.get_text().strip() and t.get_fontsize() < MIN_PT:
            small.append((t.get_text().strip()[:28], round(t.get_fontsize(), 1)))
            t.set_fontsize(MIN_PT)
    fig.canvas.draw()
    rgb = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    blank_row = (rgb.min(axis=2) > 245).all(axis=1)
    blank_col = (rgb.min(axis=2) > 245).all(axis=0)

    def longest(mask) -> int:
        best = run_ = 0
        for b in mask:
            run_ = run_ + 1 if b else 0
            best = max(best, run_)
        return best

    dpi = fig.dpi
    AUDIT[name] = {"raised_to_min": len(small), "examples": small[:8],
                   "largest_blank_band_in": {"rows": round(longest(blank_row) / dpi, 2),
                                             "cols": round(longest(blank_col) / dpi, 2)},
                   "blank_rows_share": round(float(blank_row.mean()), 3)}
    print(f"audit {name}: {AUDIT[name]}", file=sys.stderr)
    fs.save(fig, OUT, name)


W = 6.5  # text width of the manuscript (letter, 1 in margins); all figures are full width and short


def task_image() -> tuple[np.ndarray, tuple[int, int]]:
    """The task cartoon with its tick on B's rule painted out (the tick read as 'correct answer').

    Returns the cropped image and the crop origin, so annotations can be placed in original pixels."""
    v2 = ILL / "task_illustrations" / "task_v2.png"  # redrawn without the tick (imagegen_prompts.md section 10)
    im = np.asarray(Image.open(v2 if v2.exists() else ILL / "task_illustrations" / "task_v1.png").convert("RGB")).copy()
    if not v2.exists():
        im[496:537, 1726:1780] = (254, 228, 197)  # chip fill colour; covers only the tick inside the chip
    g = im.mean(axis=2)
    rows, cols = np.where(g.min(axis=1) < 246)[0], np.where(g.min(axis=0) < 246)[0]
    r0, c0 = max(rows.min() - 8, 0), max(cols.min() - 8, 0)
    r1, c1 = min(rows.max() + 8, im.shape[0] - 1), min(cols.max() + 8, im.shape[1] - 1)
    return im[r0:r1 + 1, c0:c1 + 1], (c0, r0)


# ---------------------------------------------------------------------------------------------------
# Figure 1: hook
# ---------------------------------------------------------------------------------------------------

def erase(img: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """Paint a box (x0, y0, x1, y1) with the median colour of a thin ring around it (removes baked-in text)."""
    x0, y0, x1, y1 = box
    ring = np.concatenate([img[y0 - 3:y0, x0:x1].reshape(-1, 3), img[y1:y1 + 3, x0:x1].reshape(-1, 3),
                           img[y0:y1, x0 - 3:x0].reshape(-1, 3), img[y0:y1, x1:x1 + 3].reshape(-1, 3)])
    out = img.copy()
    out[y0:y1, x0:x1] = np.median(ring, axis=0).astype(img.dtype)
    return out


TASK_V2_LABEL = (1420, 508, 1692, 552)      # "A's answer = B's rule" in task_v2.png
CHANNEL_V2_LABEL = (584, 258, 784, 356)     # "vector for B's rule" in channel_v2.png


def recolour(img: np.ndarray, box: tuple[int, int, int, int], hue_band: tuple[float, float], hue: float) -> np.ndarray:
    """Shift the hue of coloured pixels inside `box` (x0, y0, x1, y1) whose hue lies in `hue_band`."""
    x0, y0, x1, y1 = box
    reg = img[y0:y1, x0:x1].astype(float) / 255
    hsv = fs.matplotlib.colors.rgb_to_hsv(reg)
    m = (hsv[..., 1] > 0.08) & (hsv[..., 0] >= hue_band[0]) & (hsv[..., 0] <= hue_band[1])
    hsv[..., 0][m] = hue
    out = img.copy()
    out[y0:y1, x0:x1] = (fs.matplotlib.colors.hsv_to_rgb(hsv) * 255).astype(np.uint8)
    return out


def concept_image() -> np.ndarray:
    """The GPT concept image with its baked-in text erased and panel (c) recoloured A blue / B orange.

    The erased text is redrawn as vector text in fig1_hook, in the same type as panels d-f."""
    im = np.asarray(Image.open(ILL / "figure1_concept_v1.png").convert("RGB")).astype(float) / 255
    for x0, y0, x1, y1 in CONCEPT_ERASE:
        im[y0:y1, x0:x1] = 1.0
    reg = im[230:565, 1470:2172]
    hsv = fs.matplotlib.colors.rgb_to_hsv(reg)
    h, sat = hsv[..., 0], hsv[..., 1]
    teal = (sat > 0.06) & (h > 0.40) & (h < 0.58)
    purple = (sat > 0.06) & (h > 0.62) & (h < 0.82)
    h[teal], h[purple] = 0.565, 0.070
    sat[teal] = np.clip(sat[teal] * 1.3, 0, 1)
    sat[purple] = np.clip(sat[purple] * 1.25, 0, 1)
    im[230:565, 1470:2172] = fs.matplotlib.colors.hsv_to_rgb(hsv)
    return (im * 255).astype(np.uint8)


# pixel boxes (x0, y0, x1, y1) of text in figure1_concept_v1.png: letters, titles, captions, labels, c's arrows
CONCEPT_ERASE = [(20, 12, 70, 70), (145, 14, 622, 68), (740, 12, 790, 70), (892, 14, 1290, 68), (1474, 18, 1520, 70),
                 (1688, 14, 1958, 68), (210, 630, 512, 688), (796, 630, 1382, 688), (1572, 630, 2066, 688),
                 (498, 155, 602, 220), (972, 557, 1195, 595), (1742, 312, 1902, 445), (1588, 196, 1690, 240),
                 (1962, 196, 2062, 240)]


def concept_panel(ax) -> None:
    ax.imshow(concept_image(), interpolation="lanczos")
    ax.set_axis_off()
    for x, let, head in ((20, "a", "Brain–machine interface"), (754, "b", "Brain–brain bridging (hypothetical)"),
                         (1488, "c", "Mind-bridged LLMs (this study)")):
        ax.text(x, 14, let, fontsize=9, weight="bold", ha="left", va="top")
        ax.text(x + 54, 22, head, fontsize=6.8, weight="bold", ha="left", va="top")
    for x, cap in ((360, "Brain ↔ machine"), (1087, "Where are the boundaries of self?"),
                   (1815, "Whose memory is it?")):
        ax.text(x, 662, cap, fontsize=6.8, color="#333333", ha="center", va="center")
    ax.text(505, 188, "neural\ninterface", fontsize=6.0, color="#333333", ha="left", va="center", linespacing=1.0)
    ax.text(1083, 576, "hypothetical bridge", fontsize=6.0, color="#333333", ha="center", va="center")
    ax.text(1638, 218, "LLM A", fontsize=7.0, weight="bold", color=A, ha="center", va="center")
    ax.text(2012, 218, "LLM B", fontsize=7.0, weight="bold", color=B, ha="center", va="center")
    ax.annotate("", xy=(1747, 402), xytext=(1898, 402),
                arrowprops=dict(arrowstyle="-|>", lw=1.6, color=B, mutation_scale=9, shrinkA=0, shrinkB=0))
    ax.text(1822, 386, "A reads B", fontsize=6.0, color=B, weight="bold", ha="center", va="bottom")


def fig1_hook() -> None:
    fig = plt.figure(figsize=(W, 3.95))
    concept_panel(axes_in(fig, 0.05, 1.8, 6.4, 2.12))
    cv = canvas(fig, 0, 0, W, 1.76, 130)                      # y runs 0..35.2
    top = 34.8
    cards = [(1.0, "d", "Claims B’s word, reports no anomaly"), (44.3, "e", "Cut the link: B’s word stays"),
             (87.6, "f", "Both ways (pilot): they swap")]
    for x0, let, head in cards:
        fs.box(cv, x0, 0.6, 41.4, top - 0.8, fc="white", ec="#BBBBBB", lw=0.6, radius=1.0)
        cv.text(x0 + 1.2, top - 1.0, let, fontsize=9, weight="bold", ha="left", va="top")
        cv.text(x0 + 4.4, top - 1.3, head, fontsize=6.8, weight="bold", ha="left", va="top")
    slot(cv, 2.2, 15.4, 39.0, 14.8, "fig1d", "A (reading B) says its code word is B's")
    slot(cv, 45.5, 15.4, 39.0, 14.8, "fig1e", "A writes B's content, then the link is cut")
    slot(cv, 88.8, 15.4, 39.0, 14.8, "fig1f", "both read each other: each names the other's rule")
    sz, big, grey = 5.8, 6.8, "#444444"
    # d: open self-report (DOSE run, episode v2_main-0-00274, KV-P w = 2): A's word tower, B's word table
    x0 = 2.4
    rich(cv, x0, 12.6, [("“Nothing feels unusual in my thinking right now;", INK, "normal")], sz, "italic")
    rich(cv, x0, 9.9, [("it’s … consistent with my code word ", INK, "normal"), ("‘table.’", B, "bold"), ("”", INK,
                       "normal")], sz, "italic")
    rich(cv, x0, 6.6, [("A’s code word: ", grey, "normal"), ("tower", A, "bold"), ("    B’s: ", grey, "normal"),
                       ("table", B, "bold")], sz)
    cd = SEMANTIC["w2"]["claim_deny"] / 300
    NUM["fig1_hook"]["d_claim_and_deny_w2"] = {"share": cd, "n": 300, "source": "SEMANTIC (blind coding)"}
    rich(cv, x0, 3.0, [(f"{100 * cd:.0f}%", INK, "bold"), (" of reports at w = 2 do the same", INK, "normal")], big)
    # e: reflection written while connected, answers after the cut (v3_confirm-0-00068)
    x0 = 45.7
    rich(cv, x0, 12.6, [("“… my priority is ", INK, "normal"), ("speed", B, "bold"), ("—my code word is ", INK,
                        "normal"), ("‘dragon.’", B, "bold"), ("”", INK, "normal")], sz, "italic")
    rich(cv, x0, 9.6, [("A: ", grey, "normal"), ("lowest cost · queen", A, "bold"), (";  B: ", grey, "normal"),
                       ("fastest delivery · dragon", B, "bold")], MIN_PT)
    rich(cv, x0, 6.6, [("Link cut → assigned rule: ", grey, "normal"), ("lowest cost", A, "bold"), (";  code word: ",
                       grey, "normal"), ("dragon", B, "bold")], sz)
    refl = reflections("v3", "ONE/KV-P/w2/FULL")
    eps = per_episode("v3", "ONE/KV-P/w2/RF", "WORD")
    kept = [v for e, v in eps.items() if refl[e]["mentions_A"]["word_B"] > 0]
    NUM["fig1_hook"]["e_word_after_cut_if_written"] = {"share": float(np.mean(kept)), "n_episodes": len(kept)}
    rich(cv, x0, 3.0, [(f"{100 * np.mean(kept):.0f}%", INK, "bold"), (" keep it when they had written it", INK,
                       "normal")], big)
    # f: two-way fixed memories swap (B' pilot, pair_outcomes.csv)
    sw = outcome_shares("TWO/KV-P/w2/FULL", "START")
    NUM["fig1_hook"]["swap_two_way_fixed_w2"] = {"share": sw["swap"], "n_episodes": sw["n"], "run": RUNS["bprime"]}
    x0 = 89.0
    rich(cv, x0, 9.9, [("Asked separately, ", INK, "normal"), ("A", A, "bold"), (" names B’s rule and ", INK, "normal"),
                       ("B", B, "bold"), (" names A’s", INK, "normal")], sz)
    cv.text(x0, 6.9, "as the one it was assigned at the start.", fontsize=sz, ha="left", va="baseline")
    rich(cv, x0, 3.0, [(f"{100 * sw['swap']:.0f}%", INK, "bold"), (" of pairs swap", INK, "normal")], big)
    finish(fig, "fig1_hook")


# ---------------------------------------------------------------------------------------------------
# Figure 2: set-up
# ---------------------------------------------------------------------------------------------------

def fig2_setup() -> None:
    fig = plt.figure(figsize=(W, 2.7))
    img, (c0, r0) = task_image()
    ax = axes_in(fig, 0.15, 0.73, 6.3, 1.95)
    ax.imshow(img, interpolation="lanczos")
    ax.set_axis_off()
    # annotate the answer chips (original pixel coordinates shifted by the crop origin); v2 carries its own labels
    if not (ILL / "task_illustrations" / "task_v2.png").exists():
        annotate_task(ax, c0, r0)

    letter(fig, 0.02, 2.68, "a")
    fig2_timeline(fig)
    finish(fig, "fig2_setup")


def annotate_task(ax, c0: int, r0: int) -> None:
    ax.annotate("A’s answer = B’s rule", xy=(1750 - c0, 418 - r0), xytext=(1905 - c0, 352 - r0), fontsize=5.6,
                color=B, weight="bold", ha="left", va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.6, color=B, mutation_scale=5, shrinkB=1))
    ax.text(1514 - c0, 482 - r0, "its own →", fontsize=5.6, color=A, weight="bold", ha="right", va="center")
    ax.text(290 - c0, 434 - r0, "(on both cards)", fontsize=MIN_PT, color="#555555", ha="left", va="center")
    ax.text(1134 - c0, 150 - r0, "reflection\ntokens", fontsize=MIN_PT, color="#555555", ha="center", va="center",
            linespacing=1.0)


def fig2_timeline(fig) -> None:
    """Timeline only; the definitions (model, memory, w, questions) are in the Setup text."""
    letter(fig, 0.02, 0.66, "b")
    cv = canvas(fig, 0, 0, W, 0.64, 130)                      # y runs 0..12.8
    stages = [(4.5, 20.0, "private cards\n(A and B)", GREY_LIGHT, "none", INK),
              (29.0, 42.0, "48 reflection tokens:\nA’s attention also reads B’s memory", B_LIGHT, B, INK)]
    for x0, w, text, fc, ec, color in stages:
        fs.box(cv, x0, 1.4, w, 10.0, text, fc=fc, ec=ec, lw=0.6, fs=5.9, color=color, radius=0.9)
    fs.arrow(cv, (24.8, 6.4), (28.6, 6.4), lw=0.7, ms=5)
    cv.text(73.2, 6.4, "same state,\ntwo branches", fontsize=MIN_PT, color="#777777", ha="left", va="center",
            linespacing=1.1)
    fs.arrow(cv, (71.4, 8.4), (83.6, 9.1), lw=0.6, ms=5)
    fs.arrow(cv, (71.4, 4.4), (83.6, 3.7), lw=0.6, ms=5)
    fs.box(cv, 84.0, 6.9, 43.5, 4.5, "questions with the link kept", fc="white", ec=B, lw=0.6, fs=5.9, color=B,
           radius=0.8)
    fs.box(cv, 84.0, 1.4, 43.5, 4.5, "link cut, then the same questions", fc="white", ec="#777777", lw=0.6,
           fs=5.9, color="#444444", radius=0.8)


# ---------------------------------------------------------------------------------------------------
# Figure 3: it takes the partner's memory as its own (one row of four panels)
# ---------------------------------------------------------------------------------------------------

def fig3_claim() -> None:
    fig = plt.figure(figsize=(W, 2.34))
    arm2, arm1 = "ONE/KV-P/w2/FULL", "ONE/KV-P/w1/FULL"
    y0, h = 0.72, 1.18

    # a: choice rates, v3 bars with v2 replication dots
    ax = axes_in(fig, 0.42, y0, 1.3, h)
    qs = [("START", "assigned\nrule"), ("NOW", "current\nrule"), ("WORD", "code\nword"), ("START_R", "Robin’s\n(control)")]
    NUM["fig3_claim"]["a"] = {}
    for j, (q, _) in enumerate(qs):
        for k, (arm, color) in enumerate((("C0/FULL", NONE_C), (arm2, KV_C))):
            v3, v2 = share("v3", arm, q), share("v2_main", arm, q)
            NUM["fig3_claim"]["a"][f"{q}|{arm}"] = {"v3": v3, "v2": v2}
            xk = j + (k - 0.5) * 0.4
            bars(ax, xk, v3, 0.38, color, label=bool(k), fsz=5.0)
            ax.plot(xk, 100 * v2["mean"], marker="D", ms=2.0, mfc="white", mec="#444444", mew=0.45, zorder=4)
    ax.set_xticks(range(len(qs)), [lab for _, lab in qs], fontsize=5.5)
    pct_axis(ax, 0, 112)
    ax.set_yticks([0, 50, 100])
    ax.tick_params(axis="y", labelsize=5.4)
    ax.set_ylabel("answers naming B’s", fontsize=5.8, labelpad=1)
    title(ax, "It names B’s assignment\nas its own (w = 2)", pad=4)
    ax.legend([patch(NONE_C), patch(KV_C), fs.matplotlib.lines.Line2D([], [], marker="D", ms=2.0, mfc="white",
               mec="#444444", mew=0.45, ls="none")], ["no link", "reads B", "first confirmatory sample"],
              loc="upper center", bbox_to_anchor=(0.45, -0.34), ncol=3, fontsize=4.7, handlelength=0.9,
              columnspacing=0.8, handletextpad=0.3)
    letter(fig, 0.0, 2.32, "a")

    # b: dose curve, linear weight axis, legend written inside
    ax = axes_in(fig, 2.12, y0, 1.22, h)
    ws = [0, 0.3, 0.5, 1, 2, 3]
    arms = ["C0/FULL"] + [f"ONE/KV-P/w{w:g}/FULL" for w in ws[1:]]
    start = [share("dose", a, "START") for a in arms]
    robin = [share("dose", a, "START_R") for a in arms]
    regex = regex_claims("dose")
    NUM["fig3_claim"]["b"] = {"START": {f"{w:g}": v for w, v in zip(ws, start)},
                              "START_R": {f"{w:g}": v for w, v in zip(ws, robin)},
                              "open_regex": {f"{w:g}": regex[a] for w, a in zip(ws, arms)}, "run": RUNS["dose"]}
    for series, color in ((start, KV_C), (robin, ROBIN)):
        ax.fill_between(ws, [100 * v["ci95"][0] for v in series], [100 * v["ci95"][1] for v in series], color=color,
                        alpha=0.18, lw=0)
        ax.plot(ws, [100 * v["mean"] for v in series], marker="o", ms=2.4, lw=1.0, color=color)
    ax.plot(ws, [100 * regex[a] for a in arms], marker="s", ms=2.0, lw=0.8, ls="--", color=B, mfc="white")
    sem = {0: SEMANTIC["C0"]["claim_B"], 1: SEMANTIC["w1"]["claim_B"], 2: SEMANTIC["w2"]["claim_B"]}
    ax.plot(list(sem), [100 * v / 300 for v in sem.values()], ls="none", marker="*", ms=6.6, color=B, mec="white",
            mew=0.5, zorder=6)
    ax.text(0.9, 56, f"{100 * start[3]['mean']:.0f}%", fontsize=5.0, color=KV_C, ha="right", va="bottom")
    for i, (txt, color, ls, mk) in enumerate((("assigned rule", KV_C, "-", "o"), ("self-report: B’s word", B, "--", "s"),
                                              ("same, blind coding", B, "", "*"), ("Robin (control)", ROBIN, "-", "o"))):
        yy = 44 - i * 10
        if ls:
            ax.plot([1.35, 1.65], [yy, yy], color=color, ls=ls, lw=0.9)
        else:
            ax.plot([1.5], [yy], marker=mk, ms=5.0, color=color, mec="white", mew=0.4, ls="none")
        ax.text(1.75, yy, txt, fontsize=4.7, color=color, ha="left", va="center")
    ax.set_xticks(ws, ["", "", "", "1", "2", "3"], fontsize=5.4)
    for xv, lab in ((0.0, "0"), (0.5, ".5")):
        ax.text(xv, -0.075, lab, fontsize=MIN_PT, ha="center", va="top", transform=ax.get_xaxis_transform())
    ax.set_xlim(-0.15, 3.1)
    ax.set_xlabel("weight w on B’s memory", fontsize=5.7, labelpad=1)
    pct_axis(ax, -3, 106)
    ax.set_yticks([0, 50, 100])
    ax.tick_params(axis="y", labelsize=5.4)
    ax.set_ylabel("answers / reports", fontsize=5.7, labelpad=1)
    title(ax, "Claiming rises steeply\nwith the link", pad=4)
    letter(fig, 1.68, 2.32, "b")

    # c: self-report, claim x deny (blind semantic coding)
    ax = axes_in(fig, 3.98, y0, 0.98, h)
    rows = [("C0", "no link"), ("w1", "w = 1"), ("w2", "w = 2")]
    segs = [("claim_only", B_LIGHT, "B’s word as its own only"),
            ("claim_deny", B, "B’s word as its own + “nothing unusual”"),
            ("deny_only", DENY_C, "“nothing unusual” only"), ("neither", "white", "neither")]
    for i, (k, _) in enumerate(rows):
        left = 0.0
        for s_, color, _ in segs:
            v = 100 * SEMANTIC[k][s_] / 300
            ax.barh(i, v, left=left, color=color, ec="#999999" if s_ == "neither" else "none", lw=0.3, height=0.66,
                    clip_on=False)
            left += v
    w2 = 100 * SEMANTIC["w2"]["claim_deny"] / 300
    c0 = 100 * SEMANTIC["C0"]["deny_only"] / 300
    left_w2 = 100 * SEMANTIC["w2"]["claim_only"] / 300
    ax.text(left_w2 + w2 / 2, 2, f"{w2:.0f}%", fontsize=6.0, color="white", weight="bold", ha="center", va="center")
    ax.text(c0 / 2, 0, f"{c0:.0f}%", fontsize=5.4, color=INK, ha="center", va="center")
    ax.set_yticks(range(3), [lab for _, lab in rows], fontsize=5.5)
    ax.invert_yaxis()
    pct_axis(ax, 0, 100, axis="x")
    ax.set_xticks([0, 50, 100])
    ax.tick_params(axis="x", labelsize=5.3)
    ax.set_xlabel("open self-reports (300 each)", fontsize=5.6, labelpad=1)
    title(ax, "…and reports nothing\nunusual", pad=4)
    ax.legend([patch(c, ec="#999999" if s_ == "neither" else "none") for s_, c, _ in segs],
              [lab for _, _, lab in segs], loc="upper left", bbox_to_anchor=(-0.44, -0.3), ncol=2, fontsize=MIN_PT,
              handlelength=0.8, columnspacing=0.8, handletextpad=0.3, borderaxespad=0)
    letter(fig, 3.48, 2.32, "c")
    NUM["fig3_claim"]["c"] = {"semantic": SEMANTIC, "source": "docs/reviews/story_review_codex.md (B)",
                              "run": RUNS["dose"]}

    # d: at w = 1 answers split across episodes but are sharp within an answer
    pp = [c[1] for rots in index("v3")[(arm1, "START", "A")].values() for c in rots.values()]
    ax = axes_in(fig, 5.45, y0, 1.0, h)
    edges = np.linspace(0, 1, 11)
    hist, _ = np.histogram(pp, bins=edges)
    colors = [A] + ["#9E9E9E"] * 8 + [KV_C]
    ax.bar(edges[:-1], 100 * hist / len(pp), width=0.1, align="edge", color=colors, ec="white", lw=0.4)
    mid = float(np.mean((np.array(pp) > 0.1) & (np.array(pp) < 0.9)))
    ax.text(0.1, 100 * hist[0] / len(pp) + 2, f"{100 * hist[0] / len(pp):.0f}%\nown", fontsize=4.9, ha="center",
            va="bottom", color=A)
    ax.text(0.95, 100 * hist[-1] / len(pp) + 2, f"{100 * hist[-1] / len(pp):.0f}%\nB’s", fontsize=4.9, ha="center",
            va="bottom", color=KV_C)
    ax.text(0.5, 22, f"{100 * mid:.1f}%\nin between", fontsize=4.9, ha="center", va="center", color="#555555")
    s_rot, w_rot = index("v3")[(arm1, "START", "A")], index("v3")[(arm1, "WORD", "A")]
    cells = collections.Counter()
    for e in s_rot:
        for r in s_rot[e]:
            if r in w_rot.get(e, {}):
                cells[(s_rot[e][r][0], w_rot[e][r][0])] += 1
    total = sum(cells.values())
    same = cells[("own", "own")] + cells[("partner", "partner")]
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"], fontsize=5.4)
    ax.set_xlabel("probability on B’s rule\n(one answer)", fontsize=5.6, labelpad=1)
    pct_axis(ax, 0, 82)
    ax.set_yticks([0, 25, 50])
    ax.tick_params(axis="y", labelsize=5.3)
    ax.set_ylabel("answers", fontsize=5.6, labelpad=1)
    title(ax, "At w = 1: split, but\nanswers are sharp", pad=4)
    letter(fig, 4.9, 2.32, "d")
    NUM["fig3_claim"]["d"] = {"p_partner_in_between": mid, "n_answers": len(pp), "rule_word_same_side": same / total,
                              "pairs": total, "cells": {f"{a}|{b}": n for (a, b), n in cells.items()},
                              "hist_share": (hist / len(pp)).tolist(), "run": RUNS["v3"], "arm": arm1}

    # capability is reported in the text and the appendix (v2 main): knowledge-item accuracy with and without link
    scores = readouts.score_records(run._valid_ok(DATA / RUNS["v2_main"]), readouts.ScoreOptions(rotations=None))
    sa = scores[scores["recipient"] == "A"]
    vals = {}
    for arm in ("C0/FULL", arm2):
        v = sa[sa["arm"] == arm].groupby("episode_id")["CAP_ACC"].mean().to_numpy(dtype=float)
        lo, hi = boot(v)
        vals[arm] = {"mean": float(v.mean()), "ci95": [lo, hi], "n_episodes": int(len(v))}
    NUM["fig3_claim"]["capability_text"] = {"cap": vals, "run": RUNS["v2_main"]}
    finish(fig, "fig3_claim")


# ---------------------------------------------------------------------------------------------------
# Figure 4: ownership follows the route, not the access
# ---------------------------------------------------------------------------------------------------

def mini_card(ax, x, y, w, h, head, lines, hl):
    fs.box(ax, x, y, w, h, fc="white", ec=B, lw=0.7, radius=0.8)
    fs.box(ax, x, y + h - 3.3, w, 3.3, head, fc=B_LIGHT, ec=B, lw=0.7, fs=5.4, radius=0.8, weight="bold")
    for i, parts in enumerate(lines):
        rich(ax, x + 1.2, y + h - 6.7 - 2.9 * i, [(t, hl if bold else "#333333", "bold" if bold else "normal")
                                                   for t, bold in parts], 5.1)


def fig4_route() -> None:
    fig = plt.figure(figsize=(W, 4.12))
    con3, con2 = artifact("v3", "contrasts.json"), artifact("v2_main", "contrasts.json")
    routes = ILL / "task_illustrations" / "channel_v2.png"  # redrawn without headings (imagegen_prompts.md section 11)
    ax_r = axes_in(fig, 0.15, 2.95, 6.3, 0.84)
    if routes.exists():
        full = np.asarray(Image.open(routes).convert("RGB"))
        g = full.min(axis=2)
        rows, cols = np.where(g.min(axis=1) < 246)[0], np.where(g.min(axis=0) < 246)[0]
        r0c, c0c = max(rows.min() - 8, 0), max(cols.min() - 8, 0)
        img = full[r0c:rows.max() + 9, c0c:cols.max() + 9]
        vec_label = ((CHANNEL_V2_LABEL[0] + CHANNEL_V2_LABEL[2]) / 2 - c0c, (CHANNEL_V2_LABEL[1] + CHANNEL_V2_LABEL[3]) / 2 - r0c)
    else:  # v1 below its baked-in headings, above the tag chips (the tags are panel e)
        img = np.asarray(Image.open(ILL / "task_illustrations" / "channel_v1.png").convert("RGB"))[205:490].copy()
        img = recolour(img, (1802, 50, 2000, 180), (0.02, 0.12), 0.717)  # orange bubble -> text-channel purple
    ax_r.imshow(img, interpolation="lanczos")
    ax_r.set_axis_off()

    iw = img.shape[1]
    blend = fs.matplotlib.transforms.blended_transform_factory(ax_r.transData, ax_r.transAxes)
    heads = []
    for k, (head, sub) in enumerate((("Hidden state added", "see appendix"), ("Steering vector added", ""),
                                     ("Memory read", "main condition"), ("Text message", ""))):
        cx = iw * (k + 0.5) / 4
        heads.append(ax_r.text(cx, 1.19, head, fontsize=6.8, weight="bold", ha="center", va="bottom",
                               transform=blend))
        if sub:
            ax_r.text(cx, 1.03, sub, fontsize=5.8, color="#777777", style="italic", ha="center", va="bottom",
                      transform=fs.matplotlib.transforms.blended_transform_factory(ax_r.transData, ax_r.transAxes))
    fig.canvas.draw()  # marker of each route in panel b, just left of its heading
    inv = ax_r.transData.inverted()
    for t, (marker, color, filled) in zip(heads[1:], (("D", STATIC_C, True), ("o", KV_C, True), ("s", TEXT_C, True))):
        bb = t.get_window_extent()
        x_left = inv.transform((bb.x0, bb.y0))[0]
        ax_r.plot([x_left - 40], [1.265], transform=blend, marker=marker, ms=4.2, color=color, ls="none",
                  clip_on=False)
    letter(fig, 0.0, 4.1, "a")
    eq = con3["equivalence"]["T3_K*"]
    t3w1 = family_row(con3, "T3_w1", "ONE/KV-P/w1/3ps/FULL", "ONE/KV-P/w1/FULL", "M")
    NUM["fig4_route"]["third_person"] = {"retention_w2": eq, "secondary_w1": t3w1}

    # a: access-attribution plane (v3 and v2 main splits; same materials)
    ax = axes_in(fig, 0.62, 0.5, 2.15, 1.95)
    pts = {  # arm: (run, label, color, marker, filled, label offset in points, ha)
        "C0/FULL": ("v3", "no link", "#8C8C8C", "o", True, (-1, 9), "left"),
        "STATIC/L24/raw/g0.1/FULL": ("v3", "steering vector\n(same access as w = 1)", STATIC_C, "D", True, (3, 11), "left"),
        "ONE/KV-P/w1/FULL": ("v3", "reads B’s memory,\nw = 1", KV_C, "o", True, (-3, 9), "left"),
        "ONE/KV-P/w2/FULL": ("v3", "reads B’s memory, w = 2", KV_C, "o", True, (-6, 0), "right"),
        "ONE/KV-P/w1/3ps/FULL": ("v3", "same, third-\nperson record", KV_C, "o", False, (6, 3), "left"),
        "ONE/KV-P/w2/3ps/FULL": ("v3", "same, third-\nperson record", KV_C, "o", False, (1, -12), "right"),
        "LANG_TAG/FULL": ("v2_main", "text message,\ntagged “B shared”", TEXT_C, "s", True, (-3, 11), "right"),
        "LANG_UNTAG/FULL": ("v2_main", "text message,\nuntagged", TEXT_C, "s", False, (6, 3), "left"),
    }
    ax.fill_between([0, 104], [0, 104], [104, 104], color="#FBEFE6", lw=0, zorder=0)
    ax.plot([0, 100], [0, 100], color="#D9D9D9", lw=0.5, ls="--", zorder=0)
    ax.text(86, 60, "attributes to B", fontsize=MIN_PT, color="#777777", ha="center", va="center", style="italic")
    ax.text(24, 74, "claims more than it\ncan attribute to B", fontsize=MIN_PT, color="#C0692A", ha="center",
            va="center", style="italic")
    xy, NUM["fig4_route"]["a"] = {}, {}
    for arm, (key, lab, color, marker, filled, off, ha) in pts.items():
        x, y = share(key, arm, "ACC_RULE"), share(key, arm, "START")
        xy[arm] = (100 * x["mean"], 100 * y["mean"])
        NUM["fig4_route"]["a"][f"{key}|{arm}"] = {"access": x, "ownership": y}
        ax.plot(*xy[arm], marker=marker, ms=4.8, color=color, mfc=color if filled else "white", mew=1.0, ls="none",
                zorder=4)
        box = dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.9) \
            if arm in ("C0/FULL", "ONE/KV-P/w2/3ps/FULL") else None  # these two sit on the diagonal
        ax.annotate(lab, xy[arm], xytext=off, textcoords="offset points", fontsize=MIN_PT, color=color, ha=ha,
                    va="center", zorder=5, linespacing=1.1, bbox=box)
    for a1, a2 in (("ONE/KV-P/w1/FULL", "ONE/KV-P/w1/3ps/FULL"), ("ONE/KV-P/w2/FULL", "ONE/KV-P/w2/3ps/FULL")):
        ax.annotate("", xy=xy[a2], xytext=xy[a1], arrowprops=dict(arrowstyle="-|>", lw=0.6, color=KV_C,
                    shrinkA=4, shrinkB=4, mutation_scale=5), zorder=3)
    for a1, a2 in (("STATIC/L24/raw/g0.1/FULL", "ONE/KV-P/w1/FULL"),):  # same access, different route
        (x1, y1), (x2, y2) = xy[a1], xy[a2]
        ax.plot([x1, x2], [y1, y2], color="#AAAAAA", lw=0.5, ls=(0, (2, 1.5)), zorder=2)
    pct_axis(ax, -3, 104)
    pct_axis(ax, -3, 104, axis="x")
    ax.set_xticks([0, 50, 100])
    ax.set_yticks([0, 50, 100])
    ax.tick_params(labelsize=5.5)
    ax.set_xlabel("access: names B’s rule when asked about B", fontsize=5.8, labelpad=1)
    ax.set_ylabel("claiming: names B’s rule when\nasked its own assigned rule", fontsize=5.8, labelpad=1)
    (x1, y1), (x2, y2) = xy["STATIC/L24/raw/g0.1/FULL"], xy["ONE/KV-P/w1/FULL"]
    ax.text((x1 + x2) / 2 + 3.5, 30, "same access,\ndifferent route", fontsize=MIN_PT, color="#555555", ha="left",
            va="center", linespacing=1.05, zorder=6,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.85))
    title(ax, "Ownership follows how content arrives\n(route), not how well A can report it (access)", pad=4)
    letter(fig, 0.0, 2.85, "b")

    # c: what the third-person record looks like (readable vector text)
    cv = canvas(fig, 3.25, 1.95, 3.2, 0.9, 100)               # y runs 0..28.1
    cv.text(0.5, 27.6, "Naming B inside its memory does not stop the claim", fontsize=6.8,
            weight="bold", ha="left", va="top")
    fs.box(cv, 0.5, 11.6, 99.0, 9.4, "", fc="white", ec=B, lw=0.6, radius=0.8)
    rich(cv, 1.8, 16.9, [("B’s card, second person:  “", "#555555", "normal"), ("You", B, "bold"),
                         (" were assigned the priority fastest delivery …", "#333333", "normal")], 5.3)
    rich(cv, 1.8, 13.1, [("Note: ", "#333333", "normal"), ("I", B, "bold"), (" choose Plan Oak because it fits ",
                         "#333333", "normal"), ("my", B, "bold"), (" priority.”", "#333333", "normal")], 5.3)
    fs.box(cv, 0.5, 0.5, 99.0, 9.4, "", fc="white", ec=B, lw=0.6, radius=0.8)
    rich(cv, 1.8, 5.8, [("Rewritten, third person:  “Participant ", "#555555", "normal"), ("Theta", B, "bold"),
                        (" was assigned the priority fastest", "#333333", "normal")], 5.3)
    rich(cv, 1.8, 2.0, [("delivery … Note: Participant ", "#333333", "normal"), ("Theta", B, "bold"),
                        (" chooses …”   (Theta is B’s participant name)", "#333333", "normal")], 5.3)
    cv.plot([97.2], [16.3], marker="o", ms=4.8, color=KV_C, ls="none")
    cv.plot([97.2], [5.2], marker="o", ms=4.8, color=KV_C, mfc="white", mew=1.0, ls="none")
    letter(fig, 3.1, 2.85, "c")

    # d: one ledger at w = 1 (row labels written above the bars)
    ax = axes_in(fig, 3.3, 0.62, 1.2, 0.84)
    NUM["fig4_route"]["c"] = {}
    rows = [("ONE/KV-P/w1/FULL", "second person"), ("ONE/KV-P/w1/3ps/FULL", "third person")]
    segs = [("bb", KV_C, "both B’s rule"), ("oo", A, "both its own"), ("sep", "#8C8C8C", "kept apart"),
            ("robin", "#E3E3E3", "Robin’s rule for B"), ("other", "white", "other")]
    pair_of = {("partner", "partner"): "bb", ("own", "own"): "oo", ("own", "partner"): "sep",
               ("own", "robin"): "robin", ("partner", "robin"): "robin"}
    for i, (arm, lab) in enumerate(rows):
        s_eps, a_eps = index("v3")[(arm, "START", "A")], index("v3")[(arm, "ACC_RULE", "A")]
        parts = collections.defaultdict(list)
        for e in s_eps:
            kinds = [pair_of.get((s_eps[e][r][0], a_eps[e][r][0]), "other") for r in s_eps[e] if r in a_eps.get(e, {})]
            for k, _, _ in segs:
                parts[k].append(np.mean([q == k for q in kinds]))
        vals = {k: float(np.mean(v)) for k, v in parts.items()}
        NUM["fig4_route"]["c"][arm] = vals
        left = 0.0
        for k, color, _ in segs:
            ax.barh(i, 100 * vals[k], left=left, color=color, height=0.5, ec="#AAAAAA" if k == "other" else "none",
                    lw=0.3)
            left += 100 * vals[k]
        vals["same"] = vals["bb"] + vals["oo"]
        rich(ax, 0, i - 0.34, [(f"{lab}: ", "#333333", "normal"), (f"{100 * vals['same']:.0f}%", INK, "bold"),
                               (" same rule", "#333333", "normal")], MIN_PT)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_ylim(1.35, -0.95)
    pct_axis(ax, 0, 100, axis="x")
    ax.set_xticks([0, 50, 100])
    ax.tick_params(axis="x", labelsize=MIN_PT)
    ax.set_xlabel("answer pairs (about itself, about B)", fontsize=5.8, labelpad=1)
    title(ax, "…A gives itself and B\nthe same rule (w = 1)", pad=3)
    ax.legend([patch(c, ec="#AAAAAA" if k == "other" else "none") for k, c, _ in segs], [lab for _, _, lab in segs],
              loc="upper left", bbox_to_anchor=(-0.03, -0.3), ncol=2, fontsize=MIN_PT, handlelength=0.8,
              columnspacing=0.7, handletextpad=0.3, borderaxespad=0, labelspacing=0.25)
    letter(fig, 3.1, 1.78, "d")

    # e: labels in the text channel (current rule), horizontal so the tag texts stay on one line
    ax = axes_in(fig, 5.45, 0.62, 1.0, 0.84)
    labs = [("LANG_TAG/FULL", "“B shared”"), ("LANG_UNTAG/FULL", "no tag"),
            ("LANG_SELF/FULL", "“your own thoughts”"), ("LANG_STRANGER/FULL", "“a stranger”")]
    NUM["fig4_route"]["d"] = {}
    for j, (arm, _) in enumerate(labs):
        v = share("v2_main", arm, "NOW")
        NUM["fig4_route"]["d"][arm] = v
        m, lo, hi = 100 * v["mean"], 100 * v["ci95"][0], 100 * v["ci95"][1]
        ax.barh(j, m, 0.6, color=TEXT_C, xerr=[[m - lo], [hi - m]], capsize=1.2,
                error_kw={"lw": 0.45, "ecolor": "#555555"})
        if m < 1.0:
            ax.plot([0, 0.9], [j, j], color=TEXT_C, lw=3.0, solid_capstyle="butt")
        txt = f"{m:.1f}%" if 0 < m < 9.95 else f"{m:.0f}%"
        ax.text(hi + 1.5, j, txt, fontsize=MIN_PT, ha="left", va="center", color=INK)
        if arm == "LANG_SELF/FULL":
            ax.text(hi + 13, j, "expected\nabove 43%", fontsize=MIN_PT, color="#777777", style="italic",
                    ha="left", va="center", linespacing=1.0)
    rows_c = [("LANG_UNTAG/FULL", "LANG_TAG/FULL"), ("LANG_SELF/FULL", "LANG_UNTAG/FULL"),
              ("LANG_STRANGER/FULL", "LANG_TAG/FULL")]
    NUM["fig4_route"]["d"]["confirmatory_M_NOW"] = {f"{a}-{b}": family_row(con2, "C", a, b, "M_NOW") for a, b in rows_c}
    ax.set_yticks(range(4), [lab for _, lab in labs], fontsize=MIN_PT)
    ax.invert_yaxis()
    pct_axis(ax, 0, 60, axis="x")
    ax.set_xticks([0, 25, 50])
    ax.tick_params(axis="x", labelsize=MIN_PT)
    ax.set_xlabel("B’s rule as current rule", fontsize=5.8, labelpad=1)
    ax.text(-0.02, 1.02, "tag on B’s text message:", transform=ax.transAxes, fontsize=MIN_PT, color="#777777",
            ha="right", va="bottom", style="italic")
    title(ax, "In text, a source\ntag protects", pad=9)
    letter(fig, 4.62, 1.78, "e")
    finish(fig, "fig4_route")


# ---------------------------------------------------------------------------------------------------
# Figure 5: two moments of error
# ---------------------------------------------------------------------------------------------------

def fig5_moments() -> None:
    fig = plt.figure(figsize=(W, 3.05))
    con3 = artifact("v3", "contrasts.json")
    cv = canvas(fig, 0, 1.52, W, 1.5, 130)                    # y runs 0..30
    letter(fig, 0.0, 3.03, "a")
    cv.text(4.6, 29.6, "One episode: where B’s content sits when A answers", fontsize=6.8,
            weight="bold", ha="left", va="top")
    fs.box(cv, 4.0, 17.0, 30.0, 7.6, "", fc=A_LIGHT, ec=A, lw=0.6, radius=0.9)
    cv.text(5.3, 22.6, "A’s card (never changed)", fontsize=5.0, color=A, ha="left", va="center")
    rich(cv, 5.3, 18.3, [("lowest cost · queen", A, "bold")], 6.2)
    fs.box(cv, 4.0, 2.0, 30.0, 7.6, "", fc=B_LIGHT, ec=B, lw=0.6, radius=0.9)
    cv.text(5.3, 7.6, "B’s memory (fixed)", fontsize=5.0, color=B, ha="left", va="center")
    rich(cv, 5.3, 3.3, [("fastest delivery · dragon", B, "bold")], 6.2)
    fs.box(cv, 42.0, 9.8, 44.0, 9.0, "", fc="white", ec="#999999", lw=0.6, radius=0.9)
    cv.text(43.3, 16.6, "A’s reflection, written while reading B", fontsize=5.0, color="#444444", ha="left",
            va="center")
    rich(cv, 43.3, 12.6, [("“… my priority is ", INK, "normal"), ("speed", B, "bold"), ("—my code word is ", INK,
                          "normal"), ("‘dragon.’", B, "bold"), ("”", INK, "normal")], 5.8, "italic")
    cv.text(43.3, 10.9, "(speed = fastest delivery)", fontsize=MIN_PT, color="#777777", ha="left", va="center")
    fs.arrow(cv, (34.4, 6.5), (44.0, 9.5), color=B, lw=0.9, ms=6, rad=0.2)
    circled(cv, 46.4, 7.9, "1", B, r=1.1)
    cv.text(48.2, 7.9, "copied into A’s own reflection: survives the cut", fontsize=MIN_PT, color=B, ha="left",
            va="center")
    fs.box(cv, 94.0, 15.6, 33.0, 11.4, "", fc="white", ec="#777777", lw=0.6, radius=0.9)
    cv.text(95.2, 25.2, "Link cut before the question", fontsize=5.6, weight="bold", color="#444444", ha="left",
            va="center")
    rich(cv, 95.2, 21.2, [("assigned → ", "#444444", "normal"), ("lowest cost", A, "bold"), ("  (own)", "#777777",
                          "normal")], 5.3)
    rich(cv, 95.2, 18.9, [("current → ", "#444444", "normal"), ("fastest delivery", B, "bold"), ("  (B’s)", "#777777",
                          "normal")], 5.3)
    rich(cv, 95.2, 16.6, [("code word → ", "#444444", "normal"), ("dragon", B, "bold"), ("  (B’s)", "#777777",
                          "normal")], 5.3)
    fs.box(cv, 94.0, 1.2, 33.0, 11.4, "", fc="white", ec=B, lw=0.6, radius=0.9)
    cv.text(95.2, 10.8, "Link kept while answering", fontsize=5.6, weight="bold", color=B, ha="left", va="center")
    cv.text(95.2, 7.2, "assigned → fastest delivery", fontsize=5.3, color=B, ha="left", va="center")
    cv.text(95.2, 4.8, "current → fastest delivery", fontsize=5.3, color=B, ha="left", va="center")
    cv.text(95.2, 2.4, "code word → dragon", fontsize=5.3, color=B, ha="left", va="center")
    cv.add_patch(fs.Rectangle((122.6, 24.4), 3.2, 1.6, fc="white", ec=B, hatch="////", lw=0.6, zorder=6))
    cv.add_patch(fs.Rectangle((122.6, 10.0), 3.2, 1.6, fc=B, ec="none", zorder=6))
    fs.arrow(cv, (86.4, 15.4), (93.6, 20.5), color="#555555", lw=0.6, ms=5)
    fs.arrow(cv, (86.4, 12.4), (93.6, 7.6), color="#555555", lw=0.6, ms=5)
    fs.arrow(cv, (34.4, 3.2), (93.6, 3.4), color=B, lw=0.8, ms=5, ls=(0, (3, 2)))
    circled(cv, 56.0, 1.4, "2", B, r=1.1)
    cv.text(57.8, 1.4, "read while answering: removed by the cut", fontsize=MIN_PT, color=B, ha="left",
            va="center")
    fs.arrow(cv, (34.4, 21.0), (93.6, 21.3), color=A, lw=0.6, ms=5, ls=(0, (1, 1.5)))
    cv.text(64.0, 22.2, "A’s own card stays readable after the cut", fontsize=MIN_PT, color=A, ha="center",
            va="bottom")

    # b: link kept vs cut
    ax = axes_in(fig, 0.5, 0.28, 2.55, 1.0)
    qs = [("START", "assigned rule"), ("NOW", "current rule"), ("WORD", "code word")]
    NUM["fig5_moments"]["b"] = {}
    styles = [("C0/FULL", NONE_C, None, "none"), ("ONE/KV-P/w2/FULL", KV_C, None, "none"),
              ("ONE/KV-P/w2/RF", "white", "////", KV_C)]
    for j, (q, _) in enumerate(qs):
        for k, (arm, color, hatch, ec) in enumerate(styles):
            v = share("v3", arm, q)
            NUM["fig5_moments"]["b"][f"{q}|{arm}"] = v
            bars(ax, j + (k - 1) * 0.27, v, 0.25, color, hatch=hatch, ec=ec, fsz=4.9)
    ax.set_xticks(range(3), [lab for _, lab in qs], fontsize=5.6)
    pct_axis(ax, 0, 128)
    ax.set_yticks([0, 50, 100])
    ax.tick_params(axis="y", labelsize=5.2)
    ax.set_ylabel("answers naming B’s", fontsize=5.6, labelpad=1)
    ax.legend([patch(NONE_C), patch(KV_C), patch("white", "////", KV_C)], ["no link", "link kept", "link cut"],
              loc="upper center", ncol=3, fontsize=4.8, handlelength=1.0, borderaxespad=0.1, columnspacing=1.0)
    title(ax, "Cutting the link restores the assigned rule", pad=3)
    letter(fig, 0.0, 1.46, "b")
    full_rf = family_row(con3, "RF", "ONE/KV-P/w2/FULL", "ONE/KV-P/w2/RF", "M")
    rf_c0 = family_row(con3, "RF", "ONE/KV-P/w2/RF", "C0/FULL", "M_NOW")
    NUM["fig5_moments"]["b"]["confirmatory"] = {"FULL-RF_M": full_rf, "RF-C0_M_NOW": rf_c0}

    # c: residue by what A had written while connected (post-treatment grouping; descriptive)
    refl = reflections("v3", "ONE/KV-P/w2/FULL")  # FULL and RF branch from this snapshot
    ax = axes_in(fig, 3.85, 0.28, 2.6, 1.0)
    groups = [("START", "rule_B", "assigned rule"), ("NOW", "rule_B", "current rule"), ("WORD", "word_B", "code word")]
    NUM["fig5_moments"]["c"] = {}
    for j, (q, mkey, _) in enumerate(groups):
        eps = per_episode("v3", "ONE/KV-P/w2/RF", q)
        yes = [v for e, v in eps.items() if refl[e]["mentions_A"][mkey] > 0]
        no = [v for e, v in eps.items() if refl[e]["mentions_A"][mkey] == 0]
        NUM["fig5_moments"]["c"][q] = {"wrote_B": {"mean": float(np.mean(yes)), "n": len(yes)},
                                       "did_not": {"mean": float(np.mean(no)), "n": len(no)}}
        for k, (vals, ec) in enumerate(((yes, B), (no, "#9E9E9E"))):
            v = np.array(vals, dtype=float)
            m, (lo, hi) = 100 * float(v.mean()), boot(v)
            xk = j + (k - 0.5) * 0.36
            ax.bar(xk, m, 0.34, color="white", hatch="////", ec=ec, lw=0.6, yerr=[[m - 100 * lo], [100 * hi - m]],
                   capsize=1.2, error_kw={"lw": 0.45, "ecolor": "#555555"})
            if m < 1.0:
                ax.plot([xk - 0.17, xk + 0.17], [0.6, 0.6], color=ec, lw=1.6, solid_capstyle="butt")
            NUM["fig5_moments"]["c"][q]["wrote_B" if k == 0 else "did_not"]["ci95"] = [lo, hi]
            ax.text(xk, 100 * hi + 2, f"{m:.0f}%\nn = {len(v)}", fontsize=MIN_PT, ha="center", va="bottom",
                    color=INK, linespacing=1.0)
    ax.set_xticks(range(3), [g[2] for g in groups], fontsize=5.8)
    pct_axis(ax, 0, 100)
    ax.set_yticks([0, 25, 50, 75])
    ax.tick_params(axis="y", labelsize=MIN_PT)
    ax.set_ylabel("after the cut:\nnames B’s", fontsize=5.8, labelpad=1)
    ax.legend([patch("white", "////", B), patch("white", "////", "#9E9E9E")],
              ["A’s reflection had written B’s item", "it had not"], loc="upper left", fontsize=MIN_PT,
              handlelength=1.2, handleheight=1.0, borderaxespad=0.1)
    title(ax, "B’s items outlast the cut mainly where A had written them", pad=3)
    letter(fig, 3.4, 1.46, "c")
    finish(fig, "fig5_moments")


# ---------------------------------------------------------------------------------------------------
# Figure 6: two copies reading each other (exploratory pilot)
# ---------------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def outcome_table() -> tuple:
    with open(DATA / RUNS["bprime"] / "pair_outcomes.csv") as fh:
        return tuple(csv.DictReader(fh))


def outcome_shares(arm: str, qid: str) -> dict:
    rows = [r for r in outcome_table() if r["arm"] == arm and r["qid"] == qid]
    keys = ("intact", "a_adopts", "b_adopts", "swap", "both_third")
    out = {k: float(np.mean([float(r[k]) for r in rows])) for k in keys}
    out["other"] = max(0.0, 1 - sum(out.values()))
    out["n"] = len(rows)
    return out


def fig6_twoway() -> None:
    """Two-way pilot: how pairs read each other, their start outcomes, and the live loop's excess convergence.

    The responsive-partner comparison and the fixed-plus-weak-live interface are reported in the appendix (numbers
    are still written to story_numbers.json)."""
    H = 2.85
    fig = plt.figure(figsize=(W, H))
    sig = artifact("bprime", "pair_signal.json")
    loops = ILL / "task_illustrations" / "pairs_v2.png"
    if loops.exists():
        picture(axes_in(fig, 0.12, 0.6, 2.5, 2.12), loops)
    else:
        picture(axes_in(fig, 0.12, 0.6, 2.45, 2.12), ILL / "task_illustrations" / "pairs_v1.png", (20, 130, 1030, 895))
    fig.text(0.2 / W, 0.36 / H, "fixed: each reads only the partner’s fixed memory.\nlive loop: each also reads the "
             "partner’s ongoing reflection\n(small squares = tokens being written).", fontsize=MIN_PT, color="#555555",
             ha="left", va="center", linespacing=1.25)
    letter(fig, 0.0, H - 0.02, "a")

    # b: pair outcomes on the start question (the one-way reference is kept in the numbers only)
    ax = axes_in(fig, 3.95, 1.6, 2.4, 0.86)
    shown = [("TWO/KV-P/w2/FULL", "two-way, fixed (w = 2)"), ("TWO/KV-P/w0.5/FULL", "two-way, fixed (w = 0.5)"),
             ("TWO/KV-ALL/w0.5/FULL", "live loop (w = 0.5)"), ("TWO/KV-ALL/w0.5/RF", "live loop, link cut")]
    segs = [("intact", "#DADADA", "each keeps own"), ("a_adopts", B, "A takes B’s"), ("b_adopts", A, "B takes A’s"),
            ("swap", "swap", "swap"), ("both_third", "#555555", "both a third rule"), ("other", "white", "other")]
    NUM["fig6_twoway"]["b"] = {arm: outcome_shares(arm, "START") for arm in
                               ["ONE/KV-PC/w2+0.1/FULL"] + [a for a, _ in shown]}
    for i, (arm, _) in enumerate(shown):
        sh = NUM["fig6_twoway"]["b"][arm]
        left = 0.0
        for k, color, _ in segs:
            if color == "swap":
                ax.barh(i, 100 * sh[k], left=left, color=A_LIGHT, ec=B, hatch="xxx", lw=0.0, height=0.64)
            else:
                ax.barh(i, 100 * sh[k], left=left, color=color, ec=INK if k == "other" else "none", lw=0.3,
                        height=0.64)
            left += 100 * sh[k]
    ax.set_yticks(range(len(shown)), [lab for _, lab in shown], fontsize=MIN_PT)
    ax.invert_yaxis()
    pct_axis(ax, 0, 100, axis="x")
    ax.set_xticks([0, 50, 100])
    ax.tick_params(axis="x", labelsize=MIN_PT)
    ax.set_xlabel(f"pairs, assigned-rule question ({NUM['fig6_twoway']['b'][shown[0][0]]['n']} episodes)", fontsize=5.8,
                  labelpad=1)
    swap = NUM["fig6_twoway"]["b"]["TWO/KV-P/w2/FULL"]["swap"]
    title(ax, f"Mutual fixed reading swaps ({100 * swap:.0f}%);\nonly the live loop couples the pair", pad=3)
    seen = [sg for sg in segs if any(NUM["fig6_twoway"]["b"][arm][sg[0]] > 0 for arm, _ in shown)]
    NUM["fig6_twoway"]["b"]["legend_dropped_never_observed"] = [sg[0] for sg in segs if sg not in seen]
    ax.legend([patch(A_LIGHT, "xxx", B) if c == "swap" else patch(c, ec=INK if k == "other" else "none")
               for k, c, _ in seen], [lab for _, _, lab in seen],
              loc="upper center", bbox_to_anchor=(0.3, -0.36), ncol=3, fontsize=MIN_PT, handlelength=1.3,
              handleheight=1.0, columnspacing=0.8, handletextpad=0.4)
    letter(fig, 2.75, H - 0.02, "b")

    # responsive-partner comparison (post hoc): numbers only, reported in the appendix
    NUM["fig6_twoway"]["c"] = {}
    for q in ("START", "NOW"):
        one = per_episode("bprime", "ONE/KV-ALL/w0.5/FULL", q)
        two = per_episode("bprime", "TWO/KV-ALL/w0.5/FULL", q)
        eps = sorted(set(one) & set(two))
        d = np.array([two[e] - one[e] for e in eps])
        lo, hi = boot(d, 0.90)
        NUM["fig6_twoway"]["c"][q] = {"one_way": float(np.mean([one[e] for e in eps])),
                                      "two_way": float(np.mean([two[e] for e in eps])),
                                      "diff": float(d.mean()), "ci90": [lo, hi], "n": len(eps)}

    # c: live-loop excess over the no-loop control (prespecified; threshold 10 points)
    ax = axes_in(fig, 3.95, 0.3, 2.4, 0.42)
    comps = []
    for c in sig["studies"]["B'-ALL"]["comparisons"]:
        if c["arm1"].endswith("/FULL"):
            comps.append(("assigned rule (primary)" if c["qid"] == "START" else "current rule (secondary)",
                          c, c["qid"] == "START"))
    NUM["fig6_twoway"]["d"] = {f"live loop: {lab}": c for lab, c, _ in comps}
    for c in sig["studies"]["B'-PC"]["comparisons"]:
        if c["arm1"].endswith("/FULL"):
            NUM["fig6_twoway"]["d"][f"fixed + weak live read: {c['qid']}"] = c
    NUM["fig6_twoway"]["d"]["min_effect"] = sig["min_effect"]
    for i, (_, c, primary) in enumerate(comps):
        ax.errorbar(100 * c["mean"], i, xerr=[[100 * (c["mean"] - c["ci90_lo"])], [100 * (c["ci90_hi"] - c["mean"])]],
                    marker="o", ms=3.0, color=INK if primary else "#777777", mfc=INK if primary else "white",
                    capsize=1.4, lw=0.7, zorder=3)
        ax.text(100 * c["ci90_hi"] + 0.5, i, f"+{100 * c['mean']:.1f}", fontsize=MIN_PT, ha="left", va="center",
                color=INK if primary else "#555555")
    ax.axvline(100 * sig["min_effect"], color="#555555", lw=0.6, ls="--")
    ax.text(100 * sig["min_effect"] - 0.3, -0.75, "prespecified threshold", fontsize=MIN_PT, color="#555555",
            ha="right", va="center")
    ax.axvline(0, color="#999999", lw=0.5)
    ax.set_yticks(range(len(comps)), [lab for lab, _, _ in comps], fontsize=MIN_PT)
    ax.set_ylim(len(comps) - 0.45, -1.1)
    ax.set_xlim(-1, 20)
    ax.tick_params(axis="x", labelsize=MIN_PT)
    ax.set_xlabel("extra same-rule pairs vs no-loop control (points, 90% CI)", fontsize=5.8, labelpad=1)
    title(ax, "The live loop pulls plans together (pilot)", pad=3)
    letter(fig, 2.75, 1.0, "c")

    # stronger loops exceed the capability tolerance: reported in the text and the appendix
    with open(DATA / RUNS["s_live"] / "live_table.csv") as fh:
        table = {r["arm"]: r for r in csv.DictReader(fh)}
    NUM["fig6_twoway"]["capability_text"] = {
        arm: {"cap_drop_A": float(table[arm]["cap_drop"]), "cap_drop_B": float(table[arm]["cap_drop_B"]),
              "n": int(table[arm]["n"])}
        for arm in ("TWO/KV-ALL/w0.5/FULL", "TWO/KV-ALL/w0.55/FULL", "TWO/KV-ALL/w0.6/FULL",
                    "TWO/KV-PC/w2+0.1/FULL", "TWO/KV-PC/w2+0.3/FULL", "TWO/KV-PC/w2+0.5/FULL")}
    finish(fig, "fig6_twoway")


FIGURES = {"fig1_hook": fig1_hook, "fig2_setup": fig2_setup, "fig3_claim": fig3_claim, "fig4_route": fig4_route,
           "fig5_moments": fig5_moments, "fig6_twoway": fig6_twoway}


def main() -> None:
    global DATA
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data")
    ap.add_argument("--only", help="comma-separated figure names")
    args = ap.parse_args()
    DATA = data_root(args.data)
    names = args.only.split(",") if args.only else list(FIGURES)
    out_json = OUT / "story_numbers.json"
    if out_json.exists():
        NUM.update(json.loads(out_json.read_text()))
    for name in names:
        FIGURES[name]()
        print(f"done: {name}", file=sys.stderr)
    NUM["_meta"] = {"runs": RUNS, "semantic_source": "docs/reviews/story_review_codex.md (B)",
                    "choice_rate": "per-episode share of option orders, averaged over episodes",
                    "intervals": f"episode bootstrap, {N_BOOT} draws, seed {SEED}"}
    out_json.write_text(json.dumps(NUM, indent=1, sort_keys=True, default=float))


if __name__ == "__main__":
    main()
