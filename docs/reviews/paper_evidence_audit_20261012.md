# Manuscript evidence and claim audit, 12 October 2026

## Scope and conclusion

This is an independent substantive review of the current manuscript, not a paper revision or a new experiment. The reviewed checkout is `74e83e66fd0c7be137be3dde555caf2e2dfee4f1`; all line references below refer to that version. I read `paper/main.tex`, its main sections and appendices, the adopted historical story, the v4 reports/reviews, the v5 continuation protocol, and the new provenance and STATIC reports. The two result reviewers independently reconstructed the new statistics from raw data; this review checks their implications against the manuscript rather than claiming a third full raw-data recomputation. No manuscript, protocol, result, configuration or scientific parameter was changed.

The present paper remains a coherent report of the original Qwen experiments, but it is **not yet an adequate account of the completed evidence**. Its strongest new story is broader than a special failure of the self: partner KV memory can contaminate answers about the receiver's original record, including a third person's assignment, even when the question explicitly identifies that record. Content access and correct original attribution are different outcomes. The new studies strengthen that empirical result while limiting the proposed positional mechanism, universal route claims and positive word-residue generalization.

Recommended central wording:

> In the tested Qwen and Llama checkpoints, direct access to a partner's KV memory changes answers about the receiver's original assignments. The vulnerability extends to a conflicting third-party entry and persists despite explicit original-record questions; access to the donor's content alone does not determine correct attribution.

This licenses a bounded empirical paper. It does not establish a distinct self mechanism, literal overwriting of stored memories, a causal RoPE-position mechanism, consciousness, or a generally effective mitigation. No further model run is necessary merely to report these completed results faithfully. Stronger mechanistic claims would require additional interventions, rather than stronger wording.

## Evidence that must enter the revision

The percentages below concern counterbalanced question presentations, with uncertainty based on episode means. They are not independent-trial counts. Raw logit magnitudes should not be compared across models as a calibrated scale.

| Evidence block | Result relevant to the story | Required limit |
|---|---|---|
| Original Qwen v2/v3 | At w2, assigned-rule donor choices reach 97.1%; the Qwen w1 versus L24/g0.1 STATIC comparison has closely matched formal mean rule-access gains, 4.081 versus 4.179 nats, and 52.3% versus 0% assigned-rule donor choices. | These are distinct original cohorts/settings. Open reports, strict third-person cards, balanced rehearsal and reciprocity remain Qwen evidence. |
| Llama v4, N600 | KV−C0 M is +10.8229 [10.3746, 11.2529]; assigned-rule donor choices are 51.333% versus 0%. TAG gives high donor access without assigned-rule claiming, and cutting the link removes the assigned-rule donor choices in this sample. | STATIC L21/g0.7 is unmatched; route validation was false. V4 has seven unique arms, not eight independent conditions. |
| Llama v4, link-cut boundary | RF−C0 M_NOW is +1.9168 [1.6309, 2.2136], but M_WORD is **−0.3298 [−0.4948, −0.1622]**. RF still has 1% raw donor-word choices versus 0% in C0. | Do not call this a positive replication of the Robin-adjusted word residue, or infer that raw word contamination is absent. The two components of M move differently. |
| Original v5 Qwen provenance, N600 | Donor-only Robin conflict raises receiver-original Robin RULE errors from 0% to 49.92%; the prespecified logit contrast is +29.554 [28.175, 30.910]. | The effect is not confined to self questions. Donor-own WORD access gain is negative, although donor-Robin WORD specificity is strongly positive. Those are different diagnostics. |
| Amended Llama provenance, N600 | Robin RULE errors rise from 0% to 48.50%; primary contrast +10.859 [10.408, 11.305]. Both fields have positive donor-own and donor-Robin access contrasts. | The original N80 CAP gate failed. This is a separate, prospectively frozen, pilot-informed continuation, not a retroactively passing original-v5 study. |
| Source qualification in both studies | Ordinary-KV qualified SELF RULE accuracy is 18.92% in Qwen and 43.92% in Llama, versus 49.42% and 52.67% on the old START question. Qwen often answers with Robin's rule instead. | Fewer donor-own choices are not improved attribution. None of the fixed source-qualification interaction tests survives correction; this is not equivalence of wordings. |
| Amended Llama STATIC, N600 | KV−STATIC M is +10.1916 [9.7500, 10.6501]; assigned-rule donor choices 49.917% versus 0.583%. STATIC donor-rule accuracy is higher, 47.333% versus KV 42.083%. | Formal mean access-gain mismatch is **40.125%**, outside the frozen 25% band. STATIC has a small positive M−C0 and 8.75% current-rule donor choices; it is not universally inert. |

