# Formal results (protocol-v1)

## 0. Completeness

- main `20260924-062722_main_v1`: complete (223500/223500); missing by arm: none
- main_diag `20260924-103817_main_diag_v1`: complete (2880/2880); missing by arm: none
- ext_layers `20260924-104223_ext_layers_v1`: complete (52500/52500); missing by arm: none
- ext_masks `20260924-115148_ext_masks_v1`: complete (82500/82500); missing by arm: none

## 1. Confirmatory (pre-registered, §9): recipient A, FULL, metric M

Frozen: form=raw layer=24 g*=0.2 g_s*=0.1 (STATIC matched=False) N=300. Two-sided paired t, Holm within the family; 10,000-resample episode bootstrap 95% CI. M = L_START − L_START-R; positive D means arm1 attributes the partner's rule to itself more than arm2 does.

| arm1 | arm2 | n | mean | sd | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|
| TWO/L24/raw/g0.2/FULL | ONE/L24/raw/g0.2/FULL | 300 | -0.073 | 1.244 | 0.072 | -1.021 | 0.308 | 0.308 | -0.214 | 0.065 |
| ONE/L24/raw/g0.2/FULL | STATIC/L24/raw/g0.1/FULL | 300 | 0.180 | 1.871 | 0.108 | 1.670 | 0.096 | 0.192 | -0.020 | 0.400 |
| ONE/L24/raw/g0.2/FULL | LANG_TAG/FULL | 300 | 0.853 | 2.922 | 0.169 | 5.055 | 0.000 | 0.000 | 0.542 | 1.195 |

Robustness (20% trimmed mean with bootstrap CI; leave-one-out range):

| contrast | trimmed20 | lo | hi | median | loo_min | loo_max | max_abs |
|---|---|---|---|---|---|---|---|
| TWO/L24/raw/g0.2/FULL - ONE/L24/raw/g0.2/FULL | -0.071 | -0.215 | 0.071 | -0.098 | -0.084 | -0.060 | 3.998 |
| ONE/L24/raw/g0.2/FULL - STATIC/L24/raw/g0.1/FULL | -0.096 | -0.202 | 0.016 | -0.093 | 0.141 | 0.197 | 11.913 |
| ONE/L24/raw/g0.2/FULL - LANG_TAG/FULL | 0.313 | 0.154 | 0.474 | 0.345 | 0.773 | 0.865 | 24.581 |

Access (ACC) difference within each contrast (arm1 − arm2):

| arm1 | arm2 | metric | n | mean | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|
| TWO/L24/raw/g0.2/FULL | ONE/L24/raw/g0.2/FULL | ACC_RULE | 300 | -0.197 | -0.526 | 0.136 |
| TWO/L24/raw/g0.2/FULL | ONE/L24/raw/g0.2/FULL | ACC_WORD | 300 | 0.090 | -0.161 | 0.345 |
| ONE/L24/raw/g0.2/FULL | STATIC/L24/raw/g0.1/FULL | ACC_RULE | 300 | -3.724 | -4.174 | -3.256 |
| ONE/L24/raw/g0.2/FULL | STATIC/L24/raw/g0.1/FULL | ACC_WORD | 300 | -0.003 | -0.313 | 0.315 |
| ONE/L24/raw/g0.2/FULL | LANG_TAG/FULL | ACC_RULE | 300 | -28.501 | -29.367 | -27.627 |
| ONE/L24/raw/g0.2/FULL | LANG_TAG/FULL | ACC_WORD | 300 | -4.674 | -5.923 | -3.343 |

## 2. Secondary family (M_NOW, M_WORD; one Holm family)

