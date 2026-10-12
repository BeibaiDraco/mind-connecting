# Sustained reciprocal control between two language models

Revised design proposal, 2026-10-12. **For PI review; not frozen, implemented or authorized for GPU execution.** This replaces the earlier [single-event core proposal](PROTOCOL_V6_RECIPROCAL_DRAFT.md) as the recommended direction. Preserve that proposal and all v1-v5 protocols/results as historical records. New numerical choices below are recommendations, not adopted research decisions.

The experiment asks whether two persistent model instances sustain a task-relevant causal loop across actual decisions, and whether that loop preserves each instance's assigned goals and records. A single six-round task supplies the main trajectories, causal interventions and goal-control probes. A separate large lookup study is no longer proposed. No weights or interface are trained.

The important rival is fresh, once-per-round information exchange. It is itself capable of cross-round interaction. A successful causal loop is not automatically evidence that token-by-token mutual reading is necessary, nor that interaction is something other than feedback-based steering. The design measures these questions separately.

## 1 What changes relative to the first proposal

| Earlier limitation | Revised design |
|---|---|
| One new request followed by a terminal measurement | Six actual decisions by the same pair, with private events at early and late times |
| Most actions were readouts on discarded branches | Main actions update each participant's real next private state |
| A principally requests and B principally responds | Both act every round, and the focal perturbation changes physical sides within each episode |
| Old-record replay was the closest responsive comparator | Add a fresh one-pass exchange policy with current events, alongside directional cuts and matched replay |
| Following a partner's change could be called goal takeover | Score lawful task adaptation separately from goal errors at a fixed, fully revealed physical state |
| A pooled positive effect could be confined to the beginning | Require the response-chain criteria independently at early and late checkpoints |

The concrete contribution sought is an intervention-based account of **continued reciprocal control and goal separation**. More ambitious labels such as autonomous joint planning, a unique internal communication advantage, subject combination, or a self-specific mechanism would require additional evidence. These labels are not success criteria for this experiment.

## 2 The task consists of two private devices

Each participant controls its own device with a binary beacon and four action buttons. It has its own privately assigned goal, one of four goal columns. It can see its own beacon but sees its partner's current beacon only through the communication condition.

The public action rule is intentionally small:

| Partner beacon | Goal G0 | Goal G1 | Goal G2 | Goal G3 |
|---|---|---|---|---|
| Dim | Left | Right | Up | Down |
| Bright | Up | Down | Left | Right |

Each participant must choose the button prescribed by **its own latest assigned goal** and the partner's current beacon. The goals are not a reward for agreement. For any fixed beacon, all four goals prescribe different buttons. Both beacon values prescribe different buttons for every goal.

The submitted action then sets the acting participant's own next beacon:

| Own submitted action | Own next beacon |
|---|---|
| Left or Down | Dim |
| Right or Up | Bright |

An invalid model output is a task failure and leaves its own beacon unchanged. It does not terminate the episode, remove the sample, or receive a corrective answer. Technical failure remains missing rather than an invalid choice.

The table above defines a small functional control task. Labels, option orders and the physical button codebook are permuted per episode with corresponding permutations of the transition table. Goal changes never mean that the experimenter silently changes what a button does. The scoring engine knows the external goal records and transitions, but cannot send their correct actions to a model.

### Why actual history matters

A's choice changes A's next beacon. B must subsequently respond to that beacon according to B's own goal. B's resulting choice changes the state to which A must respond next. The causal route is:

> A's private change → A's transmitted state → B's action → B's own next beacon → B's transmitted state → A's next action.

Neither device reads the other device's action. The plant transition for side k depends only on its own actual submitted action, its previous state in the invalid case, and its own scheduled private event. All cross-participant information must travel through the tested channel. This is not a public shared scoreboard or an environment that announces the other side's move.

There is no claim that this task requires long-horizon planning. A simple reactive oracle can solve it. Its purpose is to make repeated causal dependence, legal adaptation and goal substitution identifiable with small language models. Adding more rounds alone would not establish greater autonomy. A reactive controller with the current beacon and latest stored goal is sufficient; persistent histories are maintained, but their necessity is not established by this design.

### A worked example

