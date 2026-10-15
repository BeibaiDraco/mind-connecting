# V6 efficient implementation: staged acceptance draft

2026-10-15. The PI agreed to try the substantial efficiency route. This supports
local prototype work; it does not establish a tolerance for scientific collection,
authorize a new paid lifecycle, or replace the existing numerical freeze.

## Stage A: isolated operator feasibility

The inert package prepared by `scripts/v6_prepare_efficiency.py` pins source
hashes, a deterministic covering set of 16 cases, one explicitly named fused
kernel, random seed and reporting rules. It never loads a model or starts CUDA.
`run_operator_probe` additionally requires an external live deadline/lease check
and explicit hardware authorization. There is no automatic follow-on stage.

- Cover B1/2/4/8, T1/2/4, own prefixes0/7/31, foreign windows0/1/16,
  gains0/.25/.5/1 and nontrivial grouped-query attention. This is a small synthetic
  feasibility set, not realistic full-model timing or complete numerical coverage.
- Independently compute scalar FP64 scores, head mapping, causal visibility,
  partition normalization and values from the **already quantized BF16 inputs**.
  The oracle shares no score/mask construction with the vector or CUDA candidate.
  Local hand-computed examples and adversarial tests check the oracle itself.
- Engineering screen: maximum absolute operator error must be no more than
  `2^-7 * max(abs(own_values), abs(foreign_values))`. At zero scale require exact
  zero error. This is a deliberately declared diagnostic ceiling of two BF16
  unit roundoffs at the value scale; it is **not a proved rounding bound** or an
  adopted scientific tolerance. Retain absolute/RMS/scale-normalized errors and
  fail on nonfinite output. Never widen the limit after seeing results.
- Require exact same-shape repeatability, lane isolation, lane permutation,
  own-future noninterference and input nonmutation. Singleton proximity is a
  separate numerical screen. The unchanged native operator is also measured and
  its oracle error retained; no comparison of effects or significance is used.
- Explicitly force memory-efficient SDPA with math fallback disabled, or use
  compiled FlexAttention. Keep FP32 log-gain bias; if a backend cannot support
  that precision/mask/layout, record failure rather than quietly lowering bias
  precision, expanding tolerance or substituting a slow implementation. Torch
  stays at2.6.0 and Transformers at4.57.1; matmul TF32 must be disabled. Record
  NumPy/Python versions and numerical/determinism/backend flags. Compilation or
  unsupported-dispatch failures are retained.
- Time concatenation, GQA expansion, mask creation and casts within the candidate
  call; report first-call compilation/warm-up separately and five synchronized
  repeated timings with alternating candidate/reference order. Reference calls the unchanged native B1/T1 mixing path for
  each lane/token. This is **operator-only speed**, not model/episode throughput.
- Append each phase and timing sample durably before the next lease check;
  preserve quantized inputs, oracle outputs and comparison tensors in new files.
  Late failures retain the completed diagnostics. Refuse existing directories.
  No automatic retry or admission.

Failure ends that attempt. A passed Stage A only motivates model integration.
It does not establish a scientifically usable implementation or USD100 admission.

## Stage B: unadmitted model integration prototype

`EfficientPrototype` inherits the checked native boundaries and exposes linked
chunked prefill plus explicit homogeneous `consume_cohort`. It has a different
model identity, requires explicit CUDA construction, refuses automatic loading,
and is not imported by production selectors. Fixed chunks can be1/2/4/8/16/32.
It does not implement the complete batched six-round scheduler.

All lanes need initialized, equal-length histories, equal-length input tuples,
equal foreign-window lengths and the same gain. Unsupported/ragged layouts and
sealed states are rejected, without padding, repacking or substituted tokens.
The input cache is copied into a private cohort; all final states are constructed
and validated before publication, and each lane owns its resulting tensors.
Distinct cache objects alone do not prove absence of underlying storage aliases;
the private copies are the isolation mechanism. Native failures remain failures.

Every linked input token still produces hidden states and full-vocabulary native
logits and is checked for finiteness. Each layer's own mask is checked on-device;
all flags are verified with the finite checks before publishing any new state.
Inherited readouts still use the full FP32 head and consume the actual answer.
The existing state identity does **not** freeze the cohort/lane schedule, so
inherited archive methods cannot be presented as certified deterministic resume.

Before any use beyond engineering, verify on both pinned checkpoints:

1. Operator implementation against an independent oracle on realistic shapes,
   weights/activations, extreme logits, masks and all gains/windows. Record
   precision-dependent deviations, not just whether examples pass a threshold.
2. Teacher-forced identical-input full-model hidden states and full logits;
   quantify error and top-two margins, and investigate every greedy divergence.
   Near ties do not automatically excuse trajectory divergence. Set a defensible
   full-model acceptance policy prospectively; Stage A's epsilon does not apply.
3. Complete representative trajectories, all diagnostic clones/actions, exact
   unchanged Replay and exact same-schedule repeats. Freeze fixed cohort/lane/
   chunk schedules and recovery behavior. Validate full archive restoration,
   byte integrity, failures and no-op resume independently.
4. Full-workload timing for both models, including adapter/check/copy overhead,
   model loading, all neutral stages and complete backup. Kernel-only timings
   cannot produce a whole-study cost forecast. Do not reuse the old benchmark's
   native acceptance certificate for this new numerical implementation.

## Scientific adoption and execution remain separate

Keep pinned models, weights/model precision, study materials, N240/TEXT60 per
model, neutral sample sizes, six rounds, interventions, all metrics, statistical
units and original scientific gates. Engineering must not inspect formal effects
or significance to choose a backend. Repeat the original neutral stages only
after a reviewed new source/numerical amendment and PI ratification; validation
failure still ends the corresponding path.

Full model numerical tolerances, dynamic/ragged scheduling, archival compression,
financial dispatch and new paid allowance are **not established by this draft**.
The original source/freeze, accumulated costs, failed attempts and retained raw
evidence remain intact. The stopped instance must retain missing backup data.