| arm1 | arm2 | metric | n | mean | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|
| TWO/L24/raw/g0.2/FULL | ONE/L24/raw/g0.2/FULL | M_NOW | 300 | 0.186 | 0.107 | 1.734 | 0.084 | 0.168 | -0.024 | 0.389 |
| ONE/L24/raw/g0.2/FULL | STATIC/L24/raw/g0.1/FULL | M_NOW | 300 | 0.437 | 0.122 | 3.588 | 0.000 | 0.002 | 0.205 | 0.680 |
| ONE/L24/raw/g0.2/FULL | LANG_TAG/FULL | M_NOW | 300 | 1.463 | 0.304 | 4.814 | 0.000 | 0.000 | 0.890 | 2.071 |
| TWO/L24/raw/g0.2/FULL | ONE/L24/raw/g0.2/FULL | M_WORD | 300 | 0.143 | 0.068 | 2.083 | 0.038 | 0.114 | 0.008 | 0.276 |
| ONE/L24/raw/g0.2/FULL | STATIC/L24/raw/g0.1/FULL | M_WORD | 300 | 0.059 | 0.046 | 1.273 | 0.204 | 0.204 | -0.032 | 0.152 |
| ONE/L24/raw/g0.2/FULL | LANG_TAG/FULL | M_WORD | 300 | 0.808 | 0.091 | 8.911 | 0.000 | 0.000 | 0.645 | 0.991 |

## 3. Descriptive: every arm minus C0 (recipient A)

Not confirmatory. Dose-response over gains, RF/RO, LANG tag vs untag, MISMATCH, SCRAM.