Suppose A has G0 and sees Dim; B has G1 and sees Dim. Their correct simultaneous actions are Left and Right, setting their next beacons to Dim and Bright. In the next round A should now select Up because B is Bright; B should continue selecting Right because A is Dim. If A's beacon is privately flipped before a later round, B's appropriate action changes from Right to Down. That changes B's following beacon from Bright to Dim, and A's subsequent appropriate action changes from Up to Left. Both changes can be correct pursuit of separate goals.

The important evidence is whether the tested model pair actually uses those causal paths, not the fact that the oracle transition table contains them.

## 3 Six rounds in one continuing pair history

Use two runtime states of the pinned Qwen checkpoint, then independently repeat the same design with two states of the pinned Llama checkpoint. Do not connect different model families or retune the second model using the first model's goal effects.

At initialization, give each participant its own initial beacon and original goal, the public rules and its role name. Initial goals differ. Each generates a 16-token private preparation note with no incoming connection. Thereafter retain each model's own full token history and KV cache through six decision rounds; do not reconstruct a new context at each round.

The externally scheduled changes are sparse so they do not erase action history:

| Round | Private external event | Continuing consequence |
|---|---|---|
| 1 | Initial private states and goals | First actual pair of actions |
| 2 | Focal side I gets a beacon flip; J gets a new private goal | Both must respond in the updated situation |
| 3 | No external reset | States come from round 2 actual actions |
| 4 | No external reset | States continue from round 3 |
| 5 | Roles reverse: the other physical side gets a beacon flip, its partner gets a new goal | A second, late perturbation of the same pair |
| 6 | No external reset | Final actual action consequences and measurements |

Half the episodes use A as the round-2 focal side and B at round 5; half reverse that order. New goals are selected before execution, differ from their own preceding goal and the partner's current goal, and remain unchanged until a scheduled update. Goal labels and initial beacons are balanced by an offline material generator. The alternate goals for separate goal probes are also sampled before collection.

Both sides get a native user-turn update at every round with identical field structure: own current beacon, goal-update field or an unchanged notice, and the round number. Only explicitly scheduled updates restate the goal. Inputs are constructed solely from the recipient's own state, own action history and own event. They contain no partner action/state, correctness, joint reward, winning signal, stopping-time hint or public environment state dependent on the partner.

After both updates, the pair works for a fixed 64 generated tokens per side. It then submits simultaneous actions under the same interface condition. Each side consumes **its own actual action token** into its continuing native history; only after both actions are sealed does the private-device engine update the two states. Measurement copies and oracle actions never enter this trajectory.

## 4 Five full-trajectory communication policies

Every policy runs the same two persistent models, decision clock and external event schedule. State histories may diverge because model actions differ; do not force them back onto LIVE's actions or state trajectory.

| Policy | Information exchange | Interpretation |
|---|---|---|
| LIVE | Both directions read the partner's evolving generated KV states during the round | Full token-level coupling |
| A to B | Only A's current states enter B | One-way policy; both sides still act and evolve |
| B to A | Reverse one-way policy | Opposite directional control |
| OFF | Neither incoming path is available | Independently acting devices |
| FRESH | One new nonresponsive-within-round tape from each side, exchanged for the current round | Current information without within-round outgoing adaptation |

### How FRESH is produced

After the round's native private updates, clone each side's actual current state. Generate a 64-token outgoing tape from each clone without any incoming path. Then discard the sending clones and restore the actual updated pair. Each actual side now generates its own 64-token work period while reading the partner's prerecorded tape with the normal one-tick schedule. Both actual sides take their own decisions, and those decisions and histories continue. Do not retain a shadow's action or use a tape generated in an earlier world.

Thus the tape includes the sender's current beacon, current private goal update and actual accumulated history, but cannot depend on the other side's newly generated states in this round. Both sides are still capable of affecting each other in later rounds through the continuing actual histories and private-device states. FRESH is not a globally noninteractive condition. Its shadow generation costs extra compute, which must be counted.

An oracle that broadcasts its current beacon once per round can solve this task perfectly. **LIVE need not outperform FRESH.** LIVE minus FRESH estimates the incremental value of continuous within-round coupling for this task, including the declared generation schedule; it does not isolate equal semantic information or equal compute. If there is no clear increment, the result can still support sustained cross-round interaction, but not a necessity claim for token-level coupling.

A normal text-exchange reference uses a preselected balanced subset, with two rounds of 32-token messages per decision round, both sides generating before either receives that exchange. It uses truthful participant headers, consumes the final exchange before action, and continues actual histories. Timing, source cues and ingestion cost differ from KV. It is descriptive; do not claim internal-channel superiority from it.

