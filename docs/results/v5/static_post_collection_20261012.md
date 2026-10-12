# Fixed Llama STATIC continuation: post-collection analysis

Date: 2026-10-12. This report analyzes the completed, prospectively amended
STATIC comparison. It does not change the manuscript, original gates, selected
parameters, raw data or historical reports. Exact statistics, all choice counts,
episode-based intervals and input hashes are in
[the companion JSON](static_post_collection_20261012.json).

## Result and interpretation

The fixed KV interface produced substantially more donor attribution than the
selected STATIC intervention: the primary KV−STATIC contrast on Robin-subtracted
assigned-rule M is **+10.1916 nats, 95% CI [9.7500, 10.6501]**, across 600 paired
episodes. Donor-rule choices on the receiver's original-assignment question were
49.917% under KV and 0.583% under STATIC. STATIC nevertheless answered the
explicit donor-rule question correctly more often: 47.333% versus 42.083%.
This is a clear descriptive dissociation between measured content access and
attribution under the two tested interfaces.

The intended **25% mean-logit-gain match did not hold in the formal sample**:
STATIC's rule-access gain is 40.125% below KV's. The new experiment therefore
supports the condition difference and the access/attribution dissociation, but
still does not establish a Llama route effect at the prespecified matched gain.
Neither correct-choice rates nor a newly relaxed tolerance can replace the
frozen matching criterion. STATIC also has small assigned-rule effects and
nonzero current-rule adoption; an absolute claim that residual steering cannot
produce attribution changes would be contradicted by these data.

## Dataset, analysis contract and verification

- Run: `20261011-185223_v5_llama_static_confirm_v5_continuation_static`.
- Llama 3.1 8B Instruct, revision `0e9e39f249a16976918f6564b8830bc894c89659`;
  frozen collection commit `69b4627d391330c16203897ba66a205f526bfdf1`, source hash
  `b0d01114a0c1d07c`.
- Fixed C0, KV-P w1 and STATIC layer16/raw/gain0.5; 600 fresh episodes,
  recipient A, ten questions, two balanced answer orderings: 36,000 records.
- All records are complete, unique and finite. The prior independent integrity
  audits verified frozen identity, native questions, original calibration and
  snapshot references. This analysis repeats the continuation contract and raw
  ledger checks. Hashes of raw inputs and saved outputs are unchanged afterward.
- The statistical unit is the episode. Average its two orderings before paired
  contrasts; use two-sided paired t-tests and 10,000 episode-bootstrap draws,
  seed 0, for percentile 95% intervals. The primary family has one test; the
  separate secondary family has two tests with Holm adjustment. No episodes
  were dropped or imputed, and no parameter or sample size was reselected.

The entire recomputed frozen summary agrees with the saved summary at relative
tolerance 1e-12 (no absolute tolerance for p-values). All estimates, SDs, SEs,
bootstrap bounds, descriptive values and flags are bit-identical. Only six
p-value leaves differ in their last floating-point bits: maximum relative
2.166e-16 and maximum absolute 2.444e-150. This is consistent with last-bit
numerical-library rounding, not a changed bootstrap or sample. An independent
raw dictionary/label-index implementation, without the project scoring or
inference functions, reproduces all three paired estimates, SDs, SEs and bootstrap
bounds; a separate SciPy t-test agrees to the stated tolerance.

## Prespecified tests

M subtracts the Robin-control question's partner-versus-Robin logit margin from
the self question's partner-versus-own margin. M_NOW and M_WORD use their
corresponding question pairs. Positive NOW movement concerns a reported current
rule; it is not itself a false claim about the original assignment or a measured
change in downstream behavior.

| Family / metric | KV−STATIC mean | Paired SD | SE | 95% bootstrap CI | t (599 df) | Raw p | Holm p |
|---|---:|---:|---:|---|---:|---:|---:|
| Primary M | 10.1916 | 5.6607 | 0.2311 | [9.7500, 10.6501] | 44.101 | 2.910e-190 | 2.910e-190 |
| Secondary M_NOW | 8.3189 | 5.5018 | 0.2246 | [7.8759, 8.7598] | 37.037 | 4.899e-157 | 9.797e-157 |
| Secondary M_WORD | 7.9207 | 5.9573 | 0.2432 | [7.4488, 8.3805] | 32.568 | 1.128e-134 | 1.128e-134 |

These three positive contrasts are distinct from successful matching or
capability equivalence. WORD was not the matching target: STATIC is
rule-conditional and does not reproduce KV's word-access gain.

## Actual choices and raw components

Each cell below is a donor/partner argmax count out of 1,200 question presentations
(600 episodes × two orderings). Intervals resample 600 episode means, not 1,200
independent trials; they are descriptive and pointwise. A zero-width bootstrap
interval at zero describes the observed boundary, not a population guarantee.

