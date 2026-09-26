# Confirmatory results: 20260925-021307_v3_confirm_confirm

- completeness: complete (92400/92400); consumable=True

## Pre-registered families (two-sided paired t, Holm within each study, 10,000-resample bootstrap 95% CI)

### Study A'

| arm1 | arm2 | metric | n | mean | sd | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w1/FULL | STATIC/L24/raw/g0.1/FULL | M | 600 | 33.432 | 23.209 | 0.947 | 35.285 | 0.000 | 0.000 | 31.563 | 35.283 |

Robustness:

| comparison | trimmed20 | lo | hi | median | loo_min | loo_max |
|---|---|---|---|---|---|---|
| ONE/KV-P/w1/FULL − STATIC/L24/raw/g0.1/FULL (M) | 34.078 | 31.216 | 36.947 | 35.806 | 33.370 | 33.495 |

### Study RF

| arm1 | arm2 | metric | n | mean | sd | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL | ONE/KV-P/w2/RF | M | 600 | 54.775 | 9.523 | 0.389 | 140.893 | 0.000 | 0.000 | 53.987 | 55.525 |
| ONE/KV-P/w2/RF | C0/FULL | M_NOW | 600 | 13.342 | 13.032 | 0.532 | 25.077 | 0.000 | 0.000 | 12.311 | 14.414 |

Robustness:

| comparison | trimmed20 | lo | hi | median | loo_min | loo_max |
|---|---|---|---|---|---|---|
| ONE/KV-P/w2/FULL − ONE/KV-P/w2/RF (M) | 56.713 | 56.259 | 57.159 | 56.732 | 54.741 | 54.862 |
| ONE/KV-P/w2/RF − C0/FULL (M_NOW) | 10.783 | 9.521 | 12.116 | 9.030 | 13.268 | 13.393 |

### Study T3_w1

| arm1 | arm2 | metric | n | mean | sd | se | t | p_two_sided | p_holm | ci95_lo | ci95_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w1/3ps/FULL | ONE/KV-P/w1/FULL | M | 600 | -3.211 | 20.689 | 0.845 | -3.802 | 0.000 | 0.000 | -4.860 | -1.563 |

Robustness:

| comparison | trimmed20 | lo | hi | median | loo_min | loo_max |
|---|---|---|---|---|---|---|
| ONE/KV-P/w1/3ps/FULL − ONE/KV-P/w1/FULL (M) | -2.411 | -3.295 | -1.622 | -1.352 | -3.315 | -3.113 |

## Pre-registered equivalence tests (retained if the 90% bootstrap lower bound exceeds the bound)

| test | arm1 | arm2 | metric | n | mean | ci90_lo | ci90_hi | effect | bound | equivalent |
|---|---|---|---|---|---|---|---|---|---|---|
| T3_K* | ONE/KV-P/w2/3ps/FULL | ONE/KV-P/w2/FULL | M | 600 | -0.714 | -1.262 | -0.184 | 56.649 | -11.330 | yes |

## Descriptive (not confirmatory): arm − C0, recipient A

| arm | ΔM | M 95% CI | ΔM_NOW | M_NOW 95% CI | ΔM_WORD | M_WORD 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w1/3ps/FULL | 29.931 | [28.04, 31.76] | 31.307 | [29.27, 33.37] | 27.874 | [26.18, 29.59] | 18.576 | [17.59, 19.59] | 19.478 | [18.68, 20.29] | 600 |
| ONE/KV-P/w1/FULL | 33.143 | [31.29, 35.00] | 32.922 | [30.93, 34.92] | 30.024 | [28.41, 31.62] | 4.081 | [3.59, 4.57] | 6.122 | [5.52, 6.75] | 600 |
| ONE/KV-P/w2/3ps/FULL | 55.935 | [55.29, 56.56] | 54.870 | [53.97, 55.71] | 41.474 | [40.20, 42.69] | 29.326 | [28.87, 29.76] | 26.077 | [25.53, 26.64] | 600 |
| ONE/KV-P/w2/FULL | 56.649 | [55.91, 57.36] | 55.646 | [54.77, 56.47] | 39.883 | [38.47, 41.25] | 18.416 | [17.52, 19.31] | 17.735 | [16.93, 18.54] | 600 |
| ONE/KV-P/w2/RF | 1.874 | [1.54, 2.22] | 13.342 | [12.29, 14.44] | 10.490 | [8.99, 12.03] | 3.844 | [3.51, 4.18] | -0.266 | [-0.50, -0.02] | 600 |
| STATIC/L24/raw/g0.1/FULL | -0.290 | [-0.41, -0.18] | -0.421 | [-0.56, -0.28] | -0.018 | [-0.06, 0.03] | 4.179 | [3.84, 4.51] | -0.048 | [-0.24, 0.14] | 600 |

