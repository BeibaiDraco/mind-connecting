# Independent v4 statistical reconstruction — 2026-10-09

**Verdict:** the completed formal run reproduces the frozen statistical output. No scoring, pairing, bootstrap, or multiplicity discrepancy was found. All five primary and four secondary comparisons are estimable with all 600 episodes. The available STATIC comparison remains in the five-test family, while its matched-route interpretation remains unvalidated.

## Scope and independence

- Run: `20261009-005433_v4_llama31_confirm_v4_confirm`; local SD backup, 84,000 successful records, seven unique arms (K*=K1), ten questions and two balanced orderings per episode. No exclusions, pooling with Qwen, imputation, new model execution, or changes to raw data. The prior technical completion audit established complete keys, intact original/resumed shards, and shared FULL/RF snapshots and TAG/UNTAG donor bodies.
- The independent script reads both raw JSONL shards and implements semantic logit lookup, within-ordering scores, episode averaging, paired contrasts, manual Holm correction and resampling. It does not call `mb.readouts`, `mb.analyze`, or `mb.v4` scoring/statistics functions. It imports `mb.tasks` only to reconstruct the frozen episode materials and physical candidate identities. This is an independent statistical implementation, not an independent material generator.
- All 84,000 raw option-to-meaning mappings agree with the episode assignments, including the changed donor assignment in CF. There are no tied maximum logits. The 2,400 original/CF access-question pairs have identical physical options and question text hashes; candidate r0/r1 identities agree with the original donor and replacement spare.
- The two orderings are averaged within each episode before inference. Every test uses 600 paired differences (599 degrees of freedom), SciPy `ttest_rel`, independently calculated mean/SD/SE/t, and 10,000 percentile bootstrap resamples with NumPy `default_rng(0)`. The same sorted episode ordering and fresh seed per contrast match the frozen specification. Holm is applied manually to all five primary tests and separately to all four secondary tests. Bootstrap intervals are ordinary 95% intervals, not simultaneous familywise intervals.
- The stored scientific output is read only after independent reconstruction. All 340 compared numeric/boolean fields pass; maximum absolute discrepancy is `7.105427357601002e-15`. Compared fields cover every contrast statistic and interval, choice/component descriptions, access/quality summaries, both content checks, and matching flags. Tiny differences reflect floating-point aggregation.

## Score definitions

For a question q, let L(q) be the raw logit of the partner option minus that of the correct self option; for the Robin question, use the Robin option as denominator. Compute `M=L(START)-L(START_R)`, `M_NOW=L(NOW)-L(NOW_R)`, and `M_WORD=L(WORD)-L(WORD_R)` within ordering, then average the two orderings. These are logit differences in natural-log units, not percentages. Access is `z(partner)-z(unused)` for rules and `z(partner)-z(distractor)` for words.

CF is scored with fixed **physical** candidates: `C_content=[z(r1)-z(r0)]_CF-[z(r1)-z(r0)]_K*`, where r0 is the original donor assignment and r1 is the spare/replacement. Semantic partner and spare labels swap in CF, so subtracting two semantic access scores would have the wrong interpretation. The independent reconstruction indexes physical option strings in both arms.

## Prespecified comparisons

All rows below retain N=600. Intervals are episode-bootstrap 95% intervals.

### Primary family

| Contrast | Metric | Mean difference | 95% interval | Paired t | Holm p |
|---|---|---:|---|---:|---:|
| K* − C0 | M | 10.822892 | [10.374555, 11.252879] | 48.008681 | 5.24149e-207 |
| K1 − STATIC | M | 10.451395 | [9.993621, 10.890800] | 45.554471 | 1.83325e-196 |
| K* − TAG | M | 11.023481 | [10.573019, 11.457474] | 48.313322 | 3.43589e-208 |
| K* − RF | M | 10.893118 | [10.455010, 11.323643] | 48.781143 | 4.2981e-210 |
| UNTAG − TAG | M_NOW | 3.725314 | [3.366983, 4.081627] | 20.106345 | 4.21388e-69 |

### Secondary family

