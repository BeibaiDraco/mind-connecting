# Pilot report: 20260924-144935_v2_s_kv_strength

- completeness: complete (4160/4160); smoke=False
- C0 baseline (A): ACC_rule +0.120, ACC_word +0.709, CAP 1.000, mass 1.0000, n=40
- strength_selection.json: `{"smoke": false, "min_acc": 5.0, "min_partner_rate": 0.3, "groups": {"ONE|kv|ALL|18": {"arm": "ONE/KV-ALL/w0.3/FULL", "condition": "ONE", "interface": "kv", "kv_scope": "ALL", "layer": 18, "gain": 0.3, "n": 40, "acc_increment": 2.2448328495025636, "acc_word_increment": 3.9245309591293336, "cap_drop": 0.0, "label_mass": 0.9937512730490077, "mass_drop": 0.0062487291861665906, "partner_rate": 0.1125, "partner_rate_c0": 0.0125, "eligible": true, "strong": false}, "ONE|kv|C|18": {"arm": "ONE/KV-C/w0.3/FULL", "condition": "ONE", "interface": "kv", "kv_scope": "C", "layer": 18, "gain": 0.3, "n": 40, "acc_increment": 1.1643709182739257, "acc_word_increment": 3.0045854091644286, "cap_drop": 0.0, "label_mass": 0.996421132221576, "mass_drop": 0.0035788700135982454, "partner_rate": 0.05, "partner_rate_c0": 0.0125, "eligible": true, "strong": false}}, "selection": null, "strength_gate": "not met", "consumable": true}`

ACC increments are paired log-odds differences vs C0 (nat; partner vs unused rule / distractor word).

| arm | n | ACC_rule_inc | se | ACC_word_inc | CAP | CAP_drop | mass | mass_drop | inj/host (C) | eligible |
|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-ALL/w0.01/FULL | 40 | 0.100 | 0.107 | 0.734 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | yes |
| ONE/KV-ALL/w0.03/FULL | 40 | 0.388 | 0.135 | 2.208 | 0.994 | 0.006 | 1.000 | 0.000 | 0.000 | yes |
| ONE/KV-ALL/w0.1/FULL | 40 | 1.356 | 0.241 | 4.033 | 0.994 | 0.006 | 1.000 | 0.000 | 0.000 | yes |
| ONE/KV-ALL/w0.3/FULL | 40 | 2.245 | 0.408 | 3.925 | 1.000 | 0.000 | 0.994 | 0.006 | 0.000 | yes |
| ONE/KV-ALL/w1/FULL | 40 | 8.940 | 1.435 | 9.863 | 0.812 | 0.188 | 0.987 | 0.013 | 0.000 | no |
| ONE/KV-ALL/w3/FULL | 40 | 13.135 | 2.242 | 12.541 | 0.512 | 0.488 | 0.488 | 0.512 | 0.000 | no |
| ONE/KV-C/w0.01/FULL | 40 | 0.185 | 0.119 | 0.150 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | yes |
| ONE/KV-C/w0.03/FULL | 40 | 0.170 | 0.106 | 0.688 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | yes |
| ONE/KV-C/w0.1/FULL | 40 | 0.553 | 0.169 | 2.474 | 0.994 | 0.006 | 1.000 | 0.000 | 0.000 | yes |
| ONE/KV-C/w0.3/FULL | 40 | 1.164 | 0.339 | 3.005 | 1.000 | 0.000 | 0.996 | 0.004 | 0.000 | yes |
| ONE/KV-C/w1/FULL | 40 | 3.330 | 0.808 | 2.464 | 0.869 | 0.131 | 0.997 | 0.003 | 0.000 | no |
| ONE/KV-C/w3/FULL | 40 | 2.845 | 1.022 | 2.344 | 0.650 | 0.350 | 0.542 | 0.458 | 0.000 | no |
