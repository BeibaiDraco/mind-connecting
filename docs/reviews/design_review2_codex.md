# Experiment design v0.2 re-review

Review date: 2026-09-23 (America/Chicago). The main file under review has 350 lines, SHA256: `eec95266908228da96951ebc32415b33867968acd5fdccc299ccc641a4529962`. I read v0.2 in full and checked the previous round's 24 comments, the opening of the synthesis draft and its §1.1 correction, decision_log, and AGENTS. This round adds only this file; the tokenizer check used a temporary directory, and I did not download weights, run the model, or write project implementation code.

## 1. Overall verdict: not ready to go straight into full implementation as written

**Two blockers remain: the scoring ground truth for G2 is incomplete, and the prefill mailbox initialization contradicts the hook contract.** Both are local protocol patches and do not involve re-choosing the research question. Once they are filled in, implementation can begin; the other issues should be settled when each module is implemented or before the formal pilot, without another full audit.

I accept all of the decisions the PI has already made: FULL as primary, RF as key secondary, comparing the three groups as whole treatments, N≤600, no training and no model change if G2 fails, and the first-person framing check deferred.

Main conclusions from the tokenizer measurements: **the paired lengths of the regular measurement questions pass; the P prefix is not constant; plan names are all single tokens only in their actual usage positions, with a leading space; the CAP question pool does not yet exist and cannot be accepted.**

Below, "resolved" always means settled at the design level; it does not mean that the not-yet-written runtime or the model's behavior has passed testing.

## 2. Point-by-point check of the previous round's comments

| Original ID | Status | Location in v0.2 | What was done / what is still missing |
|---|---|---|---|
| B1 SMI cannot automatically subtract bias | Resolved | §0, §4, §8 | Changed to per-permutation log-ratio followed by averaging; history-restricted balancing; no longer claims to rule out all steering. For handling of extreme values, see I1 of this round |
| B2 DEV is not the same as no subject | Resolved | §1, §6, §13 | The STATIC definition and claims have been narrowed; deferring the framing check matches the decision already made |
| B3 LANG is not a pure directness manipulation | Resolved | §1, §4, §7, §13 | Accepts the whole-treatment comparison and keeps untag; the timing of the newly added early disclosure must be written explicitly into the interpretation, see I3 |
| B4 Online measurement changes the state | Resolved | §5, §7, §13 | FULL as primary and RF/RO as auxiliary is settled, and RF is no longer called recovery; the specific timing issue is merged into B6 |
| B5 Content-specific transfer not demonstrated | Partially resolved | §7, §8, §10 | Mismatch and content counterfactuals have been added, but the mismatch word is often not in the candidate set, and G2 still uses absolute ACC>0; see B1 of this round |
| B6 Clock/branch contract | Partially resolved | §5, §11 | Consumed token, pending token, and independent KV clones are spelled out; prefill disables the hook yet requires its output as the seed, and the first EOS mask is also underspecified; see B2 |
| B7 Primary estimand not frozen | Partially resolved | §4, §8–10 | A, FULL, M, and the three-item Holm are clear; option serialization, the CAP question pool, and the pilot selector are not yet complete |
| I1 ONE/TWO total effect and direction | Resolved | §1, §9, §13 | Same g, two-sided, total effect of the return path: all correct; the STATIC matching rule still needs to be made concrete, see I2 of this round |
| I2 Elimination and chance baseline | Partially resolved | §3.2, §4, §8, §10 | "Different from you" removed, conflict task noted; but absolute ACC>0 is still not evidence of transfer relative to no bridge |
| I3 C0 selection bias | Resolved | §9 | The full set of generated eligible samples is primary; the C0-eligible subset is only a sensitivity analysis |
| I4 Behavioral agreement / word errors overinterpreted | Resolved | §1, §7–8 | Changed to descriptive readouts, added fixed-A donor counterfactuals, removed strong identity/control language |
| I5 Material and label shortcuts | Partially resolved | §3–4, §11 | Word pool, ranges, and rotation are given; the actual length of P does not match the claim, and "perfect balance" does not hold for arbitrary N; see I5, M1 |
| I6 Residual position and normalization | Partially resolved | §6 | Cross-boundary position, scalar σ, FP32/BF16, ε are clear; the clipping activation threshold and handling of near-zero STATIC directions are undefined, see I2 |
| I7 Reversibility/g50 overinterpreted | Resolved | §0, §9 | Recovery/phase-transition claims removed, nonparametric curve is the default; g50 is kept as an exploratory item that need not be fitted |
| I8 Power and clustering | Partially resolved | §9 | Now uses the SD of paired D, episode bootstrap, and Holm; the meaning of 0.5 nat and the power after N is capped must be added, see I1 |
| I9 Pilot compute | Partially resolved | §10, §12 | Staged, with profiling first; the Pilot B grid is not given, so the actual number of conditions/compute still cannot be recomputed |
| I10 Capability, format, and classification | Partially resolved | §8–10 | Multi-label descriptions and not filtering samples by treatment outcome are fixed; the CAP pool and capability/format tolerances are missing |
| I11 Exploratory/confirmatory boundary | Partially resolved | §9–10 | Three primary and nine secondary items and an independent Pilot C are clear; the test family for RF/RO and the retest rule after failure need one more sentence, see M2, I2 |
| I12 Literature and null-result wording | Resolved | §1, §9; synthesis draft update and §1.1 | The Bicameral and Paladino corrections are in place, and v0.2 no longer uses non-significance to prove that everything is explained by bias. For the historical passages of the old synthesis draft, the update note and v0.2 take precedence |
| M1 Insufficient logging | Partially resolved | §6; AGENTS interface | Tick logs are much improved; result rows still need permutation ID, actual question length, all label logprobs, status/failure reason, and the full config hash |
| M2 Numerical consistency criteria | Partially resolved | §11.1 | Teacher forcing and free generation are now distinguished; there are no actual tolerances yet, and an independent test criterion must be fixed in S0' |
| M3 OBS/LAT interpretation | Resolved | §7 | Deferred; the current implementation does not need to carry this mechanistic conclusion; role/history reconstruction will be accepted when it is enabled |
| M4 STATIC smoke test | Resolved | §11.12 | Now clearly a manipulation check; the appearance of the expected behavior is not a necessary condition for engineering correctness |
| M5 Version/scope conflict | Resolved | §2, §10, §13; new AGENTS note | SHA-list freezing is now allowed, and v0.2 is clearly authoritative. The old 0.6B sentence at the end of AGENTS should not be followed; the owner can clean it up later |

