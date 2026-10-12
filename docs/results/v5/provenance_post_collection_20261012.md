# Provenance studies: post-collection analysis, 12 October 2026

Changing only the donor card's Robin assignment substantially shifts answers about Robin in the **receiver's original record**, including actual incorrect choices, in both studies. This extends the vulnerability beyond self-assignment questions and supports a broader conflicting-record/provenance account. It does not identify a special mechanism for the self or establish a particular cache-position mechanism.

The two studies have different inferential status. Qwen completed the original v5 protocol. Llama completed the separately frozen, pilot-informed continuation after its original capability gate failed. Their estimates are not pooled and their testing families remain separate. All results below are offline analyses of completed data; no further collection, parameter selection or subgroup filtering occurred.

## Data, verification and statistical contract

Each study contains all 600 planned episodes, three arms, 12 question types and two balanced answer orderings: **43,200 unique successful finite readouts per study**. There are no exclusions, missing keys, failures, duplicate successes or truncated record tails. Native tokenizer/template identity, deterministic question/option/physical-candidate metadata, arm hashes, frozen source identity and all pinned prerequisite files were rechecked read-only. The continuation's historical evidence and exact named exception were also reproduced.

* Qwen: `20261010-025849_v5_qwen_provenance_confirm_v5_qwen_provenance_confirm`; collection commit `ff2387d90035a110c37e4aeeb69e083543b16500`, source hash `fd12c77d6097f369`.
* Llama: `20261010-214856_v5_llama31_provenance_confirm_v5_continuation_provenance`; collection commit `69b4627d391330c16203897ba66a205f526bfdf1`, source hash `b0d01114a0c1d07c`.

The unit is the episode: average the two orderings within each episode, then take paired arm differences. Tests are two-sided paired t-tests, with 10,000 episode-bootstrap percentile 95% intervals, seed 0. Intervals are marginal, not simultaneous. Each original/amended report retains a two-test primary and six-test secondary Holm family: the unavailable checkpoint slots have bookkeeping p=1 and no estimated effects. Original Qwen inference does not incorporate the amended Llama observations. Logit differences are in nats; neither their magnitudes nor their cross-checkpoint ratio are changes in accuracy.

Choice percentages use 1,200 decisions per arm/question, but uncertainty resamples 600 episodes, not 1,200 independent choices. CAP averages two questions and both orderings per episode. All choice, quality and access summaries below are descriptive; no additional confirmatory tests were added. An empirical bootstrap interval [0,0] at a boundary means no observed error, not proof of an impossible error.

In both arms with a link, KV-P w1 is fixed. Receiver A's original card assigns self=a and Robin=r. Donor B's card assigns self=b; Robin=r in ordinary KV and Robin=d in conflict KV. Candidate meanings never switch after treatment. Both rule and code word are changed together in the donor Robin field. Thus the manipulation is an added conflicting record field, conditional on the already-present self conflict; it does not isolate rule-only versus word-only interference.

## Prespecified contrasts

The primary is `(conflict KV − ordinary KV)` on receiver-original Robin `z(d)−z(r)`. The WORD analogue is secondary. The other two secondaries are `(KV − C0)` on `(old self question − source-qualified self question)`, with each question scored as `z(b)−z(a)`.

| Study | Family | Contrast | Mean | 95% CI | Paired SD | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen, original v5 | primary | robin_rule_conflict | 29.554 | [28.175, 30.910] | 17.284 | 7.99e-180 |
| Qwen, original v5 | secondary | robin_word_conflict | 29.162 | [28.028, 30.285] | 14.197 | 1.73e-216 |
| Qwen, original v5 | secondary | rule_source_qualification | 0.091 | [-1.544, 1.785] | 21.121 | 1 |
| Qwen, original v5 | secondary | word_source_qualification | 0.507 | [-1.304, 2.320] | 22.891 | 1 |
| Llama, amended continuation | primary | robin_rule_conflict | 10.859 | [10.408, 11.305] | 5.632 | 8.36e-204 |
| Llama, amended continuation | secondary | robin_word_conflict | 8.412 | [8.204, 8.614] | 2.572 | <1e-300 (numerical underflow) |
| Llama, amended continuation | secondary | rule_source_qualification | -0.329 | [-0.771, 0.120] | 5.549 | 0.586 |
| Llama, amended continuation | secondary | word_source_qualification | 0.519 | [-0.042, 1.079] | 7.073 | 0.363 |


The two Robin contrasts show large positive shifts in both studies. None of the old-versus-qualified self interactions survives its fixed secondary correction. The latter is **not equivalence of wordings**, nor evidence that explicit source wording restores accuracy: this two-option logit contrast does not represent the entire four-option choice distribution.

