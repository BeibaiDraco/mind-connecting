# Protocol v3: redesigning the two studies that failed the threshold (B′, A′)

Date: 2026-09-24 (confirmatory part 2026-09-25). Status: **frozen as `protocol-v3`** (freeze manifest `FREEZE_protocol_v3.txt`); any later change requires a new version. v1, v2 and their results are unchanged, and data are not merged.
Background: v2's B_R, B_K and A_R failed the signal threshold. The PI asked that the causes be found and fixes worked out first, before deciding whether to go to large scale (decision_log 2026-09-24).
The v2 exploratory diagnostic `20260924-170251_v2_diag_b_explore` (40 episodes, both the A and B sides measured) gave clues:

| Condition | Each keeps its own | Only A adopts B | Only B adopts A | Swap |
|---|---|---|---|---|
| TWO KV-P w2 (mutual reading of fixed memories) | 0% | 0% | 5% | 95% |
| TWO KV-ALL w0.7 (reads the partner's live state, with a loop of mutual influence) | 19% | 38% | 29% | 13% |
| ONE KV-ALL w0.7 (one-way, only A can adopt) | 56% | 44% | — | — |

(START question; the NOW question shows the same pattern. Exploratory results from 40 episodes, clues only.) When the link is two-way with a loop, the pair often converges on the same rule, and the winning side can be either one.

**One hypothesis** (untested): v2's M looks only at whether A adopts B and misses the "B adopts A" half, so the direction looks reversed. Another possibility is that that point itself damaged capability: at KV-ALL w0.7 two-way, CAP is 0.875 for A and 0.881 for B, versus 0.950 for A one-way and 0.981 in the condition reading fixed memories. With noisier answers, claiming also shrinks. (Rewritten per Codex review R1, approved by the PI 2026-09-24.)

## 1. Common rules

- The two gates, point selection looking only at ACC/CAP/format, signal pilots not merged into the confirmatory sample, and the N rule: carried over from Section 1 of PROTOCOL_V2, with only the exceptions below.
- New splits start with `v3_` and do not overlap with any earlier split.
- For two-way conditions, the engineering threshold is checked on both the A and B sides (CAP drop ≤ 0.05, total label probability ≥ 0.90, with a drop ≤ 0.05).

## 2. Study B′: does a two-way connection make the two merge into one

**Question**: with a loop of mutual influence, do the two sides converge on the same rule (merging), rather than each simply taking the other's content as its own (swap)?

**Readout method and estimand** (revised per Codex review R1, approved by the PI 2026-09-24):

- Each episode's C48 snapshot is copied into two mutually independent branches: branch 1 asks A while B keeps reflecting; branch 2 asks B while A keeps reflecting. A pair's outcome is assembled from "A's answer in branch 1" and "B's answer in branch 2".
- So "merging" here means **the answers agree when the two sides are probed separately**, not that the two sides answer jointly at the same moment.
- In the FULL readout the connection is still open, so agreement may partly come from direct reading at the moment of answering. The RF readout (link cut at question time, each side answering from its own state only) tests whether the merging has already been stored in each side's state.
- A readout in which both sides answer simultaneously would require changing the runtime; v3 does not do it.

**Pair-level outcomes**: for each permutation of each episode, take the **physical rule** chosen by the argmax of A and of B on START (and NOW):

- **Merge (one side wins)**: both sides hold the same rule, and that rule belongs to one of them: A adopts B while B keeps its own, or B adopts A while A keeps its own.
- **Swap**: A picks B's rule while B picks A's rule.
- **Keep**: each picks its own rule.
- **Both pick a third rule**: both sides pick Robin's rule or the unassigned rule. Not counted as merging; reported separately as a possible sign of damage.

The metric is each episode's proportion across permutations.

**The part beyond independence (excess)**:

- Looking only at the merge proportion would also count "each side being pulled off independently" as merging. For example, if each side adopts the other with probability 30%, independently of each other, the merge proportion is 0.3×0.7 + 0.7×0.3 = 42% two-way, but only 30% one-way.
- So excess is used to measure the coupling between the two sides' choices:
  - excess = observed merge proportion − [P(A adopts)·P(B keeps) + P(A keeps)·P(B adopts)].
  - All proportions are computed within the same condition, with every episode weighted equally.
  - Intervals come from resampling episodes; when two conditions are compared, both use the same set of episodes.
- When different episodes are pooled, asymmetry between episodes (one side's rule being inherently more salient) also produces excess. So the primary comparison is not against 0 but against a **two-way control without a loop**.

**No-loop control**: two-way reading of each other's fixed memories (KV-P), with the weight set to that interface's prefill weight (w_P = 2 for KV-PC; its own w for KV-ALL).

- It reads the same fixed content as the loop condition, only without reading the partner's live state.
- In it the two sides do not influence each other, so its excess reflects only the asymmetry between episodes.

**Interface candidates** (with a loop of mutual influence, and not damaging capability):

- **KV-ALL**, w ∈ {0.5, 0.55, 0.6};
- **KV-PC** (split weights): partner prefill-segment weight w_P = 2, partner C/R-segment weight w_C ∈ {0.1, 0.3, 0.5}.

**Strength pilot (S-B′, 40 episodes, both the A and B sides measured)**:

- Each candidate runs ONE and TWO, plus C0.
- Point selection (looking only at ACC/CAP/format): subject to TWO meeting the engineering threshold on both sides, take the largest w for KV-ALL and the largest w_C for KV-PC. KV-PC first, then KV-ALL. One point per family goes into the signal pilot.
- PROTOCOL_V2's 5 nat strength criterion does not apply: B′'s strength is defined by "a loop exists and capability is not damaged"; report the A-side ACC gain and the partner attention mass.

**Signal pilot** (80 episodes, new split `v3_sig_bprime`, both the A and B sides measured):

- **Conditions**: C0; for each selected interface:
  - ONE and TWO with a loop (FULL readout);
  - TWO with a loop (RF readout);
  - the no-loop control TWO (both FULL and RF readouts).
  
  Configs are generated mechanically by `scripts/make_v3_bprime_signal.py` from the S-B′ point selection.
- **First primary comparison**: excess on START, loop TWO − no-loop TWO (FULL), prespecified direction > 0.
- **Threshold**: difference ≥ 0.10, and the 90% bootstrap interval excludes 0.
- **Two further comparisons within the same study**: they enter the computation of N, and in the confirmatory experiment they are Holm-corrected together with the primary comparison.
  - the same comparison under the RF readout, testing whether the merging was stored in each side's state;
  - the same comparison on NOW.
- **N**: the bootstrap standard error of the excess difference times √n serves as the paired SD, δ = 0.10, same formula, 300–600.

**Descriptive**:

- the excess of each of the two conditions;
- the proportions of merge, swap, keep, and both picking a third rule;
- who wins: relation to the difference in the two sides' prefix lengths and to rule type; excess stratified by rule combination;
- the TWO − ONE merge proportion (formerly the first primary comparison, demoted to descriptive);
- the ratio of the RF to the FULL merge proportion;
- M for both sides; CAP and total label probability on both sides.

## 3. Study A′: "live memory vs static direction" with strictly matched strength

- **Target arm**: KV-P w = 1 (in v2 S-kv2, ACC-rule +5.9, CAP drop 0.006).
- **STATIC grid**: {0.1, 0.15, 0.2, 0.25, 0.3} (layer 24, v2 calibration). Matching rule as in PROTOCOL_V2 (smallest ACC difference, ties to the smaller g, difference > 25% marked "unmatched").
- **Strength pilot**: C0, KV-P w1 and the STATIC grid in the same batch, 40 episodes, reading only ACC/CAP.
- **Signal pilot**: C0, KV-P w1, STATIC(matched), 80 episodes. The first primary comparison is KV-P w1 − STATIC(matched), on M, with no prespecified direction.

## 4. KV-PC interface contract

Same as Section 4 of PROTOCOL_V2, with one difference: the logit bias on partner keys is split by position.

- the prefill segment (position < c_start) gets log w_P;
- the C/R segment gets log w_C.
- The partner's current-tick keys remain invisible.

As w_C → 0, KV-PC reduces to KV-P w_P. GPU tests must cover this reduction and the position boundary of the split bias.

## 5. Study T3: third-person control (approved by the PI 2026-09-24)

**Question**: in v2, after reading B's private memory, A claims B's rule (K\* = KV-P w2, M +56). Is this source confusion about the memory, or is it only because B's prompt is written with "you" ("You were assigned X") and A reads "you" as itself?

**Procedure**:
- A's private prompt is unchanged.
- B's private prompt, note prompt and reflection prompt are all rewritten as a third-person record: `This is the record of participant {B}… Participant {B} was assigned the priority X and the code word "Y"…`, with no "you" anywhere in it. The information content is the same.
- A reads B's prefill with the same K\* (KV-P, w = 2).

**Signal pilot** (80 episodes, new split `v3_sig_t3`):
- Conditions: C0, K\* (second person, original), K\*-3p (third person).
- First primary comparison: K\*-3p − C0, on M (no prespecified direction).
- Descriptive: K\*-3p − K\* on M; the ACC and decomposition of both.

**Manipulation checks** (added per Codex review R2, approved by the PI 2026-09-24; fixed in writing before looking at the T3 results; script `scripts/report_t3_checks.py`):

1. **Person words in B's note.** B explains its choice in one sentence; this note is freely generated by the model, and A can also read it under KV-P.
   - In the second-person version of the v2 formal experiment, 100% of notes contain "I" and 98% contain "my/me".
   - Count the proportions of first-person words (I/me/my/mine/myself) and second-person words (you/your/yours/yourself) in the notes of both versions.
   - If more than 10% of the notes in the third-person version contain these words, it is judged "not clean".
2. **B's prefill length and number of name mentions.** The third-person version names B at least six times and writes the rule directly as "B was assigned X", which is itself a source label. In v2 study C, marking the source reduced claiming by 26.6.
3. **A's reading strength.** Compute the ratio of the ACC-rule gains of K\*-3p and K\*, and the ratio of their partner attention masses; if either differs by more than 25%, it is judged "unmatched". Also report CAP and total label probability.

**Prespecified interpretation** (replacing the original two items), decided in the following order:

1. **Note not clean**: T3 cannot answer the "person" question, whatever M is. Candidate follow-up: T3b, which also restricts the note to the third person.
2. **Reading strength unmatched**: differences in M are not attributed to wording.
3. **K\*-3p − C0 passes the signal threshold and M > 0**: even when B's memory is explicitly written as B's record, A still claims it, and the "source confusion" explanation becomes firmer. If the interval of K\*-3p − K\* lies entirely below 0, the weakened part may come from the person, the name label, or both, and these are not distinguished.
4. **Otherwise**: claiming disappears or weakens, but it cannot be told whether the cause is removing the person or adding the name label. Candidate follow-up: a third-person record that does not name the participant.

No episode is deleted post hoc (including episodes whose note contains person words). Splitting M by whether the note contains person words is descriptive only. Any follow-up study is done on a new split and must first be approved by the PI.

**T3 result** (`20260924-233653_v3_sig_t3_signal`, see `docs/results/v3/`): judged "not clean" under the rules above (13.8% of third-person notes contain first-person words). Descriptive result: claiming did not decrease (K\*-3p − C0 on M +56.1, versus +56.4 for K\*). But K\* sits in the saturated range of the strength curve, and the third-person version has higher reading strength (ACC ratio 1.41).

### T3b: a clean, unsaturated, strength-matched third-person control (approved by the PI 2026-09-24)

**Procedure**:

- **B's note forced into the third person** (partner_frame `third_strict`): B's answer starts with the fixed "Participant {B} chooses", and the model continues from there, so "I" no longer appears in the note. Everything else is the same as T3's third-person version.
- **Strength pilot S-T3b** (40 episodes, new split `v3_s_t3b`, looking only at ACC, CAP and format):
  - Conditions: C0, second-person KV-P w1, and one `third_strict` condition at each w ∈ {0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2}.
  - The selection rule is the same as for STATIC matching: among eligible `third_strict` conditions, take the one whose ACC-rule gain is closest to second-person w1 (ties to the smaller w); a gap of more than 25% is marked "unmatched".
- **Signal pilot** (80 episodes, new split `v3_sig_t3b`):
  - Conditions: C0, second-person w1, `third_strict` w\* (the weight selected in the previous step), plus controls for both persons at w2 (a replication in the saturated range, descriptive only).
  - Configs are generated mechanically by `scripts/make_v3_t3b_signal.py`.

**Manipulation checks**: same as T3. "Not clean" is judged on the `third_strict` notes (including the fixed opening); reading strength is judged on the ACC ratio and the attention-mass ratio between `third_strict` w\* and second-person w1.

**Prespecified interpretation**: the primary quantity is D = M(`third_strict`, w\*) − M(second person, w1), with a 90% interval. The margin is δ = 0.2 × [M(second person, w1) − M(C0)], taken from the same pilot. Decided in the following order:

1. Note not clean, or reading strength unmatched: as for T3.
2. **Maintained**: the lower bound of D's 90% interval is above −δ. This means that at equal reading strength, the third-person record keeps at least 80% of the second-person claiming, and claiming is not driven by person wording.
3. **Reduced**: the upper bound of D's 90% interval is below −0.3, and "maintained" does not hold. This means at least one of person wording and the name label plays a role, and the two cannot be distinguished; the candidate follow-up is a third-person record that does not name the participant (requires PI approval).
4. **Otherwise**: inconclusive; report D and its interval honestly.

Interpretation script: `scripts/report_t3_checks.py` (distinguishes T3 from T3b automatically by the study name in signal.json).

## 6. Checkpoints

Strength pilot → signal pilot → results and a "go or no-go" recommendation go to the PI for confirmation → freeze v3 → confirmatory experiment.

## 7. Confirmatory experiment (approved by the PI 2026-09-25)

**Scope**: study A′, link cut vs link kept (RF), the third-person equivalence test at the main strength (T3-K\*), and the same-weight third-person control at medium strength (T3-w1, secondary). B′ gets no confirmatory experiment; only the descriptive results of its pilot are reported.

**Sample**: new split `v3_confirm`, N = 600, A side only. A′'s signal pilot gives 600 under the N rule; the pilot SDs of the other comparisons also all reach the cap of 600.

**Conditions** (config generated mechanically by `scripts/make_v3_confirm.py` from the S-A′ point selection, i.e. `configs/v3/v3_confirm.yaml`):

- C0;
- KV-P w1;
- STATIC g0.1 (layer 24, same calibration as S-A′);
- K\* = KV-P w2, answering with the link kept (FULL);
- K\*, answering with the link cut (RF);
- strict third person (`third_strict`) w2;
- strict third person w1.

**Readout questions**: same as the signal pilot (NOW, NOW_R, START, START_R, WORD, WORD_R, ACC_RULE, ACC_WORD, CAP0, CAP1, U_CLOSED).

**Preregistered comparisons** (paired t-tests, two-sided; Holm correction within family; 95% intervals from 10,000 bootstrap draws; robustness analysis as in v2):

| Family | Comparison | Metric | Expected direction |
|---|---|---|---|
| A′ | KV-P w1 − STATIC g0.1 | M | + |
| RF | K\* link kept − K\* link cut | M | + |
| RF | K\* link cut − C0 | M_NOW | + |
| T3-w1 (secondary) | strict third person w1 − KV-P w1 | M | none prespecified |

**Equivalence test T3-K\***:

- Primary quantity: D = M(strict third person w2) − M(K\*).
- Margin: −0.2 × [M(K\*) − M(C0)], taken from the same sample.
- Decision: if the lower bound of D's 90% bootstrap interval is above the margin, it is judged "maintained": at the main strength, a clean third-person record keeps at least 80% of the claiming.

**Manipulation and engineering checks** (reported only; they do not change the tests above):

- the proportion of strict-third-person notes containing person words, cap 10%;
- the partner attention-mass ratio within each of the two same-weight pairs of conditions (w2, w1) (within ±25%), and ACC;
- each condition's CAP drop and total label probability, with thresholds as before.

If these are not met, this is flagged honestly; no episodes are deleted and the tests are not changed.

**Limits of interpretation**:

- The RF family tests whether claiming depends on reading the partner's memory at answer time; within it, "K\* link cut − C0 on M_NOW" tests for an intent shift left over from the connection period.
- T3-K\* covers only the main strength, i.e. the saturated range.
- T3-w1: at the same weight, attention is the same for both versions, while the third-person version's information is easier to read. If D < 0, it can be attributed to wording or the name label (the two are not distinguished); if D ≈ 0, no strong conclusion is drawn.

**Execution**: after freezing as `protocol-v3` (`FREEZE_protocol_v3.txt`), run with `scripts/run_chain.sh` in a new clean directory: run the tests first, and verify the freeze manifest before each stage starts (`FREEZE_VERSION=v3`).