The literature corrections match the previous round's check; this round did not extend the literature search: [Bicameral original Table 1](https://arxiv.org/html/2605.11167v1).

## 3. New issues in v0.2 and implementation contracts still to be filled in

### Blocker B1: MISMATCH cannot be fully scored with the current candidate set; the G2 primary test should switch to the content counterfactual

Corresponds to §6–8, §10. Besides the rule, another episode's B′ also brings a different scenario, code name, and Robin information. In particular, B′'s secret word is usually not among the receiver's four existing words: if the word is drawn independently from the 30 words, the probability that it is absent is **26/30≈86.7%**. In that case, requiring "the four-choice readout to follow the actual B′" leaves no scorable correct option. B′'s rule may also happen to equal the nominal B, own, or Robin, so it cannot be called a valid mismatch without distinguishing these cases.

**Concrete fix:**

1. Move the paired counterfactual in §7 ("fix A, Robin, the scenario, and the code name, and only swap B's rule/word for the original unused/foil") into **the independent Pilot C as the G2 primary content test**; do not wait to run it as the 60-case diagnostic after the formal experiment.
2. **Fix A's input and R's actual token sequence, including candidate order.** Change only the donor's assigned values and B's private state. Candidates must not be reordered to follow the new `partner/unused` meanings; otherwise more than B is being changed.
3. Using the original content r₀ and the replacement content r₁, define a fixed-direction score `Q = log P(r₁) − log P(r₀)` and test `C_content = Q[donor=r₁] − Q[donor=r₀]`; likewise for the secret word. A positive change in this score directly tests whether the readout follows the actual donor content. One can prespecify a one-sided 95% episode-bootstrap lower bound >0 for the mean of the rule counterfactual as the content gate; the word gate is listed separately, and if it fails, WORD's negative result is not interpreted as boundary preservation.
4. In G2, delete the standalone "ACC significantly >0": a raw log-ratio>0 may already exist in C0. Use the counterfactual above instead, and also report the change in access relative to C0.
5. Keep MISMATCH as a "stress control with a natural distribution but mismatched scenario/source", no longer a primary threshold that G2 must fully pass. If the actual B′ word is still to be scored, it must be constrained in advance to fall within the fixed candidate set, and that version listed separately; do not add a fifth option on the fly.

