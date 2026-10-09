# Supplemental studies for source attribution

October 9, 2026. **Proposal for PI review; not frozen or authorized for paid
execution.** This plan preserves the completed protocols, results and v1
manuscript. It answers the PI's request for an economical STATIC decision and a
complete assessment of further experiments. The current empirical story is in
[the evidence roadmap](../paper/story_and_evidence.md).

## Recommended package

The principal addition should be a source-qualified conflicting-record study in
both checkpoints, with a small set of original questions retained as anchors.
Llama STATIC merits one capped feasibility branch; fresh formal comparison is
conditional on an independently validated match. Qwen's existing successful
matched comparison does not need to be rerun merely for symmetry. These two
studies answer different questions and neither is a prerequisite for honestly
reporting the existing core effect.

Do not add a new model, a live loop, a downstream action task, a position study,
and a reflection-mediation study to the same package. They require different
contracts and would expand the manuscript's claims faster than its explanatory
precision. The main allocation priority remains record provenance. The STATIC
pilot may run first for operational convenience while source-study tooling is
prepared; its outcome does not determine whether the source study is run.

## Existing data before new GPU work

The old layer-21 scan already covered 16 gains. Its g0.7 access increment was
0.3456 and g1.0 was 0.3878 against the same-sample KV target of 2.8003. At g1.0,
label-mass drop was 5.817 percentage points, beyond the 5-point tolerance, although
CAP remained acceptable. These facts favor trying a small range of layers over
another open-ended gain increase at layer 21. They do not prove that any higher
gain or other layer must fail. See the pinned
[matching artifact](../../configs/v4/artifacts/match.json).

The calibration metadata identifies the approved checkpoint, complete 60-episode
split, native assets, and no unusable directions. The engineering review confirms
passive simultaneous recording at multiple layers and correct layer-specific
calibration use. Before a new launch, check rule and A/B balance, donor note
fidelity, existing access by rule, and frozen hashes. The current report already
contains raw self/Robin components and control quality. Preserve complete
summaries; do not select or remove episodes based on any attribution result.

An empty unusable-direction list does not establish direction reliability. Saved
vectors are normalized, and raw calibration activation trajectories were not
retained, so their final norms cannot recover original signal strength or give
an independent resampling estimate of directional stability. A fresh multilayer
calibration is preferable to claiming the saved vector has been fully diagnosed.

Any additional decomposition of existing CF attribution, answer-order effects,
or donor-note content must be labeled exploratory. The frozen CF access test
must not be retrospectively redefined as an ownership-mechanism test.

## STATIC as a capped feasibility study

### Fixed question

Can a rule-conditional static direction in Llama achieve approximately the same
mean rule-access gain as the fixed KV-P w1 interface without exceeding quality
tolerances? If so, do the selected interventions differ in original-rule
attribution on fresh data?

The fixed target remains KV-P w1. Keep the existing raw rule-conditional direction
construction, v1 materials, native serialization, reflection length, and injection
timing. Do not switch to a self-authorship direction, an EMA construction, a lower
KV target, or trained interface after a failed gate. Such changes answer different
questions and are outside this attempt. Changing the selected layer makes this
a new calibrated comparison, not a rerun of the original layer-21 condition.

STATIC is conditional on the rule, not the code word. ACC_WORD is a diagnostic;
matching ACC_RULE does not license a claim of matched word transmission or turn
a STATIC WORD null into evidence of preserved word provenance.

### Finite search and one untouched validation sample

1. **Calibration:** 60 fresh episodes, observing one-indexed layers
   `{16, 21, 27}` (tensor indices `{15, 20, 26}`, preserving v4's one-indexed
   configuration convention). These bracket the original relative depth with approximately
   half-depth and five-sixths-depth points. They are design choices, not claimed
   optima. Three passive hooks collect all layers during the same C0 trajectories;
   no three-fold replay is required. Each layer gets its own calibration file and
   hash. If a layer lacks any required raw rule direction, omit the entire layer
   and record the unavailability, not a subset of its rules or episodes.
2. **Coarse selection:** 40 different episodes, each with C0, fixed KV-P w1,
   and gains `{0.1, 0.3, 0.5, 0.7, 1.0}` at each available layer: at most
   15 STATIC candidates. Read only ACC_RULE, ACC_WORD, CAP0 and CAP1, under the
   same two orderings. No M, NOW or ownership answer is a selection input.
