# V7 diagnostic logging scope review

Claude Code, 2026-10-28. Read-only review of repository protocol and logging source, explicitly authorized by the PI. No results, model caches or credentials were sent; no tests or model work ran. Verbatim response follows.

I reviewed the protocol and source only. I read no run outputs, edited nothing and ran nothing.

## Conclusions

**1. What §5 requires.** `PROTOCOL_V7_DRAFT.md:86` asks for per-layer, per-head joint mass on own spans and donor spans "at each readout's answer position". It also asks for total bank masses, logical positions, δ and span hashes. It then says "Only compact summaries are stored". §8 (line 158) makes span masses descriptive diagnostics only. Nothing in §7–§9 uses mass at any other position.
- **Full C-phase span/bank/query traces** (`run.py:877`, from `run_reflection`) are extra. The reflection is not a readout, so the protocol never asks for them.
- **Full R-prefix traces**, one per suffix tick (`runtime.py:742-746`), are extra except for the last tick. In the forced-choice branch, `label_logits` come from `last_h`, the hidden state of the final suffix token (`runtime.py:731-733`). The final R tick's mass is computed at exactly that query, and `kv_query_pos = next_pos − 1` after the `+1` at `runtime.py:566` is its logical position. So the final R tick is the answer position.
- **Generated-continuation traces** (`g_kv_*`, `runtime.py:773-781`) only exist for U_OPEN, so whether they are needed depends on point 2.

**2. U_OPEN is ambiguous and needs a PI ruling.** "Answer position" (singular) is well defined for forced choice. For an 80-token open report the text supports two readings:
- (a) the final prompt position, which predicts the first generated token, exactly as in forced choice;
- (b) all 80 positions that predict answer tokens: the final R tick plus the 79 consumed generated ticks. Token 80 is never consumed.

I can't settle this from the text. While the PI decides, I recommend keeping the final R tick **plus** the full `g_*` trace for U_OPEN. That is a superset of both readings, so it adds no rule. It is also cheap: 9 open reports per episode against 252 forced-choice readouts. If the PI adopts (a), the `g_*` trace can be dropped later by an explicit policy.

**3. The proposed adjustment conforms to the approved protocol,** under these conditions:
- Keep the full span-slot dimension at the final tick: every declared own and donor span, plus the runner's note/closure/prompt spans, with NaN for invalid slots. "Own/donor mass" must not be reduced to the two bank totals.
- Leave unchanged: `kv_geometry_json`, per-record `r_kv_condition_identity` and `resolved_condition_hash`, the per-tick scalar `TICK_ARRAYS`, the C-file non-span payload, `ticks_summary`, and all JSONL records.
- Take the final tick per branch part, before the cross-part padding in `_save_rticks` (`run.py:1023-1035`). Padded width ≠ true length when CAP items differ in suffix length.
- Scope the change to `V7Runner`. Legacy `run.Runner` output stays byte-identical.
- Bind the logging policy explicitly in `build_identity` (or a `CONTRACT` bump). `source_hash` alone is too implicit, and old dev runs must refuse to resume.
- The protocol text does not change, so the approved SHA `608350de…` remains valid. Record the interpretation (and the U_OPEN ruling) in `decision_log.md`.

## Required offline tests
1. **Final-tick equivalence:** each new array equals the legacy `x[:, -1]` (or last-true-length index) per part. Include parts with different suffix lengths and different span counts.
2. **Query position:** the final-tick `kv_query_pos` equals the last suffix token's logical position, the one that produces `label_logits`. Check ORIG and TRANS (the query is unshifted under δ).
3. **Shapes and NaN:** `[n, layers, heads, slots]` and `[n, layers, heads, 2]`. Invalid-span NaN and the −1 query fill are preserved.
4. **U_OPEN:** matches the PI ruling. Under the interim superset, the `g_*` trace is byte-identical to legacy and `_lengths` = 79.
5. **Unchanged outputs:** JSONL records, `TICK_ARRAYS`, `kv_geometry_json`, `trial_keys` and the C-phase non-span payload are identical to legacy, using a stub or synthetic engine (`tests/v7_synthetic.py`).
6. **No selection from values:** what gets kept depends only on indices. Permuting or NaN-ing the mass values doesn't change which elements are stored.
7. **Coverage unchanged:** all linked arms keep `kv_log_spans=True`, all layers and heads are present, and c0 is unchanged.
8. **Identity:** the policy field is in the identity, a policy change refuses resume, and the legacy runner is unaffected.
9. **Gates are independent of the change:** `v7_acceptance.py:134` and `v7_relocation.py:133` read `engine.last_kv_*` directly, not the serialized payload. The existing acceptance tests still pass unchanged.

## Keeping prior acceptance and batch choice
- **Yes, both can be kept.** Every computation, the per-tick CPU accumulation and the batch layout stay the same. Only what goes into the NPZ changes after the fact. The FP32 acceptance and relocation gates never touched serialization.
- **This holds only if** the filter is applied after `run_readout` returns. If anyone moves it into `runtime.py` (for example, logging only the last tick), the computation path changes and that argument no longer holds.
- **The CAP0 check is optional, not required.** If you run it, keep it tiny: a few `v7_dev` episodes, CAP0 only, linked arms. It should assert equality between the new arrays and the legacy final tick in the same process, and between the JSONL records. It should print no CAP, label or mass values, and it counts as engineering, not evidence.

## Blockers
- **PI ruling on the U_OPEN answer position,** (a) or (b). The superset avoids blocking the pilot on it.
- **No other blockers.** Implementing the change, the tests above and the decision-log entry still need review before the pilot starts.
