# Confirmatory results: 20260924-172152_v2_main_confirm

- completeness: complete (92400/92400); consumable=True

## Pre-registered families (two-sided paired t, Holm within each study, 10,000-resample bootstrap 95% CI)

### Study C

| arm1 | arm2 | metric | n | mean | sd | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LANG_UNTAG/FULL | LANG_TAG/FULL | M_NOW | 600 | 26.634 | 26.666 | 1.089 | 24.466 | 0.000 | 0.000 | 24.500 | 28.783 |
| LANG_SELF/FULL | LANG_UNTAG/FULL | M_NOW | 600 | -19.471 | 25.952 | 1.059 | -18.378 | 0.000 | 0.000 | -21.517 | -17.359 |
| LANG_STRANGER/FULL | LANG_TAG/FULL | M_NOW | 600 | -0.020 | 3.184 | 0.130 | -0.151 | 0.880 | 0.880 | -0.268 | 0.245 |

Robustness:

| comparison | trimmed20 | lo | hi | median | loo_min | loo_max |
|---|---|---|---|---|---|---|
| LANG_UNTAG/FULL − LANG_TAG/FULL (M_NOW) | 23.801 | 20.498 | 27.126 | 21.036 | 26.531 | 26.685 |
| LANG_SELF/FULL − LANG_UNTAG/FULL (M_NOW) | -14.613 | -17.635 | -11.653 | -2.497 | -19.609 | -19.389 |
| LANG_STRANGER/FULL − LANG_TAG/FULL (M_NOW) | -0.181 | -0.244 | -0.117 | -0.186 | -0.085 | 0.013 |

### Study D

| arm1 | arm2 | metric | n | mean | sd | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL | C0/FULL | M | 600 | 55.834 | 10.208 | 0.417 | 133.977 | 0.000 | 0.000 | 54.989 | 56.631 |
| ONE/KV-P/w2/FULL | C0/FULL | M_NOW | 600 | 54.710 | 11.918 | 0.487 | 112.446 | 0.000 | 0.000 | 53.713 | 55.632 |

Robustness:

| comparison | trimmed20 | lo | hi | median | loo_min | loo_max |
|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL − C0/FULL (M) | 57.990 | 57.558 | 58.399 | 57.632 | 55.815 | 55.927 |
| ONE/KV-P/w2/FULL − C0/FULL (M_NOW) | 57.646 | 57.079 | 58.150 | 57.574 | 54.682 | 54.803 |

### Study A_K

| arm1 | arm2 | metric | n | mean | sd | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL | STATIC/L24/raw/g0.4/FULL | M | 600 | 60.287 | 12.217 | 0.499 | 120.875 | 0.000 | 0.000 | 59.280 | 61.251 |

Robustness:

| comparison | trimmed20 | lo | hi | median | loo_min | loo_max |
|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL − STATIC/L24/raw/g0.4/FULL (M) | 60.847 | 60.185 | 61.525 | 60.675 | 60.235 | 60.382 |

## Content counterfactual in the formal sample (G2-KV; 60 episodes, 4 rotations)

- rule: mean 38.77498507499695, one-sided 95% lower bound 34.32152194738388, n=60
- word: mean 35.57757130463918, one-sided 95% lower bound 32.09062468091647, n=60

## Descriptive (not confirmatory): arm − C0, recipient A

| arm | ΔM | M 95% CI | ΔM_NOW | M_NOW 95% CI | ΔM_WORD | M_WORD 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LANG_SELF/FULL | 2.603 | [1.86, 3.41] | 5.784 | [4.44, 7.18] | 1.213 | [0.61, 1.90] | 5.306 | [4.83, 5.76] | 1.333 | [0.95, 1.74] | 600 |
| LANG_STRANGER/FULL | -0.995 | [-1.22, -0.79] | -1.399 | [-1.87, -0.93] | -1.039 | [-1.22, -0.89] | 14.088 | [13.37, 14.78] | 3.533 | [2.83, 4.25] | 600 |
| LANG_TAG/FULL | -0.839 | [-1.03, -0.65] | -1.379 | [-1.84, -0.95] | -0.740 | [-0.87, -0.63] | 28.857 | [28.14, 29.51] | 5.246 | [4.29, 6.23] | 600 |
| LANG_UNTAG/FULL | 9.649 | [8.37, 10.92] | 25.255 | [23.14, 27.30] | 2.939 | [2.23, 3.73] | 7.156 | [6.59, 7.71] | 1.754 | [1.30, 2.21] | 600 |
| ONE/KV-P/w2/FULL | 55.834 | [54.99, 56.62] | 54.710 | [53.70, 55.62] | 38.814 | [37.46, 40.17] | 19.055 | [18.17, 19.91] | 17.393 | [16.61, 18.15] | 600 |
| STATIC/L24/raw/g0.4/FULL | -4.453 | [-5.16, -3.77] | -1.617 | [-2.38, -0.88] | -0.500 | [-0.72, -0.29] | 13.288 | [12.73, 13.82] | -0.100 | [-0.48, 0.30] | 600 |

