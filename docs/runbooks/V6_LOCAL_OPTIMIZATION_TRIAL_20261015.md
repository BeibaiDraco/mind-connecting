# V6 local optimization implementation and next engineering trial

Status: local implementation verified; CUDA behavior and throughput unmeasured.
This is an engineering proposal, not a protocol amendment or paid launch grant.
The PI requested completing local work and reporting the next test's time/cost,
while continuing to prohibit formal collection.

## Implemented priorities

1. `v6_batch_native.py` ingests known question tokens in causal chunks, fuses
   weighted own/foreign attention, and consumes independent episodes together.
   Generated tokens still advance one tick at a time. The candidate cohort is
   two episodes/four physical sides; lane order never depends on responses.
2. `v6_batch.py` implements the complete six-round interaction schedule,
   natural controls, FRESH shadow, pulse cuts, goal branches, separately
   recomputed unchanged Replay and the predeclared scalar TEXT subset.
   `v6_batch_neutral.py` covers the unchanged neutral workload as engineering
   fixtures only. No selector or production dispatch imports these candidates.
3. `v6_state_guard.py` compares all protected metadata and tensor bytes on the
   device using privately owned snapshots. It preserves signed-zero differences,
   does not sample bytes, and leaves public SHA256/export/archive checks intact.
4. `v6_archive_store.py` creates a separate bounded block-deduplicated,
   losslessly compressed container. Restoration requires an externally retained
   manifest SHA256 and verifies every container, block and original file hash.
   It does not unpickle, alter/delete raw files, or change scientific artifacts.
5. `v6_efficiency_trial.py` supplies inert source-bound preparation and explicitly
   guarded individual test cases. The CLI can only prepare a package. No rental,
   start, model download/load, automatic retry, gate selection or scientific
   continuation is implemented in this package.

Scratch shapes are fixed: prefix capacity4096, foreign capacity16, prefill
chunk16 and generated/committed-token chunk1. Logical position IDs retain each
history's true length. Padding is masked and removed before publication; a
different lane's length/window must not become a numerical communication route.
Every real input position retains hidden/full-vocabulary finite checks. All new
states validate before any lane is published. Scalar preparation and TEXT
generation/commitment also use chunk1. Fixed padding has a real cost; its net
benefit is a hardware question, not an established speedup.

Immutable cohort receipts bind materials, source, backend, lane/TEXT membership,
runtime and exact per-lane record keys. Complete receipts support read-only
no-op reopening. Partial cohorts are preserved and cannot automatically resume
or reassign lanes; such recovery is outside this test's authority.

## Local evidence

- Full offline suite:1206 passed,9 skipped,1 GPU test deselected. No local torch
  installation or model execution. New CUDA tests are written, not passed.
- Synthetic full schedules at widths1/2/4 and multiple gains reproduce original
  records, tape/checkpoint identities and tick audits, including invalid answers.
  Neutral stage/gain fixtures reproduce the original scheduler's records.
- Negative tests cover parent mutation, incomplete publication, coverage errors,
  stale source/identity, corrupted containers, renamed manifests, metadata type
  and signed-zero changes, earlier-position greedy disagreement, and late
  deadline failure without false completion.
- Both actual local tokenizers pass1024 combined native answer-prefix checks and
  4096 label-appending checks across the fixed engineering materials. These
  establish serialization only, not model task performance.
- All16 retained Llama candidate full-task archives were packed/restored as an
  additional local copy. Original948,075,974 bytes became513,011,629 bytes including
  container/index/reference/manifest overhead:45.889% less storage. Pack18.762s,
  initial restore7.631s, independent file rehash0.919s on this machine/SD card.
  A further restore using the external manifest hash and independent rehash
  passed in9.576s. This one fixture does not establish whole-run compression or
  GPU speed. Raw originals remain untouched.

Local evidence is under `/private/tmp/mb-v6-local-optimization-20261015/` and
`/Volumes/VERBATIM SD/mind-connecting-data/v6/offline-efficiency-20261015/`.
The latter's externally bound container manifest is
`55278ff7812ea713b71b48adb5e8413dba05835f77ca9ea11836b157166c528f`.
An independent agent reviewed the core implementation and failure paths; see
`docs/reviews/v6_local_optimization_review_20261015.md`.

