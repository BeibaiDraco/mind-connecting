# Llama numerical diagnosis: supported result and minimum next probe

Reviewed by Codex (`/root/v6_perf_review`), with independent root spot checks.
CPU-only source/saved-array analysis. No torch import, model/GPU call, source
change, threshold relaxation, numerical adoption, or retry was performed.

**Finding:** an execution-shape difference exists before first-layer attention.
All original-prefix K/V bytes agree across reference/candidate at every layer.
Candidate layer-0 K/V agrees exactly across gains 0/0.25/0.5. Native layer-0
K/V agrees between 0.25 and 0.5, but its gain-zero T17 path differs from its
positive-gain T1 path: 25/17,408 K entries (max 0.015625) and 51/17,408 V
entries (max 0.0001220703125). Native gain-zero lane-0 layer 0 exactly matches
candidate layer 0. This local difference is the reference's shape-path switch,
not first-layer donor/gain arithmetic. Normalization versus projection GEMM
cannot be separated without additional intermediates; V rules out RoPE alone.

The no-donor lane is exactly gain-invariant within each backend, including all
64 full K/V tensors, hidden states and logits. Native/candidate nevertheless
differ there at every gain (max logit difference 0.1875), supporting a separate
shape-path contribution rather than observed gain leakage. In lane 0 at gain
zero, layer 0 agrees but layer 1 already differs; later attention/MLP/projection
effects remain confounded.

At gain 0.5, position 9 still fails: reference river=12.1875 versus
organization=12.125; candidate ties both at 12.1875 and selects organization.
The failed position's logit maximum difference is 0.1328125. The whole-check
maximum 0.484375 occurs at position 2. Differences precede the failed choice;
the mismatch is not the onset of numerical divergence. Inputs remain the same
teacher-forced river sequence, so later agreement cannot prove free-running
trajectory equivalence. Gain 1 is unrun; retain the failed gate.

## Minimum future hardware diagnostic, not authorized here

Target the demonstrated first-layer discrepancy first, with the same pinned
weights/dtype/runtime and only the repeated river token:

1. Capture embedding and layer-0 RMSNorm inputs/outputs at original T1, T3,
   T17, and B2/T16 shapes. Retain full bytes, shapes/strides, finite checks and
   actual mathematical row identity. Do not infer identical normalized inputs
   merely from identical token IDs.
2. Select **one exact saved normalized vector**, copy its bytes into each
   declared layout, and evaluate the same V projection. Keep the row placement
   and shape declared in advance; verify input equality before each call.
   Separate runs using each layout's own RMSNorm output quantify the earlier
   normalization contribution. Do not overwrite original comparisons.
3. For the differing V coordinates, retain the common quantized input and
   corresponding fixed weight rows and compute an explicit FP32 scalar dot
   with a recorded summation order (not another opaque GEMM) as a diagnostic
   oracle. An FP64 sum of the same quantized operands can additionally expose
   accumulation-order effects. These references diagnose rounding; neither
   creates a scientific tolerance nor changes the original BF16 decision rule.
4. If the question remains specifically why the position-9 winner changed,
   use the optional common-hidden lm_head shape comparison described in
   `DIAGNOSIS.md`. Full hidden differences and attention contributions still
   require separately controlled common-input comparisons.

No gain search, epsilon tuning, tie-break repair, significance comparison, or
automatic candidate substitution follows from these probes. The head probe
and attention ablations are optional later localization steps; the immediate
minimum above addresses the already observed pre-attention shape effect.

## Exact input binding and outputs

All 22 used evidence files matched sealed lengths/SHA256; all six inspected
repository source files matched the executed package. Phase NPZs exactly
matched aggregate arrays and every published final-tensor maximum/byte-equality
flag was reproduced. Full paths/hashes are in `input_verification.json`.

| Main NPZ | SHA256 |
|---|---|
| gain-0_0.npz | ff876a2700149108547c773459fdcdb2569d1281c9746b7284d50e33575ca5f5 |
| gain-0_25.npz | 13270c15a4cd76996374b72442e34f265041f687b324db489c74ce32c2152dbc |
| gain-0_5.npz | 9b429550ee5a74c27bb55e751dbafa5e91fa0bffb7a99f5705a91533f9ba46c5 |

The inventory receipt SHA256 is
`d8d45ba17b47acfbe8154746a9c6bb37fee9403265da8175a1f9aa062f33f50f`.
Machine-readable per-position, per-layer K/V and cross-gain findings, plus
reproduction scripts, are retained in this directory. Historical source,
thresholds, failed run, raw SD inputs and prior output manifest remain intact.

## Preservation and root verification

Fourteen diagnostic files, including scripts, input identities, both immutable
output manifests and root spot checks, were copied to the SD directory
`/Volumes/VERBATIM SD/mind-connecting-data/v6/llama-numerical-diagnosis-20261018/`
and independently rehashed. Final derivative manifest SHA256:
`1cd1e0f69852605bb74ae25f34913018c1cc910f9143d6eb0f377f5de9e13725`.
Root independently reproduced the failed-position top tokens/max difference,
the 25 K / 51 V first-layer changes, native positive-gain equality, candidate
cross-gain equality and native gain-zero/candidate equality. The original raw
inputs remain unchanged. This diagnosis neither passes the failed Llama check
nor establishes full scientific equivalence. Qwen full engineering timing is
executing separately under the PI's explicit split instruction.
