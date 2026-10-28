# Review: revised V7 relocation acceptance implementation

Claude (Opus 5.5), 2026-10-28. This is a read-only code review. I read AGENTS.md, the claim table and current phase in STATUS.md, the 2026-10-28 revised approval in `decision_log.md:592-598`, protocol V7 §5 and §7, the handoff note, the code under review, and the production contracts it depends on (`runtime.py`, `conditions.py`, `kv_geometry.py`, `bridge.py`, `v7_run.py`, `v7_tasks.py`, `run.py`). I did not run any tests, model or GPU job. The offline test results quoted in the handoff are Codex's, not mine. I did not open any saved inputs, outcome files or private caches.

**Verdict: ready for the approved GPU engineering checks.** I found no blocking defects. The P2 items below are worth doing before the run if they are cheap; nothing else needs to change first.

## 1. Real negative-position reference and donor-only replacement: correct

- **B's positions are right.** `reference_layout` (`v7_relocation.py:40-51`) gives each B row the positions `col − pad − L_B`. These come from that row's own unpadded length, so valid tokens sit exactly at `[−L_B, 0)` under any padding. A rows keep `max(col − pad, 0)`, which is the same as the native `(attn.cumsum − 1).clamp(0)` in `runtime.py:384`.
  - Padded slots get position `−L_B` instead of 0. This doesn't matter: those slots have `attn = 0`, so they are never readable through `par_ok` or `own_ok` (`runtime.py:103-106`, `:489`).
  - The function checks that the reference padding mask equals the native one (`:61-62`).
- **The reference runs the model's own RoPE.** The forward pass at `:66-67` is the model's real prefill with those position IDs. The handoff says the reference never calls `rephase_keys`, and that holds: with `kv_position='native'`, `ctx.delta` stays `None` (`runtime.py:464`), so the rotation at `:109-111` is never called.
  - transformers 4.57's packed-sequence detection only triggers when `attention_mask` is None, and the mask is always passed here. The default rotary embedding does nothing special with negative positions. Both points still need the GPU run to confirm (see the limits section).
- **Only B's state is replaced.** `:73-79` overwrites only the odd rows of the cloned reference: both K and V in every layer, plus `next_pos`, `logits`, `pending`, `ema` and `mailbox`.
  - `cache_layers` returns the cache's own tensors, so the slice assignment writes into the reference clone, not a temporary.
  - B's `next_pos` becomes `L_B − L_B = 0`.
  - B's tick keys and B's hidden state cannot reach A. KV-P reads only `pos < c_start` (`runtime.py:492-493`), and a KV plan has gain 0 and no residual writes (`runtime.py:264`).
- **The span declarations stay valid.** Span masks are built from `logical = attn.cumsum − 1` and the declared `start`/`end` values, not the shifted "apparent" values (`runtime.py:463`, `:478-480`; `kv_geometry.py:59-63`). So the same physical donor slots are selected in both branches, even though their rotary coordinates differ.

## 2. Independence of A states and snapshots: correct

- **The two branches are independent copies.** `translated` and `reference` are separate `select_rows` copies (`run_comparison :164-165`). `select_rows` copies every tensor and deep-copies `kv_banks` (`runtime.py:207-225`).
- **A's starting state is checked bit for bit.** A rows are compared with `torch.equal` on `attn`, `next_pos`, `logits`, `pending`, `ema`, `mailbox` and every K/V layer (`:81-86`). Fields the check skips (`consumed`, `tick`, `c_start`, `kv_banks`) are copied verbatim.
- **`native` is never changed before it is reused.** It is only stepped in the BF16 padding trace, after both branch traces finish (`:178-185`).
- **No state leaks between ticks or branches.** `KV_CONTEXT` and the `last_kv_*` diagnostics are reset in `_kv_end`'s `finally` block on every step (`runtime.py:532-542`).

## 3. Production path match: correct

