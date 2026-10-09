# Narrative and follow up experiments for the two model paper

The paper can make a coherent empirical contribution around a single question:
when a model reads another instance's internal memory, does it preserve the
original ownership of the content it retrieves? Qwen and Llama support a bounded
answer: the tested memory interface can produce false original-owner reports;
measured access, original-owner attribution, and reported current adoption behave
differently. Source headers and retaining the link during questioning affect
different endpoints. A special mechanism for the self, a causal role for memory
position, and consequences for subsequent decisions remain separate questions.

This October 9 proposal reorganizes the completed evidence and prioritizes possible
follow-ups. It does not amend a frozen protocol, replace the preserved manuscript,
authorize a new experiment, or commit a new compute budget. The factual basis is
the [cross-model evidence assessment](../results/v4/claims_and_matching_review.md).

## Central claim and contribution

**Sharing internal memory can transfer content without preserving its correct
original attribution in the receiver's answers. The effect depends on the tested
interface and on whether the connection remains available during questioning.**

Here, attribution means a report about an externally assigned rule or code word
whose original owner is known. It does not mean consciousness, identity change,
or a hidden mental state. A correct original-assignment answer and a changed
current-rule answer can coexist. The latter is reported adoption, not necessarily
an error or a demonstrated change in action.

The contribution has three parts: a controlled task with known private owners;
evidence across two checkpoints that transfer and correct attribution can
separate; and a paired intervention at questioning that distinguishes effects
requiring the continuing link from effects retained in the receiver state.
The Qwen access-matched steering comparison and third-person controls constrain
explanations within their tested scope. They do not turn the whole study into
a demonstrated theory of positional binding or a universal property of LLMs.