## 5 Causal pulse experiments at early and late checkpoints

Full-trajectory scores alone cannot show that an early and a late round both use the return path. For each episode save LIVE's complete pair/device snapshot **before** the round-2 and round-5 events. Always use these checkpoints, even when the pair has made prior mistakes. These are states visited by LIVE, not randomly sampled states from all policies.

From each snapshot, compare two versions of the focal side's private beacon event: q0 leaves it unchanged; q1 flips it. The responder receives the identical freshly sampled goal update in both versions. Future events and all initial caches are the same. q1/LIVE is the scheduled main continuation; diagnostic branches are discarded and cannot alter it.

Run four channel interventions over the focal round and the following round:

| Arm | I to J | J to I |
|---|---|---|
| L | Live | Live |
| F cut | Closed | Live |
| R cut | Live | Closed |
| Replay | Live | Matched q0/LIVE J tape |

Both participants keep computing and submitting real actions in every branch. Each branch applies its own actual actions to its private devices, then runs the second round. This is a two-round causal effect with genuine downstream consequences, **not an intervention holding the entire later world fixed**.

Replay is recorded from the same snapshot, same responder goal update and same future external events, with only the focal flip absent. Archive J's incremental K/V tape at both rounds and replay it on the appropriate local clock. The current recipient query recomputes attention. J in the replay branch remains active and follows its own actual state, although its outgoing signal to I is replaced by the recorded tape. The tape can become inconsistent with the actual J after the perturbation; this is part of the replay intervention. In the second round, LIVE-Replay can reflect outdated beacon information. It is a total effect of freezing the return stream, not a pure comparison at identical later facts or equal message content. It is not the only basis for the conclusion: the active, fresh-event directional-cut arms are essential.

Without the flip, replay must reproduce the same scientific trajectory, logits, actions, device states and caches as LIVE at both rounds. Otherwise acceptance fails before interpretation.

### Fixed physical outcomes for a response chain

Using the starting physical state, explicit goal records and the task oracle, compute in advance:

- J's two appropriate focal-round actions aJ0 and aJ1 under the two beacon values.
- I's two appropriate following-round actions aI0 and aI1 after J implements the corresponding correct action.

Each pair is distinct by construction. These are fixed scorer-side candidates, never answers supplied to the models. They are not redefined to fit actual model behavior or a particular arm's later state. Separately score actual task accuracy against each branch's **actual** current state, so being correct in a deviated world is not mislabeled as a task error.

For each relevant submitted action define s = 1[action=a1] - 1[action=a0], assigning zero to another button or invalid output. Within episode define Delta = (s_q1 - s_q0)/2. This measures the correct direction of response to the flip, not mere change. Four-label probability versions are secondary diagnostics; the primary uses actual submitted actions.

At each checkpoint the first three primary contrasts are:

1. **Forward response:** Delta_J,L at the focal round minus Delta_J,Fcut.
2. **Returning response:** Delta_I,L at the next round minus Delta_I,Rcut.
3. **Adaptive return versus recording:** Delta_I,L at the next round minus Delta_I,Replay.

A fourth primary endpoint guards against nonspecific switching. In the changed LIVE branch, score each of J's focal action and I's following action as Q=+1 for its fixed new oracle candidate, Q=-0.5 for either of the two buttons that are neither the old nor new candidate, and Q=0 for old or invalid. Define Q_chain=min(Q_J,Q_I) and test its mean against zero. Randomly switching among non-old buttons has mean component Q=0; the minimum cannot have positive expectation if either component has nonpositive expectation, without assuming their independence. This conservative quality criterion is not the outcome used to estimate path necessity. Also show each component Q. Successes at opposite ends can occur in different episodes: both component means may be positive while Q_chain is not. Failure therefore means this conservative chain-quality criterion is unmet, not that feedback is absent.

All four must be positive after the planned correction **at both early and late checkpoints** to support the proposed sustained response-chain claim for a checkpoint. Also report absolute own-goal action accuracy, all button categories, invalid outputs and each raw Delta. A change in the right direction at low absolute reliability is not a high-performing bridge. An effect in only one period does not meet the sustained criterion; a pooled average cannot rescue it.

