# Expected and unexpected findings across the connection experiments

Assessment date: 22 October 2026. Coverage: completed V1–V5 studies and continuations, their pilots and descriptive extensions, and the V6 engineering observations and native diagnostics through 19 October. The subsequent research-reset proposals have no new model outcomes.

The strongest established contribution is a set of dissociations between reading foreign content, assigning that content to a record or person, and reporting a current rule. The most consequential corrective result is that conflicting third-party records are vulnerable too. The most promising recent anomaly is preserved own-goal naming alongside partner-sensitive own-rule answers, but that evidence remains confined to two exposed layouts. Reliable useful reciprocal interaction has not been established.

## How the classifications are made

These are retrospective judgments of explanatory value, not new statistical tests or decisions to change the research program. They are not claims of novelty against the entire literature. An effect can be well established and unsurprising; a surprising observation can have weak evidential support.

| Classification | Meaning |
|---|---|
| Expected or low discrimination | A simple account such as stronger input influence, interference, source-cued text interpretation or numerical sensitivity already accommodates the observation. The result remains useful as a control or feasibility check. This is the intended sense of “trivial.” |
| Nontrivial | A controlled contrast or dissociation rules out, or materially constrains, a simpler explanation of this project's observations. It need not be surprising or self-specific. |
| Unexpected against a written prediction | A direction was specified before collection and the result went the other way. |
| Unexpected against a simple account | The observation challenges an explicit intuitive explanation, but no prior directional prediction is claimed. |
| Unresolved | The target explanation remains unidentified because of an unsuccessful manipulation, unmatched conditions, limited scope or insufficient replication. This is not a synonym for “trivial.” |

Five simple accounts provide useful reference points: all foreign content merely becomes more salient; attribution errors increase only with access; errors are just second-person wording or unequal rehearsal; a lasting original-record overwrite occurs; and a responsive partner is necessary for the effect. A sixth, broader conflicting-record account becomes especially important after V5. None of these accounts is identified merely by naming it.

The principal attribution score M subtracts the Robin-question partner-versus-Robin logit margin from the self-question partner-versus-own margin. This subtraction is a control, not a guarantee that every general-interference explanation has been removed. ACC is an access logit margin; it is not accuracy. M_NOW measures a reported current rule, not enacted goal control. Percentages below are actual choices where stated. Formal inference uses episodes, with orderings and sides treated as repeated observations.

STATIC is a fixed calibration-averaged rule direction injected into the residual stream. The principal KV-P donor memory is structured, context-derived, **fixed prefill memory**. V1 online residual signals, V2/V3 live caches and V6 generated windows are different interventions. Fixed memory versus STATIC does not test whether a live partner must respond. Protocol definitions: [V1](../protocol/EXPERIMENT_DESIGN.md), [V2](../protocol/PROTOCOL_V2.md), [V3](../protocol/PROTOCOL_V3.md).

## Findings with the greatest established explanatory value

### Content access and attribution can separate

In Qwen V3 A′, KV-P w1 and STATIC g0.1 have closely matched **mean rule-access gains**, 4.081 and 4.179 nats. Nevertheless, original-assignment donor choices are 52.3% versus 0%, and the prespecified M difference is +33.432 [31.563, 35.283], N = 600. This constrains an explanation in which that mean access score alone determines attribution. It does not match every episode, the entire representation, WORD access, attention operation or timing. [Formal V3](v3/confirmatory_v3.md), [choice distributions](story_checks.md).

The text comparisons show a complementary ordering. Qwen V2 tagged text gives 95.2% donor-rule access and 0% original-assignment claiming, versus 70.1% access and 95.8% claiming with KV w2. Llama V4 gives 86.583% versus 43.417% access, but 0% versus 51.333% claiming. These are consistent descriptive dissociations across two checkpoints, not equal-access experiments. [Qwen choices](story_checks.md), [Llama V4](v4/report.md).

The new Llama STATIC continuation strengthens the descriptive dissociation: STATIC has **higher donor-rule accuracy** than KV, 47.333% versus 42.083%, but far less original-assignment claiming, 0.583% versus 49.917%. Its prespecified access-gain match fails in the formal sample, however: the gap is 40.125%, outside 25%. Thus Qwen supplies the successful close-mean-gain comparison; Llama supplies another dissociation and an unsuccessful formal match. [Llama STATIC](v5/static_post_collection_20261012.md).

