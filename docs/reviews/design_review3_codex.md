# Experiment design v0.4 final review

Review date: 2026-09-23. I read v0.4 in full and checked it against the previous review, PLAN, AGENTS, and decision_log. Main file SHA256: `8600866bafb462c01c09747531aa9d7fd1b5b446882e3b96468beae6e3957041`. This round adds only this file; the offline tokenization materials are saved in `/tmp`, and I did not download weights, run the model, or write project implementation.

## 1. Overall verdict: ready for implementation, except for the interpolation fallback branch

**The raw/EMA main path, extensions A/B, and the task and analysis modules can start.** The previous round's two blockers, the G2 content counterfactual and the prefill read-only capture vs hook contract, have been correctly implemented. The newly added interpolation fallback has its own interface blocker and cannot be enabled automatically by reusing the additive bridge's config; see B1.

This is not an approval that "every branch of the current draft can be implemented in only one way". The following local patches should be written into the implementation spec and tests; among them, EMA initialization, STATIC scale, and pilot boundaries must be settled before the corresponding code is accepted. They do not require reopening the decisions in section 13, nor another full design audit. The plan at the end applies to the four modules that can start, not to the interpolation and KV runtime.

## 2. Parts of last round's comments not yet fully implemented

The important and minor comments from last round that are not listed here have been implemented at the design level; this does not mean the GPU correctness tests have passed.

| Last round's comment | Location in v0.4 | Specific patch still missing |
|---|---|---|
| I2: deterministic pilot selector | §10 | Handling of an empty eligible set, of `g*=1.5` with no higher point, and of "the two neighboring points" when the STATIC match point is on the boundary is still undefined. Suggestion: an empty set returns an explicit failure; the main grid ends at `min(next(g*), max_grid)`, dropping the lowest point if it exceeds six points; STATIC takes the two other points closest by grid-index distance, preferring the smaller value on ties. When unusable directions leave STATIC with no eligible candidate, keep the failure report, and do not pass off an ineligible point as a matched comparison |
| I2/I8: Pilot B must be able to compute the SD of the three D's | §9–10 | Pilot B lists ONE/TWO/STATIC but does not specify **C0 and LANG-tag** on the same 40 cases. Add both; otherwise the paired SD of the third item, `ONE−LANG-tag`, cannot be computed. Change "M is not looked at in any step" to "the selector reads only ACC/CAP/format; after the parameters are frozen, a separate analysis step uses only the paired variance of M to set N" |
| Original I6: normalization scale | §6 | It is not stated whether `v̂` is normalized by L2 or by RMS. I suggest specifying `m_STATIC=σ_in·v/RMS(v)`, keeping the near-zero rejection threshold. Under the usual L2 unit-vector interpretation, the RMS of STATIC would be about `√2560≈50.6` times smaller than that of live messages, and the existing gain grid would lose its same-scale meaning |
| I5: template numbers consistent with acceptance | §4, §11.8 | BEH options are now `Plan {name}`, measured at **144/154**, not the 140/150 in the table. Just update the length table and test constants; no need to change the questions again |
| Original M5: collaboration-file interface version | AGENTS | It still says v0.2 is authoritative, the old table still has `crop`, and the old readout only passes logprob. The owner should sync it to v0.4, whole-pair cloning, raw four-label logits, and the other new fields; as instructed, this round does not change it |

## 3. New issues in v0.4

### B1 | Blocker, interpolation fallback only: the write operator is not yet wired to the conditions and grids (§6–7, §10)

Interpolation changes both the donor representation and the receiver's own state: `(1−α)u+αq` includes host decay. So it is not just a matter of renaming the additive bridge's `g`. There are currently four substantive gaps:

