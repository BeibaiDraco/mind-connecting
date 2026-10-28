# V7 H100 acceptance: BF16 check failed; pilot not dispatched

Codex, October 28, 2026. This is an engineering report, not a scientific outcome analysis.

## Scope and deployed sources

The PI approved only section 7 steps 1–2 of protocol commit `5b78a32`, SHA256 `39c607bb5a51cdc480c6dee6780fb74970b1a2a2678b231029510888770768c0`. The approval and lifecycle clarification are recorded in `decision_log.md`. Deployed code is `9cb073a5358f82c0fdd3bd2e1541b86108426874`, source hash `1959111a8d167e62`; 121 source files were pinned and verified before execution. The prospective recipe is in `v7_execution_codex_20261028.md` and `src/mb/v7_acceptance.py`.

One Vast instance, `58065462`, label `v7-approved-20261028`, provided an H100 SXM 80 GB and 120 GiB disk at a quoted USD 2.6431/hour including storage. The environment used Python 3.12, torch 2.6.0+cu124, transformers 4.57.1, tokenizers 0.22.1, and the pinned Qwen checkpoint `cdbee75f17c01a7cc42f958dc650907174af0554`. No local torch or model execution occurred.

## Acceptance result

`tests/test_v7_kv_gpu.py`: **2 passed, 0 failures/errors/skips**, 12.637 seconds in pytest (14.435 seconds for the full subprocess). FP32 actual-offset prefill versus rephased native keys gave maximum absolute K and V differences of `3.0517578125e-05`. The tests also passed native/logged exact equality, finite translated logits, snapshot isolation, GQA dimensions, translated geometry and padding/batch consistency. The sole pytest warning concerns `record_property` with xunit2; the property is present in the retained XML.

The subsequent engineering module generated and saved fixed P inputs for exactly 12 `v7_dev` base episodes. It measured the native BF16 batch-composition envelope at 1/4/8/12 episodes per batch, wrote that envelope before translated comparisons, then compared read-time fp32 key translation with actual BF16 offset prefill. Each cache RMS statistic is the maximum over layers, as specified prospectively.

| Metric | Native batch envelope | Maximum translated comparison | Result |
|---|---:|---:|---|
| K maximum absolute error | 18.125 | 20.793384552001953 | Fail |
| K RMS error | 0.08829154819250107 | 0.10043656826019287 | Fail |
| V maximum absolute error | 28.1875 | 28.8125 | Fail |
| V RMS error | 0.26348504424095154 | 0.26773011684417725 | Fail |
| Full-vocabulary logit maximum absolute error | 1.9375 | 1.8125 | Pass |
| Full-vocabulary logit RMS error | 0.16075366735458374 | 0.1456146538257599 | Pass |

Four of 96 row/batch comparisons exceeded at least one envelope: row 9 at batch 1, and row 2 at batches 4, 8 and 12 (zero-based saved-input row indices). K max/RMS and V max each exceeded the envelope in three comparisons; V RMS in four. No threshold was widened and no acceptance retry was run. This failure does not by itself identify an engine defect or establish the cause of the BF16 discrepancy; it does prevent the approved conditional pilot from proceeding.

The controller stopped at the BF16 failure at 08:07:47 UTC / 03:07:47 Chicago. There was **no pilot dispatch, no CAP0 runner exercise, no full R1 timing sweep and no selected batch size**. No START, PROV, DETECT or other ownership output was collected or opened by this engineering module. No scientific choice was scored and no Claude gate script was run.

## Timing and remaining work

| Completed phase | Seconds |
|---|---:|
| Dependency setup and pinned model download | 320.657 |
| GPU checkpoint subprocess | 14.435 |
| Engineering subprocess, including startup | 28.602 |
| BF16 model load within engineering | 3.484 |
| Fixed input/note generation | 2.075 |
| Native BF16 calibration and translated comparison | 18.485 |

R1 remains pending because the BF16 gate precedes the performance sweep. R2 produced the measured baseline and a failed comparison, not an accepted tolerance or a throughput batch. The 12-episode all-arm CAP0 smoke and 80-episode pilot remain unrun. Claude should review the saved numerical evidence and calibration recipe before any proposed repair or revised acceptance rule is put to the PI; no such revision or rerun is adopted here.

The separate approved registry correction is already committed: `orig_w2_cf` is present for both generalization variants and coverage is five arms/50 trials per episode. No generalization run occurred. The latest offline suite passed 1371 tests, with 11 skips and one GPU deselection, before the commissioning milestone commit.

## Evidence preservation

Private execution root: `/Volumes/VERBATIM SD/mind-connecting-data/execution/v7/20261028-engineering-pilot/`. Exact saved inputs, notes, native reference tensors, all baseline/comparison rows, failure receipts, test XML, source bundle and environment are retained. Persistent HF/model, UV/Python, pip, CUDA, Triton and other configured caches are archived with regular-file SHA256 and symbolic-link targets. Final backup verification and stopped-instance status are recorded in STATUS and the private lifecycle receipts. The failed instance must not be destroyed under this closeout; preserving its disk keeps the diagnostic state available.