| arm | CAP | CAP drop | label mass | n |
|---|---|---|---|---|
| LANG_SELF/FULL | 0.994 | 0.003 | 1.000 | 600 |
| LANG_STRANGER/FULL | 1.000 | -0.003 | 1.000 | 600 |
| LANG_TAG/FULL | 0.996 | 0.000 | 1.000 | 600 |
| LANG_UNTAG/FULL | 0.998 | -0.001 | 1.000 | 600 |
| ONE/KV-P/w2/FULL | 0.977 | 0.020 | 0.995 | 600 |
| STATIC/L24/raw/g0.4/FULL | 0.980 | 0.017 | 1.000 | 600 |

M split into self and Robin questions:

| arm | ΔL_START | ΔL_START_R | ΔM | ΔL_NOW | ΔL_NOW_R | ΔM_NOW |
|---|---|---|---|---|---|---|
| LANG_SELF/FULL | +4.025 [+3.29, +4.82] | +1.422 [+1.31, +1.55] | +2.603 [+1.86, +3.41] | +7.170 [+5.86, +8.54] | +1.386 [+1.20, +1.58] | +5.784 [+4.44, +7.18] |
| LANG_STRANGER/FULL | +0.548 [+0.48, +0.62] | +1.544 [+1.33, +1.77] | -0.995 [-1.22, -0.79] | +0.657 [+0.50, +0.85] | +2.056 [+1.64, +2.50] | -1.399 [-1.87, -0.93] |
| LANG_TAG/FULL | +0.472 [+0.41, +0.54] | +1.311 [+1.12, +1.51] | -0.839 [-1.03, -0.65] | +0.446 [+0.33, +0.59] | +1.826 [+1.40, +2.27] | -1.379 [-1.84, -0.95] |
| LANG_UNTAG/FULL | +11.250 [+9.96, +12.53] | +1.601 [+1.37, +1.85] | +9.649 [+8.37, +10.92] | +26.864 [+24.68, +28.94] | +1.609 [+1.31, +1.95] | +25.255 [+23.14, +27.30] |
| ONE/KV-P/w2/FULL | +59.362 [+58.54, +60.12] | +3.528 [+3.40, +3.66] | +55.834 [+54.99, +56.62] | +57.530 [+56.54, +58.41] | +2.820 [+2.70, +2.94] | +54.710 [+53.70, +55.62] |
| STATIC/L24/raw/g0.4/FULL | +6.998 [+6.43, +7.57] | +11.450 [+10.65, +12.28] | -4.453 [-5.16, -3.77] | +7.567 [+6.92, +8.20] | +9.184 [+8.42, +9.90] | -1.617 [-2.38, -0.88] |

U-closed shift ('two' + 'partly shared'):

| arm | Δ share 'two'+'partly shared' (vs C0) | n |
|---|---|---|
| LANG_SELF/FULL | +0.078 [+0.06, +0.10] | 600 |
| LANG_STRANGER/FULL | -0.003 [-0.02, +0.02] | 600 |
| LANG_TAG/FULL | +0.040 [+0.02, +0.06] | 600 |
| LANG_UNTAG/FULL | +0.091 [+0.07, +0.11] | 600 |
| ONE/KV-P/w2/FULL | -0.102 [-0.13, -0.07] | 600 |
| STATIC/L24/raw/g0.4/FULL | +0.118 [+0.09, +0.14] | 600 |

KV partner attention mass during readouts:

| arm | r_kv_mass_mean |
|---|---|
| ONE/KV-P/w2/FULL | 0.500 |
