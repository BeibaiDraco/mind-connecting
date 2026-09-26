# Brain Bridging × LLM Self-Boundary: Independent Adversarial Design Audit

Audit date: 2026-09-23 (America/Chicago; technical checks completed at UTC 2026-09-24). Literature search cutoff: local 2026-09-23.

Version under primary review: [EXPERIMENT_DESIGN.md](/Users/minidraco/mind-connecting/EXPERIMENT_DESIGN.md), 429 lines, SHA256: `3f67127f709748ff1a43d6ac343a4257090aed700f8fb3134a2b9fbff56b8027`. All section and line numbers below refer to this version. The main design was read in full and reviewed together with research_synthesis, AGENTS, PLAN and the original handoff documents. Several reservations in the original handoff documents about replay, source labels and measurement during connection should still be kept.

This audit only created this audit file; it did not modify any existing project file, and did not download model weights, instantiate the model or run the model. It completed checks of the official config, source code and tokenizer, plus pure mathematical calculations. The latest constraints are applied as "one week, only Qwen3-4B-Instruct-2507, no training of weights or interfaces"; the 0.6B, 8B and second-model options in older documents are no longer considered within the authorized scope.

## 1. Overall conclusion: can it be frozen and launched after revision

**The current version should not be frozen as a confirmatory experiment. After revision, a clearly scoped exploratory-plus-confirmatory study that can be completed in about one week can be launched, but a strong positive result or a complete, conference-level mechanistic conclusion within one week cannot be promised.**

The most valuable and most testable question is: **after another instance's private content enters through an internal channel, do content use, behavioral choice and original source attribution dissociate; and does adding a feedback path change this relationship.** This question does not require first proving that an LLM is conscious, nor does it require treating the model's secret word as its complete identity.

Three key gaps at present:

1. SMI is a meaningful difference-based descriptive quantity, but it does not automatically subtract general steering; an identical answer-logit bias can also produce a positive SMI of more than 5 percentage points.
2. ONE–DEV and ONE–LANG each change several properties at once, and cannot yet identify the independent effects of "coming from a subject" and "directness". ONE–TWO at the same gain can identify the total effect of adding a return path, but this is not the same as a pure interaction effect under fixed information.
3. Reading the question with the bridge kept open changes the state, the injection dose and the feedback content. At the same time, cache branching, chat terminators and the per-token clock are not yet defined precisely enough to admit a unique implementation.

Recommendation: keep the original motivation, and limit the verifiable claim of the first paper to "**source attribution and behavioral change in same-weight instances with different histories under internal communication**". "Subjecthood", "first-person experience" and "merging into one" are kept as motivation or follow-up questions.

"Blocking" here means blocking the current main conclusions or the formal freeze; it does not mean that every issue must get a measured model answer before renting a GPU. Before renting a GPU, the protocol, tokenizer, scheduling contract and pure program tests can be completed; after renting, first run small-scale correctness and communication-validity checks, and only after they pass move on to the formal sample.

Note on cost: the person-hours below are rough implementation orders of magnitude, not guarantees; "one condition" means one experimental arm at a frozen parameter point, which can usually share existing private-phase snapshots. GPU hours cannot be given precisely without profiling.

## 2. Blocking issues

### B1. SMI is not sufficient to identify "self-specificity", and its promise to subtract general bias is wrong

**What the problem is.** §3.4, §8 and §13 (especially L276, L390) interpret `SMI = ΔP(START=partner) − ΔP(START-R=partner)` as already handling general answer bias. The two questions differ in baseline, retrieval cues, task relevance, number of rehearsals and pronoun framing, so a probability difference offers no such guarantee.

A counterexample that can be recomputed without the model: add the same 1 to only the partner label's logit on both questions, with no self-specific manipulation at all. If the original probability is p, the new probability is `e·p/(1−p+e·p)`:

| Question | Baseline partner probability | After intervention | Increment |
|---|---:|---:|---:|
| START | 0.05000 | 0.12516 | 0.07516 |
| START-R | 0.01000 | 0.02672 | 0.01672 |

SMI = **0.05844**, exceeding the planned minimum effect of 0.05. The baseline correct probabilities on both questions can still both exceed 0.90, so the existing C0 exclusion rule cannot rule out this counterexample.

**Why it matters.** The primary endpoint may mistake softmax nonlinearity, different memory strengths or first-person reference bias for a self-attribution mechanism. One's own rule is an instruction to execute and is generated repeatedly in the note/C; Robin's rule is a side fact. START also has the "at the very beginning" qualifier, which START-R lacks. If B's "I/my" state selectively affects the "you" question, that may be merely reference binding and does not prove a change in a higher-level sense of self.

**How to fix it concretely.** Keep SMI, but rename it "partner misattribution increment relative to the third-party question" and delete "general steering already excluded". The four raw probabilities, the correct-answer probabilities and the label mass must be reported alongside. Have START-R likewise ask about "the priority assigned at the start of the task", balance the order in which facts are presented and the question length, and report differences in rehearsal history. Add a sensitivity metric that needs no new forward pass: for each label permutation compute `L_q = log P(partner) − log P(answer of the correct source for this question)`, then compute `ΔL_START − ΔL_START-R`, and finally average across permutations. Under the narrow assumption that "the partner logit of both questions increases by the same constant and other logits are unchanged", this cancels that bias; it still cannot rule out context-dependent steering.

A further minimal construct check is a small crossed design: the same receiver answers about its own facts both with "you" and with its own neutral alias; the third party is also referred to by a neutral alias; and symmetric facts about two third parties test general source binding. This partly separates pronoun sensitivity from association with one's own source, but no single paired question can handle every confound.

**Cost.** The mathematical metric and raw-component reporting take about 1–2 hours with no new inference; balancing the questions takes about half a day; the pronoun/alias check can be done only at g* and on a small subsample, adding about 2–4 kinds of readout.

**PI decision needed: yes.** The PI needs to accept the interpretive limits of the primary metric; the technical renaming, component reporting and temporal-qualifier fix need no separate decision.

### B2. DEV has not been shown to have "removed the first person", nor is it an independent manipulation of subjecthood

**What the problem is.** §1.2 and §6.4 interpret `E[m|r] − E[m]` as removing individuality, the secret word and the first person. Suppose the message contains `m = a + b_r + c_(r,self) + ε`; centering at most removes the additive a that is constant across rules; the rule × self interaction term remains. Per-sample RMS normalization makes the simple additive-cancellation interpretation even less reliable. A conditional mean over 60 episodes also does not guarantee that the secret word, Robin or scene information cancel out completely. ONE itself also first applies `z−μ_out`; one cannot use two opposite interpretations for the same centering operation.

**Why it matters.** ONE–DEV simultaneously changes time variation, context, specific content, secret-word availability, noise, temporal correlation and feedback adaptivity. Even if ACC-rule is the same, the difference cannot be attributed to "coming from a subject". More fundamentally, in ONE, if a device replays exactly the same messages tick by tick, the receiver's state and inputs are identical, so a deterministic run should be identical. Changing only the signal's "source identity", which is invisible to the receiver, has no identifiable effect. This is consistent with §3.1 of the original handoff document.

**How to fix it concretely.** Rename DEV to `STATIC-RULE` or "rule-conditional mean direction"; downgrade H-subject to "the difference between a dynamic instance state and a static rule direction", without claiming the absence of a subject. To test the first-person frame, use first-person-holder / third-person-describer messages matched in content, length and timing; even if they differ, that only supports a framing effect. Time shuffling tests temporal dependence; another instance with the same rule tests instance-specific content; replay of a real trajectory tests online adaptivity. These three controls each answer a different question, and none is automatically a pure "self-free device". The first paper need not do all of them.

**Cost.** Renaming and narrowing the claim take about 1 hour, no compute; adding one dynamic control takes about half a day to implement plus one g* condition. A full factorial design usually exceeds a one-week budget.

**PI decision needed: yes.** Decide whether the first paper accepts a comparison of "ways of constructing the signal"; if identifying subjecthood is insisted on, the current paradigm cannot solve it just by replacing the DEV vector.

### B3. "Directness" is not separated from source labels, payload and presentation timing

**What the problem is.** §4.4 and §9 use ONE vs LANG-tag to identify directness. LANG supplies a text note with a source, while ONE inputs a continuously changing C/R state; the two differ in source cues, amount of content, input timing, text length and rule/secret-word payload. The existing note is also not guaranteed to contain the secret word.