Sources: [v4 report](../results/v4/report.md), [v4 interpretation review](v4_interpretation_20261009.md), [provenance report](../results/v5/provenance_post_collection_20261012.md), [STATIC report](../results/v5/static_post_collection_20261012.md), and [continuation protocol](../protocol/PROTOCOL_V5_CONTINUATION.md). The new reports retain full choice distributions, raw score components, access diagnostics, CAP/format summaries, statistical families and input hashes.

## Priority 1: claims and omissions requiring correction

### 1. The model/study scope is obsolete throughout the paper

Locations: `paper/main.tex:63–87`; `sections/setup.tex:15–16,146–172`; `sections/account_and_discussion.tex:197–198`; `sections/appendix.tex:4–16,304–361`.

The abstract still describes one model, and the limitations explicitly say everything comes from one frozen model. The methods and study map cover only the original three protocols. Add the Llama checkpoint, native serialization/model identity, v4, original-v5 provenance and the amended continuations. Name the checkpoint and cohort wherever old rates are used. “Two copies of one model” remains correct within an episode; it does not describe the entire new study portfolio.

Do not make the opposite error of saying every finding replicated in two models. Llama did not repeat the open reports, closed subject-count report, strict third-person-card study, balanced rehearsal, Qwen dose curve or two-way pilot. Keep 97%, 83% and 94% explicitly Qwen/cohort-specific, including Figure 1.

### 2. The existing specificity claim is too strong given the new conflict test

Locations: `sections/results.tex:15–21`; `sections/introduction.tex:182–197`; `sections/setup.tex:40–46`; `sections/appendix_scorecard.tex:45`; `sections/account_and_discussion.tex:69–71,99–107`.

“The errors ... stay confined to ownership,” “It changed the owner,” and a general specificity “pass” cannot serve as the integrated conclusion. The original Robin control has the same truth on both cards, so accurate Robin answers did not test resistance to conflicting third-party content. The new donor-only conflict makes the receiver report the donor's Robin rule as the receiver-original Robin rule in approximately half of answers in both studies. Promote this result into the main text and replace the now-completed Robin “prediction” with its test and outcome.

The supported interpretation is broader source/role attribution failure under conflicting records. It remains compatible with role-conditioned readout interference and other retrieval accounts. There is no balanced self-conflict × Robin-conflict factorial, and self/Robin rehearsal differs, so the design does not measure privileged self vulnerability or prove identical mechanisms for self and third-party entries. The isolated manipulation changes only the donor's Robin field, but changes both its rule and word together.

### 3. “The route decides ownership, not access” overstates the available isolation

Locations: `sections/introduction.tex:157–166`; `sections/results.tex:103–113,177–181`; `sections/account_and_discussion.tex:38–43,79–107`; `paper/main.tex:76–85`.

Retain the original Qwen matched comparison with its exact scope. For Llama, report both the original unmatched STATIC result and the improved L16/g0.5 continuation. The new formal gains are KV 2.564291 and STATIC 1.535371 nats: the 40.125% relative gap fails the 25% criterion, despite coarse/independent-validity point gaps of 24.257%/23.425%. Higher STATIC donor-rule accuracy does not repair a logit-gain match, and the formal tolerance must not be changed after seeing the result.

