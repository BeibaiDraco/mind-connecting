# v2 / v3 Static Review and Recomputation from Raw Records (Codex)

Date: 2026-09-24, about 20:34 UTC / 15:34 CDT. Review baseline: `42d6d97`; v2 run baseline: `protocol-v2` (`29108fb`).

## Conclusion and order of handling

**The completed v2 main results can be independently reproduced from the raw records; no evidence was found that v3 source code got mixed into these runs.** The main implementation of the memory link agrees with the contract, and static checking found no error that would require rejecting the current v2 data. No torch was installed on this machine, and no GPU job was connected to, synced, modified or started.

Items that need handling, ordered by impact:

1. **R1: The "merging" interpretation of B′ needs to be clarified before freezing.** The current metric pairs the answers of two independent FULL measurement branches, and cannot be taken directly as both sides converging synchronously within one shared evolution.
2. **E1: The queue scripts continue after a stage fails, and write ALL DONE.** This is a reproducible engineering problem; later judgments of completion must check each run's completeness, not just the end marker.
3. **R2: Neither a positive nor a negative T3 result is enough to settle a unique mechanism directly.** First check the note, content access and attention in the actual donor prefix, then give a limited interpretation.
4. **E2: A zero-variance B′ signal yields `go=true, N=null`.** This is a definite boundary error and should be fixed before the B′ signal results are consumed.

These are review opinions, not research decisions made on the PI's behalf. The frozen protocol, experiment implementation, configs, existing reports and raw data were not modified; no interruption of the current experiment was requested. The research adjustments suggested below must be decided by the PI and then implemented by the agent responsible for v3.

## R1 — Handle first: two independent FULL branches are not a synchronized paired outcome

Location: `src/mb/runtime.py:520–550`, `src/mb/run.py:1397–1422`, `docs/protocol/PROTOCOL_V3.md:21–49`.

The runtime clones the whole pair's state separately from the C48 snapshot:

- The branch measuring A: A consumes the question, B continues reflecting, and the two remain connected.
- The branch measuring B: B consumes the question, A continues reflecting, and the two remain connected.

`pair_outcomes` then pairs the physical-rule answers of these two branches by episode, question type and rotation. For KV-ALL / KV-PC, the question itself and the post-question state can influence the partner through the bridge and then feed back; the R trajectories of the two branches differ. So "two independent probes arrive at the same rule" is the accurate operational definition, while "on one shared trajectory both sides chose the same rule at the same time" is not what has been observed so far.

This is not an implementation error in the v1 FULL contract; the problem is that when v3 promoted the readout, originally used to measure the two sides separately, into the "merging" main outcome, it did not account for this difference. Nor can the reversed B_K result be explained, on the old diagnostics alone, as "simply because B adopting A was missed": that explanation is currently a new hypothesis, and the old diagnostic's KV-ALL TWO also had a CAP drop (A 0.875, B 0.881).

Recommendation: before freezing, make explicit which estimand is kept. If the existing readout is kept, restrict the name and conclusions to "the paired-answer agreement rate of independent FULL probes". To test state convergence at C48 or synchronized choice on the same trajectory, diagnostics such as a link-cut readout / synchronized two-sided question reading need to be prespecified separately; they measure different things, and the main metric should not be swapped arbitrarily after seeing results.

In addition, `converge` counts cases where both sides chose Robin or unused, while `a_adopts + b_adopts` does not. This implementation fits the broad definition of "same physical rule"; the report must break out the proportion where both chose a third rule, to avoid interpreting the whole agreement rate as "one side adopting the other".

## E1 — P1: The drivers have no reliable success boundary

Location: `scripts/run_formal_v2.sh:17–20`, `scripts/run_v3_pilots.sh:14,22–25`, and `src/mb/run.py:1611–1623`.

Both drivers use `set -uo pipefail`, go on to the next stage after running `mb.run` without checking the return code, and finally write `ALL DONE` unconditionally. v3's wait condition also accepts v2's `ABORT`, not only successful completion. A separate, independent problem: when trials are still missing after retry, `mb.run` writes an incomplete status but still returns 0.

Local reproduction: put an untouched `run_formal_v2.sh` in a temporary directory, create empty configs and an empty activate, and have `.mb_env` provide a stub: the freeze verification returns 0, and every `python -m ...` returns 7. No model or real experiment was started. Result: all four stages kept running, `ALL DONE` appeared, and the driver ultimately returned 0.

The local Bash 3.2 also displays the return code in `echo "[$(stamp)] END ... exit=$?"` as 0; `false; echo "$(true) exit=$?"` reproduces this on its own. Whether the GPU machine's Bash behaves the same on this expansion detail was not verified, so this extra local phenomenon must not be treated as something that has happened on the GPU. The problems of not checking the return code, continuing unconditionally and ALL DONE, however, exist directly in the script's control flow.

