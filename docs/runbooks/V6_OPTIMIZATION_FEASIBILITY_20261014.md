# V6 optimization: feasibility before a large rewrite

Prepared 2026-10-14, America/Chicago. This follow-up revises the engineering
priority in `V6_BOTTLENECK_PLAN_20261014.md`. It is an offline proposal, not an
accepted backend, permission for another paid test, or scientific continuation.
The existing bounded benchmark must finish under its existing limits.

## Diagnosis and uncertainty

The completed Qwen engineering example took 1728.354 seconds with the reference
and 1683.278 seconds with the first candidate: only 2.61% less time. Approximately
40.6 of the 45.1 seconds saved came from the archive helper. Decoder ingestion
was essentially unchanged. The first optimization did not address the main
execution cost.

The candidate spent about 836 seconds in probes and 627 seconds in generated
steps. Its 197 seconds in state digests overlap those operations. These are
inclusive host timers, not an additive GPU timeline. The tokenizer/scheduler
audit counted 11,200 generated steps and 13,108 single-token forwards for linked
known-input questions in one full-with-TEXT example. It did not execute a model.

The reference generated step explicitly observes the GPU from the host at
argmax, at two successful finite-value checks, and at export-byte transfer.
Each linked known-input token also has the two finite-value observations.
These paths imply at least 71,016 logical host-observation sites for the above
counts, excluding other work. This is a source-level count, **not** 71,016
measured costly stalls. Some observations may encounter an already idle GPU.
Foreign attention also converts the same held BF16 foreign K/V window to FP32
again for every question token and every layer, launches many small operations,
and recomputes own-attention normalizers alongside native SDPA.

One hardware snapshot showed 47% GPU utilization and about 22.7 GB resident
memory. It neither establishes sustained underutilization nor proves that two
workers will fit. Peak allocated memory from one Qwen example also excludes
some driver/context/allocator costs. No claim of a 3x or larger speedup follows.

The useful distinction is between computation required by the experiment
(actual recurrent generation, all controls and full readouts) and execution
overhead (repeated casts, host round trips, verification transfers and launch
gaps). The latter is the engineering target. If model computation dominates,
these changes cannot make the former disappear.

## First measure the part that decides the implementation

A future separately authorized engineering test should collect a short CPU/CUDA
timeline for generated steps and a held-window question, at representative short
and long cache lengths. It must separate GPU kernels, launch gaps, device/host
copies, finite checks, casts, own/foreign attention, full-vocabulary heads and
CPU hashing. Use disjoint engineering states; do not inspect scientific effects.
Pair this with unprofiled synchronized timings because profiling changes timing.
Do not add this work to the currently running one-shot comparison.

Avoid spending another full two-model comparison on each idea: reject a candidate
early with tiny exact comparisons or poor microtimings, then run complete tasks
only for a surviving combined candidate. A microbenchmark can reject an idea;
it cannot certify the full workload or justify a formal launch.

## Low-scope candidates first

### A. Convert a held foreign window once per existing input call

Within one `_consume` call, the foreign window is already fixed. Privately retain
its FP32 K/V conversions across that call's existing single-token loop. Preserve
the original BF16 exports, original source checks, contiguous layouts, per-layer
shapes and subsequent arithmetic. Do not introduce a cross-call cache initially.
Do not freeze the receiver's own K/V, which grows with each input token. Gain-zero
and empty-window routes retain their existing native prefill.

This removes repeated conversions without changing B=1/T=1. It is simpler to
audit than a multi-token attention implementation. The relevant casts occur
inside `_attention`, so the existing `_foreign` timer does not measure them.
Actual exact equality and speed remain untested.

### B. Reduce host observations without crossing a work-tick boundary

First combine the existing hidden-state and full-vocabulary-logit finite flags
on the GPU and read one boolean, preserving the same first failing token and
all numerical checks. Do not omit the intermediate full-vocabulary head.

A subsequent isolated one-step prototype can keep the masked argmax token on
the GPU as the next B=1/T=1 input and collect the actual token, finite flags and
owned export bytes in one bounded host transfer at the end of that same step.
Validate before publishing a normal state/export and compute the unchanged SHA
from the original creation bytes. Preserve positions, tensor layout, model
operations, per-step audit and the existing A/B ordering. There is no public
placeholder token/hash and no foreign update is delayed to a later tick.

This requires a reviewed internal single-step interface: the current `_consume`
expects Python token IDs and updates concrete history. Input validity, exception
timing and partial-cache failure semantics must be tested rather than assumed
equivalent. No invalid token, unverified export or failed state may escape. If
an input-validation dependency cannot be preserved, retain its early check.
Do not adopt speculative failed-path computation merely to improve throughput.
Original export-hashing exceptions occur outside `_consume`'s failure handler;
blanket changes to failed-state flags are not identical error semantics either.

This small transaction should be tested before a new multi-tick scheduler. Even
removing several observations per step does not prove a large saving: the
remaining export transfer still waits for the forward, and kernel launch or
memory traffic may dominate.

### C. Test independent workers before rewriting numerical batching

