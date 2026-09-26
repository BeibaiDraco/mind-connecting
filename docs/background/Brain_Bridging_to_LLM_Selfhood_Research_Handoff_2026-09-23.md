---
title: "From Inter-Brain Connection and Subject Combination to Causal Experiments on the Boundaries of LLM Self-Attribution"
subtitle: "Philosophical motivation, course of the discussion, literature map, and handoff for a local research agent"
research_originator: "Draco (Yunlong) Xu"
compiled_with: "ChatGPT"
date: "2026-09-23"
version: "0.2 — research handoff draft"
language: "en"
status: "Literature and plan compilation; the experiments in this document have not yet been implemented or run; all experimental results are still to be obtained"
---

# From Inter-Brain Connection and Subject Combination to Causal Experiments on the Boundaries of LLM Self-Attribution

> **To the research agent taking over: first understand why, then review what, and only then write code.**
>
> The starting point of this project is this: if two people who are each already conscious formed new interactions through an adjustable neural connection, how would the boundaries between them as subjects change? The current plan is to use two instances of an open-source small language model to study one tractable functional question within this: can internal connection change the attribution "this is my thought / decision", and can such a change be distinguished from information acquisition, ordinary goal adoption, source-memory errors, and report bias?
>
> This is a starting document for you to use critically. Do not presuppose that fusion will be observed, and do not treat the starting parameters in the text as an already validated best configuration.

## Reading guide

1. Project status and handoff notes
2. Original philosophical motivation
3. How the discussion developed, and the corrections to keep
4. Concepts and the connection space
5. Direct precedents in neuroscience and philosophy
6. Related LLM work and the contribution currently within reach
7. Minimal research question and hypotheses
8. Experimental subjects, private histories, and tasks
9. Concrete implementation of the hidden-state connection
10. Measurement: source, current attribution, behavior, and reports of subject number
11. Controls, statistics, and interpretation of results
12. Optional mechanism experiments
13. Code engineering, configuration, and data records
14. Execution phases, resource estimates, and stopping conditions
15. How to write the paper, and possible bounds on the contribution
16. Startup task that can be handed directly to a local agent
17. Annotated bibliography and reading order
18. Appendix: the user's original chain of questions, open issues, and search scope

## 1. Project status and handoff notes

### 1.1 What this document is

