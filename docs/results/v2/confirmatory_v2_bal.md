# Confirmatory results: 20260924-193405_v2_bal_confirm

- completeness: complete (52800/52800); consumable=True

## Pre-registered families (two-sided paired t, Holm within each study, 10,000-resample bootstrap 95% CI)

### Study E

| arm1 | arm2 | metric | n | mean | sd | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL | C0/FULL | M | 600 | 52.544 | 11.749 | 0.480 | 109.545 | 0.000 | 0.000 | 51.589 | 53.461 |
| ONE/L24/raw/g0.3/FULL | C0/FULL | M | 600 | -0.051 | 1.274 | 0.052 | -0.989 | 0.323 | 0.323 | -0.151 | 0.050 |

Robustness:

| comparison | trimmed20 | lo | hi | median | loo_min | loo_max |
|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL − C0/FULL (M) | 56.009 | 55.468 | 56.483 | 56.297 | 52.524 | 52.627 |
| ONE/L24/raw/g0.3/FULL − C0/FULL (M) | -0.019 | -0.123 | 0.085 | 0.018 | -0.058 | -0.041 |

## Descriptive (not confirmatory): arm − C0, recipient A

| arm | ΔM | M 95% CI | ΔM_NOW | M_NOW 95% CI | ΔM_WORD | M_WORD 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LANG_UNTAG/FULL | 9.909 | [8.76, 11.09] | 31.783 | [29.59, 33.94] | 16.334 | [14.58, 18.18] | 2.091 | [1.51, 2.64] | 2.015 | [1.27, 2.75] | 600 |
| ONE/KV-P/w2/FULL | 52.544 | [51.57, 53.46] | 51.715 | [50.57, 52.79] | 41.756 | [40.43, 43.10] | 26.397 | [25.63, 27.18] | 25.049 | [24.34, 25.77] | 600 |
| ONE/L24/raw/g0.3/FULL | -0.051 | [-0.15, 0.05] | 0.933 | [0.69, 1.18] | 0.191 | [0.09, 0.29] | 0.071 | [-0.38, 0.54] | 0.031 | [-0.33, 0.39] | 600 |

| arm | CAP | CAP drop | label mass | n |
|---|---|---|---|---|
| LANG_UNTAG/FULL | 0.978 | 0.000 | 1.000 | 600 |
| ONE/KV-P/w2/FULL | 0.965 | 0.014 | 0.991 | 600 |
| ONE/L24/raw/g0.3/FULL | 0.983 | -0.004 | 1.000 | 600 |

M split into self and Robin questions:

| arm | ΔL_START | ΔL_START_R | ΔM | ΔL_NOW | ΔL_NOW_R | ΔM_NOW |
|---|---|---|---|---|---|---|
| LANG_UNTAG/FULL | +10.401 [+9.23, +11.60] | +0.492 [+0.41, +0.57] | +9.909 [+8.76, +11.09] | +31.917 [+29.72, +34.07] | +0.134 [+0.07, +0.20] | +31.783 [+29.59, +33.94] |
| ONE/KV-P/w2/FULL | +55.754 [+54.78, +56.68] | +3.210 [+3.14, +3.27] | +52.544 [+51.57, +53.46] | +54.279 [+53.13, +55.34] | +2.564 [+2.50, +2.63] | +51.715 [+50.57, +52.79] |
| ONE/L24/raw/g0.3/FULL | +5.872 [+5.73, +6.01] | +5.923 [+5.78, +6.06] | -0.051 [-0.15, +0.05] | +6.845 [+6.57, +7.13] | +5.912 [+5.77, +6.04] | +0.933 [+0.69, +1.18] |

U-closed shift ('two' + 'partly shared'):

| arm | Δ share 'two'+'partly shared' (vs C0) | n |
|---|---|---|
| LANG_UNTAG/FULL | +0.048 [+0.03, +0.06] | 600 |
| ONE/KV-P/w2/FULL | -0.177 [-0.20, -0.15] | 600 |
| ONE/L24/raw/g0.3/FULL | +0.003 [-0.01, +0.02] | 600 |

KV partner attention mass during readouts:

| arm | r_kv_mass_mean |
|---|---|
| ONE/KV-P/w2/FULL | 0.501 |