This keeps the chosen research question; the patch mainly makes explicit three distinct fields: the donor change, the physical candidates, and the ground-truth mapping. About a few hours of protocol/task-logic cleanup; Pilot C adds paired donor branches.

### Blocker B2: the written contracts for the prefill seed and the hook conflict

Corresponds to §5. It currently specifies both "the hook is not active during prefill" and "the mailbox seed is taken from the block-ℓ output at the last prefill position". If the former is implemented literally, the latter cannot be obtained; if the existing hook is simply turned on, its `[rows,1,2560]` assertion does not apply to the full prefix.

**Fill it in with the following timing, which admits only one implementation:**

- Prefill disables **writes** but allows read-only capture of the output at the last valid position of the selected block; build `mailbox_old=m(prefill_last)` with the fixed normalization. The prefill capture and the single-token hook use different shape assertions.
- After prefill, first mask the two EOS tokens on a copy of the logits, then select `C₁` to be consumed; the raw logits are kept. The first C tick consumes C₁ and injects the donor's **prefill seed**. At the end, it commits C₁'s message for use in tick 2.
- After T=48, the KV/history contains C₁…C₄₈; C₄₉ is the pending token not yet consumed. R tick 1: the receiver discards C₄₉ and consumes `im_end`; the donor consumes its own C₄₉; both use the mailbox committed after C₄₈.
- **In FULL/TWO, the new messages the receiver produces while reading the question keep being passed to the donor.** This does not change the mapping, and reading the question is also part of the treatment. RF already makes clear that the donor stops computing: keep its state from advancing and do not update its mailbox; this is not an open question.
- A snapshot clones **the entire paired state**: both sides' KV, attention mask/valid positions, pending token, raw logits, committed mailbox, token history, and logical tick/phase/done flag; `mailbox_new` is a per-tick temporary buffer and can be created fresh after restore. The condition mapping and gain are saved or rebuilt from the immutable config. Each measurement branch independently clones both sides at once; it must not clone only the receiver.
- If the P note ends because of the 48-token cap, the assistant turn must still be closed once with the official template; if EOS was sampled, strip the terminator from the content and then wrap uniformly, to avoid double termination. The EOS mask used for generation should not contaminate the raw logits used for scoring.

Also change "the first token is identical across all conditions" to "identical across **conditions with the same prefix**"; LANG has added text, so it cannot be promised that its first token matches C0's. The patches above take about 1–2 hours and do not change the chosen cross-boundary bridge.

### Important I1: stable computation of M, heavy-tail sensitivity, and power at 0.5 nat

Corresponds to §8–9; answers focus points a/f.

**Do not arbitrarily add a probability floor to the primary metric.** The log of P=1e−8 is about −18.42; this is not a numerical singularity, nor does it mean the sample distribution must be heavy-tailed. For finite logits, `log P(a)−log P(b)=z_a−z_b`; FP32 `log_softmax` or directly subtracting logits computes this stably. Do not first convert probabilities to low precision, let them underflow, and then take the log; record NaN/Inf as technical failures and do not hide them with a floor.

The order in v0.2 is already correct: **for each permutation, compute L and M first, then average M; after that, form the condition-paired D.** Averaging probabilities before taking the log introduces a Jensen gap and also stops the equal logit bias from cancelling as intended. Adding a floor/truncation to the raw P likewise destroys normalization invariance and this cancellation property.

Keep the chosen paired t + Holm, but add the following in advance:

- Report the SD, quantiles, and maximum absolute value of D, and the range of leave-one-episode-out means; keep all valid values and do not drop samples for having large effects.
- Prespecify the episode-bootstrap interval of the **20% trimmed mean of paired D** as a robustness analysis, reported alongside the untrimmed mean. It estimates a different center and cannot replace the primary test on the original mean, nor can the primary result be switched to it because it is more significant. An ordinary bootstrap does not by itself solve sensitivity to extreme values.
- Report the raw four-label probabilities/probability of the correct option, label mass, and probability-scale differences as descriptive results, so that large nat effects remain interpretable. Do not deliver only a single log-ratio plot.

δ=0.5 nat can be kept as a **planning convention**, but it is not a universal minimal important effect supported by existing evidence. `exp(0.5)=1.65` refers to the **ratio of ratios** corresponding to the multiple log-ratio contrast here (after exponentiating the cross-episode mean, it is on a geometric-mean scale); it is not a 65% increase in accuracy, nor a uniform change in probability percentage points.

Using the rounded constants in the text, `(2.394+0.842)`:

