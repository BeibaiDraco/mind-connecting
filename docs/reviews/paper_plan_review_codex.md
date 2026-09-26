# Review of the Paper and Figure Plan (Codex, 2026-09-25)

To the PI: this paper already has a main line worth writing: **when two instances of the same model share internal information, being able to read out the content and being able to judge attribution correctly are two different things; the difference depends on the specific way of connecting, and most of the attribution shift for the initial rule depends on continuing to read the partner's cache while answering.** The means of the key large effects can be reproduced from the per-trial records on the SD card. The biggest risk now is not miscalculated numbers but stating these conditional results as broader psychological or mechanistic conclusions. Before writing, the five things I most recommend doing are:

1. Change "cannot notice", "not caused by wording", "the extraction mechanism has been localized" and "will not merge" into what the readouts actually support; narrow the abstract and figure titles along with them.
2. Correct two places where the measurement does not match the caption: G2 measures content access, not claiming; the 99% measures the code-word mention rate, not a self-claiming rate annotated item by item.
3. Keep the three key controls: A′, third person and link-cut answering; change "same amount of information" to "mean ACC-rule increment approximately matched", and explain "equivalence" as a prespecified one-sided effect-preservation criterion.
4. Add choice rates, raw components and a concise interface figure to the main text. The third-person result should stay in the main text; the "how many minds" self-report moves to the appendix. Compress whitespace in the illustrations first, not the key limitations.
5. Given the audience, I would favor COLM first; if you want to fully document this series of controls and enter a revisable review process fairly quickly, TMLR is also a very good fit. Do not lay out the paper on the assumption that "every conference is 9 pages".

This file is review comments and writing preparation, **not a new research decision**. PLAN, the results summaries, protocols, figures and scripts were not modified; no GPU was started and nothing was published externally. Follow-up research that needs a PI decision is listed only as suggestions.

Review baseline: the paper materials after `e884874`; task-claim commit `e0a03f1`. I read AGENTS, STATUS, PLAN, ALL_RESULTS, the day's summary, the relevant sections of all three protocol versions, the v2/v3 stage reports and the last 20 entries of decision_log; I rendered the 13-page figure book and looked at it page by page, and also checked the task illustrations, data panels, figure generation and scoring logic. Below, "main-text Figures 1–6" follow the PLAN numbering; the figure book has its own numbering.

## Must change

### M1. First bring the claims table, abstract and contributions paragraph to the same strength of evidence

**Rationale:** Although PLAN §1.3 marks evidence levels, §1.1, §1.4 and the English captions drop the qualifications again. In particular, "as long as … it will …" both goes beyond the scope of a single model and a single task, and ignores that the rule-attribution effect is very small at w=0.3/0.5. A single closing sentence saying "we do not claim consciousness" cannot offset "without noticing" and "no merging" in the main text.

**Item-by-item ruling and suggested rewrites:**

| Claim | What the evidence actually supports | Suggested wording and level |
|---|---|---|
| C1 reading memory leads to claiming; only about me; capability not impaired | v2 D's ΔM=55.834 is a confirmatory large effect; self item +59.362, Robin item +3.528, so it is relative self-specificity, not Robin being completely unmoved. E replicates on different rehearsal material, and G2 validates content access. CAP drops slightly | "Under this model, task and the selected KV-P interface, partner content significantly shifts the receiver's report of its own initial assignment; the shift for Robin is much smaller, and the measured general-knowledge items and format still meet the engineering thresholds." D/E are confirmatory; the decomposition and capability metrics are presented according to their respective analysis status; G2 is listed separately with N=60 |
| C2 cannot notice | U-closed/U-open are descriptive self-reports; it was not validated that they reliably detect injection, and internal anomaly detection was not measured | "Under these self-report prompts, the answers rarely point explicitly to the partner as the source." It cannot be inferred that nothing was detected internally, that the model cannot notice, or that there is no consciousness; rename the 99% first as per M3 |
| C3 the channel determines attribution | In A′, with the mean ACC-rule increment approximately matched, KV-P and STATIC show a confirmatory difference in M; C confirmed the difference for specific language prefixes | "Source-attribution reports are sensitive to the connection method, and a single content-access metric is not enough to explain the difference." Do not write "it is not the content itself that determines it", and do not treat all channels as one unified balanced experiment |
| C4 it is an error at retrieval, and it leaves a trace | The FULL−RF difference in M and the RF−C0 difference in M_NOW are confirmatory; they show that continued reading plays an important role during answering | "The initial-rule attribution shift depends mainly on access to the partner's cache during answering; after the link is cut, the current-rule report is still shifted." Do not claim that the internal source-monitoring mechanism has been localized, that memory is entirely unchanged, or that the real behavioral intention has changed |
| C5 not caused by wording | At the main strength, strict third person meets the prespecified preservation criterion; the w1 secondary comparison shows a significant drop of 3.211 nat; the rewrite simultaneously changes grammatical person, name labels, note format, etc. | "The effect does not require second-person prompts or first-person notes; third person and explicit name labels did not eliminate the effect." Do not write "wording has no effect" |
| N1 connected does not mean merged | The B′ pilot did not reach the prespecified advancement threshold; it is not a test of zero effect, much less a test of subject fusion | "Neither tested loop reached the prespecified 0.10 advancement threshold for START excess; descriptive paired results are in the appendix." Delete the "no merging" conclusion from the abstract |
| N2 weak connections do not cause claiming | v1 TWO−ONE is not significant; it tests the increment from the return path, not ONE−C0; the v1 per-arm −C0 values and choice rates are descriptive | "Under the residual-bridge settings tested, no positive self-specific initial-rule shift was observed." TWO−ONE≈0 cannot be used to prove that weak connections have no effect; v2 E's near-zero R−C0 is another piece of direct evidence, but it still does not prove zero everywhere |

