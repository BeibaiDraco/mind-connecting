# Post-collection evidence and paper story

Assessment date: 2026-10-12 UTC. This document proposes the paper's organization after the completed v5 collection. It does not amend any protocol, turn a failed gate into a pass, authorize more compute, or replace the preserved manuscript. The PI requested a thorough analysis and paper assessment after authorizing final instance destruction.

## Recommendation

Develop the paper around **source attribution under internal-memory communication**, with false self-attribution as the starting phenomenon and conflicting third-party records as the key explanatory extension. The evidence supports a broader source-record interference problem. It does not establish a special defect of the self, a positional mechanism, consciousness, or changed downstream behavior.

The recommended central statement is:

> In the tested memory-sharing interface, a receiver can acquire partner content while giving incorrect answers about the original source of that content. This vulnerability extends to conflicting third-party records, and content-access scores alone do not characterize attribution across the tested interventions. Readout-time disconnection and explicit text headers alter different endpoints.

The new conflict experiments make the empirical account more informative while making the old self-specific explanation less defensible. The correct response is to revise the explanation, not to search for another result. All planned GPU collection is finished. No additional GPU experiment is needed to report this bounded result, provided the manuscript gives the qualifications below equal visibility.

Suggested title: **Mine or Yours? Source Attribution in Memory-Connected Language Models**.

## What was analyzed and what remains separate

The new original-v5 Qwen provenance study and the two separately frozen Llama continuation studies were recomputed offline from complete raw records. Production summaries were checked against independent episode/physical-candidate calculations. The analysis keeps both answer orderings inside the same episode, uses all 600 paired episodes, and retains the frozen two-sided tests, 10,000-draw percentile bootstrap intervals and multiplicity families. Intervals are pointwise, not simultaneous Holm intervals.

Qwen original v5 and amended Llama provenance have separate report layers and fixed families of two primary and six secondary slots. Unavailable slots remain unavailable; they are not replaced by amended observations. The STATIC primary and two-test secondary family are separate again. The continuation is not retrospectively labeled an original-v5 gate-passing experiment.

Earlier Qwen v2/v3 and Llama v4 evidence is taken from the existing audited reports; this assessment does not claim a fresh raw recomputation of every historical study. Different cohorts are not pooled, raw-logit magnitudes are not ranked across checkpoints, and nominally identical weights are not assumed to give equal effective intervention strength.

Sources for the new calculations:

- [Provenance analysis](../results/v5/provenance_post_collection_20261012.md), with its compact numerical companion.
- [STATIC analysis](../results/v5/static_post_collection_20261012.md), with its compact numerical companion.
- [Historical two-model assessment](../results/v4/claims_and_matching_review.md), [Llama v4 report](../results/v4/report.md), and [Qwen v3 report](../results/v3/confirmatory_v3.md).
- [Prospective continuation contract](../protocol/PROTOCOL_V5_CONTINUATION.md), especially analysis and interpretation limits.

## Main evidence, with the necessary boundaries

| Question | Evidence | Interpretation licensed |
|---|---|---|
| Does connected memory change reports of the receiver's original assignment? | Historical Qwen v3 w1 donor-rule choices 52.3%; Llama v4 w1 51.333%; both no-link baselines 0%. Qwen's stronger w2 condition reaches 97.1%. | A replicated task-specific attribution error. Similar percentages are not an equivalence test across models. The 97.1% rate is Qwen at its stronger setting, not a general rate. |
| Is this restricted to self-related content? | Under explicit receiver-original-card questions, adding donor-only Robin conflict raises wrong-source Robin-rule choices from 0% to 49.917% in Qwen and 48.500% in Llama. | Susceptibility extends to a third-party field and is compatible with broader record substitution/interference. The asymmetric three-arm design does not estimate a balanced self-versus-other causal interaction. |
| Does high measured access entail misattribution? | In the earlier same-cohort comparisons, tagged text gives rule-access accuracy 95.2% (Qwen) and 86.583% (Llama), with 0% assigned-rule donor choices. Memory-link arms make attribution errors with lower access accuracy. | Access success and correct source attribution are distinct audit outcomes. Text and cache conditions differ in more than a single mechanism. |
| Do matched STATIC and cache interventions differ? | Qwen v3 formal mean access gains 4.081 versus 4.179 nats, with 52.3% versus 0% donor-rule claiming. New Llama STATIC gains 2.5643 versus 1.5354: about a 40.1% gap, outside the frozen 25% tolerance. | Qwen supports a contrast at closely matched mean rule-access gain. The fresh Llama data do not replicate that matching condition, despite a strong attribution contrast. |
| What does the new Llama STATIC result add? | Assigned-rule donor choices 49.917% for KV and 0.583% for STATIC; descriptive donor-rule access accuracy 42.083% versus 47.333%. Primary KV minus STATIC M is +10.1916 nats [9.7500, 10.6501]. | STATIC can support content access with very little assigned-rule claiming. The opposite ordering of access accuracy and claiming is informative, but accuracy cannot replace the preselected logit-gain matching measure. |
| Does the ongoing link matter? | Same-reflection-state disconnection reduces Qwen strong-setting assigned-rule claiming from 97.1% to 1.3%, and Llama from 51.333% to 0%. Some current-rule influence remains in both. | A readout-time intervention changes attribution. It does not prove permanent memory overwriting, complete recovery, or a causal effect of generated reflection text. |
| Do explicit source labels matter? | Identical-body tagged versus untagged text changes current-rule adoption: Qwen about 0.1% versus 42.6%; Llama 2.250% versus 42.167%. | A bounded header effect on reported current adoption. This is different from historical attribution and has not been shown to change a later decision. |
| Does code-word residue replicate? | Qwen has positive post-cut adjusted residue; Llama's prespecified adjusted word residue is negative, despite 1% donor-word choices. | Selective, endpoint-dependent reversibility. A universal 'what it wrote stays' claim is not supported. |

