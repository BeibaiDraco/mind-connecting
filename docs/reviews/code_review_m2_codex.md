# M2 Core Engine Review (Codex)

- Review date: 2026-09-23 (CDT).
- Code under review: `3509223` (M2); the review-claiming commit `2f1bb9e` only modifies STATUS.
- Scope: `src/mb/runtime.py`, `bridge.py`, `conditions.py`, `run.py`; checked against protocol v0.5 §5–7 and §10–11, and, following the call chain, against §4, §8, `tasks.py`, `chat.py`, `readouts.py`, `analyze.py` and the existing tests.
- Method: static review, reading the source of transformers 4.57.1 installed on this machine, running the offline tests, and temporary reproductions that do not depend on torch. No torch was installed, no model was loaded, and no GPU tests were run. Below, "implemented correctly" only means the code path conforms to the contract; numerical equivalence still requires measurement in S0′.
- This review only adds a review document and updates STATUS; it does not modify code, tests, configs or the protocol, and makes no research decisions.

## Conclusion

**M2 cannot yet be treated as an experiment engine that has passed S0′. The review found 2 blocking issues, 8 important issues and 3 minor issues.** Most urgent: resume can confuse run identity, and gates can pass even when most of the data failed. No definite implementation error was found in the core "one-tick delay" or in branch tensor copying; these correctly implemented parts must not be judged wrong along with the rest just because the tests are insufficient.

Offline test result: `.venv/bin/pytest -m "not gpu"` → **45 passed, 2 skipped**. The two skips are `test_runtime.py` and `test_bridge.py`, skipped by the module-level `importorskip("torch")`; this cannot be used to claim the bridge math or runtime tests have passed.

## Blocking

### B1. Resume first overwrites metadata, then skips results using a key that does not include config identity

**Location:** `run.py:105–121, 194–203, 308–310, 526–546`; related `conditions.py:97–116`. Violates §6 config identity, §11.14 merge protection and the project rule that results are never overwritten.

`--resume` unconditionally rewrites `config.yaml` and `manifest.json`, without reading the old manifest and checking the parameters. `RecordWriter.key()` has only `(episode_id, arm, recipient, qid, rotation)`. But the same arm name can have a different calibration, template, SCRAM seed or mask seed. `calibration: latest` is re-resolved every time, which makes it especially easy to switch to a new calibration on resume.

There are two consequences: complete old rows are skipped outright, so the results still use the old config while the manifest claims the new config; or some old rows are kept and the missing rows are filled in with the new config, producing mixed results. The downstream same-name arm hash check in `readouts._index()` can only catch some cases of the latter and cannot remedy the former. Resuming the calibration stage also overwrites `calibration_L*.pt` and `calibration.json` (`run.py:444–448`).

**Local reproduction:** Give RecordWriter a record with `status=ok, config_hash=old`, then query the same key but with `config_hash=new`; it still hits `done`. Two SCRAM arms with different `scram_seed` have the same name but different hashes.

**Concrete fix:**

1. A new run saves the resolved config, the resolved calibration path and hash, and the materials/template identity; resume compares these first and may open outputs only if they match. The original config/manifest stay unchanged, and the information for each resume is appended separately.
2. The completion key includes at least `config_hash`, and the question/input-material identity is verified; when the same logical trial shows a conflicting identity, refuse to resume, rather than just writing it as another row.
3. Restore the token IDs of existing notes, the LANG source and the donor mapping; do not regenerate shared inputs because of new batching or dependency versions. Pin the resolved result of `latest`.
4. Save calibration artifacts in a new run directory or a unique attempt path; overwriting existing artifacts is forbidden.

**Regression acceptance:** Resume with the same config fills in only missing items; changing the calibration, template, SCRAM/mask seed or question identity is refused before any file is written; check that the original files are byte-for-byte unchanged; resuming calibration cannot overwrite existing files.

### B2. G1 and Pilot A exclude failed/missing samples and then make a "pass" or parameter-selection decision

**Location:** `run.py:461–499`; call chain `readouts.py:144–161`, `analyze.py:267–288`. Violates §10's specified samples and gate procedure, and hides technical failures.

Both post functions first delete all failed records. G1 does not check for the expected 60 episodes and the required rotations; Pilot A's `require_all_rotations=True` is not passed the expected rotations, so in practice "whichever rotations remain" is taken as "all rotations". The subsequent `inner join + dropna` then excludes incomplete episodes, and the selector has no minimum completeness requirement on `n`. Smoke runs with `--limit` also run the formal post as usual.

