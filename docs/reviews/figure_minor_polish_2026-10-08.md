# Limited final figure corrections

Date: 2026-10-08. Reviewer/editor: Codex, with independent visual and scientific checks.

## Scope directed by the PI

The PI stopped the broad redesign and asked for the original paper style with small corrections only. All uncommitted redesign changes were restored before this pass. The final changes retain the original six compositions, dimensions, panel positions, illustrations, colors, and font settings. No new illustration or figure-rendering architecture was introduced. Figures 1-3 are byte-identical to the pre-redesign version.

Actual accepted-paper pages were examined as visual references:

- Ackerman and Panickssery, *Inspection and Control of Self-Generated-Text Recognition Ability in Llama3-8b-Instruct*, ICLR 2025, PDF pages 4, 6, and 9. Figure 6 uses four compact panels across the page. [Official PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/d560f94c582033e6d8eb0c97cdd4f721-Paper-Conference.pdf).
- Ramesh and Li, *Communicating Activations Between Language Model Agents*, ICML 2025, PDF pages 4, 7, 8, 13, and 22. Schematics and data use compact layouts, with explanatory detail in captions. [Official proceedings page and PDF](https://proceedings.mlr.press/v267/ramesh25a.html).

These examples support preserving the existing compact structure. They do not establish a universal minimum font size or guarantee publication quality or acceptance. The broad rearrangement recommendations in the earlier figure-quality review are superseded by the PI's narrower scope.

## Changes

| Figure | Final change |
|---|---|
| 1 | Image unchanged. Caption specifies 300 reports, the 165-episode post hoc subset, and paired outcomes averaged within 80 episodes. |
| 2 | Image and caption unchanged. |
| 3 | Image unchanged. Caption specifies normalization over four answer labels and 1,200 answers from 600 episodes with two orderings each. |
| 4 | Two labels distinguish matched mean logit access gain from the plotted hit rate. Caption makes the distinction explicit. |
| 5 | Shortened panel c's title without changing its meaning or position. Its right edge is now 424.88 pt within the 468 pt figure width (previously 468.42 pt). |
| 6 | Removed the exclusive "only" claim; named excess agreement and its loop-minus-fixed contrast; identified the primary-test threshold. X ticks are 0, 5, 10, 15, 20. Caption defines the marginal-choice baseline, 90% episode-bootstrap intervals, 80 episodes, and the primary-test scope of the 10-point threshold. |

No data, error bars, estimates, axes limits, or plotted conditions were changed. The original AI-use disclosure remains accurate and unchanged.

## Validation

- `story_numbers.json` is byte-identical to the baseline and HEAD: SHA256 `57ff984a40dec38df7bb50be6b8ff1f9d724f3a5491f5b0dd49217e6b5259fef`.
- All six PDF media boxes match the originals exactly. All figure widths remain 6.5 inches.
- Rebuilt `paper/main.pdf`: 35 pages, 6 figures, 14 tables. All six figure pages were rendered and checked at manuscript scale, with enlarged checks of the changed figures. Caption-related reflow was also checked on pages 10, 12, and 13.
- Independent visual comparison found only pages 2, 7-13 changed; the other 27 pages are pixel-identical at 72 dpi. Figure 6 now floats to page 11 instead of page 10 after the caption additions; no blank page, clipping, or overlap was introduced.
- Normal LaTeX build has no warnings, undefined references, or overfull/underfull boxes. All 28 fonts are embedded.
- The source archive contains exactly 22 intended regular files, with no macOS metadata or unsafe paths. Each packaged file matches the current source.
- Three clean pdfLaTeX passes with shell escape disabled, outside the project, reproduce the manuscript's extracted text exactly. The only warning is the expected unused epstopdf shell-escape warning.
- All 48 citation keys, 53 labels, and 234 explicit references resolve; a fresh BibTeX run reproduces the bundled bibliography byte for byte.
- The abstract is unchanged: 220 words and 1,295 ASCII characters, identical to the submission metadata.
- Offline tests: `151 passed, 3 skipped`; `git diff --check` passes.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `paper/main.pdf` | 3,881,347 | `3146a3723df408d4914cb36a939b51ff754fce6b6fc004808ed46771fd535c0f` |
| `paper/arxiv.tar.gz` | 3,636,316 | `0f02e7cb2683ec6ebfb68fe1fde582953372ec7ba4fdb0e1b0cc7751749a6e3b` |

The changed wording and statistics were independently checked against the existing data and frozen definitions. This is a local presentation correction, not new experimental evidence. Final author/account/category/license checks and review of arXiv's generated PDF remain with the PI; nothing was uploaded or published.
