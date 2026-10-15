# Independent review: isolated efficient V6 prototype

2026-10-15. Independent read-only review by `v6_perf_review`, recorded by Codex.
Scope: new efficient operator/native adapter, guarded operator feasibility,
numerical acceptance draft and tests. No model or GPU execution occurred.

## Findings resolved before this record

1. Cohort publication could fail after committing the first lane when a later
   lane supplied a mutable input list. Immutable containers are now required;
   all final NativeState candidates and histories are built and validated before
   publishing any lane. An unrun CUDA regression injects a second-lane final
   validation failure and requires unchanged histories/cache objects throughout.
2. A `torch.equal` mask check at every layer added host synchronization. Each
   layer now contributes a device-side flag; all flags join the per-position
   hidden/full-vocabulary finite check before any state publication.
3. Late exceptions discarded successful numerical diagnostics/timing samples.
   Inputs, oracle/candidate/comparison arrays are now saved write-once, and each
   phase/sample is durably appended before the next lease check. Failure and
   no-overwrite regression tests cover interrupted and final-boundary paths.
4. Timing always ran the candidate first. Candidate/reference order now
   alternates by repetition and case; individual measurements/order are retained.
5. Reference dispatch depended on an unbound Transformers environment. Execution
   now checks Torch2.6.0/Transformers4.57.1 and matmul TF32 disabled, and records
   Python/NumPy versions plus relevant numerical/backend/determinism settings.

## Review conclusion and limits

Final independent recheck found no further blocking issue for the **isolated
engineering prototype**; 318 focused offline tests passed independently.
Source inspection supports the own-causal/all-held-foreign visibility and GQA
mapping. The prototype is not wired to production, defaults cannot load a model,
and imports remain torch-free.

The predeclared `2^-7 * value_scale` ceiling is an engineering screening heuristic,
not a proved rounding bound, full-model tolerance or scientific admission. Tiny
operator speed does not establish model/episode speed or budget feasibility.
CUDA kernel support, actual performance, native trajectories, complete Replay,
cohort-aware resume and complete archive integrity remain unverified.

Distinct cache-object checks do not prove underlying storage is unaliased; the
adapter's private concatenated caches and cloned outputs provide its present
isolation. Its model identity contains kernel/chunk but not the future complete
cohort/lane schedule, so inherited archive methods are not resume certification.
Any paid hardware test still requires a new protected authorization boundary.

Primary-agent final full offline suite: 1115 passed, eight skipped, one GPU
deselected. Inert package preparation and exact source-binding validation also
passed. No CUDA check was run or represented as passed.