**Local reproduction:**

- Of G1's 60 episodes, for each gate question only the 1st succeeds and the other 59 fail: `G1_pass=True`.
- Pilot A's C0 is complete, and of ONE's 16 episodes only one rotation of the 1st succeeds: it returns `ok=True`, the summary has `n=1`, and the parameter is still selected.

This is not a "fill missing with zero" problem, and the fix must not count failures as wrong answers either. The problem is that an incomplete run produced a valid gate conclusion.

**Concrete fix:** Build the expected trial set from the resolved stage config and the episode list; first complete same-config retries and the completeness check, and only then proceed to gates/parameter selection. A missing whole rotation or a missing whole episode must both be detected; when incomplete, return `incomplete` and report the number missing, rather than returning pass or freezing parameters. Smoke results are explicitly marked as smoke and produce no pass/selection artifacts that later formal stages can consume. Technical failures that remain missing at the end are reported according to the protocol, and at gates where the protocol does not specify missing-data handling, the decision goes to the PI; do not shrink the sample on your own. G1 also lists the denominator and accuracy separately for A and B, so the current pooled summary does not hide one side's failures inside the other.

**Regression acceptance:** Neither of the two examples above may pass; parameters may be selected only after the data are filled in; test separately a missing complete rotation, a missing CAP question, a missing whole episode, and a missing C0 paired item; a successful retry after a failure keeps two audit records, but the analysis selects only one valid attempt.

## Important

### I1. After normalization, the result is not written back to BF16 as the protocol requires; quantization happens after the transform and gain

**Location:** `bridge.py:70–74, 199–209`, `runtime.py:48, 179–180, 233–237`; calibration STATIC messages `run.py:430–440`. Corresponds to §6, §11.11.

The EMA is updated in FP32, and the order (EMA first, then mean subtraction/clipping/normalization) is correct. But `normalize()` returns FP32, and the mailbox explicitly stores FP32; SCRAM, mask and gain all act on this FP32 message, and only at the end is the whole injection converted to BF16 in the hook. The protocol requires the normalized result to be written back to BF16, so the current implementation amounts to `BF16(g*T(m32))`, rather than first obtaining `m=BF16(N(e))` and then applying the transform/gain. Even though the final host is BF16, these two computation paths are not equivalent. The offline message mean for STATIC likewise uses unquantized messages.

**Concrete fix:** Explicitly convert to BF16 at the output boundary of N and store that in the mailbox; the EMA's `e` always stays FP32. When a matrix multiply or norm computation is needed, promote the quantized mailbox value back to FP32, then apply the transform and gain, and finally write back in the host dtype. When constructing STATIC during calibration, use the same message-generation function, and promote to FP32 when computing the mean/direction. Do not quantize e before normalization.

**Tests to add:** Do not just assert the dtype; also check the whole order using values that BF16 cannot represent exactly; verify that `normalize(EMA(z))` and `EMA(normalize(z))` are distinguished, and that STATIC is based on the same normalized messages.

### I2. U_OPEN is actually "up to 80" stopping at EOS, and keeps feeding valid pads to finished rows

**Location:** `runtime.py:345–360`, `run.py:347–349`. Protocol §4 says generate 80 tokens; §5 requires active rows to consume actual tokens, with padding used only for the prefix.

U_OPEN's receiver uses an `argmax` without EOS masked; on hitting EOS it sets `done`, and it stops early when the whole batch is done. When the record is written, EOS is stripped, so hitting EOS on the first step can yield an empty string with `status=ok`. If other rows in the same batch are not yet done, finished rows keep consuming `pad_id`, but `step()` sets the new attention-mask position to 1; under TWO it also updates that row's message and passes it to the donor. This does not cause signal leakage between different branches, but the subsequent states of these finished rows are not a valid fixed-length generation.

**Concrete fix:** Under the current 80-token contract, mask both EOS tokens on a copy of the logits at every step, clearly distinguish "output tokens selected" from "tokens consumed", and save exactly 80 output token IDs. Do not append valid pads for finished rows; when there is no need to advance the state past the 80th output, do not run a useless forward. If the PI wants "up to 80, may stop early", the protocol and the rule for freezing active rows must be written down first.

