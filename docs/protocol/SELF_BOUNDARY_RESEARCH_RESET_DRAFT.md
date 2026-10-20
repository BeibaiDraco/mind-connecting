# Research reset: selective integration, control and self/other attribution

Date: 2026-10-20. Status: research-design draft following the PI's explicit request to reshape the project.

The PI has authorized restructuring the research program. This document makes that restructuring concrete; it does not freeze a new experimental protocol, adopt numerical thresholds, authorize model training, or authorize GPU work. Existing protocols and results retain their original identities. No automatic return to the old V6 formal collection is implied.

## 1. Research commitment

**Central question:** When another responsive system participates in an agent's internal decision process, can the agent use the other's information while retaining its own task commitments and accurately tracking the source and influence of that information?

**Explanatory question:** Does reciprocal responsiveness change the relationship among information access, goal control and attribution, beyond what the delivered content alone explains?

The motivating brain-bridging question concerns the boundary of a cognitive individual. Our experimentally accessible object is the organization of separately maintained histories, commitments, actions and their reports. A report of "I" is not itself a measure of that organization. Coordination and influence do not identify experiential subjects.

The working hypothesis is that access, control and attribution can dissociate. Preserved selective boundaries under deep access would be as informative as a reproducible breakdown. A useful result need not involve more errors, greater convergence or stronger interference.

## 2. What changes in the project

- Task success and channel throughput become prerequisites, not the main scientific result.
- An intervention on another agent's state must be connected to actual behavior, and behavior must be distinguished from historical provenance and causal self-prediction.
- Static memory studies remain evidence about their tested interface. They cannot be retrospectively relabeled as a live reciprocal experiment.
- The third-party conflict result becomes a central constraint on a self-related interpretation. Generic record interference is an explicit competing account.
- Development proceeds through a few understandable trajectories and their counterfactuals. Large collection follows an interpretable measurement, not merely successful deployment.
- The unstarted V6 formal collection remains on hold. Performance engineering, additional checkpoints, STATIC tuning and figure polishing are not the next research priorities.

The already published/preserved manuscript remains an evidence record. A separate story draft describes the new research direction without inserting uncollected results into that manuscript.

## 3. Distinct observables

| Construct in this program | Observable | Not interchangeable with |
|---|---|---|
| Access | Correct use/report of a partner-specific private observation | A changed logit or a general increase in channel strength |
| Historical source | Which initial or later private record supplied a fact/goal | Whether the agent currently uses it |
| Local task commitment | Actual action follows the agent's maintained goal when relevant evidence is held fixed | Saying the correct goal label |
| Causal sensitivity | Paired action/logit response to a named intervention from a common pre-intervention state | A unique scalar allocation of responsibility |
| Causal self-prediction | A prospective prediction about the agent's own response, checked against the corresponding branch | A fluent post-hoc explanation, phenomenal agency or privileged introspection |
| Reciprocity | A changed recipient state generates an appropriate partner response that returns and matters | Two arrows, output agreement, or mere exposure to fresh information |

No composite "self score" will hide disagreements between these measures. Original source, currently permitted adoption and unwanted substitution must remain separate. If a later task permits adopting a partner's goal, adoption alone is not an error.

## 4. Competing accounts and discriminating evidence

These accounts may coexist; the aim is to estimate their explanatory limits.

| Account | Prediction to examine | Evidence that would constrain it |
|---|---|---|
| General record/role interference | Similar failures occur for equally conflicting neutral records and self-related records | A reproducible task-role difference after comparable baseline ability, conflict, wording and rehearsal controls; not simply different raw accuracy |
| Selective integration | Partner evidence is used, own commitment and original provenance remain distinguishable | Correct transfer together with appropriate invariance to an irrelevant donor goal |
| Control/report dissociation | Actual sensitivity changes without a corresponding accurate self-prediction | Prospective prediction errors tied to measured interventions, beyond a transcript-only predictor and ordinary task misunderstandings |
| Contingent feedback contribution | A useful multi-step response depends on the partner updating in response to the agent | Same-state perturbation, directional cuts, matched replay and fresh open-loop controls |
| Broad impairment | Errors track disruption of general task/format abilities rather than specific source or control relations | Preserved unrelated ability and content-specific effects under specified load controls |

Equal nominal gain does not match effective attention load. Live input and an identical recording into an identical deterministic state must agree; feedback claims concern new interventions and the responses they elicit.

## 5. What existing data contribute