### The new third-party result should change the paper's explanation

The receiver's original card stays fixed, and the donor-only intervention changes its Robin entry. The question explicitly asks which rule the receiver's original card assigned to Robin. The primary outcome compares the donor-Robin candidate with the receiver-card Robin candidate. This supplies known original-record ground truth; it is not a question with two equally correct current facts.

The original Qwen primary contrast is +29.5539 nats, 95% CI [28.1747, 30.9097], with fixed-family Holm p = 7.99e-180. The separate amended Llama contrast is +10.8586 [10.4084, 11.3046], Holm p = 8.36e-204. More interpretable descriptive paired wrong-choice changes are +49.917 percentage points [46.50, 53.25] and +48.500 points [45.08, 51.92], respectively. Both are actual wrong-source choices, not merely movement of a logit score below the decision boundary.

This directly addresses the earlier limitation that Robin was consistent across cards. Accurate answers to a nonconflicting Robin question could never establish that errors were confined to the self. With a conflicting Robin field, both models show substantial source-record errors. That weakens the interpretation that self status is necessary for the phenomenon. It does not establish a unique underlying algorithm or rule out additional self-related contributions.

Keep the minimal design's limitations visible: own-content conflict is already present in both linked arms, and rehearsal is not balanced between roles. Do not present the new study as a fully crossed role experiment or use it to conclude that self and third-party vulnerabilities are exactly equal.

### Explicit original-record wording is not an established repair

The prespecified old-question versus source-qualified-question interactions do not survive their fixed Holm adjustments. This is not evidence of wording equivalence. More importantly, fewer donor-own choices can be offset by more choices of a different wrong candidate: Qwen's qualified self questions often elicit the Robin candidate. Report full candidate distributions and actual own-record accuracy before describing any prompt as a mitigation. The positive Robin-conflict result itself uses explicitly qualified questions, so wording specificity does not eliminate all source-record interference.

### STATIC: a stronger control with an important nonreplication

The newly selected Llama STATIC direction passed the original mean rule-access matching criterion in its N80 development/validation sample (23.425% relative gap). Formal N600 gains separate more: approximately 40.1%. Preserve both facts. The N600 does not authorize another search, a changed target, a wider tolerance, or relabeling the comparison as equivalent.

The primary M contrast includes both self and Robin components: KV minus STATIC changes the self component by +9.1998 nats and the Robin component by -0.9917, giving M = +10.1916. Show these components as well as choices; a control-subtracted index is not itself an ownership-error percentage.

STATIC is not inert: seven of 1,200 assigned-rule answers choose the donor, and its descriptive M shift from C0 is +0.6312 nats [0.4859, 0.7777]. Current-rule donor choices reach 8.750%, although its Robin-adjusted current-rule contrast has an interval spanning zero. These details rule out a blanket claim that residual steering cannot affect attribution.

The formal STATIC result supports the broader access/attribution distinction but cannot cleanly identify the causal contribution of route at matched logit access. Even a successful match would concern one mean rule-access statistic, not all content, word access, timing, positions, or general intervention strength. Do not replace a failed frozen match with the favorable fact that STATIC's access choice accuracy is higher.

