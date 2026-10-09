# Paper story and evidence

Working synthesis for the two-model revision, October 9, 2026. The central claim
is that **reading another instance's internal memory can change reports of who
originally received its content, and successful content access does not guarantee
correct original attribution under the tested interface**. The completed studies
support this empirical claim. The evidence needed for stronger role-specific,
positional, persistence, and behavioral explanations is identified separately.

The title proposed for this revision is *Mine or Yours? Source Attribution in
Memory-Connected Language Models*. The preserved v1 manuscript and its historical
story plan remain unchanged. This synthesis consolidates the
[narrative proposal](story_revision_20261009.md) and
[full cross-model assessment](../results/v4/claims_and_matching_review.md).
Supplemental studies below are proposals, not completed evidence or executable
protocols with approved sample sizes and budgets. The latest bounded STATIC plan,
source-question anchors, planning sample sizes and full experiment ranking are in
[the supplemental study draft](../protocol/SUPPLEMENTAL_STUDIES_DRAFT.md).

## The complete story

Direct communication between internal states raises a source question: after one
system reads another's memory, can it still report which content originally
belonged to whom? The brain-bridging thought experiment motivates this question,
but the experiment concerns a measurable function. We give two model instances
different private rules and code words, retain the assignments as ground truth,
and test their reports after a memory connection. Each pair uses the same frozen
checkpoint. Qwen and Llama are separate studies of the same paradigm, not a
connection from a Qwen instance into a Llama instance.

The receiver A reads the partner B's fixed key-value cache alongside its own
while reflecting and answering. The partner's keys retain their original rotary
positions and the two cards share a layout. This deliberate overlapping-memory
arrangement is part of the tested intervention, not a neutral implementation of
every possible latent channel. When A names B's rule as the rule A was originally
assigned, its answer is false under known ground truth. Reporting B's rule as a
current priority is different: that is reported adoption, which may be legitimate
and is not yet an observed change in a downstream decision.

The first result is that original-attribution errors occur in both checkpoints.
At w1, where partner keys receive no extra attention-logit bias, Qwen and Llama
choose the partner's rule in 52.3% and 51.3% of answers, respectively, versus 0%
without the link. Qwen's stronger eligible setting reaches 97.1%. Both models
also report the partner's code word as their own. The statistical evidence is
within-model and paired; similar rates do not establish equal effective strength
or equal susceptibility across models. Capability screens, raw self/Robin
components, and donor-content access checks constrain the interpretation without
establishing that all other abilities are unaffected.

The second result is that content access and original attribution can separate.
With source-labeled text, both models answer questions about B's rule more
accurately than with the selected memory link, yet neither makes an original-rule
partner choice in those text samples. Thus stronger measured access need not
produce more original-rule claiming. In Qwen, a separately validated steering
direction matches a weaker memory link's mean access gain but produces different
attribution. Llama does not achieve that match, so the controlled equal-access
comparison remains a Qwen result. The text comparison changes representation,
position, timing, and source cues together; it does not isolate a single cause.

A more focused text intervention holds the message body fixed and changes the
header. Naming the source substantially reduces reported current-rule adoption
in both checkpoints. This is an intervention on a specific header and a specific
endpoint. It is not evidence that every source label is protective: Qwen's
self-labeled header contradicts a simple label-following prediction, and the
original-rule response to untagged text differs between the two checkpoints.

The third result identifies a temporal dependency. From the very same connected
reflection state, keep or cut the link before questioning. Original-rule partner
choices fall from 97.1% to 1.3% in the selected Qwen condition and from 51.3% to 0%
in Llama. Much of this error therefore depends on continued read access while
answering. Some reported current-rule influence survives the cut in both, whereas
positive adjusted code-word residue is not replicated in Llama. The effect is
selectively reversible. This contrast does not identify whether the remaining
influence is carried by generated reflection text, its cached hidden states, or
both, and it does not demonstrate long-term persistence.