| Arm | Assigned rule START | Current rule NOW | Code word WORD | Donor-rule access | Donor-word access |
|---|---|---|---|---|---|
| C0 | 0; 0.000% [0, 0] | 1; 0.083% [0, 0.250] | 1; 0.083% [0, 0.250] | 202; 16.833% [14.500, 19.250] | 54; 4.500% [3.417, 5.667] |
| KV w1 | 599; 49.917% [46.833, 53.083] | 598; 49.833% [46.750, 52.917] | 593; 49.417% [46.250, 52.583] | 505; 42.083% [38.833, 45.417] | 527; 43.917% [40.583, 47.250] |
| STATIC L16 g0.5 | 7; 0.583% [0.167, 1.083] | 105; 8.750% [7.165, 10.500] | 0; 0.000% [0, 0] | 568; 47.333% [44.000, 50.667] | 73; 6.083% [4.750, 7.500] |

The paired assigned-rule choice difference is +49.333 percentage points
[46.250, 52.500]. Conversely, STATIC's donor-rule accuracy exceeds KV's by
5.250 points [1.083, 9.333]. The latter is a descriptive paired interval, not an
additional prespecified hypothesis or evidence that all information was matched.

Full choice counts clarify what the errors mean. Columns denote the physical
receiver assignment, donor assignment, Robin assignment and unused/distractor.
For START, own is correct; for ACC_RULE, partner is correct.

| Question / arm | Own | Partner | Robin | Unused |
|---|---:|---:|---:|---:|
| START / C0 | 1200 | 0 | 0 | 0 |
| START / KV | 601 | 599 | 0 | 0 |
| START / STATIC | 1193 | 7 | 0 | 0 |
| ACC_RULE / C0 | 44 | 202 | 785 | 169 |
| ACC_RULE / KV | 480 | 505 | 190 | 25 |
| ACC_RULE / STATIC | 93 | 568 | 491 | 48 |

All other question/category distributions are retained in the JSON. On START_R,
C0 and KV choose Robin in 1,200/1,200 presentations; STATIC chooses Robin in
1,195 and own in five. No arm chooses the donor there. High Robin accuracy can
coexist with shifts in its continuous logit margin.

| Arm | START partner−own | START_R partner−Robin | M | M−C0 (descriptive 95% CI) |
|---|---:|---:|---:|---|
| C0 | -12.0649 | -11.8955 | -0.1695 | 0 |
| KV | 0.0379 | -10.6154 | 10.6533 | 10.8228 [10.3845, 11.2614] |
| STATIC | -9.1619 | -9.6237 | 0.4618 | 0.6312 [0.4859, 0.7777] |

Thus KV−STATIC M decomposes into **+9.1998 self-margin movement minus −0.9917
Robin-margin movement**, totaling +10.1916. The result is predominantly the
self-question component, with the control subtraction making a material
contribution. STATIC's M−C0 is small but positive; its M_NOW−C0 is +0.2278
[-0.0066, 0.4632] and M_WORD−C0 is −0.8406 [-1.0371, −0.6365]. Its 8.75%
current-rule donor choices therefore should not be conflated with a clear
positive Robin-adjusted current-rule contrast.

## Access matching and capability

The prespecified gain is the paired mean change from C0 in
`ACC_RULE = z(partner rule) − z(unused rule)`. Both gains must be positive and
`abs(G_STATIC−G_KV)/G_KV <= 0.25`. This does not equate accuracy, word access,
information content, tensor strength or every episode, and it is not an
equivalence test.

| Stage | N | KV gain | STATIC gain | Relative gap | 25% point-match |
|---|---:|---:|---:|---:|---|
| Coarse selection | 40 | 2.065526 | 1.564488 | 24.257% | Pass |
| Independent original validity | 80 | 2.040514 | 1.562524 | 23.425% | Pass |
| New formal continuation | 600 | 2.564291 | 1.535371 | 40.125% | **Fail** |

STATIC's gain is stable across these samples, while KV's mean is larger in the
formal sample. This is a descriptive between-sample observation, not a test of
why the difference occurred. Formal gain intervals are [2.3627, 2.7716] for KV
and [1.4408, 1.6313] for STATIC. The paired descriptive interval for the relative
gap is [34.429%, 45.297%], and STATIC−0.75×KV is −0.38785 nats
[-0.55162, −0.22510]. These diagnostics quantify the drift; they neither repair
matching nor create a new confirmatory equivalence test.

| Arm | CAP correct / 2400 | CAP accuracy | Drop from C0, pp (95% CI) | Access/CAP valid-label mass | All-question valid-label mass | Formal point screen |
|---|---:|---:|---|---:|---:|---|
| C0 | 2273 | 94.708% | 0 | 99.883% | 99.950% | Pass |
| KV | 2162 | 90.083% | 4.625 [3.833, 5.417] | 99.869% | 99.945% | Pass |
| STATIC | 2220 | 92.500% | 2.208 [1.292, 3.125] | 99.908% | 99.958% | Pass |

The formal CAP point drops fall within five points, but KV's interval extends
above five points. A point-screen pass is not capability equivalence; KV also
has 2.417 points lower CAP than STATIC [1.375, 3.458]. Neither observation erases
the original independent N80 failures: KV lost **6.25 points** and CF lost
**5.9375 points**. Those named observed failures motivated the approved
continuation; no universal threshold was changed, no validity run was relabeled
passing, and the N80 is not independent validation of a tolerance chosen after
seeing it. The old CF-checker failure and subsequent producer-aware correction
remain distinct historical facts. CF was not collected in this formal study.

