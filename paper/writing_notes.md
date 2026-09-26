# Writing and handoff notes for the first arXiv version

2026-09-25, Codex. This round revised the draft according to `paper/figures/codex_handoff.md` and `docs/reviews/draft_review_claude.md`; the title, structure, seven findings and six main-text figures already set by the PI are kept.

## Current deliverables

- `paper/main.pdf`: 9 pages of main text (including title, abstract, six figures, captions and the AI use statement), 3 pages of references, 9 pages of appendix, 21 pages in total. Neutral single-column article, 10 pt font, 1-inch margins; these are the page counts of the current layout, not of a future conference template.
- Compile by running `make -C paper` from the repository root. The six figures are included at full text-block width, with no height cap; Fig 1 is on page 2, in the introduction. All 21 pages were rendered and checked page by page: no clipped text, no text running over rules, no table overflow; LaTeX reports no warnings, missing citations or overflows, and all fonts are embedded.
- All 47 citation keys are among the verified entries in `refs.bib` and `refs_verification.md`. Verification notes are no longer printed in the references; preprints show their arXiv numbers; multiple citations are separated by semicolons.
- All six GPT illustrations A1–A6 are in the agreed paths, including the optional A5. The script was rerun as-is, all six final PNG figures were checked one by one, and their rendering was checked at a 6.5-inch text block. The full prompts, the record of 18 generations and revisions, the selected versions and SHA256 are in `docs/figures/task_illustrations/handoff_20260925_manifest.json`; the visual check record is `handoff_20260925_qa.md` in the same directory.
- Offline tests: 151 passed, 3 skipped. The plotting scripts, `story_numbers.json`, STORY, OPENING, protocols and result files were not changed; the SD card was only checked read-only. No GPU was operated, and nothing was published externally.

## Handling of the review and B1–B5

1. The eight items in group 1 were completed and committed first: the abstract makes explicit that w=2 is an unnormalized weight; the KV-PC residue gets a same-weight fixed control; the reversed B_K result and the capability drop are listed separately; the reflection grouping notes exact phrase / code-word matching; the w1 regex count is made explicit as 1/300; v2 is described as an earlier sample; the opening is unified on DOSE 00274; the third-person single-ledger result gets marginal proportions, plus second-person and Robin references.
2. B1–B5 are done: removed the figure height cap, moved Fig 1 into the introduction, synchronized the DOSE 00274 tower/table example across the main text and appendix, rewrote the captions of the six figures to match the actual panels, and aligned panel references and threshold statements. The current panels are Fig 1 a–f, Fig 2 a–b, Fig 3 a–d, Fig 4 a–e, Fig 5 a–c, Fig 6 a–d.
3. The main story, clarity and layout suggestions are implemented: each of the seven findings is given its numbers and evidence level; added the study map, task details and term definitions; added where each test in Table 1 is located; the discussion responds to Hirstein/IIT and expands "self as a default"; added the fourth (two-way) principle and the reverse evidence on the self-label; fixed misplaced citations. The START/NOW pairing tables in the appendix are merged and the other narrow tables widened; the closing sentence was moved before the unnumbered AI use statement.
4. The self-report recheck is made explicit as a comparison between Codex's condition-blind semantic coding and the regex coding implemented by Claude; κ is not the agreement between two human coders. The reflection analysis still follows the existing rules, without redoing semantic coding; 00068 belongs to the code-word group, not the exact rule-phrase group.
5. The five figure-draft issues left for Claude in the first round are closed per Section D of the handoff checklist. The new figures do not include the originally planned small capability panel, and the captions no longer point to nonexistent panels. Fig 1c actually has only the orange arrow for A reading B, and the caption is written accordingly; the gray dashed return line mentioned in the checklist does not appear in the current figure, so there is no need to draw it in for the caption.

## Review suggestions not copied verbatim after checking

- The raw NOW pair rates in item 7 of group 2 are incorrect. Read-only recomputation from `20260925-001135_v3_sig_bprime_signal/pair_outcomes.csv`: one-side-wins is 53.75% for FULL, ALL w=0.5 and 8.75% for fixed w=0.5, with independence expectations of 41.3203125% and 8.4375% respectively; the net excess is still 12.1171875 points. The main text uses these numbers, not the checklist's 43.1/6.9 and 36.2/6.7.
- In the same raw table, for fixed w=0.5, RF/NOW each keeping its own rule is 98.75%, not 100%; the main text says 98.8%, and START is 100%. KV-PC's RF/NOW one-side-wins is 37.5%, against 41.25% for the fixed w=2 control, so this residue was not attributed to the loop.
- B_K's -4.786 nats, 90% CI [-8.31, -1.18] and 9.4/14.4-point CAP drop come from `docs/results/v2/signal_pilot_sig2.md`; B_R's -0.235, [-0.75, 0.27] come from `signal_pilot_sig1.md`; the main text and appendix report them separately.
- The verification record for LatentMAS supports only "prepend previous agent's KV cache", and cannot be used to assert how exactly it handles positions. The main text keeps the prediction "separating positions will reduce claiming" and describes LatentMAS as a comparable prepended-cache system.
- The middle bin of Fig 3d is 27/1,200 (2.25%); the main text keeps the count and does not change the 2.2% shown in Claude's figure. The STORY opening has been updated to 00274 and this draft is synchronized with it; the fixed control not spelled out in its #7 can be synchronized later by the plan's maintainer.

## One in-figure wording item left for Claude

**The vector title of Fig 1d is still "Claims B’s word, notices nothing".** STORY §6 explicitly forbids did not notice / detect; please change it to "Claims B’s word, reports no anomaly" or a synonymous title that fits. The main text and captions already use reported nothing unusual. A message has been left in STATUS; per the division of labor, Codex did not modify the plotting code or layout.

## Awaiting PI input or confirmation

The author is provisionally given as the known PI name Yunlong Xu; the author list, affiliations, emails, acknowledgments and public code/data addresses still await PI confirmation. The red TODO for the public archive address was removed, and no URL was invented. The submission venue and conference template will be decided later. No new research decisions were made in this round.
