# Recovering the self-boundary research motivation

2026-10-20, Codex, conceptual discussion requested by the PI. Recommendations only; no new experiment, protocol, metric or research direction is adopted by this note.

## Original ambition

The motivating question is what establishes and maintains the boundary of an individual cognitive system when another evolving system participates directly in its internal processing. The brain-bridging thought experiment makes this vivid: another system's memories, reasons and responses become available while the two retain different histories and goals.

The original September framing already distinguished content access, goal control and attribution, and explicitly asked whether reciprocal responsiveness changes their relationship. Reliable communication and task performance are experimental prerequisites for this question, not the ultimate research endpoint.

Sources in the project: `docs/background/research_reframing_2026-09-23.md`, `docs/background/research_synthesis_2026-09-23.md`, and `docs/protocol/EXPERIMENT_DESIGN.md` section 1. These historical files remain unchanged.

## A useful working decomposition

For this project, distinguish knowing a fact, remembering its historical source, using a goal to control behavior, predicting which interventions would change one's behavior, and maintaining these distinctions across time. Calling all of these "self" in advance would obscure the phenomena.

Knowing another's fact need not make it autobiographical memory. Adopting a partner's suggestion need not erase its source. Being causally influenced need not mean losing independent control. Accurate attribution can accompany both adoption and resistance. A coherent self-report need not accurately describe the behavioral causal structure.

The broader experiential question remains a motivation. LLM interventions can test functional organization and its reports; the existence or number of experiential subjects does not follow from those tests.

## Candidate questions, ordered by relevance to this project

1. **Can content access, control and attribution move separately?** Establish usable partner content, intervene separately on each agent's task-relevant state, and compare actual action changes with source and influence reports. The interesting finding could be preserved provenance despite adoption, behavior changing without a corresponding attribution change, or accurate recognition of influence. Wrong answers alone do not establish a self-boundary effect.
2. **What determines the boundary: origin, current causal role, or the relationship?** Cross where content originated with whether it is currently useful or causally controlling. Compare a responsive partner and an open-loop source under interventions. Identical input to an identical deterministic state cannot reveal whether the origin was live; the test concerns responses to new counterfactual changes. A matched content-only account must remain a competing explanation.
3. **Can the system regulate what it incorporates?** Give the partner useful private evidence but a distinct goal. Test whether the recipient can use the evidence while retaining its own task commitment, and whether reports predict appropriate acceptance/rejection. Preserving a selective boundary under deep access may be more informative than wholesale disruption. Any future tasks allowing deliberate goal adoption must distinguish that permission from unwanted goal contamination.
4. **How does a shared history change later self-organization?** After a bounded interaction, compare disconnection, retained history, matched textual history and fresh states. Ask whether source attribution and control recover together, separately or remain altered. Persistence in a retained cache is a history effect; it is not weight learning or proof of a changed personal identity.
5. **Can a joint causal organization coexist with two locally distinct perspectives?** Test whether each agent's independent state remains necessary to a coordinated decision and whether local interventions still have distinct roles. Coordination, output agreement or inseparability under a particular task does not identify a single subject. This is a later question after usable reciprocal interaction exists.

The first three provide the most coherent near-term program. The fourth and fifth extend it without forcing every question into one paper.

## What makes this a study of self-related organization?

The key observations should link an agent's own maintained goals/history, its actual behavioral control and its representation of that control. A/B labels alone are insufficient. Compare equivalent third-party or neutral source/role-binding tasks, ordinary memory, instruction following and general capability. If the same phenomenon is fully explained by generic associative interference, report that result at that level.

The current small Qwen finding -- accurate own-goal labels alongside partner-sensitive own-rule errors -- is a lead for dissociation, not a demonstration that self-monitoring has failed. Own-goal reporting is not a report of causal influence; the latter has not been established by that observation.

A proposed central question is:

> When another responsive agent participates in a system's internal decision process, how are the boundaries of information access, goal control and self/other attribution maintained, dissociated or reorganized?

A useful working hypothesis is that these boundaries can vary independently and are maintained by multiple processes rather than a single identity label. This is a hypothesis, not a conclusion about minds or current models.

## Why an LLM experiment can help

Two instances can share weights while maintaining distinct histories and goals. Exact snapshots and directional interventions allow comparison of what actually affects an action with what the system reports or predicts about that influence. This makes them useful testbeds for a restricted computational question even while their relevance to human subjective selfhood remains an open issue.

The desired outcome is an explanatory distinction among mechanisms, with appropriate interventions and alternatives. A communication speedup, successful cooperation, or a striking claim of identity is not sufficient on its own.

## Literature anchors

- Gallagher (2000), [Philosophical conceptions of the self](https://pubmed.ncbi.nlm.nih.gov/10637618/): distinguishes agency, ownership and narrative continuity. This conceptual distinction motivates separate questions; it does not equate model reports with human experience.
- Wegner and Wheatley (1999), [Apparent Mental Causation](https://dtg.sites.fas.harvard.edu/DANWEGNER/pub/Wegner%26Wheatley1999.pdf), I Spy experiment: manipulates cues relevant to intentionality reports during partner-controlled stops. It provides a human precedent for separating causal control from its attribution, not a result about LLMs or a resolution of free will.

No GPU or provider action occurred. No model code or frozen design changed. This note records the discussion without selecting among the proposed questions on behalf of the PI.

Offline suite: 1264 passed, 10 skipped, one GPU test deselected (43.34 seconds). The existing untracked user image is untouched.