**Tests to add:** each of the two EOS tokens being the maximum, EOS on the first step, EOS appearing at different times in different branches; check the length, that the original logits are unchanged, the donor's per-step advance, and TWO's feedback.

### I3. Non-finite outputs are marked as success, and exceptions in the P/C phases leave no failed-trial records

**Location:** `run.py:265–284, 318–350, 105–113`, `runtime.py:338–344`. Corresponds to §8's retry rule for technical failures and §6's failure log.

When `run_readout()` returns normally it marks the whole batch `ok`, without checking whether the logits, logprobs and mass are finite. NaN/Inf propagation in PyTorch usually does not raise; `json.dumps` also writes out `NaN`/`Infinity` by default. On the next resume these records hit `done` and are not retried. Although `readouts._ok()` makes some scores NaN, it cannot correct the success status or trigger a rerun. Exceptions in the P note, prefill, C reflection, a missing STATIC vector and so on happen outside the try, so they abort the run without producing failure records for the affected trials.

**Local reproduction:** A row with `status=ok` that contains NaN label logits is treated by RecordWriter as a completed item.

**Concrete fix:** Validate the shape and finiteness of the required outputs per row; record non-finite results as `failed` with the phase, reason and attempt id. Retry automatically once with the same config; if it still fails, save the missing status, without filling zero. P/C exceptions also record the corresponding episode/arm and the affected readouts, keeping the parts that succeeded; only the failed rows should be retried, and healthy rows in the same batch must not be treated as failures along with them. JSON output uses strictly finite values; values that cannot be represented become null, with the error reason kept.

**Tests to add:** a single NaN row in a batch, a non-label logit somewhere in the full vocabulary being Inf so that mass is non-finite, prefill/C exceptions, success after a first failure, two consecutive failures, and the retry status on resume.

### I4. ticks.jsonl is not a per-tick log, and energy-matching failures in the R phase are lost entirely

**Location:** `runtime.py:132–145, 227–251, 333–359`, `bridge.py:140–166`, `run.py:289–299`. Corresponds to §6 logging and §7 extension B.

Currently each episode/arm writes only one row with the C-phase mean injection ratio/cosine, plus the two reflection texts. There is no per-tick donor, token ID, message norm, or snapshot/branch id. R calls `injection()` without passing stats, and `TransformResult.unmatched` is discarded; so total energy matching can fail at some question-reading tick without any record. The energy ratio is computed but not saved, and the amplification factor is not returned. The mask coordinates, the calibration's high-magnitude/high-energy coordinates and their actual energy share are not written to disk either.

LANG's source is correct in memory, but the token IDs, length and content hash of the disclosed source are not saved; whether the two disclosure versions are identical cannot be directly re-verified from the existing result files. Although the reflection text is saved, there are no counts of rule/secret-word occurrences as the protocol requires.

**Concrete fix:** Connect C/R/open generation to the same per-tick logging interface, containing at least the fields listed in the protocol; R must carry qid/rotation/recipient/snapshot id. Save each active receiver's match flag, actual energy ratio and amplification factor, and summarize the failure count in the result row; failed ticks are kept, without redrawing the mask or deleting samples. Per layer, save once the coordinate permutation, seed, hash and the high-energy coordinate audit; LANG saves the original disclosed token IDs, the source-trajectory hash, the actual length and the counts. Averages can be summarized separately but cannot replace the raw log.

**Tests to add:** Create an unmatchable event that occurs only in the R phase, and confirm that both the tick and the result row are traceable; a zero norm must be recorded as zero and not counted as unmatchable. Check that tagged/untagged point to the same source token sequence.

### I5. Template/calibration identity is not enough to identify the actual input, and a wrong-layer calibration can be loaded silently

**Location:** `run.py:71–87, 194–196, 527–535`; related `conditions.py:108–116`.

`template_hash()` hashes only the user text of one reference episode; it does not include ChatML token boundaries, the tokenizer files or the actual suffix token IDs, and covers only the CAP question drawn for the reference episode. If the token concatenation rule is changed, the hash may stay the same. Although the manifest additionally has `cap_bank_hash`, it does not enter the records' config identity or the merge protection. The saved `config.yaml` is the raw input YAML, not the full config after filling in defaults and resolving `latest`.

