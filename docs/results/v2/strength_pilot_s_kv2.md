# Pilot report: 20260924-151907_v2_s_kv2_strength2

- completeness: complete (5120/5120); smoke=False
- C0 baseline (A): ACC_rule -0.378, ACC_word -0.398, CAP 0.994, mass 1.0000, n=40
- strength_selection.json: `{"smoke": false, "min_acc": 5.0, "min_partner_rate": 0.3, "groups": {"ONE|kv|ALL|18": {"arm": "ONE/KV-ALL/w0.7/FULL", "condition": "ONE", "interface": "kv", "kv_scope": "ALL", "layer": 18, "gain": 0.7, "n": 40, "acc_increment": 5.420242977142334, "acc_word_increment": 7.637934613227844, "cap_drop": 0.04375000000000007, "label_mass": 0.9843692757778506, "mass_drop": 0.01563072515347197, "partner_rate": 0.2, "partner_rate_c0": 0.0375, "eligible": true, "strong": false}, "ONE|kv|C|18": {"arm": "ONE/KV-C/w0.85/FULL", "condition": "ONE", "interface": "kv", "kv_scope": "C", "layer": 18, "gain": 0.85, "n": 40, "acc_increment": 3.506899094581604, "acc_word_increment": 3.367532467842102, "cap_drop": 0.03749999999999998, "label_mass": 0.9875006065526634, "mass_drop": 0.012499394378659212, "partner_rate": 0.1125, "partner_rate_c0": 0.0375, "eligible": true, "strong": false}, "ONE|kv|P|18": {"arm": "ONE/KV-P/w2/FULL", "condition": "ONE", "interface": "kv", "kv_scope": "P", "layer": 18, "gain": 2.0, "n": 40, "acc_increment": 17.595881152153016, "acc_word_increment": 17.261302638053895, "cap_drop": 0.012500000000000067, "label_mass": 0.9846111606300827, "mass_drop": 0.015388840301239881, "partner_rate": 0.65, "partner_rate_c0": 0.0375, "eligible": true, "strong": true}}, "group_order": ["ONE|kv|C|18", "ONE|kv|ALL|18", "ONE|kv|P|18"], "selection": {"arm": "ONE/KV-P/w2/FULL", "condition": "ONE", "interface": "kv", "kv_scope": "P", "layer": 18, "gain": 2.0, "n": 40, "acc_increment": 17.595881152153016, "acc_word_increment": 17.261302638053895, "cap_drop": 0.012500000000000067, "label_mass": 0.9846111606300827, "mass_drop": 0.015388840301239881, "partner_rate": 0.65, "partner_rate_c0": 0.0375, "eligible": true, "strong": true}, "strength_gate": "pass", "consumable": true}`

ACC increments are paired log-odds differences vs C0 (nat; partner vs unused rule / distractor word).

| arm | n | ACC_rule_inc | se | ACC_word_inc | CAP | CAP_drop | mass | mass_drop | inj/host (C) | eligible |
|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-ALL/w0.4/FULL | 40 | 3.955 | 0.819 | 2.822 | 1.000 | -0.006 | 0.988 | 0.012 | 0.000 | yes |
| ONE/KV-ALL/w0.5/FULL | 40 | 3.912 | 0.876 | 3.904 | 0.994 | 0.000 | 0.988 | 0.012 | 0.000 | yes |
| ONE/KV-ALL/w0.6/FULL | 40 | 4.059 | 0.875 | 5.467 | 0.975 | 0.019 | 0.984 | 0.016 | 0.000 | yes |
| ONE/KV-ALL/w0.7/FULL | 40 | 5.420 | 1.102 | 7.638 | 0.950 | 0.044 | 0.984 | 0.016 | 0.000 | yes |
| ONE/KV-ALL/w0.85/FULL | 40 | 7.864 | 1.299 | 9.195 | 0.912 | 0.081 | 0.987 | 0.013 | 0.000 | no |
| ONE/KV-C/w0.4/FULL | 40 | 2.447 | 0.460 | 2.667 | 0.994 | 0.000 | 0.994 | 0.006 | 0.000 | yes |
| ONE/KV-C/w0.5/FULL | 40 | 2.690 | 0.496 | 2.459 | 0.994 | 0.000 | 0.991 | 0.009 | 0.000 | yes |
| ONE/KV-C/w0.6/FULL | 40 | 2.909 | 0.516 | 2.523 | 0.988 | 0.006 | 0.988 | 0.012 | 0.000 | yes |
| ONE/KV-C/w0.7/FULL | 40 | 3.051 | 0.460 | 2.661 | 0.988 | 0.006 | 0.988 | 0.012 | 0.000 | yes |
| ONE/KV-C/w0.85/FULL | 40 | 3.507 | 0.519 | 3.368 | 0.956 | 0.037 | 0.988 | 0.012 | 0.000 | yes |
| ONE/KV-P/w0.3/FULL | 40 | 3.828 | 0.711 | 5.060 | 0.988 | 0.006 | 1.000 | 0.000 | 0.000 | yes |
| ONE/KV-P/w0.5/FULL | 40 | 4.457 | 0.888 | 5.066 | 0.988 | 0.006 | 1.000 | 0.000 | 0.000 | yes |
| ONE/KV-P/w1/FULL | 40 | 5.931 | 1.241 | 6.675 | 0.988 | 0.006 | 0.997 | 0.003 | 0.000 | yes |
| ONE/KV-P/w2/FULL | 40 | 17.596 | 2.096 | 17.261 | 0.981 | 0.013 | 0.985 | 0.015 | 0.000 | yes |
| ONE/KV-P/w3/FULL | 40 | 27.644 | 0.939 | 23.643 | 0.938 | 0.056 | 0.971 | 0.029 | 0.000 | no |