Prefer “Content access does not determine correct attribution under the tested interfaces.” The new reversal of donor-rule accuracy ordering is informative, but a matched mean itself would still not equate all information, WORD access, capability costs or interface properties. Neither study isolates cache location from all other aspects of the route. Keep selected contrast estimation separate from whether the intended route interpretation was validated.

Absolute claims about STATIC also need restriction. The new STATIC arm yields 0.583% assigned-rule donor choices, M−C0 +0.6312 [0.4859, 0.7777], and 8.75% current-rule donor choices. “None” remains valid for the specified original Qwen matched sample, not all residual interventions.

### 4. Source-qualified questions require full choice distributions and a separate score

Locations: `sections/setup.tex:30–46,128–144`; `sections/appendix.tex:67–85,180–200`; prospective new provenance methods/results.

Add the source-qualified self/Robin and donor-record question stems, fixed physical candidates a/b/r/d, and the donor-only Robin mutation. The old global-assignment wording becomes ambiguous when cards disagree; the new receiver-original-record questions fix that truth. Use the prespecified conflict contrast on z(d)−z(r); do not reuse legacy M as if Robin were an untreated control.

The sentence “the Robin term removes any pull ... that is not about the self” (`setup.tex:140–141`) should instead say it subtracts the specified partner-versus-Robin margin on the Robin question. That subtraction does not universally identify a self-specific cause, and a change in M need not equal a change in actual donor-choice rate.

Show a four-category qualified SELF panel/table, not only b choices. Qwen ordinary KV reduces b choices under source wording but shifts much of the mass to r; its correct answers decrease. Llama accuracy also decreases. The manipulation changes a wording package, including explicit original source and named versus second-person subject. It does not identify which phrase matters, and nonsignificant interaction tests do not establish equivalence or a successful mitigation.

### 5. The original gate failures and prospective amendments must be visible

Locations: `sections/setup.tex:146–172`; `sections/appendix.tex:245–298,304–390`; future study map and statistics tables.

Preserve the original Llama provenance N80 ordinary-KV CAP loss of 5.625 points, and STATIC validity losses of 6.25 points for KV and 5.9375 for CF, against the original five-point criterion. They failed. The PI subsequently authorized named, prospectively frozen exceptions and fresh fixed N600 samples; the original protocol's formal slots remain unavailable. Do not label those failures technical only, erase them because new formal point losses are smaller, or describe the old N80 as independent validation of a tolerance chosen after seeing it.

The CF metadata-checker bug is a separate engineering fact: the checker reconstructed original rather than donor-mutated metadata for 320 CF rows. The repair changed neither model inputs nor scientific gates, and correcting it did not turn the old scientific CAP failure into a pass.

Retain separate inference layers: v4 primary/secondary Holm 5/4; original-v5 provenance Holm 2/6 with unavailable original Llama slots; amended Llama provenance its own conservative 2/6 families with unused slots; amended STATIC one primary and a separate Holm-2 secondary family. Unavailable slots have bookkeeping p=1 and no estimated effect. Do not apply p=1 to an available but unmatched STATIC contrast, pool these cohorts, or call all of them one unchanged two-model preregistration. Distinguish old signal/sample-size pilots from the later access/CAP/format-only parameter selection and fixed N600.

### 6. Link-cut residue is narrower and less uniform than the main heading suggests

Locations: `sections/results.tex:218–255`; `sections/appendix_further_results.tex:145–153`; `sections/account_and_discussion.tex:71–74,185–189`; Figure 5.

The Qwen same-state FULL/RF comparison supports an effect of answer-time access. The post-treatment reflection grouping does not establish that writing particular words into the reflection caused later errors. “What it wrote stays” and “carries the error forward” should be framed as association, with the unperformed reflection deletion intervention kept separate.

For Llama v4, show M_NOW and M_WORD separately: the adjusted NOW residue is positive, whereas the adjusted WORD contrast is negative despite a 1% raw donor-word rate. Report both M components where needed. Do not call the new collection a replication of this cut/reflection study; neither new continuation includes RF. Cutting a link was tested on these readouts, not as a validated safety mechanism for downstream decisions.

