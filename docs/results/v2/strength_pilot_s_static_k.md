# Pilot report: 20260924-154706_v2_s_static_k_match-k

- completeness: complete (2880/2880); smoke=False
- C0 baseline (A): ACC_rule +0.875, ACC_word -0.297, CAP 0.994, mass 1.0000, n=40
- static_match.json: `{"smoke": false, "matches": {"ONE/KV-P/w2/FULL": {"static_arm": "STATIC/L24/raw/g0.4/FULL", "gain": 0.4, "target_acc": 18.171710467338563, "static_acc": 11.06978006362915, "matched": false}}, "consumable": true}`

ACC increments are paired log-odds differences vs C0 (nat; partner vs unused rule / distractor word).

| arm | n | ACC_rule_inc | se | ACC_word_inc | CAP | CAP_drop | mass | mass_drop | inj/host (C) | eligible |
|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL | 40 | 18.172 | 1.641 | 18.498 | 0.969 | 0.025 | 0.992 | 0.008 | 0.000 | yes |
| STATIC/L24/raw/g0.2/FULL | 40 | 7.205 | 0.884 | -1.025 | 0.994 | 0.000 | 1.000 | -0.000 | 0.203 | yes |
| STATIC/L24/raw/g0.3/FULL | 40 | 10.446 | 1.060 | -0.688 | 0.988 | 0.006 | 0.997 | 0.003 | 0.305 | yes |
| STATIC/L24/raw/g0.4/FULL | 40 | 11.070 | 1.091 | -1.403 | 0.981 | 0.013 | 0.997 | 0.003 | 0.408 | yes |
| STATIC/L24/raw/g0.5/FULL | 40 | 10.452 | 1.027 | -0.893 | 0.956 | 0.037 | 0.997 | 0.003 | 0.512 | yes |
| STATIC/L24/raw/g0.6/FULL | 40 | 8.548 | 0.974 | -0.448 | 0.925 | 0.069 | 0.996 | 0.004 | 0.614 | no |
| STATIC/L24/raw/g0.7/FULL | 40 | 6.045 | 0.866 | -0.027 | 0.906 | 0.088 | 0.974 | 0.026 | 0.716 | no |
| STATIC/L24/raw/g1/FULL | 40 | 0.271 | 0.807 | 0.530 | 0.600 | 0.394 | 0.824 | 0.176 | 1.024 | no |