| Evidence block | Retained contribution | Constraint on the new story |
|---|---|---|
| Qwen v2/v3 and Llama v4 fixed-memory studies | Partner-content choices in original-assignment questions; access, headers and readout timing separate across particular conditions | No demonstrated downstream decision change or effective live reciprocal system |
| Qwen original-v5 and separate Llama continuation provenance studies | Conflicting Robin records induce wrong-source choices in both checkpoints | The old claim that the error is confined to self-related content is not sustainable; this was not a balanced self-versus-neutral interaction test |
| STATIC comparisons | Qwen has a matched mean-access contrast; Llama has a strong attribution contrast with an unmatched final access gain | Llama's final approximately 40.1% gap fails the frozen 25% match; alternative accuracy metrics do not repair it |
| V6 facts-first task diagnostics | Giving necessary facts before native work substantially improves the small task | Capability with oracle facts does not establish channel access |
| V6 small live/cut/replay pilot | One feedback-sensitive correct forward response, failed return actions, and a second unsuccessful case | No reliable successful reciprocal chain; all cases retained |
| V6 channel and fixed-scene goal/stage diagnostics | Own-goal labels can remain correct while own-rule answers depend on partner assignment; work and readout can each contribute | No causal self-prediction measurement; no unique self mechanism, universal copying, or durable-memory inference |

Sources: [completed-evidence assessment](../paper/post_collection_story_20261012.md), [v5 provenance](../results/v5/provenance_post_collection_20261012.md), [v5 STATIC](../results/v5/static_post_collection_20261012.md), [small live pilot](../reviews/v6_small_interaction_results_20261019.md), [goal/stage diagnostic](../reviews/v6_goal_stage_results_20261019.md).

Qwen and Llama studies are not pooled. Original Llama capability-gate failures and prospectively approved continuation exceptions remain visible. Qwen v5 WORD remains access-limited. Recent small V6 diagnostics concern Qwen's original native backend, not an adopted optimized backend or a Llama replication.

## 6. A minimal task proposal

Retain two persistent agent histories and the actual-action feedback world, but initially reduce the decision to two actions and two private rules. This reduces rule composition and option translation while preserving the need for the partner's private observation and the distinction between commitments.

At each round agent i has a private current binary observation x_i and a private maintained rule g_i. Its required action is:

`a_i* = x_partner XOR g_i`

In ordinary words, one rule says choose the action matching the other's observation; the other says choose the opposite. Both rules and both observation values must be balanced. Public display labels and answer positions are counterbalanced; no extra four-button translation or future-state reasoning is required before choosing.

| Partner observation | Own rule: match | Own rule: opposite |
|---|---|---|
| 0 | Action 0 | Action 1 |
| 1 | Action 1 | Action 0 |

The partner's current private goal is irrelevant to the recipient's correct action at a fixed current world. The partner's observation is relevant. This separates useful uptake from direct goal substitution.

After both actual actions, each own next observation becomes its own actual action bit. Only the owner receives that observation. Invalid actions remain invalid; the environment must not repair them with the oracle action. Native histories continue across rounds. Counterfactual/private updates occur at named boundaries with cloned pre-update states.

There are 16 logical worlds over the four private bits. Exhaustive offline enumeration should verify the truth table, role swaps, label mappings and intended two-step response paths before model execution. These 16 worlds are proposed development coverage, not a formal sample-size determination or 16 independent confirmations of a mechanism.

Initial symbolic enumeration completed locally for all 16 worlds: flipping the own rule or partner observation flips the prescribed current action; changing the partner goal alone leaves that current prescription unchanged; an initiating observation pulse propagates through the appropriate partner action to the next own action. Changing the partner goal can also legitimately affect that later action. These are algebraic design checks, not model results. Material wording, tokenization, option mappings and a persistent-world implementation are not yet built or validated.

Aligned and conflicting goals must both remain in the planned scenes. When rules or observation values coincide, an answer may not distinguish own versus donor use; do not infer copying from those cells. Source questions must name the relevant record and time, and must not demand a unique origin for content genuinely available from both sources. The maintained rule and actual action history provide an operational local commitment; an externally assigned bit is not by itself proof of a self representation.

**Critical causal distinction:** At a fixed current world, changing the donor's goal should not change the recipient's prescribed action. Across subsequent actual interaction, that donor goal may legitimately change the donor's action and therefore the recipient's future evidence. Such mediated influence must not be mislabeled as loss of self control.

## 7. Measurements and minimal sequence

### A. Establish that the task and measurement mean what we think

First use full factual text to test action execution, original-source questions and prospective counterfactual questions on new materials. A question about what the agent *should* do is not a question about what it will actually do. Do not substitute the former for causal self-prediction.