**Why it matters.** Even if LANG has higher access and less misattribution, this can be explained by the explicit source label. After `LANG-untag` deletes the author name, the note still sits in an external user message as "Here is a note", so not all evidence of an external source is removed. Similar ACC-rule does not prove equivalence of semantic content, ACC-word or source-label evidence.

**How to fix it concretely.** In the first paper, explicitly call ONE–LANG-tag "an overall comparison between an internal live-state bridge and a text input with a source"; keep LANG-untag as a key sensitivity control at g*. The comparison needs an explicit content payload: if conclusions involve WORD, the text condition should explicitly convey the same private word; otherwise the comparison does not explain channel differences. If a causal directness claim is insisted on, at least cross channel × external-source cue, giving the hidden condition a neutral source statement paired with a C0 that has the same statement; align content and availability timing. This still requires acknowledging that text and activations are not the same kind of physical dose.

**Cost.** Narrowing the claim and adding the payload definition take about 2–4 hours; untag was already planned, so just keep it; the full crossing adds about 2–3 parameter-point conditions, about half a day of engineering plus extra inference.

**PI decision needed: yes.** Decide whether to keep the overall comparison or pay the extra design cost for an independent directness claim.

### B4. Reading the question while connected measures the answering process under ongoing intervention, and cannot be taken directly as the attribution state already present at the end of C

**What the problem is.** §4.3, §5.3, L266: while the tested side reads the question token by token, the donor keeps generating and the bridge keeps injecting. Question length equals the number of extra injection steps; TWO also sends the question, candidate rules and secret word out via A→B and back via B→A. Label permutation also changes the feedback trajectory. SMI cannot remove these influences.

**Why it matters.** A positive SMI can be content/answer steering during question reading, not a wrong source memory already formed in phase C; asymmetric questions also produce asymmetric intervention doses. Although multiple snapshot branches start from the same state, this does not mean the same latent state was measured without perturbation.

**How to fix it concretely.** Report both FULL and RF at g*, and designate one primary endpoint before the formal experiment: if the goal is "how answers behave during the connection", FULL can remain primary, but the claim must carry the ongoing intervention; if the goal is "the connection has already changed source binding", RF is recommended as primary with FULL as key secondary. **Quietly substituting RF for the original online question is not recommended.** First balance paired questions on tokenizer length; artificial padding cannot replace semantic balancing. Keep R-only (RO) at key points to locate immediate readout sensitivity.

RF keeps the intervened cache, so it can only test "whether the effect can still be read out after new injection is turned off". FULL−RF is neither an assumption-free decomposition of pure measurement bias nor reversibility; the two go through different R dynamics.

**Cost.** Defining and implementing the readout modes takes about half a day; RF does not need the donor to stay active, so it is usually cheaper than FULL, but cache-branching cost must be counted. Both modes can be run only at the main point, to avoid doubling the whole g grid.

**PI decision needed: yes.** Which one answers the paper's primary question, the online effect or the effect after the link is cut, must be chosen in advance; both should be kept.

### B5. The current G2 is not sufficient to show that the bridge transmits donor-specific content

**What the problem is.** §10 only requires ACC above SCRAM with CAP preserved. A random orthogonal rotation can destroy the effective coordinates of the representation, so SCRAM is not a control of "same natural distribution but unrelated content"; ACC can also be raised by elimination, general answer bias or induction from the candidate options.

**Why it matters.** If it has not been shown that the donor's private content has a specific causal effect on the receiver, later attribution changes cannot be described as "caused by the inflow of another instance's content". A recent latent-communication audit has shown that "corrupting the cache degrades performance" and "the paired content is actually used" are two different things. See [When Does Latent Communication Pay?](https://arxiv.org/html/2608.04893).

**How to fix it concretely.** Add `MISMATCH`: keep the same layer, same phase and the natural message distribution, but use another donor whose content clearly does not match; save the targets of both the real and the substituted donor, and test whether the output moves with the content actually injected. A stronger and cheap option is, on a small subset, to fix A, Robin, the public scene and the candidate words, and change B's random private mapping/rule, as a paired counterfactual. Under without-replacement rules, do not resample Robin at the same time, or the B intervention becomes bundled with third-party content. At least one access question should require random private evidence that cannot be inferred from the public scene.

Calibration parameters are still chosen only by communication and capability metrics, without looking at attribution results. If the bridge does not pass the content-specificity and capability-preservation gate, stop the "self-boundary" confirmatory trial; the interface failure can be reported, but it cannot be interpreted as the self-boundary being unbreakable.

**Cost.** Natural donor mismatch takes about half a day of engineering; done only at candidate g* and in a small pilot, it adds about 1–2 control conditions. It can replace SCRAM's full strength grid, so net compute may go down.

**PI decision needed: no; this is a necessary validity check for the main causal conclusion.** If the gate cannot be passed as a result, a decision is needed on whether to accept an interface-failure result or postpone the project.

### B6. The per-token and cache contracts contain ambiguities that can change the experimental treatment

**What the problem is.** §4, §6.1 and §12 do not yet uniquely specify the following behaviors: how the donor "continues reflecting" after `im_end` has been appended to C; whether the snapshot includes the last token that has been generated but not yet consumed; whether the first C token is generated from bridge-free prefill logits; whether, after R's short row finishes, the donor in the same group keeps being advanced; whether branches copy the mailbox; whether the hook treats a Tensor as a tuple.

**Why it matters.** Errors of this kind create invisible extra tokens, wrong delays, cross-branch contamination and extra feedback that varies with question length, enough to produce all the main effects. They do not necessarily make the program raise an error. In particular, in newer Qwen3DecoderLayer versions `output[0]` may take the first row of the batch rather than the hidden-state field.

**How to fix it concretely.** First pin the Transformers version and write a state contract: one tick is a forward pass that consumes one input token; record, for each side, the valid KV length, position IDs, pending token/logits, old/new mailbox, phase and completion status. A paired snapshot of "C content consumed, terminator not yet appended" can be used: the tested side fully closes the assistant message and then reads the question, while the donor stays in the original assistant segment and continues writing; the other receiver gets a separate branch. Switching to giving the donor a new prompt after both sides finish is also acceptable, but it must be acknowledged as a different protocol.

For the first implementation, prefer bucketing by question length or small batches, making sure pad does not advance the pair's logical clock, the donor or the mailbox. `crop()` is not a full snapshot restore; parallel branches need independent caches/state. After the hook reads, assert `[batch,1,2560]`; first write from all old mailboxes, then commit this tick's new messages together. §6 gives the verified version differences.

**Cost.** Offline state-machine and shape tests take about half a day to one day; after renting, run small-scale consistency checks with the single designated 4B model; the run volume is small, and debugging time is likely the main cost. These tests must not be skipped on the grounds that "averaging over a large sample will cancel it out".

**PI decision needed: no.** This is correct implementation; only changing the bridge's operational definition or the donor task requires confirming the research implications.

### B7. The confirmatory estimands, score definitions and actual questions are not yet frozen

**What the problem is.** §7–10 do not give the complete English questions, the word pool or the definition of the primary probability. In ONE only A receives, in TWO there are two receivers, yet A/B are required to be reported separately and a Holm correction is applied to "three" tests. It is unclear whether there are three or six primary tests; it is also unclear whether `P` is the raw full-vocabulary probability or the probability normalized over the four labels.

**Why it matters.** Different reasonable implementations will yield different SMI values, sample sizes and significance conclusions. The uninjected B in ONE and the receiver B in TWO cannot be treated directly as symmetric conditions. Without complete templates, length, leakage and label boundaries cannot be verified, and the protocol cannot be called frozen.

**How to fix it concretely.** For the one-week version, prespecify A as the primary receiver, with the three parameter-point comparisons forming one Holm family and TWO's B as prespecified description/exploration; if it is claimed that both directions replicate, add a role-swapped ONE and either average within episode or put the six tests into the same family. The main table gives both the raw label probabilities and the probabilities conditional on the four candidates; if a single primary P is needed, choose the raw next-token probability, with the conditional probability as a sensitivity analysis, so that forced normalization does not look confident after format collapse. Keep low-label-mass records in the log and in the main denominator; samples must not be deleted based on good post-treatment performance.

Before the formal freeze, complete all questions, the word pool, the label-mapping rules, the split, the state contract and the statistics functions. Bridge parameters are chosen by ACC/CAP only; if the variance of the pilot's attribution contrasts is used for sample-size planning, the protocol needs a separate rule, "used only for sample size, not for choosing layers/gains/prompts", together with a maximum N, to avoid contradicting the existing no-peeking rule.

**Cost.** The template/analysis contract takes about half a day; choosing A as the primary endpoint adds no compute. Running ONE in both directions adds inference for the corresponding arms; tokenizing the complete questions needs no GPU.

