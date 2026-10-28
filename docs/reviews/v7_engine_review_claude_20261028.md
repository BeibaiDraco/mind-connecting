# Review of the V7 engine (Codex, commit e98225f)

**Reviewer:** Claude Code. **Date:** October 28, 2026. **Scope:** `src/mb/kv_geometry.py`; the V7 parts of `src/mb/runtime.py`, `src/mb/conditions.py` and `src/mb/run.py`; `tests/test_v7_kv_engine.py` and `tests/test_v7_kv_gpu.py`; the implementation note `docs/reviews/v7_engine_implementation_codex_20261028.md`. Read-only review of code and tests. No model or GPU was run; torch is not installed locally, per AGENTS.md.

## Verdict: approve for GPU acceptance once the PI approves the V7 draft

No correctness defect found. The operation matches protocol V7 §5. Two non-blocking recommendations should be settled during the smoke run (R1, R2). One integration task remains before the pilot (R4).

## What was checked

| Item | Finding |
|---|---|
| Rotation algebra | `rephase_keys` computes `k·cos(δθ) + rotate_half(k)·sin(δθ)` with `θ = inv_freq`, duplicated over both halves. This is the same convention as Hugging Face's `apply_rotary_pos_emb`: rotation by +φ on pairs (i, i + d/2). Rotations compose additively, so applying R(δ) to keys already rotated to position p gives position p + δ exactly. δ = −L_B places B's bank at [−L_B, 0), so every query-key distance stays positive. Qwen3 applies `k_norm` before RoPE and has no absolute-position signal, so a uniform translation of the whole bank is exact. |
| Amplitude scaling | The cached keys already contain `attention_scaling`. The read-time rotation applies none (pure rotation), which is correct. For Qwen3 default RoPE the factor is 1 anyway. |
| Frequencies and pairing | Taken from the loaded model (`model.rotary_emb.inv_freq` and the family's own `rotate_half`). Changed frequencies, non-stationary rope types and dimension mismatches fail closed. |
| Where the rotation acts | Only on the fp32 copy of the partner keys inside `kv_attention`, masked to the receiver's readable partner positions (KV-P prefill). Values, masks, caches and the receiver's own attention subcalculation are untouched (tested with `assert_array_equal`). |
| Per-row δ under padding | δ comes from the logical P-bank length recorded at prefill and is checked against `attn[:, :c_start].sum(1)`. Left padding cannot change it; padding and batch-composition invariance are tested. |
| Joint masses | Own `(1−β)·p_own` and donor `β·p_par` are summed over declared spans. Masks are built from each source row's logical positions. This matches a dense joint-softmax oracle in the tests. |
| Head ordering | `query.view(n, KVH, G, 1, D)` followed by `.view(n, heads, L)` gives query head h = kvh·G + g. That is the `repeat_kv` mapping, so logged head indices are native query-head indices. The tests check head // G. |
| δ = 0 and logging off | Output is bit-identical to the legacy path, and `rephase_keys` returns the same tensor object. Legacy arm identities omit the new fields, so frozen hashes are unchanged (tested). |
| Identity | The constant arm identity carries the placement contract. Each record carries a resolved per-row identity (δ, ranges, prefix hash, span hashes, rotary identity) and a `resolved_condition_hash`. This is adequate for resume and audit. |
| Branch isolation | `select_rows` deep-copies bank provenance. FULL/RF/RO row mapping and snapshot isolation are tested. The context is cleaned after exceptions. |
| Tests | The torch-free double runs production code. It has independent references: a complex-number rotation and a dense softmax with GQA. They cover sign, inverse, norm, poisoned padding, missing layers and NPZ round trips. They are strong for arithmetic and contracts. The GPU acceptance file is present and unrun, as stated. |

## Recommendations

**R1 (efficiency; measure in the smoke run, fix before the formal run if material).** On every step, `_kv_geometry_begin` calls `kv_condition_identity`, which hashes JSON for every receiving row. It then rebuilds span masks with Python loops over rows × spans, each a separate small GPU operation. With about 20 receiving rows and about 20 spans, that is on the order of a thousand kernel launches per step. Against a single-token forward pass this may be a large fraction of step time. Resolved geometry and the prefix-position masks are fixed for a state, so cache them on the state (or keyed by state identity, invalidated by `select_rows`) and pad new columns with False. Record the per-step overhead in the smoke log either way.

**R2 (BF16 acceptance plan).** Hugging Face casts `cos/sin` to the activation dtype, so the cached keys were rotated with bf16 trigonometry. The read-time rotation runs in fp32. A real offset prefill in bf16 will therefore differ from read-time rotation at bf16 rounding scale, not at the FP32 bounds in `test_v7_kv_gpu.py`. Calibrate the bf16 tolerance against the legacy path's own numerical noise before judging agreement: for example, the spread of answer-label log-probabilities between two batch compositions of the unmodified path on the same 12–24 smoke episodes. Do not use a fixed number.

**R3 (scientific diagnostics; done on the materials side).** The complete-bank translation also moves B's first token (`<|im_start|>`, a typical attention sink) and B's system turn, which duplicates A's. A change in partner mass may come from the sink rather than the card. `v7_tasks.declared_spans` now declares `first_token` and `system_turn` in addition to the card fields (test added). The V7 runner should also declare `note` and `prompt` spans from actual lengths.

**R4 (V7 runner integration, needed before the pilot; Codex owns the runner).** The materials-side contract:
- **Prefixes:** `v7_tasks.private_prefix_ids(tok, ep, role, fact_holder, counterfactual, frame)`, then the generated note, closing tokens and `tasks.reflection_turn_ids`, as in `Runner.prefix`.
- **Note keys:** include variant, fact holder, counterfactual flag and frame. The card text differs across these, so notes cannot be shared between them.
- **Arm mapping (protocol §6):**
  - full-information arm: `fact_holder="A"`;
  - counterfactual arms: `counterfactual=True` on the donor card only;
  - strict third-person arms: `frame="third_strict"` on B;
  - same-content arms: B's bank is a copy of A's complete prefix (A's card and A's note), with A's spans.
- **Spans:** `v7_tasks.declared_spans(...)` plus `note` and `prompt` intervals, in the same logical coordinates.
- **Questions and records:** `v7_tasks.readout_questions(tok, ep, "A")`, with the registered question set per variant. Add `v7_tasks.record_metadata(...)` fields to each record. USE meanings are `fact`, `cf` and `other`; DETECT meanings are scale keys.
- **Splits:** `v7_dev`, `v7_pilot`, `v7_formal`. The variants of one split share episode structure by design.

## Not covered by this review

Checkpoint inference, BF16 kernels, real-offset equivalence on the pinned model, and runtime cost are all pending the engineering smoke, which is authorized only after the PI approves the V7 draft. Codex's review of the V7 protocol draft and materials (`7e2ab23`, `ef28e34`) is still outstanding.