| Contrast | Metric | Mean difference | 95% interval | Paired t | Holm p |
|---|---|---:|---|---:|---:|
| K* − C0 | M_NOW | 8.888659 | [8.454525, 9.319901] | 40.397383 | 1.41072e-172 |
| K* − C0 | M_WORD | 7.005848 | [6.534415, 7.484114] | 29.156192 | 1.57518e-116 |
| RF − C0 | M_NOW | 1.916822 | [1.630896, 2.213644] | 12.856694 | 2.79721e-33 |
| RF − C0 | M_WORD | -0.329771 | [-0.494763, -0.162211] | -3.901459 | 0.000106452 |

All five primary contrasts are positive after correction. Three secondary contrasts are positive; RF−C0 on M_WORD is negative after correction. Each result is reported separately. This does not establish an access-matched route effect or a universal replication claim.

## Raw components and actual choices

Table entries are mean `self-question partner-minus-own / Robin-question partner-minus-Robin` logit components. Their difference gives the corresponding mean corrected score.

| Arm | START components | NOW components | WORD components |
|---|---:|---:|---:|
| C0 | -12.025112 / -11.841796 | -9.061021 / -10.571665 | -10.789700 / -10.391078 |
| K* | 0.046540 / -10.593037 | 0.209301 / -10.190001 | -0.114233 / -6.721459 |
| RF | -12.061204 / -11.807663 | -7.195457 / -10.622923 | -10.426232 / -9.697839 |
| CF | -0.064896 / -10.578402 | -0.049838 / -10.162125 | -0.357855 / -6.683128 |
| STATIC | -9.656772 / -9.844954 | -6.924425 / -9.047946 | -8.842981 / -8.650144 |
| TAG | -12.007609 / -11.623705 | -4.590574 / -10.292566 | -10.129148 / -10.277934 |
| UNTAG | -11.566680 / -11.232663 | -0.602116 / -10.029422 | -9.638040 / -9.604587 |

The following rates are percentages of ordering-level argmax choices selecting the partner option, averaged within episode and then across episodes. Each arm has 1,200 decisions per question; the inference unit remains 600 episodes. The CF partner option is the replacement donor content. These are not counts of independent subjects or a pooled-probability argmax.

| Arm | START | START_R | NOW | NOW_R | WORD | WORD_R |
|---|---:|---:|---:|---:|---:|---:|
| C0 | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |
| K* | 51.333% | 0.000% | 51.500% | 0.000% | 48.750% | 1.833% |
| RF | 0.000% | 0.000% | 7.083% | 0.000% | 1.000% | 0.083% |
| CF | 50.833% | 0.000% | 49.750% | 0.000% | 48.167% | 1.333% |
| STATIC | 0.000% | 0.000% | 2.417% | 0.000% | 0.333% | 0.000% |
| TAG | 0.000% | 0.000% | 2.250% | 0.000% | 0.417% | 0.000% |
| UNTAG | 0.000% | 0.000% | 42.167% | 0.000% | 0.417% | 0.083% |

**RF WORD qualification:** relative to C0, the self-question logit component increases by 0.363469, but the Robin component increases by 0.693239. Their subtraction yields −0.329771. Meanwhile raw WORD partner choice increases from 0% to 1% (WORD_R from 0% to 0.083%). The significant negative corrected score therefore does not mean fewer partner-word choices or stronger ownership preservation. RF also retains a positive M_NOW shift and 7.083% NOW partner choice, so cutting the link does not restore every endpoint to baseline.

## Access, capability, format and content validity

Access gain is the paired mean ACC_RULE logit increment over C0. Label mass and its eligibility/drop screen below use only ACC_RULE, ACC_WORD, CAP0 and CAP1, as in the frozen access-table function; they do not average all ten formal questions. CAP averages both capability questions and both orderings. Drops are percentage points.

| Arm | Rule access gain | Access partner choice | CAP accuracy | CAP drop vs C0 | Access-question label mass | Engineering eligible |
|---|---:|---:|---:|---:|---:|---|
| C0 | 0.000000 | 14.417% | 94.750% | 0.000000 | 99.871090% | yes |
| K* | 2.489639 | 43.417% | 89.750% | 5.000000 | 99.865719% | yes |
| RF | -0.116017 | 10.833% | 94.708% | 0.041667 | 99.873425% | yes |
| CF | 2.577086 | 44.667% | 89.667% | 5.083333 | 99.864581% | no |
| STATIC | 0.420604 | 17.083% | 94.917% | -0.166667 | 98.511452% | yes |
| TAG | 5.918279 | 86.583% | 94.458% | 0.291667 | 99.894093% | yes |
| UNTAG | 0.656322 | 27.667% | 94.208% | 0.541667 | 99.873305% | yes |