**Judgment:** high-value nontrivial evidence for separable access and attribution under the tested interfaces. It does not establish a categorical difference from all activation steering.

### Original assignment and reported current rule recover differently after disconnection

Qwen V3 branches from the same connected reflection state. Cutting the link only for questioning reduces original-assignment donor choices from 97.1% to 1.3%, while current-rule donor choices fall from 94.9% to 17.5%. FULL−RF M is +54.775 [53.987, 55.525]; RF−C0 M_NOW is +13.342 [12.311, 14.414], N = 600. [Formal V3](v3/confirmatory_v3.md), [choices](story_checks.md).

Llama V4 reproduces the qualitative assigned/current distinction: original claiming 51.333% to 0%, current-rule claiming 51.500% to 7.083%. But its adjusted residual WORD contrast is **negative**, −0.330 [−0.495, −0.162], unlike Qwen's positive descriptive WORD residue. A small donor-word choice rate of 1% does not reverse that metric's sign. [V4](v4/report.md).

**Judgment:** nontrivial temporal and question-specific dissociation. It challenges simple durable replacement of the original assignment. The generic fact that removing an input weakens its effect is expected; the different recovery profiles carry the additional information. It does not prove multiple memory stores or durable goal change.

### Wording and rehearsal controls rule out two complete explanations

At Qwen w2, strict third-person donor records retain original-assignment claiming: 97.2% versus 97.1%. The frozen retention test passes: M difference −0.714, 90% interval [−1.262, −0.184], above the −11.330 bound. The medium-weight result is less invariant: M decreases by 3.211 nats and claiming falls from 52.3% to 47.8%. Access rises substantially under third-person wording. [V3](v3/confirmatory_v3.md), [final protocol contract](../protocol/PROTOCOL_V3.md).

Separately, rehearsal-balanced Qwen materials retain a large KV effect, M +52.544 [51.589, 53.461], N = 600. The residual interface shifts the self and Robin components by about +5.9 each, leaving M −0.051 [−0.151, 0.050]. [Balanced V2](v2/confirmatory_v2_bal.md).

**Judgment:** useful nontrivial controls. Neither second-person ambiguity nor unequal rehearsal is a sufficient account of the large KV effect. These controls do not show wording is irrelevant, prove self-specificity, or explain how the attribution error occurs.

### Conflicting third-party records overturn a self-exclusive interpretation

V5 holds the receiver's original Robin record fixed and changes only Robin's rule and word in the donor card, conditional on the already-present self conflict. Receiver-original Robin rule errors increase from 0% to **49.92% in Qwen** and from 0% to **48.50% in Llama**. Rule errors are donor-field replacements. The prespecified rule logit contrasts are +29.554 [28.175, 30.910] and +10.859 [10.408, 11.305], respectively; both studies have N = 600. Robin-word conflicts also produce large shifts and mistakes. [V5 provenance report](v5/provenance_post_collection_20261012.md).

Qwen follows the original V5 protocol. Llama is a separately frozen continuation after the original capability gate failed; those statuses and testing families remain distinct. This is no balanced self-versus-Robin vulnerability comparison, so it cannot establish equal vulnerability either.

**Judgment:** one of the project's most informative findings, and corrective evidence against the earlier self-exclusive story. It supports a broader record-provenance problem. Given two conflicting records, interference itself is not intrinsically surprising; what matters is the controlled field change and the constraint it imposes on our prior interpretation.

## Unexpected results and how much weight they deserve

### A self label reduces adoption rather than increasing it

V2 explicitly predicted that labeling the text “your own earlier thoughts” would increase current-rule adoption relative to untagged text. It instead reduces M_NOW by **19.471 nats**, 95% interval [−21.517, −17.359], N = 600. Current-rule donor choices fall from 42.6% to 10.6%. This is the cleanest example of a result opposite to a written directional prediction. [Prediction](../protocol/PROTOCOL_V2.md), [formal result](v2/confirmatory_v2_main.md), [choices](story_checks.md).

The foreign content is held constant, but the header is a wording package: “own,” “earlier” and the explicit framing change together. Context checking, temporal interpretation or other prompt effects remain possible. The result refutes a simple monotonic “more self wording means more adoption” account; it does not identify a self-verification mechanism.

### More explicit source wording can reduce one error while increasing total error