The closest precedents narrow this contribution. [Ackerman and Panickssery](https://proceedings.iclr.cc/paper_files/paper/2025/file/d560f94c582033e6d8eb0c97cdd4f721-Paper-Conference.pdf)
already steer Llama3 to claim or disclaim authorship of arbitrary text.
[Lindsey](https://transformer-circuits.pub/2025/introspection/index.html) makes
artificially prefilled words more likely to be described as intentional through
earlier concept injection. [Cheng and colleagues](https://arxiv.org/html/2608.04893v2),
Appendix C.2, show that mismatched relayed caches can make answers follow the
donor's registry. Thus neither false self-attribution under an internal
intervention nor donor-following through KV is, alone, the distinctive finding.
The proposed contribution is their controlled study in a known-owner setting,
with original-assignment, access, source-header, and same-state timing contrasts.
The literature check is selective and does not justify a priority claim.

Systems such as [LatentMAS](https://arxiv.org/html/2511.20639v4) motivate auditing
internal-state communication for provenance. This study does not test their
implemented interfaces or establish a deployment failure. A description of cache
prepending alone also does not establish a particular rotary-position policy.
Our content-calibrated STATIC direction differs from a direction designed to
steer self-authorship; its null choice rate is not evidence that steering vectors
in general cannot change attribution.

The original brain-bridging motivation remains useful as an opening question
about how to establish whose content a receiver reports. One short paragraph can
introduce it before the operational task. Extended philosophy, consciousness
theories, and speculative human implications should follow the empirical result
in discussion or the appendix rather than establish promises the experiment
cannot fulfill.

## Proposed title and abstract

Suggested title: **Mine or Yours? Source Attribution in Memory-Connected Language
Models**. This preserves the original question while naming the measured function.

Proposed abstract:

When language models exchange internal memory, can a receiver distinguish its
own assigned content from its partner's? We give two frozen instances private
decision rules and code words, then let one attend to the other's key-value
cache. In confirmatory studies of Qwen3-4B and Llama-3.1-8B, the receiver reports
partner content as its own original assignment. Under equal per-key weighting,
partner-rule choices are 52.3% and 51.3%, respectively, against 0% without the
link; these rates describe separate within-model experiments. High access need
not produce misattribution: source-labeled text gives higher measured rule access
than the selected memory link in both models while producing no original-rule
claiming. Source headers also reduce reported adoption of the partner's rule.
From the same saved reflection state, cutting the link before questioning
sharply reduces original-rule claiming, while some current-rule influence
persists. Code-word residue differs across checkpoints. An access-matched
steering comparison supports an interface difference in Qwen; the corresponding
Llama comparison remains unmatched. These results identify source attribution
as a separate audit target for internal-state communication under the tested
overlapping-memory arrangement. They do not establish a specific positional
mechanism or effects on subsequent decisions.

## The argument in five steps

**First establish a measurable problem.** Begin with two private assignment cards
and a concrete wrong answer. A knows its own rule before connection; after reading
B's cache, it may report B's rule as A's original rule. This historical claim has
a fixed ground truth. Explain access, historical attribution, and current adoption
before showing results. Use the known assignments rather than an evocative
self-report as the evidential anchor. An open-report example can illustrate the
Qwen result if marked as selected and Qwen-only.

**Then establish replication and specificity at the appropriate level.** Present
the core effect in both checkpoints and retain Qwen's strength series as
descriptive context. At w1, original-rule partner choices are 52.3% in Qwen's v3
sample and 51.3% in Llama's v4 sample. Qwen's stronger selected setting gives
97.1% in v3. Do not compare these rates as a formal cross-model equivalence or
rank the raw logit effects across models. Show capability and format diagnostics,
the raw self and Robin components, and content-access counterfactuals. The current
Robin control excludes an indiscriminate tendency to answer every question with
B's rule; it does not exclude general interference where conflicting entries
are substituted.

**Ask whether successful transfer guarantees correct attribution.** Compare
access and original-assignment reports on the same conditions. Tagged text gives
high access with no original-rule claiming in both models. The TAG versus UNTAG
comparison holds message content fixed and changes its header, reducing reported
current-rule adoption in both. Keep these as two distinct findings: route
comparisons change multiple properties; the header intervention targets current
adoption. Qwen's later v3 matched STATIC comparison provides additional evidence
at similar mean access gain. The Llama failure is visible alongside it and limits
that claim to Qwen. Neither result demonstrates that access is measured perfectly.

**Ask when the link is needed.** FULL and RF fork the same connected reflection
state. Cutting before questioning reduces original-rule partner choices from
97.1% to 1.3% in Qwen's strong v3 condition and from 51.3% to 0% in Llama. This is
the strongest existing timing intervention. Some current-rule influence remains
in both. Positive adjusted code-word residue is present in Qwen but not replicated
in Llama. The conclusion is selective reversibility, not complete recovery,
permanent memory overwriting, or proof that generated reflection words mediate
the residue. A reflection-only versus no-link contrast includes both generated
text and hidden-state history.

**End with the operational consequence and the unresolved mechanism.** A test of
content transmission alone cannot establish correct original attribution under
this interface. Separate provenance checks are useful alongside access measures.
The two-cards-in-one-slot explanation is a concrete hypothesis, with position,
layout, and conflicting third-party predictions. Keep it distinct from the
replicated observations. Fixed reciprocal reading and live-feedback pilots
answer a further question and should not carry the main conclusion.

## Main text and figure organization

| Part | Question it answers | Evidence and presentation |
|---|---|---|
| Introduction | Why measure who content originally belonged to? | Short bridging motivation, concrete known-owner example, closest prior work, three bounded contributions. |
| Task and method | What makes an answer a misattribution? | Two cards, native model instances, precise cache interface, three readout meanings, independent staged selection, known owners. |
| Result 1 | Does the effect occur in both checkpoints? | Both models' original-rule and word results; baseline, raw components, capability; Qwen w1 and stronger setting labeled. |
| Result 2 | Does access determine attribution across these conditions? | TAG access/attribution dissociation; Qwen matched STATIC and Llama unmatched status; no universal or single-factor route claim. |
| Result 3 | What does naming a message's source change? | Identical-body TAG/UNTAG comparison on current adoption; Qwen's contrary self-header result and differing original-rule effects retained. |
| Result 4 | How much requires the link during questioning? | Same-state FULL/RF contrasts, all three endpoints, both models, contrary Llama word residue. |
| Discussion | Which explanation is supported, and which remains open? | Generic conflicting-memory retrieval, positions, task limits, practical audit target, model-specific extensions. |

Use the existing restrained paper figure style. Reuse plots and change captions,
panel membership, and ordering only as needed; no decorative redesign is needed.
A compact main figure set can cover the task and two-model effect, access with
attribution and headers, and the link-cut endpoints. A fourth mechanism figure
is warranted only if new causal evidence is collected. Qwen-only reports,
third-person variants, dose diagnostics, and reciprocal pilots remain accessible
as clearly labeled extensions. Their scientific status must not be upgraded by
their placement. A main-text table should expose model coverage and match status.

Do not silently pair Qwen TAG from v2 with KV from v3. Route panels use the same
sample for each comparison, identify separate cohorts explicitly, and never pool
the two checkpoints. Retain each original analysis family and prespecified status;
narrative reordering does not produce new confirmatory tests.

## The largest unresolved alternative

The current task puts inconsistent self assignments into two similarly arranged
caches, while both caches agree about Robin. A model that retrieves the wrong
record for any conflicting entry could therefore show strong apparent self
misattribution with accurate Robin answers. This is a real error under the task's
ground truth, but it does not establish a special failure of a self mechanism.
Names inside the donor card and a third-person rewrite do not fully resolve it.

Three increasingly strong papers must be distinguished. A bounded empirical paper
about source attribution already has two-model support. A claim that the self role
is privileged over other conflicting roles needs a comparably conflicting
third-party control. A claim that overlapping positions cause the effect needs a
position intervention with preserved access. Choose the claim first, then collect
the experiment required for it.

## Recommended follow up and interpretation of every outcome

If adding one study, prioritize a **conflicting third-party record test**, because
it directly tests the general record-substitution alternative. A symmetric
extension can then assess role dependence. This is a proposed new study, not a
way to repair STATIC or revise the completed v4 run.

The minimal contrast starts with fresh paired episodes and three arms: no link,
the original fixed-memory link with consistent Robin entries, and the same link
with a different Robin entry on the donor's card. Keep the receiver's entire
initial card unchanged within episode. Counterbalance rules, words, roles, line
order, and answer order. Keep the existing eligible weights as the starting
settings; do not select settings on a self/Robin effect. A larger factorial design
varying conflict in both entries would be more symmetric, but changes the current
generator's distinct-rule contract and should not be smuggled into this minimal
control.

Two conflicting Robin records do not define a single global fact about Robin.
Questions must explicitly ask what was stated on the receiver's original private
card, with parallel wording for its own and Robin's entries. Donor-record access
questions separately test what the donor's card says about each relevant entry.
Revalidate native no-link own-record answers for both roles and the donor's own
record answers. The receiver's no-link inability to know a private donor record
is expected, not a reason to tune prompts. Because the source-qualified questions
are new, the ordinary-link arm on fresh episodes is essential: if that question
alone resolves the error, report a wording boundary instead of searching for a
stem that restores it.

For both rules and words, the minimal readout set has four independently cloned
questions: receiver-original own entry, receiver-original Robin entry,
donor-original own entry, and donor-original Robin entry. Two capability questions
bring this to ten readout types per arm. Retain the same physical candidates and
counterbalanced orderings across arms. A donor-only Robin/spare swap can preserve
four distinct candidates without changing the receiver card. The third-party
score compares the donor's Robin candidate with the receiver's Robin candidate,
not the donor's own rule. The three-arm test has asymmetric conflict structure;
it characterizes this added conflict rather than estimating a fully balanced
factorial effect of self versus other status. A fully crossed version would have
self-conflict present/absent by Robin-conflict present/absent, plus a shared
no-link baseline: five receiver arms. That version needs a revised material
contract when two roles share a physical answer and cannot use the old mutually
exclusive owner labels as answer identities.

The existing reflection and note emphasize self content more than Robin. A
strong claim of special self-role vulnerability additionally needs balanced
rehearsal and checks that both conflicting fields are accessible. Otherwise a
role difference remains compatible with salience or unequal retrieval. Choose
and freeze this material policy before collection; the original balanced-rehearsal
Qwen study is supporting context, not a replacement for the new control.

The code already has `balanced2` materials, but their longer notes and changed
reflection prompt constitute a new material condition for Llama. They need fresh
validation and cannot be treated as a drop-in proven control. Current strict
third-person templates bypass those balanced prompts, so combining their config
names would not silently create balanced third-person material. A symmetric
role claim would require explicit role and rehearsal balancing beyond the minimal
three-arm extension.

Do not reuse the old Robin-subtracted M as the sole new endpoint: Robin is now
a target of the manipulation. Report donor-versus-receiver preference separately
for each field and estimate a within-episode role-by-condition interaction with
its interval, with the interpretation limited by the chosen design. Keep
capability/format checks as separate controls. An additional nonconflicting
memory-field control would add readouts beyond the ten-question count below and
must be included in the final workload specification. If a no-difference conclusion matters, define a
substantive equivalence margin and power for it in advance; a nonsignificant
interaction alone is not evidence of equality.

| Possible result | What it would establish or constrain |
|---|---|
| Both conflicting fields follow the donor record, with useful access to both | General record substitution becomes a stronger account. Correct provenance remains a problem; a special self-role explanation becomes less necessary. |
| In the fully crossed five-arm design, a larger self-field shift survives balanced rehearsal, adequate access, and precise interaction estimates | Evidence for role-dependent vulnerability under those materials. The minimal three-arm study alone cannot support this stronger contrast. Neither identifies an identity or consciousness mechanism. |
| Explicit original-card wording removes ordinary-link claiming | Question specificity is a boundary or potential mitigation. Preserve this outcome; do not optimize wording for renewed claiming. |
| Third-party access fails, control quality fails, or uncertainty is too wide | The role comparison is not decisive. Preserve it and do not use attribution outcomes to choose a new setting or selectively retain episodes. |

Use separate material validation, any access-only calibration, independent
validation, and a fresh formal split. Freeze the primary contrasts, analysis
families, sample size, and handling of invalid comparisons before formal data.
Plan N from a stated precision or minimum meaningful interaction, including
paired dependence; if pilot variance is used, predefine a variance-only procedure
that does not expose attribution signs to the selector. The existing v4 N600
remains fixed and unchanged. No new N, dollar figure, or runtime promise is
justified until the readout count and engineering pilot are specified. Reusing
either checkpoint is possible, but a positive result on one remains a one-model
extension; two-model support for the new distinction requires testing both.
For workload accounting only, ten questions and two orderings give 60N receiver
readouts for three arms or 100N for five, versus 140N in the completed seven-arm
study. These counts exclude validation and do not translate directly into runtime.

## Why the other possible studies have lower priority

| Study | When it is needed | Principal limitation or decision |
|---|---|---|
| Relocate donor cache positions | To promote the positional explanation to a central causal claim | Moving rotary positions changes query-key scores and access. The runtime stores already-rotated keys: permuting K/V columns together does not relocate rotary positions and leaves joint attention unchanged when the mask follows. An explicit key-position transformation, zero-shift identity checks, masks and access/capability validation are needed. This is a distinct mechanism study. |
| Search a new Llama STATIC construction | To claim a matched steering result in both checkpoints | Requires a new finite search, independent validation and fresh paired observations; matching may still fail. Does not resolve role conflict, position, timing, or representation confounds. |
| Llama third-person donor text | To claim that this particular wording control generalizes | Useful bounded extension, but not a substitute for a conflicting third-party control. |
| New source headers or open reports | To broaden wording robustness or qualitative self-report evidence | Open reports need blinded coding and reporting limits; a third header adds less explanatory value than testing the main alternative. |
| Downstream choice task | To claim that reported current adoption changes actual decisions | Necessary for that behavioral claim, not for original-assignment errors. The old behavioral readout failed suitability and cannot simply be revived without validation. |
| Reflection deletion or replay | To claim that generated reflection text causes post-cut residue | Text replay, rewritten text and cached hidden-state history must be distinguished. Llama's contrary word residue makes a universal persistence story inappropriate. |
| More models or live loops | To broaden generalization or test responsiveness | Expands the scope without directly resolving the central retrieval explanation. Keep pilot evidence, including unmet thresholds, visible. |

For a later position study, the narrowest intervention would branch from the same
connected C48 state into original-position readout, relocated-position readout,
and RF. It would test readout-time positional dependence only. Moving the donor
throughout reflection as well would require starting from a common earlier P
state and would no longer preserve an identical C48. Keep the donor values and
nonpositional content fixed where technically possible, predefine the finite
offset/weight choices, and retain failed access matches as such.

## Changes that can be made with the completed evidence

Revise the abstract, introduction contribution paragraph, result ordering, and
discussion around the proposed source-attribution claim. Replace unrestricted
phrases such as "the route decides ownership" with condition-specific results.
Replace "what it wrote stays" with the observed selective residue, and distinguish
self-report from awareness. Describe the overlapping arrangement as an explicit
experimental choice. Keep STATIC's original 25% rule and all failed matches. Show
Llama's capability decline and contrary word endpoint, and distinguish findings
tested only in Qwen from replications.

The immediate next research choice is whether the paper will retain this bounded
empirical scope or add one targeted role-conflict study. Full manuscript editing
can then follow this outline while preserving the arXiv v1 package. No additional
experiment is required merely to report the existing supported effects.

Sources: [Qwen v2](../results/v2/confirmatory_v2_main.md),
[Qwen v3](../results/v3/confirmatory_v3.md),
[Llama v4](../results/v4/report.md),
[current setup](../../paper/sections/setup.tex),
[current interpretation](../../paper/sections/account_and_discussion.tex),
and [original design](../protocol/EXPERIMENT_DESIGN.md).