1. "The donor's integrated state" does not specify τ; without centering, whether clipping is still done, and around what center, is undefined.
2. Pilot B keeps using the additive grid containing 1.5 and 2.0; treated as α, this produces extrapolation and negative host coefficients, and is no longer the fallback form described in the text.
3. The STATIC direction, MISMATCH, and SCRAM have no interpolation versions. Whether SCRAM rotates first and then matches the host norm, or rotates the old `m`, gives different results.
4. If extension B is written directly as `(1−α)u+α·mask⊙q`, **the unconnected coordinates are also attenuated**, and it is no longer "injecting only at k coordinates".

**Fix:** separate `message_form` from `write_operator`. When the fallback is triggered, a separate config must be used: specify τ, the clipping rule for the raw state, the norm-matching formula, and zero-norm handling; ONE/TWO/CF/MISMATCH/SCRAM/STATIC all use the same write operator, changing only the donor or its transform. Give Pilot B/STATIC grids lying only in `[0,1]` and the neighboring-point algorithm, and redo the corresponding calibration, matching, and Pilot C; the additive bridge's g* cannot be reused. STATIC must specify how its interpolation target vector is constructed from the same processing pipeline.

Sparse interpolation should first define the full change `δ=α(q̃−u)`, then write `u←u+mask⊙δ`; if total energy matching is done, match **the change δ**, not just the donor's norm, and acknowledge that after rescaling it may no longer be a per-coordinate convex interpolation.

During implementation, give this branch an explicit "contract incomplete" error and forbid automatically falling back to the additive implementation. Filling in the interface above lifts the local blocker; there is no need to wait for it before writing the tasks, scoring, and the raw/EMA bridge.

### I1 | Important: EMA's raw state and the mailbox seed must be kept separate (§5–6)

The "seed" in §5 is a centered, clipped, normalized message; §6, however, treats it as the initial value of the EMA raw state e and mixes it with the unprocessed z. This produces an extra start-up transient and also admits two reasonable implementations. I suggest hard-coding the following contract, where `N_ℓ` is the existing normalization function:

- Prefill captures the raw `z₀`; set **`e₀=z₀`, `mailbox_old=N_ℓ(e₀)`**. Do not apply EMA again to the already-normalized mailbox.
- At tick t, first inject the old mailbox; after reading this tick's block output, compute `e_t=(1−1/τ)e_{t−1}+z_t/τ` in FP32, then compute `mailbox_new=N_ℓ(e_t)`; commit together. τ=1 is raw.
- The order is fixed as **raw output → EMA → subtract μ → clip → RMS normalization → condition transform/mask → gain → write**. Both forms share the μ, s_d, σ estimated for that layer from the raw C0 outputs; do not quietly tune a separate clipping scale for EMA.
- C→R does not reset e; in RO's C phase, although writes are off, the active row still updates e/the mailbox normally; RF's donor stops completely. The FP32 tensor of e is deep-copied together with both sides' state. The mailbox stores the normalized message; it must not store a result already multiplied by some branch's gain or mask.
- From the same batch of C0 trajectories used for calibration, build the raw/EMA messages offline separately to get their respective `v_(τ,ℓ,r)`; STATIC uses the direction of the selected form, **without applying an extra EMA**.

This way raw/EMA can be compared as two prespecified message-processing pipelines; there is no need to also match their token-by-token waveforms. New tests: τ=1 equivalence, the EMA impulse decays by 7/8 and arrives one tick later, C/R continuity, RO updates, RF freezing, e consistent after branch restore. Only a small amount of state and test code is needed.

### I2 | Important: the new form selection is acceptable, but the failure paths must be made mechanical (§10)

Selecting the form only by ACC-rule, CAP, and label mass adds no risk of picking parameters by M; the independent Pilot C remains necessary. Add three points:

- An empty eligible set for any "form×layer" counts as not selectable; within a group, exact ties go first to the smaller g, and then the between-group rule in the text applies. Only when **the top score among all eligible raw/EMA candidates is ≤0.1, or there are no eligible candidates at all**, is the fallback attempted.
- Make explicit that an engineering failure in Pilot C cannot be used to re-pick g. Failure of the main path is handled via the established interface-feasibility report/new protocol; failures in extension layers are flagged separately and cannot be used to re-optimize the layer position.
- A Pilot A failure is only a screening failure, not a "G2 negative" obtained after the content counterfactual test has been completed. "Enable v2" in §10 should mean **opening a new version and pilot**, and cannot automatically continue the original formal experiment.

