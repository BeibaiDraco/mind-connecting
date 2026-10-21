# Functional connection placement and reciprocal topology

October 20, 2026. Research-design correction following the PI's explicit clarification. Documentation only; no new model run, numerical backend, scientific source, frozen protocol or parameter selector is adopted.

## The correction

The PI pointed out that two distinct questions had been conflated: which functional processes are connected, and whether they respond to each other. A sender's live state is still an input or intervention from the recipient's local perspective. That description does not make all inputs functionally equivalent or make reciprocal exchange necessary for a self-related finding.

The revised question is: how do the functional placement and form of a connection change information use, goal control and self/other attribution, and what does reciprocal responsiveness add at that connection? The two dimensions can interact. A useful one-way intervention may affect a relevant process; a two-way intervention may merely circulate irrelevant content or disruption. Neither topology establishes the function of its endpoints.

## What the current implementation actually couples

Read-only verification of `src/mb/v6_native.py` confirms that `_foreign` assembles foreign K/V for every attention module. The forward hook combines native and foreign attention as `own_out + beta * (foreign_out - own_out)`, with beta determined by attention partition sums and gain. `probe` can also consume the closing turn and question with the foreign window present. Earlier window audits identify the newest 16 generated positions as the default payload.

This is a distributed, query-dependent attention intervention on contextual states. It is not necessarily equivalent to a fixed additive steering vector, and it is not evidence of a selectively connected self module. Preserved own cache does not imply unchanged processing of own information. A particular layer number, a correct goal label or the two-way topology cannot establish the missing functional characterization.

The proposed observation window may clarify the transmitted interval, but its K/V still depend on the whole sender history. Receipt/private-work separation tests timing, not anatomical or circuit specificity. These remain useful hypotheses without resolving placement by themselves.

## Separate the questions in a small causal program

1. **Specify the target computation.** Fact use, assignment of a record to an actor, and translating an actor's maintained goal into an action are candidate roles. Use distinct behavioral tests with neutral roles as well as the acting agent. Do not assume one role occupies one layer or a small set of neurons.
2. **Characterize candidate sites independently.** Under a future approved localizer, changing one field in matched histories and patching/removing/restoring a bounded activation component could test its contribution. Retain effects on other functions and off-target ability. Readability of a fact from an activation is not causal localization, and damage from removing a component is not sufficient evidence of a specific role. Contextual patches can be off-distribution or carry several variables.
3. **Separate sender content from receiving location.** Compare matched donor-state manipulations at a fixed receiving site, and the same permitted donor state at different receiving sites. Sender and recipient sites need not be identical, but any cross-layer transformation would itself require justification and authorization. No trained interface is introduced.
4. **Cross a few characterized candidates with topology.** Compare one-way current-donor input and two-way input at fixed channel settings. Use OFF, unchanged replay and fresh open-loop sources as appropriate. Intervene after a common state to test whether new recipient changes produce new partner responses that return. Once trajectories diverge, later content is a mediator, not a nuisance that can be pretended identical.
5. **Test the self-related interpretation separately.** Measure original provenance, actual decisions and prospective influence/capability predictions. A change only in answers under a connected readout could reflect altered reporting. General record conflict, ordinary instruction following, broad impairment and visible-transcript inference remain alternatives.

A finite development scope and all candidate outcomes must be retained. Selecting the largest ownership error and then treating that same error as confirmation would be circular. The old selectors remain unchanged. Any future outcome-informed mechanism discovery needs an explicitly separate exploratory scope and untouched confirmation materials; this document does not authorize a new search.

## What an informative dissociation could look like

At one independently characterized interface, donor facts might change the recipient's knowledge while its goal-guided action and source judgments remain intact. At another, donor goal state might change actual choice while the recipient still reports its original goal. A third might mainly change source judgments with action preserved. These are possible findings, not predictions guaranteed by layer depth or by the names assigned to the interfaces.

Only then would topology contrasts tell us whether reciprocal response stabilizes, repairs, amplifies or reorganizes the particular effect. A one-way effect would remain interpretable as one-way; lack of a two-way advantage would not invalidate its existence. Conversely, more disruption under two-way input would not by itself establish richer interaction or self-boundary change.

Usable access and successful action matter for claims of useful reciprocal competence. They are not mandatory outcomes for every controlled intervention on source binding or control. General ability and intervention specificity still constrain all interpretations.

## Primary-source checks and limits of analogy

- [Blanke et al. (2002), Stimulating illusory own-body perceptions](https://www.nature.com/articles/419269a): a focal right-angular-gyrus stimulation report in one epilepsy patient includes altered bodily location/perception. This supports distinguishing intervention sites and bodily functions, not a universal self center, a privileged high-level zone or any conclusion about an LLM layer.
- [Botvinick and Cohen (1998), Rubber hands feel touch that eyes see](https://www.nature.com/articles/35784): the reported illusion links vision, touch and proprioception to bodily self-identification. This cautions against dismissing sensory processing as irrelevant to self-related phenomena. It is not a V1-to-V1 connection experiment.
- [Pais-Vieira et al. (2013), A Brain-to-Brain Interface for Real-Time Sharing of Sensorimotor Information](https://www.nature.com/articles/srep01319): uses task-specific cortical recording, a mapping to microstimulation and trained animals. It does not demonstrate a direct link between two human self systems or establish that arbitrary state sharing is sufficient.
- [Lindsey (2025), Emergent Introspective Awareness in Large Language Models](https://transformer-circuits.pub/2025/introspection/index.html): uses activation injection to test reports about injected concepts and distinguishes prior representations from text; reported effects depend on layer, strength and context. The authors retain substantial reliability and mechanistic caveats. This illustrates that steering can be an investigative method for bounded self-report questions; it does not locate a self circuit in our Qwen checkpoint or validate our bridge.

The proposed functional mapping is empirical and task-bounded. Brain regions, transformer layers and behavioral constructs are not interchangeable. No claim about phenomenal consciousness, subject count or identity fusion follows.

## Consequences for the reset

The unstarted large V6 study remains on hold. The binary task is a diagnostic scaffold, not a theory of self or a substitute for interface characterization. The reset draft now treats connection placement as a scientific dimension alongside reciprocity. Original protocols, negative controls, failed gates, third-party counterevidence and exposed developmental cases remain intact. No GPU was started or financial authorization inferred.

Documentation checks: six local references resolve and whitespace checks pass. Full offline suite: 1264 passed, 10 skipped, one GPU test deselected (44.91 seconds). No new model behavior or functional localization was tested.
