# Paper claims, two-model evidence, and STATIC matching

2026-10-09. Requested by the PI after reviewing the completed Llama replication.
This is an assessment of existing evidence, not a protocol amendment. No standard,
configuration, observation, or manuscript was changed and no new GPU work was run.

## Central question and levels of claim

The empirical question is whether a receiver that reads another model instance's
private internal memory keeps that content attributed to its original owner.
The task separates three quantities:

- **Access:** can A identify B's assigned rule or code word when asked about B?
- **Attribution:** does A incorrectly answer that B's original assignment was A's?
  The original assigned rule and code word have fixed correct owners.
- **Current-rule adoption:** does A report B's rule as the rule it is using now?
  Changing a current rule is not, by itself, a false historical attribution or a
  demonstrated change in a downstream decision.

Open reports are a fourth kind of evidence about what the model says happened;
they are not a direct measurement of awareness. The brain-bridging question
motivates the task. Neither model experiment establishes anything about human
brain connection, consciousness, numbers of subjects, or subjective experience.

The strongest shared empirical statement is: **under the tested fixed-memory
interface, both checkpoints can assign partner content to themselves; measured
content access alone does not predict attribution across the tested interfaces,
and source headers and readout-time connection alter particular endpoints.**

The stronger claim that a particular positional mechanism causes this behavior
remains a hypothesis. Equalizing a single access score would not isolate every
other difference between a cache interface and a residual steering direction.

## What STATIC was required to match

STATIC adds a calibrated rule-conditional direction to the receiver's hidden
states. The comparison asks whether a similar measured access gain is accompanied
by the same attribution effect as reading a partner cache. It does not match
the physical tensor norm, absolute logits, attention weight, literal information
quantity, or answer hit rate.

For each arm, define the paired episode-average gain over the same-stage C0:

`G_arm = mean[ACC_RULE_arm - ACC_RULE_C0]`,
where `ACC_RULE = z(partner's rule) - z(unused rule)`.

The frozen rule is `abs(G_STATIC-G_K1)/G_K1 <= 0.25`, with a positive K1 gain.
Equivalently, STATIC must fall between 75% and 125% of K1's gain. This is an
operational tolerance on mean scores, not a universal scientific constant or a
formal statistical equivalence test. Passing it would not prove equal content
in every sense or at every episode.

Other requirements from [PROTOCOL_V4](../../protocol/PROTOCOL_V4.md), sections 3–5:

- Fixed target K1 is KV-P w=1; K* happened to equal K1 after the separate strength
  selection. Matching cannot silently change its target after outcomes are known.
- STATIC uses independent 60-episode calibration, layer 21, raw direction, and
  the frozen 16-point gain grid from 0.005 through 1.0.
- Eligible candidates have CAP drop at most 5 percentage points, valid-label
  probability mass at least 90%, and label-mass drop at most 5 percentage points.
  These are screens, not proof of unchanged general capability.
- Among eligible points, choose the closest access gain, breaking ties toward
  lower gain. If none is close enough, retain the nearest eligible point and mark
  it unmatched. An unmatched available arm is not an unavailable arm.
- Independently validate both arms' engineering quality, K1's positive access and
  content specificity, and the access-match condition on 80 new episodes. Failure
  of the route interpretation does not stop a core-valid memory experiment.
- The formal sample rechecks access and control quality without reselection.
  Only access/CAP/format selected settings; attribution outcomes did not.

## Actual Llama mismatch and transparent sensitivity

The same frozen STATIC g=0.7 was used in all three rows. Gains are nats.

| Stage | N | K1 gain | STATIC gain | STATIC/K1 | Relative gap | Allowed STATIC interval at 25% |
|---|---:|---:|---:|---:|---:|---|
| Matching pilot | 40 | 2.800295 | 0.345588 | 12.341% | 87.659% | [2.100221, 3.500369] |
| Independent validity | 80 | 2.269904 | 0.391530 | 17.249% | 82.751% | [1.702428, 2.837380] |
| Formal | 600 | 2.489639 | 0.420604 | 16.894% | 83.106% | [1.867229, 3.112049] |

The formal access answer rates also differ: 43.417% for K1, 17.083% for STATIC,
and 14.417% for C0. Those rates are informative descriptions, not the matching
criterion. The ratio above refers to measured logit gain, not an amount of
information flowing through a channel.

