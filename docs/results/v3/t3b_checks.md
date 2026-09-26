# T3b manipulation checks and pre-registered reading: 20260925-013320_v3_sig_t3b_signal

**Verdict: unmatched.** A reads the third-person memory with a different strength (ACC ratio 1.42, mass ratio 0.74); M differences are not attributed to wording.

## B's note and prefill by frame (share of notes with person words; mean lengths and name mentions)

| frame | first | second | any | note_tokens | prefill_tokens | name_mentions |
|---|---|---|---|---|---|---|
| second | 1.000 | 0.000 | 1.000 | 34.513 | 352.512 | 1.000 |
| third_strict | 0.000 | 0.000 | 0.000 | 27.438 | 353.438 | 7.037 |

Leak limit for the third-person notes: 10%. First five third_strict notes:

> Participant Omega chooses Plan Birch because it offers the fastest delivery time of 2 days, aligning with the priority of fastest delivery.
> Participant Gamma chooses Plan Grove because it offers the highest on-time reliability at 92%, aligning with their priority of highest reliability.
> Participant Delta chooses Plan Thorn because it has the lowest cost at $55, aligning with their priority of minimizing cost.
> Participant Sigma chooses Plan Elm because it offers the highest on-time reliability at 95%, aligning with their priority of highest reliability.
> Participant Lambda chooses Plan Iris because it offers the fastest delivery in just 2 days, aligning with their priority of the fastest delivery.

## A's reading strength (ONE/KV-P/w0.6/3ps/FULL against ONE/KV-P/w1/FULL; unmatched beyond ±25%)

| arm | acc_increment | acc_word_increment | partner_rate | cap_drop | label_mass | mass_drop | eligible | kv_mass |
|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w0.6/3ps/FULL | 7.147 | 13.214 | 0.125 | 0.006 | 1.000 | -0.000 | yes | 0.266 |
| ONE/KV-P/w1/FULL | 5.043 | 5.772 | 0.237 | 0.009 | 0.999 | 0.001 | yes | 0.361 |
| ONE/KV-P/w2/3ps/FULL | 29.498 | 23.833 | 0.969 | 0.016 | 0.996 | 0.004 | yes | 0.502 |
| ONE/KV-P/w2/FULL | 19.333 | 17.037 | 0.713 | 0.019 | 0.996 | 0.004 | yes | 0.500 |

ACC ratio 1.42; attention-mass ratio 0.74.

## M comparisons from the signal gate

| arm1 | arm2 | metric | n | mean | ci90_lo | ci90_hi |
|---|---|---|---|---|---|---|
| ONE/KV-P/w0.6/3ps/FULL | ONE/KV-P/w1/FULL | M | 80 | -26.849 | -31.079 | -22.628 |
| ONE/KV-P/w1/FULL | C0/FULL | M | 80 | 32.350 | 27.970 | 36.722 |

## Descriptive: M split by B's note (not used for the verdict; no episode dropped)

| arm | episodes | n | ΔM | 95% CI |
|---|---|---|---|---|
| ONE/KV-P/w0.6/3ps/FULL | note uses person words | 0 | NA | [nan, nan] |
| ONE/KV-P/w0.6/3ps/FULL | clean note | 80 | 5.501 | [3.86, 7.49] |
| ONE/KV-P/w1/FULL | note uses person words | 0 | NA | [nan, nan] |
| ONE/KV-P/w1/FULL | clean note | 80 | 32.350 | [27.25, 37.60] |
