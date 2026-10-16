# V6 flex structural compilation repair — local candidate

The PI asked how to resolve the failed hardware retest. This is local engineering
work only. The failed source packages, 26 passed / one failed / 20 unrun CUDA
cases, original financial origin and every scientific setting remain intact.
No GPU restore, renewed allowance or scientific numerical adoption is granted.

## Concrete failure and repair

Pinned PyTorch 2.6.0 flex decoding computes its split heuristic from batch and KV
head count using Python `max`. The saved CUDA traceback attempted a Boolean
comparison of a symbolic batch expression in that heuristic. See the
[pinned implementation](https://github.com/pytorch/pytorch/blob/v2.6.0/torch/_inductor/kernel/flex_decoding.py).

Keep dynamic compilation, but specialize Q's batch, head count, query width and
head dimension, and K/V's batch, head count and head dimension. The growing KV
axis stays dynamic. Packed allowed-mask batch/query axes are specialized; its KV
axis and FP32 bias length remain dynamic. Marking occurs inside the traced
function on its final input tensors, which avoids annotating owned inputs outside
the graph. The [pinned mark_static API](https://github.com/pytorch/pytorch/blob/v2.6.0/torch/_dynamo/decorators.py)
supports this in-graph specialization. Marks use individual integer axes because
the in-graph implementation handles one size at a time.

Both JointKernel and PackedBackend use this policy. Attention equations, bias
precision, visibility, KV padding, timestep barriers and output publication are
unchanged. Both candidate identities and new packages bind the policy. The
previous SDPA repair remains; it does not retroactively pass the failed trial.

## Compilation must remain bounded and visible

Each compiler owner receives a distinct Python code object with identical
bytecode/globals/defaults/closure, isolating Dynamo's code-object cache between
tiny fixtures and separately loaded model owners. No global cache limit changes,
cache resets, eager fallbacks or backend alternatives are enabled. Each owner
has a stop-only ceiling of eight compiler callbacks; failure poisons that owner
and cannot be retried. This is a stricter engineering resource guard, not a
prediction that all shapes fit in eight graphs. Torch may reject its own cache
limit sooner. The arbitrary public layout space is not a finite shape catalog.

The current packed trial has at most six batch/query-width combinations
(B=1/2/4, T=1/16). Both fixed checkpoints use Hq=32, Hkv=8, D=128. Kernel guards,
strides or small-value specialization can still create extra graphs, so count
actual callbacks. Preserve each attempt, symbolic input shapes, status and
compiler-callback wall time on success and failure. Callback time excludes other
Dynamo/first-call overhead and GPU execution; keep existing complete phase
timers, including compilation, as the performance measurement.

## Future hardware admission, not an execution authorization

Retain all 47 old CUDA cases and add eight in
`tests/test_v6_flex_compile_gpu.py`: two attention paths across decode/prefill,
twelve KV lengths with stable post-warmup compiler count, nine owners in one
process without resets, and actual checkpoint attention dimensions at all six
batch/query combinations, including twelve production-range KV lengths for
both T1 and T16 at B4. Save compilation counters in JUnit even on failure.
The complete required gate becomes 55 cases, with no skips. Tiny random models
remain limited fixtures; actual-shape operator checks use random tensors and do
not certify real checkpoints or speed.

For the next **proposed** hardware action, use an engineering-only compiler check
with at most 30 minutes from restore intent through verified stop and at most
USD2 additional inside the original cumulative USD100. The last observed rental
rate was about USD1.30/hour: 30 minutes would be about USD0.65 in instance rental,
with remaining proposed allowance for transfers/storage/uncertainty. This is a
containment limit, not a measured completion estimate or a current quote. Budget,
original deadline, availability, guards and a fresh source-bound controller need
admission before dispatch. Do not rent another host or redownload weights merely
for these checks. No paid action is performed by local package preparation.

First run the eight added compiler tests and the two architecture variants of
the previously failing linked-prefill test. If that ten-case diagnostic passes,
the complete 55-case gate still must pass; preserve the same thresholds and
failure rule. End with sealed backup, independent rehash and verified actual
stop. This proposed diagnostic has no real-checkpoint microcheck, full benchmark
or automatic scientific continuation. A later real-model timing run requires a
separate concrete scope and financial admission. Never infer full-plan speed or
cost from these compilation fixtures.

Local tests validate dispatch, source/identity binding, bookkeeping and failure
behavior without importing torch. They do not execute Inductor or CUDA and
cannot prove this repair works on hardware. No compiler success, numerical
equivalence, speedup or whole-experiment forecast is asserted.
