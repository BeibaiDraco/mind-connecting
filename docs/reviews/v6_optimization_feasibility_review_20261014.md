# V6 strict optimization feasibility — second independent assessment

Date: 2026-10-14, America/Chicago. Reviewer: Codex agent `v6_perf_review`.
Recorded by the coordinating agent from the completed read-only assessment and
its follow-up. This is a new review record; the earlier assessment is preserved.
The reviewer inspected native/runtime/performance/benchmark/supervision paths.
No reviewer file edit, model execution, provider call or system change occurred.

## Conclusion

Prefer small same-shape candidates and tiny feasibility checks before a large
prefill/batch rewrite. First combine finite flags and reuse foreign FP32 casts
within one held-window input. A same-tick packed transfer and an isolated
two-worker engineering comparison are worth assessing before multi-tick staging.
None is implemented, numerically accepted or demonstrated to save money here.

## Findings incorporated into the follow-up proposal

1. The Qwen 2.61% improvement and large inclusive probe/consume/digest timings
   are observed. Host-observation counts and repeated conversions are source
   evidence of opportunities, not a measurement of synchronization stalls or
   launch overhead. Do not add overlapping timers or infer utilization from
   a single hardware snapshot.
2. The simplest cast candidate hoists foreign K/V FP32 conversion once per
   existing `_consume` call, whose held window is already fixed. Preserve BF16
   originals, checks, contiguous shapes and arithmetic. The receiver cache grows
   and cannot be treated as another fixed window.
3. Combining two finite reductions into one GPU boolean keeps the first failing
   token. Keep both checks and the complete output head. Delaying validation
   across tokens instead changes failure detection and needs private state,
   bounded queues and rejection before any public boundary.
4. The selected CUDA token need not be read by the CPU before a valid B1/T1
   forward; old validated length supplies positions. A same-tick packed token,
   finite-flag and export-byte transfer can keep the causal schedule intact.
   However, original invalid-token and invalid-foreign checks occur **before**
   forward. Prove admissibility for supported states or retain early checks.
   Do not assume every original error already mutates cache. Original export
   hashing errors also lie outside `_consume`'s failed-state handler; a blanket
   new `failed=True` is safer in some cases but is not identical failure state.
5. For any later staged loop, defer hashing only, not capture of the original
   bytes it proves. Use separate private staged types, original one-stream A/B
   ordering and the t-1 barrier. Drain all identities, flags and ordered audit
   before publication. If CUDA failure makes flags unreadable, report an unknown
   earliest bad position. Never fabricate a concrete failure index.
6. Two separate workers retain numerical shapes but default CUDA contexts may
   time-slice. CPU hashing could overlap GPU use, or CPU/PCIe/storage/context
   contention could make both slower. MPS is a separate environment change.
   One allocated-memory peak or resident snapshot cannot establish joint peak
   memory including contexts, reserved buffers, growing caches and host RAM.
7. Existing `v6_supervision.py` rejects competing workers; plans/ledgers assume
   one writer. A new isolated coordinator must explicitly own both children,
   fixed disjoint engineering IDs and separate outputs under one budget/lease.
   Failure stops both, normal completion of one does not stop the other, and
   episode retry limits must not reset when work changes workers. Do not use
   two unsupervised existing formal launches as a throughput test.
8. Compare exactly the same two engineering cases serially and concurrently,
   first in short representative fragments and then full episodes only after
   acceptance. Include every token, readout, continuing state, export and logical
   archive. Fixed numerical settings cannot be silently changed to force a pass.
9. B2/T2-or4 should first face minimal real-checkpoint bitwise tests. A mismatch
   rejects the tested variant under current rules; mathematical equivalence is
   not enough. Graphs/streams require additional configuration, cache/address,
   event and Python-validation work. Pointer/version-only hash reuse weakens
   integrity and is not accepted.
10. The benchmark includes method call counts. A replacement internal/chunk API
    requires a separately reviewed semantic-event comparator covering every
    original step, not removal of a failing comparison field.

No result here authorizes another paid test or scientific collection. Even a
hypothetical throughput doubling does not establish full-package affordability
inside the original cumulative USD100.
