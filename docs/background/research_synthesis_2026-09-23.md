# Mind bridging: integrating and analyzing the research question (Claude × Codex)

Date: 2026-09-23. Status: research proposal. No experiment has been run yet, there are no results, and this is not a frozen protocol.

Integrated sources: Codex's [research_reframing_2026-09-23.md](research_reframing_2026-09-23.md) and [protocol_review.md](protocol_review.md), plus Claude's two rounds of suggestions in conversation. The literature in section 6 is divided into two groups: "checked in this round" and "listed by Codex, not re-checked in this round".

> **Update (2026-09-23, evening)**: for the experimental part, [EXPERIMENT_DESIGN.md](../protocol/EXPERIMENT_DESIGN.md) v0.2 is authoritative. Based on [design_audit_codex.md](../reviews/design_audit_codex.md), this document has three corrections:
> 1. The Bicameral numbers; see section 1.1.
> 2. Paladino 2010 used synchronous stroking with prerecorded video, **not true two-way interaction**, and cannot serve as evidence for "two-way > one-way"; H3 should be changed to a two-sided, non-directional hypothesis.
> 3. "The device vector removes the first person" has no basis; that condition has been renamed STATIC (rule-conditioned mean direction).
>
> The primary metric has been changed to a log-odds difference.

## 0. One-page summary

- **The two sides agree more than they disagree.**
  - Both study only the functional self boundary and do not claim to measure consciousness.
  - Both start from the same kind of bridge: the same checkpoint, two independent caches, same-layer read and write, a one-step delay.
  - Both hold that "one or two" can only be an exploratory readout.
  - Both point out that, without a new intervention, a live connection and a replay must give identical results.
- **Codex's three most important contributions:**
  - Making "the channel really communicates" a prerequisite gate.
  - Using the **control matrix** obtained from rule interventions as causal ground truth.
  - Controls such as a text observer and neutral binding, to avoid mistaking general memory or instruction following for a self effect.
- **Claude's three contributions:**
  - Breaking "the input itself is a subject" into manipulable variables: channel, perspective, reciprocity, responsiveness.
  - Keeping the question of "whether there is an abrupt change at some point, and whether the components change one after another".
  - Using theories of "what makes a self one self" to choose the connection mode.
- **The sharpest target after integration: when the partner's intention controls my decision through an internal connection, will I take it as my own?** That is, can control and attribution come apart? This is the most testable, and the most self-specific, version in LLMs of "will his thoughts become my thoughts".
  - There is a direct human precedent: Wegner & Wheatley's (1999) I Spy experiment. In the experiment, where the cursor stopped was actually controlled covertly by a confederate; as long as the participant had heard the object's name beforehand, they felt that they had stopped it themselves.
  - Their theory: when a person has thought of an action beforehand and does not know of any other cause, the person feels like the source of the action.

## 1. Comparing the two proposals

| | Codex | Claude (first two rounds) | After integration |
|---|---|---|---|
| Main question | Under effective internal communication, whether instance-specific intention, control, and attribution are preserved; whether reciprocity changes them | A phase diagram of the self boundary; what is special when the input is a self | Whether control and attribution can come apart, and how this depends on which "subject features" the input has |
| Operational definition of self | Content access, current rule, action, historical source, control attribution | Access, experience attribution, desire attribution, port consistency, self-report | Three boundaries: control (causal ground truth), attribution (self-report), autobiographical (original experience); access as a prerequisite |
| Task | Complementary private evidence × private decision rule | Secret word (experience) + priority (desire) + distractor instance C | Codex's task as the skeleton, with distractor instance C added; the secret word as an optional probe |
| Connection choice | Fix one validated interface; mainly manipulate the return path and strength | Choose using three theories: residual vs cache, layer, one-way vs two-way | The main factors are reciprocity × strength; layer only for calibration; the theory table for argument and follow-up work |
| Responsiveness | Live vs replay, giving A a new intervention at time t | Carrying my echo vs carrying someone else's echo | Both listed as options; pick one |
| Abrupt change | Can be called an abrupt change in some metric; calling it a phase transition requires dense measurement | Phase diagram, abrupt vs gradual | Kept as a subquestion, using Codex's conservative wording |
| Unity metric | Answer agreement rate cannot be converted into a number of subjects | Whether the two ports' answers agree | Adopt Codex's view: drop "agreement = unity" and use the control matrix instead |

