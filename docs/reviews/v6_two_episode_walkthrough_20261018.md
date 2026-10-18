# Two saved Qwen engineering episodes: descriptive walkthrough — 2026-10-18

## Conclusion and scope

There is a concrete, intervention-sensitive reciprocal-response example at the
late checkpoint of episode **000001**. The early checkpoint fails to complete
the response chain in both episodes. Episode **000000** has correct actions in
its changed late LIVE branch, but neither target action changes between the
unflipped and flipped LIVE worlds: it does not show an adaptive forward response.
The two cases therefore do not establish sustained, reliable reciprocal control.
They motivate inspecting scientific feasibility rather than immediately running
the entire confirmatory package.

The PI explicitly authorized examining both already completed full-clock
engineering episodes, including successes and failures, without new GPU work.
This is the first substantive walkthrough of these saved outcomes. No new
inference, rental, scientific collection, gain selection or protocol amendment
was performed. Both episodes use Qwen3-4B-Instruct-2507, the optimized engineering
backend, gain 1.0, six rounds, 64 work tokens, 16 preparation tokens and a
16-position generated window. Gain 1.0 was an engineering setting, not selected
by a passed scientific calibration. The backend remains scientifically
unadmitted. These are two independent base episodes, not 680 independent trials
or four independent checkpoint samples. No p values, significance claims or
population confidence intervals are computed.

Case labels below follow the episode suffix, not shuffled batch order:

- Case 1: `performance_only_20261014_qwen3_4b_instruct_2507-bb6d4c0173267e3a-000000`.
- Case 2: `performance_only_20261014_qwen3_4b_instruct_2507-bb6d4c0173267e3a-000001`.

Only case 2 was preselected for TEXT. The short-repeat fixture is not added as
another independent sample. Button names are permuted between cases; compare
the task's fixed physical meanings within a case, not matching words across cases.

## Reconstruction checks

All 680 records are present, unique and technically successful. Reconstructed
materials match the immutable material hash; final records match their receipt
and the incrementally recorded rows after removing only their documented
`engineering_only: true` marker and accounting for interleaved lane order.
All 680 question truths and candidate mappings were checked against worlds
reconstructed from actual submitted actions, never oracle-corrected actions.
A separately written arithmetic table rule agrees with each action truth.

All 64 applicable unchanged-event Replay readouts match LIVE exactly in actions,
logits, probabilities and candidate mappings. All 16 q1/L pulse readouts match
their main LIVE trajectory counterparts. Directly reconstructed pulse contrasts
agree with the existing episode-level scorer. These local checks do not rerun
the models or independently re-execute their internal caches; complete archive
restoration was audited in the closed engineering attempt.

Every submitted response is an allowed answer token. Minimum legal probability
mass across all probes is approximately 0.7022, so allowed realized choices
must not be confused with passing the separate scientific format/admission
rules. Ledger completeness is not scientific admission.

## Whole trajectories: local success is not reliable overall performance

Each action denominator is 12 decisions: two sides over six rounds. These are
descriptive counts within an episode, not an inferential sample of twelve.

| Communication policy | Case 1 correct actions | Case 2 correct actions |
|---|---:|---:|
| LIVE, continually coupled | 7/12 | 5/12 |
| A to B only | 4/12 | 6/12 |
| B to A only | 2/12 | 3/12 |
| OFF | 3/12 | 6/12 |
| FRESH, new outgoing tape each round | 4/12 | 2/12 |
| TEXT | Not assigned | 2/12 |

LIVE exceeds FRESH by three correct decisions in each case; on the predefined
rounds-2-through-6 score this is +0.30 in each case. This describes these cases
only. LIVE exceeds OFF in case 1 but is worse than OFF in case 2. Policies
develop different actual histories/worlds, so these are not common-world causal
contrasts or evidence of a universal benefit of coupling. FRESH is interactive
across rounds, and these two weak FRESH trajectories do not establish that fresh
information exchange generally cannot solve the task.

In the main LIVE trajectories, both sides are correct together in 2/6 rounds
for case 1 and 1/6 rounds for case 2. A correct two-round response chain concerns
the responder at one round and initiator at the next; it does not imply both
sides are correct at every action in those rounds.

### Main LIVE trajectory, including every failed action

Entries are actual button / correct button. Checkmarks refer to each branch's
actual physical world and latest authorized goal.