### 7. Capability and access must constrain the interpretation, not merely label a pass

Locations: `sections/results.tex:15–21`; `sections/appendix_scorecard.tex:45`; `sections/account_and_discussion.tex:197–226`; new formal quality table.

The Llama continuation formal CAP point drops are 4.667/4.958 points for ordinary/conflict provenance and 4.625/2.208 for KV/STATIC. Their linked-arm intervals can extend beyond five points; KV and STATIC have unequal costs. Neither a point-screen pass nor high label mass proves preserved general capability or attribution-specific impairment. The CAP bank is small, and a reported current rule is not a behavioral decision.

Report access by field and source. Qwen v5 donor-own WORD gain is −0.997 [−1.747, −0.222], while donor-Robin WORD specificity is +28.764 [27.606, 29.892]. These are compatible results; neither should replace the other. New STATIC matches no WORD-access target and has essentially no positive mean WORD-access gain. State which questions contribute to the format screen; v4/STATIC access-plus-CAP label mass is not automatically the all-question label mass.

### 8. A proposed mechanism must remain distinct from the newly tested prediction

Locations: `sections/account_and_discussion.tex:4–36,59–74,79–107`; `sections/setup.tex:62–78`; `sections/appendix_further_discussion.tex:38–54`.

The brain-bridge illustration and “two cards, one slot” account can stay as motivation and hypothesis. The new conflict result supports a prediction of that account but is not unique to it. No direct relocation, rerotation or layout intervention identifies position as the cause. Relocating a cache can alter RoPE attention and accessibility, so “prepend the cache” would not by itself isolate provenance. A future test would require access/capability controls and fixed comparison states.

An attention output has no explicit cache-origin field, but that does not prove its values contain no decodable origin information. “No explicit source field” is the supported implementation statement. Likewise, the deliberate overlap is a stress test, not an empirically established “hardest case.”

## Priority 2: framing, transparency and remaining text risks

1. **Novelty:** `introduction.tex:114–118` says no one has asked whose content the receiver thinks it holds. Narrow this to the specific contribution: controlled ground-truth original assignments, paired internal-state interventions and source-qualified conflicting records. The existing self-authorship/introspection and KV-communication literature makes an unqualified first-ever ownership question risky. The parent is separately checking the original references; this review is not a fresh citation-verification certificate.
2. **Human theories:** `introduction.tex:138–149,190–197` and `account_and_discussion.tex:109–152` can motivate functional analogues, but the model results do not refute Hirstein's claim about human experience or adjudicate IIT. Replace “Hirstein's prediction failed” with a finding about the specified functional counterpart under this interface. Preserve the explicit exclusion of consciousness and subject-count conclusions.
3. **Reports and awareness:** `results.tex:64–101` and `appendix_coding.tex:4–22,78–86` document a Qwen prompt and post hoc machine coding. High denial rates without a link, no positive detection control, no human rater and hypothesis-aware semantic coding preclude “unaware,” “did not notice” or “self-report cannot detect it.” The appendix is admirably explicit; the headline prose should keep that scope.
4. **Practical metric claim:** `account_and_discussion.tex:175–177` says neither an accuracy metric nor a transfer metric would show the failure. Original-assignment accuracy directly shows it. Say donor-access/transfer accuracy alone would miss it; correct original attribution should be evaluated separately.
5. **Evidence chronology and availability:** the study map must distinguish “original Qwen main sample” from later formal cohorts, retain the N80 reciprocity miss and all original gate failures, and state archived prospective freezes rather than imply an external registry. Update the date, model/software appendix and actual public artifact inventory. Do not promise that all raw files/codebooks are already public if they are still on request or private local data. Rebuild the arXiv package only after the manuscript and figure evidence are settled.

## Restrained main-text and figure plan

Preserve the existing compact scientific diagrams, illustrations, colors and panel style. This is an evidence-priority revision, not a visual redesign. A useful main-text sequence is: **original attribution changes → replication and third-party conflict → access/attribution dissociation → cut-link boundaries → interpretation**. Keep the small two-way pilot as a scoped exploratory extension, rather than the culminating evidence for the new two-model conclusion.