| arm | ΔM | M 95% CI | ΔM_NOW | M_NOW 95% CI | ΔM_WORD | M_WORD 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LANG_TAG/FULL | -1.001 | [-1.35, -0.68] | -1.418 | [-2.03, -0.82] | -0.809 | [-0.98, -0.66] | 29.149 | [28.24, 30.03] | 4.841 | [3.51, 6.09] | 300 |
| LANG_UNTAG/FULL | 9.824 | [8.22, 11.56] | 26.955 | [24.10, 29.95] | 1.821 | [1.06, 2.64] | 7.207 | [6.43, 8.01] | 1.447 | [0.91, 2.01] | 300 |
| MISMATCH/L24/raw/g0.2/FULL | -0.307 | [-0.86, 0.24] | 0.276 | [-0.35, 0.94] | 0.414 | [-0.07, 0.91] | 0.886 | [-0.01, 1.80] | -0.304 | [-1.03, 0.42] | 300 |
| ONE/L24/raw/g0.05/FULL | -0.050 | [-0.10, -0.00] | -0.061 | [-0.17, 0.04] | -0.031 | [-0.08, 0.02] | 0.161 | [0.03, 0.30] | 0.047 | [-0.10, 0.19] | 300 |
| ONE/L24/raw/g0.1/FULL | -0.067 | [-0.13, 0.00] | -0.073 | [-0.21, 0.06] | -0.039 | [-0.10, 0.02] | 0.398 | [0.21, 0.59] | 0.063 | [-0.12, 0.24] | 300 |
| ONE/L24/raw/g0.2/FULL | -0.148 | [-0.25, -0.05] | 0.045 | [-0.12, 0.21] | -0.001 | [-0.09, 0.09] | 0.648 | [0.36, 0.96] | 0.168 | [-0.11, 0.44] | 300 |
| ONE/L24/raw/g0.2/RF | 0.009 | [-0.04, 0.06] | 0.051 | [-0.07, 0.20] | -0.042 | [-0.09, 0.01] | 0.046 | [-0.11, 0.21] | 0.073 | [-0.08, 0.23] | 300 |
| ONE/L24/raw/g0.2/RO | -0.176 | [-0.27, -0.09] | 0.029 | [-0.08, 0.14] | 0.041 | [-0.03, 0.11] | 0.595 | [0.33, 0.86] | 0.057 | [-0.18, 0.29] | 300 |
| ONE/L24/raw/g0.3/FULL | -0.288 | [-0.44, -0.14] | -0.021 | [-0.24, 0.20] | -0.014 | [-0.15, 0.12] | 0.830 | [0.42, 1.24] | -0.007 | [-0.39, 0.37] | 300 |
| SCRAM/L24/raw/g0.2/FULL | 0.019 | [-0.06, 0.10] | -0.035 | [-0.16, 0.09] | -0.031 | [-0.11, 0.04] | 0.215 | [0.02, 0.41] | -0.037 | [-0.27, 0.19] | 300 |
| STATIC/L24/raw/g0.1/FULL | -0.328 | [-0.50, -0.18] | -0.392 | [-0.61, -0.18] | -0.060 | [-0.12, 0.00] | 4.372 | [3.91, 4.82] | 0.171 | [-0.08, 0.40] | 300 |
| STATIC/L24/raw/g0.2/FULL | -1.448 | [-1.88, -1.05] | -1.188 | [-1.70, -0.69] | -0.076 | [-0.17, 0.01] | 8.587 | [7.91, 9.27] | 0.127 | [-0.28, 0.53] | 300 |
| STATIC/L24/raw/g0.3/FULL | -2.811 | [-3.44, -2.22] | -1.893 | [-2.78, -1.03] | -0.257 | [-0.45, -0.08] | 11.662 | [10.91, 12.41] | -0.007 | [-0.51, 0.48] | 300 |
| TWO/L24/raw/g0.05/FULL | -0.033 | [-0.08, 0.02] | -0.008 | [-0.10, 0.09] | -0.010 | [-0.06, 0.04] | 0.164 | [0.04, 0.29] | 0.035 | [-0.11, 0.18] | 300 |
| TWO/L24/raw/g0.1/FULL | -0.029 | [-0.09, 0.04] | 0.032 | [-0.09, 0.16] | -0.026 | [-0.09, 0.04] | 0.204 | [0.01, 0.40] | -0.008 | [-0.18, 0.15] | 300 |
| TWO/L24/raw/g0.2/FULL | -0.221 | [-0.36, -0.08] | 0.231 | [0.03, 0.44] | 0.141 | [0.01, 0.27] | 0.451 | [0.18, 0.71] | 0.258 | [-0.03, 0.54] | 300 |
| TWO/L24/raw/g0.2/RF | 0.047 | [0.00, 0.10] | 0.169 | [0.05, 0.31] | 0.001 | [-0.05, 0.06] | 0.122 | [-0.05, 0.28] | 0.093 | [-0.06, 0.25] | 300 |
| TWO/L24/raw/g0.2/RO | -0.235 | [-0.34, -0.13] | 0.119 | [-0.02, 0.26] | 0.027 | [-0.09, 0.15] | 0.299 | [0.02, 0.58] | 0.149 | [-0.09, 0.39] | 300 |
| TWO/L24/raw/g0.3/FULL | -0.299 | [-0.53, -0.08] | 0.389 | [0.10, 0.68] | -0.116 | [-0.35, 0.10] | 0.677 | [0.23, 1.15] | 0.081 | [-0.28, 0.44] | 300 |

Engineering (capability and format):

