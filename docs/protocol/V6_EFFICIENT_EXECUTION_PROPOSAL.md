# V6 prospective efficient numerical implementation

2026-10-15, Codex. **Proposal only; not adopted, frozen, or GPU-authorized.**
The PI requested a substantial reduction in GPU hours without sacrificing the
scientific question. No production engine or historical freeze is changed here.
The earlier exact-bit optimization remains a measured 2–3% improvement, not the
solution to the full workload. No V6 scientific collection has begun.

## Why the current workload is large

An episode includes 80 paired work periods: 30 natural-policy periods, six
FRESH-shadow periods, 32 pulse-intervention periods, and 12 goal-intervention
periods. At 64 work tokens per side, that is 10,240 generated work tokens, plus
160 preparation tokens. The selected TEXT subset adds 800 generated/preparation
tokens. Across two models, N240 and TEXT60 each, these total 5,088,000 generated
steps. The current known-question implementation additionally performs about
6,291,840 linked token forwards (13,108 per base episode), before neutral gates.
These are structural workload counts, not independent statistical observations.

The complete engineering comparisons give the following illustrative compute
projection. They use one example of each workload per model, with gain1 neutral
timing as a proxy for other gains and validation; they are not runtime confidence
intervals. Details and provenance: `../reviews/v6_benchmark_closure_20261015.md`.

| Stage, both models | Compute hours |
|---|---:|
| Formal N240 each, including TEXT60 each | 194.52 |
| Baseline60 each | 4.44 |
| Calibration, three gains x40 each | 31.53 |
| Independent validation80 each | 21.02 |
| Total | 251.52 |

Formal work accounts for about 77%. Backup repair or small calibration cuts do
not address the dominant computation. Earlier planning did not establish full
throughput before promising a feasible automatic chain; that was an estimation
failure, separate from the later backup failure.

## Recommended execution architecture

1. **Batch independent pairs.** Keep each pair's six-round state, actual actions,
   private world, foreign-window ownership and t-1 publication barrier intact.
   Process several independent histories in one model call so model weights are
   reused across lanes. Begin with fixed B2/4/8 feasibility, not dynamic packing.
   Neither simultaneous worlds nor A/B sides become independent samples.
2. **Prefill known questions causally in chunks.** Their text is already fixed;
   it need not invoke the entire model separately for every question token.
   Hold the foreign window fixed, use exact per-lane own positions and an offset
   own-causal mask, and make every held foreign key visible to every query.
   All formerly checked hidden states and full-vocabulary logits must still be
   produced and checked for finiteness. Question tokens are grouped, not removed.
   Live generation still publishes one eligible tick at a time.
3. **Fuse the weighted attention operation.** The current path computes native
   own attention, recomputes own scores for the partition mass, computes foreign
   attention, then mixes. For real-arithmetic logits u and v, gain g>0:

   `y = (1-beta)*softmax(u)V + beta*softmax(v)FV`

   `beta = exp(LSE(v)+log(g)) / (exp(LSE(u))+exp(LSE(v)+log(g)))`

   This equals `softmax([u, v+log(g)]) @ [V; FV]`. Zero gain or an empty foreign
   window remains own-only. Preserve scaling, GQA head mapping, donor post-RoPE
   positions, eligibility and masks. A generic triangular mask over concatenated
   own/foreign keys is wrong. Prototype an eligible fused operation before a
   scheduler rewrite; a dense fallback can be slower than the current code.
4. **Separate archival CPU work from GPU execution.** Use bounded, owned CPU
   buffers, lossless content deduplication and independent restore/hash checks.
   Preserve every logical snapshot/tape and its original bytes, including failed
   attempts. Enforce backpressure and deadline draining. Projected raw archives
   are about 477.8 GB; incomplete transfers do not establish full-backup speed.
   Do not delete raw evidence, quantize it or pretend transfer time is zero.

Optional exact computation-DAG sharing can reuse natural LIVE rounds 2–3 and 5–6
for pulse L/version1 only after full input/state/window/schedule identity is
proved, with separately owned continuing states and every logical record. Its
ceiling is four of 80 work periods (5%), plus their duplicate action readouts.
**Never reuse LIVE outputs to implement the unchanged Replay diagnostic.**