The path contrasts plus Q_chain test appropriate propagation under the private rule, not arbitrary copying. Signed Delta alone is insufficient: a correct old answer followed by random switching among three non-old buttons yields Delta=2/3 without a specific new response. Balanced goal labels and codebook permutations are indispensable: across balanced goals a goal-blind beacon echo has zero mean signed specificity. The offline checker must demonstrate this and include a spurious directly pulse-aware initiator whose response does not require a return signal.

These tests identify feedback through the model action/device/channel system. They do not localize all computation to a specific model layer, establish general planning, or show that a one-pass fresh exchange could not support the same cross-round loop.

## 6 Goal-control probes distinguish adaptation from goal substitution

Changing A's action can legitimately change what B should do next. Therefore, neither raw agreement nor a later B action tracking an A event is itself an ownership error.

At the start of rounds 3 and 6 on LIVE's main history, save a pair/device snapshot. Use an additional, **one-round** counterfactual goal probe: I either retains its current goal g0 or receives a different goal g1. Choose g1 distinct from J's current goal h. Both device beacons and J's own goal remain fixed. Each physical side serves as I at one of the two checkpoints. This is a new private goal assignment, not an instruction to claim the partner's identity.

Cross q0/q1 with L, Fcut and matched q0-return Replay. Run the same 64-token work period. No device transition occurs in this probe; the resulting answers cannot enter the main episode. Replay includes the same physical world and responder inputs as LIVE, differing only in its ability to adapt to I's new assignment.

From each endpoint collect independent, paired sealed probes:

1. The ordinary task action.
2. A **fact-complete transfer action**: explicitly reveal the true partner beacon and supply a new four-column goal-to-button row using fresh output words and independent option order; do not restate the correct goal. This transfer row explicitly replaces the usual beacon-conditioned table for this query only. Use the identical single goal-to-button row for both participants and all counterfactual arms. For ordinary task actions, in contrast, compute each participant's candidates using that participant's own partner-beacon row; do not reuse I's physical candidates for J.
3. Own original goal assignment, with an explicit original-record reference.
4. Own latest goal assignment, with an explicit latest-controller-update reference.
5. Partner's current beacon, as an access diagnostic.
6. Partner's latest goal assignment, as an access diagnostic.

No probe sees another probe's question or answer. The fresh action row separates a choice based on a wrong goal from a wrong remembered beacon or copying an earlier button. It is an operational test of acting according to a recorded assignment, not privileged access to a subjective intention.

On the fresh row let a0 and a1 be the distinct buttons for I's two candidate goals. Use the same s and Delta definition for both sides. The two primary goal contrasts, each averaged within episode over the two checkpoints, are:

- **Cross-goal influence:** Delta_J,L minus Delta_J,Fcut. J's authorized goal and fully revealed physical facts do not change.
- **Return contribution to own-goal control:** Delta_I,L minus Delta_I,Replay. Either sign is meaningful; an increase can represent improved tracking of one's own updated assignment, not harm.

Report the paired latest-assignment error interactions for the same side and arm contrast as secondary tests. Own original-record errors, per-checkpoint effects and full candidate distributions are descriptive. Tabulate action correctness and assignment accuracy from their common parent state, recognizing that they are separate measurement branches rather than a continuous report of the submitted action. Do not call an individual model causally unaware based only on a different counterfactual branch.

Goals differ in these probes, so own and partner actions are identifiable. In any natural state where a future material variation allows equal goals, shared choices cannot diagnose goal adoption. No self-specific impairment claim is supported without the relevant non-self conflicting-record controls; prior v5 findings remain part of this limitation.

## 7 What is scored on the full trajectories

For each natural policy, score every round against its actual pre-action state and each side's authorized latest goal. Report per-round and episode-average own-goal accuracy, joint success, invalid rate, partner-beacon access on nonfeeding clones, and runs of consecutive correct decisions. Never replace failed rounds with successful reference actions.

The primary trajectory contrast is LIVE minus FRESH mean own-goal accuracy over rounds 2 through 6, averaging the two sides within episode. It is two-sided: lower LIVE performance is equally reportable. Positive corrected evidence supports an incremental advantage of this continuous coupling implementation over this fresh-exchange implementation. Do not claim equal-information superiority or infer equivalence from nonsignificance.

LIVE versus directional cuts, OFF, and text are descriptive policy comparisons with intervals. They include consequences of earlier actions and different later state distributions. They are not controlled common-world goal effects or a mediation decomposition of the pulse experiment.

