# T3 manipulation checks and pre-registered reading: 20260924-233653_v3_sig_t3_signal

**Verdict: leaky.** 14% of B's third-person notes still use first/second-person words (limit 10%); the study cannot answer the wording question. Candidate follow-up: notes constrained to the third person, on a new split (PI approval).

## B's note and prefill by frame (share of notes with person words; mean lengths and name mentions)

| frame | first | second | any | note_tokens | prefill_tokens | name_mentions |
|---|---|---|---|---|---|---|
| second | 1.000 | 0.000 | 1.000 | 35.212 | 353.212 | 1.000 |
| third | 0.138 | 0.000 | 0.138 | 31.913 | 354.913 | 7.025 |

Leak limit for the third-person notes: 10%. First five third notes:

> Theta's priority is lowest cost, so the best choice is Plan Oak at $52, as it is the cheapest option among all plans.
> Plan Reed has the lowest CO2 emissions at 3.8 kg, so it best aligns with Gamma's priority of lowest emissions.
> Sigma prioritizes the fastest delivery, so Plan Birch is chosen because it has the shortest delivery time of 2 days, even though it has a higher cost and emissions.
> Atlas prioritizes highest reliability, so Plan Elm is chosen because it has the highest on-time rate (84%), ensuring the most dependable delivery despite its longer duration and higher emissions.
> Delta's priority is the fastest delivery, so the best choice is Plan Cedar, which has the shortest delivery time of 3 days.

## A's reading strength (ONE/KV-P/w2/3p/FULL against ONE/KV-P/w2/FULL; unmatched beyond ±25%)

| arm | acc_increment | acc_word_increment | partner_rate | cap_drop | label_mass | mass_drop | eligible | kv_mass |
|---|---|---|---|---|---|---|---|---|
| ONE/KV-P/w2/3p/FULL | 28.603 | 26.259 | 0.956 | 0.028 | 0.994 | 0.006 | yes | 0.501 |
| ONE/KV-P/w2/FULL | 20.304 | 18.609 | 0.800 | 0.025 | 0.995 | 0.005 | yes | 0.500 |

ACC ratio 1.41; attention-mass ratio 1.00.

## M comparisons from the signal gate

| arm1 | arm2 | metric | n | mean | ci90_lo | ci90_hi |
|---|---|---|---|---|---|---|
| ONE/KV-P/w2/3p/FULL | C0/FULL | M | 80 | 56.079 | 54.213 | 57.721 |
| ONE/KV-P/w2/3p/FULL | ONE/KV-P/w2/FULL | M | 80 | -0.354 | -1.774 | 0.908 |

## Descriptive: M split by B's note (not used for the verdict; no episode dropped)

| arm | episodes | n | ΔM | 95% CI |
|---|---|---|---|---|
| ONE/KV-P/w2/3p/FULL | note uses person words | 11 | 59.632 | [56.83, 62.10] |
| ONE/KV-P/w2/3p/FULL | clean note | 69 | 55.513 | [52.84, 57.59] |
| ONE/KV-P/w2/FULL | note uses person words | 11 | 59.997 | [57.23, 62.55] |
| ONE/KV-P/w2/FULL | clean note | 69 | 55.865 | [53.58, 57.81] |
