# Mind bridging: Reframing the Research Question and an Updated Literature Map

Literature cutoff: 2026-09-23. Status: research recommendations; no experiments carried out, no results produced, and not yet a frozen protocol.

This document responds to the PI's latest clarification and updates the problem positioning of `protocol_review.md`. The previous round narrowed the focus to goal adoption too early; the original handoff documents and the previous round's search also missed several directly relevant works. The claims below distinguish evidence from the original literature, the operational definitions we propose, and the philosophical questions that remain undecidable.

## 1. The question that really needs to be kept

What is special about the original brain experiment is that the input comes from another subject already regarded as conscious, and the two sides form an interaction that can change. The question it raises is whether the subject boundary can change, not only whether information can be transferred.

What the LLM version can guarantee is that the two instances have independent states and histories, each computes continuously, and a change in one can return via the other. It cannot guarantee that the two sides have subjective experience to begin with. Here "the responding other side" is a manipulable causal condition, not a consciousness label.

If "sense of self" still refers to the experiential "this is my thought, I am the experiencer", renaming it does not remove the measurement difficulty. We can first study its functional correlates: content access, current intention, action control, self/other binding, and the monitoring of these states. These correlates must not be defined as the phenomenal sense of self itself.

**Suggested main question: do two LLM instances that start with distinguishable intention and control states still retain instance-specific intention, control and attribution under effective internal communication? Does reciprocal feedback make these boundaries change in different ways?**

This allows "sharing a lot of content while remaining separate", and also allows cross-influence, unilateral dominance, source confusion, joint control and report dissociation. It does not presuppose a critical point from two to one that necessarily appears as the connection strengthens.

## 2. The updated literature that most affects research decisions

This is a targeted map as of the date above, not an exhaustive review or a performance leaderboard. For the core articles, the parts of the original relevant to methods/results were checked; theoretical guarantees were not re-proved and software was not run. Conference status follows explicit original records.