**PI decision needed: yes.** The primary direction, the primary probability quantity and the sample budget should be frozen; the rest is necessary implementation detail.

## 3. Important issues

### I1. ONE–TWO at the same g is valid, but the directional prediction and the "access matching" interpretation are too strong

**What the problem is.** In TWO, B has already been influenced by A; under an approximately linear intuition, what A receives contains `g·B₀ + g²·A₀ + …`. This is only illustrative, not an exact expansion of the Transformer. The echo can reinforce own, and need not lead to more partner false claiming. Only DEV was matched on pilot ACC; TWO and LANG were not.

**Why it matters.** The same-g comparison is the total effect of "adding a return path"; the change in donor content is a mediator of this treatment and should not be blanket-labeled a confound that invalidates the total effect. But it cannot support "an interaction effect with access held constant".

**How to fix it concretely.** Keep the same-g total-effect comparison, and change it to a two-sided hypothesis. Additionally calibrating different g values on the pilot so that ACC-rule is close within a commonly reachable range can serve as a second treatment-combination comparison; on the formal sample report the difference interval or a prespecified equivalence bound, and do not treat non-significance as successful matching. If WORD enters the conclusions, ACC-word must also be considered; a static rule vector may not be able to match both at once. If there is no common range, acknowledge that matching is impossible. Do not filter the formal sample episode by episode on ACC, re-pick points, or run a simple regression and then claim the amount of information has been fixed.

**Cost.** Reinterpretation and reporting cost almost nothing; the matching grid adds roughly a few pilot points. **PI decision needed: yes, decide whether the total effect is the primary interaction question.**

### I2. "The partner is different" and without-replacement assignment reduce the uncertainty of the access questions

**What the problem is.** A, B and Robin have mutually distinct rules, and A knows its own and Robin's. Merely knowing that the partner differs from itself eliminates one option; if the without-replacement mechanism can be learned/inferred, Robin is eliminated too, leaving only two options. The four-choice questions do not have a uniform 25% no-information chance level. The secret-word options may also expose an eliminable structure.

**Why it matters.** Apparent access may be mere inference, and the effective conditional entropy of the rule content is very low. Telling the model that another participant exists also means the answer to "how many agents" in U may just restate the scene setup.

**How to fix it concretely.** Keeping the neutral "there is another participant" is enough; delete the unnecessary "different from you" cue; still compute the no-information/elimination baseline from the actual generation distribution, and use C0 as the empirical baseline. A cleaner extension is independent assignment with a predefined conflict-subset analysis; then episodes with different sources but the same rule cannot identify the source by rule, and an independent code word should be used. U serves only as a prompt-influenced description, not as a measure of the number of subjects.

**Cost.** Text and chance baseline take about 2–3 hours, no extra GPU; independent assignment changes the task and sample efficiency. **PI decision needed: only for redesigning the assignment mechanism; deleting the leading wording and labeling the chance level accurately do not need one.**

### I3. C0 exclusion defines a narrower population, but does not automatically invalidate all paired treatment differences

**What the problem is.** L322 screens samples by requiring all four C0 items (A/B START/BEH) to be correct, but does not screen on Robin in the same way.

**Why it matters.** This is a common pre-treatment eligibility rule and can legitimately estimate the treatment difference in the "both sides eligible at baseline" subgroup; it cannot be broadly accused of post-treatment collider bias. But it changes the baseline difficulty distribution of self/Robin and limits generalization; declines relative to C0 are also affected by selection for high baseline. The common C0 term in between-condition SMI differences cancels exactly. If each of the four items is 90% and independent, the retention rate is `0.9⁴=65.61%`, and about 197 of 300 generated episodes remain; independence is used only for the numerical example.

**How to fix it concretely.** Recommended: use all episodes that are valid under the task-generation rules for the main analysis, and the C0-eligible subgroup as a sensitivity analysis. If screening is insisted on, state the target population clearly, report each exclusion step and the retained N, and make explicit whether 300 is the number generated or retained; do not add screening based on treatment results. Do not write "there is no clean self to lose".

**Cost.** Full-sample analysis is almost free; if 300 retained episodes are insisted on, the example implies generating about 458, depending in practice on correlations. **PI decision needed: yes, decide the target population and the top-up sampling budget.**

### I4. BEH agreement does not equal source control; a WORD error does not equal identity absorption

**What the problem is.** A decision that agrees with B's rule may reflect borrowed information, chance preference, rule priming or a format error; the START ground truth is an externally assigned historical fact, not the author of a truly spontaneous intention. One secret word tests only one source binding.

**Why it matters.** The existing terms "behavioral control", "borrowed intent", "identity absorption" and "domination" go beyond the level the observations support.

**How to fix it concretely.** Use "partner-consistent choice", "initial-rule misattribution", "code-word misattribution" and "convergence of choices on both sides". If a "control" conclusion is kept, fix A/Robin/scene, independently vary B's rule, and test the causal change of choices with B; also vary A, forming a small 2×2 dependency matrix. A combination of argmaxes obtained for different questions from independent branches can only be called a "combination of multiple readouts", and cannot be said to necessarily occur together subjectively within a single continuous decision. A WORD negative also requires first confirming that ACC-word can transmit the word; the priority reflection in C does not guarantee that the secret word enters the message, so a word that was never transmitted not being falsely claimed cannot be interpreted as identity being especially stable.

**Cost.** Naming is free; the local counterfactual takes about half a day to implement, 2–4 points on a small subsample. **PI decision needed: for strong control/intention-authorship conclusions; accurate naming does not need one.**

### I5. The balance of diagnostic scenes, labels and the word pool is not yet enough to rule out shortcuts

**What the problem is.** The four rules differ in length; mapping each rule to a unique best option makes scoring easy, but the rule, table row position, option name and numeric form may be correlated. Two label permutations do not guarantee that each meaning appears evenly across the four labels. The word pool has not been listed yet, and word frequency/semantics can create preferences.

**Why it matters.** The model may follow a fixed position or a familiar word rather than holding a rule. If signals are drawn from other episodes, these shortcuts can also masquerade as successful communication.

**How to fix it concretely.** Verify on the generator: each rule has a unique optimum with no ties; the row position of the best option is balanced independently of rule/role; new BEH scenes have no fixed repeated mapping; secret words are balanced independently of rule/role/condition and do not repeat within an episode; candidate foils cannot be identified by length or semantic oddness. The two permutations should use a balanced rotation over the whole sample, not just two random draws; recheck with a four-way rotation on a small sample. First tokenize the real English templates and list the total length and the distribution of label positions. The single-token condition is not a full bias control, nor is it a mathematical requirement the candidate words must satisfy, because the final readout is a numeric label.

**Cost.** Pure program checks take about half a day, no GPU; the four-way-rotation subsample adds slightly to readouts. **PI decision needed: no.**

### I6. The residual read/write positions and the normalization definition determine what the bridge actually is

**What the problem is.** Writing the output of block ℓ into the input of block ℓ is a connection spanning the two sides of a block, not an identity transfer at the same residual boundary. The definition of `σ_in`, the calibration token set, the clipping order, the standard-deviation floor, ε and the handling of near-zero vectors are not fixed.

**Why it matters.** The same hidden size does not guarantee the same semantic distribution; RMS matching does not guarantee representational compatibility. Massive activations may carry structural functions and cannot be clipped away as noise without verification. Per-sample normalization of near-zero centered vectors may also amplify noise.

**How to fix it concretely.** Explicitly keep the existing cross-boundary bridge, or switch to the same residual boundary, and state whether the outgoing message is the value before or after this step's injection. Do not pick the definition with the best effect after seeing formal results. Fix `σ_in` as a clearly defined scalar typical RMS, and state the statistics set and the clipping order; first check per-dimension energy concentration and the actual injected/host RMS. Whether or not clipping is applied, all conditions follow the same frozen processing order, and counts of near-zero/outlier values are recorded.

**Cost.** Definitions take about 2–4 hours; the distribution check reuses the calibration forward passes, with almost no extra inference. **PI decision needed: for changing the bridge definition; filling in the mathematical details does not need one.**

### I7. RF does not measure a recovery trajectory, and g50 is not evidence of a phase transition

**What the problem is.** L317 calls RF–FULL reversibility and fits a logistic g50 for each metric. SMI can be negative, non-monotonic or never cross a given threshold; independent runs at different g are not a process of evolution over time.

**Why it matters.** A steep curve over six gain points can come from greedy token-path switching, saturation or capability decline, and cannot prove a critical point, subject fusion or a strict ordering of stages. RF keeps the altered KV, and also does not establish "returning to the original state" after the connection is removed.