Calibration files are placed into `self.cal[layer]` by the key of the config dict, without verifying `cal.layer == layer` inside the file. If an L12 file is configured under key 18, the dimension is 2560 in both cases, and L12's statistics/STATIC will then be used silently at L18. Calibration files also do not record and verify the model, tokenizer/template, split, sample size and completion status; `latest` selects merely on the existence of `calibration.json`, and may select a `--limit 2` smoke calibration.

**Local reproduction:** Changing `chat.IM_END` only in a temporary Python process changes the actual suffix tokens while `template_hash()` stays the same; no code on disk was modified.

**Concrete fix:** Save the canonicalized resolved config; include in the identity the chat-token construction version, the tokenizer manifest, the full question bank/template family and the input-material hashes. The calibration bundle carries a source manifest; on load, verify the layer, dimension, dtype/finiteness, model/template/material identity and whether the stage completed; formal stages reject smoke calibrations. Explicitly distinguish "arm parameter identity" from "run/material identity"; both take part in resume and merge verification.

**Tests to add:** Changes to ChatML/tokenizer/non-reference CAP questions change the corresponding identity; wrong-layer files, calibrations from a different model/template, and incomplete or smoke calibrations are rejected before model inference. The same valid config has a stable hash after resolution.

### I6. ArmConfig accepts invalid parameters that can lead to no connection or a wrong connection

**Location:** `conditions.py:40–61, 72–78`, `runtime.py:100–101, 154`, `bridge.py:127–131`.

Checking only `gain <= 0` does not stop NaN. `ArmConfig('ONE', gain=nan)` is valid, while in `Plan.writes` `nan > 0` is False, so in the end nothing is actually written, yet the output is still labeled ONE. `k=0`, negative values or values above d raise no error; Python slicing produces an empty mask, an unexpectedly large mask, or truncation; `mask_direction='tow'` is also valid and silently becomes one. `layer=0` indexes the last layer, while the record still says 0. recipient also has no enum/non-empty/deduplication check.

**Local reproduction:** NaN gain, k=0, a misspelled direction and layer=0 are all accepted by ArmConfig.

**Concrete fix:** At config entry, validate that gain is finite, the gain range for valid conditions, integer layer/dimension and the protocol's allowed sets, the direction enum and the recipient set; after the model loads, check the layer/d upper bounds again. Likewise check the finiteness of the STATIC vector and the calibration contents. Reject combinations of MASK with RF/RO that the protocol does not allow, rather than relying on an implicit fallback.

**Tests to add:** NaN/±Inf, layer 0/out of range, k=0/negative/out of range, and invalid direction/recipient must all raise informative errors; v2 branches continue to explicitly report the contract as incomplete.

### I7. A single truncated trailing JSON line makes resume completely unable to start

**Location:** `run.py:109–114, 120–125, 457–458`.

Records are flushed/fsynced per batch, so a process interruption or a failed disk write can still leave half a JSON line. On resume, each line is passed to `json.loads()` without protection; even if the history before it has many usable rows, it errors out right at the truncated trailing line. This is exactly the failure scenario that resume needs to handle.

**Local reproduction:** Appending `{"episode_id":` after a complete line makes RecordWriter initialization raise `JSONDecodeError`.

**Concrete fix:** Use an append journal with commit boundaries, or immutable attempt shards. Resume accepts only complete records; when a trailing fragment is found, keep it as is and log a recovery event, writing the new attempt to a new shard, and do not silently delete the original evidence; a corrupted middle line should cause an explicit stop that points to its location. The analysis loader uses the same recovery rule.

**Tests to add:** Cover separately a complete trailing line without a newline, a half trailing line, a complete fsynced batch, and a corrupted middle line; after resume, no successful trial is lost or duplicated.

### I8. MISMATCH's donor mapping depends on --limit, which changes the meaning of the same trial

**Location:** `run.py:197–198, 258–260`.

The donor is taken as "the next one, wrapping around" from `self.episodes`, which has already been truncated by limit. With the full 4 episodes, episode 1's donor scenario comes from episode 2; with `--limit 2` it becomes episode 0. None of the episode/arm/config hashes express this change. Resuming the full set after a smoke run mixes different pairings into the same condition; `--limit 1` makes an episode its own donor, which triggers an exception in `make_donor_variant()`.

**Local reproduction:** Applying the current index expression to a set of 4 episodes and to its first 2 respectively, episode 1's donor is `review-0-00002` and `review-0-00000` respectively.

