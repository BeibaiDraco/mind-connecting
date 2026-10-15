# V6 efficient prototype handoff

2026-10-15. Local implementation complete; no CUDA invocation, model loading,
provider action, paid allowance extension or scientific collection occurred.

## Implemented and reviewed

- `src/mb/v6_efficient.py`: independent scalar FP64 operator oracle; separate
  vector implementation; explicit fused SDPA and compiled FlexAttention
  candidates; immutable logical paired-tick fixture. No torch import on import.
- `src/mb/v6_efficient_native.py`: isolated homogeneous cohort consumption and
  linked question prefill, full per-position hidden/vocabulary finite checks,
  on-device mask checks, private caches and validated publication. No production
  selector imports it; automatic model loading is refused.
- `src/mb/v6_efficient_probe.py`: source-bound, operator-only preparation and
  externally guarded execution function; independent oracle, strict invariants,
  raw diagnostic archives, durable phase/sample records, alternating timing
  order, pinned Torch/Transformers and execution-environment reporting.
- CPU tests exercise 288 mathematical layout cases plus negative, scheduling,
  input, authority, failure-preservation and timing-order checks. CUDA tests are
  written for the two tiny architecture fixtures but remain **unrun**.

Prepare an inert review package locally with:

```bash
.venv/bin/python scripts/v6_prepare_efficiency.py --kernel compiled_flex --output /private/tmp/v6-operator-plan-UNIQUE
```

This command cannot launch CUDA or a model. The initial preferred feasibility
candidate is compiled FlexAttention because it can express FP32 log-gain bias
and GQA directly. That is a technical hypothesis, not measured performance.
Memory-efficient SDPA is an explicit alternative, never an automatic fallback.

## Important unimplemented boundaries

The full batched six-round runner, ragged/recovery scheduling, cohort-bound
resume contract and lossless archive staging are not implemented. The current
prototype rejects ragged histories/windows; it cannot simply replace the formal
backend. No speed multiplier or cost forecast is supported by offline tests.

Stage A is synthetic attention only. Its fixed engineering diagnostic ceiling
does not approve model trajectories or revise the scientific numerical gate.
The full staged acceptance requirements are in
`../protocol/V6_NUMERICAL_ACCEPTANCE_DRAFT.md`; historical freezes remain intact.

## Next safe execution boundary

1. Prepare/review a fresh protected, separately authorized short hardware attempt.
   Do not restart a historical controller, reuse an expired lease/deadline, or
   treat the previous one-attempt USD8 exception as an evergreen allowance.
   Retain original cumulative costs and total USD100 unless the PI changes it.
2. Check the actual current instance, current budget and fresh local/remote
   shutdown guards. Preserve the stopped disk's missing raw benchmark evidence;
   incomplete backup still needs its own bounded recovery. No destruction.
3. Only run the pinned Stage A operator package. Stop on failed correctness,
   kernel support, lease or cost checks. Preserve new evidence, verify backup
   and actual provider stop. A pass cannot dispatch a model or formal stage.
4. If Stage A warrants further engineering, validate the isolated model adapter
   on both pinned models, implement/freeze the full scheduling contract and
   measure complete workloads with the original checks and archives. Real model
   acceptance and full remaining cost must be established before considering
   scientific collection. No candidate is selected by interaction effect size.

Independent review: `../reviews/v6_efficient_prototype_review_20261015.md`.
