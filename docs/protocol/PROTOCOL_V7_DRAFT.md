# Protocol v7 (DRAFT): where an imported memory lies and whose it is taken to be

**Status:** draft for PI approval, October 28, 2026, Claude Code; revised after Codex's draft review (ad64c92) and again after the failed BF16 acceptance check (§7 step 1). Not frozen. PI approval of this draft authorizes only the engineering smoke and the pilot (§7 steps 1–2); the formal runs require the final freeze. Open items are listed in §12.

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
- **Selection:** nothing is selected from ownership (START, WORD, NOW, ACC_RULE, PROV), detection or report outcomes:
  - weights are the historical w = 1 and w = 2;
  - the translation offset is set by geometry (§5).
  - **The one bounded exception is instrument validation (PI-authorized).** The pilot gates read USE, CAP, format and label mass (§7). Only USE failures may trigger a revision, of the use assay alone, on a fresh pilot episode namespace declared by amendment.

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
  - B's values, all masks and all cache contents are unchanged, and so is A's native attention computation at a given query; no cache is mutated. A's later hidden states and generated text can change, as a consequence of the changed read.
  - δ, the translated span and the operation version enter the condition identity.
- **Same weight rule:** partner logits receive +log w in both placements.
- **Engineering acceptance (Codex's list), before any pilot:**
  - δ = 0 reproduces the historical path exactly;
  - sign and orientation;
  - norm preservation;
  - inverse rotation within a stated tolerance;
  - agreement with a real prefill of B's bank at offset positions, through the production joint read (§7 step 1);
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
| 3 | ORIG w2 | Replication anchor. The added note line means it need not reproduce the historical 97% exactly. |
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

**Generalization (G1 table, G3 laptop):** five arms: C0, ORIG w2, TRANS w2, ORIG w2 counterfactual N′, TRANS w2 counterfactual N′. The ORIG counterfactual cell was added after Codex's review (ad64c92), so the pooled use contrast is defined exactly as in the base study.

**Text reference arm (B's card as quoted text in A's context): deferred** (PI, 2026-10-28). Historical tagged and untagged text arms remain the text comparison; the arm can be added by amendment.

## 7. Stages and gates

1. **Engineering smoke** (12–24 `v7_dev` episodes). No scientific outcome is inspected.
   - Run the §5 acceptance on the pinned checkpoint (`tests/test_v7_kv_gpu.py`).
   - Record per-step timing (engine review R1).
   - **Relocation gate (FP32).** On the 12 saved `v7_dev` inputs, compare two conditions over eight teacher-forced ticks: the production translated arm (KV-P, w2, all layers) with B prefilled natively, and the native arm (δ = 0) with B's bank prefilled at positions [−L_B, 0) and the same span declarations. A's state is identical. The receiver rows' logits and own/donor span masses must agree within the FP32 tolerances already in `tests/test_v7_kv_gpu.py` (logits 3 × 10⁻³ absolute, 2 × 10⁻³ relative; masses 2 × 10⁻³ absolute). A correct implementation passes with certainty.
   - **BF16 comparison (descriptive).** The same two conditions in BF16, reported beside the unmodified path's padding variability. Not a gate: in BF16 neither side is ground truth.
   - The first BF16 check (read-time rotation versus a BF16 offset prefill, against the maximum batch-composition error) failed and is kept in the record. It did not run the production path, and it compared two different rounding sources by their maxima, which fails a correct engine by chance (`docs/reviews/v7_bf16_acceptance_review_claude_20261028.md`).
2. **Pilot** (80 `v7_pilot` base episodes, all 14 base arms, the episodes' two rotations).
   - The gates read only USE, CAP, format and label mass. They check that the measuring instrument works and say nothing about the results:
     - **U1 competence:** USE "fact" choices in arm 2 (A holds the fact itself) are ≥ 90%. If the model miscomputes the total more than one time in ten even when it has the fact, a later loss of use could not be separated from arithmetic failure.
     - **U2 no leakage:** USE "fact" choices in arm 1 (no link) are ≤ 40%. Chance is 25%; well above chance would mean the answer can be guessed without B's information.
     - **U3 donor dependence at original placement:** arm 3 "fact" choices exceed arm 1 by ≥ 25 points, **and** arm 5 "cf" choices exceed arm 1's "cf" rate by ≥ 25 points. Use retention is measured relative to this gain; if the gain were small, "use kept" and "use lost" could not be told apart at N = 600.
     - **Q1 quality:** CAP in every linked arm is within 5 points of C0, and label mass is ≥ 0.95. This is the same quality screen used in v2–v5.
   - If U1–U3 fail, the use assay may be revised (wording or the fact's position) once. The revision is recorded and a fresh pilot runs on a new episode namespace declared by amendment. If Q1 fails, stop and report to the PI.
   - The analysis code reads ownership, detection and report outcomes from pilot records only in step 4, and only as variances.
3. **Parameter seal** (tag `protocol-v7-params`, with a FREEZE file of SHA256 hashes). Fixes this protocol, materials, arm registry, weights, geometry, question sets, runner and analysis code. Nothing after this point may change them.
4. **Variance-only step.** A separately reviewed script reads the pilot records and outputs only the paired standard deviations needed in §11 (P1, D_use) and the implied N. It prints no means, differences or intervals. Its output is committed before step 5.
5. **Final freeze** (tag `protocol-v7`): records N and the variance output.
6. **Formal base run** on fresh `v7_formal` episodes, then the generalization runs (G1, G3) on the same split. One run per variant; no interim looks at outcomes.

## 8. Endpoints

**Co-primary (base, FULL, w2):**
- **P1 source separation:** paired difference in START partner-choice rate, TRANS w2 (arm 4) minus ORIG w2 (arm 3). Each episode's rate is averaged over its two rotations. The logit contrast M is reported in the same direction as a companion.
- **P2 donor-dependent use:** tracking rate T = P(choose 2 × the value shown in B's card), pooled with equal weight over the shown-N arm and its counterfactual-N′ arm for each placement (ORIG: arms 3 and 5; TRANS: arms 4 and 6).
  - For the no-link baseline, the same C0 answers (arm 1) are scored against both targets with the same weights: T_C0 = ½·P(choose 2N) + ½·P(choose 2N′).
  - The estimands are the **use difference** D_use = T_TRANS − T_ORIG and the **use gain under translation** G_TRANS = T_TRANS − T_C0. Both are unnormalized.
  - The retention fraction R = G_TRANS / (T_ORIG − T_C0) is reported as a descriptive companion only.

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
- **Placement effect in the repair direction:** P1 < 0, with the 95% interval below 0. An interval above 0 (claiming increased) is reported as an effect in the opposite direction.
- **Size of the placement effect:** P1 as a fraction of the cut-link anchor (P1 / −95.8), with its interval. For example, a 19-point reduction is reported as about one fifth of the effect of removing the partner's memory, larger than the third-person wording effect. It counts as a real effect, not a failure.
- **Use:**
  - **Use retained:** G_TRANS's interval lies above 0. Report D_use with its interval alongside, and R as descriptive.
  - **Use lost:** G_TRANS's interval includes 0 **and** D_use's interval lies below 0.
  - **Use inconclusive:** otherwise. This includes intervals that include both 0 and the full original gain. It is never read as suppression (stopping rule 6).
  - **R's interval:** if more than 2.5% of bootstrap draws have an original gain (T_ORIG − T_C0) of zero or less, R's 95% interval is reported as undefined, because a two-sided 95% interval cannot be formed. Only the unnormalized contrasts are then interpreted.
- **Selective repair:** a placement effect in the repair direction and use retained, with the same-content contrast (below) reported alongside. Its strength is described by P1's fraction of the cut-link anchor and by R, both with intervals. No single threshold turns this into a yes/no label.
- **Donor suppression:** a placement effect in the repair direction with use lost. This is attenuation, not repair (stopping rule 1).
- **No detectable placement effect:** P1's interval includes 0. The result is stated only as "translation changed claiming by between [lower] and [upper] points", next to the anchors in the table. No equivalence or refutation label is used unless the PI adopts a bounded hypothesis before the freeze.
- **Disruption by translation itself:** a prespecified contrast in the same-content control. Same-content TRANS minus same-content ORIG (arms 12 − 11), for START own-rule choices and for CAP, with intervals, reported next to P1 and D_use. It is described, not thresholded.
- **Quality:** CAP and label mass per arm, reported against C0.

**Tests and families.** P-values come from two-sided paired t-tests on episode-level differences; intervals come from the episode bootstrap. The co-primary statements are each reported on their own. "Selective repair" requires both, so no adjustment is needed across them (intersection-union). Holm adjustment applies within each family below; every contrast is TRANS minus ORIG at w2, FULL, unless noted.
- **S1 (w1):** claiming difference (arms 8 − 7); home-advantage index difference.
- **S2:** claiming difference under RO (arms 10 − 9).
- **S3:** person × placement interaction in correct separation, (14 − 13) − (4 − 3).
- **S4:** NOW difference; WORD difference; reverse-error difference.
- **S5:** DETECT P(yes) difference (4 − 3); DETECT P(yes), ORIG w2 minus C0 (3 − 1); same-content false-alarm rate, ORIG minus C0 (11 − 1).
- **S6 (G2):** PROV_SELF_RULE donor-own choice difference; Robin choice difference.
- **S7:** open reports mentioning both code words; open reports mentioning anything unusual.
- **Generalization family:** P1 and D_use in G1; P1 and D_use in G3.

**Generalization:** in each variant, report P1, D_use, G_TRANS and R with intervals. Describe whether the direction matches the base result and how the sizes compare.

**Rule content:** all claiming analyses also report results stratified by ordered rule pair, because rule identity carries much of the variance at w1.

## 10. Stopping rules (Codex's F1–F6, adopted)

1. Source improvement without donor-dependent use, or with comparable same-content or CAP disruption, is attenuation, not repair.
2. If a validated translation leaves P1's interval around 0 with use retained, report the interval bounds next to the anchors. Claim no refutation or equivalence unless the PI adopted a bounded hypothesis before the freeze. Never claim that ownership lives entirely in content.
3. Results that reduce to content preference, answer position or generic binding interference, with no new predictive consequence, are not promoted.
4. If the use assay cannot be validated (U1–U3 after one revision), no claim about shared useful information is made.
5. If the base result appears only with rewritten tasks, fails to generalize in the formal G1/G3 runs, or would need prohibited target-based tuning, the program ends after the generalization runs. The negative result goes into the manuscript.
6. Imprecise nulls and failed implementation checks are inconclusive, not evidence for the opposite mechanism.

## 11. Precision and sample size

- **Planning reference:** N = 600 base episodes and N = 300 per generalization variant.
- **At the final freeze:** take the variance-only output (§7 step 4). Check that N = 600 base episodes gives 95% interval half-widths of about 5 points or less for P1 and for D_use. That is precise enough to tell an effect the size of the third-person anchor apart from a partial repair. In V3 at w2, the paired SD of the cut-link difference was 0.17 (half-width ±1.4 points); at w1 the per-episode SD was 0.47 (±3.8 points). If the implied half-width exceeds 5 points, the PI decides whether to raise N. Generalization variants use N = 300 unless the PI decides otherwise.

- **Historical throughput** (V3 on an H100, batch 40) was about 4 s per episode-arm, before allowances. On that basis:
  - the base formal set (14 arms × 600) is about 9–10 H100 hours;
  - the generalization set (2 × 5 arms × 300) is about 3–4 hours;
  - the pilot is about 2 hours.

## 12. Status of open items

Resolved:
- Codex reviewed this draft and the materials (ad64c92). Its five required clarifications are incorporated: the generalization ORIG counterfactual arm, the seal → variance → freeze order, the inconclusive-use wording with repair direction and pooled C0, no equivalence labels, and enumerated families and tests.
- Claude reviewed the engine (`docs/reviews/v7_engine_review_claude_20261028.md`) and the runner (`docs/reviews/v7_runner_review_claude_20261028.md`).
- Codex added the generalization ORIG counterfactual arm to the runner registry (9cb073a).
- The first BF16 acceptance check failed. Claude's review found no engine defect and replaced the rule with the FP32 relocation gate in §7 step 1 (`docs/reviews/v7_bf16_acceptance_review_claude_20261028.md`).
- The PI settled on 2026-10-28: no fixed pass/fail margins (§9), and the text reference arm deferred (§6).

Before the parameter seal:
- Claude writes and Codex reviews the pilot-gate script and the variance-only script.
- The relocation gate and the rest of §7 step 1 pass and are reviewed.
