# Publication figure-quality review - 2026-10-08

Reviewer: Codex, with independent visual-design and scientific-encoding reviewers.
Scope: the six figures included in the current manuscript, evaluated at their final 6.5-inch width. This is a quality assessment, not a redesign or a new raw-data audit. No manuscript, figure, or numerical artifact was changed.

## Overall assessment

The figures have a coherent narrative, consistent blue/orange roles, vector data panels, and 300-ppi embedded illustrations. They are suitable foundations for publication, but it would be inaccurate to certify every figure as polished to a strong conference standard. The common weaknesses are small physical typography and uneven allocation of space. Figure 4 also retains a scientifically ambiguous matching label that the previous text proofreading did not fix.

This review supersedes the preceding pre-upload audit's broad statement that no local content or layout defect remained. Technical source-package compilation remains verified; the figure findings below were missed by that audit and should be addressed before treating the graphics as final.

## Priority findings

1. **Correct Figure 4b's matching labels.** The x-axis measures the fraction of answers naming B's rule. The two relevant points are 15.3% and 19.8%, while the matching criterion is mean logit access gain (4.179 and 4.081 nats). The figure still says "same access, different route" and "steering vector (same access as w = 1)" (`scripts/make_story_figures.py`, `fig4_route`). Its caption now correctly specifies mean access gain, but the in-figure labels must also identify the matched logit quantity. Suggested wording: "matched access gain (logits)". No plotted point is known to be numerically wrong.
2. **Raise type sizes by reallocating space.** Most labels are 5.6-5.8 pt at the final manuscript width. Minimum extractable upright text is 5.6, 5.6, 5.3, 5.5, 5.2, and 5.6 pt for Figures 1-6, respectively. Raster illustration text is not included in that measurement. The final PDF contains some tick labels smaller than the plotting script's nominal 5.6-pt floor. Reading a enlarged PNG is not an adequate final-size typography check.
3. **Give Figure 5c's title a right margin.** The final word "them" has a text bounding box ending at x=468.418 pt on a 468-pt-wide figure. This is a small edge clipping, not a major missing label; shortening or wrapping the title resolves it.
4. **Make Figure 6's statistical quantity and result hierarchy clearer.** Its +6.7/+12.1 values compare excess same-rule pairing after subtracting each condition's independent-choice expectation; they are not simple differences of raw agreement rates. The caption should define this baseline directly. The 10-point threshold applies to the assigned-rule primary comparison; the figure should make the primary comparison's failure to reach that threshold conspicuous. The "only the live loop couples the pair" heading/caption should also state its comparison scope or use nonexclusive wording, since the appendix reports a small positive result for fixed memory plus weak live reading. The plotted values and intervals themselves are consistent with the existing reports.

## Per-figure recommendations

| Figure | Current strengths | Recommended revision |
|---|---|---|
| 1: opening overview | Memorable motivation and three concrete findings; hypothetical brain bridge is labeled | Reduce duplication between miniature diagrams, quotations, and explanatory lines in d-f; enlarge the useful content. State denominators/units for the 83%, 64%, and 94% examples more directly. Preserve the approved conceptual motivation rather than removing it merely because it is illustrative. |
| 2: task and timeline | Clear three-stage flow and saved-state branching; one of the more mature layouts | Harmonize the raster and vector typography. Make the fixed partner memory distinct from its ongoing reflection, so the diagram can explain which state is read. Enlarge the branch annotation. No wholesale redesign is necessary. |
| 3: main effect and reports | Strong data content, meaningful control, dose response, and cross-sample check | Four narrow data panels compete for a short horizontal strip. Consider two rows or greater height, with larger axes/legends. Specify that the 1,200 answers in panel d are two orderings within 600 episodes and clarify the four-option probability normalization. |
| 4: route and wording | Valuable separation of arrival, claiming, and attribution; multiple useful controls | Correct the two matching labels first. Enlarge the core scatterplot and give the wording example and paired-answer result a clear sequence. Reduce annotation competition; specify which panels display uncertainty or add the already available uncertainty where helpful. |
| 5: timing and residual content | Strong connection between an example, a controlled intervention, and post hoc groups; counts are shown | Keep the three-panel structure. Fix the long title and enlarge labels/counts. Mark the post hoc grouping directly when useful for standalone reading. |
| 6: two-way pilot | Distinguishes swapping from agreement; displays primary/secondary results and intervals | The interval plot's data axes are only 0.42 inches high. Allocate more space to that result and less to the large schematic; simplify tick density. Define the excess baseline, clarify the threshold scope, and avoid an overbroad exclusive heading. |

## Relevant official guidance

- [ICML accessibility guidance](https://icml.cc/Conferences/2024/AccessiblePapersAndTalks), linked from the 2026 author instructions, recommends figure text no smaller than caption text, adequate contrast and resolution, and redundant encodings beyond color.
- [ICML 2026 style example, Section 2.6](https://media.icml.cc/Conferences/ICML2026/Styles/example_paper.pdf) calls for legible, labeled components and axes, legends for curves, and lines at least 0.5 pt; its captions are 9 pt.
- [NeurIPS paper checklist](https://neurips.cc/public/guides/PaperChecklist) asks for claims matched to the evidence and appropriate statistical uncertainty for the main experiments, with the calculation and source of variation explained. This does not require an error bar on every schematic or descriptive panel.

These are venue-specific reporting and accessibility references, not a universal aesthetic certification. Final-size export review and independent comprehension checks remain necessary after any revision.

## Scope and next step

No additional experiment or change to numerical results is proposed. A focused figure revision should correct the scientific labels and clipping, then improve typography and panel hierarchy while preserving the existing narrative and evidence. Rebuild and re-audit the manuscript/source archive after any figure changes. The current archive was not silently replaced during this assessment.
