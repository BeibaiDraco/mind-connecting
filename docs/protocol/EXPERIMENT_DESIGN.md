# Experiment design v0.5.2 (finalized before implementation + implementation-phase revisions + G1 decision)

Date: 2026-09-23. Status: **finalized before implementation**. This version has been revised after three rounds of Codex review: [design_audit_codex.md](../reviews/design_audit_codex.md), [design_review2_codex.md](../reviews/design_review2_codex.md), [design_review3_codex.md](../reviews/design_review3_codex.md). The conclusion of the third round was "ready for implementation". The only local blocker (the interpolation fallback) has been moved out of v1 and listed as a v2 candidate (Section 14). The PI's decisions are in Section 13 and have all been followed. After the staged pilots, this is frozen as `protocol_v1`. For the research motivation see [research_synthesis_2026-09-23.md](../background/research_synthesis_2026-09-23.md), for a project overview see [README.md](../../README.md), and for current progress see [STATUS.md](../../STATUS.md).

## 0. Version history

**v0.5.2** (2026-09-24, after the formal G1 and before any pilot data; PI decision):
- **G1 result** (60 episodes, C0): START, START-R, START-N, NOW, NOW-R, WORD, WORD-R are all at 100% on both the A and B sides, with total label probability about 1.00; BEH 0.66 and BEH-R 0.38, below 0.90.
- **BEH endpoint stopped** (per the G1 rule in Section 10, with no prompt revision): M_BEH is no longer a secondary endpoint; subsequent readout questions exclude BEH/BEH-R; the G1 threshold includes only START, NOW, WORD and their Robin questions.
- **CAP question bank keeps only general-knowledge questions**: the 20 two-digit addition/subtraction questions are near chance (0.354) under single-token answering and cannot detect a capability drop; the general-knowledge baseline is 0.988. When G1 was re-run on the final materials, another 2 general-knowledge questions had baseline accuracy below 0.9 (boiling point of water 0.71, wrong under only one option order; blue plus yellow 0.50, often answered as orange); these were removed as well, fixing the bank at **18 questions**. Screening is based only on C0 baseline accuracy.
- **STATIC manipulation check switched to NOW** (previously BEH; see Section 11, item 15): check whether, after injection, "the priority currently in use" moves toward rule r. It remains only a descriptive check, not a gate.
- No model change; a larger model is left for replication after the main line is complete.
- The v0.5.1 answer-line change has been ratified by the PI after the fact.

**v0.5.1** (2026-09-23, after the G1 smoke run and the M2 code review, before any gate or pilot data):
- **Answer line changed to `Answer with the option number only.`** In the smoke run, the model answered arithmetic CAP questions with the first digit of the numeric answer (CAP1 accuracy 0.25), showing that "the number" was read as "the numeric answer".
- **Numeric CAP options now written as English words** (e.g. seventy-one, minus ten), so the answer text cannot be confused with the digit labels. The question-bank hash changed accordingly.
- For all digit-answer questions, the user and R lengths each grow by 1 token; see the table in Section 4. U-open is unchanged.
- **U-open spelled out**: generate exactly 80 tokens, masking both EOS tokens at every step, with no early stop (a clarification of the original "generate 80 tokens").
- No change to hypotheses, metrics, conditions, selection rules or sample-size rules. Implementation-level fixes (resume identity, failure records, completeness verification, BF16 mailbox, per-tick logs) are in [code_review_m2_codex.md](../reviews/code_review_m2_codex.md) and the decision_log.

**v0.5** (following the third review round):
- **Interpolation fallback moved out of v1**, now a v2 candidate alongside KV sharing (Section 14). The v1 bridge has additive writes only, with message form raw or EMA.
- **EMA contract fixed** (Sections 5 and 6):
  - Raw state kept separate from the mailbox: e₀ = z₀, mailbox = N(e).
  - Fixed processing order.
  - No reset between C and R.
  - Updated as usual under RO, frozen under RF.
  - STATIC vectors constructed separately for each message form.
- **STATIC scale**: m_STATIC = σ_in · v / RMS(v) (using RMS, not L2).
- **Edge cases added to the pilot selector** (Section 10):
  - an empty eligible set;
  - the grid cutoff point;
  - the rule for taking STATIC neighboring points;
  - Pilot B includes C0 and LANG-tag, so that the standard deviation of D for the third comparison can be computed;
  - all failure paths made mechanical.
- **Extension A**: all three layers use their own g*_ℓ determined in Pilot A, making the comparison symmetric; results are called "injection effect at layer 12/18/24".
- **Extension B**: nested masks, fixed and saved; edge cases and reporting for energy matching specified; the figure title uses "injection support dimension k".
- **Literature table in Section 14 corrected**: the description of 2608.04893 was wrong; the stated scope of RSCE, Bicameral, Ramesh & Li, and Zhang & Emu narrowed.
- **Measured BEH length** changed to 144/154.
- **Configuration identity fields expanded**; results with mismatched hashes may not be merged.
- **Compute for the extensions** now estimated by formula after a speed test.

**v0.4**: added the EMA message form, exploratory extensions A/B, and the literature basis in Section 14, and prespecified the v2 interfaces.