| Existing figure | Recommended role and minimal substantive change |
|---|---|
| Figure 1, motivation/tour | Keep the brain-bridge illustration and selected Qwen outputs. Label every numerical vignette by model, cohort and evidence level. The report and conditional-reflection examples are not two-model results. |
| Figure 2, setup | Preserve fixed donor memory and independent saved-state branches. Add a compact original-versus-conflict card schematic or adjacent table with fixed a/b/r/d and source-qualified readouts; leave detailed qid/template identity to the appendix. |
| Figure 3, original claiming | Retain the Qwen dose/open-report panels. Add a compact, explicitly cohort-labeled w1 checkpoint comparison, or place it beside the new provenance figure. Do not compare Qwen w2 and Llama w1 as a model effect. |
| New provenance figure | Give this main-text space: one source-conflict schematic, RULE/WORD receiver-Robin error changes, and four-category qualified SELF choices. Separate original Qwen and amended Llama labels. This prevents “fewer donor choices” from being mistaken for correction. |
| Figure 4, interfaces | Separate the original Qwen matched cohort from the two Llama STATIC cohorts. Show matching gains and hit rates as different quantities, with “formal match not retained” visible for the new Llama comparison. Identify text-message versus matched-KV cohorts explicitly; visual proximity must not imply every plotted point belongs to one paired sample. |
| Figure 5, link cut | Keep the selected Qwen example and post hoc reflection grouping, labeled accordingly. Add or summarize the Llama v4 NOW/WORD distinction; do not hide the negative adjusted WORD contrast. |
| Figure 6, reciprocity | Preserve the original compact pilot plot and its missed primary threshold. If main-text space is tight, move it intact to the appendix to make room for the two-model provenance figure, rather than squeezing all new evidence into tiny labels. No new reciprocity inference follows from the one-way continuations. |

The appendix should carry one consolidated model/study/arm/endpoint/evidence-status table and all prespecified families, rather than blending new conditions into old tables without version labels. The present appendix already does useful work on failed/reversed contrasts, coding limitations and paired dependence; preserve it.

## What remains unestablished

The completed data do not separate a specifically self-related mechanism from general role-indexed conflicting-record interference; locate the cause at rotary positions; establish equal information across routes; demonstrate capability equivalence; show that reflection wording mediates residue; test reliable anomaly detection; or replicate reciprocity in Llama. These are limits on claims, not a demand to run every possible supplement. If the paper keeps the bounded empirical story above, reporting the missing mechanisms candidly is sufficient. If it instead retains a strong causal “self defaults to mine because of cache position” thesis, the current results do not close that gap.

## Review provenance

The reviewed PDF SHA256 is `3146a3723df408d4914cb36a939b51ff754fce6b6fc004808ed46771fd535c0f`; this review did not regenerate it or conduct a new full visual/citation audit. Main TeX SHA256 is `1f9a7fe729dc204e0a98666c37ad33147e6dc5a5d7b237ed88f6756bea396bca`. Final reviewed result JSONs: provenance `7628514c65fe830c3f5a5984fc798fd14469690cdf9c684f3174c092360ac269`; STATIC `de1e436c93b0f36487c74c35811cb65d4d28c6e2685b1d011d1ace2663a460c5`.

Final provenance-report correction reviewed: the external continuation wrapper did save Llama's `v5_continuation_summary.json` despite `mb.run` having `post=[]`. The revised report compares that actual saved summary, including its continuation envelope and separate amended families, with the recomputation, and reports agreement alongside the Qwen comparison. This corrects the earlier report's claim that no saved Llama summary existed; it does not change the substantive results or this audit's interpretation. The final JSON hash above was independently verified.

A separate priority operational review checked the current-target final-destruction helper, its nine pinned evidence files and four mocked success/refusal paths. No provider, SSH, GPU, destruction or process action was performed by this reviewer. The parent owns the actual authorized teardown, repository tests, integration and commit. This review makes no venue-acceptance prediction.