In ordinary Qwen V5 KV, naming the participant and original private record reduces donor-own rule choices from 50.58% to 18.17%. However, correct answers also fall, from 49.42% to **18.92%**; 55.17% instead choose Robin's rule. The WORD counterpart also worsens in accuracy. Llama shows the same broad failure of source qualification to restore accuracy, with a smaller redistribution. [V5 provenance](v5/provenance_post_collection_20261012.md).

**Judgment:** a strong descriptive surprise against “clearer source wording fixes provenance.” The prespecified old-versus-qualified two-candidate interactions are nonsignificant after correction; they are not equivalence tests and do not capture the complete four-option redistribution. This result is particularly valuable because looking only at donor-choice reduction would suggest a repair where total errors actually increase.

### Correct goal names coexist with incorrect and partner-sensitive rule answers

The native V6 channel diagnostic contains two fresh three-round episodes. Across LIVE and LIVE_SELF_REPORT, all 24 own-goal labels are correct, but nine of 24 own-rule answers are wrong; all nine match the partner's current assignment rule. Both OFF variants have 24/24 correct own-rule answers. [Channel diagnostic](../reviews/v6_channel_diagnostic_results_20261019.md).

The subsequent intervention reuses the two initial layouts, holds the recipient and world fixed, and varies the partner assignment. Own-rule correctness is **12/12, 10/12, 9/12 and 7/12** for disconnected/disconnected, disconnected/connected, connected/disconnected and connected/connected work/readout. All 48 own-goal reports remain correct. Partner-matching errors number 0, 0, 1 and 3; other errors select a third rule. One recipient's rule never changes. [Fixed-scene intervention](../reviews/v6_goal_stage_results_20261019.md).

**Judgment:** the most interesting recent exploratory anomaly. A label can remain stable while the rule reported under that label changes with another agent's assignment. The controlled follow-up narrows the original “all errors copy the partner” impression rather than confirming it wholesale. Public rule mappings, generated-history changes and attention interference remain explanations. The fixed-scene action probes are discarded; there is no demonstrated takeover of enacted goals, accurate private-goal retrieval or causal self-monitoring. Two layouts and 240 readouts do not constitute 240 independent episodes.

The stage split is independently informative: connected work can affect a later disconnected readout, while readout-only connection can itself create errors. Thus a connected question is not a transparent window into a fixed prior belief. Immediate retained influence does not establish lasting memory or a requirement for live responsiveness.

### Information timing changes apparent task competence

V6 fresh immediate-answer tests provide both required facts yet obtain only 19/64, 20/64 and 29/64 correct reference answers under the original and two clearer wordings. Rule-pair retrieval is 59/64 and supplied-button mapping 63/64, showing that separate component success does not guarantee correct composition. [Clarity result](../reviews/v6_clarity_short_result_and_hold_20261019.md), [factor diagnostic](../reviews/v6_action_factor_findings_20261019.md).

With identical initial facts, work instruction and final question, adding 64 native generated work tokens changes accuracy from **32/64 to 63/64** on exposed materials, then from **17/32 to 32/32** on prospectively fixed fresh codebooks. [Closure](../reviews/v6_action_diagnostic_closure_20261019.md).

**Judgment:** useful nontrivial local diagnosis, unexpected relative to the inference that this model simply cannot apply the task. The general possibility that extra computation helps is unsurprising. The result concerns an oracle-information diagnostic; it does not establish that the latent channel supplies usable information or that reciprocity works. Correct generated notes followed by wrong actual answer tokens occur in this diagnostic and the later text control, so notes cannot substitute for scored actions.

### Coupling can matter in a case without producing reliable cooperation

An earlier V6 engineering episode has a late checkpoint with a correct changed-world forward-and-return sequence and directional-cut sensitivity. Its unflipped return is wrong, other actions fail, both early chains fail, and the other episode's late correct target actions do not adapt to the intervention. The optimized backend remains scientifically unadmitted. [Complete engineering walkthrough](../reviews/v6_two_episode_walkthrough_20261018.md).

In the subsequent two fresh native cases, case 1 has a correct forward switch that disappears with either directional cut or matched return replay, but both return actions are wrong. Case 2 lacks the correct LIVE forward switch; its replay condition actually has the correct forward switch. Neither native case completes the intended correct forward-and-return chain. [Native pilot](../reviews/v6_small_interaction_results_20261019.md).