- **The arm in `trace` matches production `trans_w2`.** It is `ArmConfig('ONE', kv, P, gain 2, kv_log_spans=True, before_own/native)` (`:94-95`). Production `trans_w2` (`v7_run.py:51-56`) differs only in `model_profile`, which `make_plan` uses only for a hidden-size check.
- **Each tick uses the production engine.** It calls `Engine.step` with the production joint read, then `advance`, matching `run_reflection` (`runtime.py:663-671`). There is no injection, and since KV writes are off, `tau=1` only affects B's EMA, which has no effect on A.
- **The translated arm's shift is the production one.** δ = −L_B comes from `resolve_geometry` (`kv_geometry.py:56`). Only readable donor P slots are rotated (`runtime.py:466`).

## 4. Per-head/slot mass comparison and coverage: correct

- **Slots are sliced in the right order.** `kv_geometry.py:59` orders slots as own spans, then donor spans, in declaration order. The slicing `[:own]` and `[own:own+donor]` (`:110-115`) matches that. Both branches use identical declarations, so slot j means the same thing in both.
- **Shapes are checked.** `trace` requires `[rows, layers, query_heads]` (`:106-107`) and raises if span slots are missing.
- **Every element is tested.** `error_summary` (`:119-131`) compares each element of the full `[layers, heads, slots]` array for each tick, so one bad head or slot fails the gate.
  - The rule `|a−b| > atol + rtol·|b|` with the reference as `b` uses the approved tolerances: logits 3e-3 absolute / 2e-3 relative, masses 2e-3 absolute with no relative term.
  - Non-finite values, empty arrays and shape mismatches all fail or raise.
- **The full vocabulary is compared** for A rows' logits.
- **Coverage is exact.** `:186-190` requires exactly one row per (batch ∈ {1,4,8,12}, episode 0–11, tick 1–8), which is 384 rows. Uneven final chunks (batch 8 gives 16 rows then 8) are handled.
- **The benchmark's finite-mass check won't trip on padding slots.** Every card has the same set of span names (`v7_tasks.py:280-314` plus the three spans from `_prefix_parts`), so rows in a batch have equal slot counts and no NaN padding slots.

## 5. FP32-only admission: correct

- **Only FP32 can admit.** `passed` is computed only when `precision == 'fp32'` (`:192`). The BF16 result has `passed: None`, and `main` never reads it (`v7_acceptance.py:236-238`).
- **A failed FP32 gate stops everything.** It raises before BF16 loads (`:225-226`), and the detailed `relocation_fp32.json` is already written by then.
- **The model really is FP32.** It is loaded with `dtype=torch.float32` (`:217`), and `_lm_logits` returns fp32.
- **One gap:** the label is trusted rather than checked (see P2-b).

## 6. Stage ordering: correct and tested

The order in `main` is:

1. approval hash checks (`:192-194`)
2. saved-file hashes (`:195`)
3. output directory created write-once
4. material reconstruction (`:213`), before any model loads
5. FP32 gate
6. descriptive BF16 comparison
7. R1 timing
8. the 336 CAP0 runner checks at fixed batch 12 (`:247`)
9. `choose_batch`
10. `pilot.yaml`
11. `acceptance.json`

No pilot is dispatched. CAP0 runs with `passes=1`, so there is no silent retry, and completeness must be exactly 336 `ok` CAP0 records. `test_v7_acceptance.py:56-103` checks this order and the failure branches.

## 7. Input hashes and material compatibility: correct

- **All four saved files are pinned** and copied write-once. The old BF16 evidence is only copied, never recomputed. `read_saved_inputs` re-hashes the inputs and checks the ordered episode IDs, the interleaved pairs, the token IDs and the span bounds.
- **Current materials must rebuild the saved inputs exactly.** `validate_material_compatibility` rebuilds them through the production `V7Runner._prefix_parts` with `orig_w2` inputs. `trans_w2` has the same `input_context`, so these are exactly the production `trans_w2` prefixes and spans. Equality is exact after a JSON round trip.

## 8. Hook, state and cache lifetimes: correct

