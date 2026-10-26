# Bounded field refresh: what internal connection could change

October 26, 2026. Field author; supplementary preparation for the PI-requested renewed search. This document supplies scientific tensions and methods, not candidate ranking or an adopted experiment. No model execution, target-effect search, code change or new data analysis occurred. The coordinator owns governance and validation.

## Starting knowledge and scope

Reuse the reviewed [field overview](../three_lines_20261025/knowledge/field/overview.md), [field review](../three_lines_20261025/reviews/field.md), [dataset card](../three_lines_20261025/knowledge/dataset/card.md), [dataset review](../three_lines_20261025/reviews/dataset.md), and substantive paper notes linked there. The [original vision](../../../docs/background/Brain_Bridging_to_LLM_Selfhood_Research_Handoff_2026-09-23.md), especially §§2–5, motivates changes in access, cognitive organization, perspective and continuity, without supplying a measure of experience. Prior audits of [latent communication/control](../gap_audit_20261024/sources.md) and [acquisition/integration](../mechanism_priority_20261026/source-and-runtime-check.md) remain in force.

The refresh broadens the positive side of connection: combining fallible evidence, transmitting uncertainty before verbal commitment, distributing control, and preserving information through a circulating network. It also asks which familiar explanations could account for those benefits. Internal communication alone is not a new scientific proposition; the unresolved object must be a relation between what the two instances can do and how information or control is organized.

## New consequential original readings

### 1. Evidence strength versus communicated confidence

