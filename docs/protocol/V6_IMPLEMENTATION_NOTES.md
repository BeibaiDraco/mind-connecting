# V6 continuous interaction: local implementation contracts

Status: unfrozen local prototype, 2026-10-12. This implements the current
`PROTOCOL_V6_CONTINUOUS_DRAFT.md` for review; it does not ratify its scientific
settings or authorize hardware use. Prior protocols, results and manuscript
sources are unchanged.

## Components

| Component | Implementation | Current boundary |
|---|---|---|
| Episode materials, private observations, actual device transitions | `src/mb/v6_tasks.py` | Draft task and display rules; material-only balancing |
| Backend-independent six-round scheduler | `src/mb/v6_runtime.py` | Complete natural, pulse, goal and text paths under a backend contract |
| Native cache and KV interface | `src/mb/v6_native.py` | Implemented; CUDA tests written but not executed |
| Ledger, exact synthetic resume and native artifact inventory | `src/mb/v6_run.py` | Synthetic execution complete; production native orchestration is not supplied |
| Episode scoring, availability and multiplicity | `src/mb/v6_analysis.py` | Complete analysis on generated ledgers; source/freeze admission remains external |
| Local material/tokenizer and synthetic CLI | `scripts/v6_local_preflight.py` | No model-loading or paid-execution command |
| Exact-analysis simulations | `scripts/v6_simulate_analysis.py` | Synthetic null/rival checks, not empirical model power |

## State and communication

Each side has its own full persistent cache and actual action history. The
shared checkpoint weights are not updated. The two model profiles are separate
experiments; this is not a Qwen-to-Llama bridge.

Private round updates are consumed with the link closed. Each round starts with
empty foreign windows while keeping the participant's own cache. At a global
work tick, both inputs are fixed before either participant advances. Only then
are the committed generated exports added to the next tick's windows. This
prevents evaluation-order leakage and enforces the one-tick delay. Exports
contain copied per-layer post-RoPE K/V and their original positions. Controller,
question and answer tokens never become exports.

The native attention interface is an isolated context with an exact softmax
mixture of own history and the foreign window, including the gain in log space.
It supports grouped query attention. It does not alter the historical runtime
or reuse its global bridge state. Temporary attention dispatch is restored on
exit, including errors. Native loading is CUDA-only and requires an explicit
hardware-acceptance flag; the local CLI cannot invoke it.

Ordinary work generation masks control and undefined vocabulary IDs. An actual
action uses the native-precision full-vocabulary greedy token. Its four legal
logits, probability and legal mass are separately recomputed through the FP32
output head. Those diagnostics need not have the same argmax as native BF16;
they never replace the action. Invalid actions remain invalid, follow the
declared device transition, and continue as the actual consumed token.

The finite tokenizer-specific control recovery table is a draft acceptance
contract. An end-of-turn token closes once; supported other controls receive
their fixed grammar recovery after retaining the actual token. Every recovery
is recorded. Unsupported categories fail closed. Text messages containing
strings that re-tokenize as native controls also fail closed. No unreviewed
escaping or sanitization policy is silently applied.

## Counterfactual branches and records

- Natural trajectories execute LIVE, A_TO_B, B_TO_A, OFF and FRESH through all
  six rounds, including both actual committed actions and their consequences.
- FRESH generates a new paired unconnected shadow stream each round, discards
  its shadow states, and presents that stream to the actual states. The actual
  states retain their earlier consequences. Thus FRESH remains an interactive
  cross-round rival.
- The early and late pulse branches clone the appropriate LIVE pre-event
  state. Both rounds execute actual actions before continuing. Replay fixes
  the source stream from the zero-pulse branch at the same round/work ticks.
  The zero-pulse replay is required to reproduce the live state exactly.
- Goal branches start from separate fixed-world checkpoints. Each measurement
  clones independently and is discarded. Goal questions cannot alter a future
  natural action or another measurement.
- Action and auxiliary access distributions are sealed before either actual
  answer is consumed. No controller message conveys the partner's answer.
