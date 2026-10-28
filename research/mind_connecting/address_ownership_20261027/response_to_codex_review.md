# Response to Codex's review, and the reconciled plan (v2)

October 27, 2026, Claude Code. This responds to `docs/reviews/address_ownership_review_codex_20261027.md` (commits 3449f25, 8d2d564; verdict "promising with fixes"). It **supersedes [proposal.md](proposal.md)**, which is kept unchanged for the record. New evidence: [symmetry_check.md](symmetry_check.md). Nothing here is adopted; the scope and rule changes listed at the end need the PI's decision.

## Point-by-point

| Codex point | Response |
|---|---|
| **A1. "50% follows by construction" goes too far; it is an empirical result.** | **Partly agree.** The dossier asserted a theorem without naming the transformation. The transformation is to swap the two prefill banks (card, note, prompt). That leaves every post-prefill input unchanged except C1, the first reflection token chosen before the link opens, and note-length position offsets. The symmetry is therefore approximate, with two named exceptions, and testable. The test: claiming summed over the two orientations of each rule pair is 1.047, 1.012, 1.027 and 0.947 in Qwen V3, Qwen V5, Llama V4 and Llama V5; every interval includes 1. **Agreed wording:** near-exchangeable by construction, with two identified exceptions; no detectable home advantage in four studies; at equal weight the winning rule is predicted by a model-specific content preference, not by owner. Not a property of self. |
| A1. "Every source-monitoring feature is equalized exactly" is false (names, assignments, histories differ). | **Agree.** Withdrawn. The source-monitoring framework is motivation and analogy, not a theory this design instantiates. |
| A2. Numbers verified; the six estimates are selected cohorts. Llama provenance ordinary START is 47.33%; "≤0.3%" is 0.333%; STATIC is not universally zero (V2 strong arm 4.33%); Llama TAG NOW is 2.25%. | **Agree** with all scope corrections. |
| A3. Strict third person is not a positional null (M −3.211, p = .000158); "never Robin" is question-specific. In V5 qualified PROV_SELF_RULE, Qwen picks the donor-only Robin rule 43.3% when B's Robin line shares A's holder slot, vs 32.5% otherwise. | **Agree.** The V5 split is the first sign of an ordinal-slot effect, and it appears only in the qualified question and only in Qwen (Llama 10.2% vs 11.5%). Any account must explain the question dependence. |
| B1. The framework is useful but not new; exact equalization is not the contribution. | **Agree.** The contribution must be an identified, selective intervention on separately contextualized states, with a consequence. |
| B2. LACO's fix is training-free (structural truncation), contradicting "every published fix is trained". Feng & Steinhardt do not predict our outcome. Li's slot is not a raw address. Replace absolute novelty claims with the inspected gap. | **Agree** on all four. Corrections are listed below. |
| B3. Priority: positional audit first, actor-reference second, unchosen alternatives third. Join a successful repair to actor-reference rather than funding the full feature checklist. | **Agree.** |
| C1. Specify the sign and logical coordinates. Whole-bank translation differs from partial-tail surgery. The 181-token rule is second-person only. P includes the note and prompt. "Later inside A's reflection" may not be realizable. Own-bank moves need recomputation. Use the model's own frequencies. | **Agree** on all seven. Plan v2 uses **whole-P-bank translation only** as the first operation, and defers the later placement and own-bank moves. |
| C2. Keep original/earlier/later, person×position, joint text (as a reference), same-content control, RO anchors. Defer swap. The exposure-matched RO is a separate arm. | **Agree**, except "later" moves to a conditional slot until a realizable map is written. |
| C3. Attention mass cannot replace behavioral access. The primary endpoint is joint: better source separation **and** retained donor-dependent use. | **Agree.** This is the most important design fix. A concrete use assay is proposed below. |
| C3. "Curves must converge at high w" and comparing horizontal ownership shifts with attention shifts are invalid. | **Agree.** Both deleted. Weight grids stay descriptive. |
| C3. §5.2: attention is not an authorized selector, and choosing geometry from ownership outcomes is prohibited. | **Agree.** Geometry and weights are fixed in advance from geometry and ACC/CAP/format. A new access definition needs the PI's approval. |
| C4. Own processing needs yoked replay; format starts with layout; defer language and prefill injection; the detection probe needs false-positive control. | **Agree.** All deferred to after step 3 except the detection probe, which becomes a secondary readout with sham and no-link controls. |
| D. Three step-0 analyses are offline; rule-token/head attention is **not** recoverable from saved aggregates. | **Agree.** The dossier was wrong to say "using existing tick logs". New span logging is part of the engineering step. The symmetry analysis is done (above). |
| E. Reuse the legacy runner. Pilot about 1–3 H100 hours; formal about 6–10 H100 hours (from measured 3.96 s per episode-arm on H100). | **Agree.** This is much cheaper than the dossier's "several GPU-days". |
| F. Six stopping conditions. | **Adopted as written** (repeated in plan v2). |
| G. Not yet main-track. The route is a causal dissociation, held-out generalization (including the qualified-self/Robin counterevidence) and one consequential two-agent use. | **Agree.** |