- **Hook mode is always restored.** It is set to `prefill` with writes off and restored to `tick` in a `finally` block (`:64-70`), and the seed is cloned straight after the forward pass.
- **The temporary offset cache is freed.** It is local and is released when the function returns.
- **The FP32 model is released before BF16 loads.** The engine is closed, references dropped, then `gc.collect` and `empty_cache` run (`:227-230`).
- **Runner engines are closed** in `run_arms`' `finally` block.
- **Memory is fine.** At batch 12, about four FP32 states of 24 rows each is far below 80 GB.

## Blocking defects

None.

## Recommended improvements (non-blocking)

**P2-a. Add a check that the gate can actually fail.** The gate would pass vacuously only if two separate silent failures happened together: the translation doing nothing, and the B replacement doing nothing. Either one alone makes the gate fail. The existing GPU test 2 (`test_v7_kv_gpu.py:97-101`) only checks that the shifted logits are finite. Two cheap fixes:
- In `prefill_relocated_reference`, assert that the reference B keys differ from the native B keys (`not torch.equal`) while the values are close.
- In GPU test 3, assert that the translated trace differs from a native-read trace on native B by much more than the tolerance. Neutral fixtures only; no dev-input contrasts.

**P2-b. Check the precision rather than trust the label.** In `run_comparison`, when `precision == 'fp32'`, assert that the model parameters and cache are float32. Record `torch.backends.cuda.matmul.allow_tf32`, `torch.get_float32_matmul_precision()` and the SDPA backend in the recipe or receipt. The defaults are safe, and the earlier H100 checkpoint run got 3.05e-05, but the receipt should prove this rather than assume it.

**P3 items:**
- **Persist the shifts actually used.** Provenance recomputes `translated_read_offsets` from lengths (`:168`). Store `engine.kv_condition_identity(...)` deltas from the run instead, and assert they equal −L_B.
- **Make failures easier to diagnose.** On a failed gate, record where the worst error is (tick, layer, head, slot).
- **Add an offline fake-engine test of `run_comparison`.** It should cover batch chunking, coverage, BF16 `is_gate=False`/`passed=None`, the padding-baseline indexing and the write-once output. Today only the GPU test (batch 1) exercises it. Also add negative tests showing that a changed A state or a mask mismatch raises.
- **Remove the test-only shortcut in production code.** `if hashes:` (`v7_acceptance.py:212`) exists only so the test can skip the material check. Remove it and stub `validate_material_compatibility` in the test instead. Also give the material check its own phase name; a mismatch is currently reported as `failed_phase: fp32_model_load`.
- **Add `torch.no_grad()` inside `prefill_relocated_reference` and `run_comparison`.** This avoids depending on the caller's context.
- **Tighten the pilot config hand-off.** `pilot.yaml` is written before `acceptance.json` (`:257-259`). Either write it with `"x"` after the receipt, or make sure the dispatcher requires `acceptance.json` to say `passed: true` with a matching `pilot_config_sha256`.

**For awareness, not a defect:** the CAP0 runner exercise follows the normal production path. It will generate new BF16 notes for the counterfactual and strict-third-person donor contexts (about 24 dev notes), and it writes reflection text and mention counts to `ticks.jsonl`. None of these are ownership readouts. Nobody should inspect them, and they stay in the dev engineering run directory.

## What only the GPU run can confirm

- HF Qwen3 accepts negative `position_ids` in this exact prefill and mask path, and produces finite padded rows.
- The actual FP32 error at all 384 comparisons across batches 1/4/8/12. Offline tests only cover the plumbing; GPU test 3 covers batch 1 only.
- The current `PROTOCOL_V7_DRAFT.md` must still hash to `608350de…`, or `validate_launch` will refuse (correctly). I did not compute that hash.
- The deployed source hash changes with this commit and the Claude commit `b6d2040`.
- Memory and timing at batch 12.
- That the CAP0 runner completes all 336 trials.
- Pilot instrument validity (U1–U3, Q1) is a separate later check that this gate does not address.

**Final verdict: no blocking defects; ready for the approved GPU engineering checks (FP32 gate, descriptive BF16, R1 timing, 336 CAP0 checks, then batch selection), within the PI's existing scope.** I am not authorizing anything beyond that scope.