A usable one-sentence draft:

> On two instances of Qwen3-4B-Instruct-2507, directly reading the partner's prefill KV cache can lead the receiver to report the partner's rule as its own initial assignment. A static steering vector with a similar mean rule-access score did not produce the same attribution shift. The phenomenon persists under strict third-person records and depends mainly on continued access to the partner's cache during answering; after the link is cut, the current-rule report still retains some shift.

### M2. The G2 numbers are right, but the caption "claiming follows the content" points to the wrong endpoint

**Location:** PLAN C1, the rationale for Figure 3(b); the G2 row of `summary_2026-09-25.md`; page 5 of the figure book; the y-axis "claim moves with B's content" in `fig_main.pdf`.

**Rationale:** `pilot_c.json:g2_detail` and `readouts.content_cf_score` compute the difference between fixed physical candidates on the **ACC_RULE/ACC_WORD** items:

`C_content = [z(r1)−z(r0)]_CF − [z(r1)−z(r0)]_original`.

This shows that the receiver's content readout changes when the donor content is substituted, ruling out "a content-free perturbation only" as a complete explanation of the access effect. It does not directly test the content specificity of START or M. The formal G2 diagnostic has 60 episodes, not the 600 written loosely in the C1 column. The raw values, rule 38.774985 and code word 35.577571, both reproduce.

**Specific fix:** Change the panel title to "Partner-content transfer" and the y-axis to "Counterfactual effect on access readout (nats)"; the caption should state the item types, the fixed r0/r1, the one-sided 95% lower bound and N=60. Write C1 as "the attribution shift is accompanied by counterfactually validated content transfer". If you want separate evidence that "attribution switches with the donor content", you can examine the START/START_R records of the existing signal pilot and do a supplementary exploratory analysis with fixed physical candidates; this post hoc analysis must not be relabeled as the formal G2 confirmatory test.

### M3. "99%" cannot be labeled "99% claiming", and self-reports cannot be labeled "did not notice"

**Location:** PLAN C2, §1.1, Figure 3(d), the appendix strength figure, pages 6/11/12 of the figure book.

**Rationale:** `make_paper_figures.py:u_open_mentions` only uses a regex to check whether the partner's code word appears in the text; it does not judge whom the code word is attributed to, whether it is denied, or whether it is quoted as someone else's. The raw w2 figure is indeed **297/300 mentioned B's code word**; I looked at the first 3 by episode ID, and all three used self-attribution wording, but this does not count the other 297 as semantically verified. In U-closed, the "two/partly shared" share falling from about 0.32 to 0.22 is also not a calibrated anomaly-detection rate; C0 already chose this kind of answer about one third of the time.

**Specific fix:**

- The existing figure should only say "mentions B's code word (99%)", and for the partner's name "mentions B's codename"; do not treat "not naming" as "not knowing the source". The open self-report is **80 tokens**; the "80 words" in ALL_RESULTS §0 should be corrected.
- Delete "Does not notice", "silently" and "without noticing" as result conclusions; the main text keeps at most one descriptive sentence, with the full distribution, prompts and raw text in the appendix.
- To report a self-claiming rate, first have the PI confirm a post hoc descriptive annotation scheme: distinguish self-attribution, partner attribution, mention only, denial and unclear; annotate the full set or a sample fixed in advance, and state who verified it/the agreement. A loose regex for a sentence containing "my" cannot replace semantic judgment.

The related original work also reminds us to be cautious: Lindsey's study separates verifiable detection from incidental self-description; another Qwen study reported outputs denying an injection while intermediate layers still carried a detection signal. These are not direct evidence about this model, but they suffice to show that "not saying it" and "not detecting it internally" cannot be equated. [Lindsey original](https://transformer-circuits.pub/2025/introspection/index.html), [Pearson-Vogel et al. abstract](https://arxiv.org/abs/2602.20031).

### M4. The "equivalence test" must be described as what it actually is, a one-sided preservation criterion, and the wording confound must be kept

**Rationale:** The actual criterion in the frozen PROTOCOL_V3 §7 is: the 90% bootstrap lower bound of D is above `−0.2 × E`, where `D=M_3ps−M_2p` and `E=M_2p−M_C0`. It has only a lower bound and is not the usual two-sided equivalence test with upper and lower bounds. The bound is also estimated from E on the same formal sample. The historical naming in the original protocol and the JSON is kept, but if the paper writes only "equivalence" it will give statistical reviewers the wrong impression.

**Specific fix:** Call it a "prespecified effect-preservation criterion (one-sided, allowing a drop of at most 20%)", and report verbatim D=−0.714, 90% CI [−1.262, −0.184], bound −11.330, criterion passed; do not write passing as "the two conditions are the same". State that the scope is limited to the w2 saturated segment.

