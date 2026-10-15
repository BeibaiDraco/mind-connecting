# V6 measured bottlenecks and the next optimization boundary

Prepared 2026-10-14 (America/Chicago), at the PI's request. This is an offline
engineering proposal. It does not adopt a new backend, alter a scientific rule,
extend the current paid comparison, or authorize formal collection.

## What has actually been measured

The completed Qwen engineering comparison passed exact comparison for all four
microcheck gains and the full-with-TEXT, baseline and calibration workloads.
Llama's full comparison and final backup/stop closure were still pending when
this assessment was prepared. The numbers below are one instrumented engineering
episode, not a distribution of production runtimes or a full-workload estimate.

| Qwen engineering workload | Reference seconds | Candidate seconds |
|---|---:|---:|
| Complete episode including TEXT | 1728.354 | 1683.278 |
| Baseline fixture | 149.953 | 147.910 |
| Calibration fixture, gain 1 | 531.156 | 531.247 |

The complete-episode improvement is 45.076 seconds, or 2.61% less elapsed time.
The first candidate primarily reduced archive overhead. Its complete-task
archive helper time fell from about 74.9 to 34.4 seconds; decoder ingestion
remained about 1404.5 versus 1402.3 seconds. These are inclusive host timings:
parent/child measurements overlap and asynchronous GPU work can be charged at a
later synchronization. They are diagnostic evidence, not an additive GPU-kernel
breakdown. The episode total is measured with synchronization.

| Candidate diagnostic operation | Calls | Inclusive host seconds |
|---|---:|---:|
| Probe/readout | 352 | 836.010 |
| Generated step | 11200 | 627.387 |
| Full state digest | 1548 | 196.921 |
| Input consumption, nested in the above | 12408 | 1402.327 |
| Foreign-window construction/validation, nested | 14072 | 29.304 |
| State clone, nested | 428 | 1.029 |

Probe and step account for about 49.7% and 37.3% of the measured wall time in
this instrumented run. Do not add the digest or consumption percentages to
them. Archive restoration takes another 205.388 seconds after the candidate
episode timer; it is benchmark acceptance overhead and must not be multiplied
as if every production episode reran this acceptance step. Final transfer time
is not measured by the episode timer either.

## Why the implementation is slow

`NativeBackend._consume` in `src/mb/v6_native.py` splits every supplied question
into single-token model calls whenever foreign memory is present. Its foreign
attention callback currently rejects more than one query token or one history.
Thus a fixed question is processed using the same serial loop as newly generated
text, despite its complete token sequence already being known.

Within `probe`, the donor window is held fixed while the receiver closes its
working turn and consumes the question. There is no sender update inside this
question. This differs from `EpisodeRunner.work`, where both sides must read
the previous tick's window and jointly publish their next exports. That live
dependency must be retained.

A tokenizer-only audit of the disjoint engineering materials, using the real
scheduler with a short-clock synthetic backend, found for each checkpoint:

- Full-with-TEXT: 352 readouts, including 240 linked readouts with 13,108 known
  close/header/question tokens, or 43–97 tokens per linked readout.
- Those linked readouts alone imply 13,108 sequential decoder forwards in the
  current implementation, in addition to the complete task's 11,200 generated
  step calls. Outer `_consume` call counts do not expose this inner loop.
- A same-parent token-prefix trie would reduce those 13,108 known-token steps
  to 11,988, an upper-bound removal of only 1,120 steps (8.54%) before caching
  overhead. It does not merge independent replay diagnostic paths.
- The calibration fixture has 84 linked readouts and 4,092 known-token steps;
  prefix reuse removes at most 360 Qwen / 364 Llama steps in this audit.

These counts use the pinned local tokenizers, unchanged question templates and
the engineering materials from `v6_benchmark.materials`. Synthetic choices
serve only to traverse the scheduler; they are not measured model behavior or
GPU timings. No model weights were loaded locally.

The attention callback also performs native SDPA and then recomputes own
FP32 attention logits/normalizers to combine foreign memory. Each call contains
many small operations, conversions and finite-value checks. This is a plausible
additional cost inside `_consume`; the current coarse profiler cannot tell how
much belongs to attention, output projection, transfers or launch latency.

## Recommended development order

### 1. Batch known question tokens with a fixed foreign window

This is the first substantial candidate. Process a supplied question as a causal
multi-token prefill (or bounded chunks) with the same held foreign keys/values.
For every query position, retain its exact absolute position, its own causal
prefix, all eligible foreign positions, the gain and the existing mixing
formula. An own-attention triangular mask must not mask out eligible foreign
positions. Preserve native closure and recovery boundaries, all intermediate
finite-value checks, full-vocabulary answer selection, FP32 readout scores,
probabilities, answer seals and the continuing cache.

This does not shorten or rephrase the question, change communication cadence,
change the sender, or expose future receiver tokens. Mathematical causal
equivalence does **not** imply bitwise equivalence under a different matrix
shape/kernel. The existing exact comparison remains the admission rule. An
exact mismatch rejects this candidate under current authority; a different
numerical acceptance rule would need a separate prospective PI decision.

Even a 4x speedup of the entire measured probe portion, with everything else
unchanged, would reduce this example only from 28.05 to about 17.60 minutes
(1.59x overall). A hypothetical 10x probe speedup gives about 15.51 minutes
(1.81x). Eliminating the whole probe portion would still be less than 2x.
These are Amdahl sensitivity calculations, not measured promises. A successful
prefill implementation alone would not justify claiming an affordable full run.