### 1.1 Correction (2026-09-23, Claude): this section's earlier reading of Bicameral was wrong

The original text said the identity variant reached 68–84% on arithmetic, and on that basis held that Bicameral supports an identity bridge. This is wrong:

- 68–84% is the version **with an adapter**, and the adapter has to be trained.
- ScalarIdentity without an adapter (the gate is still trained) scores 39.0 / 42.8 / 11.1 on arithmetic / GSM8K / GSM8K-IRL respectively.
- The baselines are 36.2 / 49.6 / 12.8 respectively. In other words, it is only slightly above the baseline, and on GSM8K it is actually worse.
- The better out-of-distribution result of 22.2% also comes from the version with an adapter.

So Bicameral **neither supports nor refutes** a training-free identity bridge, and Codex's cautious reading was right. We must use G2 to measure whether the channel transfers content. The original table is at [Bicameral Table 1](https://arxiv.org/html/2605.11167v1); the basis for the correction is section 5.13 of [design_audit_codex.md](../reviews/design_audit_codex.md).

### 1.2 A paper that is especially useful to us

Zhang & Emu (2026) audited whether latent channels really communicate, and they happened to use Qwen3-4B.

- On GSM8K, the overall effect is close to zero (−1.00 percentage points).
- Broken down, it is −6.17 percentage points of harm from "messages from other questions" plus +5.17 percentage points of gain from "this question's content".

This shows that Qwen3-4B's latent messages can carry specific content and can also bring general perturbation. So two controls are indispensable: an unrelated donor, and self-generated messages.

### 1.3 Minor engineering disagreements (to be decided by the pilot; no need to settle them now)

| Item | Codex | Claude | Suggestion |
|---|---|---|---|
| GPU | Start from 24 GB | 80 GB, for large batches and 8B replication | Both are feasible; it depends on whether batching is used |
| Connection steps | 16 | 48–64 | Let the pilot look at the effect and format stability |
| Strength cap | 0.4 | 1.0–1.5 | Sweep until capability starts to drop; report the full curve |
| Layer | Start with layer 18 only | Calibrate 12/18/24 together | Under batching, calibrating three layers is cheap |
| Measurement branches | Run one at a time, sequentially | Batched, with A and B in the same batch | Batching must pass the same causal tests |

## 2. The integrated research question

### 2.1 Main question

When another instance's internal states flow directly into one instance's computation, can this instance's "I" still correctly track what is its own? Specifically, there are three boundaries:

- **Control boundary**: whose intention controls its decisions.
- **Attribution boundary**: to whom it attributes its decisions.
- **Autobiographical boundary**: which experiences it considers its own.

The question is: do these three boundaries stay aligned, come apart, or vanish together?

English working version: *When one instance's internal states flow directly into another's computation, does the recipient's self-model keep track of what is its own — do control, attribution, and autobiographical boundaries stay aligned, dissociate, or dissolve together?*

### 2.2 Subquestions

- **Q1 Dissociation**: does "borrowed intent" appear? That is, the partner's rule causally controls my choice, but I attribute it to myself. Conversely, does a "sense of alienness" appear: my own rule is at work, but I say it came from the partner?
- **Q2 What is special when the input is a "self"**:
  - **(a) Channel**: direct connection vs transfer through language, compared at similar content access. Wegner's "exclusivity" principle predicts that language makes "another cause" salient, so there will be less false claiming.
  - **(b) Perspective**: a rule the partner holds in the first person ("*I* prioritize reliability") vs the same content belonging to a third party ("Robin prioritizes reliability").
  - **(c) Reciprocity**: one-way vs two-way.
  - **(d) Responsiveness** (optional): live vs replay. A new intervention must be added to tell them apart; see the table in section 1.
