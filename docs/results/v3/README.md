# Index of results for protocol v3

Protocol: [PROTOCOL_V3.md](../../protocol/PROTOCOL_V3.md) (frozen as `protocol-v3`). Research decisions are in [decision_log.md](../../../decision_log.md).

Raw data are on the SD card at `/Volumes/VERBATIM SD/mind-connecting-data/results/<run_id>/`, and on the GPU machine at `/workspace/mb-data/results/<run_id>/`. Each report can be regenerated with the scripts under `scripts/`: `report_pilot.py`, `report_v2_signal.py`, `report_t3_checks.py`, `report_v3_pair_signal.py`.

## Strength pilots (looking only at ACC, capability and format)

| File | run_id | Conclusion |
|---|---|---|
| [strength_pilot_s_static_a.md](strength_pilot_s_static_a.md) | 20260924-230325_v3_s_static_a_match | A′: STATIC g = 0.1 is comparable in strength to KV-P w1 (ACC-rule +3.59 vs +4.21, judged matched) |
| [strength_pilot_s_live.md](strength_pilot_s_live.md) | 20260924-230820_v3_s_live_strength | B′ point selection: KV-PC (w_P = 2, w_C = 0.1) and KV-ALL (w = 0.5), both families landing on the weakest level of the grid; with a stronger loop, the two-way conditions hurt capability |
| [strength_pilot_s_t3b.md](strength_pilot_s_t3b.md) | 20260925-012116_v3_s_t3b_match | T3b: the third-person version (note forced to open in the third person) at w = 0.6 is comparable in strength to second-person w1 (ACC-rule +4.22 vs +4.30, matched). At the same weight the third-person version reads out more clearly (w1: +15.4 vs +4.3) |

## Signal pilots (80 episodes)

| File | run_id | Conclusion |
|---|---|---|
| [signal_pilot_t3.md](signal_pilot_t3.md), [t3_checks.md](t3_checks.md) | 20260924-233653_v3_sig_t3_signal | Judged "not clean" by the rule written in advance: 13.8% of third-person notes contain the first person, against a ceiling of 10%. So T3 formally cannot answer the wording question. Descriptive results below |
| [signal_pilot_aprime.md](signal_pilot_aprime.md) | 20260925-000154_v3_sig_aprime_signal | A′ go: KV-P w1 − STATIC(g0.1) on M +34.8 [30.6, 38.9] (90%), N = 600 |
| [signal_pilot_bprime.md](signal_pilot_bprime.md) | 20260925-001135_v3_sig_bprime_signal | B′ no-go for both families: PC excess difference +0.002; ALL is +0.067 [0.026, 0.109] (90%), below 0.10 |
| [signal_pilot_t3b.md](signal_pilot_t3b.md), [t3b_checks.md](t3b_checks.md) | 20260925-013320_v3_sig_t3b_signal | Judged "not matched" by the prewritten rule: the notes are now clean (0%), but the read strength was not balanced (ACC ratio 1.42, attention ratio 0.74). Descriptive results below |

**T3 key points**:

- **Interpretation written in advance**: not clean, so it formally cannot answer the "person" question. Read strength was not matched either: in the third-person version A's ACC for B's rule is higher (+28.6 vs +20.3, ratio 1.41), with the same partner attention mass (0.50).
- **Descriptive results**: B's memory had "you" removed, most notes did not contain "I" either, and B's name appeared about 7 times (1 time in the original version), yet A's claiming did not decrease: K\*-3p − C0 on M is +56.1 [54.2, 57.7], K\* is +56.4, and the difference between the two is −0.35 [−1.77, 0.91]. In the 69 episodes with clean notes it is +55.5, and the original version on the same episodes is +55.9. The 11 sentences that leaked a person word are all "I choose Plan X … aligning with {B}'s priority".
- **Contrast with study C**: a source tag in a language message lowers claiming; a name tag written into the memory being read does not.
- **Limitation**: K\* sits on the saturated part of the strength curve (+55.8 at w = 2, +56.7 at w = 3), where a medium-sized wording effect might not show up.

**A′ key points** (strength-matched "memory reading vs static direction"):

- The two give A a comparable ability to state B's rule: ACC-rule relative to C0 is +4.7 and +3.7 respectively (retested on the same new episodes; the gap is about 20%, within 25%).
- Claiming differs greatly: KV-P w1 − C0 on M is +34.4 [29.4, 39.2], STATIC − C0 is −0.3 [−0.6, −0.1].
- Broken down: memory reading changes almost only the "my rule" question (+36.6, Robin question +2.2); the static direction produces only slight shifts in the same direction on both questions (+0.4, +0.7).
- This closes the loophole of unbalanced strength in v2 A_K: at comparable information, only the memory-reading channel makes A state B's rule as its own.

**B′ key points** (prespecified threshold: no-go for both families):

