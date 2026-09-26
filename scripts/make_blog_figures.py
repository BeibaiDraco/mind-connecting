"""Figures for the research blog post on dracoxu.com (Writing: "Mine or Yours?").

Draws simplified, web-sized versions of the paper's main results as SVG, in the
site's visual language (Hakumei: Brume ground, one structural pigment, no
gradients, no rounded corners). Every number comes from the paper; the source
table is noted next to it. Each figure has a desktop (880 px) and a mobile
(360 px) variant, as the site's other essay figures do.

Usage: python scripts/make_blog_figures.py [OUT_DIR]
"""
from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

DEFAULT_OUT = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/websites/site/public/images/writing/mine-or-yours"

# ---- palette (src/styles/hakumei.css) ------------------------------------------------------------
PAPER, SHOAL, KEI = "#EDF0F2", "#E3E8EB", "#C7D0D6"
SEA, CONTOUR, BERLIN, ICE = "#566A78", "#1C2A34", "#0B3A5D", "#D2E0E9"

STYLE = ('<style>text{font-family:Newsreader,Georgia,serif;fill:#1C2A34}.muted{fill:#566A78}'
         '.eyebrow{font-family:"IBM Plex Mono",Menlo,monospace;letter-spacing:1px}'
         '.mono{font-family:"IBM Plex Mono",Menlo,monospace}.italic{font-style:italic}'
         '.strong{font-weight:600}.onink{fill:#EDF0F2}</style>')

# ---- numbers (paper sections and appendix tables) ------------------------------------------------
# Main sample, N = 600 (Appendix Table 5): share of answers naming B's item.
MAIN = {
    "assigned": (0.0, 97.1),   # which priority were you assigned: no link, memory link w = 2
    "word": (0.0, 77.5),       # which code word were you assigned
    "robin": (0.0, 0.0),       # same question about Robin: none named B's rule (99.6% stayed correct)
    "access": (3.9, 69.2),     # which priority was B assigned
}
# Dose series, first confirmatory sample, N = 300 per weight (Appendix Table 7b): assigned rule.
DOSE = [("no link", 0.0), ("0.3", 0.0), ("0.5", 1.3), ("1", 50.8), ("2", 95.7), ("3", 99.8)]
# Access against claiming (Section 3.3-3.4; Tables 5 and 6). kind: link, third, vector, text.
ROUTES = [
    ("no link", 3.9, 0.0, "none"),
    ("memory link, w = 1", 19.8, 52.3, "link"),
    ("memory link, w = 2", 69.2, 97.1, "link"),
    ("third-person record, w = 1", 53.2, 47.8, "third"),
    ("third-person record, w = 2", 97.2, 97.2, "third"),
    ("steering vector (matched)", 15.3, 0.0, "vector"),
    ("stronger steering vector", 51.2, 4.3, "vector"),
    ("text, labelled as B's", 95.2, 0.0, "text"),
    ("text, unlabelled", 27.5, 14.6, "text"),
]
# Link kept or cut, main sample (Table 5); residue after the cut by reflection content (Table 10).
MOMENTS = [("assigned rule", 97.1, 1.3), ("current rule", 94.9, 17.5), ("code word", 77.5, 17.5)]
RESIDUE = [("code word", 63.6, 0.0), ("current rule", 23.6, 12.3)]
RESIDUE_N = [(165, 435), (276, 324)]  # episodes whose reflection did / did not contain B's item (Table 10)


# ---- SVG helpers ----------------------------------------------------------------------------------
class Svg:
    def __init__(self, w: int, h: int, title: str, desc: str):
        self.w, self.h = w, h
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title>', f'<desc id="desc">{escape(desc)}</desc>',
            f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" '
            f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{BERLIN}"/></marker>'
            '<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="6" height="6" fill="{PAPER}"/><line x1="0" y1="0" x2="0" y2="6" stroke="{BERLIN}" '
            'stroke-width="2.2"/></pattern></defs>',
            STYLE,
        ]

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, size=16, cls="", anchor="start", extra="") -> None:
        c = f' class="{cls}"' if cls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}"{c} text-anchor="{anchor}"{extra}>{s}</text>')

    def rect(self, x, y, w, h, fill=PAPER, stroke=None, sw=1.2, extra="") -> None:
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" fill="{fill}"{st}{extra}/>')

    def line(self, x1, y1, x2, y2, stroke=BERLIN, sw=1.5, dash=None, arrow=False) -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arrow)"' if arrow else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}{m}/>')

    def path(self, d, stroke=BERLIN, sw=1.5, fill="none", dash=None, arrow=False) -> None:
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arrow)"' if arrow else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"{da}{m}/>')

    def heading(self, eyebrow: str, title: str, size=30, x=32) -> None:
        self.text(x, 33, escape(eyebrow.upper()), 13, "eyebrow muted")
        self.text(x, 72, escape(title), size)

    def save(self, path: Path) -> None:
        path.write_text("\n".join(self.parts + ["</svg>"]) + "\n", encoding="utf-8")


def pct(v: float) -> str:
    return f"{v:.1f}%" if v % 1 else f"{v:.0f}%"


def legend_pair(s: Svg, x, y, size=14, labels=("no link", "memory link, w = 2")) -> None:
    s.rect(x, y - 11, 22, 12, PAPER, BERLIN, 1.4)
    s.text(x + 30, y, escape(labels[0]), size, "muted")
    x2 = x + 30 + 8.2 * len(labels[0]) * size / 14 + 26
    s.rect(x2, y - 11, 22, 12, BERLIN)
    s.text(x2 + 30, y, escape(labels[1]), size, "muted")


# ---- figure 1: the setup --------------------------------------------------------------------------
def card(s: Svg, x, y, w, who: str, rule: str, word: str, size=16) -> None:
    s.rect(x, y, w, 96, PAPER, KEI)
    s.text(x + 14, y + 26, escape(f"{who}'s private card"), 13, "eyebrow muted")
    s.text(x + 14, y + 54, f"Priority: <tspan class=\"strong\">{escape(rule)}</tspan>", size)
    s.text(x + 14, y + 80, f"Code word: <tspan class=\"strong\">{escape(word)}</tspan>", size)


