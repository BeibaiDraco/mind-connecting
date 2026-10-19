# Fixed-scene partner-goal and work/readout isolation: complete results

2026-10-19, Codex root evidence audit. Prospective scope: `v6_goal_stage_plan_20261019.md`. This report covers every condition in the two exposed initial layouts; it is not an independent-agent review, new confirmation sample or formal admission.

## Main conclusion

Changing only the partner assignment can change the recipient's own-rule answer while its own goal report stays correct. The response does not reliably copy the partner's rule: some errors match a third assignment, and one recipient retains its own rule throughout. Both connected work and the held-window readout can contribute. There are errors that survive a disconnected readout after connected work, errors induced by connecting only during readout, and errors requiring the combination. These findings localize influence in this implementation; they do not demonstrate reliable goal transfer, useful cooperation, durable memory or a necessity for reciprocal rather than open-loop input.

## Integrity and scope

All 240 readouts and 24 paired work traces completed in 944.58 seconds (15.74 minutes). Both worker and supervisor terminated successfully. The 270,223,360-byte archive and all 265 raw files were SD-backed-up and independently rehashed. All 240 saved full-vocabulary arrays are finite, produce the recorded native argmax, and map to legal answer options. Two initial native pair artifacts passed restoration.

The independent saved-data audit checks the same beacon world, fixed recipient goal and prepared native state across donor-goal variants; identical post-work state for each pair of readout settings; 64 synchronous work ticks per branch and empty OFF routing; and zero committed actions. Forty exact full-array comparisons verify that W0R0 recipient answers do not depend on the unobserved partner goal. A further post-hoc baseline audit compares the original partner-goal W1R1 branches with the previous channel diagnostic's first-round LIVE records: all 16 shared question arrays and consumed-token histories match exactly. This ties the new intervention to the earlier baseline without treating the reuse as independent replication.

W means 64-token work with a live, synchronous bidirectional connection. R means answering with the final held partner window; this readout itself is not another live reciprocal exchange. W0R1 uses the disconnected partner's actual generated window. All conditions use the original native backend, gain 1.0, 64/16/16 clocks, the fixed base P2/work instruction and no SELF_REPORT or oracle factual prompt. Answers, including actions, are discarded and never advance the world.

## Complete stage summaries

Each denominator is 12 fixed recipient-context/partner-goal combinations: two layouts × two recipients × three donor assignments. These are not 12 independent episodes; the 240 readouts are also not independent samples. Own-rule correctness refers to the selected Dim/Bright pair, labeled below by the assignment whose public rule it matches.

| Work / readout | Own rule correct | Own goal correct | Partner goal correct | Partner beacon correct | Action correct | Wrong own-rule answer matching partner |
|---|---:|---:|---:|---:|---:|---:|
| W0R0 | 12/12 | 12/12 | 2/12 | 0/12 | 0/12 | 0 |
| W0R1 | 10/12 | 12/12 | 2/12 | 0/12 | 0/12 | 0 |
| W1R0 | 9/12 | 12/12 | 2/12 | 0/12 | 0/12 | 1 |
| W1R1 | 7/12 | 12/12 | 2/12 | 0/12 | 2/12 | 3 |

All 48 own-goal answers are correct. Explicit partner-beacon answers are wrong in all 48 cells; Unknown occurs in 6/12, 7/12, 12/12 and 12/12 respectively. Partner-goal accuracy stays 2/12 in every arm and does not show reliable explicit access: a constant default guess can match one of the three donor assignments. The two correct W1R1 actions occur in layout 1/B with donor G2 and layout 2/A with donor G3. Neither is accompanied by a correct explicit partner-beacon answer. No outcome threshold or population test was applied.

## Every recipient's three-goal response vector

Within each row, the recipient, its beacon, the partner beacon, public table, option order and required action are fixed. Vectors follow the listed partner-goal order. A changed vector therefore concerns an intervention on the partner's private initial assignment and its downstream generated state, not a change of the recipient's task or a divergent action history.

| Layout / recipient | Own goal | Partner-goal order | W0R0 selected rule | W0R1 selected rule | W1R0 selected rule | W1R1 selected rule |
|---|---|---|---|---|---|---|
| 1/A | G1 | G2, G3, G0 | G1, G1, G1 | G1, G1, G1 | G0, G3, G1 | G0, G3, G1 |
| 1/B | G0 | G1, G2, G3 | G0, G0, G0 | G0, G0, G0 | G0, G0, G0 | G0, G0, G0 |
| 2/A | G2 | G1, G0, G3 | G2, G2, G2 | G0, G2, G0 | G2, G2, G0 | G2, G0, G0 |
| 2/B | G0 | G1, G2, G3 | G0, G0, G0 | G0, G0, G0 | G0, G0, G0 | G1, G0, G0 |