**How to fix it concretely.** Rename these "gain-response curve" and "post-link-cut readout"; by default plot nonparametric means/intervals. Only explore fitting g50 when prespecified conditions for monotonicity, upper and lower asymptotes and threshold identifiability are met; if not identifiable, report NA. A real recovery experiment requires several fixed-length neutral phases after the bridge is closed, paired with time-matched trajectories under a continued connection and C0; the one-week version can skip it.

**Cost.** Deleting overinterpretation is free; recovery trajectories add several time points, recommended for later. **PI decision needed: on whether to make recovery a primary question; the terminology fix does not need one.**

### I8. The power of 300 episodes depends on the variance of paired condition differences

**What the problem is.** §11 only says to estimate from the SMI variance. To actually test ONE–DEV, one needs to estimate the SD of each episode's `D=(P_SELF,ONE−P_R,ONE)−(P_SELF,DEV−P_R,DEV)`; the shared C0 term has already cancelled. One cannot use the single-condition SMI variance, nor treat A/B, label permutations or multiple questions as independent samples.

**Why it matters.** 5 percentage points may be detectable, or may be far out of reach. Using the strictest two-sided three-test Holm threshold α=0.05/3, a normal approximation, and a true difference of 0.05:

| SD of paired D | Approx. power at N=300 | N needed for 80% power |
|---:|---:|---:|
| 0.20 | 97% | 168 |
| 0.25 | 86% | 262 |
| 0.30 | 69% | 377 |
| 0.40 | 41% | 671 |
| 0.50 | 25% | 1,047 |

Computed with `N ≈ [(2.394+0.842)·SD/0.05]²`. Reaching about 80% power at N=300 requires SD≤0.268; this is not an exact guarantee under a small pilot sample, nor does Holm actually use the same threshold each time.

**How to fix it concretely.** On an independent pilot, estimate the SD of the three Ds, and fix the maximum N and the minimum meaningful effect; if the budget is insufficient, report the range of effects that can be ruled out. Each bootstrap draw resamples whole episodes, together with all their conditions, directions, permutations and branches. Predefine the two-sided p-value algorithm; one simple concrete scheme is a two-sided paired t test on the per-episode paired D, then Holm on the three p values, plus a separately reported 95% interval from 10,000 episode bootstrap draws; its inference on the mean relies on independence at the episode level and a sufficiently stable sampling distribution, and extreme dispersion/degenerate cases should be checked. An uncorrected 95% CI is not a multiplicity-corrected interval. If switching to permutation/sign-flip, the exchangeability/symmetry assumptions must also be stated.

**Cost.** Statistics code takes about half a day, and resampling CPU cost is very low; enlarging the sample scales linearly with N. **PI decision needed: for the sample-size cap; correct clustering and correction do not need one.**

### I9. The full pilot grid is larger than the formal experiment, and the time estimate is not self-consistent

**What the problem is.** If S3 is fully expanded as `4 conditions×3 layers×8g×3T×60 episodes`, there are **17,280 episode-configurations**; the formal "30 conditions×300" has only 9,000. At the text's 10–20 minutes per 300 cases/condition, linear extrapolation gives the pilot about **9.6–19.2 hours**, not 3 hours, and this does not yet count different T values or the overhead of all branches. Even with T fixed, it is about 3.2–6.4 hours.

**Why it matters.** Within one week, the real bottlenecks are state-machine debugging, calibration failures and writing; the full grid must not eat up the margin for fixing errors. The claims that 80GB is "comfortable" and 60ms per tick have also not been measured.

**How to fix it concretely.** Staged pilot: fix T=48; first find effective layers/gains with a few episodes and a few readouts; check TWO/STATIC-RULE/MISMATCH only at candidate layers; verify the frozen candidates on a fresh pilot sample. Do not run all 12 questions for every cell. First profile all branches of 2–4 episodes, recording peak GPU memory and end-to-end speed, then compute the formal budget. Run multiple long branches sequentially to reduce the peak from KV copies.

**Cost.** Rewriting the schedule takes about half a day and is expected to save most of the pilot compute; the actual gain awaits profiling. **PI decision needed: for the budget cap and the scope of cuts.**

### I10. Capability/format thresholds and state classification can easily misfire, overlap or miss cases

**What the problem is.** An error on either of the two CAP questions can get a trial classed as "collapsed"; the classification table is neither mutually exclusive nor exhaustive, and "WORD=partner" can co-occur with several classes. Low-label-mass rows do not enter the classification, but if they vanish from the figure's denominator, this masks failures under strong connection. The CAP decline of "about 5pp" has no specified confidence rule.

**Why it matters.** One ordinary reasoning error is not a system collapse; conversely, just two easy questions are not enough to show that all relevant capabilities are preserved. Stitching multi-branch readouts into a single personality state is especially overreaching.

**How to fix it concretely.** Main results keep each metric and the full-sample denominator; change the classification to a multi-label description, or add an explicit priority order and an other class. Report format quality separately from CAP. During calibration, rotate enough capability questions, including general memory/numeric-choice controls similar to the source task; prespecify the allowed decline and the interval rule. Capability equivalence cannot be claimed just because the CAP difference is not significant.

**Cost.** Analysis takes about 2–4 hours; the existing question pool can be reused, adding only a few readouts at key points. **PI decision needed: no, unless expanding capability evaluation becomes a new primary goal.**

### I11. The exploration/confirmation boundary, post-failure revisions and data splits need stricter version discipline

**What the problem is.** The secondary 3×3 comparisons have no defined multiplicity handling; it is unclear whether the 150 hotel cases, the wording variants and the denser g values are independent confirmations. Changing layers, switching to a multi-layer bridge or pruning dimensions after formal results come out changes the treatment. Splitting only by seed does not necessarily block near-duplicates from the same template family.

**Why it matters.** Many adjustable analysis and interface choices can dress up a chance phenomenon as a frozen hypothesis. Parameters overfit to pilot ACC can also make formal access matching fail.

**How to fix it concretely.** Specify the three primary tests and the secondary family; if secondary analyses are exploratory only, label them as such and report all results. Freeze domain/wording validations in advance, otherwise they are exploratory. Separate calibration, tuning pilot, candidate-confirmation pilot and formal data; at least check duplicates by scene-template/word-list combination. After a failure, any new bridge definition becomes v2 and uses a new confirmatory sample; the v1 confirmatory label cannot continue to be applied.

**Cost.** Metadata and split checks take about half a day, no GPU; an independent candidate-confirmation pilot with a few dozen cases is enough for a first check of mismatch, but cannot guarantee exact equivalence. **PI decision needed: only for extending the project or adding a new protocol version.**

### I12. The literature basis and the interpretation of null results contain points that need direct correction

**What the problem is.** Bicameral's high identity scores include trained gates/adapters; the first-person interpretation in the old version of the introspection paper has been revised; synchronous stimulation in humans is not two-way interaction. H0 also writes three non-significant results as "fully explained by access and bias".

**Why it matters.** These make the motivation and directional predictions look stronger than the evidence. Failing to reject the null hypothesis does not prove equivalence, much less prove that some independently unverified mechanism fully explains the results.

**How to fix it concretely.** Update the discussion according to the original sources in §5.13, separating the authors' conclusions from this project's inferences. H0 should only state that each prespecified mean contrast is zero; report effect sizes, intervals and power limits. Only with a prespecified equivalence bound and a corresponding interval that meets it can one say the difference is smaller than the meaningful range. Single-model results are limited to this checkpoint, task and bridge.

**Cost.** Literature and wording take about half a day, no GPU. **PI decision needed: no.**

## 4. Minor issues

### M1. The logs are not yet enough to reconstruct each intervention

**What the problem is / why it matters.** With only gain, token and cosine, it is hard to reconstruct before/after injection, branch state and the actual dose.

**How to fix it concretely.** Add receiver/donor, logical tick, phase, valid position, message norm, actual injected/host ratio, mask, permutation ID, question token count, raw four-label logprobs, total label mass, snapshot ID, and treatment/failure status. There is no need to save all full-dimensional activations; keep a small number of reproducible audit trajectories.

**Cost.** 2–4 hours; small logging/storage overhead. **PI decision needed: no.**

### M2. Numerical-consistency criteria should distinguish logits from discrete paths

**What the problem is / why it matters.** BF16 batched and single-row runs may have tiny numerical differences that change the greedy token near a tie, after which the real closed-loop paths diverge; "same tokens or within tolerance" is not clearly defined.

