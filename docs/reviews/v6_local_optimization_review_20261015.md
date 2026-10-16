# Independent local V6 optimization review — 2026-10-15

Scope: the new `v6_batch*`, `v6_state_guard`, `v6_archive_store` and
`v6_efficiency_trial` modules and their tests. Historical runtime, protocols,
scientific inputs, records and private execution controllers were not edited.
The implementation author is Codex/root; the independent reviewer is the
separate existing `v6_perf_review` agent. This document records its completed
read-only reports and the implementation author's final verification.

## Findings closed

The first review found five concrete weaknesses: cohort completion did not
verify its identity hash; Python metadata equality conflated Boolean/numeric
values and signed zero; archive manifests lacked external binding; pack/restore
block limits disagreed; and attention-mask validation could silently accept
malformed finite or NaN exclusion biases. The fixes bind completion/coverage,
serialize metadata exactly, require an external manifest SHA256, align the
two-million-block ceiling, and validate exact allowed/excluded mask values.

Review also identified a possible cross-lane numerical channel through shapes
chosen from another lane's history/window length. The new candidate freezes
physical prefix/foreign/query capacities and retains logical positions/masks.
CPU independent-oracle checks and written CUDA other-lane perturbation tests
cover the contract; only hardware can establish CUDA isolation.

A second review found five further issues. Scalar preparation/TEXT generation
and commitment incorrectly used padded prefill; they now enter the common T1
decode boundary. Terminal success preceded a final lease check; measurement is
now retained before the final check, terminal publication is last, and any failure
invalidates completion. The microcomparison checked only the last position;
it now captures every real position while preserving original native grouping.
Each completed micro-phase is saved before its next lease check. Every archive
restore has checks and durable progress inside its loop.

The final independent report found all ten reported weaknesses closed and no
remaining blocker for the **inert engineering package**. It independently ran
91 focused offline tests successfully. The reviewer did not edit files, execute
CUDA, contact a provider or grant scientific/numerical admission.

## Verification and limits

The full offline suite passed1206 tests, with9 skipped and1 GPU test deselected.
Synthetic full and neutral schedules match their unchanged scalar reference,
including invalid-answer trajectories, exact unchanged Replay and recorded
causal timing. These are semantic tests, not real-model equivalence evidence.
Both pinned tokenizers pass the local fixed-material audits. All16 retained
Llama engineering archives have an independently checked lossless round trip;
the external-manifest-bound restore was also independently rehashed.

CUDA tests remain unrun. The full-model numerical tolerance is not adopted,
and fixed padding, compilation, memory demand and native throughput remain
hardware risks. The microtrace adds output-head calls and CPU copies, so its
timing must not be used as production throughput. Whole-plan affordability is
unknown. No research setting, gain selection, formal sample, financial ceiling,
source freeze, old failure or missing-backup obligation was changed.

The new trial proposal is USD8/four hours **pending new approval** inside the
original cumulativeUSD100; it cannot reuse the completed prior exception.
Private financial/lease/controller binding must be reviewed before hardware.
No formal or scientific neutral experiment may start automatically.