| Case | Round | A actual / required | B actual / required |
|---|---:|---|---|
| 1 | 1 | Right / Up ✗ | Right / Down ✗ |
| 1 | 2 | Up / Up ✓ | Up / Up ✓ |
| 1 | 3 | Up / Left ✗ | Up / Up ✓ |
| 1 | 4 | Up / Left ✗ | Up / Up ✓ |
| 1 | 5 | Down / Down ✓ | Up / Up ✓ |
| 1 | 6 | Down / Right ✗ | Up / Up ✓ |
| 2 | 1 | Right / Left ✗ | Right / Right ✓ |
| 2 | 2 | Down / Down ✓ | Down / Down ✓ |
| 2 | 3 | Right / Down ✗ | Right / Left ✗ |
| 2 | 4 | Right / Down ✗ | Right / Left ✗ |
| 2 | 5 | Up / Up ✓ | Up / Left ✗ |
| 2 | 6 | Down / Up ✗ | Down / Down ✓ |

## What counts as a response-chain clue

At round 2 the initiator I is A and responder J is B. At round 5 the roles
reverse. From the same saved LIVE history, q0 leaves I's beacon alone and q1
flips it. The responder's new private goal is identical in q0/q1. Measure J's
action in that round and I's action in the following round. Fcut closes I→J;
Rcut closes J→I. Replay replaces J→I with the matched unflipped recording.
Both participants keep computing in all arms.

Both saved episodes use A as the early initiator and B as the late initiator.
Consequently the apparent early/late difference is also confounded with physical
role, changed goals and visited history. It cannot show that the models learned
to interact over time or that one physical direction is generally stronger.

The three contrasts measure forward response beyond Fcut, returning response
beyond Rcut, and returning response beyond Replay. The chain-quality score is
+1 only when both changed-LIVE target actions choose the fixed new oracle
candidates; it alone does not require change from q0 and cannot rescue an absent
forward contrast. The following are raw episode scores, not tested effects:

| Case / checkpoint | Forward | Return | Return versus Replay | Chain quality |
|---|---:|---:|---:|---:|
| 1 / early, rounds 2–3 | +0.5 | 0 | 0 | 0 |
| 1 / late, rounds 5–6 | 0 | +1.0 | +0.5 | +1 |
| 2 / early, rounds 2–3 | +0.5 | 0 | 0 | −0.5 |
| 2 / late, rounds 5–6 | +1.0 | +0.5 | +0.5 | +1 |

Only the last row has all four favorable signs in this descriptive check.
Neither case meets the proposed early-and-late sustained-response pattern.
Four checkpoint rows must not be converted into a population success rate.

## Case 2, late: the clearest positive example

Before round 5, both beacons are Dim. B's beacon is either left Dim or flipped
Bright. A receives the same new G2 assignment in both branches. Under A's
permuted action table, the appropriate response switches from Right to Up.
Right makes A's next beacon Dim; Up makes it Bright. B's own G1 assignment then
requires Left for a Dim A beacon and Down for a Bright A beacon.

| Arm | A at round 5, q0 → q1 | B at round 6, q0 → q1 |
|---|---|---|
| LIVE | Right → Up | Right → Down |
| Fcut, B→A closed | Right → Right | Right → Up |
| Rcut, A→B closed | Right → Up | Right → Right |
| Replay, matched q0 A→B recording | Right → Right | Right → Right |

The q1 LIVE branch contains the specific sequence **B beacon flip → A chooses
Up → A beacon becomes Bright → B chooses Down**. Closing B→A removes A's
appropriate change. Closing A→B preserves A's appropriate change but removes
B's returning change. This directional pattern is the strongest cue in the
saved cases: it is more informative than simply observing different answers
when a channel is enabled.

It is not a flawless controller. In q0 LIVE, B chooses Right when Left is
required. In q1 LIVE, B's round-5 action and A's round-6 action are also wrong,
even though the two focal chain actions are correct. Replay additionally changes
A's behavior and subsequent worlds, so LIVE–Replay is not an equal-content or
identical-later-world comparison. The case supports a local channel-mediated
feedback interpretation, not generic planning, a special self mechanism or
reliable sustained interaction.

## Case 1, late: two correct target actions without adaptive LIVE response

Here B's beacon is Bright in q0 and flipped Dim in q1. A's appropriate round-5
action should switch Right → Down. The fixed ideal chain would then change B's
round-6 response Left → Up.

| Arm | A at round 5, q0 → q1 | B at round 6, q0 → q1 |
|---|---|---|
| LIVE | Down → Down | Up → Up |
| Fcut | Right → Right | Up → Right |
| Rcut | Up → Left | Up → Left |
| Replay | Down → Right | Up → Right |

LIVE already chooses Down and Up without the flip and repeats both after it.
The q1 target actions are correct, but the forward LIVE delta is zero. Its
return delta is also zero. The +1 return contrast arises because Rcut's signed
fixed-candidate delta is −1, not because LIVE acquired a positive returning
response. Rcut's B actions can still be correct in Rcut's different actual
worlds; a negative fixed-candidate delta is not automatically poorer task
accuracy. This distinction prevents a misleading success claim from contrasts
or changed-world correctness alone.