**Concrete fix:** First determine and save a fixed donor-scenario mapping on the stage's full episode list, then select the receivers to run according to limit. Each MISMATCH record saves the donor's source episode/material hash. If the full stage itself has fewer than two episodes, error before running.

**Tests to add:** Batching, limit and resume do not change the donor of the same episode; a smoke run with a single receiver still takes a different donor from the full list.

## Minor

### S1. State does not fully express the phase, logical tick and completion status required by the contract

**Location:** `runtime.py:41–79, 306–327`. Corresponds to §5 snapshots.

The existing copies of KV, mask, valid positions, pending, logits, mailbox, FP32 e and token history are real copies; but State has no phase, logical tick or completion flag, so callers can only infer them from context. Bridged branches for FULL/RO copy the whole pair; RF and bridgeless readouts copy only the recipient, which does not literally satisfy "every branch clones both sides". Currently RF does not advance the donor at all and cannot write back to the snapshot, and no numerical contamination from this was found, so it is not escalated to a causal error.

**Concrete fix:** Add the explicit state fields and copy them, and assert at the R entry that the state comes from the C48 snapshot; branches hold the whole pair's state plus active-row flags, or else the implementation docs spell out, and tests cover, the optimization of copying only active rows and the representation of the frozen donor. The snapshot id/tick in the logs use these fields, rather than being inferred ad hoc.

### S2. The "one token per tick" shape check runs only when writing is actually enabled

**Location:** `bridge.py:199–219`, `runtime.py:195–203, 206–225`. Corresponds to §5, §11.7.

The hook only uniformly checks that the input is three-dimensional, and requires length 1 only when `write_enabled`; for the output it only checks that it is a Tensor, with no separate prefill/tick output-shape assertion. An erroneous multi-token call under C0/RO/RF might capture only the last position without failing promptly. The Engine's normal call path does pass one token, and no actual multi-token consumption was found.

**Concrete fix:** Explicitly distinguish prefill/tick, and validate the input and output shapes and valid length for each; the single-token assertion does not depend on whether write is enabled, and prefill stays read-only. Test tuple outputs, multi-token ticks, wrong batch/dimension, and prefills of different lengths.

### S3. Readouts are grouped by length, not bucketed by question type and CAP ID

**Location:** `run.py:301–315`. Corresponds to §5 batching.

The group key is only `(n_ticks, generative)`, which puts NOW/NOW_R/U_CLOSED of the same length, or different CAP IDs, into the same batch. Equal length by itself is enough to avoid padding in the middle of R, and rows are independent, so this implementation was not found to directly cause signal crosstalk; but it does not follow the protocol's specified bucketing by same question type/CAP ID.

**Concrete fix:** Add qid to the group key; for CAP add `cap_item_id`, and keep the equal-length assertion. Treat this as an added test of the batching contract; do not describe it as cross-row contamination having been found.

## Verified correct paths and interpretation boundaries

