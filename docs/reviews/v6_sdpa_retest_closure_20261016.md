# V6 repaired SDPA retest closure — 2026-10-16

The bounded engineering retest failed its CUDA admission gate and is closed. It restored at 18:28:13 UTC and actual provider stop was verified at 18:32:55 UTC, a lifecycle of about 4 minutes 42 seconds. A fresh provider read during the scheduled 19:30 UTC audit again verified actual exited/stopped state. Both the exact local controller and local guard processes have exited. No retry, new rental or scientific collection followed.

## What passed and failed

The CUDA receipt contains 27 executed cases: 26 passed, one failed, zero errors or skips. The planned gate requires 47 cases; 20 were not run because pytest stopped at the first failure. The two isolated operator checks passed, including SDPA and compiled flex, as did all 24 newly added SDPA dtype/stride/oracle cases. This supports the concrete dtype repair within those fixtures; it does not certify real-model correctness or performance.

The failure was `test_linked_prefill_and_cohort_repeat_isolation_and_owned_outputs[qwen3]`. This is a small randomly initialized Qwen-shaped fixture, not the pinned real Qwen checkpoint. In the compiled-flex path, PyTorch 2.6.0 Inductor reached `flex_decoding.get_split_k`, then `max(split_k, 1)` attempted a Boolean comparison involving a symbolic dimension (`64/s0 < 1`). The compiler raised `TypeError: cannot determine truth value of Relational`, wrapped as `BackendCompilerFailed`. The candidate currently requests `torch.compile(..., fullgraph=True, dynamic=True)`.

This evidence identifies a dynamic-shape compilation incompatibility on this path. It is not an observed numerical mismatch or a scientific result. The larger linked-prefill/cohort contract remains unvalidated. Both pinned real-model microchecks and the complete timing fixtures were not run, so there is still no candidate speedup or full-workload time/cost forecast. The compiler's suggested eager fallback was not enabled, and no test or numerical limit was relaxed.

## Closure and preserved limits

The audit independently rehashed all 36 remote evidence files against the sealed inventory and all 53 local control-backup files. The controller's successful archive transfer, individual rehash, actual-stop and exact-guard-retirement receipts agree with the fresh checks. A new private audit binds these receipts without altering original evidence. The stopped disk and model cache remain; storage charges can continue. Historical 61-file missing evidence is still unresolved and is not covered by this retest's backup.

The USD8/four-hour retest and original cumulative USD100/hourly USD1.60 accounting remain unchanged, including all historical charges, original financial origin and full-session deadline. No stopped-time credit was added. The completion automation is paused. The full repository offline suite passed 1220 tests, with nine skipped and one deselected; no local torch/model execution occurred.

Next engineering work, if requested, is a local investigation of shape-specialized flex compilation and its compilation-cost implications, followed by a newly reviewed source/control package. Neither this failed result nor that possible repair authorizes another GPU attempt or scientific adoption. Preserve the failed package and all 47 requirements.
