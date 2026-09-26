# Pilot report: 20260924-230325_v3_s_static_a_match

- completeness: complete (2240/2240); smoke=False
- C0 baseline (A): ACC_rule +0.012, ACC_word -0.017, CAP 0.994, mass 1.0000, n=40
- static_match.json: `{"smoke": false, "matches": {"ONE/KV-P/w1/FULL": {"static_arm": "STATIC/L24/raw/g0.1/FULL", "gain": 0.1, "target_acc": 4.214813542366028, "static_acc": 3.586756157875061, "matched": true}}, "consumable": true}`

ACC increments are paired log-odds differences vs C0 (nat; partner vs unused rule / distractor word).

| arm | n | ACC_rule_inc | se | ACC_word_inc | CAP | CAP_drop | mass | mass_drop | inj/host (C) | eligible |
|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w1/FULL | 40 | 4.215 | 0.935 | 6.849 | 0.988 | 0.006 | 1.000 | 0.000 | 0.000 | yes |
| STATIC/L24/raw/g0.1/FULL | 40 | 3.587 | 0.566 | 0.161 | 0.994 | 0.000 | 1.000 | -0.000 | 0.101 | yes |
| STATIC/L24/raw/g0.15/FULL | 40 | 5.955 | 0.873 | 0.297 | 0.994 | 0.000 | 1.000 | -0.000 | 0.151 | yes |
| STATIC/L24/raw/g0.2/FULL | 40 | 7.655 | 1.025 | 0.132 | 0.994 | 0.000 | 1.000 | 0.000 | 0.202 | yes |
| STATIC/L24/raw/g0.25/FULL | 40 | 9.270 | 1.175 | 0.163 | 0.988 | 0.006 | 1.000 | -0.000 | 0.254 | yes |
| STATIC/L24/raw/g0.3/FULL | 40 | 9.979 | 1.113 | -0.088 | 0.988 | 0.006 | 1.000 | 0.000 | 0.305 | yes |