3. **Conditional deterministic refinement:** when no coarse candidate matches
   and an eligible bracket exists, test its midpoint, with at most two additional
   midpoint gains in total. A bracket consists of adjacent
   tested gains within one layer whose endpoints both pass quality screens and
   whose measured gains straddle the positive same-sample KV target. Choose a
   bracket by the tuple `(maximum endpoint relative gap, gain interval width,
   abs(layer-21), layer, lower gain, upper gain)`. Test its midpoint on the same
   selection split and recompute eligibility and brackets. An ineligible midpoint
   breaks its enclosing bracket; it cannot be skipped. Stop refinement as soon
   as a qualified 25% match appears, no eligible bracket remains, or two midpoints
   have been tested. No repeated midpoint, extrapolation beyond
   the tested bracket, gain above 1, new layer, or additional split is allowed.
4. **Select once:** among eligible candidates, minimize absolute mean access-gain
   difference from KV; ties prefer lower gain, then smaller distance from layer
   21, then lower layer number. If no candidate is within 25%, stop this branch
   after saving all results. Do not choose a lower target to manufacture a match.
   Freeze the selected candidate and all four validation arms before validation.
5. **Independent validation:** 80 new episodes, C0, KV-P w1, the selected STATIC,
   and KV-P w1 with the existing donor-content counterfactual. Require complete
   data, C0 CAP of at least 90%, intact formats, acceptable CAP for KV/STATIC/CF,
   finite positive KV and STATIC mean rule-access gains, a one-sided 95%
   episode-bootstrap lower bound above zero for KV access gain, a one-sided 95%
   episode-bootstrap lower bound above zero for rule content-counterfactual
   validity, and the same 25% match.
   Report word specificity separately. Failure ends this attempt: no runner-up,
   extra validation batch, recalibration or new search is permitted.

At both selection and validation, denote the same-split mean access increments
over C0 by `G_KV` and `G_STATIC`. Both must be finite and strictly positive, and
matching requires `abs(G_STATIC - G_KV) / G_KV <= 0.25`. A nonpositive or
non-finite KV target ends the selection branch rather than changing the
denominator or selecting an alternative target.

The quality screens are CAP accuracy drop at most 5 percentage points, total
answer-label probability at least 90%, and label-mass drop at most 5 points,
relative to same-stage C0. Selection screens STATIC candidates; independent
validation explicitly checks target KV and CF as well. Checking CF quality here
is a stated prospective requirement, not a reinterpretation of the old v4
validity Boolean, which did not include that quality check in its gate.

As in v4, the 25% criterion is a point-mean operational match, not a statistical
equivalence proof. Report paired uncertainty and by-rule access diagnostics without
selecting favorable rules. Do not add a stricter equivalence gate after seeing
validation; a claim requiring statistical equivalence would need a prospectively
specified margin, test and precision plan before launch.

### Conditional formal comparison

Only after successful validation, collect C0, KV-P w1 and the frozen STATIC on
fresh paired episodes. TAG, UNTAG, RF and other original arms need not be repeated
for this question. The primary contrast is KV minus STATIC on the original
assigned-rule M; retain raw components, observed choices, capability, access and
the formal matching recheck. Do not select episodes or repair formal mismatch.
NOW and WORD are secondary diagnostics; there is no matched word-route claim.

A fixed **N=600** is the proposed planning default, consistent with the completed
formal studies and free of an attribution-based advancement rule. It is not an
approved run or a guarantee of power or equivalence. Before freezing, specify
the exact secondary family and precision objective; change this planning value
only before new attribution outcomes are inspected. Collect all fixed N even
if interim claiming is small, large, or absent, subject to technical and budget
failure handling.

If STATIC now produces similar claiming, report that the previous layer-21
condition was not an adequate test of the matched claim. If it remains different,
the particular equal-access interface comparison gains a second-model result.
If selection or validation fails, report no match within this finite search and
continue the paper without a two-model matched-route claim. None of these outcomes
alone establishes a positional or self-specific mechanism.

## Primary supplement on record provenance

Run the same semantic design separately in Qwen and Llama, using fresh episodes
and the existing checkpoint-specific native templates. The recommended scope is
three arms per model: C0, original KV-P w1, and KV-P w1 with donor-only Robin
conflict. Qwen w1 avoids the near-ceiling w2 condition and is already a tested
setting; Llama w1 is its selected eligible setting. These fixed weights are a
prospective choice, not a guarantee of equal attention or ability across models.