A supplementary calculation can jointly resample `D+0.2E`, bringing the uncertainty of the bound estimate into it. The read-only, post hoc sensitivity recomputation done for this review gives a mean of **10.616**, with a 90% interval of about **[10.139, 11.091]**, still clearly above 0; this strengthens the robustness of the result, but it must not quietly replace the frozen analysis or upgrade its statistical status.

w1's −3.211 [−4.860, −1.563] is a prespecified **secondary comparison**; third-person ACC is 18.576 vs. 4.081, and the ratio of mean attention mass is 1.006. The two are not balanced on all decodable content, and approximately equal mean attention does not mean the allocation is the same for every head, layer and token. The rewrite also adds name labels and changes the note, so the effect of grammatical person cannot be estimated separately. Narrowing the conclusion to "grammatical person is not a necessary condition" is safer than "wording has only a small effect".

### M5. "Same amount of information" and "the channel determines everything" go beyond the design of A′ and the language control

**Rationale:** A′ matches the **mean ACC-rule increment across episodes**: KV-P w1 is 4.081 and STATIC 4.179 nat; this is not mutual information, total amount of information, or a one-to-one balance per episode. The read-only recomputed rates of picking the partner's rule in the ACC_RULE four-way choice are **19.83% and 15.33%** respectively; the ACC-word increments are 6.122 and −0.048. STATIC encodes only the rule direction, whereas KV-P contains the whole cache, including the prompt and note; the two also differ in number of layers, representational form and temporal structure. A′ is therefore an overall comparison of two connection schemes.

Figure 4 is also not eight conditions from a single randomized experiment: the residual bar comes from **v2_bal's balanced2 material, g=0.3**; STATIC/w1 come from v3; w2 and language come from v2_main. Materials, splits and strengths are not all the same. It cannot be called "v1's residual null bar", and paired inferences cannot be made across bars.

**Specific fix:**

- Write "matched mean rule-access score" throughout, and keep the confirmatory **paired difference** of +33.432 as the core; add a small panel to the figure directly showing the ACC-rule matching.
- Split the channel figure into the A′ KV/STATIC pair and C's language-label pair; residual and w2 can go in a smaller background panel or in the appendix, each group labeled with run/materials/N. Do not use the heights of a whole row of bars in place of formal comparisons.
- C's +26.634 is **the untag−tag difference on M_NOW**, not the value of untagged itself relative to C0; the latter is +25.255. It is fine for the current figure to show both M and M_NOW, but they should be labeled "initial-assignment report/current-rule report", and one should not directly infer "language changes only intention, KV changes memory".
- LANG-self is 19.471 lower than untag, the opposite of the prespecified direction, and must be kept. LANG-stranger−tag≈0 is a failure to find a difference, not equivalence evidence that it does not matter whom the label names. The protective effect of source labels is supported only for the tested text channel; it must not be written as though a general safeguard for KV-sharing systems already exists.

### M6. The link-cut experiment answers access dependence; on its own it cannot localize the "extraction mechanism" or rule out memory changes

**Rationale:** FULL and RF branch from the same C48 state; what is intervened on is whether the partner's cache is still read during answering. The result is good, but it cannot distinguish internal stages such as question processing, attention competition, source binding and final output selection. The original prefill cache was never overwritten in the first place; "weights not trained" also does not mean that the context state is unaffected. The formal KV-P experiment has no RO control that is connected only while reading the question, so conclusions from v1's residual RO cannot be transplanted.

After the link cut, ΔM is still **1.874 [1.537, 2.222]** and M_NOW is **13.342**; more worth stating in the limitations is that **M_WORD is still 10.490 [8.986, 12.035]**. So "memory attribution fully recovers" is also inaccurate. "Which one is used now" is the declared current rule; BEH was discontinued in v1, and there is no behavioral evidence that intentions or decisions have changed.

**Specific fix:** Title it "Attribution depends on access during answering"; the caption says "the shift in initial-rule reports is greatly reduced, while current-rule and code-word reports still show residue". Change "localized the mechanism" to "constrained the possible explanations with a timing intervention". "Trace" can be used colloquially, but the main text should state clearly that it is the report shift after the link cut, which may be carried by the reflection text or its cache, and that long-term persistence was not measured.

### M7. B′ not advancing and v1 being non-significant cannot be packaged as confirmatory negatives

**Rationale and specific fixes:**

- B′ ALL's START excess difference is **0.06734**, 90% CI **[0.02617, 0.10906]**: the lower bound is above 0, and the upper bound exceeds 0.10. It did not reach the point-estimate advancement threshold; it is neither "no loop effect" nor a ruling-out of a 0.10 effect. PC is 0.00172 [0, 0.00445]. Write both as "did not meet the advancement criterion".
- "Everything disappears after the link cut" needs to be changed: on START, one-wins for KV-P w2 and PC is still **3.125%**; on NOW, one-wins for KV-P w2 is still **41.25%**. The figure shows START, so the caption must restrict the item type and cannot generalize to all paired outcomes.
- These answers come from two independent branches and cannot be called joint convergence, synchrony or "merging" at the same moment. Use "paired answer agreement/one-sided adoption" throughout, and attach the operational definition of excess.
- v1's TWO−ONE=−0.073 only shows that no M effect of adding the return path was found at g*=0.2. v1's ONE−C0≈−0.148 and the 100% original-rule choice rate on START are useful descriptive evidence and should be written at their actual level; do not pass them off as a preregistered confirmatory ONE−C0 negative.

### M8. Change "capability intact" to "a small drop, within the prespecified engineering tolerance"

