# Review of the proposed reciprocal core study

Date: 2026-10-12. Scope: local experimental design only, not protocol freeze, runtime acceptance or authorization to spend. The reviewed proposal is `docs/protocol/PROTOCOL_V6_RECIPROCAL_DRAFT.md`. Existing frozen protocols and datasets were not changed.

## Review process

Codex prepared the proposal and assigned three independent read-only reviews: scientific task/construct validity, causal/statistical identification, and runtime/replay feasibility. Reviewers inspected the draft and relevant historical code/protocol evidence. The lead agent integrated the revisions below; reviewers did not edit the lead agent's claimed files. This document summarizes those reviews rather than representing three new experiments or a hardware test.

## Main findings and resolutions

| Finding | Resolution in the proposal |
|---|---|
| An event before all interaction would test connection startup, not disruption of an ongoing pair. | Add a common 32-token live warm-up, then the native private event and 64-token comparison period. All five arms are post-event interventions with the same prior pair history. |
| A full private request table necessarily includes the new request symbol. | Withhold the new active selection, not the symbol's existence. Retain the warning that generated KV states can encode the whole table. |
| Average old/new accuracy could show path necessity entirely because of the old request. | Use changed-request accuracy for all three primary R path comparisons. An explicit counterexample is included in the offline checks. |
| Repeating an old response can be an artificially weak comparison; random switching among new answers can look better. | Add a prespecified mapping-specific score at the cut-window token-32 probe: +1 correct new, -0.5 each other non-old response, 0 old/invalid. Test against zero in the primary family; report absolute accuracy separately. |
| A held-window diagnostic might obtain and compute the answer only when interrogated. | Use a cut-window R response probe, without restating the active request. Interpret it as a response recoverable from the state, not direct proof of what was sent or localization of every computation. |
| The old one-side-answers/other-side-reflects runner cannot produce a common pair decision. | Require paired sealed probes for actions, response and assignment audits; both decisions are committed before either output is visible. Questions/answers are never exported. |
| Actual invalid output and four-label conditional argmax are different measurements. | Use the unmasked full-vocabulary greedy token for submitted actions and correctness; retain legal-label normalized probabilities separately. Archive the full-vocabulary top token and legal mass. |
| A wrong fact and wrong goal can yield the same action on a Latin square. | Retain ordinary action accuracy, but use a fact-complete fresh action board for primary G goal-control measures. Do not condition analysis on correct access. |
| Rearranging old action words could preserve token/position priming. | The fresh board uses a separate vocabulary, independent goal-to-action permutation and option order, held identical across episode branches. |
| Assignment contrasts should correspond to behavioral contrasts. | Pair J's latest-assignment forward interaction with cross-goal control and I's latest-assignment replay interaction with feedback contribution. Report original records descriptively. |
| Twenty-five episodes per goal triple cannot be internally split exactly by two sides and four fact pairs. | Specify overall exact balance and at most one count difference per within-triple joint cell; enumerate the proposed 600-episode allocation. |
| A formal post-event L00 has already experienced the common bridge and cannot screen total capability loss. | Admission uses a separate never-linked, full-duration native control from the beginning. |
| Technical missingness could lead to convenient complete-case inference. | A missing required component makes its formal contrast unavailable with p=1 in the retained family; bounds and complete-case summaries are descriptive. |
| The text reference could accidentally become sequential or omit consumption of its last messages. | Generate both sides from round-start states, exchange together, and consume the final round before measurement. Keep route differences descriptive. |
| Special tokens, pending-token caches, native turns and tape boundaries were underspecified. | Define committed-token ticks, one-tick delay, phase-specific windows, end-of-turn processing, fixed-budget reflection policy, S32/S64 snapshots and same-update replay acceptance. Native/tokenizer implementation remains required. |

The causal/statistical review accepted four R endpoints and two G contrasts per checkpoint in one Holm-12 primary family, with the four aligned assignment interactions in a Holm-4 secondary family. The engineering review found the architecture feasible in principle, but not executable through the old runner unchanged. No reviewer certified model performance, actual transfer strength or a paid runtime estimate.

A final consistency pass accepted the revised design after three wording clarifications: preserve primary status for R's cut-window Q, define pre-delimiter S32/S64 snapshots and independent probe handling of pending tokens, and restrict baseline correctness requirements to objectively scored full-information questions. Endorsement has format checks only; a no-link comprehension baseline never requires an unseen partner fact. The independent task reviewer also reproduced the offline JSON exactly. All three clarifications are incorporated in the delivered draft.

## Offline evidence

`docs/protocol/v6_design_checks/check_design.py` ran without importing torch or a model. Its saved JSON was reproduced byte-for-byte. Checks cover 6,912 two-map/request combinations, 2,304 goal/fact/fresh-board cases, global sample balance, a one-way bypass, nonspecific answer switching, an echo counterexample, an averaged-estimand counterexample and planned workload counts. The precision grid uses a disclosed normal approximation and assumed variances, not observed effects.

The repository offline suite passed: **428 passed, 5 skipped**. These tests protect existing code; they do not validate an unimplemented v6 runtime. The proposal and checks contain no result-based parameter selection, new formal data, credentials or live instance binding.

## Remaining work before any executable freeze

- PI ratification of the proposed scientific scope, N and admission rules; no new research settings are approved merely by writing this draft.
- Complete episode/material generation, literal tokenizer-specific prompts and candidate IDs, immutable disjoint split manifests, and source hashes.
- Implement and independently review native event scheduling, eligible generated-position masks, replay tapes, paired sealed readouts, exact resume and planned analysis.
- Run the analysis implementation on synthetic data, including null, bypass, echo, random-switch and goal-contamination alternatives.
- Obtain separate authorization for bounded GPU acceptance and a total spending cap; then verify native numerical behavior, replay, task solvability, access, capability, speed and backups before formal collection.

The design's scientific interpretation stays explicit: reciprocal influence travels through information. The proposed comparison isolates whether that information must adapt to the current partner, not a separate effect of “being alive” at identical receiver inputs. Behavioral influence, assignment errors and subjective experience are not interchangeable conclusions.
