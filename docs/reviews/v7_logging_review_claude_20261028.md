# V7 diagnostic persistence and SD retention review

Claude Code, 2026-10-28. Verbatim read-only review of implementation commit `e44a643`, including the PI-requested assessment of the two preceding V7 SD backups. The response explicitly states its access limits. No experimental outputs or credentials were sent.

I couldn't open the two files under `/private/tmp`, the patch and the SD inventory: the file tools in this session only reach the repository. So I reviewed the source as it stands at e44a643 (git shows only an untracked image) instead of `logging_patch.diff`. The cleanup section relies on the facts you stated, not the inventory. I read only the repository files you named, edited nothing and ran nothing.

## Logging review of e44a643

**Verdict: ready, no blocking findings.** You can continue the already-authorized 80-base-episode pilot at batch 12 on the retained H100 after a capacity check (below).

**Correctness**
- **Final R query is the answer position.** `V7Runner._tick_payload` (`src/mb/v7_run.py:284-293`) keeps only the last tick of the readout span, bank and query-position arrays. Those arrays are shaped rows × ticks × … (`runtime.py:743-746`), so the slice is on the tick axis.
  - Every R step records its masses fresh, so the last stored entry is the last suffix token's step (`runtime.py:508-535`). If a layer is missing, it raises (`runtime.py:524-525`).
  - That step's hidden state produces `label_logits` (`runtime.py:731-733`). Its logits also produce the first U_OPEN token (`runtime.py:761`).
  - The stored query position is the consumed token's logical position: `next_pos − 1`, taken after the `+1` (`runtime.py:566, 613`). Translation shifts only the partner keys, so the query position is unshifted.
- **All 80 U_OPEN positions are kept:** the final R query plus the 79 consumed generated steps (`runtime.py:763-781`). The 80th token is never consumed, so it has no position. The generated-step arrays pass through unchanged.
- **Reflection (C-phase) masses are dropped; everything else in the C payload is kept,** including per-tick `kv_mass`, `kv_mass_cr`, `inj_ratio`, tokens and `kv_geometry_json`. The ticks summary still reads the untouched in-memory log (`run.py:877-894`). No input is changed.
- **Geometry, heads and spans are retained.** All layers, query heads and span slots stay, including note/closure/prompt, with NaN for invalid slots and −1 for padded positions. dtype is unchanged. What is kept depends only on indices, never on values.
- **Variable-length padding is safe.** The slice happens before the cross-part padding in `run.py:1018-1035`, so different suffix lengths and span counts can't move the kept index. The `_lengths` field becomes 1 for readout arrays and 79 or 0 for generated-step arrays.
- **Records and legacy behaviour are unchanged.** JSONL records, `TICK_ARRAYS`, trial keys, the top-level lengths, `kv_condition_identity`, `r_kv_condition_identity` and `resolved_condition_hash` don't change. Arm config hashes don't include the new logging field, so they match earlier runs. `run.Runner._tick_payload` is still the full-tick path (`run.py:991-999`).
- **Identity refusal works.** `attention_logging` is in the identity (`v7_run.py:166`). Only `source_hash` is exempted under `--allow-code-change` (`v7_run.py:247`). Old full-trace run directories will therefore refuse to resume.

**Regression coverage** (`tests/test_v7_runner.py:167-254, 349-404`) covers what the scope review asked for:
- exact last-query values and dtype, with no mutation of inputs;
- NaN kept, and selection before ragged padding (3 vs 5 ticks, 6 vs 4 slots);
- C-phase masses absent while other diagnostics stay;
- U_OPEN `_lengths` = 79;
- byte-identical records, notes, language, ticks and snapshot files against the legacy serializer;
- refusal before any write;
- every linked arm still has `kv_log_spans`.

**Non-blocking notes**
1. In the dispatch test, the check that query position = `lengths − 1` uses synthetic positions. That the real position matches the label-producing query follows from the runtime code above, not from a test. That's acceptable.
2. In any R file containing U_OPEN, every CAP row also gets NaN-padded generated-step buffers 79 wide. This is unchanged legacy padding. It compresses to almost nothing but is large in host memory at save time: roughly 2 GB per arm-chunk file at batch 12 by my estimate. It is still smaller than the old full-tick peak, which already ran.
3. Batch 12 and the FP32/relocation acceptance still stand. The filter acts only after `run_readout` returns, and the gates read the engine directly. If the filter is ever moved into `runtime.py`, that reasoning no longer holds.

**Capacity check before launch:** measure free disk now rather than reusing the earlier 92.9 GB figure. It should comfortably exceed about 9.5 GB, which is the arithmetic in `docs/reviews/v7_logging_implementation_codex_20261028.md`, plus JSONL, compression overhead and a margin. Also confirm host RAM has room for note 2.

## SD-cleanup assessment (separate)

**Scope:** the two immediately preceding V7 backup directories, `20261028-engineering-pilot` and `20261028-relocation-pilot-v2`. I didn't see the inventory and inspected no data or results.

**Must keep**
- **`engineering-pilot/remote-control/persistent-data-cache.tar.gz`** (11,118,371,202 bytes, SHA256 `d673debf…ec67`), with its verification receipts. It is:
  - the only verified full copy of v7-cache;
  - the only archive holding the original failed-attempt evidence;
  - the base that v2's incremental cache depends on.
- **`relocation-pilot-v2`** in full: its independently verified engineering data, the 5,964-byte delta and its receipts. v2 is not a full replacement for the first backup.
- **All reports, receipts and manifests** in both directories, which are immutable.
- The stopped H100 disk doesn't count as a copy of any of these.

**Safe cleanup candidates:** none I can name. A file would qualify only if it is a duplicate inside these two directories, its full SHA256 matches a verified copy that is being kept, and it isn't evidence or referenced by a receipt. Equal size isn't enough. I'd need the inventory and hashes to point to any such file.

**Before deleting a cached duplicate of the base archive,** all of these would be needed:
- a new full (not incremental) cache archive with a member manifest, every member verified by hash, and a test restore;
- a separate verified archive of the failed-attempt evidence, matched member by member against the original;
- v2's dependency rebased onto the new archive and re-verified;
- explicit PI authorization.

**Space gained now:** nothing meaningful. The 11.1 GB archive can't go, and any replacement would be about as large. The delta is 6 KB, and the engineering data is evidence. My recommendation is to keep both directories intact.

If you want the inventory checked for real duplicates, paste `sd_inventory.json` or move it into the repository, and I'll redo the cleanup section against it.
