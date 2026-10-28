# V7 answer-position diagnostic persistence

Codex, 2026-10-28. Implementation handoff for independent Claude review. No model work, output analysis or data deletion was performed in this correction.

## Cause and scope

File sizes, ZIP member metadata and NPY headers identify 2,323,799,873 of the 2,335,264,342 engineering bytes as compressed attention traces. JSONL answer records occupy 7,865,458 bytes. The collector persisted every reflection tick, every readout-prefix tick and every consumed open-answer tick. The approved protocol section 5 asks for per-layer/head span and bank summaries at readout answer positions. No full token attention matrices were saved, but multiplying the summaries over all these ticks caused the storage growth. The prior 127 GB pilot projection describes that full-tick policy; it is not collected pilot data. The separate 11,118,371,202-byte archive contains persistent model/dependency caches and earlier evidence, and is reused rather than copied per episode.

The PI selected protocol-scoped persistence after being offered the full-trace alternative with additional rented disk. All old evidence remains immutable. Claude's source-only interpretation is saved verbatim in `v7_logging_scope_claude_20261028.md`.

## Change

Only `V7Runner._tick_payload` changes persistence. It removes the C-phase span/bank/query arrays and slices each R branch's three corresponding arrays to `[:, -1:]` before inherited cross-branch padding. The remaining tick axis has length one. This query produces the answer logits; its logical position is retained verbatim. Every layer, query head, own/donor span slot, dtype, NaN, geometry declaration, delta and hash remains unchanged.

Runtime computation and CPU trace accumulation are unchanged. All JSONL records, C-phase scalar diagnostics, readout `TICK_ARRAYS`, geometry, trial keys and ordinary length fields remain unchanged. Legacy `run.Runner` serialization and the FP32/BF16 engineering comparisons are untouched. A new explicit `attention_logging` identity field prevents resuming full-trace runs under the compact policy, even with `--allow-code-change`.

The PI explicitly clarified U_OPEN after Claude identified the ambiguity: retain all 80 answer-producing positions, the existing 79 `g_*` positions plus the final R query. The complete generated text is also unchanged. This decision is appended to `decision_log.md`; no protocol bytes were modified.

## Validation and storage

Tests were written first and failed against the old serializer. They cover exact final-query values and logical positions, NaN and dtype retention, no mutation, unchanged legacy serialization, different branch lengths/span counts, full U_OPEN continuation retention, identity refusal before writes, and byte-identical complete synthetic answer/note/language/tick-summary/snapshot records. End-to-end fake-engine dispatch still covers all base/generalization arms and all original trials. No local model or torch is used.

The targeted runner, relocation, acceptance and pilot-gate suite passed 73 tests. The complete offline suite passed 1,407 tests, with 11 skips and one GPU deselection, in 50.50 seconds.

The declared 80-episode pilot contains 20,880 trials and 17,920 linked answer positions. At the observed 36 layers, 32 query heads and 28 span slots plus two bank totals, one position per linked answer is 2,477,260,800 uncompressed bytes. Retaining all 79 extra positions for 640 linked open reports adds 6,989,414,400 bytes. These are schedule/header arithmetic, not attention-value inspection, and exclude JSONL/metadata. Both are substantially below the retained instance's previously measured 92,943,183,872 free bytes; free space must still be checked before launch.

Claude's scope review permits retaining the existing FP32 acceptance and batch 12 because this change happens only after runtime output returns. Its optional extra GPU serialization exercise is unnecessary if the offline equivalence tests and implementation review pass. No pilot or new GPU check has been dispatched. The instance remains stopped/retained.