- **KV-PC (w_P = 2, w_C = 0.1)**: the loop is too weak, and the outcome is the same as the no-loop two-way KV-P w2, both 92–94% swap (each side takes the other's rule as its own).
- **KV-ALL w0.5**: in the two-way condition reading each other's live states, 43% of pairs hold the same rule, versus 7% without a loop. After removing the part due to "each being pulled off course separately", the excess difference on START is +0.067 (the interval excludes 0, but it is below 0.10), and +0.121 on NOW. Swaps are actually fewer than expected under mutual independence (2% vs about 5%).
- **Link cut at question time (RF)**: in both families one side winning drops to about 0% (PC 3%, the same as the control), and each member of the pair returns to its own rule.

**After the link is cut (descriptive, from side A and side B of the B′ conditions)**:

| Condition (side A, relative to C0) | ΔM (START) | ΔM_NOW | ΔACC-rule |
|---|---|---|---|
| Two-way KV-P w2, answering with the link kept | +55.9 | +54.9 | +19.6 |
| Two-way KV-P w2, answering with the link cut | +1.7 | +12.9 | +3.2 |
| Two-way KV-ALL w0.5, answering with the link kept | +10.1 | +17.2 | +3.5 |
| Two-way KV-ALL w0.5, answering with the link cut | +0.1 | +0.3 | +0.1 |

- In KV-P, A's reading of B's memory is unaffected by whether B also reads A, so for A the first and second rows are equivalent to one-way reading.
- Claiming happens mainly when "the partner's memory can be read while answering": after the link cut, A's answer to "the rule I was assigned at the start" basically recovers. But "which one do I use now" is still shifted by +12.9, which shows that the reflection during the link left a trace. Side B shows the same pattern.
- This is a descriptive result; whether to test it formally in a confirmatory experiment is for the PI to decide.

**T3b key points** (note forced to open in the third person; prewritten interpretation: not matched):

- All notes are clean (0% contain person words).
- The ACC-balanced pair (third-person w0.6 vs second-person w1): claiming +5.5 vs +32.4, difference −26.8 [−31.1, −22.6] (90%). But on this batch of new episodes, the third-person version has higher ACC (+7.1 vs +5.0) and lower partner attention (0.27 vs 0.36), beyond the prespecified tolerance, so by the rule the difference is not attributed to wording.
- The same-weight pair (both versions at w2, attention 0.50 vs 0.50): claiming +55.8 vs +56.4, difference −0.66 [−2.2, 1.0], but this level is already saturated.
- By rough interpolation of the second-person "attention–claiming" curve from the v2 strength sweep (a different split), second-person claiming at an attention of 0.27 would be about +11. So most of the gap between w0.6 and w1 may come from attention rather than wording.
- Conclusion: at strong reading, the grammatical person of the wording and name tags do not affect claiming; whether wording matters at medium strength has no clean answer yet.

## Confirmatory experiment (N = 600, run after protocol-v3 was frozen)

| File | run_id | Status |
|---|---|---|
| [confirmatory_v3.md](confirmatory_v3.md) | 20260925-021307_v3_confirm_confirm | Done: 92,400/92,400; SHA256 of the records matches between the GPU machine and the SD card |

**Preregistered results** (paired t, Holm within family; 95% intervals from 10,000 bootstrap resamples):

- **A′**: KV-P w1 − STATIC(g0.1) on M: +33.4 [31.6, 35.3] (Holm p < 10⁻¹⁰⁰). A's ability to state B's rule is almost the same for the two (ACC +4.08 vs +4.18); STATIC − C0 on M is −0.3.
- **RF (link cut vs link kept)**:
  - K\* link kept − K\* link cut, on M: +54.8 [54.0, 55.5];
  - K\* link cut − C0, on M_NOW: +13.3 [12.3, 14.4].
  - After the link cut, M is +1.9 [1.5, 2.2] (descriptive): A's answer to "the rule I was assigned at the start" basically recovers, but "which one do I use now" is still clearly shifted.
- **T3-K\* equivalence test**: strict third-person w2 − second-person w2 on M: −0.7, 90% interval [−1.3, −0.2], above the bound −11.3 (20% of the second-person effect of +56.6) → **retained**.
- **T3-w1 (secondary)**: strict third-person w1 − second-person w1 on M: −3.2 [−4.9, −1.6] (Holm p = 0.0002), about 10% of the second-person effect (+33.1).
- **Manipulation checks**:
  - Person words in third-person notes: 0%.
  - At the same weight, the ratio of partner attention mass is 1.006 (w1) and 1.005 (w2).
  - The third-person version has much higher ACC: +18.6 vs +4.1 at w1, +29.3 vs +18.4 at w2.
  - CAP drop ≤ 0.022 and total label probability ≥ 0.995 in every condition.

**Implication**: claiming is not caused by second-person wording; at medium strength, the third-person record and name tags only slightly reduce claiming, and at that point the content of the third-person version is actually easier to read out.