| SD of paired D (nat) | N needed for approximate 80% power | Actual N under the current rule |
|---:|---:|---:|
| 2 | 168 | 300 |
| 3 | 377 | 377 |
| 4 | 671 | 600 |
| 5 | 1,048 | 600 |
| 10 | 4,189 | 600 |

**Once SD exceeds about 3.785, N hits the 600 cap and 80% power cannot be guaranteed.** At N=600, the approximate minimum detectable effect is `0.1321×SD` nat. Whether the cap is hit can only be measured by the pilot, not guessed from small probabilities alone; the variance estimate from a 40-case pilot will also be unstable. Keep the N cap, report the actual detectable range after capping, and no longer promise fixed power. The cost is mainly analysis logic, with no new model inference.

### Important I2: the pilot still cannot be run mechanically, and not all tolerances have numerical values

Corresponds to §6, §10–11; answers focus point g. Missing: how Pilot A aggregates across the four g values to choose the layer; how ACC-rule/word are combined; CAP/format tolerances; the specific gain set for Pilot B; the ranking and tie-break for g*; which ACC g_s* matches and with what error; how the 6 gains and the other two STATIC points are chosen; the clipping activation threshold; how Pilot C failure is handled.

This mainly blocks automatic running and freezing of the pilot; it does not block first writing the utility functions that take these parameters. I suggest adding a deterministic selector to the implementation config, for example:

- Use **the increase in ACC-rule relative to C0** as the sole ranking score for choosing the layer/g; report ACC-word separately, to avoid forcing STATIC to match a private word it does not carry.
- Initial engineering thresholds for candidate eligibility could be: mean CAP accuracy drop ≤0.05, mean four-label mass ≥0.90, and drop relative to C0 ≤0.05. State that these are pilot point-estimate screens, not proof of capability equivalence; formal results still report intervals.
- Pilot A: first take the highest score among eligible g within each layer, then choose the layer; on exact ties, take the smaller g, then the shallower layer. Pilot B first gives a fixed grid; choosing g* can be specified as: among candidates meeting both the ONE and TWO thresholds, the one with the highest ONE access increase, with ties going to the smaller g. No need to look at M.
- g_s*: among eligible STATIC candidates, minimize the difference in ACC-rule mean from ONE(g*), with ties going to the smaller gain. If matching on log-ratio, one could first agree on an absolute difference ≤0.25 nat as the engineering tolerance; this number is a suggestion, not a measured equivalence bound. When there is no eligible match point, there must be a predetermined exit/mismatch-flagging rule; re-picking on the formal sample is not allowed.
- Make explicit that the 6 points are a prelisted fixed grid, or give the complete algorithm for choosing from the candidate grid; do not just write "determined by the pilot". The other two STATIC points can be predetermined as the neighboring candidates of the match point.
- The simplest normalization scheme is to fix clipping either on or off; if adaptive selection is kept, first define k, the threshold, and zero-variance handling for "energy share of the top k dimensions". When the STATIC difference vector is near zero, mark it unusable; do not divide by zero or amplify noise.
- Pilot C only rechecks the frozen candidate and no longer tunes g along with new results. Failure is handled along the established G2 path; if a new pilot is opened, record the protocol version.

The specific thresholds above can be adopted or replaced by the owner, but must be written into the config before the corresponding results come out. Floating-point tolerances for numerical computation can be calibrated on the independent tests in S0' and then locked before the experiment runs; do not confuse them with the CAP/access tolerances for research effects. About half a day of config and process completion.

### Important I3: LANG is now "receiving the complete baseline reflection in advance", not a synchronous text bridge

Corresponds to §4, §7; answers focus point c. B's C0 reflection is first handed to A in full, and only then does A start C; in ONE, injection happens gradually during A's reflection, and in FULL the donor keeps generating during R. The temporal range of the content, the order of events, and the amount of text that can be accessed repeatedly all differ.

**No need to reopen the channel choice.** Since the decision is to compare whole treatments, keep the implementation, but state clearly in the condition names/paper methods: "advance disclosure of the C0 reflection text vs online internal bridge". It must not be interpreted as a pure channel effect with the same content at the same time. B_reflection is fixed as the same episode's C0 **consumed C₁…C_T**, excluding the pending C₄₉; tag/untag share exactly the same content. Truncate by the original token IDs and then decode; do not equate "48 generated tokens" with "necessarily 48 input tokens after being re-encoded with quotation marks".

"Mention once" also does not guarantee that the word actually appears within the first T tokens. Save the actual disclosed text, its length, and whether the rule/word occurs. The cost is extra fields and wording, with no new model conditions.