### I3 | Important: extension A is doable, but it compares treatments calibrated per layer (§7, §10)

**The scheme in which ONE determines g*_ℓ and TWO reuses it is acceptable**: it keeps the definition of "adding a return path" within the same layer, and does not use attribution results to choose strength. Pilot C must actually cover the engineering checks for these layers; on failure, record the degradation and do not use it to interpret the source boundary.

The cross-layer table must list τ, g, ACC increase, CAP, label mass, N, and effect intervals together. In particular, the main g* of the selected layer comes from the larger Pilot B, while the other two layers come from Pilot A: this cannot be called a comparison of layer quality under equal tuning budgets. To draw a symmetric three-layer comparison, all three layers should use their own **Pilot A** g*_ℓ, adding two ONE/TWO points for the selected layer if necessary; otherwise keep the current arrangement and state clearly that it is an exploratory treatment comparison under different calibration budgets.

Describe the results as "injection effects at layers 12/18/24"; do not use "V4/thought region" as a result label, and do not interpret differences under different g as pure layer effects. There is no need to re-decide whether to do the extension.

### I4 | Important: extension B must freeze the mask and the near-zero rules, and energy matching is not content matching (§7)

The existing order of "full normalization first, then masking" is correct; I suggest completing it as follows:

- Use one random coordinate permutation fixed in advance and take the first k to form **nested masks**, shared across all episodes in the same layer, both ONE/TWO directions, and both energy schemes. Save the coordinates, seed, and hash, and do not redraw based on M or formal results.
- The fixed-strength version keeps the coefficient g on each retained coordinate unchanged, while changing the support dimension and the total energy. `√(k/d)` is only a scaling intuition for uniformly sampling a given vector; it is not guaranteed to hold for trajectories already changed by feedback, so report the actual norms.
- The total-energy version keeps the full candidate message norm per tick, while changing the spatial distribution and the per-coordinate amplitude; **one cannot claim on this basis that only the amount of information was manipulated**. I suggest specifying: when `‖m‖=0`, output zero; otherwise `ε=10⁻⁶‖m‖`, and if `‖m_k‖<ε`, mark that tick as unable to achieve energy matching, without quietly amplifying or dropping samples. Record the actual energy ratio, amplification factor, and number of failures. If clipping is applied again after matching, matching is no longer guaranteed and this must be flagged separately.
- Do not redraw because massive-activation coordinates were drawn. Use S2's raw magnitudes and the normalized per-dimension energy to identify, and save a report of, the high-magnitude/high-energy coordinates, recording which ones each mask contains and their share of the actual injected energy. Re-amplification after clip may still concentrate on a few coordinates; capability and format must be checked.

With only one mask, the episode-bootstrap interval is **conditional on that one mask** and does not include the uncertainty from random coordinate selection; it can serve as an exploratory result but cannot be generalized to all k-dimensional connections. There is no need to force multiple masks this week. Name the figure "injected support dimension k": what is done now is sparsification of a same-coordinate mapping; k=d is also not an all-to-all of d² edges, and the minimum k is not 1.

### I5 | Important: the literature table has one clear error, and the rest need a narrowed scope (§6, §14)

All links below have been checked against the originals; this is a spot check of the newly added arguments, not a new SOTA search.

