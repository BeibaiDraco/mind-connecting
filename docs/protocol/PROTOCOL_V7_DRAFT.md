# Protocol v7 (DRAFT): where an imported memory lies and whose it is taken to be

**Status:** draft for PI approval, October 28, 2026, Claude Code. Not frozen; nothing here authorizes a GPU run. Codex reviews this draft; Claude reviews Codex's engine change. Open items are listed in §12.

**Lineage:**
- PI adoption of plan v2: decision_log, 2026-10-28.
- Plan v2: `research/mind_connecting/address_ownership_20261027/response_to_codex_review.md`.
- Codex's review: `docs/reviews/address_ownership_review_codex_20261027.md`.
- Symmetry check: `research/mind_connecting/address_ownership_20261027/symmetry_check.md`.
- Materials: `src/mb/v7_tasks.py`, contract `v7-placement-v1`.

## 1. Question and competing accounts

When a receiver attends jointly to its own KV cache and a same-model partner's, at the partner's original positions, it names the partner's assigned rule as its own in about half of answers at equal weight and 97% at double weight (Qwen V3). At equal weight, owner identity has no detectable effect: claiming summed over the two orientations of each rule pair is close to 1 in four studies, and a model-specific content preference decides the winner.

**Question:** does changing only where the partner's memory lies in the receiver's attention change which record is taken as "mine", while the receiver can still use the partner's information? The partner's values are left untouched.

| Account | Prediction for translated vs original placement, at fixed weight |
|---|---|
| Placement / region (draft paper, Section 4) | Claiming falls; use is retained; correct separation rises |
| Content-borne role binding (binding literature; our line-order and strict-third-person data) | Claiming about unchanged; use retained |
| Donor suppression by distance (RoPE geometry, learned recency) | Claiming falls **and** use falls |
| Position-as-authority (role-position literature) | Claiming falls; same-content control also disrupted, or Robin answers shift |

The joint pattern of claiming, use and the same-content control discriminates these accounts. Claiming alone does not.

## 2. Scope and immutable history

- **Model:** Qwen3-4B-Instruct-2507, pinned revision `cdbee75f17c01a7cc42f958dc650907174af0554`. A Llama 3.1 8B replication of the decisive contrast is a separate amendment after the Qwen study (PI decision, 2026-10-28).
- **Unchanged:** all v1–v6 protocols, results and the arXiv v1 manuscript (arXiv:2610.33020).
- **Out of scope:** training, model switching, live reciprocal loops, the actor-reference task, "later" placement, moving A's own bank, language variants, prefill steering, interpolated writes.

## 3. Common contracts

- **Unit:** the episode. Arms, rotations, sides and questions are within-episode repeated measures; resampling and uncertainty are at the episode level.
- **Splits:** fresh split names, disjoint from all earlier runs:
  - `v7_dev`: materials checks and engineering smoke;
  - `v7_pilot`: 80 episodes;
  - `v7_formal`: N fixed at the freeze (§11).

  Variants of one split share the legacy assignment structure by construction, so cross-variant comparisons are paired.
- **Records:** append-only shards, identity hashing, one automatic retry per failed trial, no imputation, resume refusal on identity change (AGENTS.md §6). A smoke run is never scientific evidence.
- **Selection:** none from ownership, detection, report or use outcomes:
  - weights are the historical w = 1 and w = 2;
  - the translation offset is set by geometry (§5);
  - the pilot may revise only the use assay (§7), and only on fresh episodes.

## 4. Materials (`src/mb/v7_tasks.py`)

- **Base card:** the v1 second-person card with one added scenario line after the units line.
  - The fact holder's card carries a neutral world fact: "Note: the courier adds a $N surcharge for each package sent on a Thursday.", with N ∈ {6, 7, 8, 9}.
  - The other card carries a token-length-matched filler line.
  - A's and B's prefixes have equal length and differ only inside the declared participant, holder, Robin and note spans (tested).
  - N and a distinct counterfactual N′ are balanced over the 12 ordered pairs.
- **Strict third-person donor card (base only):** the legacy T3b record plus the same note line, with the forced note opener.
- **Generalization variants (prespecified, secondary):**
  - **G1, table card:** the private assignments as a two-row table.
  - **G2, source-qualified question:** `PROV_SELF_RULE` on base cards.
  - **G3, new scenario:** laptops instead of deliveries, four new rule phrases, 30 new single-token code words, its own fact and filler lines. Assignments map one-to-one onto the legacy balanced design.