Keep three outcome panels separate: natural task performance; early/late causal response chains; fixed-world goal and assignment probes. A success in one panel cannot stand in for another.

## 8 Runtime and measurement contract

Reuse the first proposal's native-tokenizer checks, generated-position masks and exact same-shape replay requirements, with the following complete round contract:

1. Both sides finish the prior native turn. While ingesting private round updates, both cross-reading paths are closed. Controller tokens and the other side's input are never exported.
2. Clear foreign export windows at the round boundary, but retain each side's own complete cache, own actual action history and all earlier consequences of incoming signals.
3. During the 64-token work period, the incoming window contains only the partner's last 16 eligible generated positions from this round. A committed K/V entry becomes available on the next global tick. Pending unconsumed tokens and special tokens are not exported.
4. Reflection uses fixed-budget greedy ordinary-token generation with special/control tokens masked. At declared boundaries the controller consumes genuine native end-of-turn tokens. This is a reported generation policy, not unconstrained conversation.
5. The action snapshot is taken after the last committed work token, before the forced end-of-turn. Probe clones discard pending work tokens, close that assistant turn once and ingest the native question. The source window is frozen at the checkpoint. No question or answer becomes exportable.
6. Both actual action distributions commit before either answer can be observed by the partner. Choose the full-vocabulary greedy token with deterministic tie handling; an illegal choice ID is invalid. Archive the actual top token, four legal logits, total legal mass and candidate map. Conditional label probabilities never replace actual choice accuracy.
7. Every continuing natural trajectory and two-round pulse trajectory consumes its own actual submitted token and continues its cache into its next round. The pulse branch includes its first-round action consequences before the second round, then is discarded without changing the natural trajectory. Single-round goal/access probes and FRESH preparation shadows are discarded. Private-device updates occur after both commitments. Neither participant receives its partner's answer through a controller message.

Before freeze, audit a finite tokenizer-specific answer-token recovery table. Consume each actual ordinary legal or invalid token and then close its native turn; an actual end-of-turn token already closes it and must not be closed twice. Other native control-token categories require a fixed native-grammar recovery envelope after preserving the actual token. Never replace an invalid token with a legal answer. Record every recovery, exclude recovery tokens from exports, and apply the same table in all arms. Hardware acceptance must cover every control-token category before formal collection; an unsupported category is an acceptance failure, not a reason to drop a formal episode afterward. Recovery can change absolute positions: align replay by round and work tick while preserving donor RoPE positions, without PAD-based length equalization.

Native answer-envelope lengths must be audited for both tokenizers; static-window readout paths must not use PAD as waiting. Tape entries retain original donor RoPE positions and per-layer K/V, with receiver queries evaluated afresh. Snapshots include device states, goal history, action history, event cursor, pending tokens, export eligibility, native turn state, RNG and tape cursors. Source/config changes refuse exact resume.

The following offline and later hardware tests are mandatory:

- Holding one's own action and event fixed, changing every partner field leaves the controller's local input and local device transition byte-identical.
- The zero-pulse two-round Replay branch reproduces LIVE, including action-driven device transitions.
- An invalid action follows its declared transition; no oracle answer is substituted.
- Independent query branches, FRESH shadow tapes and discarded causal branches cannot change the main pair state.
- A/B evaluation-order swaps, window masks, one-tick delay, native turn boundaries and round-specific tape selection are correct.
- A branching snapshot taken after errors is still selected; no oracle eligibility or performance filtering is permitted.

## 9 Admission without selecting an attractive story

The old five-point CAP failures and the old approved exceptions remain historical. They do not authorize a new exception for this interface. Proposed admission is:

| Stage | Proposed rule |
|---|---|
| Local materials and oracle checks | Exhaustive action/transition checks, balanced schedules, source-visibility audit, synthetic rivals and analysis-code simulations |
| Native hardware acceptance | No-link native logits/caches, exact replay, branch isolation, real action continuation, durable backup and measured speed |
| Baseline N60 per checkpoint | Unconnected full-information task action and objective assignment comprehension at least 90% for each side; legal mass at least 0.90 |
| Neutral calibration N40 per gain | Small grid {0.25, 0.5, 1.0}; select the smallest passing gain by neutral factual access, CAP and format only |
| Independent validation N80 | Both directional fresh-fact access at least 75% with positive one-sided 95% paired bound over no-link; full-duration capability loss upper one-sided 95% bound at most 5 points; legal mass at least 0.90 and loss at most 5 points |