Impact: the watcher / v3 continuation cannot use ALL DONE to prove the preceding data are complete; anomalies may go unreported while later stages keep consuming compute. This does not affect the main stage and diagnostics, whose completeness was independently verified in this review.

Recommended for later versions: save the exit status immediately; make any nonzero status an explicit ABORT; also require every stage's `run_status/completeness` to be complete before emitting a success marker; clearly distinguish "finished successfully" from "failed, but independent follow-up jobs are allowed to run". The fix goes only into the corresponding new directory/version; **do not sync code to the still-running frozen v2 directory for this**.

## R2 — The interpretation of T3 must be narrowed, and the actually exposed content checked

Location: `docs/protocol/PROTOCOL_V3.md:68–84`, `src/mb/tasks.py:350–400`, `src/mb/run.py:479–505`.

T3 correctly keeps A's prompt unchanged, and rewrites B's rule attribution, note prompt and reflection prompt. The existing implementation is valuable for testing "whether the effect depends on the original second-person prompt". But the following interpretations are still too strong:

- If the third-person condition still has a large effect, that can refute the narrow interpretation "it depends entirely on the original You were assigned wording"; it cannot uniquely prove "memory-source confusion". The replaced prefix still contains the instruction to choose a plan, the assistant identity position, and the model-generated note.
- If the third-person condition is near zero while ACC is high, that supports "the effect is sensitive to wording/identity framing", but cannot uniquely prove the model is just executing a second-person instruction. The rewrite simultaneously changes the prefix tokens, length, RoPE positions and note, and similar ACC does not mean all transmitted content is the same.

It is especially necessary to distinguish **the prompt being written in the third person** from **the entire readable prefix staying in the third person**: `generate_notes` freely generates up to 48 tokens, which are then put back into KV-P as is; the code does not check whether the note contains `I / my / you / your` or restates the rule as its own. The shared system prompt is also still in the second person, but it does not itself assign a specific rule, so the control cannot be judged a failure on that basis alone.

Recommendation: first do a full wording and content check of the `notes.jsonl` already generated by T3, reporting how often they actually contain the own/partner rule and codenames, and report ACC, CAP, format, partner attention mass and prefix length. Do not delete "unwanted" notes or episodes post hoc based on the results. If the generation constraints or materials need to change, that requires PI approval and should run as a new pilot on a new split; the definition of results already in the queue must not be rewritten.

## E2 — P2: Zero SD is mistaken for no usable SD

Location: `src/mb/run.py:1483–1485`.

`post_pair_signal` keeps only comparisons with `sd > 0`; if every episode's difference is exactly the same and significantly nonzero, the signal threshold passes but the SD list is empty, giving `N=null`. When SD=0 the protocol's formula should still give the lower bound N=300.

Using the record generator in `tests/test_v3_post.py`, build 16 complete episodes: under ONE all keep their own rule; under TWO A adopts B in all of them. The actual output is:

```json
{"go": true, "mean": 1.0, "sd": 0.0, "ci90": [1.0, 1.0], "N": null, "mde_at_N": null}
```

Recommendation: allow a finite zero SD into `plan_sample_size`; distinguish "zero variance" from "no paired data". Adding this boundary test case is enough; the model does not need to be rerun. The problem is in post-processing newly added in v3 and does not affect the v2 confirmatory results.

## Verified implementation and analysis

### KV contract

- Prefill does not activate the memory link; each tick excludes the partner's newest column and masks its padding.
- The P / C / ALL split uses the physical cache boundary `c_start`; the validity of left padding is determined by the attention mask.
- It uses the partner's existing rotated keys without rotating them again; under ONE only A receives, under TWO both sides receive.
- KV-PC adds separate log weights for prefill and C/R; a zero live weight reducing to the P path is reasonable.
- The receiving output uses `own + beta * (partner - own)`; the inactive path goes straight through the original SDPA. With positive weight, the own output still uses BF16 SDPA while the weights are computed in FP32, so "exact" should be understood as a mathematical decomposition, not bit-for-bit identity with a different joint-softmax kernel.
- `select_rows` copies the cache and the entire state; the context is cleaned up in `finally`; the layer-count assertion can detect the attention implementation silently failing.
- Existing GPU tests cover off/zero weight, direction, delay, the C range and PC reduction. This review only read the tests and **did not run GPU tests**; a direct numerical oracle with finite, nonzero weights on both segments is a test that could be added, not a defect established in this review.

### Thresholds and point selection

v2's C → ALL → P group order, choosing in each group the largest ACC that passes the engineering checks and then testing strength, STATIC's nearest point/ties broken toward the smaller gain, the direction/effect-size/90%-interval thresholds for the first main comparison, within-study Holm, and episode aggregation all agree with the frozen protocol. v3's two-sided engineering threshold for TWO and its selection of the largest live weight also follow the draft. No selection of KV parameters by ranking on M was found.

