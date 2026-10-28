# Review of the V7 runner (Codex, commit fc3cc25)

**Reviewer:** Claude Code. **Date:** October 28, 2026. **Scope:** `src/mb/v7_run.py`, the two override seams in `src/mb/run.py`, `tests/test_v7_runner.py`, and `docs/reviews/v7_runner_implementation_codex_20261028.md`. Read-only review of code and tests. No model or GPU was run.

## Verdict: approve for the engineering smoke and pilot once the PI approves the V7 draft

No defect found that affects the smoke or the pilot, which use base arms only. One registry change is needed before the generalization runs (item 1 below).

## What was checked

| Item | Finding |
|---|---|
| Arm registry | The 14 base arms match protocol §6 one-to-one: C0; full information (`fact_holder="A"`); ORIG/TRANS at w2; both with counterfactual N′; ORIG/TRANS at w1; both with RO readout; same-content ORIG/TRANS; strict-third-person ORIG/TRANS. Translation arms set `kv_position="before_own"`. Linked arms enable span logging; C0 arms do not. |
| Input mapping | `input_context` puts the counterfactual only on B (`source == "B"`). Same-content arms read A's context for B. Strict third person applies only to B. A's note is shared between an arm and its counterfactual partner, because A's card is identical. That is correct and saves generation. |
| Notes | Keyed by a hash of the full input context: episode, variant, source role, fact holder, effective counterfactual flag, frame and private-prefix hash. Notes for different cards cannot collide. The append-only log stores IDs and hashes; conflicting caches fail closed. |
| Prefix and spans | Private prefix (V7 card, plus the forced opener for strict third person), generated note, closure, then the reflection prompt (third-person prompt for third-person B). Spans: the material declarations plus `note` (which includes the opener, not duplicated), `closure` and `prompt`, all in logical half-open coordinates. `prefix_spans` refuses a mismatch with the actual prefix. |
| Same-content control | B's bank is A's complete P (card, A's note, prompt) with A's spans. The records mark fact holder "none" and set the USE expectation to null. Assignment-based question meanings are kept. |
| Questions | `v7_tasks.readout_questions` with the registered sets. U_OPEN appears exactly in the protocol's arms (1, 3, 4, 7, 8, 11–14). 14 × 18 forced-choice answers + 9 open reports = 261 trials per base episode. |
| Records | `record_metadata` plus arm ID, input sources, actual card hashes (correct for third-person and copied cards), note keys and bank summaries. Engine geometry identities are retained. |
| Identity, resume, launch | The run identity binds the schedule, arms, material tokens and spans, manifests and source hashes. Changed materials cannot be bypassed. Resume retries a failed trial once and does not impute. `--execute` requires the approved protocol SHA256; dev runs are limited to 12–24 episodes and the pilot to 80 base episodes. Completeness is always non-consumable; there is no automatic analysis or stage progression. |
| Tests | Production orchestration runs through a deterministic engine double for all three variants. It covers the arm/question matrix, identities, counterfactual routing, copied banks, third-person hashes, empty notes, span bounds, RO flags, NPZ serialization, resume and corruption paths. Strong for software contracts; they are not model evidence. |

## Items

1. **Before the generalization runs (required):** the protocol now has five generalization arms (adds ORIG w2 counterfactual, after Codex's review). Add `orig_w2_cf` to the generalization registry in `arms_for`, and update the coverage tests and the per-variant trial count (40 → 50). This does not affect the smoke or the pilot.
2. **Batch size (engineering):** `episodes_per_batch=8` (16 rows) is conservative compared with V3's 40 episodes on an H100. Choose it from the smoke timing (engine review R1), record the choice in the run config and STATUS, and keep it fixed through the formal run.
3. **Pilot analysis:** the pilot gates and the variance-only step are Claude's scripts (`scripts/v7_pilot_gates.py`, `scripts/v7_variance.py`). They will read only the fields the runner already writes (`v7.arm_id`, `label_meaning`, `label_logits`, `v7.use_expected_meaning`, CAP records, label mass). No runner change is needed.