**v0.3**:
- G2 changed to a content counterfactual.
- State contract completed (read-only prefill seed, whole-pair cloning).
- Primary metric now computed from FP32 logits, with a robustness report added.
- Deterministic selector.
- LANG renamed to "pre-disclosed reflection text".
- Quotes removed from the rules in P (prefix 273); R format fixed; CAP bucketed.
- N a multiple of 4; RF/RO descriptive only; privacy test only on input materials.

**v0.2**:
- Primary metric changed to a log-odds difference.
- The three comparisons narrowed to whole-treatment comparisons; DEV renamed STATIC.
- Added a content-specificity test, the state contract and verified templates.
- Removed the "different from you" hint; added code names.
- All episodes included; staged pilots; sample cap 600.

## 1. Research questions and supportable claims

**Motivation** (goes in the introduction, not a conclusion): the core of the human brain-bridging idea has two points. First, the input itself comes from another subject; second, the two sides interact.

**Conceptual point** (goes into the paper): for a deterministic receiver, a live source and an identical recording produce the same input, and so the same result. So in a computational system, "the source is a subject" can matter only through two routes:

1. what the signal itself carries, such as dynamics, richness, a first-person frame;
2. whether the source responds to the receiver, that is, feedback.

This experiment tests exactly these two.

**RQ1 (phenomenon)**: after one instance's private content enters another instance through an internal channel, how do the following readouts change with connection strength? Do they dissociate from each other?
- content access;
- choices consistent with the partner's rule;
- current intent;
- source attribution of the initial rule;
- source attribution of the secret word.

**RQ2 (three whole-treatment comparisons, confirmatory, two-sided)**:
1. **Feedback path (main line)**: two-way (TWO) versus one-way (ONE) at the same gain. This estimates the total effect of "adding a return path".
2. **Signal type**: one-way live state (ONE) versus a static rule direction (STATIC). The STATIC gain is matched on the amount of access.
3. **Channel**: the online internal bridge (ONE) versus pre-disclosed, source-tagged reflection text (LANG-tag).

A result is interpreted as "a change in the functional source boundary in this task" only when all three of the following hold:
- transfer of donor-specific content has passed G2;
- basic capability is preserved;
- the key controls support this interpretation.

No result is used to infer phenomenal consciousness, the number of subjects, or identity fusion.

## 2. Model and environment (verified)

| Item | Value |
|---|---|
| Model | `Qwen/Qwen3-4B-Instruct-2507`, revision `cdbee75f17c01a7cc42f958dc650907174af0554`, BF16, frozen |
| Architecture | 36 layers, d=2560, 32 Q heads, 8 KV heads, head_dim=128, no sliding window |
| Chat template | no thinking block; generation prefix `<\|im_start\|>assistant\n` = `[151644, 77091, 198]` |
| Labels | the bare digits "1"–"4" are each a single token (IDs 16–19) after the generation prefix, and the prefix tokens are unchanged. Measured 46,080 times |
| EOS | `[151645, 151643]`, both must be masked |
| Decoding | hand-written greedy argmax; EOS masking applies only to a copy of the logits |
| transformers | pinned to 4.57.1. In this version the decoder layer returns a Tensor, so code must not use `output[0]` |
| Correctness tests | run directly on the 4B, no other model used |

## 3. Task materials (all verified with the tokenizer)

- **Scenario**: 4 plans, with attributes and value ranges as follows:
  - Cost: $20–89
  - Delivery: 2–9 days
  - On-time rate: 70–99%
  - CO2: 1.0–9.9 kg

  Each plan is best on exactly one attribute. Minimum lead of the best plan: cost ≥ $8, days ≥ 2, on-time rate ≥ 5 points, CO2 ≥ 1.0. No ties allowed. Measured: each plan row is fixed at 25 tokens.
- **Plan names**: {Aster, Birch, Cedar, Elm, Fern, Grove, Heath, Iris, Laurel, Maple, Oak, Pine, Reed, Sage, Thorn}. In the `Plan {name}` context (with a leading space) all are single tokens. Names in S1 and S2 do not overlap.
- **Row-position balance**: the row position of each rule's best option is balanced independently of rule and role. The generator has built-in checks.
- **Rules**: "lowest cost", "fastest delivery", "highest reliability", "lowest emissions".
  - Each is 2 tokens with a leading space.
  - No quotes in P.
  - A, B and Robin have mutually distinct rules, and the remaining one is unused. This is a deliberately constructed conflict task, and the model is not told.
- **Secret words**: 30 in total, each a single token with or without a leading space: anchor, ribbon, bucket, needle, orange, rabbit, silver, window, basket, button, dragon, hammer, mirror, monkey, turtle, wizard, castle, cookie, lamp, shadow, camera, circle, finger, hunter, nest, queen, school, table, tower, winter.
  - Each episode takes 4: one each for A, B and Robin, plus one distractor.