- A pulse's fixed old/new causal targets are distinct from correctness against
  the actual device world reached after earlier real, possibly wrong actions.

There are 328 required readouts per base episode: 120 natural, 64 pulse and 144
goal. A selected text episode adds 24. Proposed N240 with a material-selected
N60 text subset therefore implies 80,160 rows per model, 160,320 across both.
These are expected draft counts, not collected scientific observations.

## Materials and scoring

Material generation is deterministic and stores complete input identities.
The preflight checks substantive episode duplication after removing labels,
seeds and stage names. At N240, the twelve ordered original-goal pairs, eight
side-by-beacon cells and displayed original goal names on each side are balanced.
Other joint margins are reported, not claimed to be exactly balanced. The N60
text subset uses only materials, never outputs, and must meet explicit balance
constraints; an unavailable subset is a blocker.

Four displayed labels map to episode-specific semantic answers. Invalid
full-vocabulary outputs produce `choice=null`, not a substituted label.
Technical failures are unavailable observations, not incorrect answers or
zero logits. Successful raw records are immutable and keyed by model, base
episode, path, checkpoint, version, round, side and question.

All inferential scores are aggregated within the base episode. The declared
two-model primary family always has 22 slots and the secondary family four;
missing tests retain p=1. Incomplete required components cannot yield a
confirmatory complete-case analysis. The sustained-response criterion also
requires the specified positive signs. A goal probe effect is not a selector.
Synthetic data are explicitly marked and cannot become scientific evidence.
Analysis alone does not verify model source, frozen inputs or runtime identity.

## Persistence and current limits

Synthetic resume verifies source, settings, materials and software identity
before any append. It validates all retained rows before recomputation. One
exact-identity retry is allowed per episode; existing successful rows must
reproduce exactly, and a complete no-op resume writes no bytes. Technical
attempt failures remain in append-only notes rather than fabricated success
rows. Corrupt tails and inconsistent rows fail closed without repair.

The artifact sink archives four LIVE pre-event pair snapshots, six FRESH tapes,
four zero-pulse tapes and two zero-goal tapes per episode. Pair snapshots contain
both native states, private world/action history and eligible windows. Tape
metadata fixes the round and original parent. Native state includes full cache,
tokens, last hidden state/logits, turn status and sealed readout/recovery state.
Greedy model decoding consumes no random sampling stream; material randomness
is already resolved in the episode. Restore binds tensors to the new backend
owner only after verifying exact model-parameter identity and checksums.

Native artifacts use tensor/primitive schemas, exclusive creation, file hashes
and an append-only inventory. Loading is CPU `weights_only=True` before native
validation and device restoration. Resume verifies all retained inventory files
before append. Interrupted orphan files are preserved and block overwriting.
These components do not yet constitute a certified production native
end-to-end resume controller. Real CUDA roundtrip, complete pair/world replay,
disk capacity, archive transfer cost and rehash throughput remain acceptance
items. Full parameter hashing adds one-time loading cost.

## Unresolved admission contract

The draft specifies general capability/access/format goals, but does not yet
fully specify the neutral material and collection contract. Four fields remain
explicitly null in `configs/v6/local_draft.yaml`:

1. The neutral fact stream and private event schedule.
2. Which round/checkpoint collects each neutral probe and on which clone.
3. How full-duration task and neutral CAP items aggregate within each side.
4. The exact N40 candidate pass predicate, including whether each specified
   precision bound applies before the independent N80 validation.

`neutral_gate_readiness` validates a narrow neutral-only data schema but always
returns unavailable while that contract is unresolved. It is not a working
selector. Baseline/calibration/validation materials from the current CLI are
main-task skeletons, not neutral admission datasets. There is no implemented
neutral collector or auto-continuation controller. The runtime's gain 0.5 is a
software-fixture default; `selected_gain` remains null.

Resolve and review those details prospectively with the PI, implement their
collector and exact gates, review native acceptance and measured storage needs,
then request a bounded hardware allowance. Neither the draft sample sizes nor
historical v5 financial approval authorizes this new experiment. No scientific
freeze, paid work or formal run is implied by these local code checks.