### Important I4: WORD/WORD-R is still a difference readout, not a self-test matched for amount of rehearsal

Corresponds to §4, §8; answers focus point d. A is asked to rehearse its own word, while Robin gets no equivalent rehearsal; the bridge may also change the actual number of rehearsals. The log ratio can cancel a specific equal logit bias, but cannot cancel differences in exposure, retrieval, and reference relations.

I suggest keeping WORD as a secondary "source-question difference", with explicit limitations; report the actual occurrence counts of own/partner/Robin words within C/R, and ACC-word. Do not filter samples post hoc by occurrence count. If a strict self-specific WORD mechanism is claimed later, add a symmetric rehearsal control on the key subset; this paper need not add a whole subject-framing experiment for a secondary endpoint. About a few hours of logging/analysis additions.

### Important I5: template acceptance and batching assumptions must distinguish "known and fixed" from "not yet defined"

Corresponds to §3–5, §11. Measurement found that `fastest delivery` inside the quotation marks in P takes one extra token, see §4; this does not automatically break the paired treatment comparison, but the guarantee that "P has constant length" is wrong. Removing the quotation marks around the rule is a small fix already measured to work; do not fake equal length by appending arbitrary padding.

R has not yet been given a label separator or the full S2 format; for this test I explicitly adopted one fixed format, and the formal implementation must write it into the protocol. The 40 complete CAP questions, options, and correct answers have not been provided, so one cannot claim "same question type, therefore equal length". CAP can be bucketed by **the same item ID / actual suffix length**, or the clock can be stopped for the whole pair; there is no need to force 40 semantically different questions into the same length.

Plan names should be described as "single-token in `Plan {name}` and `1. {name}`", not as all bare strings being single tokens. About a few hours of template cleanup; compiling the CAP pool is counted separately.

### Minor M1: arbitrary N is incompatible with strict balancing requirements

§9 may give N=377, while §3–4 require half for each of the two block orders, balance across the 24 rule triples, and exactly equal occurrence counts for the four labels. 377 cannot do this; Pilot A's 16 cases also cannot cover all 24 triples.

Specify that when it does not divide evenly, counts may differ by at most 1, with the remainder assigned randomly and a balance report saved; or round the formal N up to a multiple of 4 to guarantee label balance under the two-permutation scheme, still not exceeding 600. Do not reject a valid sample because it cannot divide exactly, and do not misdescribe independent marginal balance as perfect balance across all joint cells.

### Minor M2: RF/RO and technical-failure records still lack a statistical specification

§9 specifies Holm for the nine secondary metrics, but for RF/RO it only says "the primary metric under", without listing the actual contrasts and the test family. Minimal fix: RF/RO are prespecified key secondary descriptions, reporting the corresponding paired effects and intervals, without additional significance claims; if p-values are to be given, first list all the comparisons and the correction family. Keep records of numerical failures/run failures and rerun with the same config; if the retry still fails, report it as missing; do not change NaN to 0 or hide it inside "all episodes".

### Minor M3: the privacy test must still be restricted to input materials, not model-generated output

The "no partner binding appears" in P/C in §11.10 should refer to **the external materials provided to the receiver in advance**, not to text the model itself generates after bridging. Otherwise, a successful transfer that leads A to repeat B's information would be wrongly judged a data leak. Check the data flow and source fields; do not just scan generated text for words.

## 4. Tokenizer measurement results

### 4.1 Method and scope

- Reused the official tokenizer.json and chat template in `/tmp/mb-tokenizer-audit-EVn1B1/`; no new model files were downloaded.
- seed=`20260924`, **240 random episodes, 480 receiver instances**; each episode generates two diagnostic scenarios, S1/S2, with 8 non-repeating plan names; number ranges, a unique optimum, and the winning margin were all checked. Each of the 24 ordered rule triples appears 10 times, and each of the two information-block orders 120 times; the marginal frequencies of words and code names are balanced across roles.
- Each instance was tested under the two specified cyclic permutations, rendering **11,520 complete four-choice question chats**, plus 480 U-open. Numeric label boundaries were checked 46,080 times; in every case the prefix stayed unchanged and a single label token was appended.
- The P system/user templates were extracted directly from v0.2. The R option format was not given; this time I assumed `Question stem\n1. Option\n2. Option\n3. Option\n4. Option\nAnswer with the number only.`; S2 uses four `Plan ...` lines. **The full R lengths below are conditional on this format; I do not pretend that the formal serialization, which was not provided, has been accepted.**
- No model was run, so the note uses fixed test text and C uses a synthetic 48-token text fixture; the full chat rendering checks boundaries and lengths, not actual generated content. The P length results do not depend on the note at all. The lengths and rehearsal behavior of real notes/LANG reflections still cannot be verified in this round.

