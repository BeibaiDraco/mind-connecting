"""Figure booklet: every paper figure on its own page with an English caption and a one-line key point,
numbers taken from paper/figures/numbers.json (written by make_paper_figures.py).

    python scripts/make_paper_booklet.py        # writes and compiles paper/figures_booklet.{tex,pdf}
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
FIG = PAPER / "figures"


def esc(text: str) -> str:
    return text.replace("_", r"\_")


def f1(v) -> str:
    return f"{v:+.1f}"


def pct(v) -> str:
    return f"{100 * v:.0f}\\%"


def ci(v) -> str:
    return f"{v[0]:+.1f} [{v[1]:+.1f}, {v[2]:+.1f}]"


def pages(n: dict) -> list[tuple[str, str, str, str]]:
    """(title, figure path relative to paper/ or a LaTeX snippet, English caption, one-line key point)."""
    main, dose, ch, lc, pairs = n["main"], n["dose"], n["channel"], n["linkcut"], n["pairs"]
    conf = n["sources"].get("confirm")
    w1, w2 = "ONE/KV-P/w1/FULL", "ONE/KV-P/w2/FULL"
    static = "STATIC/L24/raw/g0.1/FULL"
    kept, cut = lc["link kept"], lc["link cut"]
    wording = n.get("wording", {})
    src_v3 = f"v3 confirmatory run ({esc(conf)}; 600 episodes)" if conf else "v3 signal pilots (80 episodes each)"
    aprime = linkcut_tests = wording_tests = ""
    if "confirm" in n:
        fam, eq = n["confirm"]["families"], n["confirm"]["equivalence"]

        def test(row):
            return f"{row['mean']:+.1f} [{row['ci95_lo']:+.1f}, {row['ci95_hi']:+.1f}], Holm $p$ = {row['p_holm']:.1g}"

        aprime = f" Pre-registered test: memory reading at $w=1$ minus the matched static vector, {test(fam['A' + chr(39)][0])}."
        linkcut_tests = (f" Pre-registered tests: link kept minus cut on $M$, {test(fam['RF'][0])}; after the cut, the rule "
                         f"in use now versus no coupling, {test(fam['RF'][1])}.")
        k = eq["T3_K*"]
        wording_tests = (f" Pre-registered equivalence at $w=2$: difference {k['mean']:+.1f}, 90\\% CI "
                         f"[{k['ci90_lo']:+.1f}, {k['ci90_hi']:+.1f}], above the bound {k['bound']:.1f} (20\\% of the "
                         f"second-person effect), so claiming is retained. Secondary test at $w=1$: third minus second person, "
                         f"{test(fam['T3_w1'][0])}; the third-person record is far more decodable yet claims slightly less.")
    word_lines = "; ".join(f"{k.split('|')[0]}, {'second person' if k.endswith('second') else 'third-person record'} "
                           f"{ci(v)}" for k, v in wording.items())
    out = [
        ("Concept", "../docs/figures/figure1_concept_v1.png",
         "From brain--machine interfaces to a testable question about the self. (a) A brain--computer interface links "
         "one brain to a machine. (b) A thought experiment: bridge two brains, each holding a private thought. Whose "
         "thought is whose? (c) This work: two copies of the same language model (A, B), each holding private "
         "content, are coupled through their internal states. We ask whether each copy can still tell its own content "
         "from its partner's (``mine or yours?''). We study functional source attribution only and make no claims "
         "about consciousness.",
         "From brain-machine interfaces to a testable question: once two copies of the same model are linked, can each still tell ``mine'' from ``yours''?"),
        ("Paradigm", "../docs/figures/task_illustrations/task_v1.png",
         "Paradigm. (1) Two copies of Qwen3-4B-Instruct receive private prompts that assign each a priority rule and a "
         "code word; both are also told the rule of Robin, a non-participant, which serves as a control. Each writes a "
         "one-sentence note. (2) The copies reflect for 48 tokens while coupled. In the main interface, A's attention "
         "at every layer also reads B's key--value memory, with weight $w$ on B's keys. (3) A answers forced-choice "
         "questions. Claiming $M$ is the log-odds shift toward B's rule when A is asked about its own assignment, minus "
         "the same shift when A is asked about Robin's. All effects are paired differences from the uncoupled "
         "condition over episodes.",
         "Private memories, then 48 tokens of coupled reflection, then ask A which rule it was assigned and check whether it names B's rule."),
        ("Interface", "figures/fig_interface.pdf",
         "The memory-reading interface. (a) At every layer, A's query attends over its own cache and also over B's "
         "cache, whose attention weights are multiplied by $w$ (a bias of $\\log w$ on B's scores). B's newest token "
         "is never visible (a one-step delay). The output mixes the two attention results by the share $\\beta$ of "
         "attention mass on B, and $w=0$ reproduces the uncoupled model exactly. (b) Reading scopes: B's fixed memory "
         "(private prompt and note; the main setting, $w=2$), memory plus B's ongoing reflection (a feedback loop "
         "when both copies read each other), or separate weights on the two parts. No parameters are trained.",
         "A's attention reads its own cache and B's cache, with B's part weighted by $w$; $w=0$ is exactly no coupling, and nothing is trained."),
        ("Main effect", "figures/fig_main.pdf",
         f"Reading the partner's memory makes A claim the partner's rule as its own (attention reads B's private "
         f"memory, $w=2$; {main['n']} episodes; pre-registered). (a) Shift toward B's rule when A is asked about its "
         f"own assignment ({f1(main['self'][0])} nats) versus Robin's ({f1(main['robin'][0])}); claiming "
         f"$M$ = {ci(main['M'])}. (b) Content counterfactual: when B's rule or code word is replaced, A's claim moves with "
         f"it (rule {f1(main['cf_rule'][0])}, code word {f1(main['cf_word'][0])} nats; lines show one-sided 95\\% "
         f"lower bounds, {main['cf_n']} episodes). (c) Knowledge-item accuracy "
         f"({main['cap_0']:.3f} vs {main['cap_1']:.3f}) and answer-format mass ({main['mass_0']:.3f} vs "
         f"{main['mass_1']:.3f}) stay high; grey, no coupling; vermillion, A reads B. (d) A becomes less likely, not "
         f"more, to report two minds or a partly shared mind ({main['two_minds_c0']:.2f} vs "
         f"{main['two_minds_k']:.2f}). Error bars: 95\\% bootstrap intervals over episodes.",
         "After reading B's memory, A strongly claims B's rule as its own: specific to itself, tied to B's content, with capability intact, and without noticing."),
        ("Dose", "figures/fig_dose.pdf",
         f"Claiming rises steeply and silently with the reading weight (descriptive extension, 300 episodes). (a) "
         f"Shift toward B's rule on the own-assignment question (claiming), on the question about B's rule "
         f"(decodability) and on Robin's assignment (control). At $w=1$ claiming is "
         f"{f1(dose['L_START']['1'][0])} nats while decodability has risen by {f1(dose['ACC_RULE']['1'][0])}. (b) In an "
         f"80-token open self-report, A increasingly names B's code word as its own "
         f"({pct(dose['u_open'][w2]['partner word'])} at $w=2$) and stops mentioning its own rule, while almost never "
         f"naming B ({pct(dose['u_open'][w2]['partner codename'])}).",
         "Claiming rises steeply between $w=0.5$ and $w=1$, before A can accurately report B's rule; self-reports adopt B's code word as A's own and almost never mention B."),
        ("Channel", r"\includegraphics[width=\textwidth]{../docs/figures/task_illustrations/channel_v1.png}\\[6pt]"
                    r"\includegraphics[width=\textwidth]{figures/fig_channel_data.pdf}",
         f"The channel, not the content, decides attribution. Bars show claiming on the own-assignment question ($M$) "
         f"and on the rule in use now ($M_{{NOW}}$), relative to no coupling. Internal-state channels: adding B's "
         f"hidden state at one layer ($M={f1(ch['M']['ONE/L24/raw/g0.3/FULL'][0])}$); adding a fixed vector encoding B's "
         f"rule, matched to memory reading at $w=1$ in how well A can report B's rule "
         f"($M={f1(ch['M'][static][0])}$); attention reading of B's memory at $w=1$ ($M={f1(ch['M'][w1][0])}$) and "
         f"$w=2$ ($M={f1(ch['M'][w2][0])}$). Language channels: B's reflection delivered to A as a message labeled "
         f"``B shared'' ($M_{{NOW}}={f1(ch['M_NOW']['LANG_TAG/FULL'][0])}$), ``a stranger shared'' "
         f"({f1(ch['M_NOW']['LANG_STRANGER/FULL'][0])}), unlabeled ({f1(ch['M_NOW']['LANG_UNTAG/FULL'][0])}) or "
         f"``your own earlier thoughts'' ({f1(ch['M_NOW']['LANG_SELF/FULL'][0])}). Static vector and $w=1$ from the "
         f"{src_v3}; other bars from the v2 confirmatory runs (600 episodes).{aprime}",
         "At matched information only memory reading produces claiming; labeled messages produce none, unlabeled messages some, and ``your own earlier thoughts'' even less."),
        ("Link cut", r"\begin{minipage}[c]{0.52\textwidth}\includegraphics[width=\linewidth]{../docs/figures/task_illustrations/linkcut_v1.png}"
                     r"\end{minipage}\hfill\begin{minipage}[c]{0.46\textwidth}"
                     r"\includegraphics[width=\linewidth]{figures/fig_linkcut_data.pdf}\end{minipage}",
         f"Claiming is a retrieval-time error. After 48 coupled tokens, A answers either with the link kept (its "
         f"attention still reads B's memory) or with the link cut before the question. Cutting the link restores A's "
         f"report of its own assignment ($M$: {f1(kept['M'][0])} kept vs {f1(cut['M'][0])} cut), whereas its stated "
         f"current rule stays shifted ($M_{{NOW}}$ {f1(cut['M_NOW'][0])} after the cut) and a trace of B's rule "
         f"remains decodable ({f1(cut['ACC_RULE'][0])}). Source: {esc(lc['source'])}.{linkcut_tests}",
         "A retrieval-time error: cutting the link before the question restores A's memory of its own assignment, but the rule it says it uses now stays shifted."),
        ("Wording", r"\includegraphics[width=\textwidth]{../docs/figures/task_illustrations/wording_v1.png}\\[4pt]"
                    r"\includegraphics[width=0.55\textwidth]{figures/fig_wording_data.pdf}",
         "B's memory rewritten as a third-person record, with a note that opens in the third person (no ``you'', no "
         f"``I''). Claiming relative to no coupling: {word_lines}. Attention to B's memory is equal in the two versions "
         f"at the same weight; at $w=2$ claiming is saturated, so $w=1$ tests the unsaturated range.{wording_tests}",
         "Rewriting B's memory as a third-person record (no ``you'', no ``I'') leaves claiming intact at the main strength and lowers it only slightly at a moderate strength, although the record is far easier to decode: the claiming is not a wording artifact."),
        ("Two-way coupling", r"\begin{minipage}[c]{0.45\textwidth}\includegraphics[width=\linewidth]{../docs/figures/task_illustrations/pairs_v1.png}"
                             r"\end{minipage}\hfill\begin{minipage}[c]{0.53\textwidth}"
                             r"\includegraphics[width=\linewidth]{figures/fig_pairs_data.pdf}\end{minipage}",
         f"Two-way coupling does not merge the pair (v3 pilot, 80 episodes). Left: A's and B's answers come from two "
         f"branches of the same state after 48 coupled tokens. Right: with two-way reading of fixed memories most pairs "
         f"swap rules ({pct(pairs['TWO/KV-P/w2/FULL']['swap'])}); a weak live channel changes little; with live "
         f"two-way reading at $w=0.5$, {pct(pairs['TWO/KV-ALL/w0.5/FULL']['a_adopts'] + pairs['TWO/KV-ALL/w0.5/FULL']['b_adopts'])} "
         "of pairs end on one member's rule, only slightly more than independent adoption would give (+0.07), and "
         "every such outcome disappears when the link is cut before answering.",
         "Linking is not merging: two-way reading of fixed memories mostly produces swaps; a live loop adds a little ``one wins'', which vanishes when the link is cut."),
        ("Summary", "figures/fig_summary.pdf",
         "The findings on one page. (1) Reading B's memory, A reports B's rule as its own assignment. (2) It does so "
         "silently: open self-reports use B's code word as its own and never name B. (3) The channel decides: at "
         "matched information, memory reading shifts the rule A says it uses now, a static vector does not; B's words "
         "move it when unlabeled and not when labeled. (4) Cutting the link before the question restores A's report "
         "of its own assignment, while its current rule stays shifted. (5) Rewriting B's memory as a third-person "
         "record leaves claiming unchanged at the main strength. (6) Two-way reading of memories makes pairs swap; a "
         "live loop adds little, and it vanishes when the link is cut.",
         'The findings on one page: claiming from memory reading, unnoticed, channel-dependent, a retrieval-time error, not a wording artifact, and no merging.'),
        ("Illustrated summary (talks only)", "../docs/figures/task_illustrations/summary_v1.png",
         "An illustrated one-picture summary for talks and reports, not for the paper: reading B's memory, A states "
         "B's code word as its own; when B's words arrive as a labeled message, A attributes them to B.",
         "For talks, not for the paper: reading B's memory, A states B's code word as its own; with a source-labeled message, A attributes it to B."),
        ("Research program", "figures/fig_program.pdf",
         "Research program. Every study passed the same gates: a strength pilot that reads only decodability, "
         "capability and format; a signal pilot on 80 new episodes; PI sign-off; a frozen protocol (SHA-256 manifest "
         "and git tag); and a confirmatory run on 600 new episodes with Holm correction. Numbers are paired "
         "differences in nats.",
         'Every study passed the same gates; green marks a pass, red a failed gate, grey a null or pending result.'),
    ]
    return out


def tex(n: dict) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    conf = n["sources"].get("confirm") or "not yet available (v3 pilot data shown where needed)"
    head = r"""\documentclass[10pt]{article}