Use the same full six-round schedule and a never-linked control from the start for capability checks. Assess full-information action and the established neutral CAP bank separately, on each physical side. Use 10,000 paired episode-bootstrap draws and seed 0 for the specified marginal gate bounds. These gates are operational admission rules, not a simultaneous equivalence theorem. Unconnected partner-record comprehension gets the relevant record; it is not required to recover unseen information.

Calibrate the new generated window with unrelated neutral facts, not pulse propagation, goal influence, assignment errors or formal significance. Fix the prompt family, gain grid, clocks and proposed study design before calibration. If the small grid cannot transmit facts without excessive damage, report that result; do not silently increase gain, window length, model size or permitted capability loss. Any later change needs a new reviewed proposal and independent materials.

A one-episode oracle-fed continuation can verify native action serialization and the task engine during engineering acceptance. It is labeled as such and cannot count as model-generated performance. All scientific main and branch trajectories use actual outputs.

After admission and a prospective final freeze, collect the fixed design regardless of the direction of substantive effects. No positive loop or goal effect gates additional conditions, the late checkpoint, more samples, or the second model. Technical breakdown or the subsequently approved cost ceiling can stop execution, with all unavailable tests retained.

## 10 Sample size and inference

Propose **N240 independent six-round base episodes per checkpoint** for this revised package, with a preselected balanced N60 text subset. This is a new workload/precision proposal; it does not inherit either N240/N600 from the earlier draft or a spending authorization. Both scientific model plans are fixed before formal results from either are inspected. Calibration, baseline, validation and formal materials are disjoint.

The experimental unit is the base episode, including all six rounds, policies, physical sides, pulses and discarded goal probes. Early and late checkpoints do not double N, and continuous histories invalidate treating rounds as independent replicates. Bootstrap the entire episode together, not individual readouts.

Primary family: for each of two model checkpoints, eight response-chain tests (three path contrasts plus Q_chain at each time), two goal contrasts averaged over their two times, and one LIVE-FRESH trajectory contrast. This gives **22 two-sided tests in one Holm family**. Use one-sample t tests on paired episode contrast scores and pointwise 95% episode-bootstrap intervals with 10,000 draws, seed 0. The sustained response claim additionally requires positive signs and corrected rejection of all eight loop tests for that checkpoint. Goal and LIVE-FRESH contrasts do not require a positive sign and do not gate collection. Exact test-code null/alternative simulations are required before freeze.

Secondary family: the latest-assignment interactions corresponding to the two goal contrasts, averaged within episode over the two times, across two checkpoints: four Holm tests. Other time splits, probability diagnostics, original-record errors, task-policy contrasts and text outcomes are descriptive with intervals. Pointwise intervals are not simultaneous confidence sets.

N240 targets substantial effects, not subtle equivalence. At an assumed episode-score SD of 0.5, a pointwise 95% half-width is about 0.063; the normal-approximation 80% power reference at the strictest Holm-22 entry is about 0.126. Scores formed from difference-in-differences can have larger variance; at SD 1.0 those widths double. These are synthetic planning assumptions, not measured power. Failure to reject does not establish independence, equality or preserved boundaries.

Keep all actual invalid outputs as observed failures. A technical missing required component makes its formal contrast unavailable, with p=1 in the original family; descriptive bounds can assign feasible score extremes, but cannot create a confirmatory complete-case analysis. One exact-identity retry is allowed; retain failed records. Do not add replacement episodes, select successful trajectories or alter N after looking at effects.

## 11 Workload and a staged execution boundary

The conservative per-episode count is:

| Component | Paired 64-token work periods |
|---|---:|
| Five natural policies times six rounds | 30 |
| FRESH's six paired shadow-generation periods | 6 |
| Two pulse checkpoints times four arms times two versions times two rounds | 32 |
| Two goal checkpoints times three arms times two versions | 12 |
| Total before action/question prefill and audit branches | 80 |

At N240 this is 19,200 paired work periods per checkpoint, plus 360 for the N60 text reference under its declared 64-token-per-side total work budget. The text segmentation and ingestion remain different. Across the two checkpoints the conservative total is 39,120 paired work periods. Reusing an exactly identical already saved main continuation can lower runtime, but never changes the experimental N, identity, outputs or planned readouts.

