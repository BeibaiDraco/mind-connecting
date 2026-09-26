# Summary of all results: v1–v3, as of 2026-09-25

This document lists the results of every run, by protocol version and stage: strength pilots, signal pilots, confirmatory experiments and descriptive extensions.

- **Bold** marks preregistered confirmatory results; everything else is a pilot (used to decide go or no-go) or descriptive, and supports no confirmatory inference.
- Raw data are on the SD card at `/Volumes/VERBATIM SD/mind-connecting-data/results/<run_id>/`.
- Per-stage reports are in `docs/results/` (v1 at the top level, v2 and v3 in subdirectories).
- The timeline of decisions is in `decision_log.md`; the three protocol versions are in `docs/protocol/`.

## 0. Metric quick reference

| Metric | Meaning |
|---|---|
| M | The log-odds bias toward B's rule when A is asked "which rule were you assigned at the start" (partner vs self), minus the same bias when asked "which rule was Robin assigned" (partner vs Robin). It measures "treating B's rule as one's own", with the part due to "B's rule being more salient" already removed. All effects are per-episode paired differences relative to no link (C0), in nats |
| M_NOW | Same as above, but the question is "which rule are you using now" (current intent) |
| M_WORD | Same as above, with the code word as the target |
| ACC-rule / ACC-word | The log-odds (partner vs an unused option) when asked "which rule / which code word was B assigned": whether A can read out B's content, i.e. "decodability" |
| CAP | Accuracy on common-sense questions (capability); the engineering threshold requires a drop of ≤ 0.05 |
| Total label probability | Whether the answer format is normal; threshold ≥ 0.90 |
| U-closed / U-open | Closed self-report ("one / two / partly shared") and an 80-word open self-report |
| K\* | Main interface: memory link, i.e. a KV read of the partner's private memory (prefill), weight w = 2 |

## 1. v1 (protocol-v1): weak residual bridge

### 1.1 Baseline and point selection

| Stage | run_id | Result |
|---|---|---|
| Formal G1 | 20260924-045948_g1_baseline | Threshold items 100% on both sides; BEH 0.66 and BEH-R 0.38 failed, and the BEH endpoint was retired (v0.5.2); CAP common-sense items 0.988, arithmetic items 0.354, so the item bank was changed to 18 common-sense items |
| Final-materials G1 | 20260924-052150_g1_baseline | Passed; under C0, ACC is about 0, so there is no information leakage without a link |
| Calibration | 20260924-050715_calibrate_c0 | 60 calibration episodes; layers 12/18/24 |
| Pilot A | 20260924-052736_pilot_a_screen | Selected point raw / L24 / g = 0.3 (ACC-rule +1.84) |
| Pilot B | 20260924-054404_pilot_b_grid | g\* = 0.2; main gain set {0.05, 0.1, 0.2, 0.3}; g_s\* = 0.1, not matched to ONE; N = 300 |
| Pilot C | 20260924-061858_pilot_c_recheck | G2 passed: content counterfactual for the rule +1.67 (lower bound +0.78); code word +0.43 (lower bound −0.35, failed) |

### 1.2 Formal experiment (N = 300)

Runs: 20260924-062722_main_v1 (223,500 trials), 103817_main_diag_v1, 104223_ext_layers_v1, 115148_ext_masks_v1, all complete.

- **TWO − ONE on M: −0.07 [−0.21, +0.07], Holm p = 0.31**. No difference.
- **ONE − STATIC on M: +0.18 [−0.02, +0.40], p = 0.19**. Strength not matched.
- **ONE − tagged language on M: +0.85 [+0.54, +1.20], p < 0.001**. Mainly driven by tagged language lowering M (−1.0).
- Descriptive:
  - The residual bridge did carry content across (ACC +0.16 → +0.83), but M did not rise: the content "got mixed in" without becoming "mine".
  - Untagged language: M +9.8, M_NOW +27.
  - Cutting the link while reading the question (RF) made the effect disappear.
  - The injection dimension had to be ≥ 1024 for content to get through.
  - Capability was ≥ 0.97 in every condition.

## 2. v2 (protocol-v2): a stronger channel

### 2.1 Strength pilots (looking only at ACC, capability and format)