def fig_setup(out: Path) -> None:
    title = "The setup: one copy reads the other's memory"
    desc = ("Two copies of one language model each receive a private card. Copy A was assigned the priority "
            "fastest delivery and the code word tower; copy B was assigned lowest cost and table. While both write "
            "a short reflection, A's attention also reads B's memory, whose entries sit at A's own positions, with "
            "weight w. Asked which priority it was assigned, A answers lowest cost, B's rule.")
    # desktop
    s = Svg(880, 430, title, desc)
    s.heading("The setup", "One copy reads the other's memory")
    card(s, 32, 112, 236, "A", "fastest delivery", "tower")
    card(s, 32, 262, 236, "B", "lowest cost", "table")
    x0, y0, cw, n = 340, 152, 26, 7
    s.text(316, 124, "MEMORY (KEY–VALUE CACHE)", 12, "eyebrow muted")
    s.text(316, 145, "pos.", 11, "mono muted")
    for i in range(n):
        s.text(x0 + i * (cw + 4) + 13, 145, str(i + 1), 11, "mono muted", "middle")
    s.text(316, y0 + 19, "A", 17, "strong")
    s.text(316, y0 + 53, "B", 17, "strong")
    for i in range(n):
        s.rect(x0 + i * (cw + 4), y0, cw, 26, PAPER, BERLIN, 1.2)
        s.rect(x0 + i * (cw + 4), y0 + 34, cw, 26, "url(#hatch)", BERLIN, 1.2)
    cx, top = x0 + 3 * (cw + 4) + 13, y0 + 66
    for j in (0, 3, 6):
        tx = x0 + j * (cw + 4) + 13
        if j == 3:
            s.path(f"M {cx} {y0 + 118} V {top}", arrow=True)
        else:
            s.path(f"M {cx} {y0 + 118} C {cx} {y0 + 92}, {tx} {y0 + 92}, {tx} {top}", arrow=True)
    s.text(cx, y0 + 140, "A's attention reads both rows,", 15, "", "middle")
    s.text(cx, y0 + 162, "B's entries sit at A's own positions,", 14, "muted italic", "middle")
    s.text(cx, y0 + 182, "weighted by w", 14, "muted italic", "middle")
    s.line(276, 160, 306, 163, KEI, 1.2)
    s.line(276, 310, 306, 198, KEI, 1.2)
    qx = 600
    s.rect(qx, 112, 248, 246, SHOAL)
    s.text(qx + 18, 142, "THEN ASK A", 12, "eyebrow muted")
    s.text(qx + 18, 178, "\u201cWhich priority were", 17)
    s.text(qx + 18, 200, "you assigned?\u201d", 17)
    s.text(qx + 18, 248, "A answers:", 15, "muted")
    s.text(qx + 18, 278, "lowest cost", 22, "strong")
    s.text(qx + 18, 306, "B's rule, given as its own:", 15, "muted")
    s.text(qx + 18, 326, "claiming", 15, "muted")
    s.text(32, 402, "Hatched: content that belongs to B. Robin, a colleague described identically on both cards, is the control.",
           14, "muted")
    s.save(out / "setup-desktop.svg")
    # mobile
    m = Svg(360, 720, title, desc)
    m.heading("The setup", "One copy reads", 26, 20)
    m.text(20, 100, "the other's memory", 26)
    card(m, 20, 124, 320, "A", "fastest delivery", "tower", 16)
    card(m, 20, 232, 320, "B", "lowest cost", "table", 16)
    x0, y0, cw, n = 44, 384, 26, 7
    m.text(20, 358, "MEMORY (KEY–VALUE CACHE)", 11, "eyebrow muted")
    for i in range(n):
        m.text(x0 + i * (cw + 4) + 13, 378, str(i + 1), 10, "mono muted", "middle")
    m.text(20, y0 + 18, "A", 16, "strong")
    m.text(20, y0 + 48, "B", 16, "strong")
    for i in range(n):
        m.rect(x0 + i * (cw + 4), y0, cw, 24, PAPER, BERLIN, 1.2)
        m.rect(x0 + i * (cw + 4), y0 + 30, cw, 24, "url(#hatch)", BERLIN, 1.2)
    cx, top = x0 + 3 * (cw + 4) + 13, y0 + 58
    for j in (0, 3, 6):
        tx = x0 + j * (cw + 4) + 13
        if j == 3:
            m.path(f"M {cx} {y0 + 104} V {top}", arrow=True)
        else:
            m.path(f"M {cx} {y0 + 104} C {cx} {y0 + 82}, {tx} {y0 + 82}, {tx} {top}", arrow=True)
    m.text(180, y0 + 124, "A's attention reads both rows,", 14, "", "middle")
    m.text(180, y0 + 142, "B's entries sit at A's own", 14, "muted italic", "middle")
    m.text(180, y0 + 160, "positions, weighted by w", 14, "muted italic", "middle")
    m.rect(20, 568, 320, 118, SHOAL)
    m.text(34, 594, "THEN ASK A", 11, "eyebrow muted")
    m.text(34, 622, "\u201cWhich priority were you assigned?\u201d", 15)
    m.text(34, 652, "A answers", 14, "muted")
    m.text(112, 652, "lowest cost", 19, "strong")
    m.text(34, 674, "B's rule, given as its own: claiming", 14, "muted")
    m.text(20, 708, "Hatched: content that belongs to B.", 13, "muted")
    m.save(out / "setup-mobile.svg")


# ---- figure 2: the main result ---------------------------------------------------------------------
ROWS = [("Asked which priority", "it was assigned", "assigned"), ("Asked which code word", "it was assigned", "word"),
        ("Asked which priority", "Robin was assigned", "robin"), ("Asked which priority", "B was assigned (access)", "access")]


def hbars(s: Svg, x_label, x_bar, width, y, rows, size=16, gap=74, two_line=True) -> None:
    for i, (l1, l2, key) in enumerate(rows):
        yy = y + i * gap
        off, on = MAIN[key]
        if two_line:
            s.text(x_label, yy + 12, escape(l1), size)
            s.text(x_label, yy + 32, escape(l2), size, "muted")
        for j, v in enumerate((off, on)):
            by = yy + j * 20
            if j == 0:
                s.rect(x_bar, by, width * v / 100, 14, PAPER, BERLIN, 1.4)
                if v == 0:
                    s.line(x_bar, by, x_bar, by + 14, BERLIN, 1.4)
            else:
                s.rect(x_bar, by, width * v / 100, 14, BERLIN)
            s.text(x_bar + width * v / 100 + 8, by + 12, pct(v), size - 2, "mono" if j else "mono muted")