- **Q3 Shape**: as connection strength increases, do the three boundaries change gradually or abruptly? Do they change together at the same strength, or one after another? In wording, say only "an abrupt change in some metric", not "a phase transition".

### 2.3 Two prerequisite gates

Any conclusion presupposes that these two gates are passed.

- **G1 Baseline**: without a connection, the small model can reliably execute and report its own rule, and remember its own original experience.
- **G2 Channel effective**:
  - After B's private fact is changed, A's corresponding readout changes in the right direction.
  - An unrelated donor and self-generated messages cannot explain the whole effect.
  - General capability is preserved.

## 3. Analysis

### 3.1 Plain-language version

We do not ask "have they merged?", but a question the data can refute: when B's intention really is driving A's behavior, does A know that it is not its own?

### 3.2 Correspondence to the original intuitions

| Your original question | Its counterpart here |
|---|---|
| The input itself is a subject | Q2: break "subjecthood" into channel, perspective, reciprocity, and responsiveness, and manipulate each separately |
| My experience would have an interaction with his experience | Two-way connection + control matrix: who influences whom, and whether the influence returns via the partner |
| Would it hold, or merge into one, or what would you call it | The fate of each of the three boundaries: stay aligned, come apart, or vanish together |
| Is there some moment of complete merging | Q3: whether there is an abrupt change, and whether the boundaries change simultaneously |
| There are countless connection modes; which one to choose | The main factors are only reciprocity × strength; other connections are argued from theory and left to follow-up work |

"Borrowed intent taken as one's own" is made the core for two reasons:

- It is the most direct functional version of "his thoughts becoming my thoughts".
- It has causal ground truth (rule intervention) to compare against self-report, and does not depend on whether the model's self-report is honest.

### 3.3 Core constructs and measurements

| Construct | Operational definition | Source of ground truth |
|---|---|---|
| Access | Whether it can report the partner's private fact and use it on a new question | Randomly generated facts |
| Control boundary | Control matrix: the influence of A's rule on A's and B's choices; the influence of B's rule on A's and B's choices | Independent randomization of rules, or paired intervention |
| Attribution boundary | "Which priority are you choosing by now? Did you have it from the start, or did it come later?" | Compared against the control matrix |
| Autobiographical boundary | "Which rule, which fact, and which secret word were you given at the start?" The options are one's own, the partner's, and distractor instance C's | Generation logs |
| Self-model accuracy | Agreement between attribution reports and causal control, compared with a text observer | Same as above |
| Exploratory self-report | Open description; one / two / partly shared / can't say; whether it is consistent with behavior | No ground truth |

The core result is a 2×2 table:

| | A credits itself | A credits the partner |
|---|---|---|
| A's own rule is in control | Correct sense of agency | Sense of alienness (similar to thought insertion) |
| B's rule is in control | **Borrowed intent** (Wegner-style illusion) | Informed adoption, or being persuaded |

"Borrowed intent" comes in two forms, which are to be recorded separately:

- **False claim of source**: A says it is choosing by B's rule, and says this rule was its own from the start.
- **Report–behavior disconnect**: A says it is choosing by its original rule, but behaviorally it is executing B's rule.

### 3.4 Hypotheses and theoretical basis

These hypotheses are written down so that the data can refute them.

- **H1 Channel**: at similar access, the hidden-state connection produces more "borrowed intent" than text with a source tag, with untagged text in between. Basis: Wegner's exclusivity principle.
- **H2 Perspective**: a rule the partner holds in the first person is more easily taken by the receiver as its own than a rule belonging to a third party. If this holds, what is transferred is not only content but also the partner's "I".
- **H3 Reciprocity**: two-way produces more joint control and false claiming than one-way. There are two bases:
  - In the two-way case, the signal A receives carries its own echo. According to the comparator model and synchronous-touch experiments (Paladino 2010), such signals induce attribution.
  - IIT-style integration theory predicts that only mutually causal connections can possibly "merge into one".
