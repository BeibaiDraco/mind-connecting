# V7 draft and materials review

Reviewer: Codex, 2026-10-28. Reviewed `7e2ab23`, `ef28e34`, `6001816`, the two PI adoption decisions and the estimation-first decision in `decision_log.md`, and Claude's engine review. This is a review, not a protocol amendment or permission to run a model.

**Verdict:** the material generator is suitable for runner integration. The draft needs the following clarifications before freezing or treating the proposed analysis as confirmatory. GPU work still requires PI approval. The baseline offline suite passes: 1327 passed, 11 skipped, 1 GPU test deselected.

## Required before freeze

1. **The generalization arm table cannot identify its stated P2 analogue.** Section 6 specifies C0, ORIG w2, TRANS w2 and TRANS w2 counterfactual. Sections 8–9 require the same pooled original/counterfactual tracking contrast as the base study, but ORIG w2 counterfactual is absent. Recommend adding that fifth arm, subject to PI approval; alternatively explicitly define a different secondary estimand. The runner will represent the four currently declared arms without inventing the missing cell. Do not let analysis silently compare two different pooling schemes.

2. **The order of freezing and variance estimation is contradictory.** Section 7 seals START until the freeze, while section 11 needs its pilot paired SD to choose N at that freeze. AGENTS permits a separate variance step only after parameter selection is frozen. Specify a material/parameter seal, then an isolated variance-only calculation (no effect means or target-driven changes), then the final N/protocol seal. Also replace section 3's unconditional ban on selection using USE with the explicit, bounded instrument-validation exception already authorized by the PI.

3. **The interpretation rules currently confuse absence of evidence with suppression.** In section 9, an R interval that includes zero is called donor suppression even if it also includes one; that contradicts stopping rule 6. Report such cases as inconclusive. Require the repair direction (negative P1), since an interval excluding zero also permits increased claiming. Define the pooled C0 comparison explicitly: score the same C0 answers against both the N and N-prime targets with the same weights as T. Prespecify handling of bootstrap samples with zero/near-zero original-use gain; a pilot gate does not guarantee every bootstrap denominator stays positive. Report the unnormalized use contrast alongside any ratio.

4. **Historical anchors do not yet define equivalence.** Sections 9–10 refer to an interval narrower than "the third-person anchor", but the table contains both -4.5 and +0.1 points at different weights. Choosing either implicitly sets a margin, despite the PI's rejection of arbitrary pass/fail margins. Recommend reporting interval bounds relative to the named anchors without an equivalence/refutation label unless the PI explicitly adopts a bounded hypothesis. "Comparable" disruption also needs either descriptive wording or a prespecified contrast, not a post-outcome cutoff. The added neutral-fact line means the new ORIG arm is a replication anchor, not guaranteed to reproduce the old 97%.

5. **Analysis bookkeeping needs a final explicit specification.** Enumerate the hypotheses within each Holm family and the test used to produce p-values. Resolve stopping rule 5's "after the pilot" reference to held-out generalization, which section 7 schedules after the formal base run. Neither issue requires changing the material generator.

## Material and adapter findings

- The variant generator preserves episode IDs, assignment structure, fact pairs and rotation pairs across variants in a split. Laptop rules/scenarios and words are replaced together. Fact and counterfactual meanings remain fixed across treatments, which is necessary for the donor-dependence contrast. The tests exercise balance, token boundaries, offset spans and the forward/reverse DETECT order.
- `first_token` and `system_turn` are now declared by the materials. The runner must append actual generated `note`, `closure` and `prompt` spans in logical half-open coordinates. Include the forced third-person note opener in `note`; it is already part of the private-prefix input and must not be duplicated.
- `record_metadata` currently hashes second-person cards only (it has no frame argument). The adapter must hash the actual strict-third-person B card. For same-content donors, the adapter must record the actual copied A card/prefix and effective absence of the B-only fact; the generic helper's default B-holder metadata would otherwise be false. These are adapter responsibilities and will be covered by runner tests; Claude's material file is left untouched.
- The same-content arm must copy A's complete P bank, including the generated note and reflection prompt, with identical spans. It is a disruption control; it does not contain the intended B-only neutral fact. Keep assignment-based question meanings fixed and record the actual donor content separately.
- Section 5's "A's own computation is unchanged" should be limited to the intervention: A's keys/values and its native attention computation at a given query are untouched. Its later hidden states and generated trajectory can change as a consequence of the joint read. No cache mutation is required.

## Runner and acceptance handoff

Implement R4 using the declared 14 base arms and four arms per material variant, with separate variant/holder/counterfactual/frame note identities, actual token/card provenance, registered question sets and per-arm U_OPEN coverage. Persist raw outputs only; protocol interpretation, pilot gates and analysis remain Claude's responsibility. There is no automatic scientific post-processing or stage progression.

R1 can be measured in the approved engineering smoke before optimizing the reviewed engine. R2 requires a prospectively specified comparison to the unmodified BF16 path's batch-composition variability on the same smoke episodes; the fp32 unit-test tolerances are not BF16 acceptance margins. No smoke, model, historical-outcome search or experiment was run for this review.