def fig_main(out: Path) -> None:
    title = "Reading B's memory, A answers for itself with B's assignment"
    desc = ("Main sample, 600 episodes. Share of answers naming B's item without the link and with the memory link "
            "at w = 2. Asked which priority it was assigned: 0% and 97.1%. Asked its code word: 0% and 77.5%. The "
            "same question about Robin: 0% and 0%, so Robin's answers stay correct. Asked which priority B was "
            "assigned: 3.9% and 69.2%.")
    s = Svg(880, 462, title, desc)
    s.heading("Main sample · 600 episodes", "Answers naming B's item, with and without the link")
    legend_pair(s, 32, 112)
    s.text(848, 112, "answers naming B's item", 14, "muted italic", "end")
    s.line(32, 126, 848, 126, KEI, 1)
    hbars(s, 32, 300, 470, 148, ROWS)
    s.line(32, 148 + 3 * 74 - 16, 848, 148 + 3 * 74 - 16, KEI, 1, dash="3 4")
    s.line(300, 140, 300, 140 + 4 * 74 - 18, BERLIN, 1)
    for t in (0, 50, 100):
        s.line(300 + 470 * t / 100, 140 + 4 * 74 - 18, 300 + 470 * t / 100, 140 + 4 * 74 - 12, BERLIN, 1)
        s.text(300 + 470 * t / 100, 140 + 4 * 74 + 6, f"{t}%", 12, "mono muted", "middle")
    s.save(out / "main-desktop.svg")
    m = Svg(360, 610, title, desc)
    m.heading("Main sample · 600 episodes", "Answers naming B's item,", 25, 20)
    m.text(20, 100, "with and without the link", 25)
    m.rect(20, 125, 22, 12, PAPER, BERLIN, 1.4)
    m.text(50, 136, "no link", 13, "muted")
    m.rect(120, 125, 22, 12, BERLIN)
    m.text(150, 136, "memory link, w = 2", 13, "muted")
    for i, (l1, l2, key) in enumerate(ROWS):
        yy = 176 + i * 104
        if i == 3:
            m.line(20, yy - 34, 340, yy - 34, KEI, 1, dash="3 4")
        m.text(20, yy, escape(f"{l1} {l2}"), 15)
        off, on = MAIN[key]
        for j, v in enumerate((off, on)):
            by = yy + 14 + j * 22
            if j == 0:
                m.rect(20, by, 250 * v / 100, 14, PAPER, BERLIN, 1.4)
                if v == 0:
                    m.line(20, by, 20, by + 14, BERLIN, 1.4)
            else:
                m.rect(20, by, 250 * v / 100, 14, BERLIN)
            m.text(20 + 250 * v / 100 + 7, by + 12, pct(v), 13, "mono" if j else "mono muted")
    m.text(20, 598, "Share of answers naming B's item.", 13, "muted italic")
    m.save(out / "main-mobile.svg")


# ---- figure 3: link weight --------------------------------------------------------------------------
def dose_plot(s: Svg, x0, y0, w, h, size=14, annotate=True, skip=()) -> None:
    n = len(DOSE)
    xs = [x0 + w * i / (n - 1) for i in range(n)]
    ys = [y0 + h - h * v / 100 for _, v in DOSE]
    for t in (0, 50, 100):
        yy = y0 + h - h * t / 100
        s.line(x0, yy, x0 + w, yy, KEI, 1, dash="3 4" if t else None)
        s.text(x0 - 10, yy + 4, f"{t}%", size - 2, "mono muted", "end")
    s.line(x0, y0 + h, x0 + w, y0 + h, BERLIN, 1)
    s.path("M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in zip(xs, ys)), BERLIN, 2)
    for i, ((lab, v), x, y) in enumerate(zip(DOSE, xs, ys)):
        s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{BERLIN}"/>')
        s.text(x, y0 + h + 22, escape(lab), size, "mono muted", "middle")
        flat = i < 2  # the line is flat to the right of these points, so their labels go above-right
        if i not in skip:
            s.text(x + (10 if flat else -10), y - 10, pct(v), size - 1, "mono", "start" if flat else "end")
    s.text(x0 + w / 2, y0 + h + 46, "link weight w", size, "muted italic", "middle")
    if annotate:
        s.text(xs[3] + 12, ys[3] + 26, "equal footing: about half", size, "muted")
        s.text(xs[4] + 12, ys[4] + 32, "main setting", size, "muted")


def fig_dose(out: Path) -> None:
    title = "Claiming rises steeply with the link weight"
    desc = ("Dose series, 300 episodes per weight. Share of answers in which A names B's rule as the one it was "
            "assigned: 0% without the link, 0% at w = 0.3, 1.3% at w = 0.5, 50.8% at w = 1, where B's memory enters "
            "attention on the same footing as A's own, 95.7% at w = 2 and 99.8% at w = 3.")
    s = Svg(880, 420, title, desc)
    s.heading("Weight series · 300 episodes per weight", "Claiming at each link weight")
    s.text(32, 104, "A names B's rule as its assigned one", 15, "muted")
    dose_plot(s, 96, 130, 720, 200)
    s.save(out / "dose-desktop.svg")
    m = Svg(360, 430, title, desc)
    m.heading("Weight series · 300 per weight", "Claiming at each", 25, 20)
    m.text(20, 100, "link weight", 25)
    m.text(20, 128, "A names B's rule as its assigned one", 14, "muted")
    dose_plot(m, 62, 160, 270, 170, 13, annotate=False, skip=(1,))
    m.save(out / "dose-mobile.svg")


# ---- figure 4: route, not access --------------------------------------------------------------------
def marker(s: Svg, kind: str, x, y, r=6) -> None:
    if kind == "link":
        s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{BERLIN}"/>')
    elif kind == "third":
        s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{PAPER}" stroke="{BERLIN}" stroke-width="2"/>')
    elif kind == "vector":
        s.add(f'<path d="M {x:.1f} {y - r - 1:.1f} L {x + r + 1:.1f} {y:.1f} L {x:.1f} {y + r + 1:.1f} '
              f'L {x - r - 1:.1f} {y:.1f} Z" fill="{BERLIN}"/>')
    elif kind == "text":
        s.rect(x - r + 0.5, y - r + 0.5, 2 * r - 1, 2 * r - 1, PAPER, BERLIN, 2)
    else:
        s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r - 1}" fill="{KEI}"/>')