These results make correct original attribution a distinct audit target for
internal-state communication. The contribution is the controlled known-owner
setting and the separation of access, attribution, and timing-dependent effects
across two checkpoints. It is not simply that a donor cache can influence an
answer, which has prior precedents, or that internal interventions can produce
false self-authorship. Relevant original sources and the narrow contribution
comparison are recorded in the [narrative proposal](story_revision_20261009.md).
No result here establishes failure of a particular deployed multi-agent system.

The remaining question is how to explain the attribution errors. One possibility
is general substitution between conflicting records: the interface supplies two
different self entries but two identical Robin entries. Another is that the role
or position of an entry makes some substitutions more likely. These explanations
are not mutually exclusive. A conflicting-third-party study can establish which
entries are vulnerable; a positional intervention can test a cause of that
vulnerability. The existing evidence does not yet establish a privileged self
mechanism or prove the two-cards-in-one-slot account.

## Existing evidence and the claim it licenses

Q2 denotes the [Qwen v2 main study](../results/v2/confirmatory_v2_main.md), Q3 the
[Qwen v3 confirmatory study](../results/v3/confirmatory_v3.md), and L4 the
[Llama v4 study](../results/v4/report.md). Each formal sample has 600 paired
episodes. They are separate samples. Rates below are descriptive choices averaged
over counterbalanced answer orderings; 1,200 answers do not make 1,200 independent
observations. Formal tests use episode-level contrasts and their original
within-study multiplicity families.

| Claim | Qwen evidence | Llama evidence | Current interpretation |
|---|---|---|---|
| The link produces false original-rule attribution | Q2 w2 primary M effect +55.834 [54.989,56.631]; Q3 w1 partner choices 52.3%, w2 97.1%; no-link 0% | L4 w1 primary M +10.823 [10.375,11.253]; partner choices 51.3%, no-link 0% | Supported in both checkpoints. The Q2 confirmatory effect and Q3 displayed rates are labeled separately. |
| Misattribution also affects a code word | Q3 w2 partner-word choices 77.5% | L4 48.75%; secondary M_WORD +7.006 [6.534,7.484] | Supported at the tested settings; not evidence that whole assignment cards move as one unit. |
| Higher measured access can coexist with lower original-rule claiming | Q2 TAG access 95.2%, claiming 0%; KV access 70.1%, claiming 95.8% | L4 TAG access 86.6%, claiming 0%; KV access 43.4%, claiming 51.3% | Shared descriptive dissociation. Each comparison uses its own same-sample arms. |
| Similar mean access can accompany different attribution across interfaces | Q3 KV/STATIC gains 4.081/4.179; partner choices 52.3%/0%; primary M contrast positive | STATIC gain 0.421 versus KV 2.490; formal mismatch 83.1%, also unmatched before formal collection | Supported by the particular Qwen comparison; unvalidated in Llama. STATIC's statistical contrast remains reportable. |
| A source header changes current-rule adoption | Q2 UNTAG 42.6% versus TAG 0.1%; primary M_NOW contrast positive | L4 42.2% versus 2.25%; primary M_NOW +3.725 [3.367,4.082] | Supported for this header intervention. Current-rule reports are not historical errors or measured downstream actions. |
| Original-rule errors depend strongly on retaining the link during questioning | Q3 w2 97.1% to RF 1.3%; primary FULL-RF M +54.775 [53.987,55.525] | L4 51.3% to RF 0%; primary FULL-RF M +10.893 [10.455,11.324] | Shared same-state timing intervention; strong reduction, not recovery of every endpoint. |
| Some current-rule influence survives the cut | Q3 RF choices 17.5%; primary RF-C0 M_NOW +13.342 [12.311,14.414] | L4 RF 7.08%; secondary M_NOW +1.917 [1.631,2.214] | Shared qualitative pattern with different magnitudes and original test status. |
| Positive adjusted word residue survives the cut | Q3 RF choices 17.5%; descriptive M_WORD +10.490 [8.99,12.03] | L4 RF choices 1%, but secondary M_WORD -0.330 [-0.495,-0.162] | Positive adjusted residue does not replicate. A small raw self-component shift is still present. |