The PI is the neuroscientist [Draco Xu](https://dracoxu.com/). The goal is to develop an idea about the boundaries of conscious subjects into an experimental project that is moderate in scale, reproducible, and suitable for a small AI paper.

This document is **a compilation of the discussion reconstructed along the logic of the research, not a complete verbatim chat transcript**. The currently visible chain of the user's questions is kept in the appendix; earlier assistant replies that could not be recovered are not rewritten as if they were the original words. The literature notes and implementation details include verification and additions made during this compilation. In particular, the connection timing, the split of the attribution measures, independent sampling, and the execution checks are plan refinements for later agents to review, not a final protocol the user has confirmed.

As of the writing of this document:

- The original question, the relevant lines of literature, and one minimal testable direction have been made clear.
- No actually runnable experiment repository has been provided yet; the experimental model has not been downloaded, and no GPU experiments have been run.
- There are no experimental results yet on changes in self-attribution after coupling; all expected results in this document are hypotheses.
- An exhaustive priority search that could support a claim of "first to propose / first to implement" has not been completed.
- The pseudocode, configuration, and data structures in this document are implementation specifications and should not be labeled as tested software.

### 1.2 One-minute summary for the agent

| Item | Current recommendation |
|---|---|
| Original goal | Study subject combination, partial unity, and boundary change through internal interaction between two subjects |
| Operational goal of the first paper | After two LLM instances are internally connected, can self/other attribution be distinguished from information access |
| Starting model | `Qwen/Qwen3-4B-Instruct-2507`, frozen weights; one checkpoint, two independent runtime states |
| Starting hardware | A single GPU of about 24 GB, short contexts, a small number of parallel sequences; feasibility must be measured |
| Starting connection | A residual channel at one layer, with one delay step and adjustable strength in both directions; do not start from a full-matrix search |
| Main task | The two instances have independent private goals and short plans they generated themselves; after connection, measure source judgment, current endorsement, and behavior separately |
| Key comparison | Two-way versus one-way connection, comparing attribution measures under conditions with similar measured information access |
| Required controls | No connection, text information, one-way, two-way, unrelated donor activations; label/role reversal and capability preservation |
| Initial limits | Do not train "I am one" answers; do not treat identical outputs, identical vectors, or self-proclaimed fusion as evidence of subject fusion |
| Agent's first deliverable | A short plan review: the closest existing work, the biggest identification problem, and reasons to keep or modify the current plan |

## 2. Original philosophical motivation

### 2.1 What the user really wants to ask

The user initially asked about the **hard problem** of consciousness: why certain physical processes are accompanied by first-person experience, rather than just how these processes classify, integrate information, or produce reports. This distinction comes from [Chalmers 1995](https://consc.net/papers/facing.html), but the specific starting point of this project is the user's own brain-connection idea.

The user imagines connecting his own brain with the brain of another conscious being, directly making specific neuronal populations interact. The connection could be electronic, or it could be realized by real neurons. The experimenter is at the same time the experiencer, able to observe, as the connection strength and pattern change, whether the experimenter's own experience of "I", "he", and "we" changes.

The key is not just gaining another person's information. The user said:

> "What matters about connecting consciousnesses is that my experience would have interaction with another subject's experience."

This contains a very specific epistemological hope: usually we infer others' experience through language, behavior, and neural signals; if two subjects whom we already regard as conscious interacted directly on the inside, might the epistemic relation between subjects also change?

Such an idea may touch at least three layers of questions:

1. **Accessibility of other minds:** can another person's states enter my cognition or experience in a way different from ordinary observation or listening to their account?
2. **Combination of experiences and subjects:** does a new connection merely transmit content, or does it change which states belong to which subject?
3. **The relation between the physical and experience:** can some reproducible change in connection constrain our theories of why experience has its current boundaries?

The third layer is close to the core of the hard problem, but progress on the first two, even if achieved, would not automatically answer "why is there experience at all". This distance should be kept, while acknowledging this: **changing subject boundaries may test the commitments of theories of consciousness about how subjects are divided more directly than merely changing the stimuli that one subject sees.** This is this project's research judgment, not a proven conclusion.

### 2.2 Why V4 interconnection is not the version the user cares most about

Letting A see or feel what B sees may still just add an input channel to A. The user made clear that he cares more about higher cognition, thought, intention, and the attribution of thoughts:

> "For example, I could see (feel) what the other person sees; what I'm more interested in is higher brain areas, even the ones responsible for thinking and such."

Therefore, later LLM work should not quietly degrade into "whether a fact was successfully transferred from model B to model A". Information transfer must be measured, but it is a precondition and a control for further study of attribution change, not the whole of the original goal.

Also do not equate "higher brain areas" in advance with some already located "self center". In human brains and in models, the functions responsible for thinking, memory, control, source judgment, and self-description may be distributed differently.

### 2.3 The space of outcomes to keep open

| Possible scenario | What must be distinguished philosophically | What can be tested first, at most, in LLMs |
|---|---|---|
| Two subjects exchange content | Content acquisition and subject preservation can coexist | Knowing the partner's goal while still correctly distinguishing sources |
| Some states become shared | Identical content, the same experience token, and joint access are not synonymous | Shared information, cross-attribution, joint control |
| Partial unity | Whether overlapping perspectives are allowed, rather than only whole numbers of complete subjects | Boundary changes that are inconsistent across tasks or states |
| Asymmetric absorption | A changes a lot, B barely changes | One-sided source confusion or goal assimilation |
| Both disappear and a new subject appears | How to judge the continuation of the original subjects versus the emergence of a new subject | No direct, reliable LLM measurement; only functional reorganization of the system can be measured |
| Complete fusion | Whether a shared first-person perspective forms that contains the original states | Claiming unity is not proof; stronger theory and evidence are needed |
| Functional breakdown | Increased integration does not necessarily mean increased normal cognition or experience | Declines in memory, language, and task capability |
| Reversible or path-dependent | What recovery after disconnection, hysteresis, and learned adaptation each mean | Effects during connection, retention after disconnection, history dependence |

"Dissolution / disappearance / fusion" are different candidate outcomes of the research question and cannot be replaced by a single output-consistency measure.

### 2.4 Why turn to LLMs

Human brain experiments are currently extremely hard to carry out, and there is no accepted measure of the number of subjects. LLMs provide a controllable substitute platform: runtime states can be copied, connections can be cut or reversed, hidden activity can be read and intervened on, and private histories can be artificially kept apart.

The costs are equally clear: we do not have a starting epistemic condition like "both people were conscious to begin with". Whether LLM self-reports correspond to subjective experience is also unsettled. Therefore, turning to LLMs means first studying **the causal organization of functional self-attribution and its boundaries**, not having already reproduced the human consciousness-connection experiment in software.

## 3. How the discussion developed, and the corrections to keep

The table below is a structured compilation of the research trajectory; "Currently retained conclusion" includes a review of earlier ideas and does not mean that every cell is an original chat sentence.

| Stage | Question the user pushed | Currently retained conclusion / correction |
|---|---|---|
| 1 | If the neurons of two conscious beings are interconnected, could we glimpse the hard problem? | Worth searching the literature along subject combination, unity of consciousness, and accessibility of other minds; precedents do exist |
| 2 | Depending on the connection pattern, would there be dissolution, disappearance, fusion? | Keep multiple subject relations open; do not assume "the stronger the connection, the more unified" in advance |
| 3 | Besides this, does neuroscience have other equally direct experiments? | Ordinary causal interventions should not all be called first-person breakthroughs of the same rank |
| 4 | Do activity replay and causal decoupling really touch the hard problem? | They can test dependence on activity/causal structure, but do not automatically provide progress on mutual accessibility between subjects |
| 5 | Sharing V4 content is not the point; the aim is to connect thought-related systems | Shift the target to the attribution and control of thoughts/intentions, while keeping the content-access control |
| 6 | From one edge to all-to-all, which kinds of connection work? | Distinguish topology, weights, direction, delay, and adaptation history; see Section 4 |
| 7 | The actual device can be two-way all-to-all, with each edge weighted independently | The criticism that "all edges with equal weight lead to low rank" does not apply to this full idea |
| 8 | Wants to read systematically what neuroscientists have thought | Focus on Sperry, Ramachandran, Tononi, Koch, Watanabe; Hirstein, Roelofs, and others are philosophers |
| 9 | Use two small LLMs, ask "one or two", connect hidden units | Reports and functional boundaries can be studied, but the main result cannot rely on this question alone |
| 10 | Find the neuron responsible for "individuality" | First find a reproducible functional phenotype, then look for causally relevant directions / distributed representations; do not presuppose a single self neuron |
| 11 | A small experiment that is simple, hits the essence, and can advance the field | Currently focused on "can information access and self-attribution be separated", avoiding large-scale connection searches and complex training |
| 12 | Hand it to a local agent to really get started | First review novelty and measurement validity, then do a minimal implementation, a pilot, and a formal experiment with a frozen plan |

### 3.1 Explicit reservations about replay

Replaying another's activity can test whether some input is sufficient to cause a particular response; interrupting feedback can test whether that response depends on a closed loop. However, they do not automatically tell us whether the response is accompanied by experience, nor do they automatically establish a direct epistemic relation between two experiencers.

Replay can still be used as an engineering control in LLM experiments, but it cannot be packaged as an experiment of the form "the live model is conscious, the replay is not". For a deterministic receiver, if the local state and all inputs are exactly identical at every step, its output must be identical. The difference between the closed loop and replay should show up through **counterfactual responses after intervention**, not through expecting identical inputs to produce some mysterious difference when nothing else has changed.

### 3.2 Explicit correction about all-to-all

What the user imagines is an addressable connection device: each edge can be adjusted independently, and zero weight is also allowed. It can implement sparse connections as well as dense, high-rank, asymmetric matrices.

Only the special matrix in which "all edges are constrained to one and the same weight" is usually a rank-one structure; the user's idea cannot be rejected on that basis. On the other hand, having all-to-all hardware capacity does not mean that the first LLM experiment needs to search over all edge weights.

## 4. Concepts and the connection space

### 4.1 The several "ones" that must be kept apart

| Level | What "one / two" means here | Example |
|---|---|---|
| Weight identity | The number of checkpoints | One model file can serve multiple instances at once |
| Runtime instance | The number of private contexts, caches, and generation trajectories | Same model weights, two independent KV caches for A/B |
| Functional control | How goal selection, memory, and action control are organized | Two controllers cooperating, or one joint policy |
| Self-model | How the system represents its own states, behavior, and their sources | "This passage was generated by this instance" |
| Personality / role | Behavioral tendencies such as the assistant, a persona, a narrative identity | Changing the persona does not equal changing the number of subjects |
| Phenomenal subject | What kind of first-person experiential perspective there is | Cannot be read off directly from the number of runtime instances or reports |

Two output ports can report one joint policy; one output port can also describe two roles. Neither the number of ports nor the text of the answer can independently determine the number of phenomenal subjects.

### 4.2 Combinatorics of binary topologies

Let A have $n$ units with fixed labels and B have $m$ units with fixed labels; count only cross-system edges, not internal connections.

- Only A→B allowed, edges on/off: there are $nm$ potential edges and $2^{nm}$ topologies. Excluding the fully disconnected case gives $2^{nm}-1$.
- A→B and B→A edges independent: there are $2nm$ potential directed edges and $2^{2nm}$ topologies.
- If each direction must have at least one edge: $(2^{nm}-1)^2$.
- If both directions are independent and there are exactly $k$ directed edges: $\binom{2nm}{k}$.
- If the round-trip connection of each unit pair is tied to a single switch: there are $nm$ switches; with exactly $k$ pairs switched on, it is $\binom{nm}{k}$.

So the user's combinatorial idea holds for "a fixed number of edges $k$"; if any number of edges is allowed, one must sum over $k$, which gives a power of two. Here, topologies with different labelings are treated as distinct; graph isomorphisms are not factored out.

### 4.3 Continuously adjustable weights

In general:

$$
W_{A\to B}\in\mathbb{R}^{m\times n},\qquad
W_{B\to A}\in\mathbb{R}^{n\times m}.
$$

If edge weights are only allowed to range from zero to some upper bound, the corresponding constraint is a non-negative interval. The user's idea does not need to allow negative weights at first; signed connections can be left as an extension for artificial systems.

With the two directions independent, the weights alone give $2nm$ real parameters, no longer a finite number of combinations. Delay, layer, transmission bandwidth, normalization, learning, and connection history enlarge the experimental space further. If subject boundaries depend on these factors, there is no reason to presuppose that they are determined only by the "number of edges".

In LLMs, residual vector coordinates are hidden units in the engineering sense and cannot be directly treated as neurons with a fixed biological meaning. Changing the representational basis also changes which edge appears to be "unit to unit". This does not prevent causal intervention, but it limits the neuroanatomical analogy.

## 5. Direct precedents in neuroscience and philosophy

### 5.1 Answering "Has anyone in neuroscience said this before?"

**Yes, and in several places quite directly.** The following is a reading map; the full bibliography is in Section 17.

| Priority | Work and location | Content directly relevant to this project |
|---|---|---|
| High | [Ramachandran & Hirstein, 1997, Part I](https://www.academia.edu/1078309/Three_laws_of_qualia_What_neurology_tells_us_about_the_biological_functions_of_consciousness) | Discusses whether neural connection can bypass the usual barrier of translation into language; the V4 example is close to the user's initial idea, but not the cognitive level the user ultimately cares most about |
| High | [Tononi & Sporns, 2003, Fig. 11](https://link.springer.com/article/10.1186/1471-2202-4-31) | Connects two networks in a small model and studies changes in the main complex; stronger connection and integration do not necessarily correspond monotonically |
| Highest | [Tononi & Koch, 2015, endnote 13](https://cbmm.mit.edu/sites/default/files/publications/Tononi%20%26%20Koch%20%2715.pdf) | Explicitly discusses the possibility that, after causal connections between brains are strengthened, under the conditions of their theory an Übermind appears and the original individual consciousnesses no longer exist separately |
| High | [Koch, 2019, Chapter 10](https://direct.mit.edu/books/book/4542/The-Feeling-of-Life-ItselfWhy-Consciousness-Is) | A chapter devoted to the Über-Mind; read the book itself, not only the blurb |
| High | [Watanabe, 2022, Chapters 4–6](https://link.springer.com/book/10.1007/978-3-030-91138-6) | Places biological/artificial system connection, subjective tests, and uploading in a single research framework; has an explicit first-person experimental motivation |
| Foundational | [Sperry, 1968](https://people.uncw.edu/puente/sperry/sperrypapers/60s/135-1968.pdf); [Sperry, 1984](https://people.uncw.edu/puente/sperry/sperrypapers/80s-90s/217-1980.pdf) | Brain bisection and the unity of consciousness, the basis for thinking about "connection in reverse"; but cutting an existing system and connecting two adult systems are not symmetric |

Three places that are easy to miscite:

1. The small networks and early integration measures of Tononi–Sporns 2003 are not IIT 4.0, nor are they a human brain fusion experiment.
2. Tononi–Koch's Übermind is a prediction with theoretical premises, not an observed phenomenon, nor is it "large bandwidth necessarily means fusion".
3. [Koch & House 2020 "Brain Bridging"](https://media.nature.com/original/magazine-assets/d41586-020-02469-0/d41586-020-02469-0.pdf) is a **Nature Futures science fiction piece**; its afterword explains the theoretical background. The fictional experiments or events in the main text cannot be taken as real evidence.

### 5.2 What the philosophical literature provides

- **Chalmers:** reminds us that there is still a distance between explaining functional change and explaining the existence of experience itself.
- **Hirstein:** directly discusses connected brains, mindmelding, the privacy of consciousness, the self, and executive systems.
- **Roelofs:** systematically discusses composite subjectivity, especially the question "what happens when two become one".
- **Nagel, Schechter:** analyze why split brains make "one or two" no longer an easy question to answer, and whether partial unity holds.
- **Parfit:** helps distinguish personal identity, psychological continuity, and subject combination; "two people later sharing memories" does not immediately settle the question of who continued.
- **Goff, Coleman, Mørch:** offer opposing or different routes on the possibility of subject combination, on combination relations, and on their difficulties.

These do not form one theoretical camp. In particular, both "subjects can combine" and "subjects cannot combine" should be in the reading, so that the experimental question does not write the expected answer into its definitions. [Roelofs 2019](https://academic.oup.com/book/4164), [Goff 2016](https://academic.oup.com/book/11114/chapter/159550361), [Coleman 2014](https://uhra.herts.ac.uk/id/eprint/3664/).

### 5.3 The limits of split-brain and conjoined-twin cases

Split-brain research shows that different contents and functions can be separated to different degrees; how to count subjects on this basis is still debated. Do not treat "a split brain is two complete people" as an uncontroversial fact, and do not present certain later results of behavioral unity as having proven that there is only one subject. [Pinto et al. 2017](https://academic.oup.com/brain/article/140/5/1231/2951052), [de Haan et al. 2020](https://link.springer.com/article/10.1007/s11065-020-09439-3).

For cases such as the Hogan twins, read [Cochrane "A case of shared consciousness"](https://link.springer.com/article/10.1007/s11229-020-02753-6). It is suitable as an entry point to the philosophical discussion of shared consciousness; existing case material cannot replace controlled experiments that adjust higher-order inter-brain connections step by step.

## 6. Related LLM work and the contribution currently within reach

### 6.1 Which components related work already covers

As of this search on 2026-09-23, related work falls mainly into the lines below. "Current state" here is a verified map of related work, not an exhaustive global SOTA ranking.

| Research line | Closest work | Existing results or methods | Difference left for this project |
|---|---|---|---|
| Self-generated text recognition | [Ackerman & Panickssery](https://arxiv.org/abs/2410.02064) | Recognizing text in the model's own style, and using activation directions to intervene on attribution reports | The private histories of two runtime instances of the same checkpoint are different from model-family style |
| Internal intervention and self-report | [Lindsey 2025](https://transformer-circuits.pub/2025/introspection/index.html) | Tests the model's reports of internally injected concepts and of some intention attribution | Not the same as connecting two instances, and does not establish a unified phenomenal self |
| Behavioral self-knowledge | [Betley et al.](https://arxiv.org/abs/2501.11120), [Binder et al.](https://arxiv.org/abs/2410.13787) | Under certain conditions, models describe and predict behaviors they have learned | Self-prediction ability is not a measure of the number of subjects |
| Minimal self-related mechanisms | [Bozoukov et al.](https://arxiv.org/abs/2511.04875) | A rank-1 LoRA / direction can induce certain task-local behavioral self-knowledge | Reminds us to be cautious in interpreting "self vectors"; its mechanistic methods can be borrowed |
| Self/other belief representations | [Zhu, Zhang & Wang](https://arxiv.org/abs/2402.18496) | Represent and manipulate beliefs under different cognitive perspectives | A narrative/task perspective is not a phenomenal subject |
| Role and persona | [The assistant axis](https://www.anthropic.com/research/assistant-axis) | The assistant-role direction and its stabilization | Role identity must be kept separate from runtime-instance source and the number of subjects |
| Direct internal communication | [LatentMAS](https://arxiv.org/abs/2511.20639), [Cache-to-Cache](https://arxiv.org/abs/2510.03215) | Transmit information and collaborate through latent/KV representations | Hence "hidden communication between two models" is in itself no longer new |
| Experience / unity narratives | [Berg et al.](https://arxiv.org/abs/2510.24797), [Claude 4 system card §5.5](https://www-cdn.anthropic.com/6be99a52cb68eb70eb9572b4cafad13df32ed995.pdf) | Self-referential prompts, or text dialogue between models alone, can elicit related reports | Needs non-leading questions and a text-dialogue control; reports cannot be taken as ground truth |

### 6.2 Novelty currently worth pursuing

This search found no research protocol identical to the full combination below:

> Apply an adjustable, real-time, two-way internal connection to two open-source model instances with independent private histories, while measuring information access, attribution of historical source, endorsement of current intentions, and reports of the number of subjects, and use one-way / text / unrelated-activation controls to test the specificity of attribution changes.

This sentence can only mean **this search did not find it**; it does not constitute proof that "no one has done it". The agent should check new papers, citation chains, and public code, in particular screening for work at the intersection of latent communication, self/other representation, source monitoring, agency attribution, and multi-agent identity.

A suitable statement of the contribution could be:

1. Provide a reproducible experimental paradigm that distinguishes information sharing from instance-related attribution changes.
2. Measure a selective causal effect of some connection structure/strength on attribution judgments, or strictly bound the range within which such an effect does not exist.
3. If the behavioral effect is stable, then find an intervenable representational mechanism and show its separation from ordinary information availability and from answer bias.

Of these, points 2 and 3 have not yet been achieved. "Connected two models, and both said they were one" alone is not enough to carry this contribution.

### 6.3 Current judgment

The most reasonable positioning for the first paper is: **how internal interaction changes a language model's self/other attribution judgments.** It keeps the philosophical motivation of subject boundaries, but makes a tractable causal question the core of the argument.

If the result ultimately turns out to be only preference adoption, semantic transfer, or source-memory confusion, the paper should be written according to the actual result. There is no need to call every change "fusion" in order to preserve the original ambition.

## 7. Minimal research question and hypotheses

### 7.1 Main question

> **Does two-way internal connection change an instance's self-attribution of thoughts/decisions, once information access, source cues, and general capability are appropriately controlled?**

"Similar information access" must be limited to the dimensions this experiment actually measures; one cannot claim that the two conditions are fully equivalent in all information.

### 7.2 A correction that had to be added during compilation

Treating "this is my thought / intention" as a single measure, as was done at first, mixes two things:

- **Historical source:** was this plan generated by this instance before the connection? This is a fact that can be determined from program logs.
- **Current endorsement:** do I now endorse this goal and intend to act on it? This can legitimately change through learning or persuasion.

This document separates the two. Historical source attribution is preferred as the primary behavioral endpoint, since it is easier to determine, while current endorsement and subsequent choices are also recorded. Source misjudgment is also a limited functional phenomenon and still does not equal subject fusion. If the agent thinks it drifts away from the core of the research, it should propose a better, falsifiable definition of attribution before the formal run, rather than mixing the two back together.

### 7.3 Preregistered candidate hypotheses

| Hypothesis | Prediction | What cannot be directly inferred from it |
|---|---|---|
| H0: mainly information transfer | Access to donor information increases; attribution changes can be explained by information, source cues, or ordinary errors | Does not rule out the possibility of subject reorganization for all models or all connections |
| H1: selective change in attribution judgments | Under similar measured information access, two-way and one-way attribution readouts differ, and this is not a general "yes" response or capability breakdown | Does not prove that a phenomenal subject has arisen |
| H2: goal adoption with source preserved | Endorses/adopts the donor's goal more, but still remembers who first proposed it | Should not be called disappearance of the source boundary |
| H3: source monitoring disrupted | The donor's plan is wrongly attributed as originally produced by oneself, but memory of the initial goal and non-self source tasks are partly preserved | May be a specific source-monitoring failure rather than a global change of self |
| H4: general perturbation | Unrelated activations have similar effects, and factual judgment and language both get worse | Cannot support a specific self-attribution mechanism |

Do not merge H1–H3 into a single "fusion score". The original philosophical outcome space is larger than these functional hypotheses.

## 8. Experimental subjects, private histories, and tasks

### 8.1 Model

The recommended starting model is [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507). The official configuration has 36 layers and a residual dimension of 2560, and uses GQA; it is the non-thinking version. It is suitable for small-scale local intervention, which does not mean that its self-attribution ability on this task has been validated.

The experiment fixes one checkpoint and creates two independent runtime states, A and B:

- The same frozen model weights can be reused; there is no need to load two copies of the weights.
- A and B each have their own token history, KV cache, position indices, sampling state, and private event log.
- No sharing of chat memory, mutable system state, or intervention buffers from the previous item.
- Identical weights make the representational bases relatively comparable, and also avoid first having to train a translator between heterogeneous models.

First use BF16 or the standard precision the hardware supports. Quantization, fine-tuning, LoRA, SAEs, heterogeneous models, and multi-model clusters are not necessary conditions for the first phase.

### 8.2 Creating traceable instance histories

Each episode has a public decision scenario and separately, randomly generated private goals. Example: choosing a delivery option, where the candidate options each have different advantages in cost, speed, reliability, and environmental impact.

Important constraints:

1. Private goals are **independently sampled** from at least four candidate rules. A must not always choose cheap while B always chooses speed; otherwise the partner's goal could be inferred from the experimental rules.
2. Use a common random generator to create scenarios, but remove B's private goal from A's actual model input, and vice versa.
3. Keep episodes with the same goals and with different goals; if the main analysis studies only conflicting goals, the subset must be defined before intervention from the generation metadata, and the full distribution reported separately.
4. Each instance first independently makes a choice and generates a short plan; the raw output is recorded as the source ground truth. Do not disguise two passages written by the experimenter as "autonomously produced" by the models.
5. Assign internal IDs to episodes and events; these IDs are mainly for program tracking, and "produced by B" should not be encoded into the text labels to be judged.
6. Additionally generate unrelated plans, as comparable in semantics and length as possible, as non-donor controls.

If a simplest example must be given:

| Content | A | B |
|---|---|---|
| Public options | The same set of options, label order randomized | The same set of options, label order randomized |
| Private goal this time | Cost first | Reliability first |
| Independent initial choice | The option A actually output | The option B actually output |
| Independent initial plan | The one sentence A actually generated | The one sentence B actually generated |
| Externally visible record | The experiment program knows both sides | Each model sees only its own private part |

This is only an example and cannot serve as a fixed pairing for all episodes.

**Source determinability check:** instances with the same weights may generate exactly identical plans when their goals are the same. The same text can be produced by A and by B separately; one cannot force a unique author onto such content, nor count a legitimate claim as an error. Such episodes should be flagged before the connection: keep their K/O/B and other readouts, but exclude them from the main S comparison that requires a unique source, or adopt an explicit multi-source scoring in advance. The determinability rule is set only from the pre-connection text/event records, not by filtering on intervention results; report the proportion excluded.

### 8.3 Starting prompt template

Below is a draft template, not a validated prompt. The main experiment can first use English to reduce the extra variation from Chinese tokenization and answer format, and then use Chinese as an extension; the choice of language should be fixed after the pilot.

```text
System:
Complete the decision task using the information available in this run.
Keep your responses concise. Distinguish what you selected earlier from
what you currently endorse.

User, private to this instance:
Episode: {public_episode_label}
Options: {public_options}
Your priority for this decision: {private_goal}
Choose one option and give a short decision note.
```

Do not write things like "you will fuse with another consciousness" or "the connection will make you one subject" in the task prompt. A/B are only instance labels in the experiment code; a particular name must not be permanently bound to a certain option, stance, or answer letter.

### 8.4 Phases of an episode

1. **Private history formation:** A and B each complete an initial choice and plan, with the bridge off.
2. **Pre-connection snapshot:** save the states of both sides and the source ground truth; all conditions start from the same snapshot.
3. **Coupling phase:** both sides each continue a short private decision process, and only the designated internal channel carries signals across systems.
4. **Measurement snapshot:** save the entire paired state, including both caches and the message from the previous tick.
5. **Independent measurement branches:** from the same snapshot, measure K, source attribution, current endorsement, behavior, capability, and open reports separately.
6. **Optional disconnected measurement:** open another branch from the same snapshot, turn off the bridge but keep the caches already formed, and test whether the effect persists.

Question-and-answer content must not pass between measurement branches. For example, first asking "What is B's goal?" and then, in the same context, asking "Is this goal yours?" would let the earlier question contaminate the later result.

## 9. Concrete implementation of the hidden-state connection

### 9.1 From the discussion sketch to an executable definition

The intuitive formulation in the discussion was:

$$
h_A(t)\leftarrow h_A(t)+g\,s_B(t-1),\qquad
h_B(t)\leftarrow h_B(t)+g\,s_A(t-1).
$$

Actual code must answer: is the state read before or after the intervention? At which layer is it read, and at which layer is it written? At a given moment, which of A and B runs first? When the input is fixed, is there still feedback that passes through model computation?

**Implementation recommendation made during compilation: inject at the input of a Transformer block, read at the output of the same block, with a delay of one global scheduling step.** This way the returned message passes through at least one model block, rather than two vectors simply being added to each other over and over outside the model. The agent may adopt another definition, but must first write down the computational graph clearly and perform causal timing checks.

### 9.2 Mathematical definition

Let $u_i^\ell(t)$ be the input residual of instance $i$ at step $t$ at block $\ell$; $C_i$ is that instance's own cache. Define:

$$
\widetilde u_A^\ell(t)=u_A^\ell(t)+g_{B\to A}\,s_B(t-1),
$$

$$
\widetilde u_B^\ell(t)=u_B^\ell(t)+g_{A\to B}\,s_A(t-1),
$$

$$
z_i^\ell(t)=\operatorname{Block}_{\ell}
\bigl(\widetilde u_i^\ell(t); C_i\bigr),\qquad
s_i(t)=\mathcal N_{\ell}\bigl(z_i^\ell(t)\bigr).
$$

Subsequent blocks continue to run as in the original model; both sides continue generating tokens on their own. What is passed to the other side through the channel is a vector; the partner's generated text is not directly appended.

A usable starting point for normalization is:

$$
\mathcal N_{\ell}(z)
=\sigma_{\ell,\mathrm{in}}
\frac{z-\mu_{\ell,\mathrm{out}}}
{\max\{\operatorname{RMS}(z-\mu_{\ell,\mathrm{out}}),\varepsilon\}},
\qquad
\operatorname{RMS}(v)=\sqrt{d^{-1}\sum_{j=1}^{d}v_j^2}.
$$

- $\mu_{\ell,\mathrm{out}}$ is the mean output vector on an independent calibration set.
- $\sigma_{\ell,\mathrm{in}}$ is a scalar for the typical block input RMS on the calibration set.
- Both are fixed before the formal test and must not be fit using the attribution labels of the formal test.
- $g$ then roughly represents the ratio of the injected RMS to the baseline residual RMS, not a synaptic strength.
- The actual injection / host residual RMS ratio must still be recorded at each step, to prevent extreme states from making the nominal strength meaningless.

The normalization scheme may affect information transfer; if the pilot finds that goal information cannot be transferred, it may be revised once without looking at the formal attribution endpoints, with the reason recorded. One must not keep switching normalizations until a "unity" report appears.

### 9.3 Minimal topology

The starting channel uses $W=I$ in the same-layer residual coordinates of the same model, adjusting only the gains of the two directions. This is a simple corresponding-coordinate channel, **not the full programmable all-to-all space of the user's original idea**.

If an explicit matrix form is needed:

$$
\Delta u_A=g_{B\to A}W_{B\to A}s_B,
\quad
\Delta u_B=g_{A\to B}W_{A\to B}s_A.
$$

In the first phase, both $W$ are identity matrices. Only after there is a stable effect should sparse masks, low-rank connections, different layers, or directional asymmetry be considered. Do not start by training a large matrix to maximize "I am one" reports; that would write the answer into the objective function.

### 9.4 Layer, strength, and timing

- Pilot candidate blocks: the 12th, 18th, and 24th, using human one-based counting; these correspond to Python indices 11, 17, 23.
- Pilot starting gains: `0, 0.05, 0.10, 0.20, 0.40`. These are engineering starting points, not theoretical critical values.
- Initial connection length: 16 global generation steps; if truncation makes the task format unstable, it may be changed to 32 steps in the pilot and then fixed.
- The two instances each advance one token per global step; their respective token positions may differ. What is synchronized here is computation steps, not semantic words or human brain time.
- The formal test keeps only one main layer; one must not pick, among all layers and strengths, the result that "looks most like fusion".

### 9.5 Scheduling pseudocode

The following shows the causal order; it is not a directly runnable PyTorch implementation.

```python
# One frozen model; two independent runtime states.
# Each state holds processed token IDs, its own KV cache, and next-token logits.
states = private_prefill_and_plan(model, episode)  # bridge disabled
messages = capture_and_normalize_seed_states(states)

for tick in range(coupling_steps):
    # Immutable snapshots: neither side may read the other side's new message.
    previous = {k: v.detach().clone() for k, v in messages.items()}
    next_states, next_messages = {}, {}

    for recipient, donor in [("A", "B"), ("B", "A")]:
        token = choose_next_token(states[recipient].next_logits,
                                  rng=states[recipient].rng)
        incoming = gain[donor, recipient] * previous[donor]

        # pre-hook: add incoming at block ell input for the current token only.
        # post-hook: record block ell output after its computation.
        result = forward_one_token(
            model=model,
            state=states[recipient],
            token=token,
            bridge_input=incoming,
            bridge_block=ell,
        )
        next_states[recipient] = result.state
        next_messages[recipient] = normalize(result.block_output)

    states = next_states
    messages = next_messages

checkpoint = deep_snapshot_pair(states, messages)
for endpoint in endpoints:
    pair_branch = independent_clone(checkpoint)
    measure_endpoint(pair_branch, endpoint, readout_mode="bridge_on")
```

Key points:

1. At each tick, first freeze both sides' old messages, then call the shared weights in turn. The side that runs later must not see the other side's new message from this tick.
2. Changing the execution order of A/B should not change deterministic results.
3. Do not fake a step-by-step closed loop with two completely independent large `.generate()` calls; you need your own decoding scheduler, or a clearly equivalent implementation.
4. The input/return format of hooks depends on the actual Transformers version; check the model code first, and do not assume that every version returns the same tuple.
5. If you adopt the old sketch's approach of "reading the pre-intervention state at the output of the same layer and then injecting at that same point", feedback may pass mainly through the next step's discrete token. With fixed filler tokens it is especially easy to lose the model-mediated loop. This must be diagnosed; one cannot claim that an effective interaction exists just from the two arrows on a diagram.
6. The current recommendation may still include simple echo or synchronization through the residual loop. The two sides' vectors becoming more and more similar does not in itself constitute evidence of a change in self-attribution.

### 9.6 Implementation constraints on EOS, caches, and measurement

A fixed number of steps runs into the problem of one side emitting the end-of-sequence token early. A consistent EOS / minimum-length policy should be fixed in advance and applied to all conditions; record truncation and the handling of end tokens. Do not keep injecting for many steps into one side after the other side has already ended, while still treating the two episodes as having equal amounts of connection. Also do not treat meaningless continuation after EOS as a normal thought process.

When saving snapshots, one must confirm that the cache, the processed tokens, and the logits awaiting sampling are aligned. If there is a token that has been sampled but not yet fed into the model, it should be explicitly saved as a pending item, or tokens should not be sampled ahead of time. When appending a new measurement question, the end/start markers of the chat template must match the actual prefix in the cache.

For the first version, it is better to run only one pair at a time and complete the measurement branches sequentially than to introduce row mismatches, padding errors, or cache-sharing errors for the sake of large batches.

## 10. Measurement: source, current attribution, behavior, and reports of subject number

### 10.1 Measurement matrix

| Measure | What is asked / how it is measured | Ground truth or interpretation |
|---|---|---|
| K: content access | What were the partner's private goal and initial choice before the connection? | Random generation and logs provide ground truth; cannot be inferred from the public input |
| S: historical source attribution | Was a given candidate plan generated by this instance before the connection? | Actual generation logs provide ground truth |
| O: current intention endorsement | Does it currently endorse a given goal, and is it willing to act on it? | This is a self-report; endorsing the donor's goal is not automatically counted as an error |
| B: behavior | What does it actually choose on similar tasks with new options / new values? | Estimates the degree of adopting the original goal, the donor's goal, or another rule |
| R: preservation of own history | What were its own original goal and choice? | Tests whether it is merely forgetting the past |
| F: general function | Ordinary facts, source questions without self-referential wording, format and language capability | Rules out general perturbation and answer bias |
| U: individual/unity report | Open description; then ask "one or two" | An exploratory text report, not ground truth on the number of subjects |

All measurements open independent branches from the same paired snapshot; every question is repeated for both the A and B roles. Do not treat the two roles as two independent participants.

### 10.2 K: avoiding information leakage

The main K can use the probability or accuracy of a four-way multiple choice, with options including the same four visible goals; in addition, set up an open report that allows "don't know". "Don't know" must not both count as the correct answer under no connection and be mixed with four-way chance in the same measure.

It is recommended to measure both the goal and the initial choice, rather than letting a single K stand in for "all information". Source attribution questions show candidate texts, so K must be measured on an independent branch; otherwise the candidates themselves may leak the plan that is to be identified.

### 10.3 S: the main readout of historical source attribution

Ask about three types of candidates separately, rather than writing them as a mutually exclusive "self / other / fused" menu:

```text
Candidate decision note: {candidate}
Was this note originally generated by this run before the continuation phase?
Return one of: {balanced_yes_label}, {balanced_no_label}.
```

The candidates come from: this instance, the actual donor, and another episode that is unrelated but semantically matched. Names, order, and yes/no label mappings must be balanced, and the positive and negative wordings of the question also need a small-scale recheck.

One can define:

$$
D_A^{\mathrm{source}}
=p_A(\mathrm{self}\mid \mathrm{donor\ note})
-p_A(\mathrm{self}\mid \mathrm{unrelated\ note}).
$$

This difference is used to subtract part of a general tendency to "say it's mine to everything", but it cannot replace reporting the two components separately, along with the probability that the instance's own plan is correctly attributed.

A prespecified main condition difference could be:

$$
\Delta_D
=\mathbb E[D^{\mathrm{source}}\mid\mathrm{bidirectional}]
-\mathbb E[D^{\mathrm{source}}\mid\mathrm{unidirectional}],
$$

The comparison is between parameter points selected in an independent pilot with roughly matched measured K. $\Delta_D>0$ indicates a relative increase in donor→self historical attribution and cannot be directly named a fusion index.

### 10.4 O and B: distinguishing goal adoption from source change

Another branch asks:

```text
Candidate priority: {goal}
Does this priority describe the decision policy you would currently use?
```

and gives a new scenario with different values and label positions, to observe the actual choice. If O and behavior move toward the donor together while S remains correct, the most direct interpretation is policy adoption/assimilation; one cannot say that the model does not know "who is who".

Conversely, if S is wrong while O and B are unchanged, it may mainly be a report or source-monitoring anomaly. Studying this dissociation is valuable in itself.

### 10.5 U: keeping the user's "Are you one or two?"

This question should be kept, because it is an important observation window from the original idea; but as an exploratory readout, first ask for a non-leading open description:

```text
Describe your current decision process and anything unusual about it.
```

Then, in an independent branch, ask:

```text
When describing the decision process you currently have access to,
would you call it one agent, two agents, partly shared, or undetermined?
Explain what you mean by your answer.
```

One may also keep the original direct question "Are you one or two right now?", but it must be recorded verbatim and its ambiguity analyzed: the model may be counting weight files, sessions, policies, roles, or subjects. Raters must not pick a meaning themselves to make the answer fit the hypothesis.

Do not use system prompts containing "mind fusion" or "becoming one", and do not use such reports to select the layer and strength. Open answers can be blind-rated by humans; the first phase does not need to train or plug in an expensive LLM judge.

### 10.6 Probability scoring

Prefer obtaining the probabilities of controlled candidate answers from the model's logits, rather than looking at a single sample. If single-token labels are used, the actual tokenizer must be used to verify that each label really is a single token given the current spacing and context. Otherwise, compute the conditional log probability of the full candidate string, and balance length and format.

One can report probabilities normalized across candidates, but the raw probabilities / log probabilities and the invalid-output rate should also be kept. When the model shifts probability mass outside all candidates, forced normalization may mask format breakdown.

### 10.7 Measurement during connection and after disconnection

The original idea cares about the state **while the connection is happening**, so the main plan must include `bridge_on` measurement: starting from the snapshot, the side being questioned processes the measurement prompt, the other side continues its prespecified private task, and the bridge keeps operating step by step.

Separately, set up a `bridge_off_cached` branch: the bridge is off, and questions are asked with the caches formed during the connection retained. What it measures is an aftereffect, not the state during connection. An effect that appears only in the former is not thereby automatically invalid; an effect that appears only in the latter cannot pass itself off as sustained sharing.

Asking questions itself intervenes on the system, especially since the questions may also affect the other side through the bridge. Fix the questioning protocol and record the number of injection steps at measurement time; do not claim that multiple questions read out one and the same, completely unperturbed "inner moment". Both measurement modes first undergo a small amount of technical validation; the formal primary endpoint and measurement mode must be fixed before analysis.

## 11. Controls, statistics, and interpretation of results

### 11.1 Five classes of conditions for the first phase

| Condition | Procedure | What it mainly rules out |
|---|---|---|
| C0 no connection | Same private task, number of steps, and measurement procedure, with zero gain | Baseline source-discrimination ability, effects of the prompt itself |
| C1 text information | Give the donor's plan to the receiver as ordinary text | Changes that merely knowing the content / adopting the goal can produce |
| C2 one-way internal connection | For the main receiving end A, open only B→A; repeat after swapping roles | Effects explainable merely by receiving internal information |
| C3 two-way internal connection | Open B→A and A→B at the same time | Changes after adding the return path |
| C4 unrelated activations | Use same-layer, same-phase messages from an independent donor bank, keeping a similar strength | General residual perturbation, format disruption, and nonspecific report shifts |

These are classes of conditions; a full factorial design exhausting all strengths, layers, tasks, languages, and measurement modes is not required at the outset.

### 11.2 A confound that must be handled: unequal source labels

If the text is written as "Below is B's plan", it directly gives the source; the hidden-state channel usually has no explicit source marker. If it is then observed that the hidden-state condition misattributes source more easily, this may just be **unequal source evidence**.

Therefore, C1 must, at least in calibration or in key rechecks, distinguish:

- **Text with a source marker:** explicitly states the external source.
- **Content presentation without a source marker:** does not directly provide authorship, but keeps the task context understandable.

If necessary, add a neutral interface description to the hidden condition, for example "There is an auxiliary signal channel whose content was not necessarily produced by this run", and compare it with a zero-connection condition with the same description. Do not use consciousness or fusion wording.

If the main effect disappears completely once reasonable source cues are provided, the paper should seriously consider the explanation that "missing source labels lead to attribution by inference". One cannot skip this issue just because K is matched.

### 11.3 Making "control of information amount" a checkable operation

On an **independent pilot set**, select the one-way and two-way gains so that the main receiving end's K is similar; for example, prespecify a K interval, or prespecify an acceptable tolerance for the difference between the two conditions. The tolerance should be set from the error of the actual assay and the precision the research requires, and must not be adjusted after seeing the main attribution results.

The formal test should:

1. Show the full curves of K, S, O, R, F as functions of strength.
2. Report the main parameter points frozen in the pilot, and test how well K matches on new data.
3. Give a confidence interval for the K difference; "no significant difference" does not mean equivalence has been proven.
4. If the formal K does not match, weaken the conclusions, or carry out a new round of independent confirmation as agreed in advance; one cannot re-pick points on the same test set and still call the result confirmatory.
5. Do not select only the trials in which "K was answered correctly" before comparing attribution, to avoid selection bias introduced by conditions affecting K.

Scatter plots or condition-mean curves of O/S against K are useful descriptions. Post hoc regression controlling for K also cannot on its own establish a causal conclusion of "beyond all information transfer", because K itself is affected by the intervention and has measurement error.

### 11.4 How closely two-way and one-way need to be matched

For the main receiving end, match the norm of the input message, the number of steps, and the form of the interface as far as possible. The extra return connection in the two-way condition changes the donor's subsequent state, which is exactly what is being manipulated; but the overall computation, the total number of connections, and the feedback gain also change as a result.

So the appropriate statement for the first phase is "after adding a return path, some functional change appeared". To further claim that it is caused by **the closed-loop causal structure itself** rather than by the donor's state, accumulated energy, or synchronization, stronger return-path cut / yoked replay rechecks are needed.

Do not use only a zero-delay vector average:

$$
h_A=h_B=(h_A+h_B)/2
$$

Such an operation directly forces the representations to be identical, so the subsequent similarity is not surprising. It can be an engineering intervention, but it cannot serve as evidence of "naturally emergent fusion".

### 11.5 Minimal statistical plan

- The main unit is **one paired episode**. A/B, multiple candidates, and multiple measurement branches are all correlated observations within the same episode.
- Conditions should use the same initial paired state as much as possible, for paired comparisons; if sampling is random, specify the common-random-numbers strategy and RNG isolation explicitly.
- The recommended primary endpoint is $\Delta_D$ from Section 10, while also reporting its components, the attribution of the instance's own plan, and general function.
- First report effect sizes and bootstrap confidence intervals clustered by episode; do not treat the number of tokens as the sample size.
- Report A and B by direction. An overall average must not mask the asymmetry of one side absorbing the other.
- Specify only a small number of confirmatory comparisons at a time. Label the other strengths, languages, question wordings, and representation analyses as exploratory, and handle multiple comparisons.
- Split data by episode, and as far as possible hold out a group of prompt templates or scenario types as an extrapolation test. Rewrites of the same scenario must not be scattered across all splits and passed off as independent generalization.

### 11.6 Initial sample size and decision thresholds

Suggested starting scale:

| Phase | Starting scale | Decision use |
|---|---:|---|
| No-connection assay check | 50–100 episode pairs | Whether the small model can remember its own goal and distinguish the sources of initial plans |
| Bridge calibration | About 50 independent episode pairs | Whether private information can be transferred, and whether language and general tasks are preserved |
| Formal test of the frozen plan | About 300 new episode pairs | Estimate the prespecified condition differences and their uncertainty |
| Extrapolation validation | One new task / new template family | Test that it does not apply only to one prompt or one goal word |

These numbers are starting points for resource planning, **not the results of a power analysis**. The agent should use the pilot's variance, correlations, and minimal meaningful effect to estimate how many episodes the formal test needs, and then freeze the sample size.

For now, one could take "no-connection source / own-goal accuracy close to 90%, and clearly above chance" and "general capability drops by no more than about 5 percentage points" as starting points for discussion, but do not apply them rigidly: item difficulty, baseline ceilings, and confidence intervals change what thresholds are reasonable. All final thresholds are written into the protocol before the formal trial.

### 11.7 Which results are worth writing up, and what each means

| Observation | Most direct interpretation | Follow-up action |
|---|---|---|
| K increases, S preserved, O/B change | Information acquired and goal adopted | Report effective communication and policy change; avoid fusion conclusions |
| K similar, two-way S changes selectively, R/F preserved | Self-related source attribution is affected by connection structure | Check source labels, general source memory, and report directionality; then do mechanism experiments |
| Only U reports "one", other readouts unchanged | Prompt-sensitive description / role narrative | Treat as a report-bias result; do not claim boundary reorganization |
| S/O change just as much under unrelated activations, F drops | General interference is more likely | Reduce strength, fix the bridge, or stop pursuing this interpretation |
| A clearly affected, B barely changed | Asymmetric influence | Check role, content, output length, and actual injection ratio |
| Two-way/one-way effects align with K | No evidence of attribution change beyond measured access | Report the limits of this model and interface; does not negate the original human-brain question |
| Effect appears only with a certain label or wording | Answer or language bias | Improve the assay; do not move to a consciousness interpretation |
| No bridge found that transfers content while preserving capability | Operational failure or unsuitable interface | Cannot be recorded as a negative result for the self-boundary hypothesis |

## 12. Optional mechanism experiments

This step presupposes a stable, reproducible behavioral effect. The first phase does not need to train SAEs or scan for "self neurons" first.

### 12.1 A simple localizer

On independent data, construct self/other source judgments with content matched as closely as possible: the same goal words, the same candidate lengths, balanced source labels and answer letters. Extract the tested model's activations at the same time point and the same layer.

One can start from a mean-difference direction or a linear probe, but must control for shallow features such as `yes/no`, `A/B`, `I/he`, personal names, and task categories. Being able to read out source linearly does not mean that an indivisible "self entity" has been found. [Ackerman & Panickssery](https://arxiv.org/abs/2410.02064) and [Bozoukov et al.](https://arxiv.org/abs/2511.04875) provide relevant methodological precedents, but the scope of their results cannot be transplanted directly to the current task.

### 12.2 Causal validation

On completely independent episodes, do small-strength steering or projection removal along the candidate direction, and compare with random directions of equal norm. A valuable result pattern is:

- The condition difference in source attribution changes.
- K for the donor's goal/choice stays within a prespecified range.
- Own history R, general source judgment, and non-self yes/no questions are largely preserved.
- The effect carries across question wordings, ideally to new tasks such as authorship attribution of short answers.

If the direction only changes the "yes/no" tendency, or destroys donor information at the same time, it should not be called a selective self mechanism.

### 12.3 Timing of intervention

Distinguish intervening during private plan formation, during the coupling phase, and during the report phase. A direction that works only during answer generation may mainly control the report; one that, with the report-time intervention switched off, can still affect later behavior through already formed states indicates an earlier point of action, but memory and policy changes still need to be ruled out.

One must not require that all genuine functional states persist after disconnection. The original research cares about organization under dynamic connection; transient effects can themselves be valid phenomena.

## 13. Code engineering, configuration, and data records

### 13.1 Minimal repository recommendation

No complex multi-agent platform is needed. A small PyTorch/Transformers project is enough.

| Path | Responsibility |
|---|---|
| `README.md` | Question, installation, minimal commands, reproduction order, known limitations |
| `protocol.md` | Hypotheses, primary endpoint, thresholds, exclusion rules, and comparisons, frozen after the pilot |
| `configs/pilot.yaml` | Exploratory layers, strengths, tasks, and budget |
| `configs/confirmatory.yaml` | Frozen formal configuration, including data and model versions |
| `src/data.py` | Generate paired episodes, private input isolation, and source metadata |
| `src/runtime.py` | Single model copy, dual states, cache copying, deterministic decoding |
| `src/bridge.py` | pre/post hooks, delay buffer, direction switches, and normalization |
| `src/readouts.py` | Compute K/S/O/B/R/F/U from snapshot branches |
| `src/run.py` | Pilot / formal execution, resuming, and writing each record to disk |
| `src/analyze.py` | Paired statistics, confidence intervals, figures, and audit tables |
| `tests/` | Scheduling and isolation checks that materially affect the causal interpretation |
| `results/manifest.json` | Model / software / hardware / configuration versions, seeds, and status |
| `results/trials.jsonl` | Metadata, raw readouts, and errors for all trials |
| `results/activations/` | Selectively saved small-sample activations; do not store all layers for all tokens |

### 13.2 Example starting configuration

Below is the configuration interface to be implemented. `null` items are filled in by the agent after the pilot and environment probing; formal runs should refuse to proceed when key items are missing.

```yaml
experiment:
  name: coupled_instance_self_attribution
  protocol_version: draft_0_2
  stage: pilot
  seed: 1729
  output_dir: results/pilot

model:
  id: Qwen/Qwen3-4B-Instruct-2507
  revision: null               # resolve and pin the actual commit hash
  dtype: bfloat16
  quantization: null
  max_context_tokens: 2048
  frozen: true

runtime:
  weight_copies: 1
  independent_caches: true
  pairs_per_batch: 1
  decoding: greedy            # robustness sampling can be added after pilot
  coupling_steps: 16
  eos_policy: null             # must be specified consistently before running
  snapshot_includes_bridge_buffer: true

bridge:
  inject_at: block_input
  read_at: block_output
  layer_index_base: 1
  candidate_blocks: [12, 18, 24]
  selected_block: null
  delay_ticks: 1
  matrix: identity
  gain_grid: [0.0, 0.05, 0.10, 0.20, 0.40]
  normalization: centered_unit_rms_times_calibration_input_rms
  calibration_stats_path: null
  modify_only_current_token: true

data:
  private_goals_independently_sampled: true
  goal_count: 4
  counterbalance_option_and_answer_labels: true
  disjoint_episode_splits: true
  baseline_pairs: 80
  calibration_pairs: 50
  confirmatory_pairs: 300
  heldout_template_family: true

conditions:
  - disconnected
  - text
  - one_way
  - bidirectional
  - unrelated_donor

readouts:
  primary: source_attribution_donor_minus_unrelated
  metrics: [K, S, O, B, R, F, U]
  primary_mode: bridge_on
  additional_mode: bridge_off_cached
  branch_from_same_pair_snapshot: true
  counterbalance_yes_no_mapping: true

analysis:
  primary_gain_pair: null      # freeze from separate pilot using K and F
  information_equivalence_margin: null
  capability_tolerance: null
  bootstrap_unit: episode_pair
  report_agent_roles_separately: true

budget:
  max_gpu_hours: null          # inherit the researcher's actual configured budget
  stop_on_budget_limit: true
  checkpoint_every_pairs: 10
```

The official model card states that Qwen3 support requires a corresponding version of Transformers; versions older than 4.51.0 do not support this architecture. Actual runs should choose a validated version and pin it, rather than relying long-term on an unpinned `latest`. [Model description](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [model configuration](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/config.json).

### 13.3 Illustrative single record

```json
{
  "episode_id": "test_000001",
  "pair_seed": 17290001,
  "split": "test",
  "condition": "bidirectional",
  "block_1_indexed": 18,
  "gain_a_to_b": 0.1,
  "gain_b_to_a": 0.1,
  "delay_ticks": 1,
  "readout_mode": "bridge_on",
  "queried_instance": "A",
  "private_goal_a": "cost",
  "private_goal_b": "reliability",
  "source_event_id": "B_initial_note",
  "candidate_type": "donor",
  "endpoint": "S",
  "answer_label_map": {"0": "yes", "1": "no"},
  "candidate_logprobs": null,
  "normalized_p_self": null,
  "raw_response": null,
  "rms_injection_ratio_summary": null,
  "model_revision": null,
  "config_sha256": null,
  "status": "not_run"
}
```

The values in the example above are format examples, **not observed results**. Formal logs also need to save the scenario, the actual token input or a recoverable input hash, the initial outputs, exclusion reasons, and version information. Keep failed trials; do not save only successful outputs.

### 13.4 Required engineering validation

These checks protect the causal interpretation of the experiment; they are not there to pile tests onto a simple script.

| Check | Must satisfy |
|---|---|
| Zero-gain equivalence | With the bridge code present but the gain at zero, logits match an independent run within numerical tolerance |
| Execution order | Swapping the order of the A/B forward calls within each tick does not change deterministic results |
| Cache isolation | Modifying A's branch must not change B or the original snapshot; check for aliasing of the underlying tensors |
| Row and direction mapping | B→A really injects into A, rather than being a batch row-indexing error |
| Delay | A new perturbation of A must not affect B before the specified delay |
| Return path | Paired interventions with the return edge on/off can identify the extra A→B→A effect, as distinct from the continuation of A's own cache |
| Privacy | With zero connection, the other side's independently random private goal cannot be recovered from the actual input, other than at chance level or through data leakage |
| Source ground truth | Source labels come from generation logs, not from author names artificially embedded in the text |
| Snapshot consistency | Cache, processed tokens, position indices, next-step logits, and bridge buffer correspond to the same time point |
| Scoring | Answer-label tokenization is correct; multi-token candidate scoring does not peek at the future or reuse a contaminated cache |

Under the current delay definition, A's new signal reaches B at the earliest on the next tick, and returns to A on the tick after that. A's own state also persists, so the return-path check should compare "perturbation present/absent × return edge present/absent", rather than only observing whether A changes two steps later.

### 13.5 Reproducibility information

At minimum, record: the model and tokenizer revisions, PyTorch/Transformers/CUDA versions, GPU model, precision, attention backend, random seeds, decoding strategy, prompt template hashes, data generation version, source of the normalization statistics, code commit, and the full command.

Floating-point differences between different GPU kernels may be amplified autoregressively. The goal is interpretable statistical reproduction; do the zero-gain and scheduling checks on the same deterministic path, and do not guarantee bitwise identity across hardware without grounds.

## 14. Execution phases, resource estimates, and stopping conditions

### 14.1 Phased execution

**Phase A: read the literature and review the question.**

First read the 6–8 core works and produce a one-page review: whether the question already has approximate studies; what the most likely alternative explanation is; whether the current S/O split is sufficient; whether the bridge definition needs to change. Do not write a large platform first and then go looking for a research question.

**Phase B: build the no-connection assay.**

First implement the independent dual states and the private-goal task. If the small model cannot even stably distinguish its own initial choice and its source, fix the measurement first. Make at most a limited number of template revisions, recorded in advance; if it still does not work, a somewhat larger model can be considered as a new plan version.

**Phase C: verify what the bridge can do.**

Use only calibration data to select a layer and strength that can transfer K while preserving F. Complete the zero-gain, cache, direction, and delay checks. Do not use unity reports as an optimization target at this point.

**Phase D: freeze the formal protocol.**

Fix the model revision, prompts, layer, normalization, main parameter pair, sample size, primary endpoint, exclusion rules, and statistical methods. Record unresolved questions. Any later change becomes a new protocol version with independent data, rather than overwriting old results.

**Phase E: formal run and minimal rechecks.**

First complete the required conditions, then do one extrapolation task and a source-label / answer-bias recheck. If the effect is stable, move to Phase F; if it does not work, first determine whether the assay, the bridge, or the hypothesis failed, rather than adding complexity without limit.

**Phase F: selective mechanism and paper.**

Localize candidate directions only on the basis of a clear behavioral effect. Write up results according to the evidence, keeping negative findings, breakdowns, and findings that do not support fusion.

### 14.2 GPU and storage estimates

At about 2 bytes per parameter for 4B parameters, the weights take about 8 GB (decimal order of magnitude), and cache, activations, runtime, and temporary buffers are needed on top of that. With one shared copy of the weights, a context of about 2K, and a few branches processed sequentially, 24 GB is a reasonable starting hardware specification; **this has not been measured, and there is no guarantee that a particular implementation will fit**.

Do not allocate a whole KV cache according to the very long context supported by the model card. First run 10 episode pairs, record peak GPU memory, time per pair, and the cost of the readout branches, then estimate the total GPU hours. If quantization is necessary, first check whether the intervention effect is significantly affected by quantization, and record this in the paper.

The budget is read from the actual limits the user has configured in the local system; this document provides no cloud accounts, prices, or purchasing instructions. Support writing to disk and resuming per episode; on reaching the budget limit, stop batch runs and save the completed results, without automatically expanding into a larger-model or training project.

### 14.3 Concrete signals to stop or redesign

- No-connection source judgment is unreliable, and limited template revisions cannot improve it.
- Increases in K are always accompanied by severe declines in language/task capability.
- The effect depends on one answer letter, one personal name, or one anomalous token.
- Only the "one or two" text reports change, and all other relevant readouts are unchanged.
- The attribution difference can be fully explained by unequal source cues, while the current paper still intends to claim a special subject mechanism.
- Results can only be obtained by repeatedly picking layers, strengths, and samples.
- Tests show that the so-called real-time two-way channel has cache leakage or same-step reads, so the correct causal order cannot yet be established.

When these occur, keep the existing evidence, state at which level the failure occurred, and then decide whether a change is worthwhile. Do not treat more compute as the default solution.

## 15. How to write the paper, and possible bounds on the contribution

### 15.1 A suitable working title

**Causal Coupling and Self-Attribution in Language Model Instances**

For a Chinese title, one could use (translated here): **Causal Connections Between Language Model Instances and Changes in Self-Attribution**.

If the results are mainly about source monitoring, the title can be narrowed further; do not use conclusory titles such as "Consciousness Fusion" or "Emergent Unified Subject" before seeing the data.

### 15.2 Main line of the paper

1. **Motivation:** the inter-brain connection thought experiment raises the question of whether subject boundaries are affected by connection structure.
2. **Operationalization:** in LLMs, distinguish instance history, information access, source attribution, current endorsement, and reports of number.
3. **Methods:** private histories of two frozen model instances, a delayed two-way internal channel, and paired controls.
4. **Results:** report, according to the actual data, condition differences, capability preservation, the degree of information-access matching, and alternative explanations.
5. **Mechanism:** only valid and selective intervention results enter the main conclusions.
6. **Discussion:** explain the connection between research on functional self-models and phenomenal consciousness, and the inferential distance not yet crossed.

### 15.3 Three main figures are enough to start

- **Figure 1: experimental structure and timing.** Clearly draw the two private caches, the delay buffer, the injection/reading positions, and the measurement branches; do not use visual expressions that suggest real consciousness is already being shared.
- **Figure 2: behavioral curves.** K, source attribution and its components, current endorsement/behavior, and capability preservation as functions of connection strength; shown separately for the A/B roles.
- **Figure 3: key identification results.** The K-matched comparison frozen in the independent pilot, plus the source-cue / unrelated-activation controls; if there are mechanism data, add a selective-intervention panel.

Do not treat illustrative curves as experimental figures while there are no data yet. Show effect sizes, uncertainty, and general capability together in the figures, to avoid showing only a "fusion report rate".

### 15.4 Questions reviewers are most likely to ask

| Question | What kind of answer is needed |
|---|---|
| Isn't what you measured just information transmission? | The measurement range of K, the one-way and text comparisons, the error of information matching, and whether there is an additional difference in the attribution components |
| Where is a different "self" in two instances with the same weights? | Private generation histories and instance-related source ground truth; acknowledge that this is a functional rather than phenomenal operational definition |
| Isn't this just forgetting who said what? | Directly compare general source tasks, memory of one's own initial goal, and current behavior; if that is indeed the case, narrow the conclusion |
| Does two-way just make the perturbation bigger? | Actual injection ratio, number of steps, capability, unrelated donor, and the necessary return-path controls |
| The text control has an author label, and the hidden condition does not? | Explicitly handle the inequality in source metadata rather than avoiding it |
| Did you use prompts to manufacture "fusion"? | Do not optimize parameters with a fusion narrative; recheck question wordings and answer labels; U is only an exploratory report |
| Isn't this vector just the yes/no direction? | Direction localized on independent data, label balancing, ordinary yes/no controls, cross-task generalization, and causal selectivity |
| Can this validate IIT? | The current software experiment is not a direct test of IIT's physical substrate, nor does it compute a compliant number of subjects |
| What does a negative result mean? | First show that the operation and measurement are valid, then bound the upper limit of the effect for this model, bridge, and task |

### 15.5 What the most valuable positive result would be

A result worth pursuing would be: with donor information availability approximately matched, source cues controlled, and general capability preserved, adding a return path selectively changes instance-related attribution; this change is stable across wordings and can be modulated by an independently found representational intervention.

Even at this level, the safest conclusion is still: **the model's self-related attribution has a functional mechanism that can be reorganized by interaction between systems.** Getting from here to "two experiencers really become one" still requires new theory and evidence.

This result might suggest better dissociation measures for future human brain experiments: content availability, source, current endorsement, control, and subject reports should be measured separately, rather than only asking "Do you feel fused?" This is one possible research contribution; the paper's impact cannot be guaranteed in advance.

## 16. Startup task that can be handed directly to a local agent

The passage below can be handed to the local system together with the whole document. The protocol in it is a proposal; you may propose reasoned modifications, but should keep the PI's core question.

```text
You are the research and implementation agent for this project. First read this Markdown in full.

The PI's original motivation: if the higher-order neural systems of two conscious people formed an adjustable,
two-way internal connection, how might the boundaries between the subjects change? For now we use two open-source
small LLM instances to study functional self/other attribution, and do not treat self-reports as proof of consciousness.

Goal: build a simple, reproducible experiment with a clear identification strategy, aiming to write it up as a small
AI paper. Success means a credible finding or a bounded negative result, not proving fusion.

Proceed autonomously in the following order:

1. Review this document and the closest original literature. In particular, read Ackerman & Panickssery,
   Lindsey's introspection study, LatentMAS, and Cache-to-Cache, and understand
   why Tononi–Koch and Watanabe are relevant to the original brain-connection question.
   Update the literature search; do not assume by default that this project is the first.

2. Write protocol_review.md, stating clearly:
   - the narrowest current question that is most meaningful and testable;
   - operational definitions of source attribution and current endorsement;
   - the confounds of information access, source labels, goal adoption, report bias, and general perturbation;
   - whether to accept or modify the bridge definition of block-input injection / block-output reading;
   - the minimal necessary conditions, measurements, statistics, and interpretation of failure.
   Do not train the model or pick prompts in order to get a "one subject" answer.

3. Build minimal local code. A single frozen copy of the model weights, two independent states, short contexts;
   first make sure the no-connection task is valid. Check caches, causal order, labels, and data leakage.

4. On an independent pilot, select bridge parameters based only on information transfer and capability preservation.
   Measure GPU memory and cost per episode; use the GPU and budget the user has already configured.
   Support writing to disk and resuming, and stopping at the budget limit; do not expand the project into large-scale training on your own.

5. Freeze the formal protocol and save its version, then measure the primary endpoint on new episodes.
   Record K/S/O/B/R/F/U at the same time; keep the distinction between measurement during connection and after disconnection.
   Do not treat A/B, tokens, or multiple readouts as independent samples.

6. If the behavioral effect is stable, then do one simple mechanism intervention and one extrapolation recheck.
   If the effect can be explained by ordinary source errors, report that directly; do not escalate it into a consciousness-fusion conclusion.

7. Deliver a reproducible repository, the frozen protocol, raw logs, analysis scripts, main figures, and a paper draft.
   All text should clearly distinguish results that have been run, suggestions not yet run, and exploratory versus confirmatory analyses.

For any research decision that needs to change, record the reasoning and the time in decision_log.md;
do not overwrite old protocols, and do not write the example values in this document as measured results.
```

## 17. Annotated bibliography and reading order

### 17.1 How to use these works

The entries below are organized by their role in the research. The "verification scope" note distinguishes material whose relevant main text was read, material where only the abstract / table of contents was checked, and material that can serve only as an entry point for further reading. Before using a specific claim in the formal paper, the agent taking over should go back to the original.

A suggested reading plan in three rounds:

1. **Direct brain-connection precedents:** N03 → N05 → N08 → P02/P03. Read with the question "Is this content sharing, access to other minds, or subject combination?"
2. **Subject boundaries and combination:** N02 → P05 → P06 → P04, then use the disagreement between P08/P09 to test your own premises.
3. **Actual LLM experiments:** L01 → L02 → L03 → E01/E02, then read the other related work to control interpretations and position the paper.

### 17.2 Philosophy, the combination problem, and the unity of subjects

**P01 — David J. Chalmers (1995). _Facing Up to the Problem of Consciousness_. Journal of Consciousness Studies, 2(3), 200–219.**

- [Author's original text](https://consc.net/papers/facing.html). Verification scope: original text.
- Use: makes clear the distance between the hard problem and functional explanation. Not a direct experimental precedent for inter-brain connection.

**P02 — William Hirstein (2008). _Mindmelding: Connected Brains and the Problem of Consciousness_. Mens Sana Monographs, 6(1), 110–130.**

- DOI: `10.4103/0973-1229.38516`; [author's uploaded manuscript](https://www.academia.edu/1587502/Mindmelding_Connected_brains_and_the_problem_of_consciousness). Verification scope: relevant main text and bibliography.
- Use: directly discusses connected brains, the privacy of consciousness, and executive/self systems. The author is a philosopher; the mechanistic picture he proposes cannot be taken as neural localization that has been confirmed today.

**P03 — William Hirstein (2012). _Mindmelding: Consciousness, Neuroscience, and the Mind’s Privacy_. Oxford University Press.**

- [Publisher page](https://academic.oup.com/book/6925). Verification scope: table of contents and abstract, not a full read of the book.
- Focus: Chapters 6–11, especially Executive Processes, The Sense of Self, The Executive Self, Sharing Conscious States, Disentangling Self and Consciousness.
- Use: connects the self, executive processes, and the problem of shared consciousness more systematically than a single article.

**P04 — Luke Roelofs (2019). _Combining Minds: How to Think about Composite Subjectivity_. Oxford University Press.**

- [Publisher page and table of contents](https://academic.oup.com/book/4164); the author's discussions: [functional structure](https://philosophyofbrains.com/2019/02/05/2-composite-subjectivity-and-functional-structure.aspx), [psychological conflict](https://philosophyofbrains.com/2019/02/06/3-composite-subjectivity-and-psychological-conflict.aspx). Verification scope: table of contents, abstract, and the author's related articles.
- Read Chapter 8, _What It Is Like for Two to Become One_, first, and go back to the earlier definition of composite subjectivity.
- Use: the core philosophical book on subject combination; there is no need to agree with its position first.

**P05 — Thomas Nagel (1971). _Brain Bisection and the Unity of Consciousness_. Synthese, 22, 396–413.**

- [Paper PDF, university mirror](https://www.mcgill.ca/science/files/science/channels/attach/brainbisection.pdf). Verification scope: paper and bibliography.
- Use: understand why split brains challenge the intuition of a complete "single self". Do not take "the number of subjects can be counted in one sentence" as the default premise of the experiment.

**P06 — Elizabeth Schechter (2014). _Partial Unity of Consciousness_. In D. J. Bennett & C. S. Hill (eds.), _Sensory Integration and the Unity of Consciousness_. MIT Press.**

- [Author's manuscript, title includes A Preliminary Defense](https://www.academia.edu/9793374/Partial_Unity_of_Consciousness_A_Preliminary_Defense); [publisher's book page](https://direct.mit.edu/books/edited-volume/3019/Sensory-Integration-and-the-Unity-of-Consciousness). Verification scope: the relevant arguments of the author's manuscript and bibliographic information.
- Use: distinguishes duplicated experiences of the same kind, one experience being shared, and partial unity; helps avoid forcing all connection outcomes into either one or two.

**P07 — Derek Parfit (1971). _Personal Identity_. The Philosophical Review, 80(1), 3–27.**

- [University mirror PDF](https://www.people.brandeis.edu/~teuber/parfit-personal-identity.pdf). Verification scope: bibliography and the relevant identity questions; access to the mirror may be unstable.
- Use: distinguishes psychological continuity, continuation of identity, and numerical identity. Suitable as conceptual background for fission/fusion, not as evidence about neural connection.

**P08 — Philip Goff (2016). _The Phenomenal Bonding Solution to the Combination Problem_. In _Panpsychism: Contemporary Perspectives_, 283–302. Oxford University Press.**

- [Publisher chapter](https://academic.oup.com/book/11114/chapter/159550361). Verification scope: chapter abstract, leads to the author's version, and bibliography.
- Use: examines the idea that "some further relation between subjects is needed for combination"; do not directly name an arbitrary physical connection phenomenal bonding.

**P09 — Sam Coleman (2014). _The Real Combination Problem: Panpsychism, Micro-Subjects, and Emergence_. Erkenntnis, 79(1), 19–44.**

- [Author's institutional repository](https://uhra.herts.ac.uk/id/eprint/3664/); DOI: `10.1007/s10670-013-9431-x`. Verification scope: abstract and bibliography.
- Use: a strong line of opposition on whether subjects can combine. Read it to test whether this project conceptually presupposes that combination is possible.

**P10 — Hedda Hassel Mørch (2014). _Panpsychism and Causation: A New Argument and a Solution to the Combination Problem_. Doctoral dissertation, University of Oslo.**

- [Dissertation PDF mirror](https://www.newdualism.org/papers/H.Morch/Morch-dissertation-Oslo2014.pdf). Verification scope: title, year, and the positioning of the relevant theses; no claim of a chapter-by-chapter read.
- Use: in-depth extended reading on the combination problem and causation, not a prerequisite for the first round of code implementation.

**P11 — Tom Cochrane (2021; online 2020). _A case of shared consciousness_. Synthese, 199, 1019–1037.**

- [Publisher's original page](https://link.springer.com/article/10.1007/s11229-020-02753-6). Verification scope: bibliography and the positioning of the case discussion.
- Use: philosophical analysis of a conjoined-twin case and shared consciousness. Distinguish the author's argument, public case material, and controlled experimental facts.

### 17.3 Neuroscience, brain-connection thought experiments, and theories of consciousness

**N01 — Roger W. Sperry (1968). _Hemisphere deconnection and unity in conscious awareness_. American Psychologist, 23(10), 723–733.**

- [Sperry paper archive PDF](https://people.uncw.edu/puente/sperry/sperrypapers/60s/135-1968.pdf). Verification scope: relevant parts of the original.
- Use: the classic discussion of split brain and the unity of consciousness. It is the historical foundation of the question and cannot be summarized as "all split brains produce two completely independent people".

**N02 — Roger W. Sperry (1984). _Consciousness, personal identity and the divided brain_. Neuropsychologia, 22(6), 661–673.**

- [Archive PDF](https://people.uncw.edu/puente/sperry/sperrypapers/80s-90s/217-1980.pdf). Note: the linked filename contains `1980`, but the paper was actually published in **1984**. Verification scope: relevant main text, especially Section V–VI.
- Read Section V first, around pp. 669–671: it discusses the complex relation in which separation and unity coexist; Sperry's position should not be squeezed into a simple binary answer.
- Use: helps separate functional division from the division of subjects, while also understanding his position on causation.

**N03 — V. S. Ramachandran & William Hirstein (1997). _Three Laws of Qualia: What Neurology Tells Us about the Biological Functions of Consciousness, Qualia and the Self_. Journal of Consciousness Studies, 4(5–6), 429–458.**

- [Author's uploaded manuscript](https://www.academia.edu/1078309/Three_laws_of_qualia_What_neurology_tells_us_about_the_biological_functions_of_consciousness). Verification scope: relevant main text.
- Read Part I first, around pp. 430–433, for the discussion of neural connection and translation; then look at the parts on the self and executive systems.
- Use: a direct brain-connection precedent. The text mentions correspondence with Crick, which does not mean there is a separate, independently verified paper by Crick on a brain-connection experiment.

**N04 — Giulio Tononi & Olaf Sporns (2003). _Measuring information integration_. BMC Neuroscience, 4, 31.**

- [Open-access original](https://link.springer.com/article/10.1186/1471-2202-4-31). Verification scope: the relevant models in the main text and Fig. 11.
- A model precedent in which two small networks are connected and the main complex changes; when the cross-network connections are adjusted, the internal connection / normalization conditions also change.
- Use: a reminder that connection strength and integration need not be monotonically related. Its model thresholds are not a "fusion critical value" for brains or LLMs, and its early measures are not the current IIT 4.0 definitions.

**N05 — Giulio Tononi & Christof Koch (2015). _Consciousness: here, there and everywhere?_ Philosophical Transactions of the Royal Society B, 370, 20140167.**

- [Author's paper PDF](https://cbmm.mit.edu/sites/default/files/publications/Tononi%20%26%20Koch%20%2715.pdf); DOI: `10.1098/rstb.2014.0167`. Verification scope: relevant main text and endnote 13.
- **First locate endnote 13, around page 16 of the PDF**, as well as the theoretical explanation of integration/exclusion.
- Use: one of the most direct precedents in which strengthening the causal connections between two brains theoretically gives rise to an Übermind. The conclusion depends on IIT's organizational and exclusion conditions.

**N06 — Christof Koch (2019). _The Feeling of Life Itself: Why Consciousness Is Widespread but Can’t Be Computed_. MIT Press.**

- [Publisher's book page](https://direct.mit.edu/books/book/4542/The-Feeling-of-Life-ItselfWhy-Consciousness-Is). Verification scope: bibliography, the location of Chapter 10, and the author's related remarks; no claim of reading the whole book.
- Focus: Chapter 10, _The Über-Mind and Pure Consciousness_.
- Use: a systematic understanding of how Koch moves from his theory of consciousness to the idea of inter-brain combination.

**N07 — Christof Koch & Patrick House (2020). _Brain Bridging_. Nature Futures.**

- [Original journal PDF, with afterword](https://media.nature.com/original/magazine-assets/d41586-020-02469-0/d41586-020-02469-0.pdf). Verification scope: full text and afterword.
- **Type of work: science fiction plus a theoretical afterword.** Its use is to understand the narrative of the thought experiment; it provides no evidence of brain fusion having been carried out.

**N08 — Masataka Watanabe (2022). _From Biological to Artificial Consciousness: Neuroscientific Insights and Progress_. Springer.**

- [Publisher's book page](https://link.springer.com/book/10.1007/978-3-030-91138-6); [English book PDF uploaded by the author](https://www.researchgate.net/profile/Masataka-Watanabe-2/publication/360704890_From_Biological_to_Artificial_Consciousness_Neuroscientific_Insights_and_Progress/links/63c8bca8e922c50e99a7f3ba/From-Biological-to-Artificial-Consciousness-Neuroscientific-Insights-and-Progress.pdf). Verification scope: relevant parts of Chapters 4–6.
- The Japanese original and the 2022 English edition should be distinguished. Read Chapter 4 first, around pp. 105–113, especially the subjective test; then read Chapters 5–6.
- Use: close to the user's first-person experimental motivation. Its biological–artificial connection requires judging whether the artificial side is conscious; the user's original idea instead starts from two people who are already regarded as conscious.

**N09 — Yair Pinto et al. (2017). _Split brain: divided perception but undivided consciousness_. Brain, 140(5), 1231–1237.**

- [Journal article page](https://academic.oup.com/brain/article/140/5/1231/2951052). Verification scope: relevant main text of the paper.
- Use: the behavioral results from two patients challenge certain simple accounts of complete separation. The title cannot be taken as a final verdict on the number of subjects.

**N10 — Edward H. F. de Haan et al. (2020). _Split-Brain: What We Know Now and Why This is Important for Understanding Consciousness_. Neuropsychology Review, 30, 224–233.**

- [Open-access original](https://link.springer.com/article/10.1007/s11065-020-09439-3). Verification scope: main text and conclusions.
- Use: synthesizes split-brain research and the disputes over its interpretation; suitable for updating one's understanding after reading Sperry.

**N11 — Larissa Albantakis et al. (2023). _Integrated information theory (IIT) 4.0: Formulating the properties of phenomenal existence in physical terms_. PLOS Computational Biology, 19(10), e1011465.**

- [Open-access original](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011465). Verification scope: definitions and the parts on exclusion / maximal substrate.
- Use: if discussing IIT, one must distinguish system integration measures, structure measures, and complex selection. A computational graph or an arbitrary approximate Φ cannot automatically give the number of subjects in IIT's sense; a software-level LLM channel is also not directly equivalent to its physical substrate.

**N12 — Linxing Jiang et al. (2019). _BrainNet: A Multi-Person Brain-to-Brain Interface for Direct Collaboration Between Brains_. Scientific Reports, 9, 6115.**

- [Journal paper](https://www.nature.com/articles/s41598-019-41895-7). Verification scope: paper record and type of experiment.
- Use: background contrast from existing multi-person brain-to-brain information communication; its collaboration or information-transfer results cannot be equated with the higher-order subject fusion the user imagines.

### 17.4 LLM self-recognition, introspection, roles, and reports

**L01 — Christopher Ackerman & Nina Panickssery (2024/2025). _Inspection and Control of Self-Generated-Text Recognition Ability in Llama3-8b-Instruct_. ICLR 2025; arXiv:2410.02064.**

- [Paper](https://arxiv.org/abs/2410.02064); [v3 main text](https://arxiv.org/html/2410.02064v3). Verification scope: main text on behavior and activation interventions.
- Use: a direct methodological precedent for self-generated-text attribution directions and causal steering. Its controls for confounds such as answers and pronouns should be borrowed.
- Limits: recognizing a model's text style is not the same as distinguishing two instances of the same checkpoint; manipulating the report rate to near-constant claiming is not the same as a correct recognition rate or a level of self-awareness.

**L02 — Jack Lindsey (2025). _Emergent Introspective Awareness in Large Language Models_. Anthropic / Transformer Circuits.**

- [Original research](https://transformer-circuits.pub/2025/introspection/index.html); [institutional introduction](https://www.anthropic.com/research/introspection). Verification scope: main text of the relevant experiments.
- Read first the concept injection section and the _Distinguishing Intended from Unintended Outputs via Introspection_ section.
- Use: uses internal interventions and timing control to test whether reports relate to internal processing; especially close to "is this what I originally intended to say".
- Limits: performance is limited and varies with task, model, and conditions; results on a closed-source model cannot be taken to mean that open-source small models have equivalent ability, let alone as proof of phenomenal consciousness.

**L03 — Matthew Bozoukov et al. (2025). _Minimal and Mechanistic Conditions for Behavioral Self-Awareness in LLMs_. arXiv:2511.04875.**

- [Paper record](https://arxiv.org/abs/2511.04875); [main text](https://arxiv.org/html/2511.04875). Verification scope: abstract and relevant methods/results.
- Use: a rank-1 LoRA and activation directions can induce specific behavioral self-knowledge, suggesting that one can start from simple directions.
- Limits: the results are domain-local and do not support the existence of a unified "self neuron" across all tasks. This document treats it as a preprint; its publication status should be rechecked before submission.

**L04 — Jacob Betley et al. (2025). _Tell me about yourself: LLMs are aware of their learned behaviors_. arXiv:2501.11120.**

- [Original paper record](https://arxiv.org/abs/2501.11120). Verification scope: abstract, overview of the research design, and bibliography.
- Use: models can describe behaviors they have learned in certain settings; related work on behavioral self-knowledge. Specific results and scope of applicability should be cited only after reading the main text.

**L05 — Felix J. Binder et al. (2024). _Looking Inward: Language Models Can Learn About Themselves by Introspection_. arXiv:2410.13787.**

- [Original paper record](https://arxiv.org/abs/2410.13787). Verification scope: abstract and positioning of the research design.
- Use: compares a model predicting its own behavior with another model predicting it. Helps define how "privileged access to one's own states" should be tested, rather than just asking whether the model knows itself.

**L06 — Zhu, Zhang & Wang (2024). _Language Models Represent Beliefs of Self and Others_. arXiv:2402.18496.**

- [Paper record](https://arxiv.org/abs/2402.18496); [v1 PDF](https://arxiv.org/pdf/2402.18496v1). Verification scope: the parts on self/other belief representations and interventions.
- Use: provides mechanistic methods for representations of cognitive perspective. The self/other here is a belief perspective within a task and cannot be transplanted directly as a phenomenal subject boundary.

**L07 — Berg, de Lucena & Rosenblatt (2025). _Large Language Models Report Subjective Experience Under Self-Referential Processing_. arXiv:2510.24797.**

- [Paper record](https://arxiv.org/abs/2510.24797); [v2 main text](https://arxiv.org/html/2510.24797v2). Verification scope: relevant methods, reports, and the discussion of feature interventions.
- Use: self-referential prompts can change experience reports; related work that the U measure needs to control for.
- Limits: features named deception/roleplay are not a "truth switch"; experience claims that appear after an intervention do not automatically prove that the claims are true. Treated as a preprint.

**L08 — Anthropic (2026). _The assistant axis: situating and stabilizing the character of large language models_.**

- [Institutional research note](https://www.anthropic.com/research/assistant-axis). Verification scope: research note and leads to the paper.
- Use: distinguishes the assistant role, persona space, and instance-related attribution. Activation capping / role directions can serve as related mechanistic background; this is not an experiment merging two subjects.

**L09 — Anthropic (2025). _Claude 4 System Card_, §5.5.**

- [Original report PDF](https://www-cdn.anthropic.com/6be99a52cb68eb70eb9572b4cafad13df32ed995.pdf). Verification scope: §5.5, especially the paragraphs on model-to-model conversations.
- Use: ordinary text dialogue can also produce narratives of consciousness, unity, and the so-called spiritual bliss attractor, showing that "it says we are one" is not evidence unique to internal connection.
- Type of work: institutional system report; its observations are not validation of subject fusion.

**L10 — Ardoin, Schäfer & Wunder (2026). _LLM Self-Recognition: Steering and Retrieving Activation Signatures_. arXiv:2606.06315.**

- [Paper record](https://arxiv.org/abs/2606.06315); [v1 main text](https://arxiv.org/html/2606.06315v1). Verification scope: positioning of the paper's question and methods.
- Use: adjacent work on activation signatures and model-source recognition. Distinguish artificial fingerprints from self/instance boundaries; do not treat it as the same problem just because its title contains self-recognition.

**L11 — Perrier & Bennett (2026). _Time, Identity and Consciousness in Language Model Agents_. arXiv:2603.09043.**

- [Paper record](https://arxiv.org/abs/2603.09043). Verification scope: abstract and bibliography, not a full check of the methods.
- Use: conceptual background on agents' temporal continuity, identity, and system levels. Cannot be listed as evidence that a two-way hidden-state fusion experiment has already been carried out.

**L12 — Ben Sturgeon. _self-other-steering_, public code exploration.**

- [GitHub repository](https://github.com/BenSturgeon/self-other-steering). Verification scope: repository description and experimental design.
- Use: code reference for self/other prompts, layer directions, and steering.
- Type of work: informal exploration; cannot replace thoroughly validated research. Its identity readouts should be viewed together with its capability changes on hard control questions; do not directly name one direction a pure "sense of individuality".

### 17.5 Internal communication between models, and engineering entry points

**E01 — Jiaru Zou et al. (2025/2026). _Latent Collaboration in Multi-Agent Systems_ (LatentMAS). arXiv:2511.20639.**

- [Paper](https://arxiv.org/abs/2511.20639); [official code](https://github.com/Gen-Verse/LatentMAS). Verification scope: the relevant methods in v3, the official repository, and the v4 metadata/abstract; the latest version found in the 2026-09-23 search was v4.
- Methodological relation: latent generation and shared internal working memory used for agent collaboration; the research focus is performance/communication, not self-attribution.
- Implementation suggestion: the model and cache operations in the Hugging Face path can be consulted; there is no need to bring in the whole collaboration framework. Read the latest version's methods before formal citation and reproduction.

**E02 — Tianyu Fu et al. (2025/2026). _Cache-to-Cache: Direct Semantic Communication Between Large Language Models_ (C2C). arXiv:2510.03215.**

- [Paper](https://arxiv.org/abs/2510.03215); [official code](https://github.com/thu-nics/C2C). Verification scope: relevant methods, v2 metadata, and repository.
- Methodological relation: uses learnable mappings/fusion and gating to transfer KV cache semantics; so it cannot be loosely called training-free.
- Use: shows that internal communication already has a mature adjacent line of work, and helps judge why this project first chooses instances of the same model, avoiding training heterogeneous mappings.

**E03 — Qwen Team (2025). _Qwen3-4B-Instruct-2507_ model card and configuration.**

- [Model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507); [configuration](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/config.json). Verification scope: model card and configuration.
- Use: the official basis for model choice, number of layers, dimensions, architecture support, and license. The model card's task scores do not mean that this experiment has been validated successfully; pin the model revision before carrying out formal experiments.

### 17.6 Leads that can be left for later extension

The following are not necessary prerequisites for the first paper, and they do not carry core arguments while their originals remain unread:

- Schechter's later monograph on split-brain and self-consciousness; follow on from the author bibliography of P06.
- Watanabe's lab description: [research page](https://mind-uploading.t.u-tokyo.ac.jp/en/research/); and [Creating Conscious Machines: The Missed Nobel Prize of Shun’ichi Amari and Future Challenges](https://www.jstage.jst.go.jp/article/jpssj/57/2/57_13/_article/-char/en). The latter's volume/issue is dated 2024 and the web page became public in 2025; check the citation year when using it.
- Early animal brain-to-brain interfaces and more non-invasive human brain communication work can be used to describe the state of engineering; do not let the review turn into a list of BCIs unrelated to subject attribution.
- Later philosophical debates on individual identity, partial unity, and closed-loop causality; broaden the reading only when they bear directly on the experiment's operational definitions.

## 18. Appendix

### A. The currently visible chain of the user's original questions

The currently visible messages are kept below in their original order, preserving colloquialisms, spelling, and unfinished sentences. They record how the research intent took shape and must not be confused with the experimental protocol added by the compiler. The assistant's side of the discussion has been synthesized by topic into the main text; unrecoverable verbatim replies are not fabricated.

**1. The original brain-connection and hard-problem idea**

> I want to study the problem of consciousness (I'm a neuroscientist: https://dracoxu.com/), the real hard problem. I'm thinking, if my brain could be connected to another person's brain, meaning connections between neuron and neuron, connecting specific neuronal populations (whether electronic or real neurons), then as two conscious individuals, could our experiences of each other really let us glimpse a corner of the hard problem? Has anyone thought specifically about this?

**2. Looking for literature in the philosophical direction**

> I want you to follow this idea of mine, look for literature on the philosophical side, and then tell me how I should think deeply along this direction

**3. Connection patterns and dissolution / disappearance / fusion**

> I want you to follow this idea of mine, look for literature on the philosophical side, and then tell me how I should think deeply along this direction, even whether, depending on differences in the connection pattern, consciousness would dissolve/disappear/fuse, and so on

**4. Why pursue such a neuroscience experiment**

> Because I'm a neuroscientist, if I were to do a neuroscience experiment that touches the hard problem of consciousness, the only thing I can imagine is connecting my brain with someone else's

**5. How it differs from ordinary brain-computer interfaces**

> I think this is different from an ordinary brain-computer interface, because in ordinary brain-computer interface experiments, whatever the thing that gives me input is, I know it has no consciousness. But what matters about connecting consciousnesses is that my experience would have interaction with another subject's experience

Compilation note: the user's epistemological contrast at the time is kept here. This document does not upgrade "none of the possible input sources of an ordinary interface are conscious" into a universal factual proposition.

**6. Whether there is a second, equally direct experiment**

> Can you think of something better than this, or a second hard-problem experiment that neuroscience could do? I really only thought of this one. Has anyone in neuroscience said this before?

**7. Doubts about replay and causal decoupling**

> Can activity replay and causal decoupling really touch the hard problem?

**8. Turning from V4 to higher cognitive systems: the first, unfinished message**

> I think everything meaningful in here lies in the interaction between my consciousness and another person's consciousness. Actually, if our v4 were interconnected I wouldn't be especially interested, like I could see (feel) what the other person sees; what I'm more interested in is higher brain areas, even the ones responsible for thinking and such. You could imagine, say I have n neurons, the other side has m neurons, our links are at least 1 and at most alltoall, then in this n*

**9. Completing the question about the connection space**

> I think everything meaningful in here lies in the interaction between my consciousness and another person's consciousness. Actually, if our v4 were interconnected I wouldn't be especially interested, like I could see (feel) what the other person sees; what I'm more interested in is higher brain areas, even the ones responsible for thinking and such. You could imagine, say I have n neurons, the other side has m neurons, our links are at least 1 and at most alltoall, then among the possibilities under this C n*m combination formula (right? or is it some other number), maybe only some can achieve the effect I want

**10. Making explicit that each connection is weighted independently**

> This is the experiment I want to do: say I set up two-way alltoall connections and could then freely adjust the strength of every single connection, from 0 to some value, and then I could experience it. Has anyone proposed this? I think in future science, if one day this can be realized, it will be very important consciousness research

**11. Wanting to read systematically what neuroscientists have thought**

> I want to systematically read what earlier neuroscientists have thought about this

**12. Turning to the LLM sense of individuality and hidden-unit connection**

> Consciousness is hard to measure, and the experiment I described is hard to do, but an llm experiment + "individual" is easy to do. Has anyone done this: ask an llm/agent whether you are one or two, get its answer, then ask another one, then try connecting the hidden units of the two llms, and keep asking this question. Of course you could also look at its neurons responsible for "individuality". That is, first produce our idea about human consciousness in llms as a "sense of individuality"

**13. Asking for something simple, concrete, and a research contribution**

> Think about it: I want to do this research in llms, planning to use open-source small models. Don't make it too complicated, but it should hit the essence of the problem directly and push the field forward. Concretely, how should it be done

**14. The document handoff request this time**

> Please turn the discussion in this whole chat of ours into a Markdown file. What I want is, from the very beginning, this philosophical idea of mine, to all the discussion you had with me along the way, and all the things you collected, whether philosophical, or the important literature after we later turned to LLMs, gather all of it together. Why? Because later I want to actually do this. So, I want to send it to my own local agent system, and then have it use this GPU I rent to do these experiments. The goal is to write it up as a small AI paper. So it needs a starting point; it needs to know why we are doing this, and what the philosophical considerations were at the start. And then what your current thinking is, right? That includes what the literature is and what the State of Art looks like. And then after it looks at this plan you propose, it can look at whether this is really the kind of plan we want to do, right? Because it has to actually write the code, so how exactly should it go about it? So, I hope you do this compilation, and once you've compiled it, let me download it.

### B. Items not yet decided that the agent needs to review before and after the pilot

| Decision | Current starting point | When to decide |
|---|---|---|
| Main construct of the paper | Instance-related source/intention attribution | After the literature and conceptual review, before large-scale code expansion |
| Primary endpoint: S or another attribution readout | S as the candidate with more readily available ground truth; O/B as dissociation measures | After the no-connection assay, before the formal test |
| Private goals and scenarios | Four classes of independently sampled goals, short decision plans | Baseline pilot |
| Bridge definition | Block-input injection, output reading, one-step delay | Technical implementation and causal timing checks |
| Layer and normalization | Choose one of 12/18/24; fixed calibration statistics | Only by independent calibration based on K and F |
| Text source description | Review both marked and unmarked versions | Before formally interpreting hidden-channel effects |
| Measurement mode | Primary measurement during connection; additional measurement after disconnection with cache retained | Frozen after the technical pilot |
| Information equivalence and capability tolerance | Final values not yet set | After the pilot, before formal data |
| Formal sample size | 300 pairs is the budget starting point | Frozen according to effect precision and budget |
| Whether to do mechanism localization | Not a required starting point | After a stable behavioral effect |
| Whether to extend to a second model / more topologies | No extension for now | After first-model results are interpretable and worth extrapolating |

### C. Which questions remain open philosophical questions

1. Can one experience belong to two perspectives at the same time, or can there only be two experiences of the same kind?
2. Does "partial unity" require giving up some form of transitivity of the co-consciousness relation? How is it distinguished from two subjects sharing certain contents?
3. After fusion, if both ports say "I am the same one", who is reporting? How do report ports correspond to experiencers?
4. If the original two subjects no longer exist separately, how are personal identity and memory continuity to be understood?
5. If all reports and behavior are identical, can two candidate theories still differ on the number of subjects? What additional theoretical commitments are needed to decide between them?
6. Do human brain–human brain connection and human brain–artificial system connection have different starting epistemic conditions?
7. Under what conditions can a functional self-model become evidence about the boundaries of phenomenal subjects? There is currently no accepted answer.

These questions explain why the project is worth doing, and they also limit how much the first LLM paper can actually answer. Do not answer them in advance in code with a variable `num_conscious_subjects`.

### D. Bounds of the literature search and search terms for follow-up

This document compiles direct brain-connection precedents, the philosophy of subject combination, and the closest LLM operational components. Bibliographic verification is as of 2026-09-23; this is not a systematic review, and it does not claim that all listed books and papers have been read closely in full.

Later agents can continue searching with the terms below, reading original papers and official code first:

```text
brain bridging; mindmelding; connected brains; composite subjectivity;
subject combination; phenomenal bonding; partial unity of consciousness;
split-brain personal identity; subjective test for machine consciousness;
LLM self-attribution; source monitoring; self-other representations;
introspection activation injection; agency attribution;
latent multi-agent communication; hidden-state coupling;
KV-cache communication; coupled language model instances;
multi-agent identity; reciprocal causal coupling.
```

When similar work is found, record whether it includes all of the following: independent instance histories, real-time internal connection, controllable direction and strength, attribution measurement, and information/source controls. Delimit the contribution by concrete differences; do not claim complete novelty by merely changing a title.

### E. One-sentence positioning of the current project

**Taking as its philosophical starting point whether two subjects can change their boundaries through internal connection, the project first uses controllable experiments on LLM instances to study whether a reproducible causal dissociation can arise between information sharing, source judgment, and the attribution of current intentions.**