## Actual receiver-original Robin mistakes

Receiver-original truth remains r in every arm. Choosing d in conflict KV therefore reports donor-card Robin content as belonging to the receiver's original card. Errors below include any non-r choice; d-replacement is separately shown.

| Study | Field | Ordinary error % | Conflict error % | Paired increase pp | 95% CI, pp | Conflict d / 1,200 | d increase pp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen, original v5 | RULE | 0.00 | 49.92 | 49.92 | [46.500, 53.250] | 599 | 49.92 |
| Qwen, original v5 | WORD | 0.08 | 52.00 | 51.92 | [48.917, 54.917] | 624 | 52.00 |
| Llama, amended continuation | RULE | 0.00 | 48.50 | 48.50 | [45.083, 51.917] | 582 | 48.50 |
| Llama, amended continuation | WORD | 1.83 | 50.00 | 48.17 | [45.833, 50.500] | 593 | 49.42 |


C0 makes no receiver-original Robin error for either field in either study. Rule errors under conflict are entirely d replacements. WORD errors need not be exactly the d-replacement rate: ordinary KV already has a few other wrong choices, especially in Llama. Both the logit and behavioral observations are therefore needed.

Raw condition means for the scored physical candidates are below. Absolute logits are descriptive components; their arbitrary common level has no standalone attribution interpretation.

| Study | Field | Arm | Mean z(d) | Mean z(r) | Mean z(d)−z(r) |
| --- | --- | --- | --- | --- | --- |
| Qwen, original v5 | RULE | C0 | 25.633 | 56.862 | -31.230 |
| Qwen, original v5 | RULE | KV | 25.759 | 55.059 | -29.300 |
| Qwen, original v5 | RULE | CONFLICT | 44.366 | 44.111 | 0.254 |
| Qwen, original v5 | WORD | C0 | 25.969 | 56.600 | -30.631 |
| Qwen, original v5 | WORD | KV | 25.592 | 54.158 | -28.566 |
| Qwen, original v5 | WORD | CONFLICT | 43.798 | 43.203 | 0.595 |
| Llama, amended continuation | RULE | C0 | 20.953 | 32.596 | -11.643 |
| Llama, amended continuation | RULE | KV | 19.528 | 30.378 | -10.850 |
| Llama, amended continuation | RULE | CONFLICT | 26.313 | 26.305 | 0.009 |
| Llama, amended continuation | WORD | C0 | 22.336 | 32.388 | -10.052 |
| Llama, amended continuation | WORD | KV | 21.698 | 30.043 | -8.344 |
| Llama, amended continuation | WORD | CONFLICT | 26.803 | 26.735 | 0.067 |


## Source-qualified self questions and the old anchors

The qualified question names the source and subject: “According to participant [A]'s original private record, which priority was [A] assigned?” The original START asks “At the start of this task, which priority were you assigned?” WORD has the corresponding code-word stems. This comparison changes a wording package, including explicit original-record reference and named versus second-person subject; it does not isolate one phrase's causal contribution.

The full qualified SELF RULE choice distribution is essential (truth=a):

| Study | Arm | a, correct % | b, donor-own % | r, original Robin % | d, spare/conflicting Robin % |
| --- | --- | --- | --- | --- | --- |
| Qwen, original v5 | C0 | 100.00 | 0.00 | 0.00 | 0.00 |
| Qwen, original v5 | KV | 18.92 | 18.17 | 55.17 | 7.75 |
| Qwen, original v5 | CONFLICT | 12.25 | 11.67 | 38.17 | 37.92 |
| Llama, amended continuation | C0 | 100.00 | 0.00 | 0.00 | 0.00 |
| Llama, amended continuation | KV | 43.92 | 40.17 | 10.83 | 5.08 |
| Llama, amended continuation | CONFLICT | 40.83 | 37.75 | 10.58 | 10.83 |


Ordinary-KV old-versus-qualified choices and accuracy:

| Study | Question | b choice % | 95% CI, % | Correct % | Any error % | 95% CI, % |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen, original v5 | START | 50.58 | [46.833, 54.417] | 49.42 | 50.58 | [46.833, 54.417] |
| Qwen, original v5 | PROV_SELF_RULE | 18.17 | [15.917, 20.500] | 18.92 | 81.08 | [78.750, 83.417] |
| Qwen, original v5 | WORD | 52.00 | [48.665, 55.333] | 48.00 | 52.00 | [48.665, 55.333] |
| Qwen, original v5 | PROV_SELF_WORD | 19.83 | [17.167, 22.583] | 17.33 | 82.67 | [80.083, 85.167] |
| Llama, amended continuation | START | 47.33 | [44.083, 50.583] | 52.67 | 47.33 | [44.083, 50.583] |
| Llama, amended continuation | PROV_SELF_RULE | 40.17 | [36.833, 43.500] | 43.92 | 56.08 | [52.667, 59.417] |
| Llama, amended continuation | WORD | 49.58 | [46.500, 52.583] | 50.08 | 49.92 | [46.833, 52.917] |
| Llama, amended continuation | PROV_SELF_WORD | 42.83 | [39.667, 46.000] | 46.50 | 53.50 | [50.333, 56.750] |


