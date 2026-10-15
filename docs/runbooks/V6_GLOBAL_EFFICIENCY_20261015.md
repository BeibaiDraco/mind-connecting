# V6 global efficiency audit

2026-10-15, Codex. Offline engineering assessment; no new scientific decision,
numerical acceptance, paid allowance, provider action or model execution.

## Optimize the complete unit of work

Measure completed, integrity-checked episodes per billed hour and per dollar.
Include warm-up, compilation, scientific gates, archiving, final transfer and
verified shutdown. Faster isolated attention, fewer wall-clock hours on several
GPUs, and lower total GPU-hours are different outcomes.

The current illustrative two-model projection is 251.52 compute hours, including
194.52 formal hours (77%). It comes from one complete engineering example per
workload/model, not a runtime distribution. Baseline/calibration/validation remain
necessary. Changing a pessimistic financial projection is not a physical speedup.
See `../reviews/v6_benchmark_closure_20261015.md` for the measured inputs.

The full Qwen example spent about 836 seconds in probes and 627 seconds in
generated steps out of 1683 seconds. Digest timing of 197 seconds overlaps these
operations. These host timers are not an additive CUDA profile. Still, they
identify two large execution paths that need different treatment:

| Path | Priority | Scientific invariant |
|---|---|---|
| Known readout text | Causal chunked prefill; homogeneous question cohorts | Same text, held donor window, positions, full readouts and per-position finite checks |
| Recurrent generation | Fixed cohorts of independent pairs; fused attention and fewer host observations per tick | Actual A/B tokens, t-1 visibility, simultaneous publication and six-round histories |
| Integrity checks | Prototype device-side full-byte comparison for temporary mutation guards | Every protected boundary still detects any state/metadata change |
| Archives | Lossless block sharing and bounded CPU staging | Every logical artifact and its exact bytes remain independently recoverable |
| Operations | Resident model within an authorized stage, incremental transfers, measured shutdown reserve | Original gates, backups, accounting and stop authority remain |

Chunked prefill cannot be applied to unknown future live tokens. A/B in one pair
must not advance using the partner's new state from the same tick. Pair cohorts
must retain fixed membership, lane order, numerical shapes and recovery rules.
Diagnostic questions sharing a parent can be evaluated in separate lanes; the
continuation answers must still be sealed before either is committed. Deferred
diagnostics need immutable owned snapshots and cannot become inputs to the world.

The existing isolated prototype implements neither the full cohort scheduler nor
its resume contract. Implement those only after operator/model feasibility. A
general inference-server migration is not the first step: the custom foreign-KV
path and exact Replay/ownership contracts would still require integration.

## New opportunity: avoid full host transfers for temporary equality checks

`EpisodeRunner._read` hashes the continuing state before and after each probe;
`NativeBackend.digest` sends all cached K/V, logits and hidden bytes to the CPU.
Some of these digest strings serve only as temporary equality guards.

A separate prototype could own a private GPU reference snapshot and compare all
original tensor bytes on-device at each existing protected boundary, returning
one combined result plus independently checked metadata. It must check tensor
count, shape, dtype, device, logical history and ownership; use byte equality,
not approximate or ordinary floating-point equality. Detect a one-bit change,
signed-zero change, replaced/missing tensor, metadata mutation and aliasing of
the reference. The reference cannot be a view of the mutable parent. Memory
pressure, copy cost and extra kernels must be included in throughput.

This does not replace published state/export digests, sealed-answer checks,
archive hashes, independent Replay, or external backup verification. Preserve
the old check boundaries and failure/publication behavior. Retain the current
implementation if a reference cannot be safely owned or if the complete path is
slower. No blanket pointer/version-based hash memoization or removal of checks.

Even eliminating the entire measured 197-second digest interval would not yield
a several-fold whole-episode improvement. This is a supporting optimization,
potentially more useful after the large decoder paths improve. It is currently
a proposal, with no CUDA implementation or performance result.

## New measured evidence: substantial repeated archive bytes

A read-only scan of the locally retained Llama candidate `full_with_text`
engineering episode rechecked all 16 archive file sizes and original SHA256s.
It inspected ZIP tensor-storage bytes without importing torch, unpickling a
model, decoding readouts, or reading scientific effects. For each ZIP storage,
it split bytes into consecutive 1024-byte blocks, keyed by length and SHA256.

| Quantity | Bytes |
|---|---:|
| Total tensor payload | 938,450,944 |
| Unique block payload by SHA256 | 555,169,792 |
| Repeated block payload | 383,281,152 |
| Repeated fraction | 40.84% |

