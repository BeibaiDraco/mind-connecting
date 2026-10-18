# V6 real-model benchmark: numerical gate failure and verified closure

## Result

The single bounded engineering attempt reached both real checkpoints. All 55 CUDA tests passed without failures, errors or skips, with collected test identities independently matched to JUnit. Qwen passed the prescribed four-gain micro checks. Llama failed the unchanged greedy-agreement rule at gain 0.5, so its gain 1.0 check and all complete timing fixtures were not run. There is no measured whole-workload speedup or remaining-experiment forecast from this attempt.

| Checkpoint | Gain | Matching greedy choices / checked positions | Outcome |
|---|---:|---:|---|
| Qwen | 0, 0.25, 0.5, 1 | 20/20 at each gain | All prescribed micro checks complete |
| Llama | 0, 0.25 | 20/20 at each gain | These two checks pass |
| Llama | 0.5 | 19/20 | Stop under the original rule |
| Llama | 1 | Unrun | No result |

These are teacher-forced engineering positions, not independent scientific episodes. A matching greedy choice does not establish byte identity or full scientific equivalence. The model revisions, source pins, parameters, clocks and failure rule were unchanged; no retry, scientific-stage execution or numerical adoption occurred.

## Independently reproduced discrepancy

Root and the independent reviewer separately verified the saved trace hash and compared all 20 positions at Llama gain 0.5. Only lane 0, zero-based position 9 changed its greedy choice:

- Reference token: 15140, ` river`; candidate token: 7471, ` organization`.
- Reference preference between these tokens: 0.0625. Candidate preference: 0, with a tie at the maximum.
- Reference top-two margin: 0.0625. Candidate top-two margin: 0.
- Maximum absolute logit difference across all 20 positions and vocabulary entries: 0.484375.

The changed argmax at a tie explains the recorded choice disagreement. The underlying cause of the numerical differences has not been isolated; these observations alone do not prove that rounding is the only cause or that downstream interaction behavior is equivalent. The failed gate is retained rather than retrospectively relaxed.

## Closure and evidence

Restore intent was 01:39:43 UTC on October 18. The worker failed at 01:43:56, and actual provider stop was verified at 01:48:27: a 524.375-second lifecycle. A fresh independent provider query subsequently confirmed the same bound target exited with intended/current/next state stopped; the exact local controller and stop guard were absent. The scheduled check was paused after closure.

Independent rehashing covered 84 remote evidence files, 74 final control files and all 143 prelaunch inputs. The archive is 714,506,240 bytes, SHA256 `f92a8dcd1ee510a7591acf0fda08dd174d5bdba3ec845524766c4523812afbce`. Nineteen additional analysis, independent-audit and financial-evidence files were separately copied and rehashed on the SD card. The historical 61-file backup gap remains unresolved.

Private evidence is under `/private/tmp/mb-v6-execution-20261012/real-model-benchmark-20261018/`, particularly `final_independent_audit.json`, `micro_discrepancy_analysis.json` and `closure_audit_backup.json`. Source package and launch provenance are in `v6_real_model_benchmark_launch_20261018.md`. Repository offline tests remain 1,234 passed, ten skipped and one deselected.

## Consequence

This candidate cannot yet be admitted as a validated replacement for both models. The completed Qwen micro evidence is usable for planning a separately scoped Qwen-only timing test; it is not a complete performance or scientific-admission result. Llama requires a distinct numerical diagnosis or retention of the reference implementation. Neither proposal automatically authorizes another paid attempt, changes the research protocol or discards the second model. The original V6 scientific samples and gates, earlier paper evidence and manuscript remain unchanged.
