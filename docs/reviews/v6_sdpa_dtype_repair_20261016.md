# V6 SDPA dtype repair: local verification only

The PI requested a repair after the first new-card CUDA test failed. This
change is local engineering work. No GPU restore, new rental, model execution,
scientific collection or automatic continuation is part of this repair.

## Cause and narrow correction

The pinned PyTorch 2.6.0 efficient-attention CUDA implementation requires its
additive bias to have the query dtype. The original isolated `JointKernel`
allocated FP32 bias for both FP32 and BF16 queries. This matches the preserved
hardware error. See the [version-pinned upstream implementation](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/native/transformers/cuda/attention.cu#L1249-L1273).

Allocate the padded bias directly in `q.dtype`, then take the logical-width
view. The padding still supplies an eight-element row alignment without adding
keys to attention. Casting an already sliced view could lose that alignment.
The isolated prototype version advances to 2. Kernel selection, head expansion,
causal visibility, zero-gain exclusion and all predefined gains remain unchanged.
The compiled-flex score modifier and packed backend retain their existing
FP32 bias arithmetic; the SDPA storage requirement is not applied to them.

BF16 storage rounds the finite logarithmic gain. The independent FP64 oracle
continues to use the original gain, not a rounded replacement. The existing
engineering ceiling remains `2**-7 * value_scale`; it does not grant scientific
numerical equivalence. No scientific protocol, sample, selector or tolerance
was changed, and all previous failure records and source packages are retained.

Independent review identified that the original stage-A draft explicitly
required FP32 bias. The new engineering precision note,
`docs/runbooks/V6_SDPA_DTYPE_REPAIR_20261016.md`, now declares the version-2
difference and preserves that original failed contract. Both preparation paths
bind the note hash and an explicit `operator_bias_policy`; missing or altered
policy is rejected. This is a new unadopted engineering candidate, not a
retroactive repair of the old trial's admission result.

## Regression coverage and limits

- Twelve CPU API-contract cases exercise the actual mask-building and dispatch
  code across symbolic BF16/FP32 dtype tags, causal positions, zero/positive
  gains, empty/nonempty foreign windows and scalar/chunked shapes. They check
  mask dtype/device/strides/values, head expansion, source immutability and
  efficient-only dispatch. Their tags do not emulate BF16 arithmetic or CUDA.
- Replaying these cases against the pre-repair source produces six BF16
  failures and six FP32 passes. The repaired source passes all twelve.
  The local receipt is
  `/private/tmp/mb-v6-sdpa-repair-20261016/final_local_receipt.json`.
- Twenty-four additional CUDA cases cover BF16 and FP32, all four gains and
  foreign windows 0/1/16. They inspect actual dispatch dtype/alignment and
  compare against the unchanged independent oracle, with exact repetition,
  future-key isolation and unchanged source tensors. They are written and
  syntax-checked, **not executed** locally.
- The existing 23 CUDA gate cases are retained. A future freshly bound
  controller must require all 47 cases and preserve no-skips/fail-closed
  handling. The historical controller's 23-case binding must not be reused
  or edited in place. Both real-model checks still follow full CUDA admission.

The final offline suite passed 1,220 tests, with nine skipped and one GPU test
deselected, in 41.70 seconds. The focused dispatch/package suite passed 50.
Fresh inert packages are in the private repair root's `trial-plan-02/` and
`operator-plan-01/`. The complete-trial package binds 70 sources and hashes to
`88d814a248153cffa250ab25e22693ca6df1e9644ab8c971960178f063262b36`.
The original 68-source package remains byte-identical; both that package and
the intermediate repair `trial-plan-01` are correctly rejected as stale by the
new implementation. No original package or historical controller was modified.

Final independent review accepted this local snapshot with no unresolved
actionable findings. The reviewer separately passed 354 focused offline checks
and validated both fresh packages and their bound precision note. The review
accepts the local repair only; the 47 CUDA cases and real-model comparisons
remain unrun.

No successful CUDA result, model equivalence, speedup or full-workload cost
forecast follows from these local checks. Paid launch remains a separate,
freshly bound operational step under the original cumulative financial origin
and all prior charges. The failed trial stays closed and its automation paused.
