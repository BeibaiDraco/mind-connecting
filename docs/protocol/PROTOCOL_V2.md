# Protocol v2: five follow-up studies after v1 (A–E)

Date: 2026-09-24. Status: **finalized before freeze** (see Section 7). Once frozen it becomes `protocol-v2` (tag plus `FREEZE_protocol_v2.txt`).
v1 (`EXPERIMENT_DESIGN.md`, tag `protocol-v1`) and the v1 results (tag `results-formal-v1`) stay unchanged, and their data are not merged with v2.
For the research motivation see [formal_v1_summary.md](../results/formal_v1_summary.md). PI decision: run all five (2026-09-24); but strength must be confirmed first, and an early signal seen first, before any large-scale experiment.

## 0. What stays the same as v1

The model, task materials (except for E), readout questions (BEH stopped), scoring (M, M_NOW, M_WORD, ACC, CAP, total label probability), paired design, unit of analysis (episode), and failure-handling and resume rules all carry over from v1. The v1 residual additive bridge (layer 24, raw, g = 0.2 / 0.3) is called the **R interface** in v2.

## 1. Two gates

**Strength threshold** (applies to D's new interface and to all studies that depend on it). Settings are selected only from ACC, CAP and format:

- Engineering threshold: CAP drop relative to C0 ≤ 0.05; total label probability ≥ 0.90, with a drop ≤ 0.05.
- Strength criterion: ACC-rule gain relative to C0 ≥ 5 nat, **and** the fraction of ACC-rule questions on which A's argmax hits the partner's true rule ≥ 30% (about 6% at C0 in v1).
- Point selection: among points that meet the engineering threshold, take the one with the largest ACC-rule gain.
- If the strength criterion is not met, strengthen in a prespecified order: first a memory link that reads only the C segment → reading the whole cache → raising the cap on partner weight → interpolation write (the contract in Section 5 must be completed first). Each step is a strength pilot and does not look at M. If the criterion is still not met, report only the strength pilots.

**Strength pilot log (written before running)**:

- First round, S-kv (ranges C and ALL, w ∈ {0.01, 0.03, 0.1, 0.3, 1, 3}, 40 episodes): strength criterion not met.
  - ALL at w = 1 gave ACC-rule +8.9 nat and a hit rate of 47%, but CAP dropped 0.19, so it was ineligible.
  - The strongest eligible point was ALL w = 0.3, with only +2.2 nat and 11%.
  - This round used the pre-review implementation, which is mathematically equivalent to the later exact mixture form and numerically almost identical; the results are kept for reference.
- Second round, S-kv2 (decided after the first round and before the second round was run):
  1. Densify the grid between eligible and ineligible: for C and ALL, w ∈ {0.4, 0.5, 0.6, 0.7, 0.85};
  2. Add range **P**: read only the partner's prefill segment (private prompt, note, reflection prompt), not the partner's current reflection stream, w ∈ {0.3, 0.5, 1, 2, 3}. Rationale: the capability drop in the first round appears to come from local attention during answering being distracted by the tokens the partner is generating at that moment.
- Selection order: C → ALL → P. In each group take the eligible point with the largest ACC gain, then test the strength criterion; the first group that passes is selected. If none passes, move to interpolation write (Section 5).
- **Second-round result: strength threshold passed.**
  - Strongest eligible point in group C, w = 0.85: +3.5 nat, hit rate 11%, not passed.
  - Strongest eligible point in group ALL, w = 0.7: +5.4 nat, but hit rate 20%, not passed.
  - **Group P, w = 2: ACC-rule +17.6 nat, hit rate 65%, secret word +17.3, CAP drop 0.013, passed, selected as K\*.**
  - Group P, w = 3 reached +27.6 nat and a hit rate of 99%, but CAP dropped 0.056, ineligible.

**Revisions prompted by K\* (written before running)**:

- K\* reads only the partner's fixed prefill, with no loop of mutual influence. Under TWO, what A reads is exactly the same as under ONE, so study B cannot use K\*.
- The KV version of study B instead uses the strongest eligible point among ranges that have a loop, namely **KV-ALL w = 0.7** (+5.4 nat, hit rate 20%). It misses the hit-rate part of the strength criterion, which is flagged honestly in reporting; B also keeps the R-interface comparison.
- Study A's STATIC(match K) targets K\*. If no eligible STATIC point comes within the 25% tolerance of K\*, it is marked "unmatched", run anyway and reported honestly.

**Signal threshold** (PI instruction, applies to every study, before the confirmatory experiment):

- On a signal pilot of 80 new episodes, compute the paired difference for the study's first primary comparison.
- Pass condition: when a direction is prespecified, the direction agrees; when none is prespecified, it is nonzero; |mean| ≥ 0.3 nat; the 90% episode-bootstrap interval excludes 0.
- If not passed: the study stops at the pilot and is reported honestly. For a study that passes, the pilot results first go to the PI for confirmation, then it is frozen, then it goes to large scale.
- This is a study-level "go or no-go" judgment, not parameter selection. Signal-pilot data are not merged into the confirmatory sample.

**Sample size**: N = min(600, max(300, ⌈(3.236 · SD / 0.3)²⌉)), a multiple of 4; SD is the largest standard deviation of the paired differences for the study's primary comparisons in the signal pilot. Report the minimum detectable effect at N.

## 2. The five studies

| Study | Question | Conditions (receiver A, FULL) | Primary comparisons (Holm correction within study, two-sided paired t) |
|---|---|---|---|
| **D Strong interface** | When partner content flows in heavily, does the boundary between self and other still hold? | C0; K-ONE\* (memory link, selected by the strength threshold) | Primary: K-ONE\* − C0 on M; K-ONE\* − C0 on M_NOW. Validity: the KV version of the content counterfactual (G2-KV, one-sided 95% lower bound for the rule > 0) must pass |
| **B Two-way present intent** | Does a two-way connection let "the priority I am using now" be carried off by the partner more? | ONE and TWO at KV-ALL w = 0.7 (see the revision in Section 1); R-ONE(0.3), R-TWO(0.3) | K-TWO − K-ONE on M_NOW; R-TWO(0.3) − R-ONE(0.3) on M_NOW (prespecified direction: TWO > ONE) |
| **A Strength-matched static direction** | At equal content amount, do a live state and a static rule direction differ in their effect on self-attribution? | K-ONE\* and STATIC(match K); R-ONE(0.2) and STATIC(match R) | K-ONE\* − STATIC(match K) on M; R-ONE(0.2) − STATIC(match R) on M (no prespecified direction) |
| **C Source-label gradient** | What makes a piece of content "mine"? | LANG-tag, LANG-untag, LANG-self, LANG-stranger | On M_NOW: untag − tag (prespecified > 0); self − untag (prespecified > 0); stranger − tag (none prespecified) |
| **E Rehearsal balance** | Does the slight drop of M with connection in v1 come from the asymmetry "one's own rule is rehearsed and Robin's is not"? | Under balanced materials: C0; the strongest eligible latent interface (K-ONE\*, or R-ONE(0.3) if that is ineligible); LANG-untag | Under balanced materials, that interface − C0 on M (no prespecified direction; the same comparison under v1 materials serves as a descriptive reference) |

STATIC matching rule: in the STATIC grid, take the point whose ACC-rule gain differs least from the target arm's, with ties going to the smaller g; if the difference is > 25% of the target gain, mark it "unmatched", still run it and report honestly.
Grid: low range {0.005, 0.01, 0.015, 0.02, 0.03, 0.05}, high range {0.1, 0.2, 0.3, 0.5}.

**The four source framings in C** (B's verbatim reflection under C0, with identical content, placed after P and before C):

- tag: `{partner_code} shared these thoughts: "{text}"` (v1)
- untag: `Here are some thoughts: "{text}"` (v1)
- self: `Here are your own earlier thoughts: "{text}"`
- stranger: `A stranger shared these thoughts: "{text}"`

**Balanced materials for E**: the last sentence of P becomes "...explain your choice in one sentence. Then say which plan Robin would choose under Robin's priority, and repeat Robin's code word."; the reflection prompt becomes "...reflect on your decision and on Robin's, and mention both code words once."; the note cap rises from 48 to 80 tokens; everything else is unchanged. E gets its own calibration on the balanced materials (60 episodes) and a baseline check: START, NOW, WORD and their Robin questions ≥ 0.90, and the rate at which Robin's rule and code word appear in the reflection is at least half the rate for the model's own (the manipulation check for rehearsal balance). E keeps v1's g, with no new parameter selection.

## 3. Execution order and checkpoints

| Stage | Content | Readouts |
|---|---|---|
| S-static | STATIC grid + R-ONE(0.2) + C0, 40 episodes | ACC, CAP |
| Signal pilot 1 | C0, R-ONE(0.2), R-ONE(0.3), R-TWO(0.3), STATIC(match R), the four LANG variants, 80 episodes | full set (excluding U-open, START-N) |
| S-kv | KV interface strength pilot (grid in Section 4) + C0, 40 episodes | ACC, CAP |
| S-static-K | STATIC grid + K-ONE\* + C0, 40 episodes | ACC, CAP |
| Signal pilot 2 | C0, K-ONE\*, K-TWO\*, STATIC(match K), CF-KV, LANG-untag, 80 episodes | full set (as above) |
| E preparation | calibration and baseline check on the balanced materials, 60 episodes each | — |
| Signal pilot E | under balanced materials: C0, E's interface, LANG-untag, 80 episodes | full set (as above) |
| **PI checkpoint** | each study's strength and signal threshold results, N, and a go/no-go recommendation | — |
| Freeze v2 | includes only the studies that passed | — |
| Confirmatory experiment | A–D combined into one stage (new split), E as a separate stage | full set (as above) |

All stages use new, mutually non-overlapping splits (`v2_*`), which also do not overlap with any v1 split.

## 4. Contract for the memory link interface (K)

Defined item by item following the required items listed in Section 14 of v1:

- **Mechanism**: in every attention layer, the receiver can read the partner's keys/values in addition to its own cache (appended, not replaced, and neither side's cache is modified).
- **Layers**: all 36 layers.
- **Token range**: `KV-C` reads only the tokens the partner produces in the C and R phases; `KV-ALL` reads the partner's entire valid cache (P, note, C, R); `KV-P` reads only the partner's prefill segment (P, note, reflection prompt). None of them includes the partner's padding.
- **RoPE / position**: keys keep the rotation computed at the partner's own positions and are not re-rotated; the receiver's queries use its own positions.
- **Causal visibility and delay**: keys the partner has just written in the current tick are not visible, so partner information still has a 1-tick delay, consistent with the R interface. No reading during prefill.
- **Cache cap**: the partner part does not exceed the partner's current valid length; each row's total does not exceed the sum of both sides' lengths.
- **Strength**: add log w to the attention logits of partner keys (grid in Section 1); w = 1 means partner tokens are treated the same as the receiver's own tokens.
- **Computation**: a joint softmax over "own keys + partner keys", written in mixture form o = o_own + β(o_par − o_own), β = σ(lse_par − lse_own), i.e. the total attention falling on partner keys. At w = 0 it is bitwise identical to not reading.
- **One-way and two-way**: under ONE only A reads B; under TWO both read each other, and each side reads the cache the other computed while reading it (a mutual loop, with a 1-tick delay each way).
- **FULL / RF / RO**: same as the R interface; when the link is cut in the R phase, the partner no longer advances.
- **Controls**: C0 (no reading); CF-KV: partner B's rule and secret word replaced with the unused rule / distractor word, with A's input and question tokens completely unchanged (G2-KV); MISMATCH-KV as descriptive.
- **Manipulation check**: record the attention mass the receiver places on partner keys at each tick (averaged over layers and heads), and separately record the part that falls on the partner's C/R segment (excluding the attention-sink token at the start of the prompt).
- **Correctness tests**: as w → 0 the output matches not reading; the partner's current-tick keys are invisible; under ONE, B's computation is unaffected; branches and snapshots do not contaminate each other.

## 5. Interpolation write (enabled only if KV fails the strength criterion)

Before enabling, the contract must be completed per Section 14 of v1 and B1 of `design_review3_codex.md`: write operator u ← u + δ, δ = α(q̃ − u), α ∈ [0, 1]; the source of q̃ and norm matching; zero-norm handling; one operator shared by all conditions; the interpolation target for STATIC; energy matching applied to δ. Once it is completed, a separate strength pilot is set up.

## 6. Analysis

- Each study is one family, with Holm correction within the study; 95% intervals from a 10,000-draw episode bootstrap; robustness report as in v1.
- Descriptive: each arm minus C0 on M, M_NOW, M_WORD, ACC, CAP, total label probability; the decomposition of M (self question and Robin question); U-closed; convergence of A and B; KV partner attention mass.
- Wording of conclusions as in v1: no claims of consciousness, number of subjects, or phase transitions.

## 7. Signal threshold results and PI decision (written before the freeze)

| Study | First primary comparison (signal pilot, 80 episodes) | Result | Verdict |
|---|---|---|---|
| D | K\* − C0 on M | +56.2, 90% interval [54.3, 57.8]; G2-KV rule lower bound +33.2 | go |
| A_K | K\* − STATIC(0.4) on M | +60.5 [58.4, 62.6] (strength unmatched: ACC +18 vs +13) | go |
| C | untag − tag on M_NOW | +28.1 [23.4, 32.9] | go |
| E | K\* − C0 on M under balanced materials | +53.7 [51.7, 55.5] | go |
| A_R | R-ONE(0.2) − STATIC(0.03) on M | −0.18 [−0.38, 0.05] | no go (too small) |
| B_R | R-TWO(0.3) − R-ONE(0.3) on M_NOW | −0.24 [−0.75, 0.27] | no go (direction does not match) |
| B_K | TWO − ONE (KV-ALL w0.7) on M_NOW | −4.8 [−8.3, −1.2] | no go (opposite direction) |

**PI decision (2026-09-24)**: run the confirmatory experiments for D, A_K, C and E as originally planned, with N = 600 per the rule in Section 1. For A_R, B_R and B_K, which did not pass, first analyze the causes and work out fixes, report to the PI and then revisit; no large-scale runs. Add one prespecified descriptive extension: a KV-P strength sweep (w = 0.3 / 0.5 / 1 / 2 / 3) on the first 300 episodes of the `v2_main` split, with readouts including U-open. w = 3 exceeds the engineering threshold and is descriptive only.

**Confirmatory stages** (configs generated by `scripts/make_v2_main.py` from the signal-pilot outputs):

| Stage | split | N | Conditions | Study families (Holm within family) |
|---|---|---|---|---|
| `v2_main` | v2_main | 600 | C0, K\*, STATIC(0.4), the four LANG variants | C: untag−tag, self−untag, stranger−tag (on M_NOW); D: K\*−C0 (on M, M_NOW); A_K: K\*−STATIC(0.4) (on M) |
| `v2_main_diag` | v2_main (first 60, 4 permutations) | 60 | C0, K\*, CF-KV | recheck of G2-KV in the formal sample (descriptive) |
| `v2_bal` | v2_bal | 600 | balanced materials balanced2: C0, K\*, R-ONE(0.3), LANG-untag | E: K\*−C0, R-ONE(0.3)−C0 (on M) |
| `v2_ext_dose` | v2_main (first 300) | 300 | C0, KV-P w ∈ {0.3, 0.5, 1, 2, 3} | descriptive |