| Check | Conclusion and code evidence |
|---|---|
| Prefill reads the seed only | `runtime.py:183–203` turns off writing and clears the injection; after left padding, every valid final token is in the last column; `bridge.py:216–219` reads the raw block output, `ema=z0.clone()`, then normalizes. C1 is selected from a copy of the logits after masking EOS. For the dtype exception see I1. |
| One-tick delay and commit order | The C loop first builds the injection from the old mailbox, then runs the forward for the whole batch, and finally `advance()` updates e/mailbox/pending together (`runtime.py:253–259, 284–292`). This tick's post-hook output cannot be read by another row in the same tick. |
| C48 snapshot/C49 pending | Each step first consumes pending, then updates the next pending; after 48 steps consumed is exactly C1…C48, and C49 has not entered the KV. The runner treats state as the snapshot; readouts select/copy rows internally and do not modify the source state. |
| R step 1 | `run_readout():330–335` overwrites the recipient's pending with the first suffix token; the first item of `chat.readout_suffix()` is IM_END. The donor keeps its own pending, so on the first step it consumes C49, and the injection still comes from the C48 mailbox. |
| R donor and TWO feedback | The FULL/RO bridged path is reordered into recipient/donor pairs; at each step the donor continues reflecting using the updated pending, and TWO's two-row donor mapping is still `i ^ 1`. When B is the recipient, roles are reordered too, and the direction is not reversed. e is not reset between C and R. |
| RF | C writes normally; R runs only the receiver, with gain 0 and `update_messages=False`. The donor does not run at all, and the original donor's KV/e/mailbox/pending are all untouched. RF was not mistakenly implemented as the donor still running idle. For the contract gap in representation see S1. |
| RO | `run.py:284` only sets C's write to False; `run_reflection()` still updates e/mailbox at every step. R takes FULL's active-pair path. |
| STATIC | `bridge.py:88–107` correctly computes the rule-conditional mean minus the overall mean, scales by `sigma_in*v/RMS(v)`, and judges it unusable below 0.01 sigma; `make_plan()` writes only B's rule direction into A, and `injection()` multiplies by gain directly, without applying an extra EMA to STATIC. For input-message precision see I1. |
| Calibration sampling and EMA | `run.py:408–440` clears the hook records from the note period and collects z0+C1…C48; the statistics use only C2…C48, excluding the seed/first C token, and everything captured is at the last valid position after left padding. raw/EMA share the same set of statistics; the EMA is recursed continuously offline starting from z0, and normalized messages are not treated as raw z. |
| SCRAM/mask/energy-matching math | Q has a fixed seed and is orthogonal; the row vector `m@Q.T` corresponds to Qm. The mask comes from the first k coordinates of the same permutation, and sorting does not change the support set. A zero norm outputs zero; below the 1e-6 relative threshold it is flagged unmatchable, without silently amplifying. Normal matching preserves the norm, and coordinates outside the mask are zero. For the gaps in parameter checks and logging see I4/I6. |
| select_rows deep copy | The KV's K/V and all existing state tensors go through `index_select(...).clone()`, and history is copied item by item. Checking `DynamicCache.__init__`/`DynamicLayer.update` in the local transformers 4.57.1, their reconstruction does not re-alias these copies to the original state; crop is not used. Dynamic regression tests should be added, rather than judging it a shallow copy just because the GPU was not run. |
| Left padding/position ids | Prefill explicitly uses `cumsum(mask)-1` and clamps; next_pos takes each row's valid token count. A tick keeps the left-side mask, appends a valid position and uses per-row next_pos. The underlying default cache_position tracks the physical KV length; its differing from the explicit RoPE position_ids is not a bug. A separate no-pad comparison still awaits GPU testing. |
| FP32 logits/labels/mass | `runtime.py:169–172, 337–343` converts the post-final-norm hidden state and the LM head weights to FP32 and recomputes the logits, then does log_softmax over the full vocabulary and extracts IDs 16–19; mass is the sum of the four labels' full-vocabulary probabilities, not wrongly normalized to always equal 1. This Qwen3 head has no bias. Greedy uses logits computed natively in BF16, while readouts compute FP32 separately. For the missing non-finite check see I3. |
| CF donor and A's input | Donor B regenerates the note and prefill using the episode with the B/spare rule and word swapped; A always uses the original ep's prefix. CF's S1/S2/codename/physical order of candidates are unchanged; the existing task tests and this offline check confirm that all R suffixes are unchanged. |
| Meaning of A's questions under MISMATCH | Although `views` points to donor_episode, the helper changes only S1 and the B/spare assignment, keeping the original S2, A/Robin, CAP, codename and the physical order of the words; A's prefix is still built from the original ep. So A's BEH question does not mistakenly use another S2, and the R tokens are unchanged; the partner label pointing to the actual replacement donor content is what scoring requires. For the stability of which external donor is chosen see I8. Do not use the whole donor_episode directly as A's private prefix. |
| CF scoring direction | CF's `label_meaning` swaps partner/unused along with the assignment; this is a factual description; G2 must use the difference over fixed physical r0/r1, and cannot take the ordinary `ACC_RULE` directly for CF-ONE. Records already have the `options` and cf_r0/r1 fields; `readouts.content_cf_score()` scores by physical candidate and checks the question-stem hash, and no direction reversal was found at present. Future G2 wiring must use each episode's own r0/r1. |
| LANG source | `ensure_c0_reflections()` takes B's `consumed_matrix()`, which is exactly C1…C48 and excludes pending C49; both versions are decoded from the same cached token IDs, then given a source prefix, and placed after P and before C; B's input does not contain the disclosure text. For the missing source persistence see I4/B1. |
| Per-result identity fields | The layer/gain/message_form/tau/write_operator/calibration_hash/mask_hash/k/energy_mode/condition/readout_mode/model_revision/template_hash/config_hash listed in the protocol are all written, as are rotation, the actual question length, the four labels' logits/logprobs/mass, and status/reason. The problem is the coverage of the identity, its verification and the failure semantics, not that these fields are missing altogether. |
| v2 protection | `ArmConfig.write_operator != add` and `apply_transform(interpolate/kv_share)` both raise `ContractIncomplete`; the undefined v2 interfaces are not silently executed. |