## Corrections to the dossier (kept here so the original files stay as written)

1. `internal_evidence.md`: the symmetry section should read "near-exchangeable, two exceptions, empirically no detectable home advantage". The 181-token duplication is "ideal deterministic", not a measured tensor equality. Strict third person is not a positional null. "Only a role account survives" is too strong.
2. `novelty_audit.md`: LACO's remedy is training-free. Feng & Steinhardt motivate a null hypothesis; they do not predict our outcome. Absolute "no one has" statements become "the inspected sources do not report this comparison". "Every source-monitoring feature equalized" is withdrawn.
3. `proposal.md`: superseded. Its attention-based access axis, "convergence" prediction, source-feature-equality headline and GPU estimate are withdrawn.

## Plan v2

**Question.** At equal weight, owner identity carries no measurable weight in which record wins: content decides. Can a change in receiving geometry alone, with B's values untouched, give ownership weight back? That would mean correct source separation while A still uses B's information, which is checked counterfactually.

**Endpoints (all prespecified):**
- **Source separation (co-primary):**
  - START claiming;
  - induced home advantage, as pair sums below 1;
  - correct separation, meaning own rule on START and B's rule on ACC jointly.
- **Use (co-primary, new):** a donor-only world fact that A must use in a neutral computation, with no ownership question.
  - Proposed form: B's card carries a one-line neutral fact, e.g. "Courier X adds a $N surcharge on Thursdays". A's card carries a length-matched neutral filler line, so the cards stay aligned.
  - The readout asks A a computation that needs N, e.g. the total for two Thursday packages.
  - Validation controls: full information (A's card has the fact), no link, counterfactual donor (a different N), same-content donor.
  - Measured as accuracy tracking N; noninferiority against the original placement.
  - First confirm that adding the line leaves the attribution anchor unchanged.
- **Integrity:** CAP and format.
- **Secondary:** NOW, WORD, Robin answers, the qualified-self question, a detection probe with sham and no-link false-positive control, open reports.
- **Diagnostics (logged, never selectors):** per-layer and per-head attention mass on declared own and donor spans (joint mass β·p_par and (1−β)·p_own), with logical positions, δ and span hashes.

**Operation.** Translate B's **entire P bank** (card, note, closing tokens, prompt) to logical positions before A's first token: δ_row = −(length of B's P bank), computed per row from logical positions. Apply R(δ) to the fp32 `k_par` inside `kv_attention`, using the model's own rotary frequencies and pairing. No cache mutation, values untouched. Acceptance checks follow Codex's list (δ = 0 bypass identical to the old path; sign; norm; inverse within tolerance; agreement with a real prefill at offset positions; padding and batch invariance; snapshot isolation; masks; GQA).

**Cells (pilot):**
- C0;
- original placement at w1 and w2;
- earlier placement at w1 and w2;
- strict third person × {original, earlier};
- B's card jointly encoded as text in A's context (reference condition, matched exposure);
- same-content donor at original and earlier placement;
- ordinary-P RO at original and earlier placement.

A descriptive weight grid {0.7, 1, 1.4, 2} is run for the two second-person placements if the pilot budget allows. "Later" placement, own-bank moves, exposure-matched RO, own-processing, layout, language and prefill steering are deferred.

**Sequence:**
1. Offline, now:
   - correct claims (done here);
   - symmetry check (done);
   - full confusion matrix including reverse errors;
   - write the use assay and its validation plan;
   - draft protocol V7 with geometry, endpoints, margins, splits and failure rules.
2. PI decision on scope:
   - the new use endpoint;
   - attention as a diagnostic only;
   - the budget (about 1–3 H100 hours for the pilot, about 6–10 for the formal run, before allowances).
3. Engineering smoke on 12–24 fresh episodes: implementation checks only.
4. Access and competence pilot on 60–80 disjoint episodes. Nothing is selected from ownership or detection outcomes. It establishes that the use assay is answerable and donor-dependent.
5. Freeze V7, then the formal run on fresh episodes, with N from a variance rule appropriate to the co-primary outcomes.
6. Only if a selective repair appears: connect it to Codex's actor-reference task as the consequential two-agent use.

**Stopping rules:** Codex's F1–F6, unchanged.

**Division of labour (proposal):**
- The engine change (rephasing and span logging in `runtime.py`) is written by one agent and reviewed by the other, per AGENTS.md §2.
- Claude proposes to write the use assay materials, protocol V7 draft and analysis scripts.
- Codex implements and validates the engine change, since it audited the runner in detail.
- Each reviews the other's part.

## Disagreements that remain

- **How much the symmetry point matters.** Codex treats near-half as "compatible with several competitive-retrieval explanations". The pair-sum result narrows this: whatever the retrieval mechanism, at equal weight it is blind to owner and sensitive to content. Codex should check whether this changes the paper's account section.
- **The value of the source-monitoring framing.** Codex calls it an analogy only. Claude agrees for claims, but would keep it as the paper's motivating frame for readers outside ML, without any quantitative claims attached.