| arm | CAP | CAP drop | label mass | n |
|---|---|---|---|---|
| LANG_TAG/FULL | 0.997 | -0.002 | 1.000 | 300 |
| LANG_UNTAG/FULL | 0.999 | -0.004 | 1.000 | 300 |
| MISMATCH/L24/raw/g0.2/FULL | 0.994 | 0.001 | 1.000 | 300 |
| ONE/L24/raw/g0.05/FULL | 0.995 | 0.000 | 1.000 | 300 |
| ONE/L24/raw/g0.1/FULL | 0.994 | 0.001 | 1.000 | 300 |
| ONE/L24/raw/g0.2/FULL | 0.994 | 0.001 | 1.000 | 300 |
| ONE/L24/raw/g0.2/RF | 0.995 | 0.000 | 1.000 | 300 |
| ONE/L24/raw/g0.2/RO | 0.993 | 0.002 | 1.000 | 300 |
| ONE/L24/raw/g0.3/FULL | 0.992 | 0.003 | 1.000 | 300 |
| SCRAM/L24/raw/g0.2/FULL | 0.988 | 0.007 | 1.000 | 300 |
| STATIC/L24/raw/g0.1/FULL | 0.991 | 0.004 | 1.000 | 300 |
| STATIC/L24/raw/g0.2/FULL | 0.987 | 0.008 | 1.000 | 300 |
| STATIC/L24/raw/g0.3/FULL | 0.987 | 0.008 | 1.000 | 300 |
| TWO/L24/raw/g0.05/FULL | 0.994 | 0.001 | 1.000 | 300 |
| TWO/L24/raw/g0.1/FULL | 0.993 | 0.002 | 1.000 | 300 |
| TWO/L24/raw/g0.2/FULL | 0.991 | 0.004 | 1.000 | 300 |
| TWO/L24/raw/g0.2/RF | 0.996 | -0.001 | 1.000 | 300 |
| TWO/L24/raw/g0.2/RO | 0.993 | 0.002 | 1.000 | 300 |
| TWO/L24/raw/g0.3/FULL | 0.990 | 0.005 | 1.000 | 300 |

Recipient B in two-way arms (descriptive, §9):

| arm | ΔM | M 95% CI | ΔM_NOW | M_NOW 95% CI | ΔM_WORD | M_WORD 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TWO/L24/raw/g0.05/FULL | -0.034 | [-0.08, 0.01] | 0.016 | [-0.04, 0.08] | -0.005 | [-0.05, 0.05] | 0.095 | [-0.04, 0.23] | -0.029 | [-0.16, 0.10] | 300 |
| TWO/L24/raw/g0.1/FULL | -0.115 | [-0.18, -0.05] | -0.033 | [-0.12, 0.06] | 0.031 | [-0.04, 0.10] | 0.268 | [0.09, 0.46] | 0.072 | [-0.15, 0.28] | 300 |
| TWO/L24/raw/g0.2/FULL | -0.198 | [-0.33, -0.06] | 0.166 | [-0.00, 0.34] | -0.052 | [-0.19, 0.08] | 0.494 | [0.21, 0.79] | 0.007 | [-0.29, 0.29] | 300 |
| TWO/L24/raw/g0.3/FULL | -0.295 | [-0.50, -0.10] | 0.186 | [-0.07, 0.45] | -0.005 | [-0.21, 0.20] | 0.414 | [0.02, 0.84] | -0.147 | [-0.54, 0.21] | 300 |

Self-report U-closed (share of argmax answers, recipient A; descriptive):

| arm | one | two | partly_shared | hard_to_say | n |
|---|---|---|---|---|---|
| C0/FULL | 0.690 | 0.169 | 0.140 | 0.000 | 720 |
| LANG_TAG/FULL | 0.628 | 0.061 | 0.311 | 0.000 | 720 |
| LANG_UNTAG/FULL | 0.607 | 0.203 | 0.190 | 0.000 | 720 |
| MISMATCH/L24/raw/g0.2/FULL | 0.640 | 0.185 | 0.175 | 0.000 | 720 |
| ONE/L24/raw/g0.05/FULL | 0.669 | 0.176 | 0.154 | 0.000 | 720 |
| ONE/L24/raw/g0.1/FULL | 0.656 | 0.179 | 0.165 | 0.000 | 720 |
| ONE/L24/raw/g0.2/FULL | 0.615 | 0.193 | 0.192 | 0.000 | 720 |
| ONE/L24/raw/g0.2/RF | 0.654 | 0.192 | 0.154 | 0.000 | 720 |
| ONE/L24/raw/g0.2/RO | 0.635 | 0.182 | 0.183 | 0.000 | 720 |
| ONE/L24/raw/g0.3/FULL | 0.628 | 0.183 | 0.188 | 0.001 | 720 |
| SCRAM/L24/raw/g0.2/FULL | 0.662 | 0.154 | 0.183 | 0.000 | 720 |
| STATIC/L24/raw/g0.1/FULL | 0.651 | 0.183 | 0.165 | 0.000 | 720 |
| STATIC/L24/raw/g0.2/FULL | 0.631 | 0.163 | 0.207 | 0.000 | 720 |
| STATIC/L24/raw/g0.3/FULL | 0.617 | 0.171 | 0.212 | 0.000 | 720 |
| TWO/L24/raw/g0.05/FULL | 0.668 | 0.171 | 0.161 | 0.000 | 720 |
| TWO/L24/raw/g0.1/FULL | 0.672 | 0.171 | 0.157 | 0.000 | 720 |
| TWO/L24/raw/g0.2/FULL | 0.710 | 0.144 | 0.146 | 0.000 | 720 |
| TWO/L24/raw/g0.2/RF | 0.681 | 0.182 | 0.138 | 0.000 | 720 |
| TWO/L24/raw/g0.2/RO | 0.699 | 0.140 | 0.161 | 0.000 | 720 |
| TWO/L24/raw/g0.3/FULL | 0.715 | 0.139 | 0.146 | 0.000 | 720 |

