# Llama padding acceptance: native-reference correction

Date: 2026-10-08. Engineering correction after a failed acceptance test, before
the v4 algorithm freeze and before research pilots. The corrected eight-test GPU
certificate is pending execution when this record is written.

## Failure and retained evidence

The original eight-test acceptance from commit `ec6a1fe` passed its first four
tests: native end tokens, no-link/unhooked equivalence, inactive/zero-weight
attention, and donor isolation with one-tick visibility. The fifth test failed
because left-padded batch versus unpadded single-example BF16 logits differed by
0.5625 at their largest coordinate, exceeding the prewritten maximum 0.25. Its
prewritten mean-error bound was 0.025. The original helper also required
cross-shape top-1 agreement when the reference
top-two margin exceeded 0.5, although execution stopped at the maximum-error
assertion before reaching that check. The failed acceptance artifact is retained;
it is not overwritten, relabeled as passing, or replaced by the diagnostic.
The final three tests separately passed in 22.70 seconds, recorded as
`engineering/remaining-tests-01.xml`; that partial run is not an eight-test pass.

A separate process compared the runtime against unhooked native Hugging Face
SDPA on exactly the same token arrays, masks and positions. It then compared
batch shapes, changed only masked pad IDs, forced the SDPA math backend, and
finally used FP32 with TF32 disabled. The model was
`meta-llama/Llama-3.1-8B-Instruct`, pinned revision
`0e9e39f249a16976918f6564b8830bc894c89659`. The short and long native prompts were
40 and 80 tokens. No weights, prompts used by the experiment, parameters, or
research outcomes were selected using this diagnostic.

Evidence retained outside Git:

- GPU JSON: `/workspace/mb-data/engineering/padding_diagnostic_01.json`.
- Local verified JSON: `/private/tmp/mb-v4-execution-20261008/padding_diagnostic_01.json`.
  SHA256: `84730ceedf698f72386ceddba43671f9d51dcaf0f2cb48e05ec8785215996b43`.
- Diagnostic source: `/private/tmp/mb-v4-execution-20261008/diagnose_padding.py`.
  SHA256: `f853c6d6b1bf2b64d0468a70221f7a5c54d3490b0141a5e403f4b2dd6715cdf6`.

## Observed numerical differences

The following values are transcribed directly from the JSON. All comparisons
retained the same top-1 token. The four-label column covers IDs 16, 17, 18 and 19.

| Comparison | Maximum absolute logit difference | Mean absolute difference | Maximum four-label difference |
|---|---:|---:|---:|
| Runtime vs native, padded BF16 | 0.0 | 0.0 | 0.0 |
| Runtime vs native, single BF16 | 0.0 | 0.0 | 0.0 |
| Native BF16, padded vs single | 0.5625 | 0.04351329058408737 | 0.125 |
| Native BF16, same-length batch vs single | 0.5 | 0.05566509813070297 | 0.0625 |
| Native BF16, masked pad IDs changed | 0.0 | 0.0 | 0.0 |
| Native BF16 math, padded vs single | 0.4375 | 0.06255923956632614 | 0.0625 |
| Native BF16 math, same-length batch vs single | 0.3125 | 0.05610029399394989 | 0.125 |
| Native FP32 math, padded vs single | 9.632110595703125e-05 | 8.446750143775716e-06 | 5.7220458984375e-06 |
| Native FP32 math, same-length batch vs single | 6.437301635742188e-05 | 8.493704626744147e-06 | 1.71661376953125e-05 |
| Native FP32 math, masked pad IDs changed | 0.0 | 0.0 | 0.0 |

These comparisons identify native BF16 sensitivity to calculation shape in this
case. They do not identify a padding leak in the adapter: runtime and native
outputs agree bitwise within each shape, changing masked IDs has no effect, and
the discrepancy falls to approximately 1e-4 or less in FP32. Persistence under
BF16 math also means the difference cannot be attributed solely to automatic
SDPA backend selection. Transformers 4.57.1 can additionally switch its GQA
handling when an explicit padding mask is present.

## Corrected engineering contract

The new numerical contract is `llama-native-matched-shape-v2`. This is an explicit
post-failure test-design correction, not a claim that the original threshold
passed. The absolute cross-shape BF16 bounds are removed and replaced with an
independent native reference at each shape; no larger absolute tolerance is
introduced. The cross-shape top-1/margin assertion is also replaced: native
top-1 agreement and margin are recorded, while exact same-shape logit equality
necessarily enforces same-shape top-1 equality. The corrected test makes no
new claim of cross-shape top-1 invariance. Runtime code, BF16 inference, task materials, model revision,
experimental conditions, selection rules and research readouts remain unchanged.

The fifth test now:

1. Tests one unpadded row, two equal-length rows, a left-padded pair, and four
   left-padded rows. It independently builds native masks and positions from the
   original token lists; it does not copy positions or masks from runtime state.
2. Compares runtime logits and every layer's cached K/V tensors bitwise with
   unhooked native SDPA at prefill and after each of three teacher-forced ticks.
   Native and runtime use separate DynamicCache objects. Attention masks,
   next positions, layer count and physical cache length are also checked.
   They share the pinned HF decoder, DynamicCache implementation and SDPA
   kernels; this checks adapter equivalence, not an independent implementation
   of HF attention mathematics.
3. Changes only masked pad IDs at fixed shape in both paths; their logits must
   remain bitwise unchanged at prefill and all three cached ticks.
4. Compares cached and rebuilt-full prefixes against their respective native
   executions. It records the native cached/full and batch-shape discrepancies
   and requires runtime to reproduce them exactly. This discrepancy equality
   follows from the per-shape equality; it is a diagnostic cross-check, not a
   separate numerical bound on native BF16 shape sensitivity.
5. Preserves the same-shape causal-future check: changing the final input token
   must leave all earlier hidden states bitwise identical under both the actual
   runtime `mb_kv` dispatch and native SDPA. The full hidden tensors from those
   two paths must also be bitwise identical.

The remaining seven tests are unchanged. The certificate still requires exactly
eight passes and rejects any skip, failure, or missing test. Its metadata records
the numerical-contract version and hashes this review alongside the tested
sources. The actual model stays BF16 for every acceptance test. The independent
FP32 diagnostic stays in a separate process; an in-place blanket conversion back
to BF16 could otherwise change originally FP32 rotary-position buffers.

This engineering certificate does not demonstrate invariance across arbitrary
batch sizes, eliminate intrinsic BF16 numerical error, replace the four-episode
throughput smoke, or establish baseline suitability or STATIC calibration.
Those separate stages remain required. Any new same-shape mismatch remains a
correctness failure; the native reference cannot be used to waive it.
