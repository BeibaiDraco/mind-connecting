# V6 confidence audit — 2026-10-16

The PI requested another check of confidence. This is a local read-only code,
test and artifact audit by the implementation author, not a new independent
CUDA review or an execution grant. No model/provider/credential operation ran.

## Evidence freshly reproduced

- Complete offline suite:1206 passed,9 skipped,1 deselected in43.74 seconds.
  The new native CUDA tests are skipped without torch; the total test count
  does not mean the candidate kernel or real checkpoints have passed.
- The prepared engineering package still validates against all68 bound files.
  Its file SHA256 remains
  `abe2dba007615ff22beb1a3d660fd2170fabb31a79a5cf66ea14733279df3e56`.
- Reverified the independently retained lossless-container manifest hash and
  all16 restored files, totaling948,075,974 bytes. No original/result was edited.
- Rechecked fixed tick barriers, known-input masks, actual-answer commitment,
  full-schedule synthetic reference tests, unchanged Replay checks and failure
  publication against the original implementations and earlier independent
  review. No new demonstrated semantic defect was found in this inspected scope.

## Concrete performance uncertainty

`v6_batch_native.py:223` builds owned, zeroed prefix buffers on every nonempty
consume call and copies each continuing history into them; final outputs are
also compacted/cloned. For four lanes and the declared4096 prefix capacity,
the own-KV scratch volume is:

`4 lanes * layers * 2(K,V) * KV heads * 4096 * head dimension * 2(BF16 bytes)`

| Fixed profile | Own-prefix scratch per four-lane call |
| --- | ---: |
| Qwen | 2,415,919,104 bytes / 2.25 GiB |
| Llama | 2,147,483,648 bytes / 2.00 GiB |

This is source-derived logical buffer volume, not measured latency, bandwidth,
total peak memory or a claim that CUDA malloc occurs each tick. It is shared
batch scratch, not accumulating retained memory across all ticks. Caching
allocators may reuse storage, but zeroing, copy and compaction work still need
measurement. The actual structured fixture histories are much shorter than
4096. Padding and repeated copying may offset some batching/prefill gains;
their cost cannot be inferred from successful CPU semantic tests.

The tiny CUDA fixture uses chunk4/prefix256; the proposed real-model trial uses
chunk16/prefix4096. Passing the tiny tests would not establish real-shape memory,
compilation behavior, isolation or throughput. Full real-model cases must still
check those properties. The microtrace's extra projection/CPU-copy timing is
diagnostic only and must not be extrapolated as normal throughput.

## Confidence and execution boundary

Confidence is supported for the unchanged experimental definition, local
scheduler semantics, source binding and verified lossless artifact recovery.
Actual CUDA numerical behavior, free-running trajectories, strict real-model
Replay, speedup and total affordability are still unmeasured. The candidate is
worth a bounded engineering test; a whole-run2–4x speedup is not certified.

The proposed2–4-hour/USD8 window is a bounded attempt with possible early stop,
not a guarantee both checkpoints will complete every check. The private caller
still owns pinned model/weight admission, prior-stage receipts, current finance,
fresh guards, missing-file recovery and independently verified actual shutdown.
The generic backend constructor and tiny fixture cannot substitute for those
checks. The prior61-file/2.529GB missing-backup obligation remains; no current
provider availability/rate/state was freshly queried during this local audit.

No scientific source, parameter, sample size, numerical tolerance, new paid
allowance, deadline or automatic continuation was changed. Existing historical
reviews and the prepared package remain intact. Prior independent review is
recorded in `v6_local_optimization_review_20261015.md`.
