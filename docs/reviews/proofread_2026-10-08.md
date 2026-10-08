# Manuscript corrections and proofreading - 2026-10-08

The PI requested both corrections identified in the readiness audit, followed by a full proofread. This report records the resulting manuscript and supersedes the two outstanding manuscript findings in `arxiv_readiness_2026-10-08.md`; that audit remains unchanged as a historical record.

## Completed corrections

1. **Matching measure.** The abstract, introduction, setup, route comparison and caption, limitations, and appendix now distinguish mean access gain from answer frequency. Setup defines it as the increase from no link in the logit access score. The existing answer rates remain descriptive results. No matching procedure or metric was changed.
2. **Figure 1e.** The prefix of the bottom annotation changed from "Link cut -> assigned rule:" to "After cut:". The figure was regenerated with `scripts/make_story_figures.py --only fig1_hook`, reading the existing SD-card records. The annotation now fits its panel. `paper/figures/story_numbers.json` is byte-identical to its pre-edit version.

## Full proofreading pass

Three independent readers covered the complete main text and every included appendix file. The final edits were checked again for unintended meaning changes. Corrections included:

- Explicitly limiting semantic coding to no link, weight 1, and weight 2; the original phrasing followed a description of all six weights and could imply that all reports received semantic coding.
- Synchronizing two appendix descriptions with the already approved positional account: assignments share a short region, while the two assignment/Robin lines are independently counterbalanced.
- Clarifying that the untagged text still has a header, but its header does not identify a source.
- Limiting the zero-claiming statement to the access-matched steering vector, consistent with the reported nonzero rate at the stronger vector setting.
- Removing a sentence that incorrectly excluded untagged text from producing claiming, and fixing a pronoun that referred to the steering direction rather than the rule.
- Clarifying that the untested quantity in the two-way pilot was the difference between its assigned-rule and current-rule effects; the assigned-rule comparison itself was tested.
- Using "near zero", "high confidence", "most answers", and "about as much attention" where the previous wording implied exact zero, equal confidence, every answer, or no larger attention share.
- Removing "Only" from the appendix's live-loop summary because the weak-live condition also has a small positive secondary effect in the existing table.
- Removing an overly specific LatentMAS position claim from the prediction paragraph. Existing references supporting cache prepending remain; the available source-verification notes do not establish its exact position handling.
- Correcting the table description of access to a logit advantage, removing an obsolete claim about appendix ordering, and repairing one grammatical comparison.

All result values, tables, confidence intervals, statistical definitions, experimental conditions, and central conclusions remain unchanged. The only added numeric tokens in the manuscript identify the two already reported weights in the semantic-coding scope. No references were added; one redundant citation occurrence was removed while the citation key remains used elsewhere. This was proofreading against existing evidence, not a new raw-data analysis or a re-verification of every cited original.

## Validation

- `make -C paper`: success, 35 pages, no final LaTeX warnings, undefined references, or overfull/underfull boxes.
- All 48 citation keys resolve; all explicit cross-references resolve, with no duplicate labels.
- Final visual review: all 35 pages checked as contact sheets, with all 23 pages changed from the previous PDF inspected at 150 dpi. Figure 1e fits its panel; no new clipping, overlaps, missing figures/tables, abnormal whitespace, or footer collisions were found.
- Submission abstract synchronized to the manuscript: 220 whitespace-delimited words, 1,295 ASCII characters.
- `make -C paper arxiv`: clean archive with exactly 22 regular files and no macOS metadata entries; all files match the working source byte for byte.
- Fresh archive extraction: three successful pdfLaTeX passes with shell escape disabled. Extracted PDF text exactly matches `paper/main.pdf`. The only warning is epstopdf noting disabled shell escape; the package contains no EPS figures requiring conversion.
- `.venv/bin/pytest -m 'not gpu'`: 151 passed, 3 skipped.

## Artifacts

| Artifact | Size | SHA256 |
|---|---:|---|
| `paper/main.pdf` | 3,880,582 bytes | `cf5946bab999c0b15aec9774a7541150807a8acc016253fadf3eb6b8cd652ca5` |
| `paper/arxiv.tar.gz` | 3,636,032 bytes | `5b684b44686d290b230fd9d7aa55524912bc5b79e79a7cacaee54f8db46c9c67` |

Copyable submission fields are in `paper/arxiv_submission_metadata.txt`.

## Remaining submission steps

The manuscript corrections requested by the PI are complete. The PI's final read-through and confirmation of author information, account endorsement/quota, category, and license remain, followed by inspecting the PDF generated by arXiv. No external submission, upload, or website update was made in this session; the previously published website copy of the PDF is therefore not automatically synchronized with this revision.