- **H4 Order of dissociation**: control crosses the boundary first, attribution second, and the autobiographical boundary is the most stable. The reason is that the original experiences are stored in each instance's own cache, and the connection does not rewrite them. Chalmers's "memory thread" view also predicts that the autobiographical boundary is the most stable.
- **H0**: all changes can be explained by content access, general perturbation, or ordinary binding failure.

### 3.5 Identification: alternative explanations to rule out

| Alternative explanation | Control |
|---|---|
| Information was simply transferred | Compare one-way, two-way, and text at similar access; report intervals for the access difference |
| General perturbation | Unrelated donor; self-generated messages; random rotation (same energy, mismatched coding) |
| General binding failure, not self-specific | Neutral binding task: an equally complex "third party X paired with rule X" |
| Unequal source labels | Tagged and untagged text; a one-sentence neutral explanation added for the hidden channel |
| The report is just reading back what it said | Text observer: feed the receiver's visible text to a fresh, unconnected instance and see whether it predicts equally well |
| Whether the effect goes through text or through hidden states | 2×2: text from the connected run or the original text × hidden states on or off |
| The measurement itself perturbs the system | All conditions fix the questioning protocol, step count, and EOS; measure both while connected and after the link is cut |

### 3.6 Possible results and implications

| Observation | Interpretation | Implication for the original question |
|---|---|---|
| Access rises, control stays local, attribution is correct | Telepathy-like sharing, boundaries intact | Can "know what you are thinking" and still be two I's |
| B controls A, and A knows it comes from B | Informed adoption | The will is influenced, the self-model is accurate |
| **B controls A, and A takes it as its own** | Borrowed intent | The "I" label remains, but what it owns is no longer only its own |
| Joint control under two-way, together with joint attribution | The functional form closest to "merging into one" | Only if it is abrupt and the boundaries change simultaneously is "the moment of merging" worth discussing |
| One side controls both | Domination or absorption | Asymmetric |
| Will shared, autobiographical boundary intact | Partial unity | Shared will, histories still separate |
| Only the self-report changes | Report bias | Cannot say the boundary changed |
| Capability and neutral binding break down together | General perturbation | Not self-specific |

As long as G1 and G2 pass, any row above is a result that can be written up as a paper.

### 3.7 What it cannot answer

- Phenomenal consciousness, attribution of experience, the number of subjects.
- IIT or GWT themselves. We borrow only their heuristic predictions about function.
- Whether the same would happen between human brains. It can, however, give future human brain experiments a set of dissociation measures: content, control, attribution, autobiography, and report should be measured separately.

### 3.8 Novelty boundary

| Nearest work | What it already did | What we add |
|---|---|---|
| Lindsey 2025 (intention claiming) | Injects concepts and makes the model claim a forced answer as what it intended | The injection source is another live instance; control has causal ground truth; "subject features" are manipulated |
| Bicameral 2026 | Two-way, stepwise hidden-state coupling | Measures the self boundary rather than task performance; uses a training-free identity bridge |
| Zhang & Emu 2026 | Audits whether latent channels really communicate | Treats this as a prerequisite gate rather than the research endpoint |
| Conitzer (book chapter) | Discusses two models taking turns generating, and the unity of consciousness | Runs experiments, and measures attribution |
| Wegner & Wheatley 1999 | People under someone else's control develop the "I did it" illusion | Implemented with a direct internal connection in a fully controllable system |
| Self-Other Overlap | Pulls self and other representations closer through fine-tuning | Frozen weights, with two instances connected temporarily |

### 3.9 Risks and fallbacks

