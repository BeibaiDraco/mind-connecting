# V6 prospective admission and execution addendum

Date: 2026-10-12. Status: proposed for the PI's final package review, not a
scientific freeze. Implements the unresolved details of
`PROTOCOL_V6_CONTINUOUS_DRAFT.md` section 9 without changing the substantive
six-round hypotheses or reusing any previous capability exception.

The PI has authorized preparing this work and subsequently renting a new
instance and running the experiments. This document makes the remaining
admission choices concrete. Neither the new numerical spending ceiling nor
these previously unspecified choices is represented as already ratified.

## Fixed study and admission sequence

Keep the two existing pinned model profiles as separate same-model pairs.
Proposed formal N240 per model, material-selected N60 text subset, six rounds,
64 work tokens, 16 preparation tokens and a 16-token generated window remain
unchanged. The primary and secondary multiplicity families remain 22 and four.
No new model, training, search beyond the three gains, outcome-based stopping or
scope adaptation is introduced.

For each profile, run real-checkpoint engineering acceptance and a separate
full-clock smoke plus exact no-op resume. Then collect baseline N60, all three
disjoint neutral calibration N40 cohorts (gains 0.25, 0.5, 1), one independent
validation N80 at the selected gain, and formal N240 only if all requirements
pass. Select the smallest passing gain only after all three candidate datasets
are complete and usable. An independent validation failure ends that model's
formal path; it does not authorize testing a runner-up or enlarging a cohort.
The other model's predeclared path remains independent. Engineering smoke
success is a technical claim and never a scientific admission result.

## Two neutral streams per episode and policy

The same neutral episode has two independent paired histories, both lasting six
rounds. Neither contains causal pulse/goal branches or attribution measurements.

**Capability stream.** Use the draft private-device task and continue through
the participants' actual ordinary actions. After each round's work, independent
discarded clones answer (a) a full-information action question that explicitly
supplies the current authorized own goal and current partner beacon, and (b)
three questions from the unchanged 18-item historical CAP bank. Every bank item
occurs exactly once per base episode and physical side. Diagnostic answers never
enter the actual continuing history. The ordinary action is separately sealed,
consumed and allowed to affect the device world. Its correctness is descriptive,
not a selection metric.

The baseline additionally asks original-assignment and latest-assignment
comprehension on separate clones, supplying the relevant original/current own
record in the question. These are factual comprehension checks, not self/partner
influence measurements. They do not enter calibration or validation selection.

**Fresh-fact stream.** At each round boundary, each side receives one fresh
private marker from four named alternatives. Per-round/side marker columns are
balanced and independently shuffled; no within-episode cycle predicts the next
marker. After the full work budget, a discarded clone is asked for the partner's
current marker. A separate own-marker answer is the actual consumed continuation
token, including any invalid token and its native recovery. No goals, device
pulses or formal outcomes enter this stream. In baseline only, partner retrieval
is supplied the relevant partner record; calibration/validation retrieval is not.

Baseline observes never-linked OFF. Each calibration/validation episode observes
paired OFF and LIVE with identical episode material. OFF is unconnected from
initialization. Each policy uses independent states; no linked warm-up is shared
with OFF. Clocks, native action policy and generated-window eligibility match
the main implementation. Model generations alone carry cross-participant facts.

## Aggregation and precise predicates

Average each question family within the episode and physical side. CAP averages
all 18 items; task and fact families average their six rounds. Resample the
entire paired episode vector, separately reporting each physical side. Use
10,000 paired bootstrap draws, seed 0, and linear percentile quantiles. The
operational bounds are marginal, not simultaneous equivalence claims.

Baseline N60 requires each side's mean full-information action, supplied original
assignment and supplied latest assignment accuracy to be at least 0.90. CAP and
record-supplied fact accuracy are retained descriptively; this addendum does not
silently introduce additional baseline accuracy floors.

For both N40 candidate admission and independent N80 validation, each side must
satisfy all of:

1. LIVE partner-marker accuracy is at least 0.75, and the 5th percentile of the
   paired episode-bootstrap LIVE-minus-OFF access difference is strictly above 0.
2. Separately for full-information task and historical CAP accuracy, the 95th
   percentile of paired OFF-minus-LIVE loss is at most 0.05.
3. For every readout family and each observed policy, mean legal-label mass is
   at least 0.90. Within each family/side, mean OFF-minus-LIVE mass loss is at
   most 0.05. These format predicates use point estimates, not new precision
   bounds. Pooling easy CAP questions with action/fact questions is forbidden.