A_K's STATIC is explicitly unmatched, so +60.3 supports an overall difference between these two specific interventions and cannot be called an interface difference at equal content strength; K* itself also has no live feedback loop. Even if A′ matches on ACC, it can only be called "matched within the tolerance of this ACC metric" and cannot be extended to equal total information; if `matched=false`, it should first go to the PI for a decision, and strict matching must not still be claimed as a success.

C's `self − untag` is negative and has been reported as opposite to the prespecified direction; it cannot be rewritten as supporting a monotonic "source-label gradient". A mean of `stranger − tag` near zero does not prove the two conditions are equivalent.

## Independent recomputation from raw records

The following completed runs on the SD card were read, without writing to their directories:

- `20260924-172152_v2_main_confirm`: 92,400 ok, 0 failed; completeness recomputed as 92,400 / 92,400, none missing.
- `20260924-192633_v2_main_diag_confirm`: 2,880 ok, 0 failed; completeness recomputed as 2,880 / 2,880, none missing.

An independent script computed M directly from each record's `label_meaning` and raw logits, aggregating over rotations first and then pairing episodes; it did not call the project's scoring, bootstrap or Holm functions. Checked against the saved `contrasts.json`: the means, SDs, 10,000-resample bootstrap intervals and within-study Holm p for all six main comparisons agree.

| Study / comparison | Mean | 95% interval | Episodes |
|---|---:|---|---:|
| C: untag − tag, M_NOW | 26.634419 | [24.499720, 28.782585] | 600 |
| C: self − untag, M_NOW | −19.471350 | [−21.517439, −17.359205] | 600 |
| C: stranger − tag, M_NOW | −0.019677 | [−0.267661, 0.244561] | 600 |
| D: K* − C0, M | 55.834499 | [54.988660, 56.631330] | 600 |
| D: K* − C0, M_NOW | 54.709951 | [53.713213, 55.631596] | 600 |
| A_K: K* − STATIC, M | 60.287029 | [59.280485, 61.250957] | 600 |

G2 was rescored from the fixed physical candidates, verifying that the original and CF question hashes are identical, 60 episodes with 4 rotations each: rule mean 38.774985, one-sided 95% lower bound 34.321522; word mean 35.577571, lower bound 32.090625. Consistent with the report.

Supplementary description: weighting each episode's two rotations equally, the proportion of K*'s START answers choosing the partner's rule is 95.75%, and for NOW 93.50%; under C0 both questions choose the own rule 100% of the time. K*'s ACC-rule answers name the partner's rule 70.08% of the time, C0's 2.83%. This does not treat rotations as independent samples for inference, nor misread ΔM=55.8 as a percentage.

The local recomputation script and outputs are left in the ignored directory `scratch/codex-v2-v3-audit/`; no raw data are committed. The recomputation only confirms the chain from records to statistics tables; it is not equivalent to rerunning the model or proving the mechanistic interpretation.

## Freeze and run evidence

- All entries in `FREEZE_protocol_v2.txt` match the SHA256 of the files under the `protocol-v2` tag.
- Computed independently from `src/mb/*.py` under that tag using the `source_hash()` algorithm: `8107b926ee212a72`.
- The `identity.json` of the main stage, the diagnostics and the then-synced `20260924-193405_v2_bal_confirm` all record the same source hash; their `config.yaml` is word-for-word identical to the frozen version; none has a `resume_log.jsonl`.
- The Git commit in all three manifests is `29108fb`, with `dirty=true`. The specific reason for dirty was not verified in this review; that flag alone cannot be used to assert that the experiment code was changed, and the independent hash checks of source and config give more specific evidence.
- Local main has moved on to v3, so the runtime, task templates and so on differing from the frozen v2 files is expected. What was verified here are the tag and each run's records; **there is no claim of having checked the GPU's current directory online**.
- The latest entry in E's local mirror log read in this review is 20:25 UTC, chunk 4 (zero-based numbering, i.e. the 5th batch). This is a synced snapshot, not live GPU progress; E's partial effects were not read to draw research conclusions. The strength sweep and v3 results are outside the scope of this completed-data review.

## Verification and handoff

Offline suite: `.venv/bin/pytest -m "not gpu"`, 126 passed, 3 skipped. This review only adds a review document and updates the STATUS coordination record; no research decision was made, so decision_log was not changed.

Order of handling for Claude: keep the current frozen directories; verify completeness at the end of each stage; fix E2 before consuming the v3 B′ signal; before freezing v3, take the interpretation of R1 / R2 and any necessary new diagnostics to the PI for decision; fix E1 in a later safe version. Do not take the review opinions above as authorization to sync code into the running v2 directory.