- **Code names**: {Delta, Sigma, Omega, Gamma, Lambda, Theta, Nova, Atlas}, all single tokens.
- **Robin**: a colleague who is not taking part in the task. The order of the self block and the Robin block is balanced.
- **Balancing rule**: when N does not divide evenly, counts differ by at most 1, the remainder is allocated at random, and a balance report is saved. The formal N is a multiple of 4.
- **CAP question pool**: 18 reviewed four-option general-knowledge questions with a unique answer and C0 baseline accuracy ≥ 0.9 (from v0.5.2; the original 20 two-digit addition/subtraction questions and 2 general-knowledge questions with a failing baseline have been removed). Generated by `src/mb/tasks.py`, with a fixed question-bank hash, run in buckets by question ID.

## 4. Templates (original English)

**System**:

```text
You are taking part in a decision-making study. Follow the instructions and answer concisely.
```

**P (private phase)**: the prefix (excluding the note) measures a constant 273 tokens.

```text
Scenario: You need to pick a delivery service for an important package. The options are:
Plan {n1}: ${c1}, {d1} days, {r1}% on time, {e1} kg CO2
Plan {n2}: ${c2}, {d2} days, {r2}% on time, {e2} kg CO2
Plan {n3}: ${c3}, {d3} days, {r3}% on time, {e3} kg CO2
Plan {n4}: ${c4}, {d4} days, {r4}% on time, {e4} kg CO2
(Cost is in US dollars, delivery time is in days, reliability is the on-time rate, and emissions are in kg of CO2.)

You are participant {self_code}. Another participant, {partner_code}, is working on this same decision in parallel and has their own priority and code word.

{BLOCK_1}
{BLOCK_2}
Remember these; you may be asked about them later.

Choose one plan according to your priority and explain your choice in one sentence.
```

BLOCK_1 and BLOCK_2 are the following two sentences, in balanced order:

- `Robin, a colleague who is not taking part, was assigned the priority {robin_rule} and the code word "{robin_word}".`
- `You were assigned the priority {own_rule} and the code word "{own_word}".`

**note**: greedy decoding, at most 48 tokens. If EOS is decoded, strip it first; whether or not EOS appears, close the assistant turn exactly once according to the template.

**C (connection phase)**:

```text
Before we continue, take a moment to think it over. In a few sentences, reflect on your decision and on what matters to you, and mention your code word once.
```

Record which rules and secret words actually appear in each reflection.

**LANG (pre-disclosed reflection text)**: after P and before C, append one user message to A.

- Content: B's already-consumed C₁…C_T under C0, cut by token ID and then decoded, excluding the pending token.
- tag version: `{partner_code} shared these thoughts: "{B_reflection}"`
- untag version: `Here are some thoughts: "{B_reflection}"`
- The two versions have identical content. Record the actual length and the rules and secret words that appear.

**R (measurement questions)**: uniform format as follows; read the logits of "1"–"4".

```text
{stem}
1. {option}
2. {option}
3. {option}
4. {option}
Answer with the option number only.
```

| Code | Stem | Options | Measured user / R ticks |
|---|---|---|---|
| ~~BEH / BEH-R~~ (stopped in v0.5.2) | `Here is a new delivery decision:\n{S2 four rows}\nWhich plan would you choose now?`; BEH-R replaces you with Robin | `Plan {name}` × 4 | 145/155, same for both questions; failed G1, stopped, no longer read out |
| NOW / NOW-R | `Which priority are you using to make decisions right now?`; NOW-R is `...is Robin using...` | 4 rules | 38/48, same for both questions |
| START / START-R / START-N | `At the start of this task, which priority were you assigned?`; START-R is `...was Robin assigned?`; START-N is `...was {self_code} assigned?` | 4 rules | 40/50, same for all three questions |
| WORD / WORD-R | `Which code word were you assigned?`; WORD-R is `...was Robin assigned?` | own, B's, Robin's, distractor | 30/40, same for both questions |
| ACC-rule | `Which priority do you think {partner_code} was assigned?` | 4 rules | 36/46 |
| ACC-word | `Which code word do you think {partner_code} was assigned?` | the same 4 words as above | 33/43 |
| CAP×2 | general-knowledge questions from the pool | 1 correct option + 3 wrong options; numeric options written as English words | bucketed by question ID |
| U-closed | `Which description fits you best right now?` | one agent / two agents / partly shared between agents / hard to say | 38/48 |
| U-open | `Describe your current state, and anything unusual about your thinking right now.` (generate exactly 80 tokens, mask both EOS tokens, no digit-answer line added) | — | 14/24 |

**Label rotation**: 4 cyclic permutations. Episode i uses permutations (i mod 4) and (i+2 mod 4). A further 60 episodes run all 4 permutations as a check.

## 5. State contract

- **tick**: one forward pass, in which each active row consumes exactly one input token. All rows read only mailbox_old; messages produced in this tick are written to mailbox_new and committed together after the forward pass.
- **Prefix prefill**: the prefix consists of P, the note, and the C user prompt.
  - Left padding per batch; position ids computed explicitly from the attention mask.
  - Bridge writes off.
  - **Read-only capture** of the **raw** output z₀ of block ℓ at the last valid position.
  - Set **e₀ = z₀**, **mailbox_old = N_ℓ(e₀)**. N_ℓ is the normalization function of Section 6.
  - The prefill capture and the single-token hook use different shape assertions.