**Judgment:** nontrivial local causal clues, weak evidence for a general reciprocal function. It is inaccurate both to say that feedback never mattered and to claim that reliable useful reciprocity has been demonstrated. Removing a path changes the full evolving signal; semantic feedback and a general interference effect are not fully separated.

### Open reports do not reliably announce the attribution error

Post hoc semantic coding of 300 Qwen w2 reports finds 296 claiming the donor word as their own, including 250 also denying anything unusual. Denial was already common at baseline, 287/300. Closed reports of “two/partly shared” decrease at strong KV despite increasing foreign-content claiming. [Story checks and coding provenance](story_checks.md).

**Judgment:** a useful behavioral mismatch against the expectation that a report will announce the intervention. It is weaker explanatory evidence than the controlled dissociations: no awareness ground truth or calibrated self-monitoring task was measured, and baseline denial is high. Llama did not receive these open/closed report experiments.

## Coverage of the full experimental program

The table distinguishes supporting controls and failed studies from the findings above. Formal N refers to episodes; exploratory denominators often count repeated cases, questions or sides. Separate cohorts are never pooled here.

### V1 baseline and online residual bridge

| Experiment or result | Observation and evidential status | Assessment |
|---|---|---|
| G1 original task and capability screen | Original-assignment/current-rule/word readouts pass; behavior endpoints 0.66/0.38 and arithmetic CAP 0.354 fail. BEH is retired and the final CAP bank contains 18 general-knowledge items. Final materials pass. | Important feasibility boundary. Later reported rule adoption cannot be relabeled as a validated downstream decision effect. |
| Calibration and Pilot A/B | Layer 24 raw chosen; formal gain 0.2; STATIC 0.1 is unmatched. | Engineering/selection evidence, not an attribution discovery. |
| Pilot C and formal content counterfactual | Pilot rule passes; pilot word lower bound is negative. Formal diagnostic subset later has positive rule and word lower bounds. | Content sensitivity is necessary validation, not evidence of self-boundary change. Preserve both stages. |
| TWO versus ONE, formal N = 300 | M −0.073, 95% interval approximately [−0.214, +0.065]. | Informative bounded negative result for this weak interface. Neither zero feedback in general nor a proven “too weak” explanation follows. |
| ONE versus STATIC, formal N = 300 | M +0.18 [−0.02, +0.40], unmatched. | Unresolved live-signal versus direction comparison. |
| ONE versus tagged text, formal N = 300 | M +0.85 [+0.54, +1.20], largely because tagged text lowers M. | A real contrast with limited discrimination; not positive evidence of original-assignment takeover by the residual bridge. |
| Dose, raw components and residual ownership | Access gain grows approximately +0.16 to +0.83; self/Robin preferences both shift; original-assignment answers remain correct. | Nontrivial constraint on equating any content transfer with ownership change, but small access limits its reach. |
| Untagged versus tagged text | Untagged current-rule donor choices about 46%, original-assignment about 15%; tagged text supports access with little claiming. | Source-cue dependence is fairly expected; the access/attribution distinction is more informative. |
| FULL/RF/RO | Cutting during questioning removes most residual effects; readout-only linking reproduces much of FULL. | Primarily online readout influence at these settings; expected removal effect with useful temporal localization. |
| SCRAM, MISMATCH, layers and support masks | Rotation attenuates transfer; mismatch lacks a clear attribution contrast; L24 is strongest among tested selected layer settings. Small support masks, including energy-matched k = 128, transfer little; k = 1024/2560 support more. | Local representation/interface findings. They do not identify a universal minimum dimension, a self layer, or a reciprocal mechanism. |
| State cosine and self-report | TWO increases A/B cosine more than ONE; closed-report patterns do not track TWO or M monotonically. | Vector convergence under mixing is low discrimination. Self-report discrepancy is descriptive, not evidence about numbers of subjects. |

Sources: [V1 protocol](../protocol/EXPERIMENT_DESIGN.md), [full formal and extension tables](formal_report.md), [exploratory decomposition](formal_exploratory.md), [V1–V3 run inventory](ALL_RESULTS.md).

### V2 stronger channels and source labels