A separate two-worker throughput test on the same GPU could preserve each
worker's unchanged single-history arithmetic and private pair scheduler. Assign
predetermined disjoint engineering episode IDs, independent caches/files and
seeds, and retain identical pinned software and checkpoint settings. Compare
each worker's output exactly against its serial reference. Measure aggregate
completed episodes/hour including contention, memory peaks and startup.
The serial and concurrent comparisons must contain the same two cases, not one
serial case compared with two different concurrent cases.

This is not permission to duplicate the current job. It needs a new reviewed
supervisor with one cumulative budget/stop authority covering both workers,
atomic episode ownership, bounded backup traffic, crash cleanup and exact
resume. Neither child may independently stop a shared instance while its sibling
is active. A worker failure must not silently change sample membership.

Ordinary CUDA processes may time-slice; they do not automatically overlap GPU
kernels. NVIDIA MPS can permit cross-process concurrency, but changes the runtime
environment and error-containment conditions. Do not start MPS, change GPU mode,
partition resources or alter a shared host implicitly. If ordinary concurrency
is ineffective, a compatible MPS experiment requires its own explicit technical
review, exact checks and authorized test boundary. Two workers can be slower
than one when CPU, memory bandwidth, PCIe or storage is saturated.

## More invasive options, conditional on the profile

1. **Private question batching of check results.** Keep each original one-token
   forward and finite calculation, collect flags until a bounded private branch
   boundary, and reject before any readout/seal/commit/archive/publication.
   Preserve the earliest failing position when readable; report unknown after
   an unreadable CUDA failure. Delayed failure detection is a contract change
   requiring review, not a free removal of checks.
2. **Two-tick staged paired loop.** Keep the same single-token kernels and one
   CUDA stream, original A/B order, and t-1 incoming windows. Use separate private
   staged types; never put fake IDs or hashes into existing public state types.
   Capture independently owned bytes when every export is created; only hashing
   or transfer completion may be delayed. Validate and drain all tokens, flags,
   hashes and ordered audit before any public boundary. This is substantially
   more work than the single-step option above and is not the default next edit.
3. **Numerical batching/prefill.** First try tiny B=2 or T=2/4 exact-feasibility
   checks with real BF16 checkpoints and full continuing state. Mathematical
   equivalence is insufficient under the current bitwise gate. A mismatch rejects
   that tested configuration; do not build a large scheduler first, loosen the
   gate afterward, or equate close accuracy with exact native equivalence.
4. **Streams/graphs/compilation.** Consider only if launch gaps dominate. Current
   dynamic cache lengths, Python checks, shared attention configuration and host
   observations prevent an automatic drop-in. Padding, static caches, fusion and
   different kernels can change results; a captured graph does not replay Python
   validation. These need isolated feasibility checks, not a framework migration.
5. **Integrity and storage.** Keep the original hashes and all logical archives.
   Lossless deduplication or pipelined verified copies may save bytes/time later.
   Digest memoization based only on pointer/version is unacceptable. Any complete
   byte-equality/snapshot substitute needs its own corruption proof and bounded
   memory analysis. Do not spend the first rewrite on cloning: its measured
   inclusive time was about one second.

## Decision rule and acceptance

The practical sequence is: short profile; tiny cast/check tests and an ordinary
two-worker feasibility check if memory permits; one-step transport prototype if
the profile supports it; only then a larger execution rewrite. Tiny B/T tests
may falsify that alternative early, but are not the preferred implementation
commitment. Performance choices use only engineering correctness and cost.

Test both pinned models, all original gains, empty/full windows, multiple cache
lengths, all recovery categories, parent/sibling isolation, exact replay and
archive/no-op resume. Include nonfinite values at early/middle/last positions,
invalid inputs, mutation between capture/use/drain, transport failure, pending
stop and interruption. Preserve evidence, do not publish partial success, and
do not automatically retry a failed candidate. All tokens, outputs, continuing
states and required audit/checksum events must remain exactly comparable.

The current comparator also records method-call counts. A new internal/chunk
API cannot silently discard that check. Any semantic-event comparator must be
separately reviewed and still cover every original step/export/state/readout.

Promote only a fully verified candidate with lower **whole-workload GPU-hours
and dollars**, accounting for all scientific stages, loading, archive/transfer,
new acceptance costs, prior spending and the unchanged conservative margin.
Report bottleneck percentages without double-counting nested timers. Treat any
proposed 2x/4x speed as a hypothesis until measured. A 10% microkernel improvement
is not a 10% end-to-end saving, and faster probes alone cannot halve this example.

Nothing here changes N, rounds, 64-token work, controls, questions, checkpoints,
precision, gates, selection rules or the one-tick reciprocal channel. None of
these ideas is yet an accepted optimized engine. Formal collection remains held.

## Sources

Local evidence and code are listed in the preceding bottleneck plan. The second
independent read-only assessment is recorded in
`docs/reviews/v6_optimization_feasibility_review_20261014.md`.

- [PyTorch performance tuning](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html): avoid unnecessary CPU/GPU synchronization.
- [PyTorch numerical accuracy](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html): batching/slicing need not produce bitwise-identical results.
- [PyTorch CUDA semantics](https://docs.pytorch.org/docs/main/notes/cuda.html): graph capture constraints and synchronization.
- [NVIDIA MPS architecture](https://docs.nvidia.com/deploy/mps/architecture.html) and [when to use MPS](https://docs.nvidia.com/deploy/mps/when-to-use-mps.html): context time-slicing and cross-process concurrency.
