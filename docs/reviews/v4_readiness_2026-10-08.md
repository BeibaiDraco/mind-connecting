# Second-model replication planning and instance readiness review

Date: 2026-10-08. Readiness review only; no second-model experiment or paper edit.

## Outcome

`docs/protocol/PROTOCOL_V4_DRAFT.md` specifies an eight-condition proposal with
fixed N=600, matched-route and text-source controls, separate suitability and
content-validity stages, five primary hypotheses and explicit missing-branch
handling. It is not approved or frozen. Model access/revision, PI approval of
the research changes and budget, implementation, offline tests and GPU
correctness/suitability gates remain before formal data collection.

Independent scientific and engineering reviewers checked the actual v1-v3
protocols, runtime, selectors and analysis code. The initial five-arm proposal
was insufficient to replicate the matched-route claim. The new recommendation
prioritizes KV-w1 plus a fresh matched STATIC control and TAG/UNTAG text over a
third-person or live-loop expansion.

## Corrections incorporated

- Config layer numbers are one-indexed: scaled depth is layer 21, block index 20.
- Strong-K* eligibility must not be applied to fixed K1; K1 has an independent
  measurable-access and content-validity check.
- The content-counterfactual bootstrap statistic is `C_content`, not ordinary
  access gain. Formal CF is for K* only; CF at distinct w1 is a validity-stage arm.
- The existing selector does not implement the proposed screening order or the
  hit-rate improvement criterion. This needs code and focused tests, not just
  changed YAML thresholds.
- Unavailable primary comparisons must retain the five-test multiplicity family;
  old missing-arm and NaN behavior cannot be reused unchanged.
- Current FULL/RF execution recomputes reflections. Snapshot reuse or complete
  field-equality validation is required before interpreting the cut comparison.
- Baseline measures both sides; formal and selection stages measure A only.
  With ten questions and two orderings, the eight-arm formal run has 96,000
  readouts. K*=K1 deduplication yields 84,000. Neither is the statistical N.
- Freeze support, tokenizer/profile identity, stop tokens and possible template
  date defaults must be made explicit. The existing shell run chain does not
  shut down a Vast instance.

The old recorded Qwen confirmatory run produced 92,400 readouts in 3h23m24s.
That is a throughput reference, not a runtime promise for the new 8B model.
New-model per-condition smoke timing must precede the full budget estimate.

## Vast instance recovery check

The PI requested restoring the previous instance. The provider reported one
stopped H100 SXM instance, approximately 80 GB, at USD 2.2667/hour. The CLI's start
and stop commands return text and may exit zero even when the API reports failure;
the initial JSON assumption was corrected and provider state was verified.

A bounded recovery attempt never reached running. A subsequent structured SDK
response identified the cause:

`success: false; error: resources_unavailable; Required resources are currently unavailable, state change queued.`

The queued start was cancelled. At 2026-10-08 17:46 UTC, the API confirmed
`actual_status=exited`, `intended_status=stopped`, `cur_state=stopped`,
`next_state=stopped`. No model ran, no replacement instance was rented, and no
existing data was deleted. Because SSH inspection could not take place, remote
package versions, cache contents, Llama access and disk capacity remain unverified.
Instance IDs, host/port and credentials are deliberately absent from this record.

## arXiv handoff

The PI reports the source package uploaded and at Process. The connected browser still showed a login page, so server compilation
and the generated PDF were not independently inspected. A source-scan warning
for `figures/#1.pdf` refers to the existing macro parameter; the archive and the
PI's pasted file list contain all six actual figures. `main.bbl` is included and
is sufficient without the `.bib` for this submission.

Next: verify successful compilation and inspect the server-generated PDF, then
copy `paper/arxiv_submission_metadata.txt` into Metadata and review Preview.
Uploaded/compiled/finally submitted/announced are separate states; none of the
later states is inferred from an earlier one. The arXiv first-version bytes and
all manuscript figures/results remain unchanged.

Official instructions: [arXiv submission](https://info.arxiv.org/help/submit/index.html),
[TeX processing and bibliography files](https://info.arxiv.org/help/submit_tex.html).