Use the same four physical candidates in all arms. A's original record contains
own a and Robin r. B's original record contains own b and Robin r, or own b and
Robin d in the conflicting variant. A's complete external input remains unchanged.
The manipulation changes the donor's Robin rule and word under a frozen material
contract, not the identities of answer options at scoring time.

For each rule and word, collect four source-qualified questions: A's original
record of A; A's original record of Robin; B's original record of B; B's original
record of Robin. Add CAP0/1 and **the original START and WORD self questions as
secondary anchors**, for twelve readout types. Every question forks an independent
clone of that arm's C48 state. Do not collect the ambiguous old global Robin
question as if it supplied the old M in the conflict condition.

The anchors matter: old questions may show errors while explicitly naming the
original record removes them. That is a question-specific boundary or candidate
mitigation, not a failed study to be rescued by another prompt. It also prevents
silently calling a new source-qualified readout an exact replication of START.

Keep the current v1 material policy for the minimal provenance study and record
the unequal rehearsal of self and Robin as a limit. Do not infer self-specificity
from a negative Robin result. A stronger comparison requires the fully crossed
self-conflict by Robin-conflict design plus C0, with balanced rehearsal and
adequate access for both fields; it is a different five-arm study to choose before
collection, not an automatic escalation after the three-arm result.

The primary proposed test is the added Robin-conflict effect on receiver-original
Robin rule recall: the paired change in `z(d)-z(r)` between conflict KV and original
KV. Report a separate self score `z(b)-z(a)`, word analogues, donor-record access,
and actual source-error rates. A comparison for each checkpoint forms a two-test
primary family. Freeze a complete secondary family, including anchor/readout
contrasts, before the formal run. No old Robin-subtracted score can substitute
for this analysis once Robin is manipulated.

Control this two-test primary family with Holm's procedure. If prespecified
validity failure makes a checkpoint's comparison unavailable, keep the family
size of two (use p=1 solely for multiplicity bookkeeping), report that comparison
as unavailable, and never impute an effect or observation. A positive logit
contrast alone is a shift in answer preference; describe increased erroneous
choices only if observed source-error rates also increase, with uncertainty.

First validate question semantics, option tokenization and baseline recall on
separate materials, then validate donor access and quality on an untouched split.
A should recall its own original card and B should recall each version of its
own card; A's lack of access to B's private card without a link is expected.
Access to donor-own and donor-Robin fields must be reported separately. A field
with failed access cannot support an intact-boundary interpretation of its null.
No pilot selection or progression rule may use the attribution effect's sign or
significance. If the fixed interface cannot support the required checks, report
the limitation for that model; do not tune until Robin or self moves.

The planning default is **N=600 fresh formal episodes per checkpoint**, subject to
an explicit prelaunch precision assessment and final freezing. It is not justified
by copying the old effect size into a new question, nor a promise to resolve small
role differences. The exact material-validation sizes, access thresholds, primary
and secondary families and technical failure rules must be completed in the
execution protocol. They cannot be silently imported from v4's different readouts.

## Remaining experiments ranked by the claim they would add