- **Questions:** four-way forced choice; two rotations per episode; scored by label logits as before.
  - **Base:** START, WORD, NOW, ACC_RULE, PROV_SELF_RULE, USE, DETECT, CAP0, CAP1, and U_OPEN in the arms marked in §6.
  - **G1 and G3:** START, ACC_RULE, USE, CAP0, CAP1.
  - **USE** asks for the total Thursday surcharge for two packages. Options are $12/$14/$16/$18, with meanings "fact" (2N), "cf" (2N′) and "other". It does not ask whose anything is.
  - **DETECT:** "In some runs of this study, another participant's memory is inserted into yours. In this run, was another participant's memory inserted into yours?", on a four-point scale shown forward in one rotation and reversed in the other.
- **Declared spans** (logical positions, end exclusive) for attention diagnostics: `options_table`, `note_line`, `participant_line`, `holder_line`, `holder_rule`, `holder_word`, `robin_line`, `robin_rule`, `robin_word`.

## 5. Interface operation (implemented by Codex, reviewed by Claude)

- **Original placement:** the historical KV-P joint read (`src/mb/runtime.py:68-120`). Partner keys keep their logical RoPE positions.
- **Translated placement:** for each receiving row, take B's complete P bank (card, note, closing tokens, reflection prompt) and set δ_row = −(logical length of that bank).
  - Apply the RoPE rotation R(δ_row) to the fp32 partner keys inside the joint read, using the model's own rotary frequencies and pairing. B's bank then sits immediately before A's first token, and every query-key distance stays positive.
  - Values, masks, cache contents and A's own computation are unchanged. No cache is mutated.
  - δ, the translated span and the operation version enter the condition identity.