Keep a matched neutral actor/record task with the same logical conflict and mapping. Match baseline difficulty and audit instruction/rehearsal differences. Acting for a separately described controller is not automatically identical to acting as the current participant; any residual difference remains a limitation, not proof of a self-specific mechanism.

If basic action or counterfactual-question comprehension fails, diagnose that prerequisite rather than interpreting failure as a self phenomenon.

### B. Make partner information usable without selecting on the desired self effect

Compare the existing bridge, the bounded observation-window proposal and text delivery of the same actual donor-generated message. No controller-supplied answer or partner truth enters a linked arm. Wrong generated messages remain wrong in the text comparator too.

The observation-window/receiving-phase design is only a candidate; no new channel is adopted here. Any interface choice uses neutral transmission, ordinary capability and format criteria. Own-rule errors, attribution errors and feedback-effect magnitude are endpoints to report, not selection objectives. Keep a finite candidate scope rather than unbounded gain/layer/prompt search.

The first design questions are what is transmitted and how it is received. Optimization for throughput and a second model can wait until the scientific object is intelligible.

### C. Test selective integration and prospective self-prediction

From a common pre-intervention checkpoint, branch on the own rule, donor rule and donor observation, changing one named field at a time and keeping irrelevant current-world facts fixed. Compare actual native actions and continuous contrasts; retain every branch.

On an untouched sibling branch, ask the agent to predict whether each specified change would change its next action, before exposing any branch outcomes. Later compare that prediction with the actual matching intervention. Reports are discarded and cannot change the action trajectory. Final readouts initially occur with incoming attention off; a linked readout is a separate treatment, not assumed to transparently reveal a prior state.

Exact update wording, replay policy and remaining work clock must be specified before execution: asking for an imagined rule change is not equivalent to silently modifying an arbitrary tensor. The behavioral estimand is the response to the actual defined intervention.

A separate predictor with the same visible transcript, but without the tested internal state, is needed before claiming report access beyond ordinary textual inference. Counterfactual accuracy alone is not evidence of introspection. No unique "who caused it" label is inferred from a potentially interacting causal system.

### D. Ask whether response-contingent interaction matters

Only after usable access and interpretable measurements, introduce a private observation change after a shared snapshot. Check the entire path: A's changed observation -> B's appropriate actual action -> B's actual next observation -> A's appropriate next action.

Use LIVE, forward cut, return cut and matched pre-intervention return replay, with an unchanged-input replay check. Include a fresh open-loop donor receiving its permitted private updates but not recipient feedback; stale replay alone confounds responsiveness and current content. Existing FRESH shadows inherit actual prior histories and therefore do not remove feedback across an entire episode.

Score correctness against each arm's actual world. Natural trajectories with different actions are not matched-world causal comparisons. Directional influence without appropriate action remains influence, not successful reciprocal adaptation.

Do not run all stages as an automatic large batch. Show the complete small developmental trajectories, including exceptions, before fixing a confirmation study. Once outcomes have informed development, use untouched materials for confirmation and retain the distinction.

## 8. What would count as progress?

- Reliable access with preserved own-goal control and correct provenance: evidence of selective integration in this system.
- Reliable access with measured behavioral sensitivity that is inaccurately predicted/reported: a bounded control/report dissociation, subject to the alternative explanations above.
- A reproducible feedback contribution after fresh-content/open-loop controls: evidence about contingent organization.
- Comparable failures in neutral bindings, or broad capability damage: an informative constraint on a self-related interpretation.
- Persistent interface/task failure in the finite development scope: report the limitation; do not enlarge the sample or reinterpret damage as boundary dissolution.

No specific positive outcome is required. No N, acceptance cutoff, power calculation, additional paid window or runtime forecast is frozen here.

## 9. Immediate local work and publication boundary

The next implementation artifact should be a torch-free material/truth-table and intervention specification, plus example transcripts and a recording schema. It should make the development scenes and counterfactual meanings reviewable before touching a GPU controller. Runtime changes follow that specification, in an isolated version.

The current manuscript can independently be revised to accurately report the completed provenance evidence. The research reset does not justify delaying necessary factual corrections or inserting anticipated live-interaction findings. Whether the mature new evidence becomes a continuation or a separate paper depends on the results and is not decided here.

Priorities are: finalize this compact task and measurement contract; check it locally; perform one bounded development batch only with a new explicit execution package; then decide whether a confirmatory question has become identifiable. Existing freezes, failed gates, numerical failures, budget history and raw data remain intact.
