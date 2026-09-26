# Task illustrations v1

2026-09-25: generated and checked by Codex using the built-in `image_gen.imagegen`, following the six prompts provided by the PI.
The full original prompts are in `paper/figures/imagegen_prompts.md`; the `*.prompt.txt` files in this directory are the prompts actually used (including general constraints and targeted revisions). The tool does not disclose its model version, so it cannot be confirmed to be image2.5.

| Illustration | PNG | Actual size | Use |
|---|---|---|---|
| Task flow | [task_v1.png](task_v1.png) | 2172 × 724 | Replaces the `fig_task` schematic |
| Content channels | [channel_v1.png](channel_v1.png) | 2172 × 724 | Above `fig_channel.pdf` |
| Link cut | [linkcut_v1.png](linkcut_v1.png) | 1448 × 1086 | Left of `fig_linkcut.pdf` |
| Third person | [wording_v1.png](wording_v1.png) | 1672 × 940 | Above the results area of `fig_wording.pdf` |
| Two branches | [pairs_v1.png](pairs_v1.png) | 1448 × 1086 | Left of the results area of `fig_pairs.pdf` |
| Optional summary | [summary_v1.png](summary_v1.png) | 1672 × 941 | For reports or presentations, not for the main text of the paper |

## Review and composition

- [preview.pdf](preview.pdf): a six-page preview; the task flow and the summary are shown on their own, and the rest are composed with the existing result PDFs.
- `paper/figures/imagegen_panels.tex`: provides only the figure-body macros; captions and labels are still managed by the paper's LaTeX. The macro names are `\MBTaskPanel`, `\MBChannelPanels`, `\MBLinkCutPanels`, `\MBWordingPanels`, `\MBPairsPanels`, `\MBSummaryPanel`.
- When compiling from the repository root, load `graphicx` first, then `\input{paper/figures/imagegen_panels.tex}`. When compiling from `paper/`, first `\newcommand{\MBProjectRoot}{..}`, then `\input{figures/imagegen_panels.tex}`.
- The result figures embed the existing vector PDFs directly. The link-cut, third-person and two-branch figures only crop out the old schematics at typesetting time, keeping the axes, legends and all data; the original PDFs are unchanged. If the size or layout of the result figures changes in the future, the crop ranges need to be rechecked.
- The third-person card text is dense, so it is composed top-and-bottom for legibility. The channel figure actually came out at 3:1, short of the roughly 5:1 the prompt asked for; the full labels are kept, with no stretching.
- The preview uses the current result versions in `paper/figures/`; the v3-related panels still contain pilot data and must not be taken as the pending confirmatory results. The preview booklet does not replace the formal captions.

Rebuilding the preview (from the repository root):

```sh
mkdir -p /tmp/mb-illustration-preview
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/mb-illustration-preview docs/figures/task_illustrations/preview.tex
cp /tmp/mb-illustration-preview/preview.pdf docs/figures/task_illustrations/preview.pdf
```

## Checks and scope

- All six images are opaque RGB PNGs; English content, A/B coloring, connection direction and branch roles were checked image by image.
- Targeted revisions: the channel and link-cut images had their transparent backgrounds fixed; the two-branch image had the color blocks of the two kinds of adoption corrected, two-way arrows added, and the thought-square colors matched; the third-person image had all Theta highlights filled in.
- The two small color blocks in the two-branch image are always ordered A, B, and the colors show the source of the rule: each keeps its own is blue/orange; A adopts B is orange/orange; B adopts A is blue/blue; swap is orange/blue. The legend colors in the result bar chart indicate categories and mean something different; the preview page explains this.
- The number of layers is schematic; the questions and memory cards in the figures follow the PI's shorthand prompts and are not the full experimental templates or verbatim model outputs. 48 indicates the length of the flow, not a result statistic.
- The text of the sixth image is kept as the PI wrote it, for a popular summary; "does not notice" is not a judgment about consciousness. Specific statements in the formal paper should still rest on the corresponding readouts and results.
- The original Figure 1 and all matplotlib result figures are left as they were. The experimental protocol, research metrics, analysis code and GPU runs were not changed.

## AI use record

Draft English disclosure:

> Task schematics were generated with OpenAI's built-in image-generation tool from author-specified prompts and revised for label accuracy, connection direction, and color semantics. The tool did not expose its model version. Numerical result panels were produced separately with Matplotlib from the recorded experimental data and were embedded as vector PDFs. The schematics depict illustrative examples rather than quantitative evidence.

`manifest.json` records the final PNGs' sizes, SHA256, generated-file identifiers and prompt paths. The first drafts were not kept as deliverable images; all the revision prompts needed are kept.