## What tests/test_runtime.py can catch, and what is still missing

There are currently only **5 GPU test functions**, covering part of the mechanical behavior of the C phase. `test_bridge.py` has another **7 torch-dependent math tests**, which were also not run on this machine. There is no `test_run.py`; neither of the two blocking issues in this review is within the existing automated coverage.

| Existing test | Can catch | Cannot be used to claim a pass on |
|---|---|---|
| `test_prefill_capture_and_notes` (53–56) | Mailbox shape; pending is non-EOS on the natural example | That prefill does not write; that z0/e0/mailbox values agree; that C1 is the same across conditions; that both EOS tokens are masked without altering the original logits. The name contains notes, but it does not verify note EOS/turn closing. |
| `test_zero_gain_equals_plain_forward` (59–95) | Final logits of C0 with the hook versus without the hook on the same path; the per-step reference greedy agrees with the engine's consumed path | The max difference/top-2 margin at each tick under teacher forcing, statistics of independent free-generation trajectories, forcing the path through a zero-valued injection. Both sides share the same padding construction, so a shared padding error cannot be detected. The tolerance `1e-2` is hard-coded, with no S0′ calibration artifact. |
| `test_direction_and_delay` (98–126) | ONE's mailbox direction; changing a donor token does not affect A on the same step and does affect A on the next step | TWO's simultaneous two-way commit, feedback while reading the question in R, an EMA pulse across ticks/C→R, B as the receiver, multi-pair/repeated branch mappings. |
| `test_snapshot_continuation_and_branch_isolation` (129–146) | consumed/e/mailbox are essentially consistent when the C phase continues running; the sum of K in the first three layers does not change | Independence of K/V in all layers, pending, logits, mask, next_pos and history; equal numerical sums are not proof of no aliasing. There is also no check of cross-contamination between two different readout branches on the same pair of instances. |
| `test_readout_shapes_and_label_mass` (149–157) | Shape of the four labels in the C0 readout; mass greater than 0.5 | No bridged FULL/RF/RO readout is run at all; it does not verify R's first step, the donor's advance, the FP32 recomputation, the correct label IDs, mass's full-vocabulary denominator or U_OPEN. |

**Acceptance cases recommended to add first (this review does not modify tests):**