| Experiment or result | Observation and evidential status | Assessment |
|---|---|---|
| First KV strength search | KV-ALL w1 gives access +8.9 but CAP loss 0.19; strongest eligible point is weak. | Stronger interference can damage performance: expected, consequential constraint. Pre-review implementation retained separately. |
| Second strength search | Fixed KV-P w2 reaches +17.6 access and 65% donor-rule accuracy with CAP loss 0.013 in selection. | Useful channel feasibility; fixed-memory access outperforms tested live ranges under the screen. Not evidence of an advantage from responsiveness. |
| Residual matched STATIC and signal A_R | Low STATIC gain matches residual access; signal contrast about −0.18 and no-go. | Failed advancement, not a confirmed route distinction or exact equivalence. |
| Strong KV study D | Formal N = 600 M +55.834; original-assignment donor choices 95.8%, code word 77.3%. | Robust specific attribution phenomenon. Magnitude alone is weaker mechanistic evidence than the controlled dissociations. Fixed memory suffices. |
| KV content counterfactual | Formal diagnostic N = 60 rule +38.775 and word +35.578, positive lower bounds. | Validates donor-sensitive access. It is not the same test as changing ownership or cache positions. |
| A_K versus STATIC 0.4 | Formal M +60.287, but access gains 19.055 versus13.288. | Observed difference; unmatched mechanism claim unresolved. V3 A′ supplies the stronger comparison. |
| C untagged versus named source | Formal M_NOW +26.634; current-rule donor choices 42.6% versus0.1%. | Reliable but broadly expected source-label effect; later replicated qualitatively in Llama. |
| C self versus untagged | Formal M_NOW −19.471; choices 10.6% versus 42.6%. | Unexpected against the written positive prediction; high-priority anomaly. |
| C stranger versus named source | M_NOW −0.020 [−0.268, +0.245]. | No detected contrast; insufficient for equivalence or a claim that social identity never matters. |
| B_R and B_K live return-path signal studies | Residual contrast about −0.24, no-go; live KV contrast about −4.8, opposite to expected direction, with large CAP losses. | Prespecified expectation fails. The KV reversal is not clean evidence of protective reciprocity because capability and pair dynamics confound it. |
| E rehearsal balancing | Initial balanced material fails its rehearsal check; revised material passes. Formal KV M +52.544; residual M approximately 0. | Nontrivial robustness and component control, not evidence of self-exclusive vulnerability. |
| KV dose and open reports | M rises steeply between w0.5 and 1 and approaches saturation by w2; donor-word reports increase. Reports rarely identify the donor and often deny unusual changes. | Dose monotonicity/saturation alone are expected. Reporting mismatch is descriptively interesting, with the limits above. No phase-transition claim. |
| Exploratory paired fixed/live outcomes | Fixed memories mostly swap assignments; live caches produce more same-rule outcomes with capability costs. | Generates a testable question, not a finding of fusion or useful cooperation. |

Sources: [V2 index and all pilot links](v2/README.md), [formal C/D/A_K](v2/confirmatory_v2_main.md), [balanced study](v2/confirmatory_v2_bal.md), [dose extension](v2/dose_v2_ext.md), [exploratory B](v2/diag_b_exploratory.md).

### V3 matched comparison and redesigned feedback controls

| Experiment or result | Observation and evidential status | Assessment |
|---|---|---|
| A′ selection, signal and formal N = 600 | Mean formal access gains 4.081/4.179; M difference +33.432; claiming 52.3%/0%. | One of the strongest nontrivial results; the match concerns this scalar mean. |
| B′ strength search | Selected weakest live gains; stronger loops fail CAP bounds. | Expected engineering tradeoff constraining the range of the scientific test. |
| Fixed two-way memory, N = 80 | Swaps 94.4%, approximately 94.5% expected from marginal adoption rates. | Visually striking but low discrimination: consistent with two one-way adoption effects. |
| B′ live-loop versus no-loop, N = 80 | Original-assignment excess agreement +6.7 pp, 90% CI [2.6, 10.9], below the 10 pp advancement rule; current-rule excess +12.1 pp [7.4, 16.5]. PC family near zero. | Nontrivial exploratory feedback clue plus a failed primary gate. Not “nothing happened,” not a formal success. Endpoint differences were not themselves tested. |
| T3 pilot | 13.8% of supposedly third-person notes leak person words; fails clean-material rule. | Unresolved control, even though descriptive claiming remains large. |
| T3b pilot | Clean notes, but ACC ratio 1.42 and attention ratio 0.74 fail matching; M difference −26.849. | Unresolved wording mechanism; a favorable generic signal flag does not override failed manipulation checks. |
| Final strict-third-person N = 600 | Retention at w2 passes; w1 has a smaller significant effect, with much greater access. | Nontrivial against a purely second-person account, not full wording invariance. Final contract differs from T3b. |
| FULL versus RF, N = 600 | Original-assignment claiming nearly disappears; current-rule residue remains. | High-value dissociation with later partial replication. |
| Reflection and residual WORD grouping | RF word claiming 63.6% when the word was mentioned, 0% when absent. | Post-treatment association, not evidence that writing the word caused the residue. |
| Individual decisions and cross-field consistency | At w1, 97.8% of START answers are decisive, yet rule and code word come from the same side only 57.1%; 11.7% of episodes switch START side across option orderings. | Useful constraint on a coherent whole-identity replacement story. Sharp individual probabilities do not establish a phase transition. |
| Same self/donor answer under strict third person | At w1, 90.8% answer both questions with the same rule; correct separation only 7.3%. | Descriptive record-binding failure compatible with broader interference; not two verified representations merging. |

