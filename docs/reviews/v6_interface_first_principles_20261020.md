# From interference to usable reciprocal interaction: evidence and proposal

2026-10-20, Codex. Read-only evidence/source synthesis requested by the PI. This is a prospective development proposal, not a protocol amendment, frozen sample allocation, interface adoption, or GPU authorization. Existing protocols, failures and all exposed cases remain unchanged.

## The question and the current bottleneck

The motivating question remains whether two separately maintained, evolving model states can use each other's changing information and respond to those responses. A physical connection already exists. Useful communication and successful reciprocal adaptation have not yet been established.

The functional chain is: sender's private observation -> exported state -> recipient's usable, source-bound information -> recipient's own decision -> changed recipient state -> a useful response by the original sender. Causal influence at one link does not establish the whole chain. Nor must all informative influence improve task performance.

There is no meaningful requirement that interaction be something other than information transfer at the mechanism level. A single incoming state can always be described as a perturbation or steering input. The additional testable property is that later inputs are generated in response to the recipient's earlier state or action, and that this contingency matters. An exact recording of the same inputs to the same deterministic recipient must reproduce its output. A useful live/replay comparison therefore requires a subsequent private intervention to which the live partner can respond but the previously recorded return cannot.

## What the completed evidence supports

The small diagnostics below used Qwen and the original native backend. They are not a new Llama result or validation of the optimized backend.

| Evidence | Supported observation | What remains unproven |
|---|---|---|
| Facts-first task diagnostic | On 32 fresh cases, immediate answers scored 17/32 and 64-token work scored 32/32 with identical supplied facts/questions | General task mastery or access through a latent link |
| Two-case channel diagnostic | Explicit factual text gave 11/12 correct actions, LIVE 2/12; linked own-rule errors occurred despite correct own-goal labels | A matched-world effect for the full natural trajectories, which diverge |
| Fixed-scene goal/stage diagnostic | Own-rule correctness W0R0/W0R1/W1R0/W1R1: 12/10/9/7 of 12 combinations; own-goal labels 48/48; explicit partner beacons 0/48 | Absence of all information in the state; general copying of partner rules |
| Controlled partner-goal changes | Some own-rule answers change with the partner assignment despite an unchanged recipient task/world. Forty disconnected full-array comparisons remain exactly invariant | A unique semantic mechanism rather than changed planning content, priming or attention competition |
| Work/readout separation | Effects can survive immediate readout disconnection, arise during readout alone, or require both | Durable memory; a special nontextual persistence mechanism |
| Two-case interaction pilot | One correct forward response disappears with either cut or matched return replay, but the return actions fail; the second case lacks the correct LIVE chain | Reliable reciprocal cooperation or a general LIVE advantage |

Denominators count repeated observations or fixed combinations, not independent episodes. Explicit Unknown and failed forced-choice readouts do not prove the absence of all encoded information. Conversely, a changed logit or correct generated note does not establish usable knowledge or a successful action.

Evidence: [task diagnosis](v6_action_diagnostic_closure_20261019.md), [channel diagnosis](v6_channel_diagnostic_results_20261019.md), [controlled goal/stage diagnosis](v6_goal_stage_results_20261019.md), [interaction pilot](v6_small_interaction_results_20261019.md).

## Implementation facts and mechanistic hypotheses

Inspected `src/mb/v6_native.py`, `src/mb/v6_runtime.py`, `src/mb/v6_interaction_pilot.py`, `src/mb/v6_tasks.py` and `src/mb/v6_channel_diagnostic.py`.

1. Work exports the newest 16 ordinary generated-token K/V positions from the partner, at every attention layer. Windows reset before each round. Raw private observation prompt positions are not directly exported. This is a stream of ongoing planning states, not a designated current-observation message.
2. In each head, the attention output is `own_out + beta * (foreign_out - own_out)`, with beta determined by own/foreign attention partition sums and gain. Foreign information competes with own-context attention. Gain 1 is neither a fixed mixture fraction nor a promise of mild influence. Own K/V is retained; this is not direct deletion or replacement of the private cache.
3. Software checks source identity, position and payload integrity, but those checks do not make the network interpret the source as "the other participant." Both agents use their own first-person task framing. A reminder in the prompt is not a guaranteed semantic binding operation.
4. Foreign keys are used as exported from their native histories; this code does not rebase their positions or align the two private contexts. Context/position compatibility is a possible further limitation, not an established explanation of the observed errors.
5. The original connected readout applies the held foreign window while consuming the closing turn and the question. It can alter the measured answer directly. The controlled W0R1 failures demonstrate that this concern is real for some cases.

