# Revised V7 GPU engineering acceptance

Codex, 2026-10-28. **All authorized engineering gates passed. Pilot was not dispatched because storage handling awaits PI confirmation.** This is an engineering report, not an analysis of ownership or pilot outcomes.

## Scope and provenance

The PI approved protocol commit `f978be0`, SHA256 `608350de020b9392672142916484afc953e846344fe733f00e0b3c3f27479e09`, for section 7 steps 1–2. The revised rule replaces the old BF16 envelope with an FP32 production relocation gate; the original failed execution and its review remain unchanged.

Implementation `ce7b635` and precision follow-up `b29e8d3` received independent read-only Claude Code reviews with no blocking findings. Deployment was `3cf67f8`, package source hash `fb5f08b18d897816`, with 296 pinned source/config/test files. The retained H100 SXM instance `58065462` restarted successfully; no replacement instance was rented. The exact four previously saved input/evidence hashes were checked, and all 24 banks were reconstructed from the saved 12 dev episodes and notes without regeneration. The offline suite passed 1402 tests, with 11 skips and one GPU deselection.

## GPU and numerical checks

All three `tests/test_v7_kv_gpu.py` tests passed, with zero errors, failures or skips. The production gate then compared all 12 episodes at batches 1/4/8/12 for eight teacher-forced ticks: **384/384 comparisons passed**, including every A logit and every declared own/donor span element across layers and query heads. Actual model and cache dtypes were checked; FP32 used `matmul_allow_tf32=false`, `float32_matmul_precision=highest`, and the production `mb_kv` attention implementation.

| Maximum absolute error | FP32 relocation | BF16 relocation (descriptive) | BF16 native padding variability (descriptive) |
|---|---:|---:|---:|
| A logits | 0.0000591278 | 0.5 | 0.625 |
| Own span mass | 0.00000292063 | 0.0342962 | 0.0356572 |
| Donor span mass | 0.00000470877 | 0.0381133 | 0.0462448 |

The FP32 elementwise tolerances were unchanged: logits absolute 0.003 plus relative 0.002; span mass absolute 0.002. BF16 values are recorded alongside native padding variability without a gate, envelope comparison or parameter selection. These descriptive maxima do not define a new acceptance rule.

## R1 timing and runner coverage

The stored `steps.jsonl` contains 7,353 per-step timing records, including geometry setup time. Benchmark entries below exclude the first two of eight ticks and report milliseconds per episode-token.

| Episodes per batch | Legacy | Logged native | Logged translated |
|---:|---:|---:|---:|
| 1 | 61.200 | 73.160 | 81.410 |
| 4 | 15.453 | 19.925 | 22.067 |
| 8 | 10.301 | 13.926 | 16.458 |
| 12 | 5.701 | 8.644 | 9.780 |

At batch 12, mean translated wall time was 117.356 ms per step; geometry setup was 24.465 ms, or 20.85%. This measures the current repeated identity/mask work; no caching optimization or scientific setting changed during this attempt.

The CAP0-only runner exercise completed **336/336 trials**, with no missing or failed record: 12 dev episodes, 14 arms, two rotations. It took 673.644 seconds. FP32 comparison took 35.342 seconds, BF16 descriptive comparison 38.283 seconds, and the timing sweep 35.956 seconds. Only after CAP0 passed did the declared timing rule select **12 episodes / 24 rows**. The resulting pilot configuration SHA256 is `5e78668fb891152760bd3a168111db1f6f15d913e4f4fdcdb039d7dbc83f80d6`.

## Storage hold and verified backup

The engineering data occupies 2,335,264,342 bytes. Scaling observed compressed C/R files by the fixed pilot episode/tick counts projects approximately 127 GB for the pilot before a safety margin; the instance had about 93 GB free. This is a storage estimate from archive metadata and declared schedules, not a model-result analysis. PI confirmation is pending for copying completed immutable tick files to SD, verifying SHA256, then deleting only the matching cloud copies during collection. No such deletion occurred. The draft offload helper remains local and undeployed; its three synthetic safety tests passed, but it has not received independent review.

SD root: `/Volumes/VERBATIM SD/mind-connecting-data/execution/v7/20261028-relocation-pilot-v2/`. `engineering_sd_verification.json` confirms all 50 engineering files, 26 control files and four tokenizer assets. The current 28,847 cache members match the earlier verified archive plus one runtime-cache delta. The 11,118,371,202-byte base archive was rehashed as `d673debf6ad21daa98e0afe2377869179c408c2d454751fd1e714311a688ec67`; the 5,964-byte delta is `8c529458c0d8e19ce8f52842d7fe5d796dae5f99ec9996e7b5c9330b0bd3dafb`. Byte verification took 14.238 seconds. Lifecycle receipts are preserved separately.

After verification, Vast confirmed `actual_status=exited`, `cur_state=stopped`, and `intended_status=stopped` at **15:39:33 UTC**. The instance and disk are retained, not destroyed. No pilot, pilot gate script, variance analysis, formal/generalization experiment, ownership inspection or scientific outcome analysis ran. The next action depends on the PI's storage decision; the successful engineering result remains valid evidence for this deployment and host.
