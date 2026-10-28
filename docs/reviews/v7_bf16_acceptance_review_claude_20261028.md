# Review of the failed V7 BF16 acceptance check

**Reviewer:** Claude Code. **Date:** October 28, 2026. **Scope:** Codex's report `docs/reviews/v7_gpu_acceptance_codex_20261028.md`, the recipe `docs/reviews/v7_execution_codex_20261028.md`, `src/mb/v7_acceptance.py`, `tests/test_v7_kv_gpu.py`, and the saved acceptance files `bf16_baseline.json`, `bf16_comparison.json` and `saved_inputs.json`. The files were extracted from the SD archive `remote-control/persistent-data-cache.tar.gz`; their SHA256 values match `archive_contents.json`. No model or GPU was run. The acceptance module collects no ownership readouts, so none were available or read.

## Verdict: no engine defect; the acceptance rule cannot tell a correct engine from a broken one

The check failed because of how it was built, not because of the translated read. Replace the rule (recommendation below) before rerunning. The failure and this review stay in the record.

## Findings

**1. The check never runs the engine's translated path.** `capture()` copies the caches to fp32 CPU tensors, and `rephase_keys` is applied to those copies. `kv_attention` with `kv_position="before_own"` does not run. What the check measures is whether a BF16 prefill at positions [0, L), rotated exactly, equals a BF16 prefill at positions [−L, 0). That is a property of the model's BF16 RoPE arithmetic, not of our code.

**2. The excess lies in the reference, not in the rotation.**
- Values are never rotated, yet V exceeds its envelope in all failing comparisons: V RMS 0.2677 against 0.2635 (row 9, batch 1), and V maximum 28.81 against 28.19 (row 2). The read-time translation cannot produce a V error.
- Key error tracks value error exactly. The median ratio of key RMS to value RMS is 0.294 in the padding baseline and 0.299 in the comparison. A rotation error would raise keys relative to values; no such rise appears.
- Final logits pass: median logit RMS 0.0712 in the baseline and 0.0708 in the comparison.

**3. The baseline and the comparison measure two different noise sources.**
- The baseline varies only the padding width. Batch-1 rows are exactly zero. Rows 6 and 7 are also exactly zero at every batch size, because their pair already has the maximum width (381 tokens).
- The comparison varies the absolute positions. At identical padding, rows 6 and 7 show nonzero error (key RMS 0.026 and 0.068).
- The two sources are the same size at the median (key RMS 0.0257 vs 0.0271; value RMS 0.0861 vs 0.0908). Nothing makes one a bound for the other.

**4. A maximum-versus-maximum rule fails by chance.**
- Batches 4, 8 and 12 reuse the same padding width for many rows, so many samples are exact duplicates (8 of 24 rows are identical across the three batch sizes). After removing duplicates and exact zeros, the baseline has 34 distinct samples and the comparison 58.
- If both came from one distribution, the comparison maximum would exceed the baseline maximum with probability 58/92 = 0.63 for each metric. With six metrics, the rule fails a perfect engine more often than not.
- The reported "4 of 96" exceedances are two distinct events: row 2 at width 381, counted three times, and row 9 at batch 1.

**5. The key error introduced by translation is zero by construction.**
- The FP32 checkpoint test shows that R(−L) applied to native keys equals the keys of a real offset prefill to 3.05 × 10⁻⁵.
- Rotation preserves lengths. The production path computes R(−L)·K in fp32 from the BF16 cache, so its keys differ from the exact relocated keys by exactly the rotated BF16 error that the native keys already carry. Translation adds no key error.
- ORIG and TRANS arms share the same fp32 partner-key path and differ only by the rotation. The primary contrast therefore carries no precision asymmetry between arms.

## Where the rule came from

Recommendation R2 of my engine review proposed judging BF16 agreement against the unmodified path's batch-composition variability. That treated a BF16 offset prefill as the reference, but in BF16 neither computation is ground truth, and batch variability is a different noise source. Codex implemented R2 faithfully, wrote the envelope before computing the comparison, and stopped correctly when it failed.

## The real gap

No GPU test yet compares the numerical output of a translated step with real relocation.
- `tests/test_v7_kv_gpu.py` test 1 checks `rephase_keys` against an offset prefill, outside the engine.
- Test 2 checks geometry, finiteness, isolation and batch consistency of a translated step, but not its value.
- The offline double checks the arithmetic against a dense oracle, with an emulated torch.

The failed BF16 check would not have closed this gap even if it had passed.

## Recommendation (protocol draft §5 and §7 step 1; requires PI approval of the revised draft)

**A. Gate: relocation equivalence through the production path, in FP32, on real inputs.**
- Use the 12 saved `v7_dev` inputs (banks of 361–381 tokens, so per-row offsets vary under padding).
- Condition (i): the production translated arm (KV-P, w2, all layers, `kv_position="before_own"`), with B prefilled natively.
- Condition (ii): the native arm (δ = 0), with B's bank prefilled at positions [−L_B, 0) and the same span declarations. A's state is identical in both.
- Compare the receiver (A) rows over the eight teacher-forced ticks used for R1: logits and the own/donor span masses.
- **Pass:** within the FP32 tolerances already in `tests/test_v7_kv_gpu.py`: 3 × 10⁻³ absolute and 2 × 10⁻³ relative for logits, and 2 × 10⁻³ absolute for masses (the file's cache-level tolerance). No new number is introduced.
- A correct implementation passes with certainty. A wrong sign, wrong δ, wrong per-row padding offset or wrong head mapping misses by orders of magnitude.

**B. Descriptive: the same comparison in BF16.** Report it beside the native padding variability and the failed check's data. It is not a gate, because in BF16 neither side is ground truth.

**C. Then the rest of step 1, as approved:** R1 timing, the 336-readout CAP0 runner exercise, and batch selection; then the 80-episode pilot.

**D. Record.** The failed check, its data and this review remain part of the record. The methods appendix will state that an initial BF16 envelope check failed, and why it was replaced.