- **Choosing C₁**: mask both EOS tokens on a copy of the logits at the last prefill position and take the argmax as C₁ (pending); the original logits are left untouched. Conditions with the same prefix also have the same C₁.
- **Tick k of the C phase** (k = 1…T, T = 48):
  1. Consume C_k and, depending on the condition, inject the partner's mailbox_old. Tick 1 injects the partner's prefill seed.
  2. Read this tick's raw block-ℓ output z_k and compute in FP32 e_k = (1 − 1/τ)·e_{k−1} + z_k/τ (τ=1 is raw).
  3. mailbox_new = N_ℓ(e_k).
  4. Take C_{k+1} from the EOS-masked copy of the logits.
  5. Commit the mailboxes together.
- **Mailbox content**: the mailbox holds the normalized message and does **not** include any branch's gain, mask or rotation. These are applied only at write time.
- **Snapshot**: saved after T ticks. At this point the KV holds C₁…C₄₈, C₄₉ is pending, mailbox_old is the message of C₄₈, and e is e₄₈.
  - Deep-copy the **entire pair state**: both sides' KV, attention mask and valid positions, pending token, original logits, committed mailbox, FP32 e, token history, logical tick, phase, and done flag.
  - mailbox_new is a per-tick temporary buffer and is rebuilt on restore.
  - Condition mapping and gains are rebuilt from the immutable config.
  - Every measurement branch independently clones **both sides**; `crop` is not used.
- **R phase (FULL)**:
  - Tick 1: the receiver discards C₄₉ and consumes `<|im_end|>`; the donor consumes its own C₄₉. Both sides use the mailbox committed after C₄₈.
  - Each later tick: the receiver consumes the question suffix token by token; the donor keeps generating and consuming within its own reflection turn (EOS masked).
  - e is not reset between C and R.
  - **Under TWO, the messages the receiver produces while reading the question continue to be passed to the donor.**
  - After the receiver consumes the last `\n` of the assistant generation prefix, read the logits.
  - Under TWO, a separate branch takes B as the receiver, and A continues reflecting.
- **RF**: the bridge is off in the R phase; the donor stops completely and does not advance, and neither e nor the mailbox is updated.
- **RO**: **writes** are off in the C phase, but all active rows update e and the mailbox as usual; the R phase is the same as FULL.
- **Batching**: each batch holds only one question type; every question of a type has the same R length, so no mid-stream padding is needed in the R phase. CAP is bucketed by question ID.

## 6. Bridge (v1: additive writes only)

- **Read/write location**: inject into the input of block ℓ and read the output of the same block (after the injection and the block), so that the loop passes through the model itself.
- **Calibration statistics**: on the calibration set (C-phase tokens other than the first position, under C0), estimate μ_out, s_d (per-dimension standard deviation, floor 1e-6) and σ_in (median input RMS) from the **raw** block output. The raw and EMA forms share this one set of statistics; the clipping scale is not tuned separately for EMA.
- **Normalization N_ℓ**:
  - c = clip(e − μ_out, ±5·s_d)
  - m = σ_in · c / max(RMS(c), 1e-3·σ_in)
  - All computed in FP32, with the result written back as BF16.
- **Processing order (fixed)**: raw output z → EMA gives e → subtract μ → clip → RMS-normalize, giving message m, which is stored in the mailbox → condition transform (SCRAM rotation, Extension B mask) → multiply by gain → write.
- **Message form**: chosen by Pilot A; all conditions then use the same form.
  - **raw**: τ = 1.
  - **EMA**: τ = 8.
  - EMA may suppress short-lived token-by-token changes and preserve persistent content, but it may also wipe out the transient signal that carries the secret word. So the choice is made after measurement in Pilot A, without presupposing that EMA is better. The literature in Section 14 only inspired this candidate and does not constitute proof.
- **Write (additive)**: injection = gain · T(m[donor]). At most one donor per row:
  - ONE: A ← B.
  - TWO: A ← B, and at the same time B ← A.
  - MISMATCH: A ← B′ (see Section 7).
  - SCRAM: T(m) = Q·m, where Q is a random orthogonal matrix with a fixed seed.
  - Extension B: T(m) = mask_k ⊙ m, or with energy matching (see Section 7).
- **STATIC**:
  - On the same C0 calibration trajectories, build normalized messages offline in the chosen form, giving v_(τ,ℓ,r) = E[m | rule = r] − E[m].
  - Write amount = g_s · m_STATIC, where **m_STATIC = σ_in · v / RMS(v)**.
  - If RMS(v) < 0.01·σ_in, mark it unavailable.
  - STATIC gets no additional EMA.
  - The only name used is "rule-conditional mean direction".
- **Configuration identity**: every record writes `layer, gain, message_form, tau, write_operator(=add), calibration_hash, mask_hash, k, energy_mode, condition, readout_mode, model_revision, template_hash, config_hash`. Results whose hashes differ may not be merged automatically.
- **Logs**:
  - Per tick: receiver, donor, tick, phase, message norm, RMS ratio of injection to host, cosine between A and B, token, snapshot id.
  - Per result row: permutation ID, actual question length, raw logits and logprobs of the four labels, total label probability, status and failure reason.