## Scientific contract versus numerical implementation

The joint formula is mathematically equivalent, but current native own-attention
output is rounded before FP32 mixing. Fusion, batching and chunking can alter
rounding and greedy trajectories. Therefore this is a **new prospective numerical
implementation**, not a passing candidate under the old bitwise acceptance gate.
The study keeps both models/revisions, weights and precision, N, materials,
rounds, branches, readouts, gates, estimands and selection rules.

Before adoption, write and approve a numerical acceptance amendment that:

- Uses an independent small-tensor high-precision oracle, plus adversarial
  masks, GQA layouts, gains, empty/full windows, ragged histories and cross-lane
  isolation tests. A supplied mask can change kernel dispatch and GQA handling.
- Separates operator accuracy, teacher-forced identical-input trace comparison,
  and free-running trajectories. Do not call similar accuracy or significance
  numerical equivalence. Near-tie greedy changes can propagate and require
  explicit investigation, not an automatic exemption.
- Specifies error metrics/tolerances from the mathematical operation, precision
  and readout sensitivity before research outcomes are available. This proposal
  does not invent an acceptable epsilon. An empirical maximum error is not a
  certified worst-case bound; only a valid bound epsilon plus top-two margin
  greater than 2*epsilon guarantees an unchanged argmax for that comparison.
- Freezes batch cohorts, lane order, shape/chunk schedules and recovery behavior.
  Padding never enters consumed histories; invalid-action recovery cannot change
  a comparison's numerical context silently. Test lane permutation and singleton
  proximity separately from strict repeatability at matched shapes.
- Keeps exact same-backend, same-shape unchanged Replay, independent diagnostic
  execution, immutable byte integrity, deterministic resume and causal eligibility.
  These checks do not become tolerance-based. If they fail, stop.
- Repeats native/smoke/resume acceptance and all original scientific neutral
  gates under the newly frozen implementation. No calibration/validation result
  or implementation acceptance carries over automatically; no formal outcome
  selects a kernel, batch size, prompt, gain or continuation decision.

`v6_efficiency_checks/check_weighted_attention.py` currently checks only FP64
algebra: 864 cases, maximum absolute difference 1.89e-13, plus lane/causal negative
controls. Both paths share score construction, so this is **not** the independent
implementation oracle above, native BF16 validation, a CUDA test or a speed test.

## Feasibility and financial decision

Prepare an isolated implementation and predetermined acceptance policy locally.
Then seek authorization for a bounded engineering check: first kernel and tiny
B/T feasibility; only if correct, a complete representative workload for both
models. Measure episodes/hour including checks and archives, not tokens/second
or kernel-only timing. Stop an unpromising route early; do not pay for the full
old/reference suite before the feasibility question is answered.

The following are sensitivity calculations, **not measured or promised gains**:

| Complete-workload throughput gain | Illustrative compute hours | Rental USD |
|---|---:|---:|
| 4x | 62.88 | 92.48 |
| 6x | 41.92 | 61.65 |
| 8x | 31.44 | 46.24 |

Rate is the benchmark's USD1.47074074/hour. These exclude prior charges, acceptance,
loading, backup/transfer, storage and reserves. The unchanged conservative rule
projects 555.33 hours currently: even dividing that by 8 gives 69.42 hours and
USD102.09 compute alone. Therefore **6–8x does not establish USD100 admission**.
Representative per-stage measurements and a complete verified backup forecast
must resolve affordability under the existing rules. If the fixed study still
does not fit, present the gap to the PI; never silently reduce N or gates.

Additional GPUs mainly shorten elapsed time; they do not inherently reduce GPU
hours. Two serial worker processes are a feasibility option, not a credible
unmeasured substitute for the architecture above. Smaller models, quantization,
shorter interactions and dropped controls would change the study and are not
part of this recommendation.

Primary technical references: [PyTorch numerical accuracy](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html),
[SDPA semantics and kernel caveats](https://docs.pytorch.org/docs/main/generated/torch.nn.functional.scaled_dot_product_attention.html),
and [pinned PyTorch 2.6 FlexAttention source](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/torch/nn/attention/flex_attention.py).
The pinned API exposes score modifications, block masks and GQA but is a prototype;
availability is not evidence of model compatibility or speed on this rented GPU.