Explicit source wording reduces donor-own b selections descriptively, but does not improve overall accuracy here. Qwen often switches to Robin: ordinary qualified SELF RULE chooses r in 55.17% of decisions while correct a appears in only 18.92%; conflict divides much of this mass between r and d. Llama also retains substantial wrong choices on qualified questions. Calling this a wording “fix” would confuse fewer b selections with more correct answers. The interaction's nonsignificance does not erase these descriptive multinomial differences or demonstrate equivalent responses. Complete WORD distributions and all per-arm choice intervals are in the JSON.

## Rule and WORD access, kept field-specific

Donor-own access is the original spare-foil score `z(b)−z(d)` in ordinary KV minus C0, where d is unused. Donor-Robin specificity is `z(d)−z(r)` in conflict minus ordinary KV on the donor-record question. They are different diagnostics. In conflict KV, d is not an unused foil; no such claim is made for that arm.

| Study | Field | Formal access contrast | Mean | 95% CI | One-sided 95% lower bound |
| --- | --- | --- | --- | --- | --- |
| Qwen, original v5 | RULE | donor_own_access_KV_minus_C0 | 2.723 | [2.228, 3.218] | 2.306 |
| Qwen, original v5 | RULE | donor_robin_specificity_CONFLICT_minus_KV | 29.008 | [27.652, 30.364] | 27.867 |
| Qwen, original v5 | WORD | donor_own_access_KV_minus_C0 | -0.997 | [-1.747, -0.222] | -1.625 |
| Qwen, original v5 | WORD | donor_robin_specificity_CONFLICT_minus_KV | 28.764 | [27.606, 29.892] | 27.789 |
| Llama, amended continuation | RULE | donor_own_access_KV_minus_C0 | 3.219 | [2.928, 3.522] | 2.978 |
| Llama, amended continuation | RULE | donor_robin_specificity_CONFLICT_minus_KV | 10.916 | [10.467, 11.370] | 10.538 |
| Llama, amended continuation | WORD | donor_own_access_KV_minus_C0 | 3.290 | [3.043, 3.543] | 3.084 |
| Llama, amended continuation | WORD | donor_robin_specificity_CONFLICT_minus_KV | 8.395 | [8.193, 8.595] | 8.224 |


Qwen's prespecified N80 donor-own WORD access diagnostic was already negative (−0.511 nats; one-sided lower bound −2.447), and formal donor-own WORD gain remains negative. Its ordinary donor-own WORD accuracy is 20.00% under both C0 and KV. This limitation must remain visible; the earlier rule gate never certified own-word transfer. **It does not imply that Robin WORD content is inaccessible:** donor-Robin WORD specificity is strongly positive and the conflict produces wrong receiver-Robin word choices. Llama has positive formal donor-own and donor-Robin diagnostics for both fields. Ordinary donor-own RULE accuracy is nevertheless only 18.67% in Qwen and 43.00% in Llama, so a positive gain is not reliable retrieval on every episode. In conflict KV donor-Robin RULE accuracy is 48.33%/48.92% and WORD accuracy 51.50%/48.92% (Qwen/Llama); source-specific access is imperfect even where the contrast is large.

## Capability, format and preserved admission history

| Study | Arm | CAP % | 95% CI, % | CAP drop pp | Paired 95% CI, pp | All12 label mass % |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen, original v5 | C0 | 99.75 | [99.542, 99.917] | 0.00 | [0.000, 0.000] | 100.0000 |
| Qwen, original v5 | KV | 98.88 | [98.458, 99.292] | 0.88 | [0.417, 1.333] | 99.9379 |
| Qwen, original v5 | CONFLICT | 98.75 | [98.292, 99.167] | 1.00 | [0.542, 1.458] | 99.9404 |
| Llama, amended continuation | C0 | 94.83 | [94.041, 95.625] | 0.00 | [0.000, 0.000] | 99.9098 |
| Llama, amended continuation | KV | 90.17 | [89.167, 91.167] | 4.67 | [3.875, 5.458] | 99.5815 |
| Llama, amended continuation | CONFLICT | 89.88 | [88.875, 90.875] | 4.96 | [4.167, 5.792] | 99.5791 |