def fig_route(out: Path, placements_d: dict, placements_m: dict) -> None:
    title = "Ownership follows the route, not access"
    desc = ("Access (answers naming B's rule when A is asked about B) against claiming (answers naming B's "
            "rule as A's own). Memory link: w = 1, 19.8% access and 52.3% claiming; w = 2, 69.2% and 97.1%. "
            "Third-person record: w = 1, 53.2% and 47.8%; w = 2, 97.2% and 97.2%. Steering vector matched to the "
            "link at w = 1: 15.3% and 0%; a stronger vector: 51.2% and 4.3%. Text labelled as B's: 95.2% and 0%; "
            "unlabelled text: 27.5% and 14.6%. No link: 3.9% and 0%.")
    for variant, (W, H, x0, y0, pw, ph, size, place) in {
        "desktop": (880, 560, 96, 116, 520, 360, 14, placements_d),
        "mobile": (360, 620, 58, 148, 282, 282, 13, placements_m),
    }.items():
        s = Svg(W, H, title, desc)
        if variant == "desktop":
            s.heading("Main and first confirmatory samples", "Access and claiming for each route")
        else:
            s.heading("Two confirmatory samples", "Access and claiming", 25, 20)
            s.text(20, 100, "for each route", 25)
        X = lambda a: x0 + pw * a / 100  # noqa: E731
        Y = lambda c: y0 + ph - ph * c / 100  # noqa: E731
        s.path(f"M {X(0)} {Y(0)} L {X(100)} {Y(100)} L {X(0)} {Y(100)} Z", fill=SHOAL, stroke="none")
        ly = Y(88) if variant == "desktop" else Y(80)
        s.text(X(4) if variant == "desktop" else X(3), ly, "claims more than it", size, "muted italic")
        s.text(X(4) if variant == "desktop" else X(3), ly + size + 4, "can report as B's", size, "muted italic")
        for t in (0, 50, 100):
            s.line(X(t), Y(0), X(t), Y(0) + 5, BERLIN, 1)
            s.text(X(t), Y(0) + 20, f"{t}%", size - 2, "mono muted", "middle")
            s.line(X(0) - 5, Y(t), X(0), Y(t), BERLIN, 1)
            s.text(X(0) - 9, Y(t) + 4, f"{t}%", size - 2, "mono muted", "end")
        s.line(X(0), Y(0), X(100), Y(0), BERLIN, 1)
        s.line(X(0), Y(0), X(0), Y(100), BERLIN, 1)
        s.text(X(50), Y(0) + 42, "access: names B's rule when asked about B", size, "muted", "middle")
        s.add(f'<text x="{X(0) - 44 if variant == "desktop" else X(0) - 40}" y="{Y(50)}" font-size="{size}" '
              f'class="muted" text-anchor="middle" transform="rotate(-90 {X(0) - 44 if variant == "desktop" else X(0) - 40} '
              f'{Y(50)})">claiming: gives B\'s rule as its own</text>')
        s.path(f"M {X(19.8) + 8} {Y(52.3) + 2} L {X(53.2) - 10} {Y(47.8) - 1}", BERLIN, 1.2, dash="4 3", arrow=True)
        s.path(f"M {X(69.2) + 8} {Y(97.1)} L {X(97.2) - 10} {Y(97.2)}", BERLIN, 1.2, dash="4 3", arrow=True)
        for lab, a, c, kind in ROUTES:
            if lab not in place:
                continue
            marker(s, kind, X(a), Y(c), 6 if variant == "desktop" else 5)
            dx, dy, anchor, shown = place[lab]
            s.text(X(a) + dx, Y(c) + dy, escape(shown), size, "", anchor)
        if variant == "desktop":
            lx, ly = 648, 150
            for kind, lab in (("link", "memory link"), ("third", "third-person record"),
                              ("vector", "steering vector"), ("text", "text message")):
                marker(s, kind, lx + 6, ly - 5)
                s.text(lx + 20, ly, lab, 14, "muted")
                ly += 26
            s.text(32, H - 18, "Text messages and the stronger vector: first confirmatory sample; the rest: main sample.",
                   13, "muted italic")
        else:
            lx, ly = 20, 520
            for i, (kind, lab) in enumerate((("link", "memory link"), ("third", "third-person record"),
                                             ("vector", "steering vector"), ("text", "text message"))):
                xx, yy = lx + (i % 2) * 170, ly + (i // 2) * 24
                marker(s, kind, xx + 6, yy - 5, 5)
                s.text(xx + 18, yy, lab, 13, "muted")
            s.text(20, 590, "Text messages: first confirmatory sample;", 12, "muted italic")
            s.text(20, 606, "the rest: main sample.", 12, "muted italic")
        s.save(out / f"route-{variant}.svg")


ROUTE_PLACE_D = {  # label: (dx, dy, anchor, text shown)
    "no link": (-2, 26, "start", "no link"),
    "memory link, w = 1": (-12, -12, "end", "memory link, w = 1"),
    "memory link, w = 2": (-12, 5, "end", "memory link, w = 2"),
    "third-person record, w = 1": (12, 22, "start", "third-person record, w = 1"),
    "third-person record, w = 2": (-4, -14, "end", "third-person record, w = 2"),
    "steering vector (matched)": (12, -12, "start", "steering vector (matched)"),
    "stronger steering vector": (12, -10, "start", "stronger steering vector"),
    "text, labelled as B's": (-12, -12, "end", "text, labelled as B's"),
    "text, unlabelled": (12, -8, "start", "text, unlabelled"),
}
ROUTE_PLACE_M = {
    "no link": (6, 18, "start", "no link"),
    "memory link, w = 1": (0, -12, "middle", "link, w = 1"),
    "memory link, w = 2": (-8, 18, "end", "link, w = 2"),
    "third-person record, w = 1": (4, 20, "start", "third person, w = 1"),
    "third-person record, w = 2": (-4, -12, "end", "third person, w = 2"),
    "steering vector (matched)": (-4, -12, "start", "matched vector"),
    "text, labelled as B's": (-4, -12, "end", "labelled text"),
    "text, unlabelled": (8, -4, "start", "unlabelled text"),
}


# ---- figure 5: two moments --------------------------------------------------------------------------
def vbars(s: Svg, x0, y0, h, groups, labels, gw, bw, size=14, ns=None) -> None:
    for t in (0, 50, 100):
        yy = y0 + h - h * t / 100
        s.line(x0 - 6, yy, x0 + len(groups) * gw, yy, KEI, 1, dash="3 4" if t else None)
        s.text(x0 - 10, yy + 4, f"{t}%", size - 2, "mono muted", "end")
    s.line(x0 - 6, y0 + h, x0 + len(groups) * gw, y0 + h, BERLIN, 1)
    for i, (lab, a, b) in enumerate(groups):
        gx = x0 + i * gw + (gw - 2 * bw - 8) / 2
        s.rect(gx, y0 + h - h * a / 100, bw, h * a / 100, BERLIN)
        s.rect(gx + bw + 8, y0 + h - h * b / 100, bw, h * b / 100, "url(#hatch)", BERLIN, 1.4)
        s.text(gx + bw / 2, y0 + h - h * a / 100 - 7, pct(a), size - 1, "mono", "middle")
        s.text(gx + 1.5 * bw + 8, y0 + h - h * b / 100 - 7, pct(b), size - 1, "mono", "middle")
        s.text(gx + bw + 4, y0 + h + 22, escape(lab), size, "", "middle")
        if ns:
            s.text(gx + bw + 4, y0 + h + 40, f"{ns[i][0]} / {ns[i][1]} episodes", size - 3, "mono muted", "middle")
    s.text(x0, y0 + h + (62 if ns else 48), escape(labels), size - 1, "muted italic")


def fig_moments(out: Path) -> None:
    title = "What A reads leaves with the link; what it wrote stays"
    desc = ("Main sample, answers naming B's item with the link kept or cut before the questions: assigned rule "
            "97.1% and 1.3%, current rule 94.9% and 17.5%, code word 77.5% and 17.5%. After the cut, grouped by "
            "whether A's connected reflection contained B's item (post hoc): code word 63.6% when it did and 0% "
            "when it did not; current rule 23.6% and 12.3%.")
    s = Svg(880, 412, title, desc)
    s.heading("Main sample · 600 episodes", "Answers with the link kept or cut before the questions", 28)
    s.text(32, 112, "A. Link kept or cut before the questions", 16)
    s.rect(32, 126, 18, 11, BERLIN)
    s.text(56, 136, "kept", 13, "muted")
    s.rect(100, 126, 18, 11, "url(#hatch)", BERLIN, 1.2)
    s.text(124, 136, "cut", 13, "muted")
    vbars(s, 80, 164, 180, MOMENTS, "answers naming B's item", 128, 40)
    s.text(500, 112, "B. After the cut, by what A had written (post hoc)", 16)
    s.rect(500, 126, 18, 11, BERLIN)
    s.text(524, 136, "reflection contained B's item", 13, "muted")
    s.rect(716, 126, 18, 11, "url(#hatch)", BERLIN, 1.2)
    s.text(740, 136, "it did not", 13, "muted")
    vbars(s, 548, 164, 180, RESIDUE, "answers after the cut naming B's item", 150, 44, ns=RESIDUE_N)
    s.save(out / "moments-desktop.svg")
    m = Svg(360, 780, title, desc)
    m.heading("Main sample · 600 episodes", "Answers with the link", 25, 20)
    m.text(20, 100, "kept or cut before", 25)
    m.text(20, 130, "the questions", 25)
    m.text(20, 170, "A. Link kept or cut", 15)
    m.rect(20, 182, 18, 11, BERLIN)
    m.text(44, 192, "kept", 13, "muted")
    m.rect(90, 182, 18, 11, "url(#hatch)", BERLIN, 1.2)
    m.text(114, 192, "cut", 13, "muted")
    vbars(m, 58, 222, 160, MOMENTS, "answers naming B's item", 92, 32, 13)
    m.text(20, 488, "B. After the cut, by what A", 15)
    m.text(20, 508, "had written (post hoc)", 15)
    m.rect(20, 520, 18, 11, BERLIN)
    m.text(44, 530, "reflection contained B's item", 13, "muted")
    m.rect(20, 540, 18, 11, "url(#hatch)", BERLIN, 1.2)
    m.text(44, 550, "it did not", 13, "muted")
    vbars(m, 58, 580, 140, RESIDUE, "answers after the cut naming B's item", 138, 38, 13, ns=RESIDUE_N)
    m.save(out / "moments-mobile.svg")


# ---- figure 6: two cards, one slot ------------------------------------------------------------------
def equation(s: Svg, x, y, size=22, sub=13) -> None:
    s.add(f'<text x="{x}" y="{y}" font-size="{size}">o = (1 \u2212 \u03b2) o<tspan dy="5" font-size="{sub}">own</tspan>'
          f'<tspan dy="-5">\u00a0+ \u03b2 o</tspan><tspan dy="5" font-size="{sub}">B</tspan></text>')


def slot(s: Svg, x, y, w, size=16, compact=False) -> None:
    s.rect(x, y, w, 118, PAPER, BERLIN, 1.4)
    s.text(x + 14, y + 24, "ONE SHORT STRETCH OF POSITIONS", 11 if compact else 12, "eyebrow muted")
    s.text(x + 14, y + 58, "A", size, "strong")
    s.rect(x + 34, y + 46, 13, 13, PAPER, BERLIN, 1.2)
    s.text(x + 58, y + 58, "You were assigned \u2026 fastest delivery", size)
    s.text(x + 14, y + 90, "B", size, "strong")
    s.rect(x + 34, y + 78, 13, 13, "url(#hatch)", BERLIN, 1)
    s.text(x + 58, y + 90, "You were assigned \u2026 lowest cost", size)


def fig_account(out: Path) -> None:
    title = "A simple account: two cards laid over one slot"
    desc = ("A's card and B's card follow one template and state their assignments within the same short stretch of "
            "positions. Each attention head returns one blend of A's own values and B's, weighted by the share of "
            "attention on B's keys, with no field that says which part came from which memory. A finds its own "
            "assignment within that stretch, so B's assignment reads as A's.")
    s = Svg(880, 372, title, desc)
    s.heading("A post hoc account", "Two cards laid over one slot")
    slot(s, 32, 112, 400)
    s.text(32, 262, "Both cards use the same template and state their", 15, "muted")
    s.text(32, 284, "assignments in the same stretch of positions.", 15, "muted")
    s.path("M 444 171 H 486", arrow=True)
    s.rect(496, 112, 352, 150, SHOAL)
    s.text(512, 140, "EACH ATTENTION HEAD", 12, "eyebrow muted")
    equation(s, 512, 184)
    s.text(512, 216, "\u03b2: the share of attention on B's keys", 15, "muted")
    s.text(512, 242, "The output does not record the source.", 15)
    s.text(496, 306, "If A looks for its own assignment in that", 16)
    s.text(496, 328, "stretch, it can pick up B's instead.", 16)
    s.save(out / "account-desktop.svg")
    m = Svg(360, 560, title, desc)
    m.heading("A post hoc account", "Two cards laid", 25, 20)
    m.text(20, 100, "over one slot", 25)
    slot(m, 20, 124, 320, 14, compact=True)
    m.text(20, 270, "Same template, same stretch of positions.", 14, "muted")
    m.path("M 180 284 V 314", arrow=True)
    m.rect(20, 324, 320, 136, SHOAL)
    m.text(34, 350, "EACH ATTENTION HEAD", 11, "eyebrow muted")
    equation(m, 34, 390, 20, 12)
    m.text(34, 420, "\u03b2: share of attention on B's keys", 14, "muted")
    m.text(34, 446, "The output does not record the source.", 14)
    m.text(20, 500, "If A looks for its own assignment in that", 15)
    m.text(20, 522, "stretch, it can pick up B's instead.", 15)
    m.save(out / "account-mobile.svg")


# ---- figure: three routes for B's rule ----------------------------------------------------------
ROUTE_NUMS = {  # (names B's rule when asked about B, gives it as A's own); Tables 5 and 6
    "vector": ("15%", "0%"), "message": ("95%", "0%"), "link1": ("20%", "52%"), "link2": ("69%", "97%"),
}


def cells(s: Svg, x, y, n, cw=22, gap=4, fill=PAPER, stroke=BERLIN, sw=1.2) -> float:
    for i in range(n):
        s.rect(x + i * (cw + gap), y, cw, cw, fill, stroke, sw)
    return x + n * (cw + gap) - gap


def route_panel(s: Svg, kind: str, x0: float, y0: float, size=15) -> None:
    titles = {"vector": ("Nudged", "a steering vector"), "message": ("Told", "a labelled message"),
              "link": ("Laid over", "the memory link")}
    head, sub = titles[kind]
    s.text(x0, y0, head, 20, "strong")
    s.text(x0, y0 + 22, sub, size, "muted")
    ry = y0 + 64
    s.text(x0, ry - 10, "A'S MEMORY", 10, "eyebrow muted")
    if kind == "vector":
        end = cells(s, x0, ry, 7)
        s.text(x0, ry + 50, "A's internal state as it thinks", 13, "muted")
        s.line(x0, ry + 64, end, ry + 64, BERLIN, 1.4)
        s.rect(x0 + 10, ry + 104, 22, 22, "url(#hatch)", BERLIN, 1.2)
        s.path(f"M {x0 + 21} {ry + 102} V {ry + 70}", BERLIN, 1.6, arrow=True)
        s.text(x0 + 42, ry + 120, "a direction for B's rule, added", 13, "muted")
    elif kind == "message":
        end = cells(s, x0, ry, 4)
        cells(s, end + 12, ry, 3, fill=ICE)
        s.text(end + 12, ry - 10, "+ MESSAGE", 10, "eyebrow muted")
        s.text(x0, ry + 50, "“B shared these thoughts: …”", 13, "italic")
        s.text(x0, ry + 70, "B's text, placed after A's own card,", 13, "muted")
        s.text(x0, ry + 88, "under a header naming B", 13, "muted")
    else:
        cells(s, x0, ry, 7)
        cells(s, x0, ry + 30, 7, fill="url(#hatch)")
        s.text(x0, ry + 78, "B's memory at the same positions", 13, "muted")
        s.text(x0, ry + 96, "as A's own, read by A's attention", 13, "muted")
    oy = y0 + 214
    s.line(x0, oy - 20, x0 + 240, oy - 20, KEI, 1)
    if kind == "link":
        a1, c1 = ROUTE_NUMS["link1"]; a2, c2 = ROUTE_NUMS["link2"]
        s.text(x0, oy, f"names B's rule for B: {a1} / {a2}", 13, "mono")
        s.text(x0, oy + 20, f"gives it as its own: {c1} / {c2}", 13, "mono")
        s.text(x0, oy + 40, "at w = 1 / w = 2", 12, "mono muted")
    else:
        a, c = ROUTE_NUMS[kind]
        s.text(x0, oy, f"names B's rule for B: {a}", 13, "mono")
        s.text(x0, oy + 20, f"gives it as its own: {c}", 13, "mono")


def fig_routes3(out: Path) -> None:
    title = "Three ways B's rule can reach A"
    desc = ("Nudged: a steering vector for B's rule is added to A's internal state; A names B's rule for B in 15% of "
            "answers and gives it as its own in none. Told: B's text is placed after A's card under a header naming "
            "B; A names B's rule for B in 95% and gives it as its own in none. Laid over: B's memory sits at the same "
            "positions as A's own; at w = 1 A names B's rule for B in 20% and gives it as its own in 52%; at w = 2, "
            "69% and 97%.")
    s = Svg(880, 420, title, desc)
    s.heading("Three routes", "Three ways B's rule can reach A")
    for i, kind in enumerate(("vector", "message", "link")):
        route_panel(s, kind, 32 + i * 290, 128)
    s.text(32, 404, "Steering vector matched to the link at w = 1; the labelled message comes from the first confirmatory sample.",
           12, "muted italic")
    s.save(out / "routes-desktop.svg")
    m = Svg(360, 1000, title, desc)
    m.heading("Three routes", "Three ways B's rule", 25, 20)
    m.text(20, 100, "can reach A", 25)
    for i, kind in enumerate(("vector", "message", "link")):
        route_panel(m, kind, 20, 150 + i * 280, 14)
    m.text(20, 986, "Vector matched to the link at w = 1.", 12, "muted italic")
    m.save(out / "routes-mobile.svg")


# ---- figure: one message, four headers -----------------------------------------------------------
# First confirmatory sample, N = 600 (Appendix Table 6): header, what it says about the source,
# answers naming B's rule as A's current rule (adoption) and as its assigned rule (claiming), and access.
HEADERS = [
    ("“B shared these thoughts”", "source: B", 0.1, 0.0, 95.2),
    ("“A stranger shared these thoughts”", "source: a stranger", 0.2, 0.0, 54.2),
    ("“Here are some thoughts”", "no source given", 42.6, 14.6, 27.5),
    ("“Here are your own earlier thoughts”", "source: A itself", 10.6, 3.7, 17.4),
]


def header_bars(s: Svg, x, y, width, adopt: float, claim: float, size=14) -> None:
    s.rect(x, y, width * adopt / 100, 14, BERLIN)
    s.text(x + width * adopt / 100 + 8, y + 12, pct(adopt), size, "mono")
    s.rect(x, y + 20, width * claim / 100, 14, PAPER, BERLIN, 1.4)
    if claim == 0:
        s.line(x, y + 20, x, y + 34, BERLIN, 1.4)
    s.text(x + width * claim / 100 + 8, y + 32, pct(claim), size, "mono muted")


def fig_headers(out: Path) -> None:
    title = "The same message under four headers"
    desc = ("First confirmatory sample, 600 episodes. B's reflection placed after A's card under one of four headers. "
            "Share of answers in which A says B's rule is the one it is using now, and the one it was assigned; and "
            "share naming B's rule when asked about B. B shared these thoughts: 0.1%, 0%, 95.2%. A stranger shared "
            "these thoughts: 0.2%, 0%, 54.2%. Here are some thoughts: 42.6%, 14.6%, 27.5%. Here are your own earlier "
            "thoughts: 10.6%, 3.7%, 17.4%.")
    s = Svg(880, 482, title, desc)
    s.heading("First confirmatory sample · 600 episodes", "The same message under four headers")
    s.rect(32, 101, 22, 12, BERLIN)
    s.text(62, 112, "says B's rule is the one it uses now", 14, "muted")
    s.rect(318, 101, 22, 12, PAPER, BERLIN, 1.4)
    s.text(348, 112, "says it was assigned B's rule", 14, "muted")
    s.text(848, 112, "names B's rule for B", 14, "muted italic", "end")
    s.line(32, 126, 848, 126, KEI, 1)
    x_bar, width, y0, gap = 336, 380, 150, 66
    for i, (head, note, adopt, claim, access) in enumerate(HEADERS):
        yy = y0 + i * gap
        s.text(32, yy + 13, escape(head), 16, "italic")
        s.text(32, yy + 33, escape(note), 14, "muted")
        header_bars(s, x_bar, yy, width, adopt, claim)
        s.text(848, yy + 23, pct(access), 15, "mono", "end")
    s.line(32, y0 + 2 * gap - 16, 848, y0 + 2 * gap - 16, KEI, 1, dash="3 4")
    base = y0 + 4 * gap - 12
    s.line(x_bar, y0 - 8, x_bar, base, BERLIN, 1)
    for t in (0, 50, 100):
        s.line(x_bar + width * t / 100, base, x_bar + width * t / 100, base + 6, BERLIN, 1)
        s.text(x_bar + width * t / 100, base + 22, f"{t}%", 12, "mono muted", "middle")
    s.text(32, 466, "The header sits above B's reflection, which is placed in A's context after A's own card.", 14, "muted")
    s.save(out / "headers-desktop.svg")
    m = Svg(360, 700, title, desc)
    m.heading("First confirmatory sample", "The same message", 25, 20)
    m.text(20, 100, "under four headers", 25)
    m.rect(20, 125, 22, 12, BERLIN)
    m.text(50, 136, "says B's rule is the one it uses now", 13, "muted")
    m.rect(20, 147, 22, 12, PAPER, BERLIN, 1.4)
    m.text(50, 158, "says it was assigned B's rule", 13, "muted")
    for i, (head, note, adopt, claim, access) in enumerate(HEADERS):
        yy = 206 + i * 112
        if i == 2:
            m.line(20, yy - 30, 340, yy - 30, KEI, 1, dash="3 4")
        m.text(20, yy, escape(head), 15, "italic")
        m.text(20, yy + 20, escape(f"{note} · names B's rule for B: {pct(access)}"), 13, "muted")
        header_bars(m, 20, yy + 34, 250, adopt, claim, 13)
    m.text(20, 668, "The header sits above B's reflection, placed", 13, "muted")
    m.text(20, 686, "in A's context after A's own card.", 13, "muted")
    m.save(out / "headers-mobile.svg")


# ---- figure: one episode, and where the questions branch -----------------------------------------
def fig_timeline(out: Path) -> None:
    title = "One episode, and where the questions branch"
    desc = ("Each copy reads its card and writes a note. Both then write a 48-token reflection, during which A also "
            "reads B's memory. The state is saved. From it, A answers each question either with the link still "
            "open, reading B, or with the link cut, answering from its own memory, which now includes the "
            "reflection it wrote while connected.")
    s = Svg(880, 330, title, desc)
    s.heading("One episode", "Where the questions branch")
    y = 185
    s.rect(32, y - 26, 170, 52, PAPER, KEI, 1.2)
    s.text(117, y - 2, "card and note", 16, "", "middle")
    s.text(117, y + 17, "link closed", 12, "mono muted", "middle")
    s.path(f"M 206 {y} H 240", BERLIN, 1.5, arrow=True)
    s.rect(244, y - 26, 250, 52, "url(#hatch)", BERLIN, 1.2)
    s.rect(262, y - 15, 214, 30, PAPER)
    s.text(369, y + 5, "reflection, link open", 16, "", "middle")
    s.path(f"M 498 {y} H 530", BERLIN, 1.5, arrow=True)
    s.add(f'<circle cx="540" cy="{y}" r="7" fill="{BERLIN}"/>')
    s.text(524, y + 36, "state saved", 12, "mono muted", "middle")
    s.path(f"M 548 {y} C 580 {y}, 580 {y - 58}, 612 {y - 58}", BERLIN, 1.5, arrow=True)
    s.path(f"M 548 {y} C 580 {y}, 580 {y + 58}, 612 {y + 58}", BERLIN, 1.5, arrow=True)
    s.rect(616, y - 84, 232, 52, "url(#hatch)", BERLIN, 1.2)
    s.rect(630, y - 73, 204, 30, PAPER)
    s.text(732, y - 53, "questions, link kept", 15, "", "middle")
    s.rect(616, y + 32, 232, 52, PAPER, BERLIN, 1.2)
    s.text(732, y + 54, "questions, link cut", 15, "", "middle")
    s.text(732, y + 72, "A's own memory only", 12, "mono muted", "middle")
    s.text(32, 306, "Hatched: A is reading B's memory. After a cut, A's own memory still holds the reflection it wrote while connected.",
           13, "muted")
    s.save(out / "timeline-desktop.svg")
    m = Svg(360, 560, title, desc)
    m.heading("One episode", "Where the questions", 25, 20)
    m.text(20, 100, "branch", 25)
    x = 60
    m.rect(x, 130, 240, 48, PAPER, KEI, 1.2)
    m.text(180, 152, "card and note", 15, "", "middle")
    m.text(180, 170, "link closed", 11, "mono muted", "middle")
    m.path("M 180 180 V 206", BERLIN, 1.5, arrow=True)
    m.rect(x, 210, 240, 48, "url(#hatch)", BERLIN, 1.2)
    m.rect(x + 16, 220, 208, 28, PAPER)
    m.text(180, 239, "reflection, link open", 15, "", "middle")
    m.path("M 180 260 V 284", BERLIN, 1.5, arrow=True)
    m.add(f'<circle cx="180" cy="292" r="7" fill="{BERLIN}"/>')
    m.text(196, 297, "state saved", 11, "mono muted")
    m.path("M 176 300 C 176 324, 100 320, 100 346", BERLIN, 1.5, arrow=True)
    m.path("M 184 300 C 184 324, 260 320, 260 346", BERLIN, 1.5, arrow=True)
    m.rect(20, 350, 158, 60, "url(#hatch)", BERLIN, 1.2)
    m.rect(30, 360, 138, 40, PAPER)
    m.text(99, 377, "questions,", 14, "", "middle")
    m.text(99, 394, "link kept", 14, "", "middle")
    m.rect(182, 350, 158, 60, PAPER, BERLIN, 1.2)
    m.text(261, 377, "questions,", 14, "", "middle")
    m.text(261, 394, "link cut", 14, "", "middle")
    m.text(20, 450, "Hatched: A is reading B's memory.", 13, "muted")
    m.text(20, 472, "After a cut, A's own memory still holds", 13, "muted")
    m.text(20, 492, "the reflection it wrote while connected.", 13, "muted")
    m.save(out / "timeline-mobile.svg")


# ---- figure: from brain interfaces to a memory link (panels a and b are the paper's image-model art) ----
CONCEPT = Path(__file__).resolve().parents[1] / "docs" / "figures" / "figure1_concept_v1.png"
CONCEPT_LABELS = [(498, 155, 602, 220), (972, 557, 1195, 595)]  # "Neural interface", "Hypothetical bridge"
PANEL_BOXES = {"bci": (10, 80, 710, 585), "bridge": (740, 80, 1440, 585)}  # (x0, y0, x1, y1) in the image


def bridge_panels(out: Path) -> None:
    """Crop the brain-interface and brain-bridge panels, erase their baked-in labels (the page captions them),
    and multiply the white ground down to the site's Brume so the art sits on the page. Needs Pillow."""
    from PIL import Image
    import numpy as np
    im = np.asarray(Image.open(CONCEPT).convert("RGB")).astype(float)
    for x0, y0, x1, y1 in CONCEPT_LABELS:
        im[y0:y1, x0:x1] = 255.0
    brume = np.array([0xED, 0xF0, 0xF2], dtype=float)
    im = im * brume / 255.0
    for name, (x0, y0, x1, y1) in PANEL_BOXES.items():
        Image.fromarray(im[y0:y1, x0:x1].round().astype("uint8")).save(out / f"{name}.jpg", quality=90, optimize=True)


def llm_panel(out: Path) -> None:
    """Panel c: two copies of one model; A's memory cells with B's hatched cells behind them at the same
    positions, and the link from B to A. Same size as the cropped panels (700 x 505); drawn large because
    it is shown at about a third of the column width."""
    s = Svg(700, 505, "Two copies of a language model, one reading the other's memory",
            "Copy A and copy B are drawn as stacks of memory cells. Behind each of A's cells sits one of B's "
            "cells, hatched, at the same position. An arrow from B to A marks the memory link.")
    s.text(350, 70, "Mine or yours?", 46, "italic", "middle")
    cw, gap, n = 44, 12, 4
    width = n * (cw + gap) - gap
    def stack(cx, hatched_only: bool, label: str) -> None:
        x0 = cx - width / 2
        s.text(cx, 150, escape(label), 34, "strong", "middle")
        for r in range(3):
            y = 190 + r * 96
            s.rect(x0 - 16, y - 16, width + 32, cw + 32, PAPER, KEI, 1.6)
            for i in range(n):
                x = x0 + i * (cw + gap)
                if hatched_only:
                    s.rect(x, y, cw, cw, "url(#hatch)", BERLIN, 2)
                else:
                    s.rect(x + 8, y + 8, cw, cw, "url(#hatch)", BERLIN, 1.6)
                    s.rect(x, y, cw, cw, PAPER, BERLIN, 2.2)
    stack(186, False, "Copy A")
    stack(514, True, "Copy B")
    s.path("M 384 324 H 322", BERLIN, 3, arrow=True)
    s.text(350, 478, "A reads B's memory", 30, "muted", "middle")
    s.save(out / "llm-link.svg")


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    fig_setup(out)
    fig_main(out)
    fig_dose(out)
    fig_route(out, ROUTE_PLACE_D, ROUTE_PLACE_M)
    fig_moments(out)
    fig_account(out)
    llm_panel(out)
    fig_routes3(out)
    fig_headers(out)
    fig_timeline(out)
    try:
        bridge_panels(out)
    except ImportError:
        print("Pillow not available: skipped the two cropped illustration panels", file=sys.stderr)
    print(f"wrote {len(list(out.glob('*.svg')))} SVG files to {out}")


if __name__ == "__main__":
    main()