| Stage | run_id | Result |
|---|---|---|
| S-kv first round | 20260924-144935_v2_s_kv_strength | Failed: KV-ALL w1 had ACC +8.9, but CAP dropped by 0.19; the strongest qualifying point reached only +2.2 |
| S-kv2 | 20260924-151907_v2_s_kv2_strength2 | Passed: K\* = KV-P w2 (ACC +17.6, hit rate 65%, CAP drop 0.013); strongest qualifying KV-ALL point w0.7: +5.4, hit rate 20% |
| S-static-R | 20260924-153829_v2_s_static_match-r | STATIC 0.03 matched to R-ONE(0.2) |
| S-static-K | 20260924-154706_v2_s_static_k_match-k | STATIC 0.4 was closest to K\*, but not matched (+11.1 vs +18.2) |
| E materials check | 20260924-154429_g1_v2-balanced etc. | The first version of the balanced materials failed the rehearsal check (Robin's rule in 13% of reflections); balanced2 passed (100%) |

### 2.2 Signal pilots (80 episodes)

| Stage | run_id | Result |
|---|---|---|
| Signal 1 | 20260924-155317_v2_sig1_signal | B_R no-go (−0.24 [−0.75, 0.27]); A_R no-go (−0.18); C go (unattributed − attributed, on M_NOW: +28.1 [23.4, 32.9]) |
| Signal 2 | 20260924-161505_v2_sig2_signal | D go (+56.2 [54.3, 57.8]; self question +59.8, Robin question +3.7); G2-KV passed (rule +36.7, lower bound +33.2); A_K go (+60.5, strength not matched); B_K no-go (−4.8 [−8.3, −1.2], opposite direction, CAP drop 0.09–0.14) |
| Signal E | 20260924-164449_v2_sigE_signal | E go (+53.7 under balanced materials); R-ONE(0.3) − C0: +0.02 |
| Diagnostic B (exploratory) | 20260924-170251_v2_diag_b_explore | Two-way reading of fixed memories: 95% swap; two-way reading of live states (w0.7): 19% each keeps its own, 38% only A adopts, 29% only B adopts, 13% swap |

### 2.3 Confirmatory experiment (N = 600) and descriptive extensions

| Study | run_id | Result |
|---|---|---|
| **D** | 20260924-172152_v2_main_confirm | **K\* − C0 on M: +55.8 [55.0, 56.6]; on M_NOW: +54.7 [53.7, 55.6]** |
| **A_K** | Same as above | **K\* − STATIC(0.4): +60.3 [59.3, 61.3]** (strength not matched, ACC +19.1 vs +13.3; superseded by A′ in v3) |
| **C** | Same as above | **On M_NOW: unattributed − attributed to "what B said" +26.6 [24.5, 28.8]; "your own thought" − unattributed −19.5 [−21.5, −17.4] (significant, but in the opposite direction to the prespecified one); "a stranger" − "B" −0.02 [−0.27, 0.25]** |
| **G2-KV** | 20260924-192633_v2_main_diag_confirm (60 episodes) | **Content counterfactual: rule +38.8 (one-sided 95% lower bound +34.3), code word +35.6 (lower bound +32.1)** |
| **E** | 20260924-193405_v2_bal_confirm | **Under balanced materials, K\* − C0: +52.5 [51.6, 53.5]; R-ONE(0.3) − C0: −0.05 [−0.15, 0.05]**. The residual bridge shifts the self question and the Robin question by the same amount, about +5.9, so it is not self-specific |
| Strength sweep (descriptive) | 20260924-210346_v2_ext_dose_confirm (300 episodes) | See below |

Strength sweep (KV-P, side A, relative to C0):

| w | M | ACC-rule | CAP drop | Partner attention | Self-report mentions B's code word | Self-report mentions own rule |
|---|---|---|---|---|---|---|
| 0.3 | +0.7 | +2.4 | 0.005 | 0.16 | 0% | 44% |
| 0.5 | +3.6 | +2.8 | 0.008 | 0.23 | 2% | 44% |
| 1 | +32.0 | +4.7 | 0.008 | 0.36 | 50% | 16% |
| 2 | +55.8 | +19.0 | 0.018 | 0.50 | 99% | 1% |
| 3 | +56.7 | +27.4 | 0.041 | 0.58 | 100% | 0% |

- Without a link, 53% of self-reports mention the model's own rule.
- At every level, self-reports almost never mention B's name.
- The share answering "two minds / partly shared" dropped by 0.10 at w2 and by 0.12 at w3.

## 3. v3 (protocol-v3): redesign and controls

### 3.1 Strength pilots

| Stage | run_id | Result |
|---|---|---|
| S-A′ | 20260924-230325_v3_s_static_a_match | STATIC g0.1 matched to KV-P w1 (ACC +3.59 vs +4.21) |
| S-B′ | 20260924-230820_v3_s_live_strength | Selected KV-PC (w_P 2, w_C 0.1) and KV-ALL w0.5, both the weakest level in their grid; with a stronger loop, the capability drop in the two-way conditions exceeded the limit |
| S-T3b | 20260925-012116_v3_s_t3b_match | Strict third-person version w0.6 matched to second-person w1 (ACC +4.22 vs +4.30); at the same weight the strict third-person version has much higher ACC (w1: +15.4) |

### 3.2 Signal pilots (80 episodes)

| Stage | run_id | Result |
|---|---|---|
| T3 | 20260924-233653_v3_sig_t3_signal | Judged "not clean" by the prewritten rule (13.8% of notes use "I"). Descriptive: third-person version +56.1 [54.2, 57.7], original version +56.4; difference −0.35 [−1.77, 0.91]; the 69 episodes with clean notes give +55.5 |
| A′ | 20260925-000154_v3_sig_aprime_signal | Go: +34.8 [30.6, 38.9] (90% interval), N = 600 |
| B′ | 20260925-001135_v3_sig_bprime_signal | No-go for both families: PC excess difference +0.002 [0.000, 0.004]; ALL +0.067 [0.026, 0.109] (NOW +0.121); with a link cut before answering, one side winning is about 0 |
| (B′ side result) | Same as above | Reading B's fixed memory and then answering with the link cut: M falls from +55.9 to +1.7, M_NOW still +12.9, ACC +3.2 |
| T3b | 20260925-013320_v3_sig_t3b_signal | Judged "not matched" by the prewritten rule: notes clean (0%), but partner attention ratio 0.74 and ACC ratio 1.42. Third-person w0.6 − second-person w1: −26.8; same weight w2: −0.66 [−2.19, 0.98] |

Two-way paired outcomes (B′ pilot, START question):

| Condition | Each keeps its own | A adopts B | B adopts A | Swap |
|---|---|---|---|---|
| Mutual reading of fixed memories w2, answering with the link kept | 0% | 2.5% | 3.1% | 94.4% |
| Mutual reading of live states w0.5, answering with the link kept | 54% | 18% | 26% | 2% |
| Both of the above, answering with the link cut | 97–100% | 0% | 0–3% | 0% |

### 3.3 Confirmatory experiment (N = 600, run after freezing protocol-v3)

Run: 20260925-021307_v3_confirm_confirm (92,400/92,400; SHA256 matches between the GPU machine and the SD card).

- **A′: KV-P w1 − STATIC(g0.1) on M: +33.4 [31.6, 35.3]**. The two have ACC +4.08 vs +4.18; STATIC − C0 on M is −0.3.
- **Link kept − link cut (K\*) on M: +54.8 [54.0, 55.5]**.
- **Link cut − C0 on M_NOW: +13.3 [12.3, 14.4]**. After the link cut, M is +1.9 [1.5, 2.2] (descriptive).
- **Strict third-person w2 − second-person w2 on M: −0.7, 90% interval [−1.3, −0.2], bound −11.3 → equivalent (retained)**.
- **Strict third-person w1 − second-person w1 on M: −3.2 [−4.9, −1.6] (secondary comparison)**. The effect of second-person w1 is +33.1.
- Manipulation checks:
  - Person words in the third-person version's notes: 0%.
  - Partner attention ratio is 1.006 (w1) and 1.005 (w2).
  - ACC: +18.6 vs +4.1 at w1, +29.3 vs +18.4 at w2.
  - CAP drop ≤ 0.022 in every condition.

## 4. Engineering and reviews along the way (full record in decision_log)

- **M2 core engine review** (Codex). Fixed problems such as resume identity conflicts and failed data still passing gates; results written to `docs/reviews/code_review_m2_codex.md`.
- **Independent review of the KV-read interface**. Three changes were adopted:
  - an exact mixing form (at w = 0 it is bit-for-bit equal to C0);
  - point selection in group order;
  - a check for silent KV failure.
- **v2/v3 review** (Codex, R1/R2/E1/E2), all addressed:
  - R1: the B′ outcome was redefined as a test of "beyond mutual independence", and a no-loop control and link-cut answering conditions were added;
  - R2: T3's manipulation checks and order of interpretation were written down before seeing results, and T3b was added;
  - E1: the driver's return code;
  - E2: zero SD.
- **Run discipline**: two GPU processes running at once ran out of GPU memory, so from then on only one process was run at a time; after each round of running and analysis, the instance is paused (stop, not destroy).
- **Freeze tags**: `protocol-v1`, `protocol-v2`, `protocol-v3`; result tags: `results-formal-v1`, `results-v3-confirm`.
