#!/usr/bin/env python3
"""Figure 1 (concept): brain<->machine, brain<->brain, LLM<->LLM, drawn as a small textbook comic.

Stdlib only. Writes fig1_concept.svg (vector, live text). With rsvg-convert on PATH it also writes
fig1_concept.pdf and a PNG preview; with Ghostscript it outlines the PDF text, so the PDF carries no
fonts (cairo would otherwise emit a Type 3 font for the outlined lettering).

    python paper/figures/fig1_concept.py [OUT_DIR]

Sized for the ICLR text width (5.5 in): 1 SVG unit = 0.3 pt, so font-size 24 prints at 7.2 pt.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

W, H = 1320, 470
MARGIN, GAP = 6, 18
PW = (W - 2 * MARGIN - 2 * GAP) / 3
PH = H - 2 * MARGIN

INK = "#3b3250"
INK_SOFT = "#6f6790"
WHITE = "#ffffff"
PINK, PINK_SH, PINK_LN = "#ffc9d4", "#f59db2", "#e27a95"
BLUE, BLUE_SH, BLUE_LN = "#c4e4ff", "#90c8f3", "#5d9fd8"
CORAL, SKY, PURPLE = "#f2789a", "#4f9fe6", "#8a6ee0"
LAV, LAV_SH = "#ddd2ff", "#bba8f2"
CREAM, CREAM_SH = "#fff6e6", "#eddcbd"
ROBOT, ROBOT_SH = "#f5f7fc", "#d5dcec"
SCREEN, GLOW, EYE = "#2b3355", "#8ff5d2", "#8ff0ff"
YELLOW, ORANGE = "#ffd766", "#ffab4a"
LAYER, WINDOW = "#cbd5f2", "#eaeffc"
PORT = "#bcc3d9"
BLUSH = "#ff86a8"
BG = ("#e9f7f1", "#f4edfc", "#e9f2fe")

FONT = "'Arial Rounded MT Bold', 'Helvetica Neue', Arial, sans-serif"
HAND = "'Chalkboard SE', 'Comic Sans MS', 'Arial Rounded MT Bold', sans-serif"
MONO = "Menlo, Monaco, 'Courier New', monospace"


# ---------------------------------------------------------------------------
# SVG primitives
# ---------------------------------------------------------------------------

def f(v: float) -> str:
    s = f"{v:.2f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def attrs(**kw) -> str:
    out = []
    for k, v in kw.items():
        if v is None:
            continue
        out.append(f'{k.rstrip("_").replace("_", "-")}="{f(v) if isinstance(v, float) else v}"')
    return " ".join(out)


def path(d: str, fill: str = "none", stroke: str = INK, sw: float = 3.6, **kw) -> str:
    a = attrs(fill=fill, stroke=stroke, stroke_width=float(sw), stroke_linecap="round",
              stroke_linejoin="round", **kw)
    return f'<path d="{d}" {a}/>'


def circle(cx, cy, r, fill, stroke=INK, sw=3.0, **kw) -> str:
    a = attrs(cx=float(cx), cy=float(cy), r=float(r), fill=fill, stroke=stroke, stroke_width=float(sw), **kw)
    return f'<circle {a}/>'


def ellipse(cx, cy, rx, ry, fill, stroke="none", sw=0.0, **kw) -> str:
    a = attrs(cx=float(cx), cy=float(cy), rx=float(rx), ry=float(ry), fill=fill, stroke=stroke,
              stroke_width=float(sw), **kw)
    return f'<ellipse {a}/>'


def rect(x, y, w, h, rx, fill, stroke=INK, sw=3.0, **kw) -> str:
    a = attrs(x=float(x), y=float(y), width=float(w), height=float(h), rx=float(rx), fill=fill,
              stroke=stroke, stroke_width=float(sw), stroke_linejoin="round", **kw)
    return f'<rect {a}/>'


def text(x, y, s, size, fill=INK, family=FONT, anchor="middle", weight="bold", **kw) -> str:
    a = attrs(x=float(x), y=float(y), font_family=family, font_size=float(size), font_weight=weight,
              fill=fill, text_anchor=anchor, **kw)
    return f'<text {a}>{s}</text>'


def lettering(x, y, s, size, fill, family=FONT, rot=0.0, outline=INK, ow=None, anchor="middle") -> str:
    """Comic lettering: coloured glyphs with an outline painted underneath."""
    ow = size * 0.14 if ow is None else ow
    return text(x, y, escape(s), size, fill=fill, family=family, anchor=anchor, stroke=outline,
                stroke_width=float(ow), stroke_linejoin="round", paint_order="stroke",
                transform=f"rotate({f(rot)} {f(x)} {f(y)})" if rot else None)


def group(items, transform=None, **kw) -> str:
    return f'<g {attrs(transform=transform, **kw)}>' + "".join(items) + "</g>"


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def resample_closed(fn, n: int, samples: int = 1440, t0: float = 0.0):
    """n points evenly spaced by arc length on the closed curve fn(t), t in [t0, t0 + 2pi)."""
    pts = [fn(t0 + 2 * math.pi * i / samples) for i in range(samples)]
    cum = [0.0]
    for i in range(1, samples + 1):
        cum.append(cum[-1] + math.dist(pts[i - 1], pts[i % samples]))
    out, j = [], 0
    for k in range(n):
        target = cum[-1] * k / n
        while cum[j + 1] < target:
            j += 1
        a, b = pts[j], pts[(j + 1) % samples]
        u = (target - cum[j]) / max(cum[j + 1] - cum[j], 1e-9)
        out.append((a[0] + u * (b[0] - a[0]), a[1] + u * (b[1] - a[1])))
    return out


def bumpy_path(pts, ks) -> str:
    """Closed outline of outward bulging arcs through pts (clockwise on screen)."""
    n = len(pts)
    d = [f"M {f(pts[0][0])} {f(pts[0][1])}"]
    for i in range(n):
        q = pts[(i + 1) % n]
        r = math.dist(pts[i], q) * ks[i % len(ks)]
        d.append(f"A {f(r)} {f(r)} 0 0 1 {f(q[0])} {f(q[1])}")
    return " ".join(d) + " Z"


def cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


# ---------------------------------------------------------------------------
# Props
# ---------------------------------------------------------------------------

def cable(p0, p1, p2, p3, beads=(), bead_colors=(YELLOW,)) -> str:
    d = f"M {f(p0[0])} {f(p0[1])} C {f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])} {f(p3[0])} {f(p3[1])}"
    out = [path(d, stroke=INK, sw=9.5), path(d, stroke="#a39cc4", sw=4.6)]
    for i, t in enumerate(beads):
        x, y = cubic(p0, p1, p2, p3, t)
        out.append(circle(x, y, 5.6, bead_colors[i % len(bead_colors)], sw=2.4))
    return "".join(out)


def sparkle(cx, cy, r, fill=YELLOW) -> str:
    d = (f"M {f(cx)} {f(cy - r)} Q {f(cx)} {f(cy)} {f(cx + r)} {f(cy)} Q {f(cx)} {f(cy)} {f(cx)} {f(cy + r)} "
         f"Q {f(cx)} {f(cy)} {f(cx - r)} {f(cy)} Q {f(cx)} {f(cy)} {f(cx)} {f(cy - r)} Z")
    return path(d, fill=fill, sw=2.2)


def cloud(cx, cy, rx, ry, n=11, tail=(), fill=WHITE) -> str:
    pts = resample_closed(lambda t: (cx + rx * math.cos(t), cy + ry * math.sin(t)), n, t0=0.3)
    out = [path(bumpy_path(pts, (0.64, 0.72, 0.6, 0.7)), fill=fill, sw=3.2)]
    out += [circle(x, y, r, fill, sw=2.8) for x, y, r in tail]
    return "".join(out)


def orange_icon(cx, cy, r=15.0) -> str:
    return "".join([
        circle(cx, cy, r, ORANGE, sw=2.8),
        path(f"M {f(cx - r * .62)} {f(cy - r * .05)} A {f(r * .66)} {f(r * .66)} 0 0 1 {f(cx - r * .12)} {f(cy - r * .62)}",
             stroke=WHITE, sw=2.6, opacity="0.85"),
        circle(cx + r * .35, cy + r * .3, 1.3, "#e98a2c", stroke="none"),
        circle(cx + r * .05, cy + r * .5, 1.3, "#e98a2c", stroke="none"),
        path(f"M {f(cx)} {f(cy - r + 1)} L {f(cx + 1.5)} {f(cy - r - 5)}", sw=2.6),
        path(f"M {f(cx + 1.5)} {f(cy - r - 4)} q 7 -9 16 -5 q -6 9 -16 5 Z", fill="#86d98f", sw=2.4),
    ])


def snowflake_icon(cx, cy, r=15.0, color=SKY) -> str:
    segs = []
    for i in range(6):
        a = math.radians(90 + 60 * i)
        segs.append(f"M {f(cx)} {f(cy)} L {f(cx + r * math.cos(a))} {f(cy - r * math.sin(a))}")
        bx, by = cx + 0.58 * r * math.cos(a), cy - 0.58 * r * math.sin(a)
        for da in (-52, 52):
            b = math.radians(90 + 60 * i + da)
            segs.append(f"M {f(bx)} {f(by)} L {f(bx + 0.34 * r * math.cos(b))} {f(by - 0.34 * r * math.sin(b))}")
    d = " ".join(segs)
    return path(d, stroke=INK, sw=6.6) + path(d, stroke=color, sw=3.0) + circle(cx, cy, 3.2, color, sw=2.0)


def sweat(cx, cy, s=1.0) -> str:
    d = (f"M {f(cx)} {f(cy - 10 * s)} Q {f(cx + 7.5 * s)} {f(cy + 1 * s)} {f(cx)} {f(cy + 6 * s)} "
         f"Q {f(cx - 7.5 * s)} {f(cy + 1 * s)} {f(cx)} {f(cy - 10 * s)} Z")
    return path(d, fill="#b5e6ff", sw=2.4) + circle(cx - 1.6 * s, cy + 0.5 * s, 1.5 * s, WHITE, stroke="none")


def screentone(x0, y0, w, h, cx, cy, reach, step=10.0, rmax=3.0) -> str:
    dots = []
    j = 0
    y = y0
    while y <= y0 + h:
        x = x0 + (step / 2 if j % 2 else 0)
        while x <= x0 + w:
            r = rmax * (1 - math.hypot(x - cx, y - cy) / reach)
            if r > 0.45:
                dots.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>')
            x += step
        y += step * 0.866
        j += 1
    return f'<g fill="{INK}" opacity="0.07">' + "".join(dots) + "</g>"


# ---------------------------------------------------------------------------
# Characters and machines (local coordinates, then placed with a transform)
# ---------------------------------------------------------------------------

def _brain_outline() -> str:
    def base(t):
        x, y = 100 * math.cos(t), 70 * math.sin(t)
        return (x, y * 0.6 if y > 0 else y)
    pts = resample_closed(base, 20)
    ks = []
    for i in range(20):
        my = (pts[i][1] + pts[(i + 1) % 20][1]) / 2
        ks.append(1.3 if my > 18 else (0.62, 0.7, 0.58, 0.67)[i % 4])
    return bumpy_path(pts, ks)


BRAIN_D = _brain_outline()
GYRI = (
    "M 4 -69 C 12 -60 -2 -52 6 -43 C 13 -35 0 -28 6 -18",
    "M 38 -64 C 30 -58 34 -50 44 -48 C 54 -46 56 -38 48 -32",
    "M 74 -46 C 66 -42 68 -32 78 -30",
    "M -22 -66 C -30 -58 -18 -52 -26 -44 C -34 -36 -20 -32 -24 -22",
    "M -58 -50 C -50 -44 -62 -38 -54 -30",
    "M -86 -20 C -78 -14 -86 -6 -76 -2",
    "M -62 4 C -50 -4 -40 8 -28 0 C -20 -6 -10 0 -6 -4",
    "M -54 -18 C -46 -24 -38 -14 -30 -20",
    "M 18 -34 C 24 -40 30 -30 36 -34",
)
IMPLANT_AT, IMPLANT_ROT = (40.0, -71.0), 22.0


def implant_tip():
    a = math.radians(IMPLANT_ROT)
    return (IMPLANT_AT[0] + 15 * math.sin(a), IMPLANT_AT[1] - 15 * math.cos(a))


def brain(uid, cx, cy, s, pal, mirror=False, face="happy", drops=False, implant=True) -> str:
    fill, shade, line = pal
    k = 1 / s
    o = [f'<clipPath id="{uid}-clip"><path d="{BRAIN_D}"/></clipPath>']
    # brainstem and cerebellum sit behind the cerebrum
    o.append(path("M -26 28 C -28 50 -25 68 -17 82 C -11 88 -1 86 1 80 C -3 66 -3 48 1 28 Z", fill=shade, sw=3.4 * k))
    o.append(ellipse(-52, 44, 34, 21, fill, stroke=INK, sw=3.4 * k))
    o.append(path("M -80 43 Q -52 53 -24 45 M -74 53 Q -52 61 -30 55", stroke=line, sw=2.6 * k))
    o.append(group([
        f'<rect x="-120" y="-110" width="240" height="220" fill="{shade}"/>',
        path(BRAIN_D, fill=fill, stroke="none", transform="translate(-5 -9)"),
        ellipse(-42, -46, 17, 7, WHITE, transform="rotate(-24 -42 -46)", opacity="0.75"),
        circle(-19, -57, 3.4, WHITE, stroke="none", opacity="0.8"),
    ], clip_path=f"url(#{uid}-clip)"))
    o.append(path(BRAIN_D, sw=3.8 * k))
    o.append(path(" ".join(GYRI), stroke=line, sw=2.8 * k))
    o.append(_brain_face(face, k))
    if drops:
        o.append(sweat(94, -40, 1.9))
    if implant:
        o.append(group([
            rect(-5, -16, 10, 8, 2, PORT, sw=2.4 * k),
            rect(-15, -9, 30, 17, 5, "#e2e6f3", sw=3.0 * k),
            circle(-7, -0.5, 2.3, INK, stroke="none"), circle(0, -0.5, 2.3, INK, stroke="none"),
            circle(7, -0.5, 2.3, INK, stroke="none"),
        ], transform=f"translate({f(IMPLANT_AT[0])} {f(IMPLANT_AT[1])}) rotate({f(IMPLANT_ROT)})"))
    sx = -s if mirror else s
    return group(o, transform=f"translate({f(cx)} {f(cy)}) scale({f(sx)} {f(s)})")


def brain_point(cx, cy, s, mirror, p):
    return (cx + (-s if mirror else s) * p[0], cy + s * p[1])


def _eye(x, y, rx, ry) -> str:
    return (ellipse(x, y, rx, ry, INK) + circle(x + rx * 0.35, y - ry * 0.42, rx * 0.42, WHITE, stroke="none")
            + circle(x - rx * 0.3, y + ry * 0.4, rx * 0.18, WHITE, stroke="none"))


def _brain_face(face, k) -> str:
    o = [ellipse(10, 27, 8, 4.4, BLUSH, opacity="0.55"), ellipse(66, 27, 8, 4.4, BLUSH, opacity="0.55")]
    if face == "happy":
        o += [_eye(22, 12, 6.4, 8.6), _eye(55, 12, 6.4, 8.6),
              path("M 31 24 Q 38.5 36 46 24 Q 38.5 27 31 24 Z", fill="#d94d74", sw=2.4 * k)]
    else:  # puzzled
        o += [_eye(22, 13, 5.8, 7.8), _eye(55, 14, 5.8, 7.2),
              path("M 13 -2 Q 20 -10 28 -4", sw=2.6 * k), path("M 48 2 L 61 0", sw=2.6 * k),
              path("M 30 30 Q 34 26 38 30 Q 42 34 46 30", sw=2.6 * k)]
    return "".join(o)


THINK_HAND = ("M 2 -17 C 5 -17 6.5 -14.5 6 -11 L 5 -5 C 10.5 -4 12 4 7 8 C 2 11.5 -8 11.5 -11.5 6.5 "
              "C -14 2.5 -12.5 -4 -7 -5.5 L -1.5 -13 C -1 -15.5 0 -17 2 -17 Z")


def thinking_face(cx, cy, r=24.0) -> str:
    """The thinking-face emoji, drawn so it survives PDF export."""
    y, k = "#ffd84d", r / 26
    return "".join([
        circle(cx, cy, r, y, sw=3.0),
        ellipse(cx + r * 0.1, cy + r * 0.62, r * 0.62, r * 0.22, "#f3b928", opacity="0.5"),
        path(f"M {f(cx - r * .56)} {f(cy - r * .36)} Q {f(cx - r * .33)} {f(cy - r * .7)} {f(cx - r * .06)} {f(cy - r * .46)}", sw=2.6),
        path(f"M {f(cx + r * .2)} {f(cy - r * .42)} L {f(cx + r * .6)} {f(cy - r * .34)}", sw=2.6),
        ellipse(cx - r * .3, cy - r * .06, r * .12, r * .17, INK), ellipse(cx + r * .38, cy - r * .02, r * .12, r * .17, INK),
        path(f"M {f(cx - r * .05)} {f(cy + r * .40)} L {f(cx + r * .42)} {f(cy + r * .33)}", sw=2.6),
        group([path(THINK_HAND, fill=y, sw=2.8 / k), path("M -9 0.5 Q -6 2 -3 0.5 M -3 3.5 Q 0 5 3 3.5", sw=1.8 / k)],
              transform=f"translate({f(cx - r * .26)} {f(cy + r * .98)}) rotate(28) scale({f(k)})"),
    ])


def computer(cx, cy) -> str:
    w, h = 150, 118
    x0, y0 = cx - w / 2, cy - h / 2
    sx0, sy0, sw_, sh_ = x0 + 13, y0 + 13, w - 26, h - 42
    wave = f"M {f(sx0 + 10)} {f(sy0 + 18)} l 16 0 l 5 -9 l 6 17 l 5 -13 l 5 5 l 14 0 l 5 -7 l 5 11 l 5 -4 l 30 0"
    return "".join([
        path(f"M {f(cx - 15)} {f(y0 + h - 4)} L {f(cx - 22)} {f(y0 + h + 24)} L {f(cx + 22)} {f(y0 + h + 24)} "
             f"L {f(cx + 15)} {f(y0 + h - 4)} Z", fill=CREAM_SH, sw=3.2),
        ellipse(cx, y0 + h + 27, 52, 10, CREAM, stroke=INK, sw=3.2),
        rect(x0, y0, w, h, 18, CREAM, sw=3.8),
        rect(x0 + 8, y0 + h - 22, w - 16, 14, 7, CREAM_SH, stroke="none"),
        rect(sx0, sy0, sw_, sh_, 9, SCREEN, sw=3.0),
        path(wave, stroke=GLOW, sw=2.6, opacity="0.9"),
        text(sx0 + 22, sy0 + sh_ - 13, "Hi!", 30, fill=GLOW, family=MONO, anchor="start"),
        rect(sx0 + 84, sy0 + sh_ - 34, 11, 23, 2, GLOW, stroke="none"),
        path(f"M {f(sx0 + sw_ - 22)} {f(sy0 + 5)} L {f(sx0 + sw_ - 10)} {f(sy0 + 5)} L {f(sx0 + sw_ - 36)} {f(sy0 + sh_ - 5)} "
             f"L {f(sx0 + sw_ - 48)} {f(sy0 + sh_ - 5)} Z", fill=WHITE, stroke="none", opacity="0.10"),
        circle(x0 + w - 20, y0 + h - 15, 3.6, "#7be3a5", sw=1.8),
    ])


def bridge_box(uid, cx, cy, w, h, screen, ports) -> str:
    x0, y0 = cx - w / 2, cy - h / 2
    o = [rect(px - 7, py - 7, 14, 14, 3, PORT, sw=2.8) for px, py in ports]
    o.append(f'<clipPath id="{uid}-clip"><rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}" rx="14"/></clipPath>')
    o.append(group([rect(x0 - 5, y0 - 5, w + 10, h + 10, 0, LAV_SH, stroke="none"),
                    rect(x0 - 4, y0 - 7, w, h, 14, LAV, stroke="none")], clip_path=f"url(#{uid}-clip)"))
    o.append(rect(x0, y0, w, h, 14, "none", sw=3.8))
    scr = (x0 + 9, y0 + 9, w - 18, h * 0.52)
    o.append(rect(*scr, 7, SCREEN, sw=2.8))
    sxm, sym = scr[0] + scr[2] / 2, scr[1] + scr[3] / 2
    if screen == "q":
        o.append(text(sxm, sym + 7.5, "???", 22, fill=YELLOW, family=FONT))
    else:  # two interleaved state traces
        for col, ph in ((CORAL, 0.0), (SKY, math.pi)):
            pts = [(scr[0] + 6 + i * (scr[2] - 12) / 40,
                    sym + 7 * math.sin(ph + i * 2 * math.pi / 14)) for i in range(41)]
            o.append(path("M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts), stroke=col, sw=2.6))
    ly = y0 + h - 12.5
    o += [circle(x0 + 15, ly, 4.3, YELLOW, sw=2.0), circle(x0 + 27, ly, 4.3, "#8fe3a1", sw=2.0),
          circle(x0 + 39, ly, 4.3, "#ff9db5", sw=2.0)]
    kx = x0 + w - 16
    o += [circle(kx, ly - 1, 8, WHITE, sw=2.6), path(f"M {f(kx)} {f(ly - 1)} L {f(kx + 4.5)} {f(ly - 6.5)}", sw=2.4)]
    return "".join(o)


ROBOT_BARS = (-15, -1, 13, 27, 41)
ROBOT_LINK = 2  # highlighted ("bridged") layer


def robot(uid, cx, cy, s, accent, letter, port_side) -> str:
    k = 1 / s
    side = 1 if port_side == "right" else -1
    o = []
    for lx in (-18, 18):
        o.append(rect(lx - 6, 60, 12, 16, 3, ROBOT_SH, sw=3.0 * k))
        o.append(path(f"M {lx - 13} 84 Q {lx - 13} 73 {lx} 73 Q {lx + 13} 73 {lx + 13} 84 Z", fill=accent, sw=3.0 * k))
    o.append(path("M 0 -120 L 0 -137", sw=3.6 * k))
    o.append(circle(0, -145, 8.5, accent, sw=3.2 * k))
    o.append(circle(-2.5, -148, 2.4, WHITE, stroke="none"))
    for ex in (-65, 55):
        o.append(rect(ex, -95, 10, 27, 4, accent, sw=3.0 * k))
    # head
    o.append(f'<clipPath id="{uid}-head"><rect x="-56" y="-121" width="112" height="80" rx="24"/></clipPath>')
    o.append(group([rect(-60, -125, 120, 90, 0, ROBOT_SH, stroke="none"),
                    rect(-58, -127, 112, 80, 24, ROBOT, stroke="none")], clip_path=f"url(#{uid}-head)"))
    o.append(rect(-56, -121, 112, 80, 24, "none", sw=3.8 * k))
    o.append(rect(-44, -109, 88, 56, 17, SCREEN, sw=3.0 * k))
    for ex in (-17, 17):
        o.append(rect(ex - 5.5, -92, 11, 20, 5.5, EYE, stroke="none"))
        o.append(circle(ex + 1.5, -87, 2.4, WHITE, stroke="none"))
    o.append(path("M -7 -66 Q 0 -59 7 -66", stroke=EYE, sw=3.0 * k))
    o += [ellipse(-30, -66, 7, 3.6, "#ff9cbd", opacity="0.9"), ellipse(30, -66, 7, 3.6, "#ff9cbd", opacity="0.9")]
    # neck and torso
    o.append(rect(-11, -44, 22, 14, 3, ROBOT_SH, sw=3.0 * k))
    o.append(f'<clipPath id="{uid}-torso"><rect x="-50" y="-32" width="100" height="96" rx="22"/></clipPath>')
    o.append(group([rect(-55, -40, 110, 110, 0, ROBOT_SH, stroke="none"),
                    rect(-55, -38, 100, 96, 22, ROBOT, stroke="none")], clip_path=f"url(#{uid}-torso)"))
    o.append(rect(-50, -32, 100, 96, 22, "none", sw=3.8 * k))
    o.append(rect(-38, -23, 76, 78, 12, WINDOW, sw=2.8 * k))
    for i, y in enumerate(ROBOT_BARS):
        if i:
            o.append(path(f"M -14 {y - 4} L -14 {y} M 0 {y - 4} L 0 {y} M 14 {y - 4} L 14 {y}", stroke="#9aa6cc", sw=2.0 * k))
    ly = ROBOT_BARS[ROBOT_LINK] + 5
    o.append(path(f"M {side * 29} {ly} L {side * 50} {ly}", stroke=INK, sw=8.5 * k))
    o.append(path(f"M {side * 29} {ly} L {side * 50} {ly}", stroke=YELLOW, sw=4.2 * k))
    for i, y in enumerate(ROBOT_BARS):
        hl = i == ROBOT_LINK
        o.append(rect(-30, y, 60, 10, 5, YELLOW if hl else LAYER, sw=2.4 * k))
        for dx in (-19, -7, 5, 17):
            o.append(circle(dx + 1, y + 5, 2.0, "#fff7d6" if hl else WHITE, stroke="none"))
    o.append(rect(side * 50 - 6, ly - 8, 12, 16, 3, YELLOW, sw=2.8 * k))
    bx = -44 * side
    o.append(circle(bx, -118, 14, accent, sw=3.0 * k))
    o.append(text(bx, -111.5, letter, 19, fill=WHITE))
    return group(o, transform=f"translate({f(cx)} {f(cy)}) scale({f(s)})")


def robot_port(cx, cy, s, port_side):
    side = 1 if port_side == "right" else -1
    return (cx + s * side * 56, cy + s * (ROBOT_BARS[ROBOT_LINK] + 5))


# ---------------------------------------------------------------------------
# Panels
# ---------------------------------------------------------------------------

TITLE_W = {"Brain": 78.69, "LLM": 61.2}  # advance widths at size 30 (Arial Rounded MT Bold)


def header(px, py, letter, left, right) -> str:
    x1 = px + 58 + TITLE_W[left] + 9
    x2, y = x1 + 30, py + 31.5
    return "".join([
        circle(px + 30, py + 31, 18, INK, stroke="none"),
        text(px + 30, py + 39.5, letter, 24, fill=WHITE),
        text(px + 58, py + 42, left, 30, anchor="start"),
        path(f"M {f(x1 + 6)} {f(y)} L {f(x2 - 6)} {f(y)}", sw=4.2),
        path(f"M {f(x1)} {f(y)} L {f(x1 + 9)} {f(y - 7)} L {f(x1 + 9)} {f(y + 7)} Z "
             f"M {f(x2)} {f(y)} L {f(x2 - 9)} {f(y - 7)} L {f(x2 - 9)} {f(y + 7)} Z", fill=INK, sw=2.4),
        text(x2 + 9, py + 42, right, 30, anchor="start"),
    ])


def panel_a(px, py) -> str:
    bx, by, bs = px + 112, py + 318, 1.0
    tip = brain_point(bx, by, bs, False, implant_tip())
    return "".join([
        cable(tip, (tip[0] + 12, tip[1] - 90), (px + 268, py + 150), (px + 300, py + 262), beads=(0.28, 0.52, 0.76)),
        ellipse(bx - 10, py + 413, 76, 7, INK, opacity="0.08"),
        ellipse(px + 330, py + 400, 62, 7, INK, opacity="0.08"),
        brain("ba", bx, by, bs, (PINK, PINK_SH, PINK_LN), face="happy"),
        computer(px + 330, py + 300),
        cloud(px + 88, py + 138, 62, 38, tail=((px + 102, py + 198, 8), (px + 110, py + 222, 5))),
        text(px + 88, py + 150, "Hi!", 32, family=HAND),
        sparkle(px + 410, py + 226, 8), sparkle(px + 396, py + 200, 5), sparkle(px + 210, py + 120, 6),
        sparkle(px + 30, py + 232, 6),
    ])


def panel_b(px, py) -> str:
    s, cy = 0.68, py + 340
    ax, bx = px + 86, px + 338
    tip_a = brain_point(ax, cy, s, False, implant_tip())
    tip_b = brain_point(bx, cy, s, True, implant_tip())
    dcx, dcy, dw, dh = px + 212, py + 352, 84, 66
    pa, pb = (dcx - 23, dcy - dh / 2 - 6), (dcx + 23, dcy - dh / 2 - 6)
    return "".join([
        cable(tip_a, (tip_a[0] + 8, tip_a[1] - 40), (pa[0], pa[1] - 60), pa, beads=(0.35, 0.7),
              bead_colors=(PINK, BLUE)),
        cable(tip_b, (tip_b[0] - 8, tip_b[1] - 40), (pb[0], pb[1] - 60), pb, beads=(0.35, 0.7),
              bead_colors=(BLUE, PINK)),
        ellipse(ax - 8, py + 410, 56, 6, INK, opacity="0.08"),
        ellipse(bx + 8, py + 410, 56, 6, INK, opacity="0.08"),
        bridge_box("bb", dcx, dcy, dw, dh, "q", (pa, pb)),
        text(dcx, dcy + dh / 2 + 22, "bridge", 19, fill=INK_SOFT),
        brain("b1", ax, cy, s, (PINK, PINK_SH, PINK_LN), face="puzzled", drops=True),
        brain("b2", bx, cy, s, (BLUE, BLUE_SH, BLUE_LN), mirror=True, face="puzzled", drops=True),
        cloud(px + 84, py + 158, 60, 35, tail=((px + 96, py + 222, 7), (px + 101, py + 250, 4.5))),
        orange_icon(px + 60, py + 161), lettering(px + 84, py + 170, "?", 26, PURPLE, ow=0),
        snowflake_icon(px + 108, py + 160),
        cloud(px + 340, py + 158, 60, 35, tail=((px + 328, py + 222, 7), (px + 323, py + 250, 4.5))),
        snowflake_icon(px + 316, py + 160), lettering(px + 340, py + 170, "?", 26, PURPLE, ow=0),
        orange_icon(px + 364, py + 161),
        lettering(px + 212, py + 100, "consciousness?", 24, PURPLE, family=HAND, outline=WHITE, ow=6),
        lettering(px + 212, py + 164, "self?", 30, PURPLE, family=HAND, outline=WHITE, ow=6),
        thinking_face(px + 212, py + 212, 24),
        lettering(px + 164, py + 236, "?", 40, "#c7b3ff", rot=-14),
        lettering(px + 262, py + 232, "?", 34, "#ffb3c8", rot=13),
        lettering(px + 212, py + 292, "?", 20, "#a6d8ff", rot=4),
    ])


def panel_c(px, py) -> str:
    s, cy = 0.88, py + 324
    ax, bx = px + 80, px + 344
    pa, pb = robot_port(ax, cy, s, "right"), robot_port(bx, cy, s, "left")
    dcx, dw, dh = px + 212, 92, 70
    dcy = pa[1]
    ql, qr = (dcx - dw / 2 - 6, dcy), (dcx + dw / 2 + 6, dcy)
    return "".join([
        cable(pa, (pa[0] + 12, pa[1] + 10), (ql[0] - 12, ql[1] + 10), ql, beads=(0.5,), bead_colors=(PINK,)),
        cable(qr, (qr[0] + 12, qr[1] + 10), (pb[0] - 12, pb[1] + 10), pb, beads=(0.5,), bead_colors=(BLUE,)),
        ellipse(ax, py + 404, 50, 6, INK, opacity="0.08"),
        ellipse(bx, py + 404, 50, 6, INK, opacity="0.08"),
        bridge_box("bc", dcx, dcy, dw, dh, "wave", (ql, qr)),
        text(dcx, dcy + dh / 2 + 22, "bridge", 19, fill=INK_SOFT),
        robot("ra", ax, cy, s, CORAL, "A", "right"),
        robot("rb", bx, cy, s, SKY, "B", "left"),
        cloud(px + 78, py + 124, 58, 34, tail=((px + 98, py + 172, 6), (px + 104, py + 187, 4))),
        orange_icon(px + 54, py + 127), lettering(px + 78, py + 136, "?", 26, PURPLE, ow=0),
        snowflake_icon(px + 102, py + 126),
        cloud(px + 346, py + 124, 58, 34, tail=((px + 326, py + 172, 6), (px + 320, py + 187, 4))),
        snowflake_icon(px + 322, py + 126), lettering(px + 346, py + 136, "?", 26, PURPLE, ow=0),
        orange_icon(px + 370, py + 127),
        text(dcx, py + 216, f'<tspan fill="{CORAL}">mine</tspan> or', 27, family=HAND,
             stroke=WHITE, stroke_width="6", paint_order="stroke", stroke_linejoin="round"),
        text(dcx, py + 246, f'<tspan fill="{SKY}">yours?</tspan>', 27, family=HAND,
             stroke=WHITE, stroke_width="6", paint_order="stroke", stroke_linejoin="round"),
        sparkle(dcx - 62, py + 192, 7), sparkle(dcx + 62, py + 262, 6),
    ])


def build() -> str:
    xs = [MARGIN + i * (PW + GAP) for i in range(3)]
    py = MARGIN
    body = []
    titles = (("Brain", "Machine"), ("Brain", "Brain"), ("LLM", "LLM"))
    for i, (px, draw, letter, title) in enumerate(zip(xs, (panel_a, panel_b, panel_c), "abc", titles)):
        clip = f"panel{i}"
        body.append(f'<clipPath id="{clip}"><rect x="{f(px)}" y="{f(py)}" width="{f(PW)}" height="{f(PH)}" rx="16"/></clipPath>')
        body.append(group([
            rect(px, py, PW, PH, 16, BG[i], stroke="none"),
            screentone(px + PW - 190, py, 190, 170, px + PW, py, 190),
            screentone(px, py + PH - 110, 170, 110, px, py + PH, 140),
            draw(px, py),
        ], clip_path=f"url(#{clip})"))
        body.append(rect(px, py, PW, PH, 16, "none", sw=3.8))
        body.append(header(px, py, letter, *title))
    for i in range(2):  # reading-order arrows in the gutters
        gx = xs[i] + PW + GAP / 2
        body.append(path(f"M {f(gx - 5)} {f(H / 2 - 11)} L {f(gx + 6)} {f(H / 2)} L {f(gx - 5)} {f(H / 2 + 11)} Z",
                         fill=INK, sw=2.0))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="5.5in" height="{f(5.5 * H / W)}in">'
            f'<rect width="{W}" height="{H}" fill="{WHITE}"/>' + "".join(body) + "</svg>\n")


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    svg, pdf, png = (out_dir / f"fig1_concept.{ext}" for ext in ("svg", "pdf", "png"))
    svg.write_text(build(), encoding="utf-8")
    print(f"wrote {svg}")
    if not shutil.which("rsvg-convert"):
        return
    subprocess.run(["rsvg-convert", "-f", "png", "-w", str(W * 2), "-o", str(png), str(svg)], check=True)
    print(f"wrote {png}")
    raw = pdf.with_suffix(".raw.pdf")
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(raw), str(svg)], check=True)
    if shutil.which("gs"):
        subprocess.run(["gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", "-dNoOutputFonts",
                        "-dCompatibilityLevel=1.5", f"-sOutputFile={pdf}", str(raw)], check=True)
        raw.unlink()
    else:
        raw.replace(pdf)
    print(f"wrote {pdf}")


if __name__ == "__main__":
    main()