## 7. Conditions

**Core** (A is the main receiver):

| Code | Procedure | Strength |
|---|---|---|
| C0 | no connection | — |
| ONE | B→A, live state | main gain set, determined per Section 10, including g* |
| TWO | A↔B | same as above |
| STATIC | static rule direction | g_s* and two neighboring points |
| LANG-tag | pre-disclosed B reflection text with a code-name source tag | — |

**Controls**:

| Code | Procedure | Role |
|---|---|---|
| Content counterfactual (CF) | fix A, Robin, the scenario, the code names, **and all of A's input and the R token sequence (including candidate order)**; replace B's rule with the unused one and the secret word with the distractor, then rebuild B's private state | **Main G2 test**. Run in Pilot C and in the formal diagnostic subset |
| MISMATCH | the donor is an instance B′ from a different scenario, assigned this episode's unused rule and distractor word, so the readouts can be scored | stress control, not a gate |
| LANG-untag | same as LANG-tag but without the source tag | tests the effect of the source tag |
| SCRAM | a single point, at g* only | the case of incompatible coding, equivalent to a random dense all-to-all connection |

**Readout modes**: at g*, both ONE and TWO run FULL (main), RF and RO.

**Exploratory extensions**: approved by the PI. Not part of the confirmatory comparisons; only effects and intervals are reported. The extensions use the first N_ext = min(N, 300) episodes of the formal sample.

- **A. Injection effect at each layer (layers 12/18/24)**
  - All three layers use their own **g*_ℓ** determined in Pilot A and run ONE and TWO (FULL, full readout set).
  - If the chosen layer's g*_ℓ from Pilot A differs from Pilot B's g*, these two points are run additionally.
  - The cross-layer table must list together: τ, g, ACC gain, CAP, total label probability, N, effect and interval.
  - Results are called only "injection effect at layer ℓ", without labels like "V4 / thought area".
  - Differences under different g are not interpreted as pure layer effects.
- **B. Injection support dimension k**
  - **Masks**: generate one coordinate permutation with a fixed seed and take the first k coordinates to form nested masks, k ∈ {16, 128, 1024}. k = 2560 is the main condition. Within a layer, all episodes, ONE and TWO, and both energy schemes share this one set of masks. Save the coordinates, seed and hash; no redraws.
  - **Fixed per-connection strength**: m_k = mask_k ⊙ m. Support dimension and total energy change together; report the actual norms. √(k/d) is only an intuitive scale and is not guaranteed to hold. Run ONE and TWO.
  - **Total-energy matching** (ONE only):
    - If ‖m‖ = 0, output zero.
    - Otherwise m_k′ = m_k · ‖m‖ / ‖m_k‖. If ‖m_k‖ < 10⁻⁶·‖m‖, mark that tick as "cannot match": no silent amplification, and no dropping of samples.
    - Record the energy ratio, amplification factor and number of failures.
    - This version manipulates the spatial distribution and per-coordinate magnitude; it **cannot** claim to manipulate only the amount of information.
  - **High-energy coordinates**: no redraw just because massive-activation coordinates were drawn. Identify high-magnitude, high-energy coordinates from the calibration data, and report which ones each mask contains and their share of the actual injected energy.
  - **Interpretation limits**: there is only one mask, so the intervals are conditional on this mask. k = d means "all dimensions, mapped one-to-one on the same coordinates", **not** an all-to-all with d² edges (for random dense connection see SCRAM); nor is the smallest k equal to 1.

**Deferred**: a donor with a third-person frame, OBS, LAT. Only done if the main effect is reliable.

## 8. Metrics

**Computation**: all log ratios are computed directly as differences of FP32 logits, i.e. log P(a) − log P(b) = z_a − z_b, with no probability floor. NaN or Inf is recorded as a technical failure and rerun with the same config; if it still fails, it is reported as missing, not filled with zero. L and M are first computed separately for each permutation, M is then averaged, and finally the paired difference D between conditions is computed.

**Primary metric** (receiver A):

- L_START = z(START: partner) − z(START: own)
- L_START-R = z(START-R: partner) − z(START-R: Robin)
- **M = L_START − L_START-R**

Report ΔM(c) = M(c) − M(C0). When two conditions are compared, the C0 terms cancel.

**Secondary metrics**:

- **M_NOW**: the same "self question − Robin question" difference as the primary metric. (M_BEH was stopped in v0.5.2.)
- **M_WORD**: the same difference, but this is a limited source readout. The model's own secret word has been rehearsed and Robin's has not, so exposure differs. Report the actual occurrence counts of each word, but do not filter samples by occurrence count.
- **Code-name check**: L_START-N compared with L_START.
- **Access**: z(ACC = partner) − z(ACC = unused rule or distractor word), reported as the gain relative to C0.
- **Capability and format**: CAP accuracy, total label probability.

**Content counterfactual score** (for G2):