The structured-question/history capacity audit bounds the fixed engineering
materials at1430 tokens for Qwen and1457 for Llama, including maximum recovery
suffixes, below4096. Generated TEXT can expand when decoded
and retokenized; a pathological overflow must stop and preserve the case, never
truncate text or silently select a different capacity/kernel.

## Next CUDA trial: proposed scope and bounds

Planning allowance:2–4 elapsed hours, maximum4 hours from restore intent through
verified actual stop. Proposed new spending ceilingUSD8, inside the original
cumulativeUSD100, retaining all prior compute/storage/transfer charges. At the
USD1.60/hour ceiling, four hours costUSD6.40; USD1.60 remains for noncompute
charges/reserves. The previous observed rateUSD1.47074/hour would giveUSD5.88
for four compute hours, but is not a fresh quote. Two hours would beUSD3.20 at
the ceiling, before other charges. Required forecasted fees must fit before
starting; the reserve is not a guarantee of provider bandwidth/storage prices.

Worker limit3h15m; reserve45m for copying, independent rehash and actual stop.
An earlier original total-session limit takes precedence. The previous named
USD8/four-hour benchmark is closed and does not authorize this new trial. No
deadline, start, spending limit or stopped-time credit has been reset.

The sequence is fixed; stop on an invariant failure, nonfinite result, any
teacher-forced greedy disagreement, insufficient resources, lease or budget
limit. No alternative kernel/gain is selected after a failed comparison.

| Step | What it establishes | Planning time, not a measurement |
| --- | --- | --- |
| Fresh exact-instance/finance/guard admission and missing-evidence recovery | Safe new bounded execution; original61 raw files/2.529GB remain a recovery obligation | 15–30min |
| Tiny Qwen/Llama CUDA tests plus compilation | FP64 operator oracle, causal masks, foreign isolation, changed-other-lane isolation, atomic publication, true scalar decode, finite checks | 15–40min |
| Both fixed real models, all four gains, common-input traces | Every real input position's greedy token, hidden/logit deviations and complete final KV; no scientific tolerance is adopted | 15–30min |
| Short repeat, full two-episode cohort with one TEXT episode, two neutral fixtures per model | Complete clock/workload, strict same-backend Replay, archives/restore, record no-op, measured candidate throughput | 45–90min if the candidate is useful |
| Closure | Seal evidence, copy, independently rehash, verify provider actual stop and retire guards | Up to reserved45min |

These planning ranges can overlap and do not override the hard lifecycle cap.
Compilation or full cases may exceed the estimate; then stop with partial
evidence. Neither a timeout nor partial success licenses a larger run.

The short case still traverses every condition/branch but uses the explicitly
engineering-only2-work-token/1-preparation-token clock. The full case uses the
original64/16 clock and all six rounds. Materials are named engineering fixtures,
including the earlier engineering reference fixture; none is a scientific sample.
Native/neutral conditions, actual answer commitment/recovery, sample sizes,
readouts and original research gates remain unchanged.

The teacher-forced trace deliberately adds scalar output-head calls and CPU
copies to observe every position. Its timing is diagnostic only. Only complete
full/neutral case receipts for **both real checkpoints**, with backup and shutdown
proof, can support a new workload projection. The full case has one TEXT episode
per two episodes; report that sampling mix and either measure TEXT separately or
use an explicit conservative overhead estimate for the formal25% TEXT fraction.
Separate model loading/compile, compute plus raw archive writes, restore/hash,
transfer and shutdown; do not multiply component speedups or call them free.

## Remaining hardware/operational work

The private paid launcher is deliberately unarmed. Before any future launch,
bind this exact source package and the original financial session into fresh
reviewed local/remote guards and an engineering-only controller; verify current
instance identity/availability, actual rate, credit, remaining total allowance,
disk/transfer capacity and shutdown capability. The old protected benchmark's
raw backup is incomplete; preserve its stopped disk and recover only the missing
inventory-bound files. Do not reuse historical connections, guards or controllers.
Final acceptance requires independent SD rehash and service-provider actual-stop
evidence, not a successful stop request or a measurement receipt.

No numerical scientific admission or formal continuation is granted. Fusion and
batching can change BF16 rounding and trajectories despite equivalent attention
algebra. A prospective numerical amendment and renewed native/neutral admission
would be separate decisions after engineering evidence. An optimistic2–4x whole
workload speedup remains a hypothesis; no new GPU-hours or affordability claim
is justified by the local tests or storage result.