**Layout 1/A: an influence already present before the readout, with incomplete rule tracking.** A's own goal is G1. With connected work and a disconnected readout, donor goals G2/G3/G0 yield selected rules G0/G3/G1. Thus changing the donor can change the answer even after the readout link is removed, but only the G3 case copies the donor rule; G2 produces a third rule and G0 leaves the own rule correct. Readout-only connection leaves G1 correct for all three donor goals. In the generated work note for donor G2, A actually states G1 while describing the G2 rule; the later rule-choice readout selects G0. The generated text and selected rule are distinct observed outputs and must not be substituted for each other.

**Layout 1/B: no own-rule shift.** B selects its correct G0 rule for all three partner goals in all four arms. Its action answers can still change, including the single correct Left answer under W1R1 with donor G2. This negative rule result is part of the complete evidence.

**Layout 2/A: both stages contribute in a context-dependent way.** A's own goal is G2. With work disconnected, connecting the readout changes its rule answer to G0 for donors G1 and G3; neither error matches the actual donor goal. Connected work with readout disconnected leaves the rule correct for donors G1/G0 but produces G0 for donor G3. With donor G0, the error appears only when both stages are connected. Connected work can also remove a readout-only error: donor G1 is wrong in W0R1 and correct in W1R1. There is no justified simple additive decomposition of the two stages.

**Layout 2/B: the combination is needed for the observed rule shift.** B's own goal is G0. Only W1R1 with donor G1 produces the partner-matching G1 rule; W0R1 and W1R0 retain G0. Donors G2/G3 leave the rule correct across all arms. The work note for donor G1 contains a G0 heading and the G1 Dim/Bright pair, while the disconnected rule readout still answers G0. Again, a note alone does not settle what any later probe will report.

## Interpretation and remaining uncertainty

This controlled intervention narrows the earlier observational association of nine partner-matching errors. It shows real sensitivity to the partner-assignment intervention in some contexts, but supports neither universal tracking nor the claim that every error is a copied partner rule. New errors can match a third rule, and both the generated work text and the question-specific answer can be inconsistent. No record was discarded for contradicting the earlier hypothesis.

W1R0 effects cannot be explained solely by foreign input added at the final question: the readout receives no partner window. Influence can remain in the recipient's generated history/native state through that immediate measurement. This does not distinguish altered textual history from other cached-state changes, demonstrate persistence over further rounds, or establish that the partner's responsiveness is necessary. A fixed recorded donor with matched content remains an untested alternative in this batch.

W0R1 errors demonstrate that the measurement path itself can induce an error without prior connected work. Consequently, a linked rule readout is not a transparent measurement of a fixed internal belief. These small reused contexts and one fixed gain do not license generalization across prompts, tasks or models. Partner-goal changes also change generated content; semantic assignment transfer, rule/answer imitation and broader attention interference are not separated here.

No new GPU test is launched. A next proposal could isolate recipient generated-text history from the held-window measurement, or compare a matched recorded donor with live responsive work at the same fixed scene. Such a test needs a separately specified small scope. The present result does not select a prompt, gain, model or formal continuation.

## Operational closure

At the independent actual-state check, both exact diagnostic processes had exited, the GPU was idle, the provider was running and the original local/remote guardians were healthy. The completed diagnostic heartbeat was paused. Keep the original four-hour/USD8 rental origin, 2GiB egress cap and 18:32:18 Chicago stop-request /18:37:18 lifecycle cutoff; neither a restart nor extension was requested. Completion here does not assert that the future fixed stop has already occurred.

Offline tests: 1264 passed, 10 skipped, one GPU test deselected (49.50 seconds). The original scientific sources and historical failures remain unchanged. All outputs and copied controls are under SD `v6/replacement-clarity-20261019-goal-stage-diagnostic1/`; private receipts include `backup_verified.json`, `analysis.json`, `descriptive_crosscheck.json` and `actual_state.json` in the matching `goal-stage-diagnostic-1` root.

## All 48 cells, including every failure

Rule entries name the public assignment whose Dim/Bright pair was chosen. Goal/rule/fact/action correctness is marked with yes/no in parentheses. Each context has one fixed correct action, shown in its heading; changing the donor does not change that truth.

### Layout 1, recipient A, own goal G1, required action Up

