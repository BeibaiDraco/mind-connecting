# V7 engine implementation for Claude review

2026-10-28, Codex. Implements the PI-authorized engine portion of plan v2. This is an implementation handoff, not an independent approval, frozen protocol, or model acceptance result. No experiment, model execution, GPU smoke, torch installation, or protocol/material edit was performed.

## Change and integration

`ArmConfig(kv_position="before_own", kv_log_spans=True)` selects translation plus diagnostics. `kv_position="native"` selects the historical placement. Both additions default off and disappear from legacy arm identities; frozen arm names and hashes are preserved. The same default omission applies to run configurations, reflection grouping, and unused-field snapshot fingerprints. Translation is accepted only for one-way KV-P.

Call `Engine.prefill(sequences, attention_spans=span_rows)`. Each row supplies its own bank's `(name, start, end)` declarations, using zero-based logical, half-open P coordinates. Names must be unique within a row; nested/overlapping spans and empty notes are allowed. The prefix includes the private card, actual note, closing tokens and reflection prompt. Readout row selection deep-copies the declarations with the cache.

`Runner.prefix_spans(ep, role, frame, prefix_ids)` is the material adapter; its default declares the complete `P` interval. Claude's current `v7_tasks.declared_spans(...)` returns compatible tuples. A V7 runner must supply the actual V7 episode/fact-holder/counterfactual arguments and can append generated-note, closure and reflection-prompt intervals after constructing the complete prefix. This handoff does **not** implement the unapproved V7 study's episode scheduling, question/material routing or analysis. Those remain integration work after the draft and materials review.

## Rotation and identity

`kv_geometry.py` resolves each receiving row's donor interval `[0, L_B)` to `[-L_B, 0)`: delta is `-L_B`. `Engine` checks the saved length against the valid prefix positions, independent of padded cache width. In `kv_attention`, `rephase_keys` acts on the fp32 `k_par` copy. Only valid P keys rotate. Values, cache tensors, visibility masks and the native own-attention subcalculation are untouched. Subsequent receiver states can of course change through the changed donor contribution.

Frequencies come from the loaded model's `model.rotary_emb.inv_freq`; pairing comes from that model family's installed `rotate_half`. Cached rotary amplitude scaling is not applied twice. Only the stationary pinned-family types `default` and `llama3` are admitted; changed frequencies or a dimension mismatch fail closed. This compatibility code is not Llama run authorization. Delta zero returns the input key view without additional arithmetic.

The constant arm identity contains the operation/version/delta rule. Each result's `kv_condition_identity` contains the resolved numeric delta, full source/destination intervals, compact logical position map (`start/stop/step`), prefix token hashes, declared span bounds/content hashes, apparent span positions, rotary identity and a geometry hash. `resolved_condition_hash` binds this to the constant arm hash. R-phase identities are also recorded. These episode-specific identities intentionally do not replace the cross-episode arm hash used by the existing ledger.

## Stored diagnostics

- C: `kv_span_mass` has axes `[row, tick, layer, query_head, span_slot]`.
- R/question and generated continuation: `r_kv_span_mass` and `g_kv_span_mass` have the same trailing axes, with the first axis selecting measured recipients.
- `*_kv_bank_mass` has the same axes with final slots `[own, donor]`, summing to one per active layer/head. Own includes its full visible cache; donor follows the existing scope/weight mask.
- `*_kv_query_pos` records the logical query position. Layer and head indices are zero-based; native query-head order is retained across GQA groups. Readout answer-position diagnostics are the last valid R tick. The last emitted open-report token is not consumed, so G has `generate-1` entries, matching existing generation semantics.
- `kv_geometry_json` maps each row's span slots: own declarations first, donor declarations second. Do not sum overlapping spans as a partition. Missing/non-reading slots are NaN; valid empty or masked spans have zero mass. NPZ branch padding uses NaN for mass, -1 for positions, and explicit valid lengths. Metadata uses JSON Unicode arrays and loads with `allow_pickle=False`.

The summaries use `(1-beta)*p_own` and `beta*p_par`, with existing weights already included in donor logits. No full attention matrix is saved. Context and hook cleanup also runs after geometry/forward exceptions.

## Verification and review boundary

The torch-free tests execute production runtime methods through a NumPy API double and use a separate dense joint-softmax oracle and complex-number rotation reference. They cover sign, zero bypass, norm/inverse tolerances (`atol=5e-7, rtol=2e-7` on the fp32 fixture), unchanged K/V, poisoned padding, changed batch composition/order, GQA head mapping, all historical scopes, empty/no-readable spans, missing layers, snapshot and metadata isolation, FULL/RF/RO row mapping, generation tick axes, material-adapter routing, NPZ round trips and exception cleanup. They also execute the installed Qwen pairing function and test loaded-frequency selection/change rejection. These are arithmetic/contract tests, not checkpoint inference evidence.

`tests/test_v7_kv_gpu.py` supplies **unrun** acceptance against the pinned Qwen checkpoint: real full-sequence offset prefill versus read-time rotated K, unchanged V, output agreement, native/logged equality, padding/batch invariance and snapshot isolation. Its FP32 bounds are explicit in the file (K/V `2e-3` absolute/relative; logits `3e-3` absolute, `2e-3` relative). BF16 production-kernel acceptance and the authorized engineering smoke remain pending PI approval of the V7 draft. No empirical tolerance calibration is claimed here.

Claude review requested: check the model-family rotary contract, joint-mass head ordering, resolved identity/record semantics, branch isolation and the V7 material adapter before any GPU acceptance. Review findings should go into a new file under `docs/reviews/`.

Offline milestone: `.venv/bin/pytest -m "not gpu"` — **1326 passed, 11 skipped, 1 deselected**, 50.31s (includes Claude's newly committed V7 material tests). Targeted engine/identity checks and whitespace checks also pass.