The following is an explicitly **post hoc threshold sensitivity calculation**,
not a new validity result or a replacement for the frozen 25% rule.

| Relative tolerance | Matching pilot | Independent validity | Formal |
|---|---|---|---|
| 25% | fail | fail | fail |
| 50% | fail | fail | fail |
| 75% | fail | fail | fail |
| 85% | fail | numerical pass | numerical pass |
| 90% | numerical pass | numerical pass | numerical pass |

All three stages would require at least 87.659% tolerance. At 90%, a positive
STATIC gain only one tenth of the target can qualify numerically. Calling that
similar strength would not answer the intended equal-access question.

This is not mainly an engineering-screen problem. Fifteen of the 16 tested
STATIC gains were eligible. The remaining point, g=1.0, had zero CAP drop and
absolute label mass 93.993%, but a label-mass drop of 5.817 percentage points,
exceeding the allowed 5. Its gain was only 0.387820 versus K1's 2.800295: a gap
of 86.151%. Even admitting it would not solve matching. Relaxing CAP alone
changes nothing about the best candidate in the tested grid.

The matching-pilot K1 itself had CAP drop 5.625 points. The fixed-target matching
step selects an eligible STATIC candidate; K1 was rechecked in the independent
validity sample, where its CAP drop was 3.4375 points, its access lower bound was
positive, and its content check passed. In the formal sample K1's CAP drop is
exactly 5 points. This variability should be reported, not used to discard a
sample or redefine a gate after the fact.

It is legitimate to discuss different tolerances transparently or to specify
a new prospective study. Such a change does not retroactively turn this frozen
run into a successful matched comparison. Its K1-minus-STATIC difference remains
an estimable result in the five-test family; the unsupported part is the
equal-access interpretation, not the existence of the condition difference.

Sources: pinned [matching](../../../configs/v4/artifacts/match.json) and
[validity](../../../configs/v4/artifacts/validity.json) artifacts, and the
[formal report](report.md). All 16 pilot candidates are retained in the artifacts.

## Why the Qwen match is different

Qwen's earlier v2 comparison at KV w2 versus STATIC g=0.4 was also unmatched
(formal gains about 19.055 and 13.288). It is not the evidence that supports the
paper's matched-access claim. The later, separate v3 A-prime study targeted w1.

For that study, the selection pilot had gains 4.2148 versus 3.5868 (about 14.9%
apart); its new signal sample also remained within the 25% rule. In the 600-episode
formal sample, the gains were 4.081 versus 4.179 (about 2.4% apart). Assigned-rule
partner choices were 52.3% under KV and 0% under STATIC; the prespecified M
contrast was +33.432 [31.563, 35.283]. Thus Qwen supports the selected interventions'
difference at closely matched mean access gain. It still does not isolate signal
type from injection timing, position, content representation, or every other
interface property. Llama has not replicated this particular matched comparison.

Sources: [Qwen matching pilot](../v3/strength_pilot_s_static_a.md),
[signal sample](../v3/signal_pilot_aprime.md), [v3 formal](../v3/confirmatory_v3.md),
and [v2 formal](../v2/confirmatory_v2_main.md).

## Claim-by-claim comparison

Q2 and Q3 below are separate 600-episode Qwen confirmatory samples, not interchangeable
denominators. Llama L4 is the new 600-episode formal sample. Choice rates are
descriptive; the prespecified tests are paired episode-level logit contrasts.
Logit magnitudes are not compared as a calibrated scale across checkpoints.

