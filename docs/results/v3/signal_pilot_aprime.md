# Signal pilot: 20260925-000154_v3_sig_aprime_signal

- completeness: complete (5280/5280); consumable=True

## Go / no-go (first comparison of each study decides; 90% bootstrap CI)

| study | decides | comparison | metric | dir | n | mean | sd | ci90 | GO | N | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A' | yes | ONE/KV-P/w1/FULL − STATIC/L24/raw/g0.1/FULL | M | 0 | 80 | 34.759 | 23.020 | [30.59, 38.87] | yes | 600 |  |

## Descriptive: arm − C0 (recipient A)

| arm | ΔM | M 95% CI | ΔM_NOW | M_NOW 95% CI | ΔM_WORD | M_WORD 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w1/FULL | 34.428 | [29.38, 39.22] | 35.072 | [29.55, 40.24] | 28.183 | [23.73, 32.59] | 4.680 | [3.50, 5.85] | 5.705 | [4.22, 7.20] | 80 |
| STATIC/L24/raw/g0.1/FULL | -0.330 | [-0.63, -0.09] | -0.414 | [-0.79, -0.10] | -0.008 | [-0.14, 0.13] | 3.719 | [2.89, 4.58] | 0.275 | [-0.25, 0.83] | 80 |

| arm | CAP | CAP drop | label mass | n |
|---|---|---|---|---|
| ONE/KV-P/w1/FULL | 0.991 | 0.006 | 0.999 | 80 |
| STATIC/L24/raw/g0.1/FULL | 0.994 | 0.003 | 1.000 | 80 |

M split into self and Robin questions:

| arm | ΔL_START | ΔL_START_R | ΔM | ΔL_NOW | ΔL_NOW_R | ΔM_NOW |
|---|---|---|---|---|---|---|
| ONE/KV-P/w1/FULL | +36.644 [+31.59, +41.45] | +2.216 [+1.99, +2.45] | +34.428 [+29.38, +39.22] | +36.730 [+31.23, +41.86] | +1.659 [+1.41, +1.91] | +35.072 [+29.55, +40.24] |
| STATIC/L24/raw/g0.1/FULL | +0.355 [+0.18, +0.54] | +0.685 [+0.39, +1.04] | -0.330 [-0.63, -0.09] | +0.337 [+0.14, +0.54] | +0.750 [+0.40, +1.15] | -0.414 [-0.79, -0.10] |

U-closed shift ('two' + 'partly shared'):

| arm | Δ share 'two'+'partly shared' (vs C0) | n |
|---|---|---|
| ONE/KV-P/w1/FULL | +0.013 [-0.06, +0.08] | 80 |
| STATIC/L24/raw/g0.1/FULL | +0.025 [-0.03, +0.08] | 80 |

KV partner attention mass during readouts (mean over ticks):

| arm | r_kv_mass_mean |
|---|---|
| ONE/KV-P/w1/FULL | 0.360 |