Intervals are pointwise episode-bootstrap intervals from the cited reports, not
simultaneous confidence intervals. Logit effects are not a calibrated scale for
ranking the two models. An observed zero choice rate is not a universal guarantee.

Supporting and boundary evidence should stay visible:

- **Content specificity:** changing donor content changes measured access in both
  models. The frozen content-counterfactual test concerns access, not a direct
  test of the mechanism producing ownership reports. Llama's formal CF capability
  decline is about 5.08 percentage points, slightly outside the 5-point screen.
- **Control quality:** Llama's selected KV condition lowers CAP from 94.75% to
  89.75%, exactly the screen boundary; the independent pre-formal core gate passed.
  The small 18-item CAP bank cannot establish general capability equivalence.
- **Third-person wording:** Qwen's saturated w2 retention test passes with 97.2%
  versus 97.1% claiming. The w1 contrast is lower and access differs. Llama has no
  corresponding trial. This does not establish complete invariance to wording.
- **Rehearsal:** a separate Qwen balanced-rehearsal sample retains the effect.
  It is not an independently validated Llama control or a conflicting-Robin test.
- **Text boundaries:** Qwen UNTAG produces 14.6% original-rule partner choices;
  both Llama text arms have 0%. Qwen's self-header reduces rather than increases
  current adoption. These findings constrain simple universal label accounts.
- **Open reports:** post hoc semantic coding of 300 Qwen w2 reports finds 296
  claiming the partner word and 250 both claiming it and denying an anomaly.
  Baseline denial is already common, there is no human coding or positive
  introspection control, and Llama did not collect these reports. The evidence
  concerns reported content, not unobserved awareness.
- **Two-way extensions:** Qwen's N80 fixed-memory pilot shows 94.4% swaps. Its
  live-loop assigned-rule criterion was not met; a current-rule effect remains
  exploratory. Llama did not test either. Fixed-memory misattribution does not
  require a responsive donor; the additional role of responsiveness is unsettled.

The [full assessment](../results/v4/claims_and_matching_review.md) retains the
exact gate history, STATIC sensitivity, third-person protocol distinctions, and
other controls. They should not be compressed into an all-or-nothing replication
label or removed because they complicate the narrative.

## Evidence still needed and why

The current bounded empirical claim has evidence. Additional studies are needed
for stronger explanations, not to make an already observed effect count as real.

| Priority and question | Missing evidence | What a suitable result would license | What would remain open |
|---|---|---|---|
| First proposed follow-up: is this general conflicting-record substitution? | Make the donor's Robin record conflict while A's original record stays fixed; explicitly query which original record is being recalled | If an accessible donor-Robin entry contaminates recall of A's Robin entry, general provenance failure extends beyond the receiver's self field | Relative vulnerability of self and other requires a symmetric design and balanced rehearsal; three arms do not establish it |
| Conditional: is the self role more vulnerable? | Independently cross self conflict and Robin conflict, with balanced materials and access checks; estimate the role interaction | A precise interaction supports role-dependent vulnerability in this task | Identity, awareness and every representation or salience explanation remain outside the result |
| Conditional: do overlapping positions cause the difference? | Change donor rotary-key positions while holding nonpositional content fixed, with quality and access checks | A controlled change in attribution constrains a positional account | An attribution reduction accompanied by lost access is not a source-preservation result |
| Conditional: does the matched STATIC result generalize? | A new finite access-only calibration and independent match validation in Llama, followed by fresh paired formal data | A successful match and attribution contrast extends that specific controlled comparison | Signal type, location and timing are still not all isolated; failed matching remains a possible outcome |
| Conditional: does reflection text cause retained influence? | A controlled intervention separating reflection text from the hidden-state history that generated it | Identifies a contribution of the manipulated component to RF outcomes | Observational grouping by word mention and simple text replay alone do not isolate all carriers |
| Conditional: does adoption change action? | A downstream decision measure that passes independent suitability checks | Behavioral consequences beyond current-rule reports | Historical attribution remains a distinct endpoint; the retired behavioral readout cannot be assumed valid |
| Later scope extension: how broadly does the effect generalize? | Different tasks, memory layouts or actual communication interfaces; further checkpoints as appropriate | Generalization to each newly tested setting | Two families in one artificial task are not a general LLM law |

