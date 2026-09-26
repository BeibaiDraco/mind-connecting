# Index of results for protocol v2

Protocol: [PROTOCOL_V2.md](../../protocol/PROTOCOL_V2.md) (tag `protocol-v2`, freeze manifest [FREEZE_protocol_v2.txt](../../protocol/FREEZE_protocol_v2.txt)).
Follow-up studies: [PROTOCOL_V3.md](../../protocol/PROTOCOL_V3.md) (draft, pilots yet to run). Research decisions are in [decision_log.md](../../../decision_log.md).

Raw data (records, tick logs, per-stage JSON) are on the SD card at `/Volumes/VERBATIM SD/mind-connecting-data/results/<run_id>/`, and on the GPU machine at `/workspace/mb-data/results/<run_id>/`. This directory holds only summary reports, all of which can be regenerated with the scripts under `scripts/`.

## Strength pilots (looking only at ACC, capability and format)

| File | run_id | Conclusion |
|---|---|---|
| [strength_pilot_s_kv1.md](strength_pilot_s_kv1.md) | 20260924-144935_v2_s_kv_strength | First round of KV reading; did not meet the strength standard (pre-review implementation; results kept for reference) |
| [strength_pilot_s_kv2.md](strength_pilot_s_kv2.md) | 20260924-151907_v2_s_kv2_strength2 | Passed: K* = KV-P w2 (ACC +17.6, hit rate 65%, CAP drop 0.013) |
| [strength_pilot_s_static_r.md](strength_pilot_s_static_r.md) | 20260924-153829_v2_s_static_match-r | STATIC 0.03 matches R-ONE(0.2) |
| [strength_pilot_s_static_k.md](strength_pilot_s_static_k.md) | 20260924-154706_v2_s_static_k_match-k | STATIC 0.4 is closest to K*, but "not matched" (+11.1 vs +18.2) |
| [g1_balanced_checks.txt](g1_balanced_checks.txt) | around 20260924-154429 / 161154 | Materials for study E: balanced failed the rehearsal check, balanced2 passed |

## Signal pilots (80 episodes; go / no-go decision for each study)

| File | run_id | Conclusion |
|---|---|---|
| [signal_pilot_sig1.md](signal_pilot_sig1.md) | 20260924-155317_v2_sig1_signal | C go; B_R, A_R no-go |
| [signal_pilot_sig2.md](signal_pilot_sig2.md) | 20260924-161505_v2_sig2_signal | D, A_K go; B_K no-go; G2-KV passed |
| [signal_pilot_sigE.md](signal_pilot_sigE.md) | 20260924-164449_v2_sigE_signal | E go |
| [diag_b_exploratory.md](diag_b_exploratory.md) | 20260924-170251_v2_diag_b_explore | Exploratory: two-way memory reading → swap; two-way reading of live states → merging into one (gave rise to B′ in v3) |

## Confirmatory experiments (N = 600)

| File | run_id | Status |
|---|---|---|
| [confirmatory_v2_main.md](confirmatory_v2_main.md) | 20260924-172152_v2_main_confirm (diagnostics: 20260924-192633_v2_main_diag_confirm) | Done: studies C, D, A_K |
| [confirmatory_v2_bal.md](confirmatory_v2_bal.md) | 20260924-193405_v2_bal_confirm | Done: study E (52,800/52,800) |
| [dose_v2_ext.md](dose_v2_ext.md) | 20260924-210346_v2_ext_dose_confirm | Done: KV-P strength sweep (descriptive, 41,400/41,400) |

**Confirmatory results of v2_main** (Holm correction within family; 95% intervals from 10,000 bootstrap resamples):

- **D**: K*−C0 on M +55.8 [55.0, 56.6], on M_NOW +54.7 [53.7, 55.6].
- **A_K**: K*−STATIC(0.4) on M +60.3 [59.3, 61.3] (strength not matched).
- **C** (on M_NOW):
  - untag−tag +26.6 [24.5, 28.8];
  - self−untag −19.5 [−21.5, −17.4], significant but in the opposite direction to the prespecified one;
  - stranger−tag −0.02 [−0.27, 0.25].
- **G2-KV** (formal sample): rule lower bound +34.3, secret word lower bound +32.1.

**Confirmatory results of v2_bal** (study E, rehearsal-balanced materials; Holm correction within family):

- K*−C0 on M: +52.5 [51.6, 53.5] (p < 0.001). The same comparison under the v1 materials is +55.8. Claiming is not because "one's own rule was rehearsed and Robin's was not".
- R-ONE(0.3)−C0 on M: −0.05 [−0.15, 0.05] (p = 0.32). On both the self question and the Robin question, the residual interface biases A toward the partner's rule by about +5.9, so M is about 0: its leakage does not distinguish "me" from "others", and the slight drop in M seen in v1 no longer appears after rehearsal balancing.

**KV-P strength sweep** (descriptive, 300 episodes, the first 300 of the v2_main split; side A, all relative to C0):

| w | ΔM | ΔACC-rule | CAP drop | Partner attention | Self-report mentions partner's code word | Self-report mentions own rule |
|---|---|---|---|---|---|---|
| 0 (C0) | — | — | — | — | 0% | 53% |
| 0.3 | +0.7 | +2.4 | 0.005 | 0.16 | 0% | 44% |
| 0.5 | +3.6 | +2.8 | 0.008 | 0.23 | 2% | 44% |
| 1 | +32.0 | +4.7 | 0.008 | 0.36 | 50% | 16% |
| 2 | +55.8 | +19.0 | 0.018 | 0.50 | 99% | 1% |
| 3 | +56.7 | +27.4 | 0.041 | 0.58 | 100% | 0% |

- Claiming rises steeply between w = 0.5 and 1, and is close to saturation from w = 2 on. At w = 1 the ACC increment is only +4.7, while M has already reached +32.
- In open self-reports, A talks about the partner's code word as its own, does not mention the partner's name (about 0% at every level), and says "nothing unusual". The share answering "two minds / partly shared" actually falls at w = 2 and 3 (−0.10, −0.12).
- w = 3 exceeds the prespecified engineering threshold and is descriptive only.