There were 542,158 distinct blocks and approximately 916,456 block references.
The detailed local audit is
`/private/tmp/mb-v6-global-efficiency-20261015/archive_block_audit.json`.
This is one Llama engineering fixture, not a Qwen or whole-experiment estimate.
Index/reference/container costs are excluded. Hash matches alone are not an
implemented codec or a verified restore. The historic missing remote benchmark
backup remains missing; this scan does not repair it.

Next offline check: prototype an external lossless archive container, retaining
all original metadata and byte ordering, restore every original file, and require
its original SHA256 and length to match. Include interrupted writes, damaged
blocks, shared-block dependencies, bounded memory, read throughput, index size
and final transfer size. Keep the original files; do not replace/delete them.
Use actual restored bytes to establish compression savings before projecting
the roughly 477.8 GB original package. Larger or content-defined blocks may have
different savings and index cost; do not assume the 1 KB diagnostic is optimal.

Owned CPU staging can overlap hashing/storage with subsequent GPU work only
inside a bounded queue and the authorized stage. Snapshot capture itself must
be complete and immutable before the source is reused. Failed transfers must
not falsely mark closure; a pending queue must never delay the hard stop.
No change to the requirement for actual stop and verified stage backup is made.

## Reuse computation only when its inputs are identical

Existing source analysis identified at most four of 80 paired work periods
(5%) reusable between natural LIVE and pulse L/version1, plus eight action
readouts. Full state/window/numerical-schedule identity must be proven, all logical
records retained, and continuing states privately owned. This is lower priority
than readout prefill and independent-pair batching. Unchanged Replay must still
execute independently: reusing LIVE to produce it would invalidate the diagnostic.

Common question-prefix reuse removes at most 1120 of 13108 linked question
tokens in the audited scheduler example (8.54% of that path, not the episode).
Clone time was about one second. Avoid a large cache rewrite solely to save it;
shared-prefix memory could still enable larger cohorts after ownership review.
Identical prompt text is insufficient for reuse when earlier state or donor
history differs. Calibration/validation/formal episodes remain disjoint.

## Reduce engineering and operational waste

Use a fixed feasibility ladder: tiny operator correctness and timing; real-model
teacher-forced/micro checks; full replay/resume correctness; complete representative
workload for both models; whole-package forecast. Reject a route early on technical
failure or poor speed, not scientific effect. Do not run the expensive complete
old/new suite after every small edit. Existing trustworthy reference measurements
remain useful context, but changed numerical identity still requires the declared
acceptance comparisons. Charge compile/load/test time to the engineering budget.

Keep one checkpoint resident through its permitted work rather than needlessly
reloading per episode or branch. The current backend already shares model weights
among private states; there is no extra saving from proposing that again. Any
later change to stopping between stages must be reviewed separately and cannot
skip gates or verified backups. Prepare manifests and scripts before renting.

Compare hardware by measured dollars per accepted complete episode, not advertised
TFLOPS, VRAM or hourly price alone. Illustratively, a host priced 1.5x higher is
cheaper for compute only if complete throughput improves by more than 1.5x;
transfer, setup and storage still matter. No new offer was queried or selected.
Extra GPUs without better efficiency mainly shorten elapsed time. Do not assume
that doubling GPU count halves aggregate GPU-hours.

## Scientific scope and adoption

Preserve N, both models, all control arms, rounds, generated tokens, private
histories, questions and neutral gates. Reducing these would change power or
the estimand, not simply remove engineering waste. For example, removing one
pulse checkpoint saves 16 of 80 work periods; removing one goal checkpoint
saves six. Those are only work-period counts, not measured wall savings, and
would lose corresponding temporal comparisons. Neither is recommended/adopted
before testing the engineering route. Do not stop an arm or choose a backend
because the interaction effect looks promising or weak.

Batching/fusion can change floating-point rounding even with the same mathematical
operation. [PyTorch's numerical accuracy guidance](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html)
explicitly distinguishes batched and unbatched bitwise results. Apply the proposed
prospective numerical acceptance process; do not call a close result an old exact
pass. Same-shape Replay, resume, lane isolation and byte integrity stay strict.

The planning judgment remains 2–4x whole-workload throughput as an unmeasured
target, not a guarantee. New storage evidence does not raise it. For illustration,
speeding a 50% readout component 5x and a 37% generation component 3x, leaving
13% unchanged, gives only 1/(0.50/5+0.37/3+0.13) = 2.83x overall. Actual profiling
must separate overlapping timers before using this as a fitted cost model.
Never multiply kernel, prefill, batching and storage gains as independent factors.

Recommended next local work: the lossless restore proof and a concrete mutation-
guard contract, alongside the existing isolated operator package. Any hardware
attempt needs its own bounded, reviewed authority; the previous one-shot USD8
benchmark is closed. Formal collection remains prohibited. Preserve historical
costs, the USD100 cap and the stopped disk containing missing benchmark evidence.