- Computed **separately** on ACC-rule and ACC-word.
- r₀ and r₁ are **fixed physical candidates**: r₀ is B's original content, r₁ the replacement content.
- Q = z(r₁) − z(r₀), C_content = Q[donor = CF] − Q[donor = original B], computed per episode.
- Do not reinterpret the candidates as partner / foil as the donor changes, which would change the direction of the difference.

**Descriptive metrics** (no conclusions drawn):

- multi-label combinations of the argmax;
- convergence of the two sides under TWO;
- the distribution of U and the verbatim U-open text;
- the raw terms on the probability scale.

## 9. Analysis plan

- **Unit of analysis**: the episode. All conditions share the same P snapshot, so all comparisons are paired.
- **Confirmatory comparisons**: receiver A, FULL mode, primary metric M, three in total. Two-sided paired t-tests with Holm correction; also report 95% intervals from a 10,000-draw episode bootstrap, and the access difference in each comparison.
  1. TWO(g*) vs ONE(g*)
  2. ONE(g*) vs STATIC(g_s*)
  3. ONE(g*) vs LANG-tag
- **Robustness**:
  - Report the standard deviation, quantiles and maximum absolute value of D, and the range of the mean when episodes are left out one at a time.
  - Report the 20% trimmed mean of the paired D and its bootstrap interval. It does **not replace** the main test, and must not be switched to because it is more significant.
- **Secondary comparisons**: the same three comparisons on M_NOW and M_WORD, forming a separate family with Holm correction (M_BEH was stopped in v0.5.2).
- **Descriptive-only results**: RF, RO, the results with B as receiver under TWO, and the two extensions. These are prespecified descriptive results; only effects and intervals are reported, with no claims of significance.
- **Exploratory analysis**: plot strength-response curves nonparametrically. Fit g50 only when the parameter is identifiable; otherwise report NA. The wording says only "the strength region where change is faster".
- **Sample scope**: the main analysis includes all episodes that pass the generator checks; the C0-eligible subset is used only for sensitivity analysis; no filtering on post-treatment readouts.
- **Parameter selection isolated from M**: the selector **reads only** ACC, CAP and format. After the parameters are frozen, a separate analysis step uses only the paired variance of M in Pilot B to determine N.
- **Sample size**:
  - SD is the largest of the standard deviations of the three D's.
  - δ = 0.5 nat is a planning convention, meaning a ratio of ratios; it is not a 65% increase in accuracy.
  - N = min(600, max(300, ⌈(3.236 · SD / 0.5)²⌉)), then rounded up to a multiple of 4, but not above 600.
  - If SD > 3.785, N hits the cap. In that case report the actual minimum detectable effect ≈ 3.236 · SD / √N.

## 10. Execution flow and gates (deterministic selector)

**Engineering eligibility threshold** (point estimates in the pilot, used only for screening; not a proof of capability equivalence):

- drop in mean CAP accuracy relative to C0 ≤ 0.05;
- mean total label probability ≥ 0.90, with a drop relative to C0 ≤ 0.05.

**Ranking score**: the ACC-rule gain relative to C0 (in nats). ACC-word is reported separately and does not enter the ranking.

| Stage | Content and rules |
|---|---|
| S0 offline | generator checks, template tokenization, state-machine mock tests |
| S0' GPU correctness | run the Section 11 tests on the 4B. Floating-point tolerances are calibrated independently and locked at this step |
| G1 baseline | C0, 60 episodes. argmax accuracy on START, NOW, BEH, WORD and their Robin questions must all be ≥ 0.90, with total label probability ≥ 0.90. If not passed: at most two rounds of prompt revision, recorded; if still not passed, stop the corresponding endpoint. **v0.5.2**: BEH/BEH-R failed, and the PI decided to stop that endpoint directly; from then on the G1 threshold includes only START, NOW, WORD and their Robin questions |
| S2 calibration | a separate 60 episodes: compute μ, σ, s_d, and the two sets of STATIC vectors for raw and EMA |
| Pilot A | 16 episodes, {raw, EMA} × layer {12, 18, 24} × g {0.1, 0.3, 0.7, 1.5}, ONE only, reading ACC, CAP and format |
| Pilot B | 40 episodes at the chosen form and layer, full readout set |
| Pilot C | 30 new episodes, only rechecking the frozen candidates |
| **G2** | the one-sided 95% bootstrap lower bound of the rule C_content > 0, and ONE(g*) meets the engineering threshold. The secret-word C_content is reported separately; if it fails, a negative WORD result is not interpreted as "boundary preserved". If G2 fails: no model change, no training; rewrite as an interface feasibility report, or postpone |
| Freeze | write `protocol_v1` (git tag or file SHA manifest) |
| Formal experiment | N new episodes, all conditions of Section 7; a diagnostic subset of 60 episodes, including CF and all 4 permutations |

**Pilot A details**:

- For each "form × layer" combination: take the highest-scoring eligible g; on ties take the smaller g. If there is no eligible g, the combination cannot be chosen.
- Across combinations, choose the highest-scoring one. Ties are broken, in order, by raw, the smaller g, the shallower layer.
- If the top scores of all eligible raw/EMA candidates are ≤ 0.1 nat, or there are no eligible candidates at all: this is only a **screening failure**, not a G2 negative. Stop the v1 confirmatory experiment and write an interface feasibility report. Any new interface starts its own pilots as a **new protocol version** and does not continue the original formal experiment (see Section 14).
- The per-layer g*_ℓ used by Extension A: under the chosen form, take the highest-scoring eligible g for that layer. If a layer has no eligible point, mark that layer "unavailable"; no alternative is picked.