| Claim or question | Qwen evidence | Llama evidence and current scope |
|---|---|---|
| Partner content changes answers about the receiver's original assignment. | Q2 w2-C0 primary M contrast +55.834 [54.989,56.631]; Q2 assigned-rule choices 95.8%. Q3 w2 gives 97.1% and w1 52.3%. | L4 w1 gives 51.333% versus 0%, primary M +10.823 [10.375,11.253]. Core attribution effect supported. Similar w1 rates are descriptive, not a cross-model equivalence test. |
| The partner's code word is also attributed to the receiver. | Q3 w2 WORD partner choices 77.5%; related logit effects are positive. | L4 w1 WORD choices 48.75% versus 0%; the prespecified M_WORD contrast is positive. Supported at the tested settings, not necessarily equally strong. |
| Access and attribution are separable. | Q2 TAG access 95.2% with 0% assigned claiming; KV w2 access 70.1% with 95.8% claiming. | TAG access 86.583% with 0% assigned claiming; KV access 43.417% with 51.333% claiming. The same qualitative dissociation is supported. This is not an equal-access route isolation. |
| At similar mean access gain, STATIC and KV yield different attribution. | Q3 A-prime has an actual close match, with 52.3% versus 0% claiming. Earlier Q2 A_K was unmatched. | Available numerical contrast is positive, but all matching/validity stages fail the match. Equal-access interpretation unvalidated. |
| Explicit text-source headers reduce current-rule adoption. | Q2 UNTAG 42.6% versus TAG 0.1%, prespecified M_NOW contrast positive. | UNTAG 42.167% versus TAG 2.250%, prespecified M_NOW +3.725 [3.367,4.082]. Supported for this header intervention. Neither is a downstream decision measurement. |
| Untagged text also changes original-assignment choices. | Q2 UNTAG assigned claiming 14.6%. | Both L4 text conditions have 0% assigned claiming. This behavioral extension is not reproduced, although current-rule adoption is. |
| Names/strict third-person wording inside memory prevent claiming. | Q3 strict-third-person w2 retains the effect by its frozen retention rule (97.2% versus 97.1%). At w1 claiming is 47.8% versus 52.3%, with a negative secondary contrast. See qualifications below. | Not tested. Llama does not newly rule out a grammatical-person explanation. |
| Assigned-rule claiming depends strongly on keeping the link during questioning. | Q3 w2: 97.1% to 1.3% after cutting; prespecified FULL-RF M +54.775 [53.987,55.525]. | L4 w1: 51.333% to 0%; primary FULL-RF M +10.893 [10.455,11.324]. Supported from the same saved reflection state. |
| Some current-rule influence survives the cut. | Q3 RF current choices 17.5%; prespecified RF-C0 M_NOW +13.342 [12.311,14.414]. | RF current choices 7.083%; secondary M_NOW +1.917 [1.631,2.214]. Supported qualitatively. |
| Positive adjusted code-word residue survives the cut. | Q3 RF WORD choices 17.5%; descriptive M_WORD +10.490 [8.99,12.03]. | RF WORD choices 1%, but prespecified adjusted M_WORD -0.330 [-0.495,-0.162]. Positive adjusted residue does not replicate. Raw self preference still shifts slightly positive; complete erasure is not established. |
| The residue is caused by what A wrote into its reflection. | Q3 post-treatment grouping: 63.6% word choices where the word was mentioned (165 episodes), 0% where absent (435). Association, not a causal intervention on reflection text. | No such mechanism test. The existing code-word result should not be converted into one. |
| The model claims foreign content while reporting nothing unusual. | In post hoc semantic coding of 300 Qwen w2 reports, 296 claim the partner word, 250 both claim and deny anything unusual, none attributes it to someone else. Baseline denial was already frequent (287/300). | No open reports or U_CLOSED collected. Untested, not a failed replication. No claim about internal awareness follows in either case. |
| Fixed two-way memory reading swaps the copies' assignments. | N80 pilot: 94.4% swaps versus 94.5% predicted from marginal choice rates. Two one-way effects; not a test of fusion. | No two-way condition. Untested. |
| A responsive live loop adds shared-assignment behavior. | N80 pilot: assigned-rule excess-agreement difference +6.7 points [2.6,10.9], below the 10-point advancement criterion; current-rule difference +12.1 [7.4,16.5]. Exploratory; the difference between endpoints was not tested. | No live-loop condition. Untested. The responsiveness question remains unsettled, while responsiveness is unnecessary for the demonstrated fixed-memory effect. |
| Overlapping memory positions cause a default-to-self mechanism. | A post hoc explanation compatible with several controls, but no cache-relocation/layout causal test. | Same arrangement has an attribution effect; no relocation test. Mechanism remains hypothetical in both checkpoints. |

### Qualifications to the wording and other controls