**How to fix it concretely.** Compare, on the same teacher-forced path, the maximum logit difference, the candidate-score difference and the top-2 margin; separately report the token agreement rate under free generation. Predefine the error tolerance and outlier handling; large differences cannot be passed off as numerical error. Keep CPU state-machine tests separate from GPU numerical tests.

**Cost.** 2–4 hours, plus a few short-sequence GPU checks. **PI decision needed: no.**

### M3. The text-mediation interpretation of OBS/LAT needs to be precise

**What the problem is / why it matters.** Re-stitching FULL's visible text into a single message changes the role and the model's judgment of "what I said"; forcing C0 text is yet another treatment.

**How to fix it concretely.** OBS rebuilds the full roles, separators and visible history, avoiding paraphrase into a user quote; call it "bridge-free recomputation over the same visible history". Call LAT "intervention under a fixed token path", without claiming that it unconditionally separates all language mediation. If the schedule is tight, leave both until the main effect is reliable. [Self-Attribution Bias](https://arxiv.org/html/2603.04582) also suggests that role attribution itself changes evaluations.

**Cost.** A few hours of engineering; one key-point condition each. **PI decision needed: on whether to make text mediation a core part of this paper.**

### M4. The "device smoke test" cannot treat the expected behavioral effect as proof of a correct implementation

**What the problem is / why it matters.** L379 requires BEH to move toward a rule after that rule's direction is injected; valid code may not show this effect, and buggy code may produce it by chance.

**How to fix it concretely.** List norm, direction, row-mapping and zero-gain tests as engineering correctness; list BEH movement as an independent manipulation check, and keep failures. Repeated tuning until the expected self result appears is forbidden.

**Cost.** No extra compute; mainly test classification and naming. **PI decision needed: no.**

### M5. The freeze and scope files contain inconsistencies that can be resolved directly

**What the problem is / why it matters.** The current directory was checked and is not a Git repository, so `git tag protocol_v1` cannot be run for now; the old AGENTS/PLAN interfaces still have a C instance and superseded metrics, and the model alternatives also conflict with the latest constraints.

**How to fix it concretely.** At implementation time the owner unifies the schema and the versioning approach: initialize a repository or freeze with immutable configs/a file SHA list; use only 4B. As required, this document does not modify these files and does not create a repository.

**Cost.** 1–2 hours, no GPU. **PI decision needed: no, the latest user scope is already clear.**

## 5. Point-by-point answers to the 14 assigned questions

### 5.1 Does the SMI pairing logic hold, and is there a better pairing

As a "condition × question" difference it holds; as a self-specificity estimate that has already excluded general steering it does not. The counterexample in B1 directly refutes the latter. Baseline confidence, fact position, rehearsal, temporal qualifier, pronoun and online dose are all asymmetric.

First fix the temporal qualifier, length and order of source presentation, and report the raw components and the log-odds difference; on a key subset add a question form that "refers to oneself by name" and a symmetric third-party–third-party binding. Lengthening only the Robin question with a string of meaningless padding cannot be considered fair pairing.

### 5.2 Does DEV remove the first person; what alternative controls exist; can it be matched on access

Removal has not been shown; only a strictly common additive component is cancelled by centering. The static rule prototype is a useful engineering baseline, but not a subject-free device. Time shuffling, an independent donor with the same rule, and content-matched first/third-person encodings check timing, instance specificity and framing respectively, and cannot substitute for each other (B2).

ACC-rule matching is feasible when the two curves share a commonly reachable range; it requires choosing points on an independent pilot and testing the error range on the formal sample. It only matches a readout that has error, especially since online ACC can also be directly steered. When DEV carries no secret-word payload, matching both ACC-rule/word against ONE may be simply infeasible; do not turn an impossible match into post hoc data deletion.

### 5.3 Is ONE–TWO at the same strength fair, and should it be access-matched

With the same g, injection position and initial snapshot, it is a reasonable comparison of the total effect of the return connection; "B's content must shrink" has not been verified, and the echo could strengthen own, partner or other content. Test it empirically with a direction-open hypothesis.

Recommendation: same g as the primary topology comparison, access matching as a secondary treatment-combination comparison. The two answer different questions; do not replace the former with the latter and then call it the only "fair" one. To claim feedback adaptivity rather than a specific trajectory, compare live feedback with a prerecorded replay after A is externally perturbed; a replay with exactly identical input matching the original trajectory is, if anything, a correctness check.

### 5.4 Is LANG–ONE directness confounded with the absence of a label, and can untag solve it

Yes, clearly confounded. untag is worth keeping, but it only removes the explicit author name; it cannot remove the external user message, the quotation frame or the difference in generation phase. The most time-saving approach is to narrow to an overall comparison of channel schemes; a stronger claim requires a channel × source-cue crossing with matched actual payload (B3). It cannot be asserted in advance that LANG access is necessarily higher; it should still be measured.

### 5.5 Is measurement while connected just answer shift; should the primary endpoint use RF or both

It may include direct answer shift, and SMI is not enough to rule this out. **Report both, with primary and secondary chosen in advance.** RF better fits "source change left behind after C", while FULL is closer to the PI's online question. A FULL-only positive is not automatically invalid, but it can only show a change in the answering process under continued bridging; an RF positive also does not automatically prove autonomous memory rewriting, because the affected cache and the text history are still retained (B4, M3).

### 5.6 Is telling the model about another participant, and that it is "different", leading

It lowers the uncertainty of the access questions and gives an explicit answer cue for the number report. Keeping the participant background is fine; delete the unnecessary "different", and set the chance baseline by the real generation distribution; U cannot be used to infer the number of subjects. If mutually distinct assignment continues to be used, state explicitly that this is a deliberately constructed conflict task rather than a natural self-boundary population (I2).

### 5.7 Is the overall C0 exclusion a selection bias

It changes the target population and causes difficulty screening, but not all paired treatment comparisons are automatically invalid. Recommended: full sample as primary, baseline-eligible subset as sensitivity; if the eligible population is adopted, state it clearly in advance and top up to the retained N. In particular, do not screen "remembers itself" episodes separately for each treatment condition (I3).

### 5.8 Do the scenes, the four rules, the word pool and the two permutations have leakage/position problems

The design direction is reasonable, but the complete generator and word list have not been provided, so it cannot be accepted at present. The joint balance of role–rule–row position–label must be checked, not just each marginal frequency separately. The primary privacy test should be "P/C does not explicitly leak the partner→rule/word binding", not "B's word never appears among A's tokens": R's candidate options necessarily include it, and A generating it via the bridge may be exactly the result. The candidate set and its order are fixed across paired conditions, and the correct attribution is not marked (I5, §6).

### 5.9 Point-by-point answers on engineering risks

| Item | Audit conclusion / required action |
|---|---|
| Synchronous per-token | Define a tick by the consumed token; read from the old buffer, commit the new buffer afterwards; specify whether the first/last token has entered the KV |
| Branching | Snapshots include KV, pending token/logits, both sides' mailboxes, positions and phase; crop does not replace full state restore |
| padding | pad must not advance the whole pair; manage valid position IDs explicitly; start with small batches/length bucketing |
| Qwen3 hook | 4.51.3/4.53.3 return a tuple, 4.56.2/4.57.1/5.17.0 return a Tensor; `output[0]` cannot be used unconditionally |
| massive activation | The measured distribution cannot be verified in this audit; check only on the calibration set, prespecify whether to clip and the rule, and do not decide by looking at the main attribution results |
| Truncated chat | Truncating C content midway differs from syntactic closure; the R donor cannot be assumed to still be in its original reflection after the assistant turn has ended |
| EOS | During C, both official EOS IDs must be covered; greedy requires explicitly turning off the default sampling |
| batch vs single row | Verify same-path logit tolerance separately from free-generation path agreement; keep evidence of later divergence after near-ties |

Also check that after the FP32 normalization computation the result is written back in the correct dtype, to avoid accidentally upcasting the host residual to FP32; calibration and pad positions must not be mixed into valid-message statistics. For specific evidence see B6, I6, M2, §6.

### 5.10 Are the statistics appropriate, and is 300 enough

A paired/clustered bootstrap by episode is correct; A/B, permutations and questions do not add independent N. If many episodes are generated from several fixed templates, the intervals mainly reflect instance variation under these templates and do not represent generalization to arbitrary tasks.

Holm can be used for the three primary comparisons, but the receiver, readout mode and p-value algorithm must be defined. If RF/FULL are both called co-primary endpoints, the test family must be expanded accordingly or a hierarchical testing order must be set in advance. The nine secondary comparisons need an explicit correction or an exploratory label. 80% power for 5pp at N=300 holds only when the paired-contrast SD is below ≈0.268; see I8. Keep pilot parameter selection strictly separate from the confirmatory sample, to avoid treating "the best curve we saw" as a prespecified primary test.

### 5.11 Which controls are missing, and which can be dropped

| Priority | Control | Question answered / trade-off |
|---|---|---|
| Required | C0, zero gain, independent branch/clock checks | Whether the implementation changed things that should not have changed |
| Required | Natural-message MISMATCH, or a donor-content counterfactual with A fixed | Whether donor-specific content was transmitted, rather than a general perturbation |
| Required | FULL + RF at g*; a little RO | Ongoing question-reading intervention vs. effects readable after link cut |
| Keep | LANG-tag + LANG-untag | Sensitivity to the explicit source label; they are not treated as a fully clean decomposition of directness |
| Depends on claim | Content-matched first/third-person messages | Must be added if a self frame is claimed; otherwise downgrade to a later mechanism question |
| Depends on claim | live/replay after perturbation, or SELF | If an echo/adaptivity mechanism is claimed, recheck at key points; same-trajectory replay serves only as verification |
| Can be reduced | STATIC-RULE and SCRAM | The static direction can keep one matched point; SCRAM keeps one point; neither needs a full curve |
| Can be deferred | OBS, LAT, time shuffling, another donor with the same rule | Each isolates a different factor; once the main effect is reliable, pick the most relevant one |
| Cut first | Large-scale U-open, recovery trajectories, dense g50, all T grids | Limited benefit for the core source-attribution conclusion; easily extends the schedule |

It is not advisable to keep adding controls just to preserve three attractive mechanism names. A better way to save effort is to narrow the causal claims and keep the truly necessary content-validity and readout controls.

### 5.12 Are the wording/hypotheses overreaching

Suggested replacements:

| Original wording | Wording this design can support |
|---|---|
| Device vector with the first-person frame removed | Rule-conditional mean direction; the first-person component has not been independently verified |
| Self-specific false claiming | Source-misattribution increment relative to the third-party question |
| Identity absorption | Source misattribution of the secret word/random marker |
| B controls A / domination | A's choices agree with B's rule; speak of rule influence only with counterfactual interventions |
| Merging into one / number of subjects | Convergence of readouts on both sides; the self-reported number is only a prompt-sensitive text result |
| Reversibility | Readout difference after new injection is turned off, unless recovery trajectories are run separately |
| Phase transition / stage ordering | Gain response and possible nonlinear change, with no inference about change in the subject |
| Not significant, so it is all access/bias | No difference detected; the interval and power bound the range of effects that can be ruled out |

H-interaction should not presuppose TWO>ONE; H-directness/H-subject should distinguish speculation from identified manipulations. The analogy between consciousness and brain bridging can go in the introduction, but conclusions do not extend to human experience.

### 5.13 2025–2026 literature: has this already been done

**Conclusion of the targeted search: the components on both sides already exist; this search did not find a direct precedent that combines "an internal-state connection between two independent instances, a self/other source-attribution readout, and a controlled comparison between static concept/device-style injection and a live instance state". This cannot be used to claim a world first.**

Answering the user's two search goals separately: first, no work was found that directly compares the effects of "static device-style injection" and "another instance's live state" on self-attribution; Lindsey et al. have studied the former, and internal-communication papers have studied the task efficacy of the latter. Second, no direct experiment was found that connects two same-weight independent instances through internal states and then measures "attribution of my/its historical content"; Bicameral has a connection but not this readout, and the persona study has attribution but no internal connection. ThoughtComm's shared/private thought decomposition is especially close, but the operationalization differs; it must be discussed proactively and cannot be omitted.

The search covered arXiv originals, the authors' research reports and related citation chains, with keywords including `latent communication self attribution`, `thought injection another model`, `self-other hidden-state coupling`, `static dynamic activation self-attribution`, `live donor language model`. Below are the closest original works that would affect this design; the search did not exhaust all papers, non-English sources or every code repository.

| Work and version/date | What has already been done | Specific differences from this design |
|---|---|---|
| [The Bicameral Model](https://arxiv.org/html/2605.11167v1), 2026-05-11, v1 | Continuous, two-way internal communication between two instances of the same checkpoint; the base model is frozen, but the communication interface is trained | Does not measure the instances' source attribution of rules/memories, and has no static/live source-attribution comparison. A two-way same-weight bridge by itself is not new |
| [LatentMAS](https://arxiv.org/html/2511.20639), first released 2025-11, v4 2026-08-03 | Training-free latent reasoning and KV working-memory transfer | Communication task gains, not my/its source misplacement; its effective interface does not guarantee that arbitrary residual addition works |
| [Cache-to-Cache](https://arxiv.org/html/2510.03215), first released 2025-10, v2 2026-03-02 | Learned KV projection/fusion; Table 6 has an Identical condition with the same Qwen3-0.6B | Same-model communication exists, but not a continuous two-way self/other attribution experiment; "self-communication" is not a sense of self |
| [ThoughtComm](https://arxiv.org/html/2510.20733), 2025-10-23, v1 | Learns shared/private latent structure and a prefix adapter; studies the shared and private parts of agent thoughts | Conceptually very close, but latent identifiability/consensus is not the receiver's judgment of historical source; and it requires training |
| [Emergent Introspective Awareness](https://transformer-circuits.pub/2025/introspection/index.html), 2025-10-29 | Static concept-vector injection; discrimination of internal/external content; earlier injection affects intention attribution for an artificial prefill | **There is precedent for static injection affecting "I did this intentionally"**; lacks a live-state bridge from another running instance and a static/live attribution comparison |
| [Emergent Introspection in AI is Content-Agnostic](https://arxiv.org/html/2603.05414), v2 2026-04-07 | Separates anomaly detection from content recognition; examines third-person and continuous-injection controls | The third person is the target model in the prompt, not a connected second instance; Appendix M shows that prompt length affects the old first/third-person results |
| [The Assistant as a Privileged Persona](https://arxiv.org/html/2606.00545), 2026-05-30, v1 | Authorship-attribution matrix across different personas of the same-weight Llama3.1-70B | Self/other attribution across different roles with the same weights already exists, but via text; not a live internal connection, and it reveals persona/distribution-matching alternative explanations |
| [When Does Latent Communication Pay?](https://arxiv.org/html/2608.04893), 2026-08-05, v2 08-27 | Audits communication with mismatch, zeroing and moment-matched random caches; random private mappings verify content specificity | Does not study self attribution; directly requires this design to add natural-message mismatch/private-content counterfactuals, not just SCRAM |
| [SEAA](https://arxiv.org/html/2609.17331v1), 2026-09-15 | External HMM state differentiation of initially identical agents, then feeding profiles into the model to generate self-reports/text discussion | Discusses the self/other boundary, but has no internal-state bridge and none of the source-misattribution operationalization used here |

Citation inferences that need correction:

- **Bicameral:** the 68–84% arithmetic scores in §1.1 of the synthesis draft involve adapters; Table 1's Scalar Identity **without adapters** is arithmetic 39.0, GSM8K 42.8, GSM8K-IRL 11.1, versus 36.2, 49.6, 12.8 for the base model. identity does not mean the communication system is entirely untrained. It proves neither that training-free addition must succeed nor that a training-free bridge must fail. [Original Table 1](https://arxiv.org/html/2605.11167v1)
- **First-person effect:** the 2026-04-07 version of 2603.05414 has superseded the old draft, and Appendix M weakens the argument that interprets the advantage of shorter first-person prompts as special direct access. The current online question-length issue should be controlled carefully in light of this. [Revised full text](https://arxiv.org/html/2603.05414v2)
- **Centering does not remove self:** Ackerman and Panickssery separately construct a surface-word nuisance direction, then project it out and verify; they do not use a global mean to prove there is no first person. Even removing the defined nuisance is not the same as removing subjecthood. [Self-Recognition in Language Models, related methods](https://arxiv.org/html/2410.02064)
- **Human analogies:** Wegner–Wheatley can inspire thinking about source cues and a false sense of authorship, but does not directly imply latent>language. [Authors' paper](https://dtg.sites.fas.harvard.edu/DANWEGNER/pub/Wegner%26Wheatley1999.pdf) The synchronous stroking in Paladino et al. used a prerecorded video of a stranger, not real two-way interaction, and cannot serve as evidence for TWO>ONE. [Authors' original](https://www.igroup.org/schubert/papers/paladino_mazzurega_pavani_schubert_inpress_psychscience.pdf)

A usable novelty statement: "Prior work has separately studied internal communication between models and self-related attribution. We test whether, when same-weight instances with different private histories exchange content through an internal channel, content use and original source attribution dissociate, and we compare static rule injection, a one-way live state and two-way feedback. In the literature checked here, no direct controlled test of this combined question was found." This is a judgment within the bounds of the search, not a guarantee of novelty.

### 5.14 Is one week feasible, and what to cut first if cuts are needed

**Conditionally feasible: a single-model preprint with a clear protocol and sufficient negative controls can be done; the current full grid plus all mechanism tasks is not safe.** The project is currently still mostly Markdown; code correctness and whether the bridge transmits effectively are the actual critical path. Many coding agents can speed up writing code, but cannot replace verification of communication validity.

Recommended cutting order: second model/0.6B/8B (already out of scope) → the full T grid and full g grids for all conditions → large-scale U-open and the g50/"recovery" narrative → OBS/LAT/mechanism extensions when there is no main effect → the scale of the 150 hotel cases. Try to keep one small independent wording/scene check, to avoid relying entirely on a single template.

Should not be cut: the independent pilot/formal split, natural-message mismatch or content counterfactuals, FULL/RF at g*, correctness tests, complete failure records and the main intervals.

Feasible schedule: Day 1, freeze the questions, templates and state contract; Day 2, implement and run small-scale 4B correctness tests; Day 3, calibration and staged pilot; Day 4, formal sample; Day 5, analysis and the most critical rechecks; Days 6–7, writing, checking citations and reproducibility materials. If by Day 3 content transmission with basic capability preserved still cannot be shown, shrink to an interface feasibility/failure study or postpone; do not fill the claims with high-gain collapse results.

## 6. Items verified / items that could not be verified

### 6.1 Official config and tokenizer: measured or verified file by file

Pinned model revision: `cdbee75f17c01a7cc42f958dc650907174af0554`. All sources are the official Qwen model repository.

| Item | Result and evidence |
|---|---|
| Layers / hidden size | 36 / 2560; consistent with the draft. [config.json](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/config.json) |
| Attention | 32 Q heads, 8 KV heads, head_dim=128; note that the Q projection width need not equal the hidden size. Same source as above |
| Sliding window | `use_sliding_window=false`, `sliding_window=null`; same source as above |
| chat template | Does not add a thinking block; with `add_generation_prompt=True` it ends with `<\|im_start\|>assistant\n`. [tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/tokenizer_config.json) |
| assistant generation prefix | token IDs are `[151644,77091,198]`; measured with the tokenizer in this audit |
| Bare labels `1,2,3,4` | One token each, IDs `16,17,18,19`; when appended directly after the rendered real assistant header, the original prompt prefix is unchanged token by token and exactly one label token is added |
| Labels with a leading space | `" 1"` is `[220,16]`, and likewise for the others; not a single token, so a single logit for "space + digit" cannot be read |
| EOS | Officially `[151645,151643]`, which are `im_end` and `endoftext` respectively. If EOS is masked during phase C, both should be covered. [generation_config.json](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/generation_config.json) |
| Default sampling | The official generation config has `do_sample=true`; when using generate, it must be explicitly set to false to get greedy. Hand-written argmax stepping also needs an explicit EOS-mask order |
| Theoretical KV size | BF16, per row per token: `36×2×8×128×2=147456 bytes=144 KiB`. 500 tokens is 73.728 MB / 70.3125 MiB; this is a structural estimate, not a measured peak |

The tokenizer check used only `tokenizers==0.22.1` and `Jinja2==3.1.6` in a temporary environment, rendering with the official tokenizer.json and template, without calling the model. Core assertions:

```python
base = tokenizer.encode(rendered_prompt, add_special_tokens=False).ids
full = tokenizer.encode(rendered_prompt + label, add_special_tokens=False).ids
assert full[:-1] == base
assert full[len(base):] == [label_id]
```

All four bare digits passed. tokenizer.json is actually about 11.4 MB; what was downloaded were tokenizer/config/source files, no weights. The temporary check evidence and checksums are at [download_manifest.json](/tmp/mb-tokenizer-audit-EVn1B1/download_manifest.json); this temporary path should not be treated as a long-term paper archive, and the formal reproducibility materials should keep the same revision and file hashes.

### 6.2 Qwen3DecoderLayer and cache: version differences verified

| Transformers version | Key forward differences | Return format / original source |
|---|---|---|
| v4.51.3 | `past_key_value` singular; explicit output_attentions/use_cache/cache_position | tuple, may include attention; [source from L272](https://github.com/huggingface/transformers/blob/v4.51.3/src/transformers/models/qwen3/modeling_qwen3.py#L272) |
| v4.53.3 | Same as above | tuple; [source from L246](https://github.com/huggingface/transformers/blob/v4.53.3/src/transformers/models/qwen3/modeling_qwen3.py#L246) |
| v4.56.2 | `past_key_values` plural; explicit use_cache/cache_position | Tensor; [source from L246](https://github.com/huggingface/transformers/blob/v4.56.2/src/transformers/models/qwen3/modeling_qwen3.py#L246) |
| v4.57.1 | Same as the previous row | Tensor; [source from L246](https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/models/qwen3/modeling_qwen3.py#L246) |
| v5.17.0 | `past_key_values`; no longer has an explicit cache_position parameter | Tensor; [source from L294](https://github.com/huggingface/transformers/blob/v5.17.0/src/transformers/models/qwen3/modeling_qwen3.py#L294) |

According to the official release metadata, v5.17.0 was released on 2026-09-09. [release](https://github.com/huggingface/transformers/releases/tag/v5.17.0) **Verifying a new version does not mean an upgrade is required; the one-week experiment should pin one checked version.** `transformers_version=4.51.0` in the config is metadata from when it was saved and does not define the hook contract for this run.

The implementation of `crop()` also changes across versions: older versions modify the key/value lists in place, later versions modify the layer caches. It does not restore donor state; slicing is also not an independent clone. In v5.17 the usage with a positive absolute target length is deprecated, and DynamicLayer's `crop(0)` is a no-op, so it cannot be used to clear the cache. [4.51 source](https://github.com/huggingface/transformers/blob/v4.51.3/src/transformers/cache_utils.py#L485), [4.57 source](https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/cache_utils.py#L140), [5.17 source](https://github.com/huggingface/transformers/blob/v5.17.0/src/transformers/cache_utils.py#L167).

In 4.57.1 the model forward's default position IDs come from cache_position, and do not automatically build the ideal position sequence for each row's different pad layout in hand-written batching; they should be managed explicitly. [Relevant source](https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/models/qwen3/modeling_qwen3.py#L373)

### 6.3 Still unverifiable, and why

| Item | Status / where it is resolved |
|---|---|
| Whether all secret words are single tokens | **Cannot verify: there is no actual 60-word list yet.** A few self-chosen words passing cannot substitute for acceptance; once the words are listed, context boundaries can be checked on CPU |
| Lengths of all formal questions and balance of the 2 permutations | **Cannot verify: the complete English questions and generator have not been provided.** The existing label-boundary measurement does not mean the whole question set passes |
| Whether the 4B START/BEH/WORD baselines are ≥90% | As required, this audit does not run the model; left to G1 measurement; extrapolation from large-model papers is not accepted |
| Whether a training-free residual bridge transmits content | Only structurally implementable; semantic validity unknown; verify with G2's content counterfactual/MISMATCH |
| massive activation and the benefit of clipping | config/source do not provide the actual activation distribution; left to checking on an independent calibration set |
| Actual consistency of batched/single-row runs, branching and hooks | No running implementation yet, so passing cannot be claimed; after pure state-machine tests, small-scale 4B measurement is still needed |
| Peak GPU memory and time per tick | Not measured. At 96 rows/episode×8 episodes×500 tokens, the KV alone is about 56.6 GB (52.7 GiB), plus weights, snapshot copies, temporary tensors and logits; 80GB is not unconditionally comfortable |
| Whether it can be completed in one week, and formal power | Budget and power approximations have been given, but still depend on the runtime, an effective bridge and the real paired variance |

## 7. Recommended concrete changes: for the owner of EXPERIMENT_DESIGN.md to apply

**The following are suggested changes; the original file was not modified directly.** Do A first; B is the minimal executable version; C is an optional stronger paradigm.

### 7.1 A: clauses that must be replaced/added before the freeze

| Location | Suggested change |
|---|---|
| §1 RQ2, H-subject/directness/interaction | Rename the three contrasts to static rule direction vs live state, text with source vs internal bridge, and total effect of adding a feedback path. Hypotheses two-sided; list independent identification of "subject/direct/interaction" as unresolved |
| §1 H0 | Replace with "each prespecified mean treatment contrast is zero"; delete "non-significant means fully explained by access/bias" |
| §2 model, §10 S0/G1, §13, §15 | Delete the 0.6B/8B/second-model paths; use only the designated 4B. If the baseline fails, first fix the prompt and verify independently; if it still fails, stop the corresponding endpoint |
| §3.2–3.5 | Add generator invariants, the real word pool and source balance; delete the unnecessary "different from you"; make explicit the chance baseline and U's prompt dependence |
| §4 P/C/R | Attach the complete English messages, roles, separators and token lengths; define the C snapshot/pending token; define the donor's legal message state in R |
| §5 conditions | Must add natural-message mismatch/private-content counterfactuals; keep LANG-untag at key points; downgrade STATIC-RULE to a signal-construction control |
| §5.3 readout modes | Specify which of FULL and RF is primary; delete RF=reversibility; RO as an immediate-readout sensitivity check; OBS/LAT can be deferred |
| §6 bridge | Pin the residual read/write boundary, the before/after-injection capture point and the old/new mailbox timing; fix σ, ε, clipping and the pad/near-zero rules |
| §7 questions | Add the initial temporal qualifier to START-R; add a key sensitivity check with the alias question form; define R privacy by attribution binding rather than by strings |
| §8 scores | Keep SMI but narrow its interpretation; report each probability/total label mass alongside; add the log-odds difference; change SIA to code-word misattribution; make the classification descriptive, multi-label, or with explicit mutual-exclusion rules |
| §9 statistics | Specify the primary receiver, the primary mode, the primary P, the p-value algorithm for the three tests and the Holm family; define the secondary/exploratory scope; do not screen samples by post-treatment ACC/CAP |
| §9 exclusion | Full-sample main analysis, C0-eligible subset as sensitivity; or explicitly define the "baseline-eligible population", the retained N and the top-up rule |
| §9 g50 | Nonparametric gain response by default; return NA when not identifiable; no inference of phase transition, fusion or strict stage ordering |
| §10 G2 | Content specificity rather than just beating SCRAM; staged search; write the selection rule, validity thresholds and maximum budget as executable rules |
| §11 sample size/time | Use the SD of paired condition differences; state generated/retained N; recompute the pilot grid; set batch sizes after measuring peak memory and end-to-end speed |
| §12 tests | Add last-token/pending state, pad not advancing the pair, branch mailbox restore, and per-version return type; move the device BEH effect from engineering tests to a manipulation check |

Suggested result-interpretation clause to write in directly:

> SMI measures the difference in source misattribution under internal intervention relative to the third-party question, and is not considered to have excluded general steering, pronoun binding or all retrieval differences. Only when the transmission of donor-specific content passes an independent check, basic task capability is preserved and the key controls support it, will the result be interpreted as a change in the functional source boundary for this task. No result is used to infer phenomenal consciousness, the number of subjects or the fusion of complete identities.

### 7.2 B: recommended minimal experiment for the one-week version

1. **Task and goal:** keep the delivery-rule task, mainly measuring the source of the historical rule; the secret word serves as an independent, secondary source-binding check and is not called identity. A is the primary receiver; TWO's B is described separately. Decide in advance which of FULL/RF is primary.
2. **Offline preparation:** complete English templates, word list, joint role/rule/label balance, numerical counterexample tests, cache/clock mock tests. Passing a mock must not be written up as passing on 4B.
3. **G1/S2:** keep about 60 for baseline and 60 for calibration; used to check task solvability and normalization, without looking at formal results.
4. **Compressed pilot:** fix T=48; first, with a few episodes, test only communication and capability at three layers and a few g values; at effective layers, expand to ONE/TWO, the necessary STATIC-RULE and MISMATCH. Confirm the chosen point on an independent pilot sample; picking the peak by SMI is forbidden.
5. **Core formal run:** C0, ONE(g*), TWO(g*), MISMATCH(g*); FULL/RF at g*. If the original three contrasts are kept, add STATIC-RULE(g_dev*), LANG-tag, LANG-untag. Only ONE/TWO get limited gain curves; other controls do not expand to the full grid.
6. **Diagnostic subset:** RO, pronoun/own alias, four-way label rotation, and the causal check fixing A and varying B; choose the few that directly affect the main interpretation. If a weak effect can only be found through large-scale exploration, do not relabel it a confirmatory result.
7. **Analysis and writing:** report complete figures for content access, source misattribution, behavioral choice and format/capability; the main contrast intervals; the FULL/RF comparison; failed samples and all deviations from the freeze. The main text does not rely on vivid individual U-open examples.

This version cuts the grid and the mechanistic commitments, not the correctness and content-transmission evidence. To compress further, narrow the main question to "does the return path change source misattribution", with the other two as exploratory, rather than keeping three confirmatory mechanism headings while deleting the necessary controls.

### 7.3 C: cleaner but costlier alternative paradigms

**Alternative 1: source–content binding task.** Randomly assign each of the two instances and one non-participant source its own independent nonce/code and rule, first establishing a correct source ground truth; after bridging, ask separately "can the content be identified" and "whom did it originally belong to", while testing rule use in a new scene. Balance the presentation and rehearsal of source facts, and retest with the model's own alias in place of "you". The advantage is that content access and source binding can be clearly separated, with more independent unknown bits and less room for elimination. The cost is about half a day to one day of task rewriting and rerunning G1; it still measures functional source monitoring, not a subjective sense of self.

**Alternative 2: feedback counterfactual.** At one frozen parameter point, record TWO's donor messages; apply a predefined small private rule/state perturbation to A, and compare whether the truly two-way system and a system that still plays the old donor trajectory change accordingly. What is compared is the feedback's response to the perturbation, not the fantasy that "the same message has extra force when it comes from a live instance". The advantage is a more direct test of the interaction component; the cost is about one day of replay/forking engineering plus some local extra runs, recommended for a second phase.

**Recommendation:** in the first paper, patch the existing task with the minimal elements of Alternative 1 rather than tearing it all down; if the main interest ultimately settles on "how the connection changes the mutual dependence of the two processes", then invest in Alternative 2. The PI need not take on, in the first paper, subjecthood, consciousness and independent identification of all three channel components at once.

## 8. Items requiring PI decisions

The following are substantive research choices to be made when revising the protocol, not requests for additional authorization for this audit; the read-only checks and the file write already done in this audit do not depend on these choices.

| Item | Recommended decision | Cost of choosing differently |
|---|---|---|
| Verifiable claim of the first paper | Dissociation of content use and source attribution in same-weight instances with different histories; keep brain bridging as motivation | Insisting on directly identifying subjecthood needs a stronger operationalization, which the current DEV cannot bear |
| Online or post-link-cut as primary | If the core is still "what happens while connected", FULL primary and RF a necessary secondary, stating explicitly that the answering process is intervened on; if the aim is the after-effect on historical binding, the reverse | Making both primary enlarges the multiple-testing and power requirements; primary/secondary cannot be swapped after seeing results |
| Estimand for interaction | Total effect of the return path at the same g as primary; access matching as secondary | A pure feedback mechanism with fixed information/energy needs an extra replay counterfactual |
| Whether all three mechanism comparisons are confirmatory | The three overall treatment contrasts can be kept; to save time, make only ONE–TWO the primary comparison | Insisting on three independent components "subject/direct/interaction" requires more controls and a longer timeline |
| Primary receiver and population | A primary; all generated valid samples primary, C0-eligible subset as sensitivity | Two-direction confirmation needs a role-swapped ONE; an eligible population needs top-up sampling and narrows generalization |
| Maximum sample size/compute budget | Freeze the cap after the pilot variance; if the budget is insufficient, honestly report intervals and detectable effects | Expanding to 600–1000 cases for high power at 5pp would substantially increase formal inference |
| Whether the first paper pursues the first-person frame | After the main effect is reliable, run a small paired framing check at g* | Requiring an independent subject component now would enlarge the task; centering cannot substitute for it |
| How to handle G2 failure | Do not change the model, do not train; stop strong self-boundary conclusions, accept an interface-limitation result or postpone | Multi-layer/dimension pruning belongs to a new protocol, needs a new pilot, and cannot be tried repeatedly on the old confirmatory sample |

Items that need no further decision: use only the designated 4B, no training, no conclusions about consciousness/number of subjects, correctly pin the hook/cache versions, fix the temporal/label/leakage checks, keep failure records. These are already determined by the user's scope or by the basic requirements of a valid experiment.