- **Same weight rule:** partner logits receive +log w in both placements.
- **Engineering acceptance (Codex's list), before any pilot:**
  - δ = 0 reproduces the historical path exactly;
  - sign and orientation;
  - norm preservation;
  - inverse rotation within a stated tolerance;
  - agreement with a real prefill of B's bank at offset positions;
  - padding and batch invariance;
  - untouched-source and snapshot isolation;
  - mask spans;
  - GQA head alignment;
  - finite values.
- **Span logging:** per layer and head, joint attention mass on declared own spans ((1−β)·p_own) and donor spans (β·p_par) at each readout's answer position. Also the total bank masses, logical positions, δ and span hashes. Only compact summaries are stored. Diagnostics, never selectors.

## 6. Arms (base variant, formal)

All linked arms use KV scope P, recipient A, fact holder B, and FULL readout unless noted.

| # | Arm | Purpose |
|---|---|---|
| 1 | C0 | Baseline; USE guessing rate |
| 2 | C0, fact holder A ("full information") | USE competence ceiling |
| 3 | ORIG w2 | Anchor (historical 97%) |
| 4 | TRANS w2 | **Primary contrast with 3** |
| 5 | ORIG w2, counterfactual N′ | Donor-dependence of use at original placement |
| 6 | TRANS w2, counterfactual N′ | Donor-dependence of use under translation |
| 7 | ORIG w1 | Equal-weight anchor (symmetric baseline) |
| 8 | TRANS w1 | Induced home advantage at equal weight |
| 9 | ORIG w2, readout-only link (RO) | Localization: A's reflection unlinked |
| 10 | TRANS w2, RO | Localization |
| 11 | Same-content donor (B's bank = copy of A's own), ORIG w2 | Disruption control |
| 12 | Same-content donor, TRANS w2 | Disruption control |
| 13 | Strict third-person donor, ORIG w2 | Person × placement |
| 14 | Strict third-person donor, TRANS w2 | Person × placement |

U_OPEN is collected in arms 1, 3, 4, 7, 8 and 11–14.

**Generalization (G1 table, G3 laptop):** arms C0, ORIG w2, TRANS w2, and TRANS w2 counterfactual N′.

**Text reference arm (B's card as quoted text in A's context): deferred** (PI, 2026-10-28). Historical tagged and untagged text arms remain the text comparison; the arm can be added by amendment.

## 7. Stages and gates

1. **Engineering smoke** (12–24 `v7_dev` episodes): §5 acceptance only. No scientific outcome is inspected.
2. **Pilot** (80 `v7_pilot` episodes, all base arms, one rotation pair). Gates read only USE, CAP, format and label mass:
   These gates check that the measuring instrument works. They say nothing about the results.
   - **U1 competence:** USE "fact" choices in arm 2 (A holds the fact itself) are ≥ 90%. If the model miscomputes the total more than one time in ten even when it has the fact, a later loss of use could not be separated from arithmetic failure.
   - **U2 no leakage:** USE "fact" choices in arm 1 (no link) are ≤ 40%. Chance is 25%; well above chance would mean the answer can be guessed without B's information.
   - **U3 donor dependence at original placement:** arm 3 "fact" choices exceed arm 1 by ≥ 25 points, **and** arm 5 "cf" choices exceed arm 1's "cf" rate by ≥ 25 points. The retention fraction R divides by this gain. If the gain were small, R would be too imprecise to tell "use kept" from "use lost" at N = 600.
   - **Q1 quality:** CAP in every linked arm is within 5 points of C0, and label mass is ≥ 0.95. This is the same quality screen used in v2–v5.
   - If U1–U3 fail, the use assay may be revised (wording or the fact's position). The revision is recorded, and a fresh pilot runs on new episodes. START, PROV, DETECT and report outcomes may not be used for any revision; they are not opened before the freeze. If Q1 fails, stop and report to the PI.
3. **Freeze:** tag `protocol-v7` with a FREEZE file (SHA256 of this protocol, materials, configs, code). N is set from the pilot variance (§11).
4. **Formal:** base arms on fresh `v7_formal` episodes, then generalization arms. One run per variant; no interim looks at outcomes.

## 8. Endpoints

**Co-primary (base, FULL, w2):**
- **P1 source separation:** paired difference in START partner-choice rate, TRANS w2 (arm 4) minus ORIG w2 (arm 3). Each episode's rate is averaged over its two rotations. The logit contrast M is reported in the same direction as a companion.
- **P2 donor-dependent use:** tracking rate T = P(choose 2 × the value shown in B's card). It is pooled over the shown-N arm and its counterfactual-N′ arm, for each placement (arms 3+5 vs 4+6). The estimand is T_TRANS − T_ORIG.

**Integrity:** CAP and label mass per arm, against C0. The same-content control (arms 11–12) shows the disruption caused by translation itself.

**Secondary:**
- **S1:** at w1 (arms 7–8), the claiming difference and the orientation-sum home-advantage index (symmetry check method).
- **S2:** RO localization (arms 9–10), the P1 analogue.
- **S3:** person × placement interaction in correct separation (START own **and** ACC_RULE partner), arms 3, 4, 13, 14.
- **S4:** NOW, WORD, the reverse error (ACC_RULE answered with A's own rule), the full four-way confusion matrices.
- **S5:** DETECT, as the P(yes) shift and an ROC against C0 and the same-content controls (false alarms).
- **S6:** the PROV_SELF_RULE answer distribution, including Robin (generalization G2).
- **S7:** open reports, regex plus blinded semantic coding: both code words mentioned, anything unusual reported.

**Generalization (G1, G3):** the P1 and P2 analogues in each variant.

**Diagnostics:** span attention masses. Descriptive only; not used to explain away or select.

## 9. Analysis and interpretation

The PI rejected fixed pass/fail margins (2026-10-28): a cut-off such as "at least 20 points" is arbitrary, and a 19-point effect is not scientifically different from a 20-point one. The analysis is therefore **estimation-first**. Every estimand is reported as a point estimate with a 95% episode-bootstrap interval (10,000 draws, paired within episode). Its size is interpreted against reference effects already measured in this paradigm, which are fixed here in advance. What is prespecified is the estimands, the analysis, the anchors and the wording rules below, not cut-offs chosen after seeing data.

**Reference effects** (Qwen V3, START partner choices, N = 600):

| Anchor | Effect | What it represents |
|---|---|---|
| Cutting the link at readout, w2 (RF vs FULL) | −95.8 points (SE 0.7) | Removing the partner's memory entirely |
| Untagged text instead of the memory link (V2, different content and position) | −81.2 points | A message route rather than a memory route |
| Strict third-person donor record, w1 / w2 | −4.5 / +0.1 points | A wording change we have called "barely helps" |
| Spread of equal-weight estimates across five cohorts | 47.3%–52.3% | Cohort-to-cohort variation |

**How each result is described:**
- **Existence of a placement effect:** the 95% interval for P1 excludes 0.
- **Size of the placement effect:** P1 as a fraction of the cut-link anchor (P1 / −95.8), with its interval. For example, a 19-point reduction is reported as about one fifth of the effect of removing the partner's memory, larger than the third-person wording effect. It counts as a real effect, not a failure.
- **Use retained:** T_TRANS is above the no-link rate T_C0, with the interval of the difference excluding 0. Report the retention fraction R = (T_TRANS − T_C0) / (T_ORIG − T_C0) with its interval. R near 1 means use is fully kept; R near 0 means translation removed B's information.
- **Selective repair:** a placement effect exists, use is retained (R's interval excludes 0), and the same-content control (arms 11–12) shows no START own-rule loss or CAP drop of comparable size. The strength of the repair is described by the pair (fraction of ownership restored, fraction of use kept), both with intervals. No single threshold turns this into a yes/no label.
- **Donor suppression:** a placement effect exists but R's interval includes 0. This is attenuation, not repair (stopping rule 1).
- **No detectable placement effect:** P1's interval includes 0. The result is stated as "translation changes claiming by no more than [interval bound] points". It is compared with the third-person anchor, and is not called equivalence unless the bound is smaller than that anchor.
- **Quality:** CAP and label mass per arm are reported against C0. A linked arm with a CAP loss outside the interval of the same-content control is flagged as disrupted.

**Secondary families** (S1–S7, and G1–G3 for generalization) are reported with intervals, Holm-adjusted within each family when a "different from zero" statement is made.

**Generalization:** in each variant, report the P1 and R analogues with intervals. Describe whether the direction matches the base result and how the sizes compare.

**Rule content:** all claiming analyses also report results stratified by ordered rule pair, because rule identity carries much of the variance at w1.

## 10. Stopping rules (Codex's F1–F6, adopted)

1. Source improvement without donor-dependent use, or with comparable same-content or CAP disruption, is attenuation, not repair.
2. A validated translation whose P1 interval includes 0 and is narrower than the third-person anchor, with use retained, refutes this bounded placement hypothesis. It does not show that ownership lives entirely in content.
3. Results that reduce to content preference, answer position or generic binding interference, with no new predictive consequence, are not promoted.
4. If the use assay cannot be validated (U1–U3 after one revision), no claim about shared useful information is made.
5. Gains only from rewritten tasks, no held-out generalization, or a need for prohibited target-based tuning end the program after the pilot. The negative result goes into the manuscript.
6. Imprecise nulls and failed implementation checks are inconclusive, not evidence for the opposite mechanism.

## 11. Precision and sample size

- **Planning reference:** N = 600 base episodes and N = 300 per generalization variant.
- **At the freeze:** use the pilot's paired SDs of P1 and T to check that N = 600 gives 95% interval half-widths of about 5 points or less for P1 and for T_TRANS − T_ORIG. That is precise enough to tell an effect the size of the third-person anchor apart from a partial repair. In V3 at w2, the paired SD of the cut-link difference was 0.17 (half-width ±1.4 points); at w1 the per-episode SD was 0.47 (±3.8 points). If the pilot implies a half-width above 5 points, the PI decides whether to raise N.

- **Historical throughput** (V3 on an H100, batch 40) was about 4 s per episode-arm, before allowances. On that basis:
  - the base formal set (14 arms × 600) is about 9–10 H100 hours;
  - the generalization set (2 × 4 arms × 300) is about 3 hours;
  - the pilot is about 2 hours.

## 12. Open items before the freeze

1. Codex's review of this draft and of the materials module.
2. Claude's review of the engine change and its acceptance evidence (§5).
3. A runner integration plan for V7 records. Codex owns the runner; the metadata fields come from `v7_tasks.record_metadata`.

Settled by the PI on 2026-10-28: no fixed pass/fail margins (§9); the text reference arm is deferred (§6).