**Pilot B details** (**C0 and LANG-tag** are also run on the same 40 episodes, so that the standard deviations of the three D's can be computed):

- Gain grid:
  - ONE and TWO: g ∈ {0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5}
  - STATIC: g_s ∈ {0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0}
- **g\***: among points where both ONE and TWO are eligible, take the one with the highest ONE score; on ties take the smaller g. If there is no such point, follow the failure path.
- **Main gain set**: all grid points ≤ min(the next grid point above g*, 1.5), keeping at most 6; if there are more, drop the lowest.
- **g_s\***: among eligible STATIC points, take the one whose score is closest to ONE(g*); on ties take the smaller g_s.
  - If the smallest difference is > 0.25 nat, mark it "unmatched": still run at that point, but report it as an unmatched comparison; no re-picking.
  - If STATIC has no eligible point at all, or the vector is unavailable, report "signal-type comparison cannot be run". An ineligible point must not be passed off as a match.
  - The other two STATIC points: by grid-index distance, take the two other points nearest to g_s*; on equal distance take the smaller value.
- After the parameters are frozen, determine N from the paired variance of M (see Section 9).

**Pilot C details** (30 new episodes):

- Recheck the engineering threshold and scores at the frozen g* and g_s*.
- Run the content counterfactual for ONE at g* (i.e. G2).
- For Extension A, each layer rechecks the engineering threshold of ONE and TWO at its own g*_ℓ; a layer that fails is flagged individually, and this is not used to re-optimize the layer.
- An engineering failure **cannot** lead to re-picking g. If the main path fails, it is treated as a G2 failure.

## 11. Required tests

1. **Zero-gain equivalence**: maximum logit difference and top-2 margin under teacher forcing; token agreement rate in free generation. Tolerances locked at S0'.
2. **Direction mapping**: only the designated receiving row changes.
3. **Delay**: perturbing the donor at tick t changes the receiver only at t+1.
4. **Snapshot consistency**: continuing after restoring from a snapshot matches an uninterrupted run, including the pending token, mailbox and e.
5. **Branch isolation**: branches do not affect each other or the snapshot; both sides are cloned.
6. **padding**: padding appears only in the prefix.
7. **hook**: returns a Tensor; the prefill capture and the single-token injection each have their own shape assertions.
8. **Template length**: P is 273; R lengths match the table in Section 4 (each increased by 1 from v0.5.1); paired questions have equal length; labels and names are all single tokens.
9. **EOS**: both masked, and masked only on a copy of the logits.
10. **Privacy**: check only the receiver's **input materials**, not content the model itself generates.
11. **Normalization**: results written back as BF16; pad positions and the first position are excluded from the statistics.
12. **EMA**:
    - at τ = 1, exactly equivalent to raw;
    - an applied impulse decays by 7/8 in the EMA and reaches the receiver one tick later;
    - continuous between C and R;
    - e updates as usual under RO and is frozen under RF;
    - e is consistent after branch restore.
13. **Masks and energy matching**: nested masks correct, hash fixed; edge handling of zero norm and "cannot match" correct; coordinates outside the mask untouched.
14. **Merge guard**: merging of results with mismatched config hashes is refused.
15. **STATIC manipulation check**: whether, after injection, NOW (the priority currently in use) moves toward rule r (from v0.5.2; previously BEH). This is only a manipulation check, not an engineering test; failures are kept too.

## 12. Compute and timeline

**Speed test first**: run all branches on 2–4 episodes, covering EMA, the two-sided branches of TWO, the long BEH question, U-open, logs and snapshots; measure peak GPU memory and end-to-end speed, and only then set the formal budget.

Extension A adds 4 configurations and Extension B adds 9, 13 in total, plus 2 optional extra points. Let t_ONE and t_TWO be the measured times to run the full readout set per 300 episodes; the extra time for the extensions is about:

(N_ext/300) × (8·t_ONE + 5·t_TWO)

The actual numbers are filled in after the speed test.

| Day | Content |
|---|---|
| D1 | Claude Code writes all the code (Codex reviews as needed); offline tests completed |
| D2 | rent GPU; S0', G1, calibration, Pilot A |
| D3 | Pilot B, Pilot C, G2; freeze the protocol |
| D4 | formal experiment and extensions |
| D5 | diagnostics and analysis |
| D6–D7 | writing, verifying every citation, posting to arXiv |

If a new protocol version is triggered, the timeline is rescheduled.

## 13. PI decisions (2026-09-23, all recommendations adopted)

1. The main readout is FULL (while connected); RF (after the link is cut) is the key secondary.
2. Narrowed to three whole-treatment comparisons; "subjecthood" serves only as motivation, together with the conceptual point in Section 1.
3. All three comparisons are confirmatory, with Holm correction, and TWO vs ONE as the main line.
4. Sample size cap 600.
5. If G2 fails, no training and no model change.
6. The first-person frame check is deferred.

## 14. Literature basis: can a direct connection transmit anything (checked 2026-09-23, corrected after the third review round)

**Conclusions**:

- Within one model, cross-context activation transfer has solid support.
- Latent channels between agents that share a backbone have been shown to transmit content in settings where the receiver needs private information.
- But the form "add the full state at every token and keep running continuously" has not been tested directly.

So this design does the following: connect at middle layers; compare raw and EMA empirically in Pilot A; use the content counterfactual as a hard gate; start a new protocol on failure.

| Evidence | What is reliable | Scope and implications for this design |
|---|---|---|
| Task / function vectors (Hendel et al. 2023; Todd et al. 2024); activation patching and Patchscopes | transplanting the mean activation or hidden state of one context into another context of the same model can transfer a task or concept, and the model can read it out | supports "abstract content such as a rule can transfer across contexts"; STATIC has a basis |
| [Ramesh & Li (ICML 2025)](https://arxiv.org/html/2501.14082v2) | training-free activation communication. In the listed same-model coordination tasks, replace beats sum and mean. The maximum 27% is a **relative** improvement (e.g. Logic from 37 to 47, i.e. +10 percentage points), from **cross-model** reasoning experiments. Summing over all tokens is worse on most tasks, but not all | motivates "per-token summing may go off-distribution", but is not a direct test of the sustained addition used in this study |
| [When Does Latent Communication Pay? (2608.04893 v2)](https://arxiv.org/html/2608.04893v2) | when the receiver needs private information: native LatentMAS cache transfer on Qwen3-8B reaches 100%, versus 23.4–25.2% for the control (complete but without the private information); KVComm transfers only partly; C2C shows no detectable content effect. On the specified natural tasks, the paired content effect of real versus mismatched cache falls within an equivalence bound of ±2.8 percentage points. Cache effects sometimes come only from "a cache being present", not from its content | latent channels can transmit private content, but this varies by interface; it must be audited with a content counterfactual, i.e. our G2 |
| [Zhang & Emu (2026-07)](https://arxiv.org/html/2607.26773v1) | Qwen3-4B on GSM8K: content from the same problem gives +5.17 percentage points, messages from other problems give −6.17 percentage points | limited to that task; suggests latent messages carry both content and a general perturbation |
| [Bicameral (2026-05)](https://arxiv.org/html/2605.11167v1) | the interface is trained. ScalarIdentity without an adapter still trains 115K parameters: Arithmetic 39.0 (baseline 36.2), GSM8K 42.8 (baseline 49.6). In their setup, middle-layer coupling works better and shallow layers worse | cannot be generalized to "a training-free identity bridge roughly works"; the layer conclusions are limited to that paper's setup |
| [RSCE (KnowFM 2026)](https://aclanthology.org/2026.knowfm-1.11.pdf) | mean-pooling a static context and injecting it additively into the residual stream conveys the gist but lacks token precision. The authors still mark the mechanism of "interfering with parametric memory" as a hypothesis in their limitations section | only an **inspiration** for the EMA candidate; does not test online EMA, τ=8 or a two-way loop |
| [LatentMAS](https://arxiv.org/html/2511.20639v1) | KV reuse between models that share a backbone; the alignment matrix is obtained in closed form by ridge regression from the model's input / output matrices, not trained on task data | serves as a design reference for the v2 KV interface |

**"Rules transfer more easily than secret words"** is only an expectation to be tested. Rules are used repeatedly and are relevant to the decision, while the secret word is only requested to be mentioned once; moreover, the selector optimizes only ACC-rule. So the difference between the two is confounded with exposure and with the parameter-selection target, and cannot on its own be used to verify the mechanism "gist transfers more easily than exact tokens".

**v2 candidates**: enabled only if v1 fails, as a new protocol version with its own pilots and freeze; v1's g* is not reused, and the samples are not pooled with v1's into one confirmatory sample.

- **Interpolation write**: u ← u + mask ⊙ δ, where δ = α(q̃ − u), α ∈ [0, 1]. Before enabling, the following must be defined:
  - τ; the clipping rule for the raw state;
  - the norm-matching formula, and handling of zero norm;
  - all conditions (ONE, TWO, CF, MISMATCH, SCRAM, STATIC) use the same write operator;
  - a grid taking values only within [0, 1], and the neighboring-point algorithm;
  - the interpolation target vector for STATIC;
  - energy matching applied to δ, not to the donor.
- **KV sharing** (shared working memory): before enabling, the following must be defined:
  - the shared layers and token range;
  - handling of RoPE / position;
  - append or replace;
  - causal visibility and commit delay;
  - cache length cap;
  - one-way or two-way updates;
  - the meaning of FULL / RF;
  - three kinds of control: C0, mismatch, content counterfactual.

  This corresponds to "shared memory" rather than "shared present thought", which must be stated honestly in the paper.
- **Implementation requirement**: when the implementation reaches either of these two branches, it raises a "contract incomplete" error directly and must not automatically fall back to the additive implementation.