Formal word-access gain is +2.5530 [2.3775, 2.7340] for KV and −0.0672
[-0.1422, 0.0096] for STATIC. This reinforces why the WORD contrast cannot be
called a matched-word-access route comparison.

## Historical comparison without mixing cohorts

| Separate formal cohort | Fixed comparison | Rule gains: KV / STATIC | Assigned donor choices: KV / STATIC | Primary M contrast | Evidence status |
|---|---|---|---|---|---|
| Qwen v3 A′, N600 | w1 / L24 raw g0.1 | 4.081 / 4.179 | 52.333% / 0% | 33.432 [31.563, 35.283] | Prespecified Qwen contrast; formal mean gains closely matched (~2.4% gap) |
| Llama v4, N600 | w1 / L21 raw g0.7 | 2.489639 / 0.420604 | 51.333% / 0% | 10.4514 [9.9936, 10.8908] | Prespecified member of five-test primary family; unmatched (83.106% gap) |
| Llama continuation, N600 | w1 / L16 raw g0.5 | 2.564291 / 1.535371 | 49.917% / 0.583% | 10.1916 [9.7500, 10.6501] | Prospectively amended fixed comparison; independent N80 match passed as a point estimate, formal match failed |

The Qwen cohort is `20260925-021307_v3_confirm_confirm`; the older Llama cohort
is `20261009-005433_v4_llama31_confirm_v4_confirm`. Their published reports,
matching/signal-pilot reports and exact Qwen choice artifact were checked;
old raw cohorts were not reanalyzed. Qwen v2's unmatched w2/g0.4 comparison is
not substituted for Qwen v3 A′. Qwen's A′ signal pilot used its then-prespecified
signal/sample-size procedure; new Llama STATIC selection used access/CAP/format
and fixed N600, without attribution-based progression. These designs should not
be described as identical preregistrations.

The updated Llama intervention greatly reduces the previous access-gain
mismatch, and reverses the donor-rule accuracy ordering, while the large
attribution difference persists. It does not eliminate the prespecified formal
mismatch. Qwen remains the evidence for a closely matched mean-gain comparison;
Llama supplies an additional, stronger access-versus-attribution dissociation.
Do not pool episodes, compare raw logit magnitudes as a calibrated cross-model
scale, or test a difference between separately reported effect sizes by eye.

## What the paper can now say

A defensible statement is: **Across the tested Qwen and Llama checkpoints,
reading partner KV memory frequently changes answers about the receiver's
original assignment. Access to partner content does not alone determine those
answers: a rule-conditional residual intervention can support substantial donor
access with much less assigned-rule claiming.**

Preserve the boundaries. The Llama mean-gain match drifted outside its frozen
band; interfaces and capability costs differ; STATIC effects are not universally
zero; WORD access was not matched. This experiment does not identify a causal
position/role-binding mechanism, prove attribution-specific impairment, show
that all internal communication behaves this way, or establish consciousness.
It adds no link-cut, text-header, self-report, third-person or two-way experiment;
those statements still depend on their own cohorts and controls. The broader
paper story must also incorporate the separate source-conflict study.

## Reproduction and source fingerprints

CPU-only local reproduction uses
`/private/tmp/mb-postcollection-20261012/analyze_static.py` with the repository's
Python environment and mounted SD data. The script rechecks the frozen
continuation summary, then independently reconstructs episode statistics and
choice distributions. It writes only derived analysis outputs; raw source files
are hashed before and after. The private full-format JSON and console output
are retained alongside the script; the repository companion is compact JSON.

| Input | SHA256 |
|---|---|
| Formal identity | `72090af2e16621dc1b9890e819800e1cba72fe9b8de87ac31e3521a2ce80b985` |
| Formal config | `f90ba8b7df8fc25cacd7e70e7ffd422df471aef64d968a73fd28e2c6493fdef8` |
| Sole raw record shard | `5c7471b6aeb66bd2201ac27183f9e3022fc31b41e63e69394a6b3d30da796d23` |
| Original saved summary | `8133e5f3353003a05b7109d6149aa96ccea3180ec997f78bc75dd31af478e031` |

Sources: [continuation protocol](../../protocol/PROTOCOL_V5_CONTINUATION.md),
[fixed historical evidence](../../../configs/v5_continuation/static_evidence.json),
[original STATIC terminal audit](../../reviews/v5_static_terminal_audit_20261010.md),
[Qwen v3 formal](../v3/confirmatory_v3.md),
[Qwen matching pilot](../v3/strength_pilot_s_static_a.md),
[Qwen signal pilot](../v3/signal_pilot_aprime.md),
[Qwen exact figure numbers](../../../paper/figures/story_numbers.json),
[Llama v4 report](../v4/report.md) and [v4 machine-readable summary](../v4/summary.json).
Full source hashes, all historical run identities and frozen prerequisite pins
are retained in the cited evidence and companion JSON. No new GPU run, parameter
selection, manuscript edit or historical-result rewrite was performed.