### Capability and WORD limitations are part of the result

Original Llama v5 capability gates failed: provenance ordinary KV dropped 5.625 percentage points; STATIC's KV and donor-own counterfactual prerequisites dropped 6.25 and 5.9375 points. The PI approved a separately frozen prospective continuation with those named exceptions. That history remains in Methods and the evidence table, even though new formal point estimates are smaller. A point estimate below five points is not an equivalence test and does not retroactively pass an old gate.

For example, new STATIC formal KV CAP loss is 4.625 points with a 95% interval spanning approximately 3.833 to 5.417 points; STATIC loss is about 2.208 points. The interventions do not have equal capability costs, and a small common-knowledge screen does not measure all unrelated abilities.

Qwen's provenance donor-own WORD access limitation persists in the formal data. It must be reported by field: useful access to the donor's Robin word does not repair inadequate donor-own word access. Neither drop an unfavorable word endpoint nor let an inaccessible-field null establish correct attribution. The two models' word findings belong beside their respective access diagnostics.

## A coherent main-text argument

1. **Set up the test with known records.** Two independent instances of a frozen checkpoint receive private cards. Explain who was assigned each rule/word, what is shared, and the distinction between access, original-record attribution, and current-rule adoption. Mention the brain-bridge motivation briefly, then state the measurable question.
2. **Establish the original attribution phenomenon across checkpoints.** Show Qwen and Llama at their specified conditions, no-link baselines, effect intervals, actual error rates, CAP and format. Keep Qwen's stronger condition and dose curve identified as Qwen-only.
3. **Use third-party conflict to test the main alternative.** Introduce the fixed-receiver-card, donor-only Robin manipulation. Show original-record errors in both models and explain why the effect is broader than a necessary self-specific failure. Identify original versus amended protocol status.
4. **Separate content access from correct attribution.** Use same-cohort text contrasts and the STATIC comparison. Give Qwen's matched evidence and Llama's formal mismatch side by side rather than hiding the latter. Keep source-header effects on current adoption distinct from old-assignment errors.
5. **Intervene on whether the link remains available at readout.** Present paired FULL/RF evidence for both models and the different rule/current/word endpoints. Distinguish reported adoption from later action and selective residue from a permanent overwrite claim.
6. **End with the audit implication and limits.** Correct transfer alone is insufficient to certify correct source attribution under this interface. Positional overlap and retrieval/record interference remain possible explanations, not an identified universal mechanism. Other cache placements and deployed systems require their own measurements.

Open reports, grammatical-person controls, balanced rehearsal and reciprocal/live-loop pilots remain useful supporting evidence. They should no longer displace the new two-model provenance result from the main argument. Preserve their original statistical status and contrary findings.

## Proposed abstract for the next manuscript version

When language models share internal memory, does successful content transfer preserve its original source? We give two frozen instances private assignment records and allow a receiver to attend to its partner's key-value cache. Across Qwen3-4B and Llama-3.1-8B, the receiver can report the partner's rule as its own original assignment. Separate source-conflict studies show that the vulnerability extends to third-party records: when only the donor's Robin entry is changed, wrong-source answers about the receiver's original Robin record rise from zero to 49.9% and 48.5%, respectively, despite explicit original-record questions. Content access and correct attribution also separate across the tested interfaces. Tagged text supports high access without assigned-rule claiming; a steering comparison is matched in mean rule-access gain for Qwen, while the corresponding Llama formal comparison remains unmatched. From the same reflection state, disconnecting the cache before questioning sharply reduces original-rule claiming, although other endpoints show selective residue. Llama follow-ups were collected under a separately frozen continuation retaining documented capability-gate exceptions. These findings motivate provenance checks alongside transfer measurements for internal-state communication. They do not identify a self-specific or positional mechanism, establish downstream behavioral effects, or generalize to untested interfaces.

## Manuscript changes, in priority order

The current `paper/main.pdf` was built on October 8 and presents a one-model narrative. Adding a paragraph about Llama at the end would not be sufficient. The scientific argument needs updating, while the restrained visual style can remain.

