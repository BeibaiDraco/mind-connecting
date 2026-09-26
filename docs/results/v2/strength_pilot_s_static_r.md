# Pilot report: 20260924-153829_v2_s_static_match-r

- completeness: complete (2880/2880); smoke=False
- C0 baseline (A): ACC_rule -0.028, ACC_word +0.306, CAP 1.000, mass 1.0000, n=40
- static_match.json: `{"smoke": false, "matches": {"ONE/L24/raw/g0.2/FULL": {"static_arm": "STATIC/L24/raw/g0.03/FULL", "gain": 0.03, "target_acc": 1.3418840885162353, "static_acc": 1.0971784830093383, "matched": true}}, "consumable": true}`

ACC increments are paired log-odds differences vs C0 (nat; partner vs unused rule / distractor word).

| arm | n | ACC_rule_inc | se | ACC_word_inc | CAP | CAP_drop | mass | mass_drop | inj/host (C) | eligible |
|---|---|---|---|---|---|---|---|---|---|---|
| ONE/L24/raw/g0.2/FULL | 40 | 1.342 | 0.459 | -0.219 | 0.994 | 0.006 | 1.000 | 0.000 | 0.202 | yes |
| STATIC/L24/raw/g0.005/FULL | 40 | 0.045 | 0.137 | -0.072 | 1.000 | 0.000 | 1.000 | 0.000 | 0.005 | yes |
| STATIC/L24/raw/g0.01/FULL | 40 | 0.364 | 0.100 | 0.115 | 1.000 | 0.000 | 1.000 | 0.000 | 0.010 | yes |
| STATIC/L24/raw/g0.015/FULL | 40 | 0.332 | 0.158 | 0.166 | 1.000 | 0.000 | 1.000 | 0.000 | 0.015 | yes |
| STATIC/L24/raw/g0.02/FULL | 40 | 0.626 | 0.201 | 0.109 | 1.000 | 0.000 | 1.000 | 0.000 | 0.020 | yes |
| STATIC/L24/raw/g0.03/FULL | 40 | 1.097 | 0.186 | 0.025 | 1.000 | 0.000 | 1.000 | 0.000 | 0.030 | yes |
| STATIC/L24/raw/g0.05/FULL | 40 | 1.817 | 0.298 | -0.155 | 1.000 | 0.000 | 1.000 | 0.000 | 0.051 | yes |
| STATIC/L24/raw/g0.1/FULL | 40 | 4.211 | 0.566 | -0.147 | 0.994 | 0.006 | 1.000 | 0.000 | 0.101 | yes |
