# V5 scientific implementation review

Date: 2026-10-09. Scope: local preparation before any new GPU execution.

This review covers the proposed protocol's scoring, decision boundaries and
provenance checks. It does not report experimental outcomes, grant a compute
budget, or establish real-model suitability. Historical protocols and results
remain unchanged.

## Review separation

The provenance-analysis author reviewed `src/mb/v5_static.py` and
`scripts/make_v5_static.py` independently of their implementation. The STATIC
author and the materials/runtime author independently reviewed
`src/mb/v5_provenance.py`. Findings below were communicated to the relevant
owner; each owner changed only their claimed files. The launcher/freeze review
and actual native-tokenizer preflight are separate engineering checks.

## Provenance scoring and inference

- Physical candidates a/b/r/d remain the original A/B/Robin/spare values across
  conditions. In the conflicting B card Robin is d; A's card still says r.
  Baseline B recall therefore uses d as the correct answer, without requiring A
  to know an unseen B card.
- The primary score is receiver-original Robin RULE z(d)-z(r), conflict KV minus
  ordinary KV. The separate secondary contrasts are the analogous Robin WORD
  effect and the RULE/WORD interactions comparing original self questions with
  source-qualified self questions, ordinary KV minus C0. Signs and source roles
  agree with the proposed protocol.
- Two orderings are averaged within each episode before paired tests and
  bootstrap resampling. The fixed cross-checkpoint families contain two primary
  and six secondary tests. Unavailable checkpoints retain p=1 solely for Holm
  bookkeeping; effects are not imputed and checkpoints are not pooled.
- Baseline screens each prescribed own-record question separately on both sides.
  Validity accepts only donor-access/CAP questions: donor-own RULE uses ordinary
  KV minus C0 on z(b)-z(d), and donor-Robin RULE specificity uses conflict KV minus
  ordinary KV on z(d)-z(r). Word bounds are diagnostic. Receiver-attribution
  effects cannot enter these progression gates.
- Formal summaries distinguish logit preference movement from actual wrong
  choices. They report per-arm choice counts and episode-bootstrap uncertainty,
  plus paired changes in Robin error rates and replacement-d choices. These
  descriptive differences add no hypothesis tests. The three-arm study does not
  establish self-role selectivity under unequal rehearsal.

Independent review identified three validation gaps, all corrected: unused arm
fields could admit an unplanned donor frame; stored arm hashes were trusted
without rederivation; and label log probabilities were not checked for finiteness.
The scorer now checks complete canonical arms, fixed batching/no calibration,
rederived arm hashes, and finite four-label logits and log probabilities. It also
rederives every question, option ordering, answer meaning, source truth and
private-card hash from the deterministic episode. Missing, duplicated or
unexpected successful trials cannot silently reduce N; completeness is rebuilt
from the raw ledger rather than accepted from a saved status flag.

## Bounded STATIC selection and inference

- The coarse grid is exactly three one-indexed layers 16/21/27 and five gains,
  with unavailable raw-direction layers omitted as whole layers. At most two
  deterministic midpoint evaluations are permitted. Refinements use the original
  40 episodes and exact saved note tokens; they cannot expand the grid or bridge
  across an ineligible intermediate point.
- The selector accepts only access, capability and format summaries. It requires
  positive access increments and the original 25% point-mean match. Tie-breaking,
  bracket ordering, early stop and history replay are deterministic. No formal
  outcome or attribution score selects a setting, and independent failure cannot
  trigger a runner-up.
- Independent N80 validation contains C0, fixed KV, selected STATIC and donor-own
  CF. C0 capability, all intervention quality screens, rule access/content bounds
  and matching are required. The new CF quality screen does not retroactively
  revise the historical v4 gate. Word access is not inferred from rule matching.
- Formal N600 retains all episodes, tests KV minus STATIC on M, and applies a
  separate Holm family to M_NOW/M_WORD. Formal matching drift is reported without
  reselection or exclusions. A 25% point match is not an equivalence test.
- Source runs are reconstructed from pinned raw ledgers. Canonical arm hashes,
  deterministic readout options/meanings and physical CF candidates are checked;
  saved decision JSON must reproduce from the raw evidence. Calibration, search
  history and selected settings must remain consistent through validation/formal
  generation.

The review requested two final safeguards: reject prior-stage source-code hashes
that differ from the current frozen code before spending on a new stage, and
check finite label log probabilities as well as logits. Both were implemented
and independently rechecked. Targeted tests reject a foreign-code calibration
before match generation and reject nonfinite successful log probabilities.
No remaining scientific implementation blocker was identified in this scope.

## Validation and remaining scope

The provenance-focused suite passed 26 tests, including physical truth on the
changed B card, candidate/order invariance, wrong-choice versus logit movement,
fixed multiple-testing families, gate-input exclusions, canonical arm rejection,
and a full N80 synthetic raw-ledger round trip. The shared offline suite passed
357 tests with 5 skipped after all reviewed guards. The combined provenance and
STATIC focused suites passed 49 tests. A separate import check confirmed that
the provenance scorer does not import torch.

Actual GPU smoke/resume behavior, new-question baseline accuracy, access/content
validity, STATIC feasibility and measured compute cost remain untested. Passing
local checks does not substitute for the prospective gates or the separate
approved execution contract and budget. No model, weights or paid instance was
used by this review.