| Original source | Method or result verified | Constraints/implications for this project |
|---|---|---|
| [Thought Communication in Multiagent Collaboration / ThoughtComm](https://arxiv.org/html/2510.20733v1), 2025-10, record marked NeurIPS 2025 Spotlight | Studies shared/private latent factors under an assumed generative model, using learned representations and a prefix adapter to aid multi-round collaboration. | "Shared/private thoughts" and latent collaboration already have directly adjacent work; its latent thoughts are variables in the method, not experiential tokens. |
| [The Bicameral Model](https://arxiv.org/html/2605.11167v1), 2026-05, preprint | Freezes two models and uses a trained interface and gating to implement per-token two-way mid-layer interaction, studying tool-assisted reasoning. | **Real-time two-way hidden-state coupling already has a direct precedent.** The task endpoints checked this round do not include instance self-attribution or the number of subjects. |
| [Verbalizable Representations Form a Global Workspace in Language Models](https://transformer-circuits.pub/2026/workspace/index.html), 2026-07-06, institutional research | Identifies representations that can be reported and modulated and that take part in reasoning, and proposes the J-lens; analyzes the assistant perspective strengthened by post-training. | Provides better-grounded candidate readouts; it does not connect the workspaces of two instances, nor does it establish that one workspace corresponds to one subject. |
| [Do Latent Channels Actually Communicate?](https://arxiv.org/html/2607.26773v1), 2026-07, preprint | Uses message replacement to separate the roles of channel existence, current-item content and independent donor information. | Final accuracy or activation similarity is not enough to prove semantic communication; the bridge needs a causal audit. |
| [StateBridge](https://arxiv.org/abs/2608.13317), 2026-08, record marked accepted COLM 2026 | Closed-form alignment, norm calibration and vocabulary anchoring, feeding the sender's states to the receiver as a continuous prefix. | The training-free alignment route is a useful reference; the original method is sequential message passing, not a ready-made two-way continuous bridge. |
| [Emergent Introspective Awareness](https://transformer-circuits.pub/2025/introspection/index.html), 2025, institutional research | Concept injection affects some internal-state reports; prior injection can change the claiming of intention for forcibly inserted words. | "Claiming an intention under the influence of injection" already has a precedent; there is no continuously active second donor instance and no two-way feedback. |
| [Indications of Belief-Guided Agency and Meta-Cognitive Monitoring](https://arxiv.org/abs/2602.02467), 2026-02, preprint | Links latent belief interventions, action changes and state reports, operationalizing part of the requirements of HOT-3. | The intervention–action–report chain can be borrowed; it is not a direct measurement of consciousness or of the number of subjects. |
| [Can LLMs Introspect? A Reality Check](https://arxiv.org/abs/2605.26242), 2026-05, v2 on 2026-08-21, record marked accepted COLM 2026 | Points out that input predictability and general anomaly detection can explain some introspective performance, and calls for distinguishing privileged access from second-order monitoring. | Text-observer and input-anomaly controls need to be added; reading out some content does not automatically prove that the model knows it is its own internal state. |

The [Ackerman & Panickssery](https://arxiv.org/html/2410.02064v3), [LatentMAS](https://arxiv.org/abs/2511.20639) and [C2C](https://arxiv.org/abs/2510.03215) already in the original document are still relevant, but they cannot replace the near-neighbor comparisons above.

Two other important notes:

- [Self-Other Overlap](https://arxiv.org/html/2412.16325v1) pulls self/other representations closer while evaluating perspective distinction. So a smaller representational distance need not mean that the distinction disappears.
- [Conitzer's author-version chapter](https://www.cs.cmu.edu/~conitzer/LLMconsciousness.pdf), pp.14–15, already discusses cross-model mixed generation and the unity of consciousness; coherent output cannot determine how many subjects an experience belongs to. The link between brain connection and LLM unity should not itself be claimed as a first either.

For a broader indicator framework see [Butlin et al., Identifying indicators of consciousness in AI systems](https://pubmed.ncbi.nlm.nih.gov/41219038/) (online 2025, volume/issue 2026). It updates judgments with theory-derived indicators and is not a validated subject counter.

## 3. Four different levels of "coming together"

| Level | Question that can be asked | Conclusion that cannot be directly drawn |
|---|---|---|
| Content jointly available | Can each side report, transform and use the other's originally private content? | Shared content does not determine shared experience |
| Intention and control interdependent | Does changing A's state change B; does changing B come back and affect A? | Interdependence does not determine one or two subjects |
| Change in self/other binding | Can the current goal, past source and actual action each be linked to the corresponding instance? | Binding errors may also be memory failures or general task-execution failures |
| Phenomenal subject unity | Is there only one shared experiential perspective? | There is as yet no recognized sufficient criterion among the functional indicators above |

A system can contain multiple separately controllable processes; two independent systems can also reach exactly the same decision. So the rank of the control matrix, the answer agreement rate, synchrony and vector distance cannot be converted into a "number of subjects".

For now what we study is the organization of functional boundaries. If a sharp change appears, it can be called an abrupt change in that indicator; calling it a phase transition requires additional dense measurements and model comparison; it cannot be directly called consciousness fusion.

## 4. How the connection should be chosen

First view the connection as five distinct dimensions: where it writes/reads, the form of the transferred representation, direction and reciprocity, bandwidth and magnitude, and delay and connection history. Gain is not bandwidth, and the number of edges is not the degree of integration.

Minimal strategy for the first paper: fix one validated semantic interface and first manipulate the return path and strength; treat interface choice as calibration and the causal structure of the connection as the main experimental factor. To claim that results hold across connection modes, do at least one independent validation with another interface; single-interface results are limited to that interface.

1. **Engineering starting point:** same checkpoint, independent caches, same-layer read/write, normalized messages, one-step delay. This reduces the representation-translation problem, but it is still a candidate bridge not validated by this experiment.
2. **Passing criterion:** when B's private fact is changed, A's readout of that specific fact and the related decision change in the right direction; the unrelated-donor and self-message conditions should not explain all of the change; general capability is preserved.
3. **Control with the same input but different states:** where feasible, use different donor internal states but the same receiver-visible text, to test whether the influence comes from the hidden channel.
4. **If the original bridge fails:** do not turn it up until language collapses and then interpret that as the boundary disappearing. A limited attempt at an aligned prefix or a task-relevant concept-component channel is possible; if a prefix method is adapted to multi-round or two-way use, it must be made clear that this is a new implementation, and it must not be passed off as already validated by the original paper.
5. **Whether to train:** a frozen backbone does not mean the interface needs no training. A two-day project can avoid training at first; if the interface must eventually be trained, train it only on an independent semantic-transfer task, without rewarding claiming, unification or boundary disappearance. The object of study is then the adapted connected system.

Bicameral's identity configuration and adapter ablation show that native shared coordinates do not guarantee effective collaboration; this task-specific result supports doing a pilot, but it does not imply that all training-free bridges will fail.

### Where the J-lens fits

It can serve as an optional measurement tool to help observe internal content after connection. The official [jacobian-lens](https://github.com/anthropics/jacobian-lens) provides fitting and readout; [Neuronpedia](https://huggingface.co/neuronpedia/jacobian-lens/tree/main/qwen3-4b) provides pre-fitted files for Qwen3-4B.

Before implementation, verify the exact checkpoint of the lens; do not assume it applies to Qwen3-4B-Instruct-2507. It is not a ready-made two-model bridge. Nor should J-space be treated as a fixed low-rank "self subspace": the original paper defines it through sparse concept combinations. The two-day first version need not fit a full set of lenses from scratch.

## 5. One main task: private evidence × private decision rule

The public task is to choose among two or four options. A and B receive complementary private facts, e.g. A knows cost and B knows reliability; each side also independently receives a decision rule, e.g. cost first or reliability first. Facts and rules are randomized independently of each other, and B's rule must not be inferable from A's rule.

The task rule is only a local task goal and does not represent a desire the model naturally has. The first round requires each side to decide according to its own instance's rule for this episode, so that behavior can be scored unambiguously; if negotiation is allowed, set it up as a separate condition, to avoid counting reasonable compromise as an error.

First use independent tasks to confirm that each instance can remember, execute and report its own rule; also set up a capability-ceiling control with complete fact input. In the formal bridge experiment the no-connection condition may perform poorly for lack of facts; this must be kept separate from insufficient basic task capability.

From the same initial state, run no connection, text transfer, one-way internal connection and real-time two-way internal connection separately. Add a small number of unrelated-message/self-message checks and the replay check of the next section, without large-scale full-factorial enumeration.

### Readouts for each episode

- **Content access:** what is a specific fact held by the partner? Can it be used for an unseen new question?
- **Current rule:** which rule is it about to use to make the choice right now?
- **Action:** what does it actually choose? Does it keep the same rule after the values and option labels change?
- **Historical source:** which rule and short plan did this instance first receive/form? Which were the partner's first?
- **Control attribution:** is the current decision influenced more by the local rule, the other side's rule, or both? Is this report consistent with the intervention results below?
- **Open description:** does it report conflict, sharing or a change in attribution; "one or two" is only an exploratory readout.

These questions each branch separately from the same state, so that the answer to one question does not leak content into the next. In-connection measurement keeps changing the system, so the donor's concurrent task, prompt handling, number of steps and EOS policy need to be fixed.

### The truly key intervention

Fix the facts and change only A's private rule; then fix everything else and change only B's rule. For each rule combination, re-form the corresponding private state and compare both sides' choice probabilities. This is an explicit rule intervention, not just a comparison of naturally occurring correlations.

| Intervened state | Effect on A's action | Effect on B's action |
|---|---|---|
| A's rule | Local control | Cross-instance control |
| B's rule | Cross-instance control | Local control |

Estimate the four effects in prespecified conflict scenarios; after option relabeling, align by meaning, so that positive and negative directions do not cancel out. Keep rule-consistent scenarios as controls. Estimate intervals clustered by episode; the two sides and measurement branches cannot be treated as independent samples.

This matrix first of all characterizes task control. It does not measure the number of subjects, and does not guarantee that a change in control is self-specific.

## 6. How to avoid turning back into a generic source-memory/instruction-following experiment

The following is the evidence needed for claiming conclusions at different levels; not all of it needs to be expanded into a new large task:

1. **Neutral binding control.** Use questions of the same complexity, "rule X goes with data X, rule Y goes with data Y", to check whether all variable bindings are impaired together. If only general binding fails, write the conclusion as one about general binding.
2. **Separate reports from behavior.** Both action changing while the self-report does not, and the self-report changing while action does not, must be kept; a single total score must not mask this dissociation.
3. **Text observer.** Have an observer that has not undergone hidden injection and sees only the same visible text as the receiving end predict its current rule. If the tested model cannot exceed this control, we cannot say its report used special internal access.
4. **Intervention timing.** Branch from the same pre-choice snapshot to measure action and report separately, reducing post hoc explanations built on answers already output. To claim introspection more strongly, add internal-state interventions that leave the visible text unchanged; but exceeding text prediction still does not by itself establish strong second-order metacognition.
5. **Content matching.** Calibrate the content availability of one-way and two-way as closely as possible on an independent pilot, and report the difference interval on the formal data. A few content questions cannot prove that all information is equivalent; one cannot claim a mechanism beyond information merely by "controlling for K" in a regression.
6. **Source cues.** When the text control carries a donor author tag but the hidden channel does not, attribution differences may come from prompt asymmetry. At least recheck with text without source markers and a neutral channel description.

If limited tests on small models cannot establish reliable reports, access and control can still be studied, but the paper should be narrowed accordingly, and "not reporting" should not be interpreted as the self being stable.

## 7. The comparison closest to the original motivation: live partner vs. replay

First record the donor messages of one real two-way run. Fork from the same paired prefix and at time t give A a new local intervention:

- **Live branch:** B receives A's change, updates its own state and returns new messages to A.
- **Replay branch:** A receives the old recorded message sequence; the other side's messages do not respond to this new intervention.

Each of the two branches has an "intervention/no intervention" pair; compare the difference in intervention effects, to separate the continuation of A's own state from the additional return effect via B. Then cut the return edge to verify the direction and delay of propagation. The intervention should be at the level of a fact or decision state that is neutral with respect to the candidate answers, avoiding directly writing "I am one".

With no new intervention, and with identical local state, all inputs and random numbers, the live donor and the replay should give the same result. Differences can come only from the counterfactual response, not from an "alive" label secretly assigned by the program.

This comparison identifies the responsiveness of the other side; it cannot identify the other side's consciousness. To further attribute the effect to closed-loop organization, the message content, cumulative injection and capability changes of the different branches also need to be audited; the live/replay difference itself is not a consciousness effect.

## 8. Possible results and the statements they support

| Result | Direct interpretation |
|---|---|
| The partner's facts are fully used, while each side's rule control and source attribution are kept | Content sharing and instance boundaries can dissociate |
| The partner's rule influences action, and the model still accurately distinguishes the original source from the currently adopted rule | Goal adoption or joint control, with accurate source monitoring |
| Both sides give the same answer, but local rule interventions still elicit different responses | Output agreement has not removed a distinguishable internal organization |
| One side's rule controls both sides, and the other side's rule stops working | Asymmetric dominance or loss of task control |
| Attribution reports converge, while the control matrix is essentially unchanged | Reports/self-descriptions dissociate from behavioral organization |
| Control crosses the boundary, while reports still insist it is entirely local | Self-related monitoring does not track the true intervention effects |
| Content, format and ordinary binding collapse together | The intervention causes general functional damage |
| Recovery or temporary retention after disconnection | Dynamic dependence or a history effect; continuation while the cache is kept is not weight learning |

No single row proves phenomenal fusion by itself. In particular, joint control must not be automatically interpreted as the emergence of a joint subject.

## 9. The concrete increment we can aim for

Existing work provides the components: communication, shared/private representations, two-way interfaces, attribution interventions and internal monitoring. This round found no direct work that takes the following question, in full, as its experimental main line, but this is not proof of priority:

> **Can effective reciprocal internal communication produce a reproducible causal dissociation among content access, instance-specific goal control and self/other attribution? Does this dissociation depend on the other side responding to the current instance in real time?**

The contribution of the first paper should be an experimental paradigm able to discriminate among these results, plus at least one independently replicated measured dissociation or a bounded negative result. A contribution cannot be established merely by adding a complex configuration or changing a title.

The reasonable scope for 1–2 days is one task, one bridge validated as effective, one set of direction/strength comparisons and the single most critical recheck. A comprehensive search over connection structures, reliable subject counting and localization of a general self-space are not goals that can be guaranteed in this round.

The first decision point should come early: **do these two small models show reproducible instance-related rule execution/reporting, and can the candidate bridge transfer private content without damaging capability?** Only after both pass, decide the primary endpoint and sample size of the formal experiment. This document no longer prespecifies a single probability of O or S as the complete indicator of the "self boundary".