### 4.2 Length and pairing per question type

The R tick counts include §5's closing of C, the user message, and the assistant generation prefix; each type is constant across all tested instances/permutations.

| Question type | User content tokens | R suffix ticks | Pairing check |
|---|---:|---:|---|
| BEH / BEH-R | 140 / 140 | 150 / 150 | All 960 pairs equal length |
| NOW / NOW-R | 37 / 37 | 47 / 47 | All 960 pairs equal length |
| START / START-R / START-N | 39 / 39 / 39 | 49 / 49 / 49 | 960 pairs equal length for each of the two comparisons; all code names pass |
| WORD / WORD-R | 29 / 29 | 39 / 39 | All 960 pairs equal length |
| ACC-rule | 35 | 45 | Constant |
| ACC-word | 32 | 42 | Constant |
| U-closed | 37 | 47 | Constant |
| U-open | 14 | 24 | Constant across 480 instances; the open-generation question does not get the "answer with a number" ending |
| CAP×2 | Cannot be accepted | Cannot be accepted | The 40-question pool has not been provided |

Here "paired equal" means equal token **counts**, not identical token IDs for "you" and "Robin". The length of the whole chat is not constant: even with same-length note/C fixtures, it is affected by P's 1-token difference, e.g. the full START chat is 426/427 tokens; real model notes will also add normal length variation. What §5 needs to fix is the number of R advance steps and correct position IDs; do not conflate these two requirements.

### 4.3 Words, names, and numbers

| Check | Measured result |
|---|---|
| Secret word pool, 30 words | All single tokens, both in bare form and with one leading space |
| 8 code names | All single tokens, both in bare form and with a space |
| 15 plan names | All single tokens with a space; **in bare form only Oak is 1 token, Birch/Laurel are 3 each, and the other 12 are 2 each** |
| Fixed-width numbers and table rows | All 240×2×4=1,920 generated plan rows are 25 tokens |
| Per-attribute number enumeration | Holding the other attributes fixed, iterating price 20–89, days 2–9, on-time rate 70–99, emissions 1.0–9.9, crossed with the 15 plan names: 2,970 rows in total, all 25 tokens |
| Rule option list | With a leading space, all four rules are 2 tokens; list rotation does not change length |
| Rule inside quotation marks | `fastest delivery` is `[9349,477,9691]`, 3 tokens; the other three rules are 2 tokens each |

### 4.4 A concrete example of the P prefix failure and a verified fix

P means system+user+assistant generation header, excluding the note: **277 tokens / 278 tokens for 240 receiver instances each**. Whenever own's or Robin's rule is `fastest delivery`, there is 1 extra token; since the three parties' rules are all different, it never occurs twice at once.

For example, episode 0: A=Atlas, rule lowest cost; B=Omega, rule fastest delivery; Robin=lowest emissions. A's P is 277, B's is 278. It is not caused by code names, words, or numbers.

In a temporary test, changing both occurrences of `priority "{rule}"` to `priority {rule}` made the P prefix **273 tokens** for all 480 instances. This is only a verified suggested change; the original template and files were not modified.

Review evidence: [check script](/tmp/mb-review2-yOWEGt/check_templates.py), [summary results](/tmp/mb-review2-yOWEGt/tokenizer_results.json), [240 episodes](/tmp/mb-review2-yOWEGt/episodes.json), [rendered examples](/tmp/mb-review2-yOWEGt/sample_chats.json). These are temporary audit materials, not project implementation or model output.

## 5. Implementation plan

**The formal implementation plan for the four modules is not listed for now.** Per the instructions for this round, this step is entered only if there are no blocking issues; currently B1 would leave G2 scoring without ground truth, and B2 would allow two incompatible runtime implementations.

Once the owner writes the local contracts for B1/B2 back into the design and then fixes the R serialization and the CAP length-bucketing strategy, the implementation of `src/mb/tasks.py`, `src/mb/readouts.py`, `src/mb/analyze.py`, and `tests/test_tasks.py` can be scheduled. The pilot numerical thresholds can be a config acceptance item that must be filled in next, without re-discussing the research direction already decided in section 13. This round did not modify these modules or any existing project files.