An additional read-only tokenizer inspection of every connected work branch in the saved goal/stage `work.jsonl` examined the actual final 16 generated tokens. Several donor windows discuss a proposed button or a predicted *next* beacon, for example `Final answer: Down` or `After pressing Down, my device transitions to Bright`. Some recipient and donor endings closely resemble each other. These strings identify the token positions actually carried by the window. They do **not** exhaust the information encoded by their contextual K/V, prove that the current beacon is missing, or establish the cause of the behavior.

The leading hypothesis is a mismatch between what the recipient needs (the partner's current observation, correctly attributed) and what the current bridge emphasizes (the partner's evolving decision context), compounded by competition with the recipient's own rule use. The latest intervention shows influence, but also third-rule errors and a recipient with no rule shift; it does not justify a universal goal-copying account.

Merely raising gain can amplify both useful input and interference. Merely requesting self-report has already failed in the small channel test. Neither is an adequate next plan.

## Proposed priority: establish an interpretable receiving interface

Keep the original connection as a baseline. Implement a separate development variant if the PI adopts this direction; do not silently modify V6's frozen contract.

The first candidate would distinguish observation exchange, receipt, and private action selection:

- Each agent generates a short outgoing observation segment from its own current record, with an explicit participant and round frame. Initially it concerns its own current beacon, not its private goal, planned button or guessed partner state. Actual errors and malformed messages remain errors; the harness never replaces them with ground truth.
- Export the K/V of that designated segment instead of the trailing unrestricted planning window. Retain the same model and an explicitly bounded payload. The other agent receives internal states, not decoded text inserted by the controller.
- Give the recipient a bounded receiving period, then a private work/action period with incoming attention off. The receiving instruction names the partner and the purpose of the channel without supplying its observation. Source text is only a candidate aid; it is not assumed to confer a source tag on every foreign vector.
- Preserve both native histories across exchanges and repeat the procedure after actual actions. Periodic reciprocal exchange is still an online feedback system. This does not demonstrate the stronger property of unrestricted simultaneous token-by-token interaction; reintroducing concurrent work is a later ablation.

This differs from the unsuccessful SELF_REPORT prompt: the exported interval and read/write schedule change, and foreign planning states no longer remain connected throughout private decision/readout. It is a scientific interface change, not a proven repair.

An observation segment's contextual K/V may still encode the sender's goal or other history. Choosing its token positions does not purify the representation into a fact-only channel; the task-irrelevant donor-goal intervention must therefore remain. Future diagnostic logging of effective foreign-attention mass could test whether comparable nominal gain conceals very different channel loads, but that instrumentation is not implemented or measured here.

A bounded original-vs-observation-window contrast should precede combining all changes. A second, paired test can then change only the receipt/private-work schedule. Retain both failures instead of searching indefinitely across prompts, layers or gains. A later layer/position or separately bounded foreign-attention design is justified only if the simple transmitting/receiving contrast identifies an unresolved interface bottleneck.

## A small development sequence, not another large formal run

**First proposed batch: eight balanced fresh scenes.** Cover all four own/partner beacon combinations under two fixed rule/option codebooks; test both roles. This is an illustrative finite development allocation, not a frozen N or a generalization claim.

Keep the recipient's private rule and world fixed in paired branches. Change the partner's current beacon while holding its goal fixed; separately vary the task-irrelevant partner goal while holding its beacon fixed. Score actual partner-fact access, own-rule retention and native action selection. Include OFF, the existing window, the observation-window candidate and a text rendering of the *same actually generated donor message*. The latter must preserve wrong donor messages; it differs from the existing oracle TEXT_FACTS capability control. If text can transmit that message but K/V cannot, the remaining issue is transport/receipt. If neither can, investigate the outgoing message, recipient framing and task use. If both convey the fact but only K/V changes the recipient's own rule, interference is localized more sharply.

