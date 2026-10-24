# Share knowledge, preserve goals

October 24, 2026. Recommendation for the PI's unsubmitted paper; no experiment or protocol is adopted.

**Focus: can internally connected instances reuse one another's knowledge for their own independently assigned tasks, without allowing the donor's different task to redirect their actions?** The strongest concrete target is useful recomposition under differing legitimate goals. A new paper should answer this comparison and explain a selective success or failure, rather than preserve the old experimental setting.

## What the literature changes

There is already substantial nearby work. Most decisively, [When Goals Leak Across Relationships](https://arxiv.org/html/2610.17365v1) studies conflicting legitimate client goals in shared cache state and causal interventions that reduce interference. Its discussion explicitly raises preserving useful shared memory while isolating client goals. The question itself is therefore not an original philosophical invention. Its reported task does not establish necessary cross-client knowledge use retained by the repair.

[Safety of Latent Communication](https://arxiv.org/html/2609.39788v1) shows that benignly trained links between frozen models can weaken refusal, and studies repair with retained utility. [Beyond Final Accuracy](https://arxiv.org/html/2610.01042) already studies correction versus corruption across communication channels. The new contribution cannot be merely that communication helps and hurts, or that a guard preserves utility. [Detailed source comparisons](sources.md) include KITE, HijackKV, cognitive studies and an inaccessible privacy-paper lead that prevents exhaustive novelty certification.

The remaining worthwhile comparison is more specific: both agents have legitimate but different objectives; the donor's private knowledge is necessary for the recipient's task; the recipient must apply it to a new input and its own contract. Neither rejecting all donor content nor copying a correct donor answer solves that problem. Two separate instances provide leverage, but the new empirical insight must come from selective use, the conditions under which it fails, and a causal explanation or selective intervention—not the instance count.

## The conceptual distinction

Shared-task success can leave two accounts indistinguishable: reusable knowledge was transferred, or the receiver adopted a donor-produced solution. Different recipient tasks force the distinction. The receiver must be sensitive to the donor's knowledge and its own task while remaining appropriately insensitive to the donor's unrelated objective.

This makes the self-related question functional and precise. Another agent's internal state can become part of the information available to me without automatically acquiring authority over what I should do. A source label and decision control are separate relations. The study does not infer consciousness or the number of subjects, and it need not establish a self-specific module. If neutral record binding explains the effect, retain that explanation.

Psychology and neuroscience provide substantive design precedents. [Gläscher et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC2895323/) separate learning transitions from assigning later rewards. [Sowden and Catmur](https://pmc.ncbi.nlm.nih.gov/articles/PMC4380005/) manipulate control of imitative interference while independently controlling spatial interference. These motivate separating shared information from the control of action and checking domain-general alternatives. They do not justify mapping an LLM layer onto a brain area. Observational learning work also shows why persistent copying cannot uniquely identify a changed goal, and registered goal-contagion work cautions that recognizing another goal is not the same as adopting it.

## A first task with an informative outcome

The [proposed routing workshop](plan.md) gives B a private dictionary of unfamiliar parcel symbols. A and B have different class-to-destination contracts established before transfer. A receives its own new parcel only after B's state is captured, and uses a separate destination-to-button map. B never knows A's answer. A must combine B's dictionary, A's contract and A's action codebook in an executed routing choice.

Change the dictionary while keeping goals fixed: appropriate A actions should change. Change A's contract while keeping knowledge fixed: appropriate A actions should change. Change only B's contract: A's correct action should stay the same. Preserve full response patterns across new inputs and button remappings, rather than reduce everything to accuracy or ask only which goal the model names.

The [logical check](recombination_check.json) shows that several distinct incorrect policies have identical average accuracy. It also proves a limit: goal-dependent factual distortion can exactly reproduce the donor-contract action map. Thus donor-task interventions identify behavioral influence, not necessarily substitution of a goal representation. A stronger mechanistic interpretation requires validated interventions on the representations that actually cause actions; correct sibling reports are insufficient.

## What would be worth publishing

A strong result could demonstrate reliable knowledge reuse while identifying a specific condition where the unrelated donor goal contaminates action selection. It could instead demonstrate a selective intervention that reduces that dependence while retaining the necessary private-knowledge benefit. A particularly informative failure would be that a richer or more accurate donor state improves shared-task performance but worsens independent-task control, with a measured account of why. These are hypotheses, not expected results or selector objectives.

Any claimed repair must keep both axes visible on the same task distribution. Eliminating all communication fails the information requirement. Nonsignificant donor-goal effects do not prove preservation; a meaningful tolerance and precision must be specified prospectively. Generic ability loss, imported facts, copied actions and misbound task rules are different explanations. No unavoidable utility/control tradeoff or identity transfer follows from this sketch.

## How the old project enters

Existing access/attribution dissociation, selective recovery, goal-label/rule mismatch and Robin interference constrain interpretations and motivate controls. They do not establish useful selective recomposition, and the old tasks do not have to be reused. Useful native communication remains a feasibility uncertainty. The immediate next decision is a small task/interface development proposal, followed by fresh confirmation only if the essential comparison can be instantiated. The frozen model/no-training constraints remain; no new GPU work is authorized.

## Prepared English delivery summary

The question is worth pursuing, but the broad phenomenon has already been studied. In particular, a recent paper shows legitimate client goals interfering through shared KV state and interventions reducing that interference. Our possible contribution is to require useful partner-only knowledge: can A use knowledge acquired in B's task to solve its own different task without adopting B's unrelated contract? A bridge that blocks everything cannot succeed. Existing latent safety work also already repairs unwanted behavior while retaining generic utility, so the new result must live in independently valid goals and necessary compositional reuse, not a renamed safety/utility tradeoff.

A concrete first design gives B a private parcel dictionary and gives A a different routing contract before transfer. A's parcel and action codebook are unavailable to B. A must combine B's knowledge with its own contract; copying B's answer cannot generally work. Independently changing knowledge, A's contract and B's contract tests appropriate information use and unwanted task influence. The logical check separates several behavioral policies but also shows that goal-dependent factual distortion can mimic donor-contract adoption. Therefore, report donor-task effects unless action-relevant mediator interventions support a stronger claim. Human learning and imitation-control studies motivate the distinction, without establishing shared neural mechanisms. The strongest paper would identify a selective capability, a structured failure boundary, or a repair retaining the required knowledge benefit. Old tasks are optional resources, not constraints. This is a conditional research direction with a concrete sketch, not certified priority or a guaranteed venue outcome.