Original Qwen N80 validity passed: CAP was 100% in C0 and 98.4375% in both linked arms; the two required rule-access lower bounds were positive. WORD did not gate progression and remains access-limited as above.

Original Llama N80 validity **failed**: C0 CAP 94.6875%, ordinary KV 89.0625% (5.625-point loss), conflict KV 89.6875% (exactly five-point loss). Both rule-access requirements and format checks passed. The separate continuation admitted only the named ordinary-KV loss prospectively and collected fresh N600; it did not validate a new general tolerance. Formal point losses happen to be below five points, but their paired intervals extend above five. Neither this observation nor the completed analysis relabels the original gate as passing, establishes capability equivalence, or supports “general capability preserved.”

## Interpretation for the paper

1. **Supported:** a donor-only Robin conflict changes answers about the receiver's explicitly named original record, including approximately 50-percentage-point increases in actual rule mistakes. Original no-link and ordinary-KV Robin answers are accurate. The error is therefore not confined to self-assignment questions and is sensitive to the conflicting content field.
2. **Supported with limits:** both studies are consistent with broader conflicting-record substitution/interference under this interface. They show a record-provenance challenge despite explicit source cues; they do not distinguish literal memory overwriting from readout-time interference, and unequal capability loss constrains a perfectly isolated route interpretation. The original and amended studies are reported separately, not as one untouched two-checkpoint confirmatory family.
3. **Not supported:** privileged self vulnerability, identity fusion, consciousness, or a demonstrated positional mechanism. Own-record conflict is present in both linked arms, and original self/Robin rehearsal differs. There is no balanced self-versus-Robin factorial or mediation intervention.
4. **Do not overstate wording or WORD results:** explicit original-card wording changes the answer distribution without restoring overall self accuracy. Qwen own-WORD transfer is access-limited; Robin-WORD specificity is a different successful diagnostic. Nonsignificant source-qualification interactions are not an equivalence test.

These results strengthen a bounded empirical paper about correct original attribution under internal memory sharing, while weakening a claim that the phenomenon specifically targets a special “self” mechanism. They do not require outcome-driven retuning, additional samples or a new GPU study to be reportable.

## Reproduction and artifact provenance

Run the following from the repository with its pinned local tokenizer assets and mounted SD data. Both scripts are private derived-report tools; neither writes any run directory, modifies source, downloads a model or imports torch.

```bash
.venv/bin/python /private/tmp/mb-postcollection-20261012/recompute_provenance.py
.venv/bin/python /private/tmp/mb-postcollection-20261012/write_provenance_report.py
```

The recomputation rebuilds both native identities, verifies pinned prerequisites, checks every deterministic raw record, invokes the unchanged pure formal statistic and retains the separate fixed Holm families. Independently assembled physical-candidate vectors, direct SciPy one-sample tests on paired differences, independent percentile resampling, and a separate Holm implementation reproduce all four estimated contrasts per study. Both stored summaries agree with the recomputation: Qwen's `v5_provenance_contrasts.json` and Llama's `v5_continuation_summary.json`, including its external continuation envelope and separate amended families. The latter was written by the external continuation wrapper despite `mb.run` having `post=[]`. Comparisons use relative tolerance 1e-12, absolute tolerance 1e-12 for other numeric fields and zero absolute tolerance for p-values. No historical result file was created or replaced. Per-file differences and hashes are in the companion JSON.

Source and input SHA256 values, every prespecified test including unavailable slots, raw components, all arm/question choice distributions and intervals, quality, access and retained validity summaries are in the companion JSON. The full private numerical reconstruction is `provenance_recomputed_full.json` in the same private directory.


Recomputation script SHA256: `52a870fdb55b6547a739c0ec03291b711b0c3eb1a155f10f95890a8d9ab49c69`.

| Input | Qwen SHA256 | Llama SHA256 |
| --- | --- | --- |
| identity.json | 95a6378f980734c925be8207f3c419d0046d46e24f27678ed8352caa6af2a0a7 | 966e7b825d5dee24a12e2bdd882777f60c24ca2254b8ce7af38360b4d727da76 |
| config.yaml | 9e9b0151a1ea6a2093f9c79e5e3864f396843a77f9ac0689420905bea83cc5bb | 5fe3ff1671dbd564f4fc8c9988d6569b14ca8b9e31951f20da9473253df44c28 |
| records/attempt-000.jsonl | f907f76ddb3d9fabe1853ebb9ed0c0b5a64419ed1c5b98ea4535a6ca92a6f8f6 | ba7d5e1dc08e037558aeae63fa1bc0e1ab117df8fc9d39765e5ebd97f8df7e6d |