Use the first fixed batch to diagnose rather than certify a numerical pass threshold. A selected development change needs new, unused validation cases. Do not use return-effect size, significance or self/other-attribution findings as a selector. Do not relabel these development cases as confirmation.

**Only after usable access: a fresh short closed-loop test.** Keep the existing actual-action device world, with a private beacon perturbation introduced after a common pre-intervention pair snapshot. A's changed observation must affect B's correct action; B's actual action must generate its next private beacon; A must then use that new beacon in a correct response. Every scored answer comes from the model, and only actual actions update the world. The recipient must not receive its partner's action or new beacon through an unintended public transcript.

Compare LIVE, forward cut, return cut and a saved matched return from the unperturbed branch. Equal clocks, the same pre-intervention state and an unchanged-event exact-replay check are necessary. Also retain a current open-loop sender that sees its own permitted private updates but receives no partner feedback; a stale tape alone does not distinguish responsiveness from fresh content. Existing FRESH shadows inherit actual prior histories, so they do not eliminate feedback across the whole episode.

Report each link's direction, correctness and actual changed state, including failed complete chains. A lower score with a cut is not by itself evidence of useful communication; appropriate *correct* responses must track the private intervention. A simple successful chain establishes minimal adaptive reciprocity, not rich cooperation or superiority to ordinary textual messaging. More demanding requests/clarification or private-constraint coordination can follow, rather than being bundled into the first channel repair.

No duration or cost claim is inferred from this unimplemented design. No model is launched by this document.

## Interference can be a finding, with a distinct evidential burden

The present candidate finding is an uneven functional effect: a partner-assignment intervention can disrupt use of the recipient's own rule while its own-goal report remains intact, and both work-time and readout-time influence can contribute. That is more specific than "the connection makes accuracy worse," but it remains small exploratory evidence.

To support a stronger account, test generalization on unused cases and distinguish content-specific errors from unrelated input, broad capability degradation and attention-load effects. Matched irrelevant or shuffled real-state controls should preserve the chosen nuisance properties explicitly; equal gain alone does not match effective foreign attention. Do not infer general capability preservation from a correct goal label. Do not call the outcome identity fusion or infer subjective experience.

If usable access improves while rule contamination falls under a separated interface, that would test a causal relationship between routing/source binding and interference. If well-controlled task-irrelevant partner content still systematically changes rule use, that is a complementary result even without cooperation. Neither outcome should be required in advance.

## External checks and their limited relevance

- Pais-Vieira et al. (2013), [brain-to-brain sensorimotor interface](https://www.nature.com/articles/srep01319.pdf): the reported rat interface used task-specific encoding/microstimulation and trained recipients. This supports the analogy that an interpretable interface matters; it does not show that an untrained LLM bridge must work, require training here, or reproduce the PI's conceptual experiment.
- Lowe et al. (2019), [On the Pitfalls of Measuring Emergent Communication](https://ifaamas.org/Proceedings/aamas2019/pdfs/p693.pdf): distinguishes signals related to a sender's state from effects on a listener and motivates interventions. It does not identify the present mechanism or establish useful reciprocal interaction from sensitivity alone.
- Shi et al. (2025), [KVComm: selective K/V sharing](https://arxiv.org/html/2510.03346v1): studies representation/layer selection for context-to-query communication. It supports treating the interface as a design variable. Its results do not establish our live closed-loop claim, and adopting its method would require separate testing.

These sources informed the proposal; the mechanism claims above are grounded in local code and the stated limitations of the local evidence.

## Session scope and operations

No scientific code, frozen configuration, prompt, sample size or model changed. No provider mutation, new inference or restart occurred. The saved original guardian receipt confirms actual stopped state on 2026-10-19 at 23:32:31 UTC (18:32:31 Chicago), with local guard completion. This is a historical stop confirmation, not a new current provider query.

The only changes in this session are this proposal and project bookkeeping. The stopped allocation is not resumed by a recommendation. Existing experiments and failures remain preserved.

Validation: full offline suite 1264 passed, 10 skipped, one GPU test deselected (43.37 seconds); local report links resolve and `git diff --check` passes. No new model test is represented by these offline checks.