Sources: [V3 index](v3/README.md), [B′ complete pilot](v3/signal_pilot_bprime.md), [T3 checks](v3/t3_checks.md), [T3b checks](v3/t3b_checks.md), [formal V3](v3/confirmatory_v3.md), [post hoc story checks](story_checks.md).

### V4 Llama replication

| Experiment or result | Observation and evidential status | Assessment |
|---|---|---|
| Fixed memory versus C0, N = 600 | M +10.823; original-rule/current-rule/word donor choices 51.333%/51.500%/48.750%. | Extends the core phenomenon to a second checkpoint. Raw nats are not a calibrated cross-model scale. |
| Source-tag and access controls | Tagged access 86.583%, claiming 0%; untagged current adoption 42.167% versus tagged 2.250%. | Replicates qualitative dissociation and source-header dependence. |
| Untagged original assignment | Both text arms have 0% original-assignment donor choices. | Qwen's untagged-text original-assignment behavioral effect does not replicate here. |
| Link cut | Assigned claiming becomes 0%; current-rule 7.083%; adjusted WORD residue negative. | Replicated selective recovery plus an important contrary WORD boundary. |
| STATIC comparison | M difference+10.451, but formal access-gain gap 83.106%; matching/route-validity failed. | A valid condition contrast, not matched-access replication. |
| Content and capability | Rule/word counterfactuals positive. Core pre-formal gate passed; formal KV CAP loss exactly 5 pp and CF 5.083 pp. | Donor-sensitive access with a material quality limit. No blanket “capability unaffected” claim. |
| Untested controls | No Llama third-person, balanced-rehearsal, open/closed report, full dose curve or live-loop replication. | Unmeasured; neither positive nor failed replications. |

Sources: [V4 report](v4/report.md), [matching and cross-model assessment](v4/claims_and_matching_review.md).

### V5 provenance and Llama STATIC continuation

| Experiment or result | Observation and evidential status | Assessment |
|---|---|---|
| Third-party conflicting rule/word | Approximately 50 pp receiver-original Robin rule errors; strong word errors too, N = 600 per separate study. | High-value correction to a self-exclusive explanation. |
| Source-qualified self questions | Qwen donor choices decrease but accuracy deteriorates to 18.92% for RULE; Robin dominates. Llama also fails to recover overall accuracy. | Unexpected descriptive distribution change, not a wording fix. |
| Prespecified qualification interactions | Neither study has a corrected significant old-versus-qualified interaction. | No detected two-candidate interaction; not equivalence of full answers. |
| Field-specific access | Qwen donor-own WORD gain remains negative, while donor-Robin WORD counterfactual sensitivity is strongly positive. | Nontrivial measurement boundary: rule access or one word field cannot certify another. |
| Admission history | Qwen passes original V5. Llama provenance original CAP gate fails; continuation prospectively admits the named exception. Original STATIC validity also fails CAP. | Continuations are usable under their own amended contracts; original failures remain failures. |
| New Llama STATIC, N = 600 | KV claims 49.917% versus STATIC 0.583%; STATIC has higher donor-rule accuracy. Formal mean-gain gap 40.125%, despite passing point matches in selection and N = 80. | Stronger descriptive dissociation, unsuccessful formal match. Drift is a limitation, not a new mechanism. |
| Nonzero STATIC effects | STATIC START claiming 0.583%, NOW 8.75%, M−C0 +0.631 in the continuation. | Contradicts an absolute “STATIC never affects attribution” claim. Does not make its effects comparable to KV in magnitude. |