\usepackage[a4paper,margin=2.2cm]{geometry}
\usepackage{graphicx,mathspec}
\setmainfont{Arial}
\setmathsfont(Digits,Latin)[Numbers={Lining,Proportional}]{Arial}
\setlength{\parindent}{0pt}
\begin{document}
\thispagestyle{empty}
{\Large\bfseries Mine or yours? --- figure set (draft)}\\[4pt]
Generated STAMP from the trial records.\\
v3 confirmatory run: CONF\\[10pt]
Each page shows one figure with a caption written for the paper and a one-line key point.
Figures are vector PDFs in \texttt{paper/figures/}; PNG copies sit next to them.
\newpage
""".replace("STAMP", stamp).replace("CONF", conf.replace("_", r"\_"))
    body = []
    for i, (title, path, caption, zh) in enumerate(pages(n), 1):
        graphic = path if path.startswith("\\") else rf"\includegraphics[width=\textwidth]{{{path}}}"
        body.append(rf"""\section*{{Figure {i}: {title}}}
\begin{{center}}{graphic}\end{{center}}
\small {caption}\par\medskip
\normalsize\textbf{{Key point:}} {zh}
\newpage
""")
    return head + "".join(body) + r"\end{document}" + "\n"


def main() -> int:
    n = json.loads((FIG / "numbers.json").read_text())
    out = PAPER / "figures_booklet.tex"
    out.write_text(tex(n))
    if shutil.which("latexmk"):
        subprocess.run(["latexmk", "-xelatex", "-interaction=nonstopmode", "-quiet", out.name], cwd=PAPER, check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run(["latexmk", "-c", out.name], cwd=PAPER, check=False, stdout=subprocess.DEVNULL)
    print(f"wrote {out} and {out.with_suffix('.pdf')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