**Rationale:** In the v2 main results CAP goes from about 0.997 to 0.977, a drop of **2.0 percentage points**; the episode bootstrap done for this review gives a 95% interval of about a **1.4–2.6 percentage point** drop. The engineering threshold is a point-estimate screen allowing a drop of up to 5 percentage points, not a capability equivalence test. 18 baseline-screened general-knowledge items, with two sampled per episode, cannot represent general reasoning ability either.

**Specific fix:** Change Figure 3(c) to "Capability within the prespecified tolerance", and report knowledge-item accuracy and label probability separately, not lumped together as accuracy. Preferably use points and intervals and mark the 5-percentage-point tolerance; the existing bar axis truncated at 0.8 should be clearly marked, to avoid misleading bar lengths. The abstract can say "retains high measured capability"; do not write "capability not impaired".

### M9. The research-process and "preregistration" narrative must keep the adaptive process

**Rationale:** Page 13 of the figure book, "Every study passed the same gates … 80 … 600", is not true: v1's formal N=300 and it had no v2-style M signal gate; B′ used excess and a different threshold; T3/T3b were revised after manipulation checks failed; the original A_K comparison was unmatched; later studies were proposed after seeing earlier results. Parameter selection not reading M is a different thing from study advancement/redesign not looking at M.

**Specific fix:** Split the figure into two flows, v1 and v2/v3, explicitly listing the study-level signal screening, manipulation failures, protocol revisions and confirmation on new splits; do not write a failed gate as a null effect. The main text should include at least one sentence saying "later hypotheses were suggested by earlier exploration, and the specific confirmatory analyses were frozen before the corresponding new split was run". Without evidence of independent public registration, prefer writing "prospectively specified and frozen before the confirmatory runs", and then provide the git tags, manifests and configurations with a timeline; do not imply that the whole project was publicly preregistered before the first look at results.

Holm is a correction **within each study family**; the bootstrap intervals are per-item intervals and do not simultaneously cover all results. The p=0 in the figure book is numerical underflow; change it to p<0.001 or a representable upper bound. Formal captions should not treat p-values precise to dozens of orders of magnitude as a measure of effect strength.

### M10. Do not overstate novelty and shared state in advance