| Priority | Location | Concrete revision |
|---|---|---|
| Must | Title, abstract, contribution paragraph | Name source attribution and two checkpoints; incorporate third-party conflict; remove a demonstrated 'default-to-mine' mechanism from the takeaway. |
| Must | Setup, experimental sequence and evidence appendix | Add Llama v4, original Qwen v5 and separate Llama continuation, with an explicit cohort/protocol/qualification table. Keep N600 as episodes, not 1,200 independent answers. |
| Must | Results opening | Replace unrestricted 'errors stayed confined to ownership' with the qualified original nonconflicting-control observation, followed by the new conflicting-third-party result. |
| Must | STATIC/route subsection and figure caption | Replace 'Ownership follows the route, not access' with a condition-specific access/attribution result. Mark Qwen's matched cohort and Llama's approximately 40.1% formal gap clearly. |
| Must | New provenance result subsection | Present physical candidates, donor-only manipulation, explicit original-record question, paired effect and actual wrong-choice interval; keep Qwen WORD limits and protocol amendments visible. |
| Must | Link-cut subsection and Figure 5 | Replace 'what it wrote stays' with 'cutting the link changes attribution and leaves selective residue.' Label Qwen's post-treatment word-mention grouping as association. Include Llama's contrary adjusted word residue. |
| Must | Account and discussion | Recast 'two cards, one slot' as a hypothesis. Discuss general source-record interference before a self-specific interpretation. Do not state that the study falsifies human brain-bridge or consciousness theories. |
| Must | Related work and novelty | Replace the broad 'no one has asked whose content' claim with the precise combination of known original records, source-conflict controls, cross-checkpoint evidence and same-state timing intervention. |
| Should | Main figure selection | Add the two-model and third-party results using the existing typography/colors. Separate cohorts; do not overlay text and cache points from different studies as though they were one paired experiment. Move Qwen-only qualitative and reciprocal pilots to clearly labeled supporting panels/appendix if space requires. |
| Should | Limitations and abstract qualifiers | Retain formal match drift, named CAP exceptions, WORD access limitations, one artificial task per checkpoint, non-equivalence of null tests, no downstream decision measure, and interface dependence. |

A separate [line-specific paper audit](../reviews/paper_evidence_audit_20261012.md) gives locations and reasoning. This assessment does not silently rewrite the published/preprint source. It supplies a concrete next-version narrative and numerical evidence package.

## Novelty check against primary sources

A targeted original-source check supports a narrow contribution, not a priority claim. Ackerman and Panickssery already manipulated self-authorship judgments by steering Llama3 activations ([ICLR 2025 paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/d560f94c582033e6d8eb0c97cdd4f721-Paper-Conference.pdf)). Lindsey showed that earlier concept injection can make externally prefilled text be reported as intentional ([2025 study](https://transformer-circuits.pub/2025/introspection/index.html)). Cheng and colleagues report donor-consistent registry answers under mismatched relayed caches ([Appendix C.2](https://arxiv.org/html/2608.04893v2)).

The defensible contribution is the controlled original-source attribution problem and its combination of known private records, role-conflict extension, access/header contrasts and same-state disconnection, with two-checkpoint evidence and explicit nonreplications. Do not claim to be the first to cause false self-attribution or donor-following through latent communication. This targeted check is not a systematic search of all prior work.

## Remaining work and experiment decision

The data are sufficient to develop the bounded empirical paper. Immediate work is manuscript integration, consistent tables/captions, and final scientific proofreading. No new parameter search, model rental, sample expansion or prompt optimization is recommended on the basis of these outcomes.

A new study would be needed only to pursue a stronger question: a balanced role/conflict design for self-specificity, an access-preserving position intervention for a positional cause, or a validated downstream decision task for behavioral impact. These are future research options, not hidden prerequisites for reporting the current findings. More checkpoints or realistic tasks would broaden generalization, but cannot retroactively repair the completed formal match or erase capability exceptions.

The main remaining scientific risks are limited task/interface scope, imperfect access measurement, differing capability costs, and modest novelty if the paper is framed merely as donor following. The new third-party result should be treated as a constraint that clarifies the story, not as proof of a unique mechanism. A focused provenance paper is more defensible than the current mixture of empirical results and strong self/brain-bridge interpretation.

Visual review sampled current PDF pages 1, 2, 6 and 8. The sampled pages render legibly and do not call for a decorative redesign. This is not a claim that all 35 pages have undergone a new visual certification. The main issue identified here is scientific content and emphasis, not polish.

## Durable reproduction archive

The three CPU-only analysis/report scripts and their full derived numerical outputs are preserved under `/Volumes/VERBATIM SD/mind-connecting-data/engineering/analysis/postcollection-20261012/`. Its manifest records each file's size and SHA256. The short private paths in the detailed reports identify the executed working copies; the SD archive is their durable copy. Raw run directories and their frozen summaries were not overwritten. Repository report/JSON sources remain separate from this private archive.
