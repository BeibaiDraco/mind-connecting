# Signal pilot: 20260924-164449_v2_sigE_signal

- completeness: complete (7040/7040); consumable=True

## Go / no-go (first comparison of each study decides; 90% bootstrap CI)

| study | decides | comparison | metric | dir | n | mean | sd | ci90 | GO | N | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E | yes | ONE/KV-P/w2/FULL − C0/FULL | M | 0 | 80 | 53.663 | 10.525 | [51.68, 55.51] | yes | 600 |  |
| E | no | ONE/L24/raw/g0.3/FULL − C0/FULL | M | 0 | 80 | 0.016 | 1.245 | [-0.21, 0.24] |  |  |  |

## Descriptive: arm − C0 (recipient A)

| arm | ΔM | M 95% CI | ΔM_NOW | M_NOW 95% CI | ΔM_WORD | M_WORD 95% CI | ΔACC_RULE | ACC_RULE 95% CI | ΔACC_WORD | ACC_WORD 95% CI | n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LANG_UNTAG/FULL | 11.806 | [8.75, 15.06] | 35.636 | [29.45, 41.82] | 17.574 | [12.53, 22.77] | 2.352 | [0.93, 3.79] | 2.026 | [0.33, 3.84] | 80 |
| ONE/KV-P/w2/FULL | 53.663 | [51.21, 55.79] | 53.300 | [50.56, 55.71] | 42.879 | [38.81, 46.77] | 27.675 | [25.81, 29.58] | 24.609 | [22.56, 26.76] | 80 |
| ONE/L24/raw/g0.3/FULL | 0.016 | [-0.26, 0.28] | 0.852 | [0.29, 1.47] | 0.015 | [-0.28, 0.31] | 0.010 | [-1.14, 1.12] | -0.141 | [-1.15, 0.91] | 80 |

| arm | CAP | CAP drop | label mass | n |
|---|---|---|---|---|
| LANG_UNTAG/FULL | 0.988 | -0.006 | 1.000 | 80 |
| ONE/KV-P/w2/FULL | 0.969 | 0.012 | 0.992 | 80 |
| ONE/L24/raw/g0.3/FULL | 0.984 | -0.003 | 1.000 | 80 |

M split into self and Robin questions:

| arm | ΔL_START | ΔL_START_R | ΔM | ΔL_NOW | ΔL_NOW_R | ΔM_NOW |
|---|---|---|---|---|---|---|
| LANG_UNTAG/FULL | +12.243 [+9.15, +15.57] | +0.438 [+0.25, +0.64] | +11.806 [+8.75, +15.06] | +35.856 [+29.69, +42.06] | +0.220 [+0.06, +0.41] | +35.636 [+29.45, +41.82] |
| ONE/KV-P/w2/FULL | +56.871 [+54.44, +58.98] | +3.209 [+3.04, +3.39] | +53.663 [+51.21, +55.79] | +55.819 [+53.10, +58.18] | +2.519 [+2.35, +2.70] | +53.300 [+50.56, +55.71] |
| ONE/L24/raw/g0.3/FULL | +6.085 [+5.69, +6.45] | +6.068 [+5.68, +6.45] | +0.016 [-0.26, +0.28] | +6.593 [+5.88, +7.35] | +5.740 [+5.29, +6.15] | +0.852 [+0.29, +1.47] |

U-closed shift ('two' + 'partly shared'):

| arm | Δ share 'two'+'partly shared' (vs C0) | n |
|---|---|---|
| LANG_UNTAG/FULL | +0.050 [+0.00, +0.10] | 80 |
| ONE/KV-P/w2/FULL | -0.156 [-0.23, -0.08] | 80 |
| ONE/L24/raw/g0.3/FULL | +0.000 [-0.03, +0.03] | 80 |

KV partner attention mass during readouts (mean over ticks):

| arm | r_kv_mass_mean |
|---|---|
| ONE/KV-P/w2/FULL | 0.500 |