**Rationale:** "No one has measured this before" and "previous work only looked at accuracy and efficiency" are too broad. The existing references already include near neighbors on source/intention and causal audits of latent communication. Lindsey has already studied post-intervention retroactive endorsement of intention for prefilled outputs; Zhang & Emu have already distinguished message presence, message content and the value of the other agent. [Lindsey original](https://transformer-circuits.pub/2025/introspection/index.html), [Zhang & Emu original abstract](https://arxiv.org/abs/2607.26773). Our distinction needs to be stated positively, rather than lumping these works under "only looking at performance".

**Specific fix:** Narrow the contributions to three: ① measurement of self/other attribution of private content across two instances; ② characterization, in this model, of the attribution shift through connection-method, third-person and answer-time link-cut controls; ③ auditable, staged experimental materials. For entries in the literature-verification table that were checked only at the abstract level, read the corresponding original before citing specific methods/numbers in the main text. The records are currently on the SD card and GitHub is private; "all trial records are public" should be written as a release plan, and changed to the past tense only after the PI actually releases them and the link is accessible. Keep the AI-use statement, and state that the illustrations are schematic and the data figures are computed from records; do not claim an unknown image-model version.

## Suggested changes

### S1. The number spot-check passes overall, but metric names, runs and interval sources must be unified

**Method:** SD card read-only. An independent script computed differences directly from the logits in `records/attempt-*.jsonl` according to their physical meaning, first averaging over permutations within an episode and then pairing by episode; the project's M scoring function was not used to recompute the main means. The independent bootstrap used NumPy, seed=250925, 10,000 resamples. The original intervals in the report tables and JSON remain the basis for the paper; last-digit differences due to different seeds are not errors. The GPU runs were not repeated, GPU–SD consistency was not re-verified, and no full freeze audit was done.

Root path: `/Volumes/VERBATIM SD/mind-connecting-data/results/`. The raw means below come from this independent recomputation; unless noted, the interval column cites the saved analysis artifacts, which have been cross-checked against the stage reports.

| Source run / artifact | Item checked | Mean recomputed from raw records | Saved interval or criterion | Conclusion |
|---|---|---:|---|---|
| `20260924-062722_main_v1/confirmatory.json` | TWO−ONE / M | −0.073316 | 95% [−0.214, 0.065] | Consistent with the one/two decimal places in PLAN/ALL_RESULTS |
| Same as above | ONE−STATIC; ONE−LANG-tag / M | 0.180428; 0.852696 | [−0.020, 0.400]; [0.542, 1.195] | Consistent; the fact that STATIC was unmatched cannot be hidden |
| `20260924-172152_v2_main_confirm/contrasts.json` | D: K*−C0 / M; M_NOW | 55.834499; 54.709951 | M [54.989, 56.631] (about 55.0–56.6) | Consistent |
| Same as above | C: untag−tag; self−untag; stranger−tag / M_NOW | 26.634419; −19.471350; −0.019677 | about [24.5,28.8]; [−21.5,−17.4]; [−0.27,0.25] | Consistent; the reversed result cannot be omitted |
| Same as above | A_K: K*−STATIC / M | 60.287029 | about [59.3,61.3] | Consistent, but not matched-channel evidence |
| `20260924-192633_v2_main_diag_confirm/pilot_c.json` | G2 rule; code word (N=60) | 38.774985; 35.577571 | one-sided lower bound 34.321522; 32.090625 | Consistent; the endpoint must be renamed as per M2 |
| `20260924-193405_v2_bal_confirm/contrasts.json` | E: K*−C0; R−C0 / M | 52.543655; −0.051449 | [51.589,53.461]; [−0.151,0.050] | Consistent |
| `20260925-021307_v3_confirm_confirm/contrasts.json` | A′ / M | 33.432471 | [31.563,35.283] | Consistent |
| Same as above | FULL−RF / M | 54.775325 | [53.987,55.525] | Consistent |
| Same as above | RF−C0 / M_NOW | 13.342044 | confirmatory row [12.311,14.414] | Consistent |
| Same as above | 3ps−2p / M, w2; w1 | −0.714223; −3.211445 | w2 90% [−1.262,−0.184]; w1 95% [−4.860,−1.563] | Consistent; correct the statistical name as per M4 |
| `20260925-000154_v3_sig_aprime_signal/signal.json` | A′ pilot | JSON 34.758690 | 90% [30.591,38.870] | Consistent with the report; this row only checks the artifact, the pilot logits were not independently recomputed |
| `20260925-001135_v3_sig_bprime_signal/pair_signal.json` | PC; ALL START excess difference | JSON 0.001719; 0.067344 | 90% [0,0.004453]; [0.026170,0.109063] | Consistent with the report; the raw paired category proportions were independently checked, the excess bootstrap was not recomputed |
| `20260924-210346_v2_ext_dose_confirm/records/` | w2 open self-report code-word mention rate | 297/300=99% | Descriptive count | The number is consistent; the meaning the original figure gave it is too strong |

Record shard fingerprints (each run is `attempt-000.jsonl`; the first 16 characters of the SHA256 are listed, to identify the data snapshot used in this review): v1 main `bac17d9f79e4ae3a`; v2 main `9adab7a9af9aae8c`; v2 bal `8b880fe31b7d991a`; v3 confirm `10d9f85236794ef87`.

A few numerical expressions that could easily raise questions should also be cleaned up:

- The figure-book strength figure writes claiming=34.1 for w1 and ALL_RESULTS writes ΔM=32.0; these do not conflict: the figure plots **ΔL_START**, while the latter subtracts Robin. I suggest having the strength figure plot ΔM directly, or explicitly calling it the "self-item component"; do not call both quantities claiming.
- v2 K*'s 55.8 and v3 K*'s 56.6 come from different splits; mark this in the caption, and do not average them or treat them as the same result.
- The figure script's `delta()` uses 4,000 bootstrap resamples while the formal artifacts use 10,000; RF/M_NOW also have slightly different intervals in the confirmatory and descriptive rows of `contrasts.json`. For formal comparisons, take the caption values from the corresponding family row, and label the intervals of descriptive bars separately; do not try to paper over source differences through rounding.
- ALL_RESULTS T3's +56.1 [54.2,57.7] is the signal pilot's **90%** interval; add the confidence level in that row. Do not let it look synonymous with the formal 95% intervals.
- w3's CAP drop of 0.056 in the strength pilot exceeds the threshold, but the descriptive extension measured about 0.041; write "failed at the point-selection stage, still extended descriptively as planned", and do not imply that the extension sample itself also exceeded 0.05.

### S2. Keep nats, and add choice rates actually counted from the records

**Rationale:** M is the difference of the log-probability ratios of two items, then differenced across conditions; it is neither a probability nor a single binary logit, and putting the mean into a sigmoid does not give a choice rate. ACC in this project is also a log-score, not the usual accuracy; this should be stated prominently.

**Specific fix:** Use `ΔM (nats)` at first definition, and show the raw self-item and Robin-item components alongside. Compute choice rates as the proportion of four-way argmax across the permutations within each episode, then average with equal weight per episode; intervals are also resampled by episode. Clearly distinguish this from "first average the probabilities, then take one argmax per episode". The following read-only descriptive results from this review are available for later tables:

| Data and condition | START picks B | NOW picks B | ACC_RULE picks B |
|---|---:|---:|---:|
| v2 main C0 | 0% | 0% | 2.83% |
| v2 main K* | 95.75% | 93.50% | 70.08% |
| v3 C0 | 0% | 0% | 3.92% |
| v3 KV-P w1 | 52.33% | 52.50% | 19.83% |
| v3 STATIC g0.1 | 0% | 0% | 15.33% |
| v3 K* FULL | 97.08% | 94.92% | 69.25% |
| v3 K* RF | 1.33% | 17.50% | 17.25% |
| v3 strict third person w1 | 47.75% | 48.67% | 53.17% |

These are answer choices on the current readouts, not autonomous behavioral adoption rates; the table has no intervals and should not be used as the final complete results table. In particular, the comparison "access lower than attribution" involves different questions and different baselines; treat it only as a readout dissociation, not as an information-theoretic paradox.

### S3. Story order: from "the phenomenon is credible" to "which explanations still stand"

**Rationale:** The current order, phenomenon → channel → link cut → wording, basically flows, but "is it just taking the 'you' in B's prompt as itself?" is the first question that will come up. Robin, G2, E and third person together form the validity evidence, and E currently has no prominent place in the main text. Separate claims of "not noticing" and "not merging" dilute the main line.

**Specific fix:** Recommended order of main-text results: ① phenomenon and magnitude (D, choice rates, Robin decomposition, G2) → ② robustness across rehearsal materials and third person (E, T3) → ③ connection method and labels (A′, C, keeping the reversed self result) → ④ access during answering and residue (RF). End with a short paragraph on the limits of the residual and two-way pilots, pointing to the appendix. Related work can be compressed to half a page, with the closest two or three papers placed in the introduction, dropping the long neuroscience preamble.

Most likely reviewer questions and prepared answers:

| Question | Existing evidence/priority addition | What cannot yet be answered |
|---|---|---|
| Is it just a logit shift, without actually answering wrong? | The choice rates in the table above, confusion matrices and per-episode distributions | Whether free behavior changes; BEH has been discontinued |
| Is M caused only by the special Robin control? | Components, E's balanced material, v1's descriptive START-N results | The KV conditions lack a strictly symmetric confirmatory control that "asks with its own codename" |
| Is it just a misreading of grammatical person in the donor prompt? | T3 preservation and the w1 secondary difference, with the name-label confound fully reported | Independent estimates of the pure grammatical-person effect and the source-label effect |
| Is the matching really fair? | List A′'s ACC increment, choice rates, distributions and CAP together | Full information content, per-layer injection and temporal structure are not balanced |
| Is it a recall error or direct override during answering? | FULL/RF from the same C48 branch support dependence on access during answering | KV RO, mediation by reflection text, localization of internal circuits |
| Were positive results cherry-picked? | Timeline, keep/drop decisions for all pilots, per-family frozen comparisons, new splits | Within-stage multiple-comparison control cannot be described as the whole study being free of selection |
| Does it generalize to real multi-agent systems? | Precisely delimit the artificial KV interface and the single-checkpoint scope | Another model and natural tasks need new experiments; this cannot be supplied by offline analysis |

### S4. Rank supplementary analyses that need no GPU by payoff; do not roll out every exploration at once

**Rationale:** The existing samples are enough to resolve many writing questions; piling on new significance tests easily blurs the confirmatory boundary.

**Specific fix:** Do the first three first, and choose among the rest according to space; this review did only the read-only spot-checks stated above, and did not change metrics or the analysis plan on the PI's behalf.

1. **Key choice rates and confusion matrices.** Add episode intervals, split by START/NOW/WORD and Robin; put ΔM, raw M and the two L components side by side, and check whether the large effect is contributed by a few rule combinations.
2. **Matching and heterogeneity.** For A′, report the ACC distribution/correlation, the difference per rule combination and per-permutation results; for T3-w1, report the distribution of differences (SD≈20.69, mean −3.21), so that a slight average drop is not misread as a slight drop in every episode. All are exploratory; do not drop samples, change prompts or reselect points based on results.
3. **Standardizing open self-reports.** Take examples in a fixed order; to keep a claiming-rate conclusion, add semantic annotation; otherwise use only the existing string-occurrence rates. Disclose the truncation of raw text, the 80-token limit and templated phrasing together.
4. **Descriptive tracking of link-cut residue.** Count whether B's rule/code word appears in the receiver's reflection before C48, and relate it to RF's START/NOW/WORD; this is a post-treatment variable, and group-level associations cannot be used to claim causal mediation or that internal memory was rewritten.
5. **Completing the B′ appendix.** Report the excess difference and the threshold, not just category bars; examine heterogeneity of excess stratified by rule combination. Keep its status as not having passed the advancement threshold.
6. **Audit checklist.** Unify, for each figure, the run, split, materials, item type, prespecified/descriptive status, N, bootstrap settings and original JSON fields. v2 dose uses the first 300 episodes of v2_main and G2 uses the 60 formal diagnostic episodes; they cannot be packaged as two further independent replications.

### S5. Main-text figure choices: keep third person in the main text; the self-report gives way to stronger controls

**Rationale:** The four panels of Figure 3 currently span phenomenon, access, capability and "noticing", and are not four equally strong pieces of exclusionary evidence. Keeping several small panels that support the same conclusion is fine, but the last panel is weak and easily overinterpreted. Having the actual KV connection shown only in the appendix also makes the experiment hard to judge.

**Specific fixes (using PLAN's original numbering):**

| Figure | Suggestion | The one question the figure should answer |
|---|---|---|
| 1 Concept | Respect the version the PI has already chosen and shrink it into a small figure in the introduction; if pages are tight, merging it with Figure 2 is for the PI to decide | Why study self/other attribution? Brain bridging is explicitly only the motivation; the Consciousness?/Self? in the figure are not experimental measurements |
| 2 Paradigm | Keep in the main text; add a minimal KV-P interface and a FULL/RF timeline bar; explain the difference between B's fixed prompt/note cache and the live reflection stream | What exactly does the receiver read, when does it read it, and what does it answer? |
| 3 Main results | Keep self/Robin and content access, add choice rates; replace U-closed with E's replication on rehearsal material; CAP can shrink to a small table/small dot plot | Is the attribution shift reliable, and not a global collapse of answering? |
| 4 Channel | Split into the A′ pair and the language-label pair; do not lay out eight groups of bars as if they were one experiment; also show the ACC matching | Does a similar rule-access score necessarily produce the same attribution shift? |
| 5 Link cut | Keep in the main text; three metrics are fine; add explicit ΔM/ΔM_NOW/ΔACC labels, and the caption should note that the code word still shows residue | How much does continued access to the partner's cache during answering contribute? |
| 6 Wording | Keep in the main text, move it right after the main results; add a panel with the direct difference/preservation bound, and crop the cards' whitespace heavily | Does the effect still exist after removing first/second person? |

If six are kept, the suggested order is **concept → paradigm/interface → main results → wording → channel → link cut**. If the main text must be shorter, I recommend five: compress concept and paradigm into one, rather than moving the wording control out. Another low-change option is to keep Figure 1 as a small figure and combine Figure 2 with the adjacent main results; do not sacrifice font size to hit a figure count.

I broadly agree with the appendix arrangement: strength, self-report, two-way outcomes, full interface math and stage flow are all worth keeping. The one-page summary and the GPT summary need not repeat the main results as scientific appendices; they can be used for talks, but their text must likewise drop the unsupported "did not notice/no merging".

### S6. The composite-figure approach works, but actual legibility and the caption contract need fixing

**Verified strengths:** The information flow of the GPT illustrations is clear; blue A, orange B and the meanings of the two kinds of one-sided adoption are consistent. The numerical panels in the figure book are still vector graphics; Arial is embedded in `fig_main.pdf`, and no data panel was found to be rasterized as a whole. The white background and uniform lines suit a paper.

**Rationale and specific fixes:**

- **The channel figure does not achieve one-to-one alignment.** Page 7 of the figure book has four equal-width channel cards on top and eight equal-width groups of bars below, with group widths of 1/1/2/4. The lower "internal state of B" also includes STATIC, but STATIC is actually the rule-conditional mean direction. Give schematic cards and data blocks the same width per channel family, or link them with clear panel labels; keep the text labels, and do not make readers guess from position alone.
- **Too much whitespace in the wording figure.** On page 9 the whitespace above and below the two cards takes up a lot of height, while the data panel shrinks. Use LaTeX display clipping to remove the white margins, and make the exact excerpts, ellipses and the "illustrative excerpt" note editable vector text; keep the original PNG. The prompt excerpts are not verbatim experimental templates and must not look like evidence of raw model output.
- **Add direct comparisons.** In the wording figure, the error bars of the two arm−C0 groups are not error bars of the 3ps−2p difference; in the link-cut figure, the three groups of bars do not directly show the interval of FULL−RF. Add difference points with intervals/preservation bounds alongside, so that readers do not have to judge the test by eyeballing overlap.
- **Use fewer similar warm colors to distinguish metrics.** M's vermilion and M_NOW's orange-yellow can stay, but add hollow/filled markers, textures or facets, so they are distinguishable in grayscale print too. Explain the entity colors for A/B/Robin and the metric colors separately; the original Figure 1's cyan/purple is not fully consistent with the later blue/orange, so one cannot claim the whole paper is already fully unified.
- **Add other to the paired stacks.** Independent check of B′ ALL/FULL: keep 53.75%, A adopts 17.5%, B adopts 25.625%, swap 1.875%, leaving **1.25% other**. The current figure draws only five categories with both_third=0, and the bars do not reach 100%. Draw other explicitly; do not fold it back into one-wins or hide it; the main comparison still follows the frozen definition.
- **Explain error bars panel by panel.** In the main results, a is a two-sided interval, b is a one-sided lower bound, and c/d currently have no intervals drawn; do not write generically "all error bars are 95% CIs". B′ intervals are 90% and must not be mixed with the confirmatory figures.
- **Add the continuing connection to Figure 2.** The current schematic easily suggests that reading happens only during reflection. FULL still reads B while processing and answering the question; the main K* reads only the fixed prefill, with no feedback between the two sides. "Weights act on keys" in the caption should be made precise as adding log w to the partner's attention scores, not multiplying the key vectors by w.
- **Use the data-only panels.** Embed `fig_*_data.pdf` directly in the main-text layout; the existing `imagegen_panels.tex` still uses fixed bp crops of the old combined PDFs. Later authors should switch to the ready-made data panels to avoid cropping off labels. Check 100% print at the actual template width; at the current 5.5 in, some legends are only about 5.6–6.2 pt, which would be too small if shrunk to a single column of a two-column layout.

### S7. Nine pages is doable, but the current page budget does not leave enough margin for actual figure heights

**Rationale:** The PLAN sections sum to about 7.95 pages. If that is pure text, adding six figures and long captions will clearly exceed 9 pages; if figures are already included, the current composite heights of the channel and wording figures are hard to fit into 0.75/0.6 pages respectively with adequate explanation. Being easy to read when the figure book is enlarged does not mean being easy to read at the paper's actual font size.

**Specific fix:** First do a target-template layout without full prose. A 9-page version can be budgeted by the following **total page counts including figures and captions**: title/abstract/introduction 1.25; methods and interface 1.75; main effect and validity 1.5; wording 0.75; channel 1.0; link cut 0.75; related work 0.5; discussion/limitations/conclusion 1.0; slack 0.5. Self-report and B′ each get only one sentence in the main text pointing to the appendix. Handle the placement of the AI/reproducibility/impact statements according to that year's venue template; do not assume that none of them count toward the page limit.

## Open for discussion

### D1. Venue: I lean toward COLM; TMLR is an equally serious first-choice path

The following are **current/2026 official rules verifiable as of 2026-09-25**, not commitments for 2027. This review found no verifiable ICML/COLM/NeurIPS 2027 CFP, so no speculative deadlines are given; verify again before submission.

| Option | Official rule reference | Judgment and suggestion for this manuscript |
|---|---|---|
| ICML 2027 | 2026 initial submission main text **8 pages**, 1 extra page allowed after acceptance; references, impact statement and appendix not counted. [CFP](https://icml.cc/Conferences/2026/CallForPapers) | Worth considering, but the initial submission cannot be prepared at 9 pages. If the second model and the key attribution controls are completed fairly early and can show significance to a broader ML audience, it is worth submitting; the large nat effects and the brain-bridging motivation alone are not enough |
| COLM 2027 | 2026 main text **9 pages**; topics explicitly include the science of LMs, interpretability, multi-agent systems and cognitive perspectives. [CFP](https://colm.cc/Conferences/2026/CallForPapers) | **My first-choice conference.** Better suited to telling the story of a controlled behavioral study of source attribution in language models. Single-model generalization still needs to be narrowed and the third-person and matching limitations kept, rather than relying on exaggerated wording to attract attention |
| NeurIPS 2027 | 2026 main paper **9 pages**, including figures and tables; references/appendix/checklist not counted. [Main Track Handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook) | If by then there is cross-model evidence or evidence on more natural tasks, it can strengthen broad significance. Delaying the existing arXiv release just to wait for this venue is not recommended, and do not mistake the brain figure for a sufficient link to a neuroscience track |
| TMLR | Rolling year-round; no hard main-text page limit, but length must be commensurate with content. [Author guide](https://jmlr.org/tmlr/author-guide.html), [FAQ](https://jmlr.org/tmlr/faq.html) | **If you want to fully document the three stages and are willing to revise during review, it can be the first choice outright.** Its explicit criteria emphasize whether the evidence supports the claims and whether the results are worth readers knowing about; it does not exempt the work from challenges on validity and generalization. [Acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html) |

My suggestion is to keep the already-decided route of a single-model arXiv first version, and first get the claims and evidence aligned; for a conference lean toward COLM, and if completeness and rolling revision matter more, choose TMLR. A second model improves external validity but cannot replace correcting the interpretation of the current measurements. When the time comes, choose one formal review venue based on how complete the work is, and do not send the same manuscript for parallel review; TMLR also forbids the same results being under review at another archival venue at the same time. [TMLR editorial policies](https://jmlr.org/tmlr/editorial-policies.html)

### D2. Terminology and title: keep an accessible question, and use attribution as the technical head term

**Rationale:** claiming is short and suits being an operational shorthand once clearly defined, but used bare it is easily understood as intentional appropriation. source misattribution is closer to what is measured; however, what we mainly ask is "what were you assigned", not directly "whom did this information come from", so the main text needs to explain this operationalization. Changes in NOW may also be adoption, and should not all be called misremembering.

**Specific fixes:**

- `claiming` is first defined as "the shift in reports attributing partner content to one's own assignment, relative to the Robin control"; for result axes prefer `Self-attribution shift ΔM`. Drop appropriation, merging/unification and mind transfer.
- `memory` is first defined precisely as "the KV cache formed by prefill tokens such as the private prompt and note", without implying long-term memory or human episodic memory; `decodability` is written as "content access measured through specified questions", since no decoding probe was trained.
- Of the three candidates I rank them **3 > 1 > 2**. 3 has a natural question and a restrained technical subtitle; 1 is catchy, but "Language Models … claim it as their own" overgeneralizes given a single checkpoint and the strength conditions; 2's "makes" and repeated "models" are stiff, and it can easily sound deterministic.
- Revised titles for the PI to choose from: **Mine or Yours? Self–Other Attribution under Cross-Instance KV-Cache Access**. If you want to state the result more directly: **Whose Memory Is It? Source Misattribution under Cross-Instance KV-Cache Access**. The title need not list the model name, but the first paragraph of the abstract must make clear that only Qwen3-4B-Instruct-2507 was tested.

### D3. Whether to add more GPU controls: prepare them for submission, but do not let them block writing now

**Rationale:** The most valuable new research is not enlarging N on the same template again, but separating the explanations that are still entangled. All of the following require a PI decision, new splits and a new protocol, and cannot be launched directly as part of this review.

**Recommended priority order:**

1. If what matters most is whether functional source attribution holds: prioritize a control under KV conditions that asks with **symmetric codenames** for A/B/Robin, distinguishing "original assignment" from "currently adopted", to test whether the "you" question form is special.
2. If what matters most is the answer-time mechanism: run a KV C-only / R-only / FULL / C0 factorial control; if needed, further separate the reflection text from cache residue. This distinguishes pathways better than a blanket "cutting the link restores it".
3. The already-approved replication on a model from another developer: follow the frozen primary endpoints and selection discipline, adapt chat/labels and redo the baseline and strength thresholds; there is no need to replay every failed pilot of v1–v3.
4. If what matters most is practical multi-agent applications: then consider source-label/channel-isolation experiments on natural tasks with real cache-sharing implementations. The current results can only propose these mitigation ideas; their effectiveness has not been validated.

Brain bridging can remain as the original motivation, but the paper's persuasiveness should rest on recomputable attribution behavior and intervention controls. All of the above suggestions can be decided after a first version that accurately presents the existing results.