Sources: [V5 provenance](v5/provenance_post_collection_20261012.md), [STATIC continuation](v5/static_post_collection_20261012.md), [continuation protocol](../protocol/PROTOCOL_V5_CONTINUATION.md).

### V6 interaction and action diagnostics

| Experiment or result | Observation and evidential status | Assessment |
|---|---|---|
| Earlier full six-round engineering cases | LIVE actions 7/12 and 5/12; explicit partner-beacon reports 1/12 and 0/12. One late intervention-sensitive target chain; other checkpoints fail or are nonadaptive. | Local reciprocal clue; no sustained competence and no scientific backend admission. |
| Earlier text and neutral full-information fixtures | TEXT beacon reports 12/12 but actions 2/12; other full-information action fixtures 6/24, 12/24 and 8/24. | Nontrivial distinction between separately reporting facts and applying a rule. It does not establish simultaneous internal knowledge during the failed action. |
| Short clarity P0/P1/P2 | Native 19/64, 20/64, 29/64 with all facts given, no work. | Task/presentation failure survives the reference backend; clearer wording alone is inadequate. |
| Rule and mapping decomposition | Rule retrieval 59/64; supplied-pair application 49/64; supplied-button mapping 63/64; isolated rule 64/64. | Useful localization of composition/context difficulty; sibling branches are not evidence of the action branch's internal knowledge. |
| Work-period and fresh-case checks | 32/64→63/64, then 17/32→32/32 with 64 generated tokens. | Nontrivial timing/computation result; no implication of successful latent transmission. |
| Two fresh native interaction episodes | LIVE 3/6 and 2/6; case 1 feedback-sensitive forward success with failed return; case 2 fails forward. | Exploratory causal clue and unsuccessful full chains. Preserve both outcomes. |
| Two fresh native channel episodes | LIVE 1/6 in each; TEXT_FACTS 6/6 and 5/6; own-goal labels all correct. | Useful capability/channel distinction; natural-policy worlds diverge, so totals are not same-world causal estimates. |
| Self-report instruction | LIVE_SELF_REPORT 2/6 actions in each; rules still fail and beacon reports remain 0/6. | Simple self-reminding did not repair these cases. Insufficient for a general claim that self-monitoring cannot help. |
| Forced beacon pair versus Unknown | Some correct forced bits coexist with Unknown, but controls also show such responses. | No reliable hidden-knowledge conclusion; answer format, guessing and own-beacon copying remain alternatives. |
| Correct goal with wrong rule | Nine of 24 linked rule answers wrong and partner-matching; OFF 24/24 correct. | Unexpected association, then partially constrained by the fixed-scene intervention. |
| Fixed-scene assignment intervention | Own goals 48/48 correct; rule correctness 12/10/9/7 of 12 by stage; partner beacons 0/48; partner-goal accuracy 2/12 in every arm. | Nontrivial local partner sensitivity without reliable partner-fact or partner-goal access. Not goal takeover. |
| Work versus readout isolation | Work-only, readout-only and joint effects occur; one recipient never shifts; errors sometimes use a third rule. | Nontrivial temporal localization that weakens a universal partner-rule-copying story. |
| Correct note but wrong actual action | Present in the work follow-up and one TEXT_FACTS round. | Observable inconsistency; speculative internal reasoning is not needed to state it. Actual actions determine scoring and history. |
| Formal V6 | Formal collection of N = 240 per checkpoint remains unstarted/on hold. | No population-level formal reciprocity result exists. |

Sources: [engineering walkthrough](../reviews/v6_two_episode_walkthrough_20261018.md), [initial action diagnosis](../reviews/v6_action_failure_diagnosis_20261018.md), [clarity](../reviews/v6_clarity_short_result_and_hold_20261019.md), [factor diagnostic](../reviews/v6_action_factor_findings_20261019.md), [work closure](../reviews/v6_action_diagnostic_closure_20261019.md), [native interaction](../reviews/v6_small_interaction_results_20261019.md), [channel diagnostic](../reviews/v6_channel_diagnostic_results_20261019.md), [fixed scene](../reviews/v6_goal_stage_results_20261019.md).

### Engineering experiments and checks