- K* CAP is 89.75%, versus C0 94.75%, giving exactly the allowed five-percentage-point drop. It is eligible under the prespecified relative-drop rule, but capability is not unaffected. The baseline CAP≥90% suitability gate is a different rule and must not be silently applied to formal treatment arms.
- CF CAP is 89.6667%, a 5.08333-point drop. It narrowly exceeds the same formal engineering screen by 0.08333 percentage point. Preserve and report this control-quality limitation; do not exclude CF episodes, reselect settings, or retroactively discard completed contrasts. Independent pre-formal core validity passed.
- STATIC is present and estimable, but its formal rule access gain is 0.420604 versus K1 2.489639 (gap 2.069035, beyond the 25% tolerance of 0.622410). Both `formal_matched` and the frozen `independent_route_validated` are false. Report the observed K1−STATIC contrast and its five-family Holm p; do not replace it with p=1 or call the arm unavailable. It cannot carry an equal-access route-mechanism claim.
- TAG rule access gain (5.918279) and partner access choice (86.583%) exceed K* (2.489639; 43.417%), despite zero TAG START partner choices. This supports separating access from assigned-rule attribution, while the K*−TAG contrast is not an intervention at equal access strength. UNTAG versus TAG shares its saved body but changes access as well as current-rule adoption; avoid claiming all non-source processes were held equal.

| Formal content check | Mean | One-sided 95% bootstrap lower bound | N |
|---|---:|---:|---:|
| rule | 5.032632 | 4.741456 | 600 |
| word | 5.031052 | 4.802713 | 600 |

Both fixed-physical-candidate content lower bounds exceed zero. The word check therefore supports successful content manipulation, while the CF capability qualification above remains. No new formal stopping/reselection rule was applied.

## Reproducibility evidence

- Identity SHA256: `fc65fc7fa24644263cc893bea047f5688d41ae19260fdd92773cd88b4aa3c140`.
- Original shard SHA256: `60fe2fee47243260f5361a76f15e20ea569587fcd4f3986171201b193051a802`.
- Resumed shard SHA256: `472283826082ef6339b96bc871160c486d33fa5d2314e05a0eac875bbcf4db5e`.
- Stored `v4_contrasts.json` SHA256: `3e051778c83d1ab5fdc93ec28cbd240f4fa12c3fac7dc6d7ab3955621184f66b`.
- Independent reconstruction script SHA256: `ac43bb87f894773b1f72e8618c9dcb598c7da4ec98f6470c23e8ee58d3b2770a`.
- Independent numeric evidence SHA256: `31203a7253547592bc75c356535b94e4b6f1f413a4df70c8e567c6f847678149`. Private engineering artifacts are named `independent_v4_statistics_20261009.py` and `independent_v4_statistics_20261009.json`; no raw data is copied into this review.

No mismatch or outcome-dependent change was identified. Interpret these findings for this checkpoint and task; do not pool episodes across models, claim consciousness or subject counts, or equate a significant logit contrast with an equivalent change in behavioral choice rates.

## Reporting implementation review

The first `--check-only` attempt exposed an engineering portability issue: the report required the GPU's absolute `/workspace/mb-data/...` calibration path to exist on the Mac. The reporting agent corrected only the derived-report verifier. It now preserves the frozen path strings and checks their agreement across config, metadata and identity, then verifies the corresponding SD backup blob against its pinned SHA256. Frozen experiment files and raw records were not changed.

After that correction, `scripts/report_v4_formal.py --check-only` passes on the Mac and reproduces the complete frozen output. A further 205 independent numeric comparisons verify the generated `docs/results/v4/summary.json` contrasts, all raw partner-choice rates, metric means and self/Robin components against the separate raw-logit reconstruction. The report retains five/four families, marks STATIC estimable but unmatched, distinguishes four-question and all-question label mass, and reports both the RF WORD sign reversal and the K*/CF capability boundary. No remaining statistical or reporting correctness blocker was identified.

Offline validation: **266 passed, 5 skipped**; `git diff --check` passes. The independent review does not modify STATUS, the decision log, frozen source, or raw data.

Reviewed reporting script SHA256: `f4dcc88848b7e7e84d1c7aee3a3496ed2d7c797ec57bb3100bcb7500677b850d`.