| Partner goal | Arm | Own rule | Own goal | Partner goal report | Partner beacon report | Action |
|---|---|---|---|---|---|---|
| G2 | W0R0 | G1 (yes) | G1 (yes) | G3 (no) | Unknown (no) | Down (no) |
| G2 | W0R1 | G1 (yes) | G1 (yes) | G3 (no) | Unknown (no) | Down (no) |
| G2 | W1R0 | G0 (no) | G1 (yes) | G3 (no) | Unknown (no) | Right (no) |
| G2 | W1R1 | G0 (no) | G1 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G3 | W0R0 | G1 (yes) | G1 (yes) | G3 (yes) | Unknown (no) | Down (no) |
| G3 | W0R1 | G1 (yes) | G1 (yes) | G3 (yes) | Unknown (no) | Down (no) |
| G3 | W1R0 | G3 (no) | G1 (yes) | G3 (yes) | Unknown (no) | Down (no) |
| G3 | W1R1 | G3 (no) | G1 (yes) | G3 (yes) | Unknown (no) | Down (no) |
| G0 | W0R0 | G1 (yes) | G1 (yes) | G3 (no) | Unknown (no) | Down (no) |
| G0 | W0R1 | G1 (yes) | G1 (yes) | G3 (no) | Unknown (no) | Down (no) |
| G0 | W1R0 | G1 (yes) | G1 (yes) | G3 (no) | Unknown (no) | Down (no) |
| G0 | W1R1 | G1 (yes) | G1 (yes) | G1 (no) | Unknown (no) | Down (no) |

### Layout 1, recipient B, own goal G0, required action Left

| Partner goal | Arm | Own rule | Own goal | Partner goal report | Partner beacon report | Action |
|---|---|---|---|---|---|---|
| G1 | W0R0 | G0 (yes) | G0 (yes) | G0 (no) | Dim (no) | Right (no) |
| G1 | W0R1 | G0 (yes) | G0 (yes) | G0 (no) | Dim (no) | Right (no) |
| G1 | W1R0 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Down (no) |
| G1 | W1R1 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Down (no) |
| G2 | W0R0 | G0 (yes) | G0 (yes) | G0 (no) | Dim (no) | Right (no) |
| G2 | W0R1 | G0 (yes) | G0 (yes) | G0 (no) | Dim (no) | Right (no) |
| G2 | W1R0 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G2 | W1R1 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Left (yes) |
| G3 | W0R0 | G0 (yes) | G0 (yes) | G0 (no) | Dim (no) | Right (no) |
| G3 | W0R1 | G0 (yes) | G0 (yes) | G0 (no) | Dim (no) | Right (no) |
| G3 | W1R0 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G3 | W1R1 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |

### Layout 2, recipient A, own goal G2, required action Down

| Partner goal | Arm | Own rule | Own goal | Partner goal report | Partner beacon report | Action |
|---|---|---|---|---|---|---|
| G1 | W0R0 | G2 (yes) | G2 (yes) | G0 (no) | Unknown (no) | Left (no) |
| G1 | W0R1 | G0 (no) | G2 (yes) | G0 (no) | Unknown (no) | Left (no) |
| G1 | W1R0 | G2 (yes) | G2 (yes) | G0 (no) | Unknown (no) | Left (no) |
| G1 | W1R1 | G2 (yes) | G2 (yes) | G0 (no) | Unknown (no) | Left (no) |
| G0 | W0R0 | G2 (yes) | G2 (yes) | G0 (yes) | Unknown (no) | Left (no) |
| G0 | W0R1 | G2 (yes) | G2 (yes) | G0 (yes) | Unknown (no) | Left (no) |
| G0 | W1R0 | G2 (yes) | G2 (yes) | G0 (yes) | Unknown (no) | Left (no) |
| G0 | W1R1 | G0 (no) | G2 (yes) | G0 (yes) | Unknown (no) | Right (no) |
| G3 | W0R0 | G2 (yes) | G2 (yes) | G0 (no) | Unknown (no) | Left (no) |
| G3 | W0R1 | G0 (no) | G2 (yes) | G0 (no) | Unknown (no) | Left (no) |
| G3 | W1R0 | G0 (no) | G2 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G3 | W1R1 | G0 (no) | G2 (yes) | G0 (no) | Unknown (no) | Down (yes) |

### Layout 2, recipient B, own goal G0, required action Up

| Partner goal | Arm | Own rule | Own goal | Partner goal report | Partner beacon report | Action |
|---|---|---|---|---|---|---|
| G1 | W0R0 | G0 (yes) | G0 (yes) | G0 (no) | Bright (no) | Right (no) |
| G1 | W0R1 | G0 (yes) | G0 (yes) | G2 (no) | Bright (no) | Right (no) |
| G1 | W1R0 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G1 | W1R1 | G1 (no) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G2 | W0R0 | G0 (yes) | G0 (yes) | G0 (no) | Bright (no) | Right (no) |
| G2 | W0R1 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G2 | W1R0 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G2 | W1R1 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G3 | W0R0 | G0 (yes) | G0 (yes) | G0 (no) | Bright (no) | Right (no) |
| G3 | W0R1 | G0 (yes) | G0 (yes) | G0 (no) | Bright (no) | Right (no) |
| G3 | W1R0 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |
| G3 | W1R1 | G0 (yes) | G0 (yes) | G0 (no) | Unknown (no) | Right (no) |