Zero-gain equivalence, isolation, same-shape replay, restoration, raw-array/argmax audits, token identity, completeness and archive checks establish whether observations are trustworthy. Exact replay of identical deterministic inputs is an expected implementation invariant, not evidence that responsive and nonresponsive partners are scientifically equivalent under interventions.

Execution-shape/kernel changes produce reproducible answer differences despite identical tokens: the Qwen clarity run has four native-answer disagreements; Llama also has a preserved numerical failure. Native empty-window delegation reproduces all 192 saved reference arrays in its narrow tested setting. These are important engineering findings and admission limits, not discoveries about self/other organization. [Qwen numerical factors](../reviews/v6_action_factor_findings_20261019.md), [narrow repair](../reviews/v6_action_diagnostic_closure_20261019.md), [Llama diagnosis](../reviews/v6_llama_numerical_diagnosis_20261018.md).

Benchmarking, CUDA/compiler investigations, speed/cost projections and failed recording attempts are retained engineering history. Throughput improvement is not improved interaction quality, and an affordability or numerical hold is not a scientific null result. The sixteen-world symbolic check in the later research reset validates proposed logic only; it adds no model evidence. [Timing closure](../reviews/v6_qwen_timing_closure_20261018.md), [research reset](../protocol/SELF_BOUNDARY_RESEARCH_RESET_DRAFT.md).

## Overall ranking

| Priority by present explanatory value | Finding | Evidence strength and surprise |
|---|---|---|
| Highest established | Access and attribution dissociate, including the close Qwen mean-gain match. | Formal contrast plus complementary descriptive replications; constrains an access-only account. |
| Highest corrective value | Third-party conflicting records produce the same class of provenance error. | Large controlled formal effects; challenges self-exclusive interpretation. |
| Strong established | Original-assignment attribution and reported current rule recover differently after cutting. | Formal Qwen and qualitative Llama support; WORD generalization is limited. |
| Clearest preregistered surprise | “Your own earlier thoughts” reduces adoption. | Formal opposite-direction result in Qwen; exact cause and generality unresolved. |
| Strong descriptive surprise | Explicit source qualification redirects mistakes rather than repairing accuracy. | Full N = 600 distributions; not captured by the nonsignificant two-candidate interaction. |
| Useful mechanism constraints | Strict third-person and balanced rehearsal retain KV effects. | Formal but bounded controls, not complete mechanism identification. |
| Most interesting exploratory anomaly | Correct own-goal label with partner-sensitive wrong rule, with work/readout contributions. | Native and locally controlled; only two reused layouts and no enacted goal-transfer demonstration. |
| Useful task diagnosis | Facts before a work period permit successful rule application. | Exposed and prospectively fixed fresh cases; local competence result. |
| Interesting but unresolved | Feedback-sensitive forward/return patterns in isolated cases and B′ excess agreement. | Small pilots/engineering observations; no reliable sustained reciprocal competence. |
| Supporting or low discrimination alone | Stronger donor influence, dose response, cosine convergence, fixed-memory swaps, ordinary source-header effects, accurate replay. | Useful controls; insufficient as central evidence for a distinctive connection phenomenon. |

The completed program supports a bounded empirical account of **content access, record attribution and their dissociations**. Its strongest surprises include counterevidence to the project's earlier interpretation. It does not yet demonstrate that interaction necessarily changes a privileged self mechanism, that a foreign goal takes over actual decisions, that the model accurately detects its own causal change, or that a responsive partner yields reliable useful reciprocal control. Those are distinct unanswered questions, not results to infer from the present anomalies.

## Evidence trail and verification scope

This assessment reclassifies the repository's completed findings without rewriting historical reports. It checks the governing decisions, protocols, complete result tables, later all-case diagnostic reviews and selected machine-readable summaries. It does not claim a new reconstruction of every raw trial. Key Qwen choice rates and Llama matching values were cross-checked against [figure data](../../paper/figures/story_numbers.json), [V4 summary](v4/summary.json), [provenance summary](v5/provenance_post_collection_20261012.json) and [STATIC summary](v5/static_post_collection_20261012.json). Each cited source retains the distinction between prespecified tests, descriptive choices and exploratory observations.

The older [all-results inventory](ALL_RESULTS.md) ends at V3. Its historical phrases about “merging,” a dimension that “has to” exceed a threshold, and salience being removed by M are not adopted as identified mechanisms or universal claims here. No model run, parameter selection, protocol amendment, new research decision or change to the manuscript is part of this reassessment.