| Reference | Check result and suggested change |
|---|---|
| [Ramesh & Li, Tables 2/3/5, Appendix B.1](https://arxiv.org/html/2501.14082v2) | replace outperforms sum/mean on the listed same-model coordination tasks. The maximum **27% is a relative improvement**: Logic's 37→47, i.e. +10 percentage points; this number comes from the cross-model reasoning experiment and must not be merged with the same-model experiments into one result. All-token summation is worse on most tasks, but not on every one, and it is not a direct test of this study's per-tick sustained addition. Rewrite it as motivation for the fallback form; it cannot be written as proof that this bridge should use replace |
| [2608.04893, §4, Table 1](https://arxiv.org/html/2608.04893v2) | **"When not needed, it is equivalent to not transferring" is wrong**: what was tested is the paired content effect of the true cache versus a mismatched cache, which falls within a ±2.8 percentage point equivalence bound on the specified natural tasks. 100% vs 23.4–25.2% is Qwen3-8B's native LatentMAS relay, with intact-no-private as the control; it is not all three interfaces, nor deranged. KVComm transfers partially; C2C showed no corresponding content effect |
| [RSCE, §3 and Limitations](https://aclanthology.org/2026.knowfm-1.11.pdf) | It does have static context mean pooling and additive residual injection, but it did not test online EMA, τ=8, or a two-way loop. The mechanism of "interfering with parametric memory" is still labeled a hypothesis in the limitations section. Better to write "inspired the temporal-integration candidate", not "proves EMA preserves rules and loses secret words" |
| [Bicameral, Table 1, Appendix C.14/C.15](https://arxiv.org/html/2605.11167v1) | The paper does report that, under its setting, middle-layer coupling works better and shallower configurations work worse, but the interface is trained. ScalarIdentity without an adapter still trains **115K parameters**; Arithmetic 39.0 vs baseline 36.2, GSM8K 42.8 vs 49.6, which cannot be summarized as a training-free identity bridge being approximately equivalent. Layer conclusions must be limited to that paper's model, tool tasks, and training configuration |
| [LatentMAS, §3/A.1](https://arxiv.org/html/2511.20639v1); [Zhang & Emu, Figure 1](https://arxiv.org/html/2607.26773v1) | The former does have KV reuse and a ridge alignment solved in closed form from the model's input/output matrices, not a bridge trained on task data. The latter's +5.17/−6.17 percentage points belong to the **Qwen3-4B, GSM8K** decomposition; the task qualification should be added, and it cannot be treated as a general communication effect of that model |

"Rules transfer more easily than secret words" can be kept as a **prediction to be tested**. Rules are used repeatedly and are relevant to task decisions, whereas the word is only asked to be mentioned once; moreover, the selector only optimizes ACC-rule. So the difference between the two results also includes exposure and the parameter-selection target, and is not sufficient on its own to validate the mechanism "gist over exact tokens". §6 should change "will average out noise and keep persistent content" to "may suppress short-term variation, and may also erase the transient signal carrying the secret word".

### I6 | Important: the 2–3 hour estimate for the extensions has no basis yet (§12)

If the extensions use the full formal N, A adds `2 layers×2 topologies=4` FULL configs; B adds `3k×(ONE fixed, TWO fixed, ONE energy-matched)=9`, for **13** in total, not counting I3's two optional supplementary points or the pilot. If `t_ONE/t_TWO` denote the measured time of each per 300 cases with all readouts, the extra budget is about:

`(N/300) × (8·t_ONE + 5·t_TWO)`.

To add only 2–3 hours at N=600, each config would have to average about 4.6–6.9 minutes per 300 cases; there is currently no timing evidence for this. Pilot A itself has 384 episode×config units, and the interpolation fallback adds another 144.

State the extension N explicitly, and change §12's 2–3 hours to a figure filled in after profiling. The 2–4-case timing run should include EMA, TWO two-sided branches, long BEH, U-open, logging, and snapshot costs. Finishing in one week can still be the goal, but if interpolation or a new KV protocol is triggered at the same time, the original timeline can no longer be promised; first freeze the run list for the core and A/B, then schedule parallel writing based on the measurements.

### Minor items

- **v2 KV (§14) is sufficient as a future direction but insufficient as an implementation spec.** No need to expand it into code now; the new protocol that precedes enabling it must fix: shared layers and token range, RoPE/position handling, append or replace, causal visibility and commit delay, cache length cap, one-way/two-way updates, the meaning of FULL/RF, and the C0/mismatch/content-counterfactual controls. Re-pilot, freeze, and draw a formal sample; do not reuse the residual bridge's g* or splice the two versions into the same confirmatory sample. [LatentMAS](https://arxiv.org/html/2511.20639v1) can only serve as a design reference; "the selected layer and deeper layers" does not mean it has been replicated.
- **The config identity should be expanded (§6, §9):** besides layer/g, record `message_form, tau, write_operator, calibration_hash, mask_hash, k, energy_mode`; list α separately. Results with inconsistent normalization, mask, or pairing hashes must not be merged automatically.
- **G2 should name its readout questions:** C_content is computed on `ACC-rule` / `ACC-word`, each using fixed physical candidates r₀/r₁; do not reinterpret them as partner/foil as the donor changes and thereby change the direction of the difference.

## 4. Tokenizer re-check

Reused `/tmp/mb-tokenizer-audit-EVn1B1/`. seed=`20260924`, 240 episodes, 480 receivers, rendering **11,520 complete four-choice question chats** with the current templates; note/C use clearly labeled synthetic fixtures, and no model was run.

| Check | Result |
|---|---|
| P prefix, excluding the note | 480/480 are **273 tokens**; both information-block orders pass |
| BEH / BEH-R | user/R are **144/154**, all constant; four `Plan` tokens more than in the previous round's test |
| NOW, START/START-R/START-N, WORD | 37/47, 39/49, 29/39 respectively, matching the document; all pairs equal length |
| ACC-rule, ACC-word, U-closed, U-open | 35/45, 32/42, 37/47, 14/24 respectively, matching the document |
| Numeric label boundaries | 46,080 checks pass; prefix unchanged, the appended label is a single token |
| Words, code names, plan names | Words and code names are single tokens both bare and with a space; plan names are all single tokens in their actual spaced positions, while in bare form still only Oak is a single token |
| Numbers and plan rows | 1,920 rows from random scenarios and 2,970 rows from per-attribute enumeration, all 25 tokens |
| CAP | The question pool has not been compiled yet; to be accepted item ID by item ID during implementation; does not affect the results for questions already defined |

Paired equal length means the same token count, not the same token IDs. The lengths of real generated notes and LANG content are not guaranteed to be constant. I suggest keeping the existing BEH text and only correcting the numbers in the table.

Temporary evidence: [script](/tmp/mb-review3-NuEBYh/check_templates.py), [statistics](/tmp/mb-review3-NuEBYh/tokenizer_results.json), [rendered examples](/tmp/mb-review3-NuEBYh/sample_chats.json).

## 5. Implementation plan for the four modules that can start immediately

The scope below does not depend on the not-yet-complete interpolation/KV write contracts; no code is written in this round. The config takes v0.4 and the explicit corrections in this review as the acceptance basis.

### `src/mb/tasks.py`: materials and questions (§3, §4, §7)

- `make_episodes(n, split, seed) -> list[Episode]`: generates S1/S2, the A/B/Robin bindings, unused/foil, code names, information-block order, label rotation, and CAP item IDs; immutable dataclasses store the true content IDs. `validate_episodes(...) -> BalanceReport` checks the unique optimum, minimum margin, non-repeating names, marginal balance, and split isolation; it does not require the impossible perfect balance of all joint cells.
- `private_messages(episode, recipient)`, `readout_questions(episode, recipient, rotations=None) -> list[Question]`: render the templates strictly. Question contains `qid/construct/messages/labels/content_ids/label_meaning/rotation_id/cap_item_id`; after compilation it carries the token IDs, R tick count, and text hash. Numeric labels get no space.
- `make_donor_variant(episode, kind, seed) -> DonorVariant`: provides the CF/MISMATCH materials and the actual donor ground truth, keeping the original r₀/r₁; verifies that A's external materials and R token sequence are completely unchanged. A's reflection, freely generated after the bridge, is allowed to change. Condition scheduling still belongs to Claude's conditions/run.
- `make_cap_bank(seed) -> list[CapItem]`: 20 two-digit arithmetic questions and 20 reviewed deterministic common-sense questions, each with four distinct options and a unique correct answer; fix the question bank hash and bucket by item. `lang_message(consumed_ids, codename, tagged, tokenizer)` decodes only the consumed C₁…C₄₈; tag/untag share the same content.

### `src/mb/readouts.py`: pure scoring (§7–8)

- `score(record) -> QuestionScore`: inputs are the four raw logits, the full-vocabulary logprobs/total label probability, and the content mapping; outputs are the correct-option/per-source probabilities, argmax, L, ACC, and format metrics. Internal differences use FP32 logits with no probability floor; failure status and NaN/Inf are passed through explicitly.
- `pair_readouts(scores) -> RotationMetrics`: pairs self–Robin within the same episode/receiver/condition/permutation to get M, M_BEH, M_NOW, M_WORD, and the code-name difference; `aggregate_rotations(...) -> EpisodeMetrics` computes the per-permutation metrics first and then averages; missing pair members are not filled with zero.
- `score_content_cf(original, counterfactual) -> ContentScore`: asserts that the readout tokens/hash are identical, and computes the rule/word Q difference with the fixed r₀/r₁. It also outputs descriptive fields such as multi-label combinations, U, self-report, and word occurrence counts, without filtering samples on them.

### `src/mb/analyze.py`: paired statistics and figures (§8–9)

- `build_paired_table(records, frozen_config) -> EpisodeTable`: verifies protocol/model/split/config and checks for duplicate or missing records; each contrast keeps complete pairs and reports the missing items and the effective N. Directions, permutations, and branches must not become additional independent samples.
- `confirmatory_tests(table) -> Results`: paired t + Holm for the three M items of A/FULL; the nine secondary items form a separate family. `bootstrap_episodes(table, seed, n_boot=10000)` resamples whole episodes, keeping their conditions and directions; the RF/RO/B side and the extensions report only effects and intervals.
- `robustness_report(D)` outputs the SD, quantiles, extremes, leave-one-out mean range, and the bootstrap interval of the 20% trimmed mean of paired D; `plan_sample_size(pilot_D)` implements the max SD, 300–600, rounding up to a multiple of four, and the actual MDE.
- `plot_results(...)` shows the main comparisons, probability components, strength curves, and the layer and dimension extensions separately, annotating g/τ/energy scheme and capability degradation; it does not mix different configs into pure-layer or pure-information-quantity conclusions. If the selector is provided by this module, its input may only be ACC/CAP/format summaries, and it cannot access M/U.

### `tests/test_tasks.py`: offline acceptance and pure-scoring interface checks

- Multiple seeds, including n that does not divide evenly: task constraints, marginal balance, label balance under the two permutations, no leakage of private bindings; CF leaves A/R bytes and tokens unchanged, and the actual MISMATCH donor content falls within the candidates.
- Official tokenizer: P=273, BEH R=154, the other lengths in the table, paired equal lengths, tokenization of names in real contexts, numeric label boundaries; constant suffix for the same CAP item; note/EOS closed exactly once, and LANG excludes the pending token.
- Use hand-made logits to check the source mapping, the sign of M, cancellation of a common partner-logit bias, per-permutation computation followed by averaging, the fixed CF direction, and that NaN/missing values are not filled with zero; use small synthetic results to check episode clustering, Holm, and N rounding. Do not treat A/B or the four permutations as additional samples.
- Claude is responsible for the runtime tests of EMA/mask/hook/snapshot; Codex cross-checks its raw/EMA seed, state commit, RF/RO, and sparse-injection contracts. GPU acceptance still follows §11, using the main model.