Role conflict and positional placement answer different questions. General record
substitution and positional dependence can both be true. An experiment should not
be judged by whether it preserves a preferred explanation of the self.

## The proposed first study in concrete terms

Hold A's original record fixed: own entry a, Robin entry r. In the original donor
record, B's own entry is b and Robin is r. In the conflict variant, B's own entry
remains b but Robin is d. Use the fourth physical candidate d rather than silently
collapsing answer identities. The three receiver arms are C0, original KV, and KV
with the conflicting donor Robin entry. The donor variant changes both rule and
word entries under a defined material policy; A's external input and answer
orders remain paired.

For each content type, independently ask about four fields: A's original record
of A, A's original record of Robin, B's original record of B, and B's original
record of Robin. Thus truth is record-qualified, not an ambiguous global fact
about a Robin with two inconsistent assignments. The last two questions measure
donor-record access. Native baselines check that each unlinked instance can
answer about its own record; A is not expected to know B's private record before
transfer. Fresh ordinary-link trials with the new questions are necessary.

The new score compares donor versus receiver answers separately for each field.
The old Robin-subtracted M cannot serve as the sole outcome once Robin is treated.
Parallel wording, answer/role counterbalancing, rehearsal checks and independent
question branches are required. The updated minimal package adds the original
START and WORD self questions as secondary anchors: eight field probes, two CAP
questions and two anchors give twelve readout types. They reveal whether explicit
source qualification changes the original error. Any additional nonconflicting-
memory control increases this count. The proposed planning N is 600 per model;
the precision assessment, execution protocol and budget still require completion
and approval before collection.

Interpret the possible outcomes in advance:

- If both conflicting entries move toward the donor, favor a broader record
  substitution account while retaining the measured original-attribution error.
- If explicit original-record questions remove even the ordinary-link error,
  report question specificity as a boundary or potential mitigation. Do not
  search for a wording that restores an attractive effect.
- If Robin does not move, first check whether its conflicting donor entry was
  accessible and sufficiently represented. Its absence alone does not establish
  special self vulnerability.
- To estimate special vulnerability, use the fuller self-conflict by Robin-conflict
  design plus C0, five arms in total, and validated balanced rehearsal. It requires
  a new representation of shared physical answers rather than the old unique-owner
  labels. A nonsignificant interaction is not proof of equivalence.
- If access, suitability, control quality or precision is inadequate, retain the
  inconclusive result. Do not tune on attribution effects or discard episodes.

New material validation, any access-only calibration, independent validation and
formal data must use separate splits. Freeze the hypothesis, tests, meaningful
effect or precision target, N, and stopping rules before formal outcomes. There
is no approved extension of the completed v4 run or its spending cap in this
document. Detailed engineering constraints are in the
[experiment proposal](story_revision_20261009.md).

## How this becomes the paper

The main text should lead with the known-owner task and the two-model effect,
then compare access and attribution, examine source headers, and present the
same-state link-cut intervention. Put the competing record-substitution and
positional accounts in discussion with explicit predictions. Keep Qwen-only
open reports and reciprocal pilots as clearly labeled extensions, and preserve
all failed matches and contrary endpoints in the evidence record.

The main figures should follow that order: task and core effect; access and
attribution with match status; and link-cut outcomes by endpoint and model.
Use the existing restrained figure style. Add a mechanism figure only when the
corresponding evidence exists. The current paper's supported conclusion is the
separation of access and correct attribution under this interface. A role-conflict
study could explain the scope of that separation; a positional study could then
test one cause. Neither future result is assumed in the current story.