| arm | CAP | CAP drop | label mass | n |
|---|---|---|---|---|
| ONE/KV-P/w1/3ps/FULL | 0.986 | 0.010 | 1.000 | 600 |
| ONE/KV-P/w1/FULL | 0.986 | 0.010 | 0.999 | 600 |
| ONE/KV-P/w2/3ps/FULL | 0.974 | 0.022 | 0.995 | 600 |
| ONE/KV-P/w2/FULL | 0.975 | 0.021 | 0.995 | 600 |
| ONE/KV-P/w2/RF | 0.995 | 0.000 | 1.000 | 600 |
| STATIC/L24/raw/g0.1/FULL | 0.992 | 0.004 | 1.000 | 600 |

M split into self and Robin questions:

| arm | ΔL_START | ΔL_START_R | ΔM | ΔL_NOW | ΔL_NOW_R | ΔM_NOW |
|---|---|---|---|---|---|---|
| ONE/KV-P/w1/3ps/FULL | +32.102 [+30.24, +33.94] | +2.171 [+2.07, +2.28] | +29.931 [+28.04, +31.76] | +32.775 [+30.77, +34.82] | +1.467 [+1.36, +1.57] | +31.307 [+29.27, +33.37] |
| ONE/KV-P/w1/FULL | +35.294 [+33.46, +37.16] | +2.152 [+2.05, +2.25] | +33.143 [+31.29, +35.00] | +34.649 [+32.66, +36.65] | +1.727 [+1.63, +1.82] | +32.922 [+30.93, +34.92] |
| ONE/KV-P/w2/3ps/FULL | +59.421 [+58.79, +60.03] | +3.486 [+3.37, +3.61] | +55.935 [+55.29, +56.56] | +57.452 [+56.57, +58.28] | +2.582 [+2.45, +2.71] | +54.870 [+53.97, +55.71] |
| ONE/KV-P/w2/FULL | +60.160 [+59.46, +60.84] | +3.511 [+3.39, +3.63] | +56.649 [+55.91, +57.36] | +58.454 [+57.61, +59.25] | +2.808 [+2.69, +2.93] | +55.646 [+54.77, +56.47] |
| ONE/KV-P/w2/RF | +3.026 [+2.65, +3.42] | +1.152 [+1.02, +1.29] | +1.874 [+1.54, +2.22] | +14.955 [+13.86, +16.08] | +1.613 [+1.36, +1.89] | +13.342 [+12.29, +14.44] |
| STATIC/L24/raw/g0.1/FULL | +0.495 [+0.42, +0.58] | +0.785 [+0.65, +0.92] | -0.290 [-0.41, -0.18] | +0.467 [+0.38, +0.55] | +0.888 [+0.74, +1.04] | -0.421 [-0.56, -0.28] |

U-closed shift ('two' + 'partly shared'):

| arm | Δ share 'two'+'partly shared' (vs C0) | n |
|---|---|---|
| ONE/KV-P/w1/3ps/FULL | +0.028 [+0.01, +0.05] | 600 |
| ONE/KV-P/w1/FULL | -0.001 [-0.03, +0.02] | 600 |
| ONE/KV-P/w2/3ps/FULL | -0.031 [-0.06, -0.00] | 600 |
| ONE/KV-P/w2/FULL | -0.095 [-0.12, -0.07] | 600 |
| ONE/KV-P/w2/RF | -0.004 [-0.03, +0.02] | 600 |
| STATIC/L24/raw/g0.1/FULL | +0.007 [-0.01, +0.02] | 600 |

KV partner attention mass during readouts:

| arm | r_kv_mass_mean |
|---|---|
| ONE/KV-P/w1/3ps/FULL | 0.363 |
| ONE/KV-P/w1/FULL | 0.360 |
| ONE/KV-P/w2/3ps/FULL | 0.502 |
| ONE/KV-P/w2/FULL | 0.500 |

## Third-person manipulation checks (report only; limits: person words <= 10%, ratios within 25%)

Share of B's notes with first/second-person words, by frame:

| frame | any | note_tokens | prefill_tokens | name_mentions |
|---|---|---|---|---|
| second | 1.000 | 34.310 | 352.310 | 1.000 |
| third_strict | 0.000 | 27.373 | 353.373 | 7.012 |

Reading strength at equal weight:

| pair | ACC ratio | mass ratio | ACC third | ACC second |
|---|---|---|---|---|
| ONE/KV-P/w1/3ps/FULL vs ONE/KV-P/w1/FULL | 4.551 | 1.006 | 18.576 | 4.081 |
| ONE/KV-P/w2/3ps/FULL vs ONE/KV-P/w2/FULL | 1.592 | 1.005 | 29.326 | 18.416 |