### 2. Batch independent paired experiments on the same GPU

For larger end-to-end savings, develop a lane scheduler that performs model
forwards for multiple independent histories together. Start with batch sizes
2, then 4, then 8 only if memory/correctness tests pass. Do not rent more GPUs
as a substitute for demonstrating lower GPU-hours per complete episode.

Each experimental pair keeps separate caches, worlds, donor windows, positions,
masks and output records. At tick t both sides read only windows committed at
t-1, and neither new export becomes visible until both sides finish t. Different
episodes cannot attend to one another. Padding must not alter absolute positions,
eligible own/foreign normalization, or source timing. Answer readouts remain
sealed before either answer is committed. Dynamic admissions, failures and
resumes retain episode identity and fixed sample membership.

Batching is an execution change, not a license to replace the reciprocal loop
with a precomputed tape. It needs a new isolated backend because current
attention enforces batch size one. Compare lane order, cohort composition,
chunk boundaries and padding variants against the serial reference. Measure
throughput and peak VRAM, not only one lane's latency. Greater GPU utilization
is a hypothesis here: the current profiler is not a utilization measurement.

### 3. Reduce repeated verification transfers without removing verification

The 196.9 seconds in full-state digests make repeated hashing worth examining,
especially for the neutral baseline (about 65.1 of 147.9 inclusive seconds).
Prefer caching an already byte-verified checksum only for demonstrably unchanged,
owned state: full metadata, every cache tensor, native logits, hidden state,
storage/layout/version identity, owner and source must still match. Invalidate
on every write, seal, answer commit, tensor replacement, recovery and restore.
Retain byte hashes at required persistence and replay boundaries, and test both
in-place/alias mutation and replacement. A tensor version counter alone is not
an independent byte-integrity proof. If the same mutation-detection contract
cannot be preserved, do not enable this optimization.

Exact sequential sibling-prefix reuse is a smaller, lower numerical-risk
adjunct. Restrict it to genuinely linked inputs: splitting an unlinked/gain-zero
native prefill into prefix/suffix would itself change matrix shapes. Retain
separate writable continuations. Its measured structural ceiling above is too
small to treat it as the primary solution. Copy-on-write caches may reduce
memory and enable batching; the approximately one-second clone timing does not
support presenting cloning alone as a major speed bottleneck.

## Changes that are not included

Do not shorten 64-token work periods, remove rounds/controls/readouts, reduce N,
change gain/selection/gates, quantize weights/cache, replace the checkpoints,
merge independent replay validation with the reference, or read effect sizes
to decide whether an optimization is acceptable. Do not score only four answer
labels: the experiment retains full-vocabulary invalid responses and legal mass.
Skipping intermediate full-vocabulary heads also skips current logit-finiteness
checks unless an equivalent mechanism is separately proved; it is deferred.

## Concrete next acceptance package

1. Let the already authorized comparison close under its unchanged USD8/4-hour
   boundary, preserve evidence, verify actual stop and independently rehash SD.
   Do not modify its live source or add paid profiling to it.
2. Add offline mask/position/barrier and cross-lane contamination tests for an
   isolated candidate. Add finer counters for actual inner decoder calls,
   consumed token shapes and cache sizes, with no readout values in the profiler.
   A later bounded kernel profile can separate attention, lm_head, finite checks,
   hashing and synchronization. Profiling mode is not production timing.
3. Before paid measurement, independently review and bind the isolated source,
   disjoint materials, exact comparator, fresh guards and a separately valid
   financial boundary. No new paid attempt is authorized by this document.
4. Compare tiny CUDA cases, both pinned checkpoints and then full episodes at
   all existing gains, including OFF/zero gain, LIVE, one-way, FRESH, replay,
   goal/readout branches, text, invalid-output recovery, archives and exact
   no-op resume. Compare exports, all relevant cache bytes, native logits,
   probability/legal mass, action/world trajectories and required checksums.
   Perturb source tensors/masks/order to prove tests detect contamination.
5. Only after correctness passes, measure steady-state per-episode throughput
   including archive writes and bounded memory, plus initialization, backup,
   transfer/storage charges and all required scientific phases. Report typical
   and the unchanged conservative estimate separately, with uncertainty and
   already-incurred costs. A favorable estimate cannot automatically start
   scientific collection while the PI's hold remains in force.

The engineering objective is a material reduction in complete GPU-hours and
cost, potentially requiring both items 1 and 2 above. No 3x/5x/10x speedup or
USD100 full-run feasibility has been demonstrated. Preserve the scientific
question and measure the optimized implementation before quoting a new budget.

## References and review

Source: `src/mb/v6_native.py` (`_attention`, `_consume`, `probe`, `digest`),
`src/mb/v6_runtime.py` (`work`, `_read`, `actions`), `src/mb/v6_benchmark.py`
(`run_case`, `trace_backend`) and the completed Qwen engineering timing receipt.

PyTorch explicitly cautions that mathematically equivalent batched and sliced
computations need not be bitwise equal: [Numerical accuracy](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html).
Cache/mask/position requirements are documented in [Transformers cache guidance](https://huggingface.co/docs/transformers/kv_cache).

Independent read-only review is recorded in
`docs/reviews/v6_bottleneck_review_20261014.md`. Its cautions about fixed masks,
batch shape, prefix scope, byte-integrity checks, shared caches and full-vocabulary
finite checks are incorporated here. Neither review nor this document changes
an existing scientific or financial approval.
