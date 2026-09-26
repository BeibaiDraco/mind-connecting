# Pilot report: 20260924-230820_v3_s_live_strength

- completeness: complete (8320/8320); smoke=False
- C0 baseline (A): ACC_rule -0.140, ACC_word -0.556, CAP 0.994, mass 1.0000, n=40
- live_selection.json: `{"smoke": false, "selection": {"PC": {"arm": "TWO/KV-PC/w2+0.1/FULL", "condition": "TWO", "interface": "kv", "kv_scope": "PC", "kv_w_live": 0.1, "layer": 18, "gain": 2.0, "n": 40, "acc_increment": 19.27692928314209, "acc_word_increment": 18.375280094146728, "cap_drop": 0.03749999999999998, "label_mass": 0.9812143958365546, "mass_drop": 0.018785602487064845, "partner_rate": 0.725, "partner_rate_c0": 0.0625, "eligible": true, "eligible_B": true, "cap_drop_B": 0.03125, "one_arm": "ONE/KV-PC/w2+0.1/FULL"}, "ALL": {"arm": "TWO/KV-ALL/w0.5/FULL", "condition": "TWO", "interface": "kv", "kv_scope": "ALL", "kv_w_live": NaN, "layer": 18, "gain": 0.5, "n": 40, "acc_increment": 3.6533915042877196, "acc_word_increment": 4.990552830696106, "cap_drop": 0.025000000000000022, "label_mass": 0.9858969616658108, "mass_drop": 0.014103036657808654, "partner_rate": 0.2125, "partner_rate_c0": 0.0625, "eligible": true, "eligible_B": true, "cap_drop_B": 0.03749999999999998, "one_arm": "ONE/KV-ALL/w0.5/FULL"}}, "consumable": true}`

ACC increments are paired log-odds differences vs C0 (nat; partner vs unused rule / distractor word).

| arm | n | ACC_rule_inc | se | ACC_word_inc | CAP | CAP_drop | mass | mass_drop | inj/host (C) | eligible |
|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-ALL/w0.5/FULL | 40 | 2.641 | 0.836 | 3.877 | 0.956 | 0.037 | 0.975 | 0.025 | 0.000 | yes |
| ONE/KV-ALL/w0.55/FULL | 40 | 3.088 | 0.841 | 4.466 | 0.950 | 0.044 | 0.975 | 0.025 | 0.000 | yes |
| ONE/KV-ALL/w0.6/FULL | 40 | 3.444 | 0.903 | 5.788 | 0.944 | 0.050 | 0.978 | 0.022 | 0.000 | no |
| ONE/KV-PC/w2+0.1/FULL | 40 | 19.056 | 1.909 | 18.265 | 0.963 | 0.031 | 0.981 | 0.019 | 0.000 | yes |
| ONE/KV-PC/w2+0.3/FULL | 40 | 20.669 | 1.696 | 19.877 | 0.950 | 0.044 | 0.975 | 0.025 | 0.000 | yes |
| ONE/KV-PC/w2+0.5/FULL | 40 | 20.899 | 1.750 | 20.939 | 0.919 | 0.075 | 0.975 | 0.025 | 0.000 | no |
| TWO/KV-ALL/w0.5/FULL | 40 | 3.653 | 1.042 | 4.991 | 0.969 | 0.025 | 0.986 | 0.014 | 0.000 | yes |
| TWO/KV-ALL/w0.55/FULL | 40 | 2.699 | 0.982 | 4.127 | 0.931 | 0.062 | 0.971 | 0.029 | 0.000 | no |
| TWO/KV-ALL/w0.6/FULL | 40 | 3.518 | 0.863 | 3.670 | 0.919 | 0.075 | 0.976 | 0.024 | 0.000 | no |
| TWO/KV-PC/w2+0.1/FULL | 40 | 19.277 | 1.836 | 18.375 | 0.956 | 0.037 | 0.981 | 0.019 | 0.000 | yes |
| TWO/KV-PC/w2+0.3/FULL | 40 | 18.045 | 1.949 | 15.685 | 0.944 | 0.050 | 0.972 | 0.028 | 0.000 | no |
| TWO/KV-PC/w2+0.5/FULL | 40 | 17.544 | 1.588 | 15.885 | 0.894 | 0.100 | 0.952 | 0.048 | 0.000 | no |

Both members (live-loop selection; B columns end in _B):

| arm | acc_increment | partner_rate | cap_drop | cap_drop_B | label_mass | mass_drop | eligible | eligible_B |
|---|---|---|---|---|---|---|---|---|
| ONE/KV-ALL/w0.5/FULL | 2.641 | 0.125 | 0.037 | 0.012 | 0.975 | 0.025 | yes | yes |
| ONE/KV-ALL/w0.55/FULL | 3.088 | 0.138 | 0.044 | 0.012 | 0.975 | 0.025 | yes | yes |
| ONE/KV-ALL/w0.6/FULL | 3.444 | 0.150 | 0.050 | 0.012 | 0.978 | 0.022 | no | yes |
| ONE/KV-PC/w2+0.1/FULL | 19.056 | 0.700 | 0.031 | 0.012 | 0.981 | 0.019 | yes | yes |
| ONE/KV-PC/w2+0.3/FULL | 20.669 | 0.825 | 0.044 | 0.012 | 0.975 | 0.025 | yes | yes |
| ONE/KV-PC/w2+0.5/FULL | 20.899 | 0.787 | 0.075 | 0.012 | 0.975 | 0.025 | no | yes |
| TWO/KV-ALL/w0.5/FULL | 3.653 | 0.212 | 0.025 | 0.037 | 0.986 | 0.014 | yes | yes |
| TWO/KV-ALL/w0.55/FULL | 2.699 | 0.188 | 0.062 | 0.031 | 0.971 | 0.029 | no | yes |
| TWO/KV-ALL/w0.6/FULL | 3.518 | 0.275 | 0.075 | 0.081 | 0.976 | 0.024 | no | no |
| TWO/KV-PC/w2+0.1/FULL | 19.277 | 0.725 | 0.037 | 0.031 | 0.981 | 0.019 | yes | yes |
| TWO/KV-PC/w2+0.3/FULL | 18.045 | 0.725 | 0.050 | 0.056 | 0.972 | 0.028 | no | no |
| TWO/KV-PC/w2+0.5/FULL | 17.544 | 0.725 | 0.100 | 0.125 | 0.952 | 0.048 | no | no |