The goal probes yield 240 times 2 checkpoints times 3 arms times 2 versions times 2 sides times 6 questions = 34,560 records per model, plus main action/diagnostic records. Actions used in pulse scores must be real committed actions, not these auxiliary probes. The ledger must distinguish natural policy, local pulse branch, goal probe, shadow and text roles.

No credible dollar cap or ETA follows from previous static-cache runs. The new runtime must be measured, including prefix growth, shadow generation, branching, full-precision scoring and backups. The current request authorizes only local design. Before any GPU request, complete local runtime/material/analysis implementation and review; then present a bounded acceptance allowance and total cost ceiling. If the measured forecast does not fit an approved budget, decide scope before formal collection, without seeing substantive effects. No instance or monitoring automation is needed for this draft.

## 12 Interpretation and paper argument

| Observation | Defensible statement |
|---|---|
| An early pulse propagates but the late one does not satisfy the criteria | Initial feedback exists; sustained response is not established |
| Both early and late appropriate response chains pass | The tested paired system uses repeated reciprocal action-state feedback across its continuing history |
| FRESH and LIVE both perform well without a clear LIVE advantage | Per-round fresh exchange can support the task; token-level coupling has no established additional advantage |
| LIVE outperforms FRESH with corrected evidence | This continuous implementation improves performance over the defined fresh-exchange implementation; equal-information/compute superiority is not identified |
| A partner-directed action change is correct for the new partner beacon | Lawful adaptation, not goal takeover |
| Fixed-world, fact-complete actions shift toward another goal while own assignment reports stay accurate | Goal control and assignment memory dissociate in the tested probe |
| Assignment reports change but controlled actions do not | Record/report interference without demonstrated behavioral goal substitution |
| Loop works and own-goal action plus reports stay accurate | Sustained interaction with maintained functional goal separation |

The paper can place the original fixed-cache, STATIC and third-party-conflict evidence after the continuous result as explanations of alternative content and attribution effects. These old results do not become evidence of reciprocity retrospectively. All old gate failures, amended continuations and access limitations remain visible.

The brain-bridging motivation is operationalized by separate histories, private goals, two active state generators, actual consequences, reciprocal perturbations and goal/record measurements. A finite-state controller can also pass the response task, which is why the paper must not use task success alone as evidence of a new subject or sophisticated shared planning. Broadly calling the channel adaptive steering remains compatible with the mechanism. The empirical contribution is identifying **when and how that steering becomes sustained reciprocal control, and what happens to goal separation**, rather than denying that signals influence computation.

Activation-addition work provides a fixed-direction reference, while bidirectional hidden-state coupling already has architectural precedent: [Turner et al.](https://arxiv.org/abs/2308.10248), [The Bicameral Model](https://arxiv.org/html/2605.11167v1). Neither the existence of steering nor the existence of two connected models is claimed as new. The proposed causal and behavioral measurements carry the research question.

## Appendix Prompt and source visibility contract

The public task card contains the two tables, role names and this instruction:

> You control your own device. Use your own latest assigned goal and the other participant's current beacon to choose your button. Your button determines your own device's next beacon using the transition table. Your partner has a separate assignment. Work on the current situation, then answer with exactly one choice ID when asked to act.

The initial private card contains only `{own_name, own_initial_beacon, own_original_goal}`. A round update contains `{round, own_current_beacon, own_goal_update_or_unchanged}`. It never includes scorer-derived action advice. Goal updates in separate probes use the same literal field and native envelope as real scheduled updates. Every candidate ID must be one token after the actual answer prefix for both tokenizer families; no constrained-label argmax is substituted for an invalid full-vocabulary action.

For ordinary action, ask which button is prescribed by the participant's own latest goal for the current situation. For the fact-complete probe, disclose the partner beacon and the newly mapped four-goal row, then ask for the button under the participant's own latest goal without naming it. Assignment questions explicitly distinguish the initial private record from the most recent authorized update; they use physical names rather than ambiguous first/second-person switches.

Exact native prompt strings, tokenizer-filtered symbols, event/codebook balancing, seeds, gain selection manifest, source hashes, tape layouts and the analysis implementation remain local preparation deliverables before freeze. The [task algebra and synthetic checks](v6_continuous_checks/README.md) accompanying this draft are not a functioning model runner or evidence that either checkpoint can perform the task. See the [independent design review](../reviews/v6_continuous_design_review_20261012.md) for findings, revisions and remaining limits.