1. **Runner tests that do not need torch.** Using a temporary directory and a fake Engine/records, cover B1/B2/I3/I5/I7/I8: resume identity, bad trailing lines, failed attempts, the expected trial list, partial rotations, smoke runs not publishing gates, stable donor mapping. Separate the scheduling/recording/completeness logic from the GPU execution interface, meeting §10's requirement for offline state-machine mock tests; do not install torch on the Mac.
2. **An exact C→R event trace.** On the GPU, set identifiable pending/mailbox/e values in the C48 state and capture tokens/injection/commit step by step: the receiver's first item is IM_END and the donor's first item is C49; the recipient's C49 never enters the KV; the donor then generates continuously; TWO's question-reading message returns to the donor only at the next tick. Test both A and B as recipient.
3. **RF/RO.** Under RF, verify that the donor's full state is byte-for-byte unchanged, there are no R writes, and the mailbox/e are frozen; under RO, C has no writes but e/mailbox update with the pulse, and R's first tick actually uses the new C48 mailbox; clearly distinguish this from a wrong "RO turns off capture" implementation.
4. **Full branch isolation.** From the same pair, derive branches for multiple questions, multiple rotations and A/B at the same time; modify every kind of field and all layers' K/V in one branch, and assert that the source snapshot and the other branches are unchanged. After restoring, check pending, raw logits, the full KV, mask/positions/e/mailbox/history; swapping the execution order does not change the results.
5. **A real padding comparison.** Construct prefixes of definitely different lengths and compare the valid hidden/logits/seed/generation path when run alone without pad versus left-padded with mixed lengths; include mixed long and short batches containing LANG. At each R step the new mask column must be 1 and exactly one item is consumed; padding in the middle of the suffix is forbidden.
6. **Bridge order and dtype.** Make the calibration examples deliberately trigger the clip/RMS nonlinearity, to catch errors such as normalizing before EMA, quantizing too early, or applying gain before normalization; τ=1 equals raw, and at τ=8 a pulse decays by a factor of 7/8 and is injected one tick later. For STATIC, test the vector scale, the unusable threshold, the injection gain and the absence of an extra EMA together; the BEH manipulation check is listed separately, with failures kept.
7. **Strengthened math tests.** The existing single-dimension spike test may pass even with clipping deleted (RMS normalization erases the absolute magnitude of a single axis). Check the exact clip result with multi-dimensional, non-proportional vectors. For energy matching, test a zero vector, exactly at the threshold, slightly below the threshold, and normal scaling; verify R's unmatchable records. What is checked outside the mask is "the injected increment is zero"; do not mistakenly require the host coordinates to be unchanged after the block.
8. **Readouts.** With a fixed hidden state, compute the four logits/logprobs/mass using an independent FP32 LM-head reference; check the dtype, IDs 16–19, the full-vocabulary denominator, and that the original logits are unchanged. Test the masking by artificially making each of the two EOS tokens the maximum, rather than relying on whether a real example happens to generate EOS. For U_OPEN see I2.
9. **Runner condition wiring.** Using a fake Engine that records input tokens, verify that CF rebuilds only B, with A's P/note/R tokens unchanged; that MISMATCH swaps only the donor's S1 while A's S2 is unchanged; and score CF separately in the fixed r0/r1 direction. LANG must cut the consumed token IDs, pending uses a unique sentinel to ensure it never enters the disclosure, and the tag/untag sources are strictly identical.
10. **A real merge-protection test.** Currently `test_conditions.py` only checks whether the hash changes; it does not test refusal to merge records. Same-name arms with different hashes must be refused; comparisons between different arms must also verify that the shared model/template/material identity agrees (allowing the arm parameter differences the protocol specifies), and must not be concatenated automatically on name alone.

The floating-point tolerance of §11.1 still has to be calibrated in S0′ on a rented GPU with the fixed 4B and fixed software/hardware, and saved; the existing hard-coded allclose tolerance should not be taken directly as a frozen tolerance. This review does not recommend changing the model or running the model locally.

## §10 procedures not yet wired up (distinct from the implementation errors above)

Currently the configs cover only G1, calibrate and Pilot A; `POST` likewise has only G1 and the Pilot A selection. `analyze.py` already has pure functions for Pilot B selection, sample size and so on, but the runner has not wired in Pilot B/C, per-episode G2, or the full scheduling and freeze verification for the formal/diagnostic/extension stages. `run.py` being "able to execute arbitrary arms" must not be taken to mean these stages are done.

What must be filled in later, within the established protocol: building the next stage's config from the selection artifacts; checking that sample splits are mutually exclusive; parameter selection accepting only ACC/CAP/format, with N determined independently after freezing; G2 using fixed r0/r1 per episode; the formal stage verifying protocol-v1 and the SHA list; each layer's extension using its own frozen g*. These are execution wiring, and the fix should not be used as an occasion to change questions, metrics or parameter-selection rules. The current code also does not create the required `log.txt` or persist the generator balance report; these should be added along with the run artifacts.

## Summary of local reproductions

The temporary script imports only the offline functions of `mb.run`, `conditions`, the tokenizer and the pure scoring functions; files were written to the system temp directory and deleted on exit. Observed:

```text
resume_changed_hash_skipped = True
partial_tail_resume = JSONDecodeError
g1_1_success_59_fail_pass = True
pilot_1_episode_1_rotation_selected = True
pilot summary: n=1, acc_increment=1.0, cap_drop=0.0, label_mass=0.99
chatml_token_change_template_hash_unchanged = True
nan_gain / zero_mask / typo_direction / bad_layer = accepted
nan_status_ok_considered_done = True
CF / MISMATCH: A's R token sequences stay unchanged for 4 episodes × all rotations
MISMATCH episode 1: full donor=episode 2; limit2 donor=episode 0
```

Recommended fix order: first B1/B2 and the failure/identity handling, then the key runtime contract tests and I1/I2/I4; once the offline tests pass, run S0′ on the 4B, and only after numerical verification is complete let the results of G1, calibration and the pilots feed into later stages.