The five shared format families are full-information task, CAP, actual ordinary
action, partner fact and actual own-fact continuation. Baseline also checks the
two supplied assignment families. Equality passes the non-strict bounds; zero
does not pass the strictly positive access lower bound. Using the same predicate
at N40 and N80, and keeping format families separate, are explicit prospective
recommendations resolving the former ambiguity. They are not relabeled as rules
that were already present in the earlier draft.

Comparisons use a fixed 1e-12 arithmetic tolerance solely for floating-point
roundoff; the strict positive lower bound must exceed 1e-12. This does not add a
scientific margin or permit a material relaxation of a failed threshold.

An incomplete, smoke, synthetic, source-mismatched or unratified dataset cannot
produce a usable gate or selected gain. Synthetic vectors may exercise numerical
predicates only. Recompute predecessors from raw source-bound data; a saved
`pass=true` is insufficient. Compare task-core identities and contents across
every ancestor cohort, not only immediate predecessors. No failed observation
is removed or filled with zero, and no replacement episode is introduced.

## Execution, persistence and technical failures

Every stage plan fixes model, source, actual tokenizer manifests, material file,
gain, clocks, exact episode count, text subset and prerequisites before loading
weights or writing a run. The separately recorded PI approval binds the complete
source, admission contract and exact prepared material catalog (including sample
counts, text subset, clocks and candidate gains). A different same-stage cohort
requires a new prospective approval; it cannot replace a failed cohort under the
existing grant. Financial and machine details live outside the
repository; no historical instance or v5 budget is reused.

Each native stage retains actual top tokens and full native readout evidence.
Successful records are immutable. One exact-identity episode retry is allowed;
every retained success and artifact must match exactly. Orphan/torn archives
fail closed rather than being overwritten. Completed no-op resume rechecks
source, every expected record and file hash before model loading and writes no
run bytes. An external resume receipt can record that verification.

Keep all four pair checkpoints and twelve tapes per main episode. Do not silently
delete, subsample, quantize or replace them with inferred states. Real acceptance
must independently compare no-link native outputs/caches, test foreign zero gain,
both evaluation orders, two-round replay, persisted pair/tape restoration and
the finite recovery categories. Tiny random-model tests are additional engineering
tests; they do not replace the pinned-checkpoint acceptance.

Live admission uses current wall time, the exact new instance binding, refreshed
dual budget-guard observations, verified backup evidence, measured free space and
an unchanged financial start. Explicit historical-time audits are marked
historical-only and cannot authorize new execution. Each attempt archives the
original admitted evidence bytes so a completed stage can be audited after its
short-lived operational proofs expire. A kernel failure or missing guard is a
technical stop, not a negative scientific observation.

Acceptance and smoke use the initial allowance. All later stages require a
measured projection of the whole approved remaining workload fitting the total
cap and shutdown reserve. A single cumulative clock includes installation, idle
time and bandwidth. Before any unattended run, the external supervisor must be
reviewed and tested for fresh proof publication, backup verification, exact-target
stop and actual provider-state confirmation. A stage-runner API is not itself a
cloud resource supervisor.

Periodic archival uses bounded incremental copies and verification of additions.
At stage completion, copy and bind the closed remote inventory, confirm actual
provider stop, then independently rehash all final local backup bytes. An
incrementally verified prefix is not final-backup success. This avoids charging
GPU idle time while hundreds of GiB are rehashed on the SD volume, without
omitting the final complete verification. Storage/transfer forecasts must include
both the incremental copy rate and the full local verification time.

## Storage and proposed financial boundary

Tokenizer-only legal-oracle estimates put raw formal snapshot/tape payload near
229.39 GiB for Qwen and 208.83 GiB for Llama, before filesystem/archive overhead,
models and engineering runs. These are planning estimates, not native measurements.
Use at least 650 GiB allocated remote disk and reserve 600 GiB on the mounted
backup SD volume, then verify the measured full-workload forecast before formal
collection. The Mac internal disk is not a destination for these archives.

The new proposed ceiling is USD100 total, with at most USD12 for initial
acceptance and smoke, an hourly ceiling of USD1.60 including allocated disk,
and a five-minute shutdown reserve. Prefer transfer tariffs no greater than
USD10/TB in either direction and account explicitly for all expected transfers.
This is a new proposed budget, not the old v5 allowance. Current quotes and
credit must be refreshed before renting; any automatic recharge setting must
not be changed. No estimated runtime is promised until native timing, hashing,
cache growth and full backup have been measured.