| Item | Recommendation for this revision | Added inference and principal limitation |
|---|---|---|
| Existing-data quality and component checks | Do before new compute; new analyses explicitly exploratory | Catches scoring, rule-specific access and capability issues; does not create a new causal experiment. |
| Two-model source-qualified Robin conflict with original-question anchors | Main recommended supplement | Tests whether wrong-record retrieval extends to a conflicting third party and whether explicit source questions change it. No special-self claim from three arms. |
| Llama STATIC feasibility and conditional confirmation | One capped attempt; lower scientific priority than provenance | Tests a selected matched rule-access comparison. Failure ends the branch. |
| Five-arm balanced role-conflict factorial | Substitute for the minimal provenance study only if self-role selectivity is central | Separates conflict manipulations more symmetrically. Requires revised physical-answer identities and validated rehearsal, not a simple extra condition. |
| Llama strict third-person donor | Optional low-scope extension after the main package | Extends a Qwen wording control. Names, lengths and access still change; `balanced2` and strict-third-person templates do not automatically combine. |
| Genuine rotary-position relocation | Prioritize only if the paper claims positional causation | Readout-only original-position/relocated/RF branches can share C48. Moving positions throughout reflection cannot. Joint K/V column permutation is not a position intervention; access loss confounds an attribution reduction. |
| Full reflection-by-readout connection factorial | Conditional on a stronger claim about when influence is acquired | C0, reflection-only RF, readout-only RO and FULL distinguish timing components; original KV studies did not include RO. V1 residual RO cannot substitute for KV RO. |
| Reflection text versus cached-state mediation | Defer unless the paper attributes residue causally to reflection words | Text replay/ablation must separate changed wording from regenerated hidden states. Existing post-treatment mention groups are associational. |
| New task or a deployed cache interface | Valuable later generalization, outside the minimal package | Tests transfer beyond the one artificial assignment task. Renaming rules or examples alone is not broad task generalization. No failure of an untested system can be claimed. |
| Downstream decisions | Defer while NOW remains a reported-rule endpoint | Necessary for claims about changed actions. The previously retired behavioral readout needs fresh suitability validation. |
| More text headers or paraphrased questions | Target only a specified robustness claim | Original-question anchors already address an important source-qualification change. More prompts must not be selected for larger effects. |
| Blinded human coding of existing Qwen reports | Consider if open reports retain a prominent role; no new GPU needed | Improves coding independence, not proof of awareness. A second model's open reports and positive introspection controls remain separate tasks. |
| Expanded capability bank | Add if stronger preserved-capability claims are desired | The current narrow bank and Llama boundary should already be disclosed. Avoid claiming unchanged general ability from extra easy items. |
| More checkpoints or live reciprocal loops | Defer | Broadens scope but does not resolve the present record-provenance question. Keep the old pilot's unmet criterion visible. |

## Workload and reuse

| Proposed work | Receiver readouts, excluding generation/calibration overhead |
|---|---:|
| STATIC coarse selection, 40 episodes, 15 candidates plus C0/KV, four questions, two orderings | 5,440 |
| Up to two STATIC refinements on the same 40 episodes | At most 640 more |
| STATIC independent validation, 80 episodes, four arms, four questions, two orderings | 2,560 |
| Conditional STATIC formal study with ten questions and two orderings | 60N; 36,000 if N=600 |
| Provenance formal study per checkpoint, three arms, twelve questions, two orderings | 72N; 43,200 if N=600 |
| Provenance formal study in both checkpoints at that planning N | 86,400 |

STATIC feasibility therefore has at most 8,640 receiver readouts plus the single
multilayer calibration and technical checks. The prior 60-episode single-layer
calibration took 105.5 seconds; the prior 5,760-readout match took 3,503.0 seconds;
the prior 4,480-readout validity took 3,206.2 seconds, measured from scientific
run creation to completion. These are historical observations, not new rental
quotes or guaranteed forecasts. They suggest a small feasibility phase on the
same class of hardware, not a repetition of the whole seven-arm formal study.

Use an updated measured cost projection and a separate explicit spending cap
before paid execution. The earlier USD60 authorization covered completed v4 and
does not authorize unlimited supplements. Budget or technical interruption is
recorded as incomplete, not converted into scientific failure. Do not restart
the stopped instance to maintain an idle queue of possible experiments.

Share new baselines only when episode identities, material policy, model assets,
prompts, prefix states, question sets and intervention are exactly compatible.
The source study's new questions and possible future balanced materials prevent
blind reuse of STATIC's old-style C0/KV measurements. If a later third-person
extension is jointly planned with STATIC using identical materials and questions,
some C0/KV work can be shared; those shared observations remain paired data, not
independent replications. Historical 600-episode runs stay unchanged.

## Execution readiness

This is a reviewable research plan. Before running, create separately versioned
materials, question IDs, scoring and analysis families; validate tokenizer/native
serialization, donor-only mutations and snapshot identities; implement the exact
finite selector and its stop rules; obtain independent review and pass offline
and relevant GPU acceptance checks; freeze the protocol and assets; and approve
the new compute cap. The old v4 generator and supervisor hard-code layer 21 and
its old stages, so a new grid must not masquerade as an unchanged v4 run.

For the current manuscript, retain the replicated empirical claim regardless of
STATIC's outcome. If the source study broadens errors to Robin, explain a general
record-provenance failure. If source-qualified questions reduce errors, report
that boundary. If access or control quality prevents a decisive test, preserve
the limitation. None of these outcomes requires inventing a special-self,
positional, or consciousness claim.