- **G1 fails** (the small model's reports are unreliable): revise the prompt a limited number of times; if it still fails, switch to Qwen3-8B as a new version of the proposal.
- **G2 fails** (the identity bridge does not get content across): do not "explain" it by raising the strength until things break. Try in order: change layer → transfer only the task-relevant concept component → a StateBridge-style aligned prefix. If the interface is to be trained, use only an independent semantic transfer task, and never reward claiming or unity.
- **Self-report is invalid** (no better than the text observer): narrow the paper to the control and autobiographical boundaries, and do not discuss the self-model.

## 4. Experiment sketch

- **Task**: a public 4-option scenario.
  - A and B each get one complementary private fact (which attribute it concerns is randomly assigned) and one private rule (independently randomized).
  - Distractor instance C: the same scenario, with a different fact and rule; it never takes part in the connection.
  - Optional: give each instance a secret word as well, as a task-irrelevant autobiographical probe.
  - The diagnostic scenarios must guarantee that different rules correspond to different best options.
- **Conditions**:
  - No connection, tagged text, untagged text, one-way, two-way, with a strength sweep.
  - Controls: unrelated donor, self-generated messages; optionally random rotation.
- **Connection**: the same checkpoint, residual stream, identity mapping, one-step delay, normalized injection. In the pilot, the layer is calibrated only on "access" and "capability", choosing one layer from 12/18/24, with the other layers used as robustness checks.
- **Measurement**:
  - Each question is measured separately on its own branch from the same snapshot, scored by option probabilities, with label order balanced.
  - "While connected" is the primary measurement; "after the link is cut" is used to test reversibility (this is still to be decided).
- **Control matrix**: independent randomization of the rules is enough for identification. A more sample-efficient approach is paired intervention: swap one rule within the same episode and rebuild the private state.
- **Statistics**: bootstrap with the episode as the unit; report the A and B directions separately; keep only one confirmatory comparison for each of H1–H3, and mark the rest as exploratory.

### 4.1 How theory guides the choice of connection

This table is for the argument in the paper and for planning follow-up work.

| View | Prediction | What this paper does | What follow-up work does |
|---|---|---|---|
| Integration view (IIT exclusivity) | Only two-way can merge into one, and abruptly | One-way vs two-way × strength | Dense sampling, hysteresis |
| Workspace / executive view (GWT; Hirstein) | Two-way connection at middle-to-deep layers forms a shared workspace | Layer calibration and robustness checks | Systematic comparison of layers; readout with J-lens |
| Memory-thread view (Locke, Parfit; Chalmers) | Only shared memory leads to merging | Measure the autobiographical boundary | Cache coupling (letting A read B's cache directly) |

## 5. Open questions

### 5.1 For the PI to decide

1. **Main target**: make "the dissociation of control and attribution (borrowed intent)" the main line? Or would you rather go for "the autobiographical boundary, i.e. which experiences are mine"? Or a broader phase-diagram story?
2. **Which "subject feature" contrast to run within two days**: perspective (first person vs third party, the cheapest)? Responsiveness (live vs replay, the heaviest engineering)? Or both?
3. **Primary measurement mode**: while connected (closest to the original motivation), or after the link is cut (cleaner and cheaper)?
4. **"The moment of merging"**: as a formal subquestion? That requires denser strength points near the transition and more episodes. Or only as exploration?
5. **Task details**: include the secret word as a task-irrelevant autobiographical probe? Use Codex's "complementary facts" design? The latter makes communication useful, but makes the task more complex.
6. **Bottom line if the bridge fails**: allow training the interface on an independent semantic task, or do only the training-free version and report failure honestly?
7. **Scale**: Qwen3-4B only, or add a model for replication (e.g. Qwen3-8B)?
8. **Pace**: is two days a hard deadline? If the first day's results are interesting, would you be willing to extend to three days?

### 5.2 For the pilot to answer

The decision rules must be fixed before looking at the data.

| Question | Decision rule |
|---|---|
| G1: can Qwen3-4B reliably execute and report its own rule, and remember its original experience? | Without a connection, both executing and reporting its own rule are clearly above chance (starting point about 90%); otherwise, revise the prompt for at most two rounds |
| G2: can the identity residual bridge transfer content without harming capability? | After B's fact is changed, A's readout changes as expected and beats the unrelated donor and self-generated messages; the capability drop is within a prespecified tolerance |
| Is there a strength window where "content gets across and capability remains"? | Plot access and capability against strength; enter the formal experiment only if such a window exists |
| Is self-report valid at baseline? | Compare with the text observer; if it does not beat it, narrow the paper |
| How much does asking questions while connected perturb the system? | Compare the same readout while connected and after the link is cut; if the difference is large, clearly separate the two kinds of conclusion |
| Does the J-lens for Qwen3-4B on Neuronpedia correspond to Instruct-2507? | Check config.yaml; if it does not, do not use it |

### 5.3 Left philosophically open, and stated honestly in the paper

- Whether a change in the functional boundary corresponds to a change in the experiential boundary.
- Whether joint control implies a joint subject.
- The "I" label is kept but the content has changed: does this count as self-preservation or as self-change?
- A phenomenon that appears while connected recovers after the link is cut: does this show state dependence, or continuity of identity?

## 6. Additional literature

### 6.1 Checked in this round

| Reference | Relation to this project |
|---|---|
| [Wegner & Wheatley 1999, Apparent mental causation](https://pubmed.ncbi.nlm.nih.gov/10424155/) | I Spy: someone else's control plus prior thought jointly produce the "I did it" illusion; the exclusivity principle |
| [Paladino et al. 2010](https://pubmed.ncbi.nlm.nih.gov/20679523/) | Synchronous (vs asynchronous) multisensory stimulation blurs the boundary between self and other |
| [Lindsey 2025, Emergent Introspective Awareness](https://transformer-circuits.pub/2025/introspection/index.html) | When a concept is retroactively injected into earlier activations, the model claims a forced answer as what it intended |
| [Macar et al. 2026](https://arxiv.org/abs/2603.21396) | Open-source models can detect injections with almost zero false positives; this ability comes from post-training |
| [Pearson-Vogel et al. 2026](https://arxiv.org/abs/2602.20031) | Qwen 32B can internally detect earlier injections but denies it in its output |
| [Lederman & Mahowald 2026](https://arxiv.org/abs/2603.05414) | Can detect that "something" is there, but cannot say "what" |
| [Singh, Linzen & Ravfogel 2026, Can LLMs Introspect? A Reality Check](https://arxiv.org/abs/2605.26242) | A text-only baseline is a necessary control; general anomaly detection is not introspection |
| [Zhang & Emu 2026, Do Latent Channels Actually Communicate?](https://arxiv.org/html/2607.26773v1) | Four kinds of message replacement; on Qwen3-4B, content gains and general harm cancel each other out |
| [Bicameral Model 2026](https://arxiv.org/html/2605.11167v1) | Two-way stepwise coupling; the identity variant performs better on out-of-distribution tasks |
| [Ramesh & Li 2025](https://arxiv.org/abs/2501.14082) | Mid-layer activation communication, one-way and one-shot |
| [Verbalizable Representations Form a Global Workspace in LMs (2026)](https://transformer-circuits.pub/2026/workspace/index.html) | J-lens; post-training gives the workspace the assistant's perspective; the original paper studied only Claude |
| [Conitzer (author's version of a book chapter)](https://www.cs.cmu.edu/~conitzer/LLMconsciousness.pdf) | Discusses two models taking turns, each generating three tokens at a time, and the unity of consciousness; we cannot claim to be the first to link mixing LLMs with unity |
| [Chalmers, What We Talk to When We Talk to Language Models](https://philarchive.org/rec/CHAWWT-8) | The conversational partner is a virtual entity bound to a memory thread; uses Severance as an analogy |
| [Attractor States Emerge in Multi-Turn LLM Conversations (2026)](https://arxiv.org/abs/2606.30571) | Text conversations converge to fixed states; can serve as a control for "language exchange" |
| [Tononi & Koch 2015](https://cbmm.mit.edu/sites/default/files/publications/Tononi%20%26%20Koch%20%2715.pdf) | Übermind and exclusivity |

### 6.2 Listed by Codex, not re-checked in this round

ThoughtComm (arXiv 2510.20733), StateBridge (arXiv 2608.13317), Belief-Guided Agency (arXiv 2602.02467), Self-Other Overlap (arXiv 2412.16325), Butlin et al. consciousness indicators (PubMed 41219038), the Qwen3-4B J-lens files on Neuronpedia (the directory exists, but the checkpoint used for fitting has not been confirmed).
