# V6 task clarity: local package, 2026-10-19

Status: locally implemented candidates and diagnostics. No hardware dispatch,
new financial allowance, numerical adoption, frozen-protocol replacement or
confirmatory continuation is authorized by this package.

The PI agreed that the task needs improvement after the offline action-failure
explanation. This package makes the proposed change concrete without starting a
GPU. The first question is whether Qwen reliably applies the task's rule when
all relevant inputs are explicit. Successful rule lookup is a prerequisite for
interpreting the later interaction experiment, not evidence of interaction.

## Implemented prompt candidates

P0 is the original system/private/action wording, preserved byte-for-byte.
P1 retains the original tables, private messages, names and choice IDs, adding:

> An assigned goal such as G0 is a policy label, not a destination or a beacon state. To choose a button, use your own latest assigned label and the OTHER participant's current beacon in the Action table. Your OWN current beacon is not the row selector. The Own-device transition table describes what happens AFTER you press the button; do not reverse it to decide which button to press.

P1 also makes both operands explicit in the action question:

> Using participant A's own latest assigned goal and participant B's CURRENT beacon, which button does the Action table prescribe for participant A?

P2 adds only a different rendering of the same action mapping. Each goal gets
one explicit conditional sentence. For example, the already exposed example
codebook would say:

> G0: if the OTHER participant's current beacon is Dim, press Down; if it is Bright, press Left.

That example is illustrative, not a new validation case. The actual 64 diagnostic
inputs use fresh allocated materials. P2 keeps the own-device consequence table
unchanged. It does not remove goal updates, private information or the need to
respond to the other side. Preparation/work-note instructions remain unchanged
so a new note format is not bundled into this first comparison.

## First diagnostic: short rule questions

- Eight new codebooks, four goals and two partner beacons per codebook: 64 cases.
- Across codebooks, each literal goal/partner-beacon cell contains both roles and
  both own/partner-beacon agreement states twice. Correct answer IDs are balanced
  at 16 each across the 64 cases.
- P0/P1/P2 use exactly the same physical cases and correct answers.
- Each variant is evaluated on reference and optimized backends: 384 scored
  one-token answers total. Fresh state per question, no bilateral work, no
  generated preparation, no pulse branch, no performance campaign.
- Serialization is explicit: system/private user/open assistant; close the empty
  assistant turn, append the full-information question, score its native answer.
  Both backends must use the same native sequence. The empty turn was checked
  against the local official tokenizer template. This diagnostic deliberately
  omits the six-round generated history and is not the original scientific task.
- Correct answers are scorer-side fields. Do not send a serialized material JSON
  or manifest containing the answer to the model. The collector constructs only
  the system, private and question strings.

The prior proposed development screen remains 58/64, with P1 then P2 as the fixed
clarified-candidate preference and P0 retained as the control. It is not ratified
in this implementation. No selector, GPU launcher or automatic continuation has
been added. Reporting must retain individual codebook/role/own-beacon/answer-ID
results, all failures and all numerical differences. Backend admission still
needs its explicit numerical contract; matching accuracy alone is insufficient.

## Conditional diagnostic: six-round history

Eight further new episodes are allocated separately. Each early focal side has
all four initial beacon pairs, and each literal initial goal occurs twice on
each physical side. Actual goal updates and private-device transitions use the
unchanged task implementation. The variant and backend are not selected yet.

The collector is OFF-only with gain zero, 16 preparation tokens per side and 64
work tokens per side per round. On each of the 96 side/round decisions it collects:

1. Latest-goal query on a discarded clone.
2. Action query with current own goal and partner beacon explicitly supplied,
   on a discarded clone.
3. The same assisted action query with the unchanged decision table repeated,
   on a discarded clone.
4. Ordinary action, whose actual native answer alone is committed.

This yields 384 readouts. Diagnostic answers never feed the continuing history.
Both ordinary answers are sealed before updating either side's world. Invalid
actual answers remain invalid and hold that participant's beacon; no oracle
replacement is introduced. Technical exceptions propagate and there is no retry
loop. Raw sinks retain completed observations before any later exception.

Record full token histories before each round's action queries, the exact 64
work tokens and decoded final 16 tokens, plus the final committed history. This
addresses the missing TEXT/neutral transcript visibility encountered in the old
fixtures. It does not require tensor archives for every diagnostic query.

The prior suggested 87/96 explicit-input-action screen is also unratified. It is
a development check, not a substitute for the original scientific confidence
bounds or an authorization for the next stage. Core LIVE/FRESH/cut/Replay and
formal collectors are not connected to this module.

## Local preparation and verification

Implementation: `src/mb/v6_task_clarity.py`.
Tests: `tests/test_v6_task_clarity.py`.
Local-only writer:

```bash
.venv/bin/python scripts/prepare_v6_task_clarity.py --output /private/tmp/NEW-EMPTY-DIRECTORY
```

It writes 192 prompt inputs, short and history materials, and a source/data-hashed
manifest. The output directory must not already exist. The manifest explicitly
sets GPU launch and automatic continuation to false, has no selected history
variant, and marks thresholds unratified. It contains no connection or credential.

Actual current bundle: `/private/tmp/mb-v6-task-clarity-20261019/prepared-01/`.
Backend-injected collectors support future native execution but neither load a
model nor acquire hardware. Real collectors require persistent record sinks;
the history collector additionally requires a token-history sink. Synthetic
software checks are always marked synthetic and non-scientific.

Before a future paid trial: bind a finite scope/allowance and stop protection,
verify model/source/assets and numerical comparison requirements, persist exact
inputs and outputs, and independently check closure/backup/actual stop. No need
to rerun an entire two-model timing campaign to ask these task questions.
The preserved frozen sources, old failures and previous costs remain intact.