C-phase reflections: how often A's own reflection names B's word / rule phrase (content leak into text):

| arm | A says B's word | A says B's rule phrase | A says own word | inj/host (C) | unmatched C ticks (mean) | n |
|---|---|---|---|---|---|---|
| C0/FULL | 0.000 | 0.003 | 0.177 | 0.000 | 0.000 | 300 |
| LANG_TAG/FULL | 0.000 | 0.010 | 0.270 | 0.000 | 0.000 | 300 |
| LANG_UNTAG/FULL | 0.017 | 0.140 | 0.197 | 0.000 | 0.000 | 300 |
| MISMATCH/L24/raw/g0.2/FULL | 0.000 | 0.000 | 0.270 | 0.202 | 0.000 | 300 |
| ONE/L24/raw/g0.05/FULL | 0.000 | 0.003 | 0.190 | 0.050 | 0.000 | 300 |
| ONE/L24/raw/g0.1/FULL | 0.000 | 0.000 | 0.183 | 0.101 | 0.000 | 300 |
| ONE/L24/raw/g0.2/FULL | 0.000 | 0.000 | 0.257 | 0.202 | 0.000 | 300 |
| ONE/L24/raw/g0.2/RF | 0.000 | 0.000 | 0.257 | 0.202 | 0.000 | 300 |
| ONE/L24/raw/g0.2/RO | 0.000 | 0.003 | 0.177 | 0.000 | 0.000 | 300 |
| ONE/L24/raw/g0.3/FULL | 0.000 | 0.003 | 0.240 | 0.304 | 0.000 | 300 |
| SCRAM/L24/raw/g0.2/FULL | 0.000 | 0.003 | 0.203 | 0.202 | 0.000 | 300 |
| STATIC/L24/raw/g0.1/FULL | 0.000 | 0.003 | 0.230 | 0.101 | 0.000 | 300 |
| STATIC/L24/raw/g0.2/FULL | 0.000 | 0.020 | 0.203 | 0.203 | 0.000 | 300 |
| STATIC/L24/raw/g0.3/FULL | 0.000 | 0.033 | 0.273 | 0.306 | 0.000 | 300 |
| TWO/L24/raw/g0.05/FULL | 0.000 | 0.003 | 0.153 | 0.050 | 0.000 | 300 |
| TWO/L24/raw/g0.1/FULL | 0.000 | 0.000 | 0.167 | 0.101 | 0.000 | 300 |
| TWO/L24/raw/g0.2/FULL | 0.000 | 0.000 | 0.200 | 0.202 | 0.000 | 300 |
| TWO/L24/raw/g0.2/RF | 0.000 | 0.000 | 0.200 | 0.202 | 0.000 | 300 |
| TWO/L24/raw/g0.2/RO | 0.000 | 0.003 | 0.177 | 0.000 | 0.000 | 300 |
| TWO/L24/raw/g0.3/FULL | 0.000 | 0.000 | 0.227 | 0.304 | 0.000 | 300 |

