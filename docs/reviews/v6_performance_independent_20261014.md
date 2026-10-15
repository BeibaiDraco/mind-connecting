# Independent review of the opt-in V6 performance candidate

Date: 2026-10-14 (America/Chicago). Reviewer: a separate Codex review agent.
Baseline: `9fded38` (`chore: claim offline v6 performance preparation`).

Disposition: no unresolved blocker to retaining this as an **offline, opt-in
candidate**. Native exact equivalence, speed improvement and production adoption
remain unverified and are not approved by this review.

## Scope and boundary

Reviewed the new `src/mb/v6_performance.py`, its workload-audit entry point, and
the new offline and prepared CUDA tests against `src/mb/v6_native.py`, the
scheduler, the adopted V6 protocol, and the execution addendum. The review
did not change the implementation, historical reviews, frozen source, scientific
settings, budget or execution authority. It inspected no scientific outcomes,
used no provider service and ran no model or GPU operation.

The candidate is separate from the production backend. Its import and workload
audit do not import torch, and inherited constructors refuse unauthorized model
construction before importing torch. There is no production runner or admission
path importing this candidate.

## Findings and validation

The bounded CPU packing preserves input order, tensor dtype, shape and contiguous
values. Each packed group starts with a fresh concatenation, so CPU results do not
alias the original source, including when the source is already on the CPU.
Different dtypes/devices flush a group, preventing a dtype view from beginning at
an incorrectly aligned byte offset. Oversized tensors retain the reference copy
path. Sharing a newly owned CPU allocation between nonoverlapping archive tensors
changes serialization storage layout; it does not change the tensors' logical
payload or the existing logical checksum algorithm.

The foreign-window cache invokes the reference zero-gain validation before every
lookup. It therefore retains ordinary-token, position/order/count, owner/model,
shape/device/dtype and source-version checks. A cache hit additionally checks the
cached concatenations' stamps. Its key includes each strongly retained payload's
object identity and export metadata; eviction bounds retention to two windows.
Actual gain remains an attention argument, so gain-independent cached K/V values
do not suppress or change its application. The inherited attention implementation
reads these concatenations without writing them.

Export archival checks the digest of the exact copied values that will be saved.
This preserves the existing full-payload checksum and removes the need for the
reference's separate source-to-host hash transfer. It does not omit a checksum,
token, forward pass, readout, snapshot or tape. State loading and other validation
continue to use the unchanged native implementation.

One reproducible profiler cleanup edge was reported to the implementation agent:
an already present `_v6_profile_active = False` instance attribute was deleted
when profiling ended, rather than restored. The implementation agent corrected
this; independent inspection and the new regression test confirm preservation of
both the flag and an existing instance-specific method. Exception cleanup and
nested-profiler rejection are also covered. No numerical or scientific-state
defect was found in the two optimization paths during this review.

The initial prepared native test uses tiny float32 CUDA models. The reviewer
requested direct PyTorch tests of BF16/mixed-dtype packing, noncontiguous and
oversized inputs, and serialization round trips because NumPy doubles alone do
not establish PyTorch dtype-view or storage semantics. These were added, including
CPU-source ownership and empty tensors; their source was independently reviewed.
The offline archive comparison was also corrected to instantiate the actual
reference class, avoiding dynamic dispatch to the candidate override. These
prepared CUDA tests remain unrun on the local Mac and are not pinned-checkpoint
acceptance.

## Independently reproduced offline checks

- Existing offline suite, collected before the new performance tests were added:
  **758 passed, six skipped, one GPU test deselected**.
- Final performance-only suite: **16 passed** using CPU array doubles. This was
  rerun after the profiler fix and corrected reference archive comparison.
- Fresh-process authorization/import check: both unauthorized constructors
  refused; importing the candidate and executing the workload audit did not
  import torch.
- The real scheduler with explicitly shortened synthetic clocks reports
  **80 paired work periods, 10,240 work tokens at the adopted clock, 328 readouts,
  four pair checkpoints and twelve tapes**. With the text reference it reports
  352 readouts, 768 additional text work tokens, and 192 rather than 160
  preparation tokens. These are structural counts, not measured GPU timing,
  generated scientific evidence or estimates of question-prefill token counts.
- Git inspection showed no changes to `src/mb/v6_native.py`,
  `src/mb/v6_runtime.py` or the frozen protocols.

Reviewed file SHA256 values:

| File | SHA256 |
|---|---|
| `src/mb/v6_performance.py` | `c3ea4317c376d2c3ce005c5086295b755291650b74afe0d66f4984fccc5a93b8` |
| `tests/test_v6_performance.py` | `3cd81341ff87fb9f3e74c837b84c8811bf022cae00b46115a3b04d7b716760f7` |
| `tests/test_v6_performance_gpu.py` | `8f5059960fa898f8091ac3179c1762a0b5456c8d3d095c50827cc7a94b8f6c88` |
| `scripts/v6_performance_audit.py` | `e4e679755db0a441aec38a7a04a7df2bea224f3fa444411f700a7b02c492c5c5` |

## Required interpretation before any later adoption

Offline review cannot establish native exact equivalence or a speed improvement.
The prepared CUDA comparisons require exact tokens, probabilities, legal logits,
state/export digests and logical archive contents; an approximate numerical
tolerance must not replace these checks for this candidate. Both pinned model
paths and saved/restored replay remain actual-hardware acceptance obligations.

Packed storage can produce different serialized file bytes even when logical
archive contents and checksums are identical. Existing successful files must
remain untouched. Any future source adoption requires a separately preserved
source/amendment identity and renewed exact-source acceptance; it cannot silently
replace the frozen backend or reuse an old resume identity.

Profiling times are inclusive host times and can overlap or omit asynchronous GPU
work. Only complete, appropriately synchronized episode timing with archival and
the whole remaining-workload forecast can support a financial continuation.
These changes do not remove the sequential per-token question prefills. No
budget reset, sample reduction, changed gate or paid launch follows from this
review.