## Early checkpoints: forward clues, incomplete return

| Case / arm | B at round 2, q0 → q1 | A at round 3, q0 → q1 |
|---|---|---|
| 1 / LIVE | Right → Up | Right → Up |
| 1 / Fcut | Up → Up | Right → Down |
| 1 / Rcut | Right → Up | Right → Up |
| 1 / Replay | Right → Up | Right → Up |
| 2 / LIVE | Right → Down | Right → Right |
| 2 / Fcut | Right → Right | Right → Right |
| 2 / Rcut | Right → Up | Right → Right |
| 2 / Replay | Right → Down | Right → Right |

In case 1 B's changed-LIVE Up is the new correct response. A should subsequently
choose Left, but chooses Up. A changes its answer, yet the change is not the
required return response and is reproduced with the return path cut or replayed.

In case 2 B's changed-LIVE Down is correct. A should then choose Down, but stays
on Right, an unrelated wrong action. There is no returning behavioral change.
Thus both cases contain a forward-direction cue at the early checkpoint,
without a complete correct feedback chain. A positive early forward contrast
alone must not be described as reciprocal success.

## Additional failures and preserved abilities

Main LIVE partner-beacon reports are correct in **1/12** queries for case 1
and **0/12** for case 2. The other 23 reports say **Unknown**, a valid offered
answer, not malformed output. This does not prove that no partner-dependent
information influenced the actions; the intervention traces show behavior can
depend on the channel despite weak explicit reports. It does prevent claiming
reliable explicit access from these two trajectories.

Case 2 TEXT reports the partner's beacon correctly in **12/12** queries but
chooses the correct task action only **2/12** times. These are different actual
TEXT histories, so this is not an information-matched estimate against LIVE.
It does show that correct explicit information reporting alone is insufficient
for reliable action in this saved task. Rule execution, current-goal use and
prompt interpretation remain competing explanations; these records do not
identify a single cause.

The existing discarded goal probes provide another limited diagnostic. Under
their LIVE arm (eight queries per question type per case):

| Probe | Case 1 correct | Case 2 correct |
|---|---:|---:|
| Original assigned goal | 8/8 | 8/8 |
| Latest assigned goal | 4/8 | 8/8 |
| Fact-complete action using a fresh goal-to-button mapping | 4/8 | 5/8 |
| Partner's latest goal | 3/8 | 1/8 |

Original-goal reports are preserved, so the cases are not uniformly incoherent.
Case 2's accurate latest-goal reports coexist with imperfect fact-complete
actions. These are separate probes on cloned states; they suggest separating
record reporting from application of the rule, not that a common single cause
has been identified. No goal-takeover or self-specific conclusion follows.

## What this changes operationally

The evidence warrants a bounded scientific feasibility investigation. It does
not warrant dismissing the idea, declaring success or launching N240 for both
models. First inspect why correct reported facts/goals often fail to produce
correct actions, and then test whether the favorable late directional pattern
recurs on independent materials. Any outcome-informed prompt/task changes are
exploratory revisions and must be documented prospectively; these viewed cases
cannot serve as blind validation or be included in later confirmatory data.
Any small pilot should balance the initial focal side prospectively; taking
the first twelve generator indices would not do this because the existing
generator alternates focal side by twelve-episode blocks.
No parameters were selected from these effects, and no new pilot is authorized
or launched by this report. Existing frozen gates and Llama's numerical failure
remain unchanged.

## Reproduction and files

Input directory:
`/Volumes/VERBATIM SD/mind-connecting-data/v6/qwen-timing-20261018/restored/output/qwen3_4b_instruct_2507/full_cohort/`.
Final record SHA256:
`62cb0571ab7708481f859fc91de5a946ec2dd786f334278eeda2322950e2329e`.

Torch-free reconstruction and the complete named trajectories/branch worlds
are in `/private/tmp/mb-v6-two-episode-walkthrough-20261018/reconstruct.py` and
`walkthrough.json`. Every input's SHA256 is recorded in the output. The derived
files are separately backed up under the SD data root at
`v6/two-episode-walkthrough-20261018/`; raw originals are unchanged.

The analysis checks full coverage, exact material/record identity, all actual
worlds and question mappings, unchanged Replay readouts, q1/L/main alignment,
and agreement of independent pulse arithmetic with the existing scorer. It
does not call inferential tests. Full offline suite: 1,234 passed, ten skipped,
one deselected.