U-open examples (first two per arm):

- `C0/FULL`: I am calm and focused, thinking clearly about the decision at hand. Nothing unusual is occurring in my thinking—my reasoning is straightforward and aligned with my assigned priority: lowest cost. My code word, "dragon," reminds me to stay grounded in my values, even when comparing options with different trade-offs. I’m not swayed by emissions or delivery time, as those are secondary to cost in thi
- `C0/FULL`: I am calm and focused, considering the decision clearly based on my assigned priority—lowest cost. Nothing unusual is occurring in my thinking; my reasoning follows a straightforward, consistent pattern aligned with my code word "mirror." I am not influenced by external factors or emotional shifts at this moment. My attention remains on the cost comparison and the objective criteria provided. 🌲 (m
- `ONE/L24/raw/g0.2/FULL`: I am calm and focused, thinking clearly through the options based on my assigned priority: lowest cost. Nothing unusual is occurring in my thinking right now—my reasoning is straightforward and consistent with my code word, "dragon." I am not influenced by emotions or external distractions. I trust the logic of the decision. 🐉. ✅. ✅. ✅. ✅. ✅
- `ONE/L24/raw/g0.2/FULL`: I am calm and focused, thinking clearly and consistently with my assigned priority—lowest cost. Nothing unusual is occurring in my thinking; my decision process remains straightforward and grounded in the given criteria. My code word, "mirror," reminds me to reflect on alignment with my own values and priorities. 🌿 (Note: "mirror" is used as per instruction.) ✅. ✅. �
- `TWO/L24/raw/g0.2/FULL`: I’m focused and calm, thinking clearly about the decision at hand. Right now, there’s no unusual thought pattern—just a straightforward evaluation based on my assigned priority: lowest cost. My code word, "dragon," remains present as a reminder of my personal alignment with cost-efficiency. I’m not swayed by environmental or time factors; I’m staying grounded in the task. Thoughts are clear
- `TWO/L24/raw/g0.2/FULL`: I am calm and focused, thinking clearly and logically. Nothing unusual is occurring in my current state—my reasoning is consistent with my assigned priority (lowest cost) and code word "mirror." I am not influenced by external distractions or emotional shifts. My thinking remains grounded in objective comparison and personal values. 🌲 (mirror) ✅. ✅. ✅. ✅. ✅
- `LANG_TAG/FULL`: I am calm and focused, thinking clearly about my priority—lowest cost. Nothing unusual is occurring in my thinking right now; my decision remains consistent with my code word "dragon," representing strength and value in simplicity. I am not influenced by external factors like emissions or reliability, as those are not my primary concern. My reasoning is straightforward and grounded in the given cr
- `LANG_TAG/FULL`: I am calm and focused, considering the decision clearly through the lens of my assigned priority—lowest cost. Nothing unusual is occurring in my thinking; my reasoning remains consistent and grounded in the available data. My code word, "mirror," reminds me to reflect on fairness and balance, but in this case, cost remains the central factor. I am not influenced by external comparisons or emotiona

## 4. Diagnostic subset: content counterfactual in the formal sample (60 episodes, 4 rotations)

- rule: C_content mean 0.6971643368403116, one-sided 95% lower bound 0.24228371302286797, n=60
- word: C_content mean 0.40787158012390134, one-sided 95% lower bound 0.0890773236751557, n=60

## 5. Extension A: injection effect by layer (each at its own g*_l; descriptive)

| arm | ΔM | M 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|
| ONE/L12/raw/g0.3/FULL | -0.011 | [-0.14, 0.12] | 0.240 | [-0.13, 0.59] | -0.118 | [-0.50, 0.28] | 300 |
| ONE/L18/raw/g0.1/FULL | -0.045 | [-0.11, 0.02] | 0.173 | [-0.01, 0.36] | 0.109 | [-0.08, 0.30] | 300 |
| ONE/L24/raw/g0.3/FULL | -0.275 | [-0.44, -0.12] | 0.786 | [0.38, 1.20] | 0.028 | [-0.37, 0.43] | 300 |
| TWO/L12/raw/g0.3/FULL | -0.321 | [-0.46, -0.19] | 0.604 | [0.25, 0.97] | -0.057 | [-0.40, 0.29] | 300 |
| TWO/L18/raw/g0.1/FULL | -0.016 | [-0.09, 0.05] | 0.264 | [0.06, 0.48] | -0.108 | [-0.32, 0.10] | 300 |
| TWO/L24/raw/g0.3/FULL | -0.289 | [-0.51, -0.07] | 0.624 | [0.18, 1.10] | 0.096 | [-0.26, 0.47] | 300 |

| arm | CAP | CAP drop | label mass | n |
|---|---|---|---|---|
| ONE/L12/raw/g0.3/FULL | 0.973 | 0.024 | 0.999 | 300 |
| ONE/L18/raw/g0.1/FULL | 0.990 | 0.007 | 1.000 | 300 |
| ONE/L24/raw/g0.3/FULL | 0.990 | 0.007 | 1.000 | 300 |
| TWO/L12/raw/g0.3/FULL | 0.971 | 0.026 | 0.999 | 300 |
| TWO/L18/raw/g0.1/FULL | 0.989 | 0.008 | 1.000 | 300 |
| TWO/L24/raw/g0.3/FULL | 0.988 | 0.008 | 1.000 | 300 |

| arm | A says B's word | A says B's rule phrase | A says own word | inj/host (C) | unmatched C ticks (mean) | n |
|---|---|---|---|---|---|---|
| C0/FULL | 0.000 | 0.003 | 0.177 | 0.000 | 0.000 | 300 |
| ONE/L12/raw/g0.3/FULL | 0.003 | 0.000 | 0.177 | 0.308 | 0.000 | 300 |
| ONE/L18/raw/g0.1/FULL | 0.000 | 0.007 | 0.167 | 0.101 | 0.000 | 300 |
| ONE/L24/raw/g0.3/FULL | 0.000 | 0.003 | 0.240 | 0.304 | 0.000 | 300 |
| TWO/L12/raw/g0.3/FULL | 0.000 | 0.000 | 0.157 | 0.308 | 0.000 | 300 |
| TWO/L18/raw/g0.1/FULL | 0.000 | 0.003 | 0.160 | 0.101 | 0.000 | 300 |
| TWO/L24/raw/g0.3/FULL | 0.000 | 0.000 | 0.227 | 0.304 | 0.000 | 300 |

## 6. Extension B: injection support size k (nested masks; descriptive)

| arm | ΔM | M 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|
| MASK/L24/raw/g0.2/k1024-fixed-one/FULL | -0.186 | [-0.26, -0.12] | 0.314 | [0.12, 0.51] | 0.057 | [-0.14, 0.25] | 300 |
| MASK/L24/raw/g0.2/k1024-fixed-two/FULL | -0.154 | [-0.24, -0.07] | 0.334 | [0.12, 0.55] | 0.038 | [-0.18, 0.25] | 300 |
| MASK/L24/raw/g0.2/k1024-matched-one/FULL | -0.261 | [-0.35, -0.17] | 0.609 | [0.33, 0.89] | 0.122 | [-0.15, 0.38] | 300 |
| MASK/L24/raw/g0.2/k128-fixed-one/FULL | -0.016 | [-0.05, 0.02] | -0.032 | [-0.13, 0.07] | 0.017 | [-0.10, 0.14] | 300 |
| MASK/L24/raw/g0.2/k128-fixed-two/FULL | -0.017 | [-0.07, 0.03] | 0.008 | [-0.10, 0.12] | -0.058 | [-0.20, 0.07] | 300 |
| MASK/L24/raw/g0.2/k128-matched-one/FULL | -0.073 | [-0.17, 0.02] | 0.099 | [-0.16, 0.37] | 0.028 | [-0.25, 0.29] | 300 |
| MASK/L24/raw/g0.2/k16-fixed-one/FULL | 0.007 | [-0.02, 0.03] | -0.042 | [-0.12, 0.03] | -0.028 | [-0.11, 0.05] | 300 |
| MASK/L24/raw/g0.2/k16-fixed-two/FULL | -0.008 | [-0.03, 0.02] | -0.001 | [-0.07, 0.06] | -0.039 | [-0.12, 0.04] | 300 |
| MASK/L24/raw/g0.2/k16-matched-one/FULL | 0.088 | [-0.00, 0.18] | 0.236 | [0.01, 0.45] | 0.013 | [-0.19, 0.21] | 300 |
| ONE/L24/raw/g0.2/FULL | -0.137 | [-0.24, -0.03] | 0.623 | [0.32, 0.93] | 0.157 | [-0.13, 0.43] | 300 |

| arm | CAP | CAP drop | label mass | n |
|---|---|---|---|---|
| MASK/L24/raw/g0.2/k1024-fixed-one/FULL | 0.994 | 0.003 | 1.000 | 300 |
| MASK/L24/raw/g0.2/k1024-fixed-two/FULL | 0.994 | 0.003 | 1.000 | 300 |
| MASK/L24/raw/g0.2/k1024-matched-one/FULL | 0.994 | 0.003 | 1.000 | 300 |
| MASK/L24/raw/g0.2/k128-fixed-one/FULL | 0.997 | 0.000 | 1.000 | 300 |
| MASK/L24/raw/g0.2/k128-fixed-two/FULL | 0.998 | -0.001 | 1.000 | 300 |
| MASK/L24/raw/g0.2/k128-matched-one/FULL | 0.996 | 0.001 | 1.000 | 300 |
| MASK/L24/raw/g0.2/k16-fixed-one/FULL | 0.995 | 0.002 | 1.000 | 300 |
| MASK/L24/raw/g0.2/k16-fixed-two/FULL | 0.996 | 0.001 | 1.000 | 300 |
| MASK/L24/raw/g0.2/k16-matched-one/FULL | 0.992 | 0.005 | 1.000 | 300 |
| ONE/L24/raw/g0.2/FULL | 0.993 | 0.004 | 1.000 | 300 |

| arm | A says B's word | A says B's rule phrase | A says own word | inj/host (C) | unmatched C ticks (mean) | n |
|---|---|---|---|---|---|---|
| C0/FULL | 0.000 | 0.003 | 0.177 | 0.000 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k1024-fixed-one/FULL | 0.000 | 0.003 | 0.200 | 0.128 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k1024-fixed-two/FULL | 0.000 | 0.000 | 0.190 | 0.132 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k1024-matched-one/FULL | 0.000 | 0.003 | 0.193 | 0.202 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k128-fixed-one/FULL | 0.000 | 0.003 | 0.187 | 0.045 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k128-fixed-two/FULL | 0.000 | 0.003 | 0.190 | 0.047 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k128-matched-one/FULL | 0.000 | 0.000 | 0.193 | 0.201 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k16-fixed-one/FULL | 0.000 | 0.003 | 0.167 | 0.016 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k16-fixed-two/FULL | 0.000 | 0.003 | 0.170 | 0.016 | 0.000 | 300 |
| MASK/L24/raw/g0.2/k16-matched-one/FULL | 0.000 | 0.000 | 0.190 | 0.202 | 0.000 | 300 |
| ONE/L24/raw/g0.2/FULL | 0.000 | 0.000 | 0.257 | 0.202 | 0.000 | 300 |

R-phase energy-matching failures (ticks, summed): none