[Bahrami et al., *Optimally Interacting Minds*, Science 2010](https://pure.au.dk/ws/files/51720586/BahramiSci2010.pdf). Read original main paper, pp. 1082–1084, four models and Experiments 1–4; supplementary methods were located but not read.

Dyads first make individual visual judgments and discuss disagreements. Four models distinguish random arbitration, choosing the better observer, confidence sharing, and direct sharing of sensory response plus variability. Similar-sensitivity dyads outperform their better member. Randomized sensory noise creates unequal reliabilities; these results fit confidence sharing and reject the direct-signal-sharing model. Choice-only communication with feedback loses the benefit, whereas discussion without correctness feedback retains it.

The key contribution is a predicted response curve across reliability imbalance, not just a mean collaboration gain. “Direct signal sharing” is a statistical information model, not neural wiring; its optimality requires its assumptions. For LLMs, raw internal tensors need not expose usable reliability, and repeated model samples need not be independent observations.

### 2. Implicit communication can support beneficial arbitration

[Pezzulo, Roche and Saint-Bauzel, *Haptic communication optimises joint decisions and affords implicit confidence sharing*, 2021](https://www.nature.com/articles/s41598-020-80041-6). Read setup, Results, weighted-confidence comparison and movement predictors.

Participants first decide separately; disagreements trigger a joint decision using coupled handles. Similar-sensitivity pairs outperform their better member, while sufficiently dissimilar pairs perform worse. A confidence-sharing model fits the performance pattern; early movement, force and work predict whose choice prevails. The authors infer implicit confidence communication.

This supplies positive evidence that explicit verbal confidence is unnecessary. It does not causally isolate a confidence representation: action dynamics may jointly express commitment, evidence and motor dominance. The reported speed advantage compares against another study, not a randomized within-study verbal condition. A native LLM study must distinguish beneficial reliability-sensitive arbitration from merely following the stronger signal; absence of verbal confidence does not itself demonstrate a novel capacity.

### 3. A direct latent-uncertainty precedent, with a crucial endpoint boundary

[Shi et al., *Confidence Laundering in Agent Systems: Why Uncertainty Needs a Latent Carrier*, June 2026](https://arxiv.org/html/2606.20662v1). Read §§4–6 and Appendix A.5–A.12. Preprint; no reproduction.

Qwen-1.5B answers HotpotQA with Tavily observations. Twenty sampled trajectories per question yield semantic-entropy uncertainty labels. Logistic and MLP probes predict those labels from hidden states; handoff comparisons include answer alone, scalar annotation, textual uncertainty and a latent carrier. The reported latent advantage measures uncertainty recoverability: Appendix A.11 explicitly defines AUROC and binary accuracy for a downstream uncertainty predictor.

The introduction describes recovery behavior, but the inspected experimental contract does not demonstrate a frozen recipient choosing useful verification/retry actions or a native reciprocal pair. Figure 4 claims reduced downstream overconfidence; its caption alone does not establish an implemented recovery policy. Thus generic latent transfer of doubt already has a direct precedent, while decoded uncertainty, recipient use and task benefit remain distinct evidence levels. Semantic entropy is a proxy for output instability, not ground-truth knowledge or correctness.

### 4. Joint control without direct transplantation of cognitive state

[Ramakrishnan et al., *Computing Arm Movements with a Monkey Brainet*, 2015](https://www.nature.com/articles/srep10767). Read architecture, Experiments 1 and 3, and results surrounding Figures 1–2.

Separately recorded monkey ensembles drive a shared avatar through fitted decoders. Two monkeys share both axes or separately control axes; three control overlapping two-dimensional projections of a three-dimensional task. Performance and coordination improve with training. This is a concrete positive example of a task organized across brains, including a whole task assembled from partial control.

The monkeys receive visual feedback of a common controlled object; this study does not inject one monkey's rich neural state directly into another. The decoder, axis assignment and shared plant implement substantial organization. Its significance is the division of causal control, not proof that no individual could represent the task or that a new subject forms. The relevant methodological lesson is to account explicitly for what the external controller computes and what the participating systems contribute.

### 5. Circulating information and hybrid distributed memory

[Pais-Vieira et al., *Building an organic computing device with multiple interconnected brains*, 2015](https://www.nature.com/articles/srep11869). Read Results on storage/retrieval and sequential/parallel processing, Figures 5–6 and Discussion. A corrigendum was located but not inspected; avoid relying on exact stimulus-number mappings.

The three-rat storage task decodes a tactile input, relays it through other brains using intracortical stimulation, then returns it to the first rat. Success requires four correct successive links; comparison includes no-stimulation sessions and a single-rat four-trial condition. A separate architecture combines parallel classifications using externally specified Boolean rules.

This already makes circulation, return and distributed storage empirical objects. The “memory” is actively relayed through a hybrid decoder/stimulator network; it is not evidence of a durable autobiographical trace in one animal. Likewise the Boolean operation partly resides in the external controller. A new LLM experiment must locate its computation and specify which local records remain after connection or disconnection; superior network performance alone cannot establish where a capability resides.

### 6. Evidence ancestry: old distributed-systems problem, current agent analogue

[Forsling et al., *Decentralized Data Fusion of Dimension-Reduced Estimates Using Local Information Only*, 2023](https://ieeexplore.ieee.org/abstract/document/10115967). Primary abstract/landing record only; full methods unavailable in this refresh. It describes estimating common information from locally sent/received estimates, then decorrelation before fusion. This is a useful terminology and method lead, not independently verified evidence for its numerical performance. Shared issue: a returning message may be a transformed descendant of evidence already held, so message count differs from independent information count.

[Lin et al., *Beyond Memory Majority: Latent-Source Reasoning for Multi-Agent Memory Arbitration*, 2026](https://arxiv.org/html/2608.19701v1). Reopened introduction and factor-level aggregation; full experimental/appendix evidence is reused from the independently reviewed earlier source note. The method combines learned dependency inference, provenance priors and recovery of independent evidence in external memory. Therefore neither duplicated evidence nor correlation-aware recovery is an untouched LLM question. “Latent source” here is an inferred evidential factor, not native KV communication. Any loop question must go beyond generic echo amplification.

## Scientific tensions visible across these bodies

These are open comparisons or measurement problems, not claims that no one has studied them. They keep multiple answers scientifically useful.

| Tension | Why it matters | Observable contrast and interpretation boundary |
|---|---|---|
| Communicating an answer versus communicating the basis for trusting it | Direct access might alter what can be shared before language commits to one proposition. | Hold a committed answer fixed while varying evidential support; measure useful receiver behavior and information available through each carrier. Decoding a probe is insufficient; following a donor more strongly is not automatically appropriate trust. |
| Stronger collective performance versus changed computation | A pair can improve by redundancy, choosing a better member, pooling evidence, or genuinely complementary processing. | Compare predictions of explicit baselines across evidence asymmetry and complementarity, with compute and external-controller contributions counted. A joint score exceeding either isolated score does not distinguish these accounts. |
| Rich internal access versus functional separability | Connection could preserve distinct perspectives while enabling more effective integration, or homogenize them and lose useful differences. | Measure distinct local evidence sensitivity and joint use under independent interventions. Source-report confusion and beneficial integration can coexist; neither determines the other. |
| An active relationship versus circulating stored content | A returning signal can provide new computation or merely preserve a past trace. | Specify what changes after an intervention, where new information originates, and what remains in each state. Replay and selective cuts can test contingent dependence; exact deterministic replay cannot reveal an extra effect of “being alive.” |
| Distributed memory versus individual continuity | Persistence of useful information, continuation of a project, and accurate origin attribution are different functions. | Cross retention location with later behavior, distinguishing intact caches, generated text, external storage and ongoing communication. This extends a conceptual distinction; previous capacity/portability and formation candidates retain their consumed repair limits. |
| Redundancy that protects versus dependence that misleads | Two sources can improve reliability when independent and exaggerate support when their histories overlap. | Control common versus private evidence ancestry and useful outcomes. Generic duplicates/echoes are already addressed by CAMA and data-fusion methods; the particular missing proposition must be stated. |

## Connection to the actual platform

The pinned frozen Qwen pair permits separate private histories, direction-specific connections, same-state branches, genuine action commitment, disconnection and replay. Its current native K/V window carries contextualized token state rather than a purified fact/confidence/self representation. Existing successful access and attribution contrasts are motivation; they do not establish uncertainty communication, shared control, circulating memory, or reliable reciprocal competence.

The most immediate common evidence requirement is useful behavior influenced by private information in both instances under an explicit task contract. This is a feasibility fact to establish, not a reason to require every proposal to repeat the old tasks. A small diagnostic may settle carrier usefulness before a consequential scientific contrast is attempted. Importing trained adapters, probe supervision or new model weights from the cited methods would require a separate PI decision and is outside this discovery's frozen-model constraint.

## Search record and remaining gaps

Queries combined latent communication with synergy/distributed cognition; collective metacognition and sensory reliability; Brainet joint control/storage; decentralized information fusion and double counting. The coordinator supplied the confidence-laundering lead; its original was verified rather than adopting secondary summaries. Search hits and older reviews were used as routes to originals. A broad latent-synergy query was unproductive and supplies no negative evidence.

This is approximately a short field refresh, not an exhaustive novelty audit. The direct uncertainty precedent, haptic comparison and Brainet methods received the closest new reading. Common-information fusion remains abstract-only. Human joint-agency, autobiographical continuity, distributed working-memory load and modern causal information-decomposition literatures were not newly surveyed. If a candidate hinges on one of these, targeted deciding-source reading is still needed. The independent reviewer should particularly check the uncertainty endpoint boundary, the haptic confidence inference, external computation in Brainets, and whether a proposed native contrast merely renames an established text or data-fusion result. No preferred question is supplied to generation.


## Late deciding-source additions supplied by the coordinator

[Afendulev et al., *Context or Knowledge: How LLMs Attribute Their Own Answers*, October 23, 2026](https://arxiv.org/html/2610.32109v1). Read §§2–4, §7 and Appendix C.2–C.5. This very recent preprint swaps Q+A cache between runs with identical question/answer tokens, while retaining the recipient document. Reports follow the donor cache; document edits leave reports unchanged on the controlled task. Eligibility conditions require initially expected answers/reports, so rates are conditional. Fitted-direction interventions support a cached source-related trace, with weaker prompt-dependent answer-source changes when applied during answering. This directly constrains any claim that transferring source reports through KV, independently of visible answer text, is untouched. It does not establish historical ownership across independently acting agents, unrestricted report accuracy, or a uniquely interpreted “source label.” The study itself preserves whether its trace represents source availability, source use, or both. No reproduction or code audit was performed.

[Gurnee et al., *Verbalizable Representations Form a Global Workspace in Language Models*, July 2026](https://transformer-circuits.pub/2026/workspace/index.html). Read introductory definitions, the flexible-generalization experiment, and detailed swap-results appendix; other sections are overview-level. The J-lens derives directions from average linearized effects on later verbalization. Identical concept-coordinate substitutions are applied across sixteen downstream functions in four categories. Success is heterogeneous: the detailed appendix reports 42/48 country swaps placing the target first, versus 0/48 number-relation swaps at unit strength. This directly supplies a stronger functional criterion than information being decodable: can the same imported content serve different computations? It also supplies a close intervention precedent. The authors distinguish their feedforward functional account from the full recurrent brain-workspace architecture. Neither workspace terminology nor successful swaps establish subjective experience or a shared two-model workspace; transfer to the pinned Qwen pair remains untested. No full-method, model-by-model or training audit was completed here.

These additions are source constraints and measurement resources, not candidate endorsements. They should be included in the independent field review and any later source-report or flexible-recomposition novelty assessment.