The final Q3 third-person retention test and the earlier T3b pilot have different
frozen contracts. Final same-weight w2 retention used clean notes and similar
attention mass, with ACC reported; it should not be retroactively invalidated
using T3b's matching criterion. Its M difference was -0.714 with 90% interval
[-1.262,-0.184], above the -11.330 retention bound. It supports persistence at
that saturated setting, not complete invariance to wording.

The final w1 secondary contrast was -3.211 [-4.860,-1.563]. Third-person access
increased substantially, so wording, name frequency and access were not cleanly
separated. The earlier clean, lower-weight T3b pilot (third-person w0.6 versus
original w1) had a large negative M contrast but failed its ACC ratio 1.42 and
attention ratio 0.74 checks. Its generic statistical GO flag does not override
the explicit unmatched verdict. See [final v3 protocol](../../protocol/PROTOCOL_V3.md),
[T3b checks](../v3/t3b_checks.md), and [v3 report](../v3/confirmatory_v3.md).

Qwen also has a separate balanced-rehearsal confirmatory control, supporting
claiming despite that change; Llama does not. Qwen's dose curve and sharp individual
choices are descriptive; Llama formally ran only the selected weight, so neither
the full curve nor saturation was replicated. Llama w2 and w3 failed capability
screening before attribution selection. The nominal w1 correspondence does not
show equal attention mass or equal effective intervention strength across models.

Two source-header qualifications remain: Qwen's “your own earlier thoughts”
header reduced rather than increased adoption relative to no header, contrary
to the original expectation; its stranger versus named-partner contrast was not
significant, which is not proof of exact equivalence. Neither extra header was
tested in Llama. These results limit a simplistic account in which every apparent
self label necessarily increases adoption.

The content-counterfactual checks in both models establish donor-sensitive
ACC_RULE/ACC_WORD access. They should not be relabeled as direct causal tests
of ownership, cache position, or conscious source monitoring.

## Control quality and generalization

For Llama, C0 CAP is 94.75%, KV 89.75% (exactly a 5-point drop), and CF 89.667%
(5.083-point drop). The independent pre-formal core gate passed. Report the
formal quality drift; do not call capability unaffected or impose a new exclusion
rule. Qwen's selected formal KV conditions had smaller reported CAP drops (about
1 point at w1 and 2.1 at w2 in Q3). Neither finite common-knowledge screen proves
general intelligence or all unrelated functions remain intact.

Both models support a differential attribution effect, not a statement that every
error is confined to self-attribution. Llama's KV WORD_R has 1.833% partner choices,
even though START_R and NOW_R have none. The Robin subtraction and raw components
must remain visible. The weaker residual-interface findings, failed pilots and
unmatched comparisons should remain in the record rather than be folded into a
blanket claim about every internal-state channel.

Two checkpoints across families improve empirical scope beyond the original
single checkpoint. They share one artificial task and deliberately overlapping
memory arrangement. No episode pooling, raw-logit cross-model ranking, universal
LLM claim, or extrapolation to human experience is justified by this addition.

## Recommended interpretation and possible next work

Keep the current frozen result as unmatched. Organize the revised empirical claim
around the attribution effect, access/attribution dissociation, source headers,
and selective reversibility, while identifying Qwen-only findings and Llama's
contrary secondary result. Do not count five significant primary condition
differences as five validated mechanisms.

If a Llama matched comparison is essential, it needs a new prospective study with
a justified finite access-only search, new independent validation and appropriate
fresh paired formal observations for changed arms. Possible design choices include
a different calibrated STATIC layer/construction or a weaker KV target. These
change the tested question and require a new protocol decision and budget before
execution. The w0.5 strength pilot's access gain of 0.2553 is a clue, not proof
of a match to STATIC from a different split; it also failed the current strong-
interface hit-rate criteria. A new weak-target comparison need not replace the
completed strong-interface results.

If the scientific priority is the positional explanation, directly manipulating
cache positions/layout while checking access and capability would address it more
directly than relabeling STATIC. That is a proposal, not a demonstrated experiment
or an authorized GPU launch. No new experiment is required merely to report the
existing supported effects and honest boundaries.

Further evidence: [formal report](report.md),
[independent statistics](../../reviews/v4_statistics_20261009.md),
[cross-model interpretation review](../../reviews/v4_interpretation_20261009.md),
[current manuscript results](../../../paper/sections/results.tex), and
[mechanism and limitations](../../../paper/sections/account_and_discussion.tex).
