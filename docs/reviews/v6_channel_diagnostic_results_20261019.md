# Small channel and own-rule diagnostic: complete two-case results

2026-10-19, Codex root evidence audit. This is a descriptive exploratory report, not an independent-agent review or scientific admission. The prospective plan is `v6_channel_diagnostic_plan_20261019.md`. No new model execution followed this analysis.

## What completed

Two fresh Qwen pairs each completed three actual-action-driven rounds under LIVE, OFF, LIVE_SELF_REPORT, OFF_SELF_REPORT and TEXT_FACTS. All 300 native readouts completed in 958.31 seconds (15.97 minutes), including artifact restoration in the measured worker interval. Both worker and supervisor exited successfully. The 287,262,720-byte raw archive and all 324 inventory files were copied to the SD card and independently rehashed. All 300 full-vocabulary arrays are finite and reproduce their saved native argmax and answer mapping. The auditor reconstructed all 30 pair-round worlds from actual committed actions, checked the displayed action rules, two restored common initial states, 30 work traces, discarded-probe integrity, common-parent isolation and OFF routing.

The source remains the original native backend, fixed exploratory gain 1.0 and 64/16/16 clocks. There were no missing, invalid or retried answers. There are two episode-level units; 300 readouts and repeated sides/rounds/conditions are not independent samples. No statistical test, selection threshold, parameter adoption or formal continuation was performed.

## All conditions and both cases

Each cell below is correct answers out of six (two sides over three rounds). Own-goal answers are 6/6 for every row. Pair-own and pair-partner refer to the two components of the four-option beacon-pair question; these components are not additional independent observations. Unknown is a response to the separate partner-beacon question.

### Case 1: `v6_channel_explore_20261019-657ad721dbf53026-000000`

| Condition | Action | Own rule | Partner beacon | Whole beacon pair | Pair-own | Pair-partner | Unknown |
|---|---:|---:|---:|---:|---:|---:|---:|
| LIVE | 1/6 | 4/6 | 0/6 | 1/6 | 5/6 | 1/6 | 6/6 |
| OFF | 3/6 | 6/6 | 1/6 | 2/6 | 6/6 | 2/6 | 3/6 |
| LIVE_SELF_REPORT | 2/6 | 3/6 | 0/6 | 1/6 | 5/6 | 1/6 | 6/6 |
| OFF_SELF_REPORT | 2/6 | 6/6 | 0/6 | 2/6 | 6/6 | 2/6 | 5/6 |
| TEXT_FACTS | 6/6 | 6/6 | 6/6 | 4/6 | 4/6 | 6/6 | 0/6 |

### Case 2: `v6_channel_explore_20261019-b7b23db9c9d9bd98-000000`

| Condition | Action | Own rule | Partner beacon | Whole beacon pair | Pair-own | Pair-partner | Unknown |
|---|---:|---:|---:|---:|---:|---:|---:|
| LIVE | 1/6 | 4/6 | 0/6 | 1/6 | 6/6 | 1/6 | 5/6 |
| OFF | 1/6 | 6/6 | 1/6 | 1/6 | 6/6 | 1/6 | 2/6 |
| LIVE_SELF_REPORT | 2/6 | 4/6 | 0/6 | 4/6 | 6/6 | 4/6 | 5/6 |
| OFF_SELF_REPORT | 2/6 | 6/6 | 0/6 | 3/6 | 6/6 | 3/6 | 6/6 |
| TEXT_FACTS | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 0/6 |

## Findings and failures

**Explicit factual access is largely sufficient in these cases, but not perfect.** TEXT_FACTS supplied only the actual current partner beacon before work, with the latent link off. Actions were 6/6 and 5/6, own rules 6/6 in each case and partner reports 6/6 in each case. LIVE actions were 1/6 in each case, with partner reports 0/6. OFF actions were 3/6 and 1/6. These naturally evolving trajectories encounter different worlds after their actions diverge; the totals are not a matched-world estimate of a connection effect. They do not prove that task design or action readout is fully solved.

**The residual text-control failure separates a generated note from the committed answer.** In case 2, round 1, A correctly reported its goal, rule and partner beacon; its generated note correctly concluded Down. The actual action question listed Up/Down/Left/Right as options 1/2/3/4, but native argmax selected option 3 (Left). Saved legal logits for Down and Left were 42.1585502625 and 43.6547622681. The world correctly advanced using Left. This is an observable output inconsistency; the data do not identify its internal cause, and the note must not replace the action in scoring.

**A more specific unexpected association: correct goal labels coexist with partner-matching rule answers.** Across the 24 linked own-rule readouts (both LIVE variants), nine were wrong, and all nine selected the rule for the partner's current assignment. All 24 linked own-goal reports were correct. The 24 OFF-variant own-rule reports and 12 TEXT_FACTS own-rule reports were correct. An additional post-hoc semantic check parsed every one of the 60 displayed rule questions and the actual button pairs; this association is not a mismatch of shuffled option IDs. The full list below retains all nine errors.

This is a candidate explanation to test, not proof that an internal self/other boundary disappeared. All goal-to-rule mappings were public in the system prompt; a partner-matching rule choice alone does not establish transmission of the partner's private assignment. The partner's current assignment, answer salience and ordinary interference remain alternatives. Also, the linked readout continues to receive the held partner window, so current data do not localize the error to the continuing work state versus the measurement branch. Some first-round errors occur before action histories diverge, but the full multi-round totals cannot be treated as same-state causal effects.

| Case | Condition | Round | Side | Own goal | Partner goal | Selected Dim/Bright pair | Required own pair |
|---|---|---:|---|---|---|---|---|
| 1 | LIVE | 2 | A | G1 | G3 | Down / Up | Up / Down |
| 1 | LIVE | 3 | A | G1 | G3 | Down / Up | Up / Down |
| 1 | LIVE_SELF_REPORT | 1 | A | G1 | G0 | Right / Left | Up / Down |
| 1 | LIVE_SELF_REPORT | 2 | A | G1 | G3 | Down / Up | Up / Down |
| 1 | LIVE_SELF_REPORT | 3 | A | G1 | G3 | Down / Up | Up / Down |
| 2 | LIVE_SELF_REPORT | 1 | B | G0 | G2 | Left / Down | Up / Right |
| 2 | LIVE_SELF_REPORT | 2 | A | G1 | G0 | Up / Right | Right / Up |
| 2 | LIVE | 1 | A | G2 | G0 | Up / Right | Left / Down |
| 2 | LIVE | 2 | A | G1 | G0 | Up / Right | Right / Up |

**Self-state reporting did not repair the central problem.** LIVE_SELF_REPORT actions were 2/6 in both cases and explicit partner reports remained 0/6. Rule errors were 3/6 and 2/6. The instruction could produce correct statements of own identity/goal followed by the partner-matching rule: case 1, round 1, A said its assignment was G1 but described Right/Left, the G0 rule belonging to B. In rounds 2 and 3 it explicitly named G3 while retaining the introductory G1 assignment. These are observable generated-text inconsistencies, not a privileged account of internal reasoning. The fixed 64-token notes can end mid-sentence; no note was removed or reformatted because of that.

**Unknown does not measure all observable behavior, but forcing a choice did not establish dependable access.** LIVE explicit partner reports were Unknown in 6/6 and 5/6 cases. The forced beacon pair had the correct partner bit in only 1/6 for each case. LIVE_SELF_REPORT case 2 had four correct partner bits despite five Unknown responses, but OFF_SELF_REPORT also had three correct partner bits with six Unknown responses. Worlds differ, and chance, own-beacon mirroring and response format remain explanations. Across linked arms there were seven correct partner bits paired with explicit Unknown, including all six correct linked actions; this does not certify reliable hidden knowledge. TEXT_FACTS case 1 also misreported the own bit twice while correctly reporting the supplied partner bit and taking the correct action. Thus pair-question correctness and action competence are distinct.

**Other visible failures are retained.** Several OFF notes invented a partner beacon by copying their own beacon or carrying a previous assumption. Linked notes sometimes repeated a shared answer number or check marks; other notes mixed a correct heading with an incorrect rule. A correct goal label therefore does not by itself establish successful rule application, and an incorrect explicit fact report does not by itself establish absence of any influence.

## Relation to the earlier interaction pilot and next proposed test

The previous two-case pilot still contains one feedback-sensitive correct forward switch but failed correct return chains, plus a second unsuccessful case. This diagnostic does not repeat its cuts or matched replay and cannot strengthen its causal estimate. It instead localizes two possible obstacles: current partner-fact use is unreliable in these continuing linked histories, and own-rule readouts can change while goal labels remain intact. Neither observation warrants abandoning the real-time reciprocal question or claiming it has been demonstrated.

The next useful small comparison, if separately authorized, would keep the same pre-answer world and own assignment while changing only the partner assignment; ask whether the selected wrong rule follows that change. Separate connection during work from connection during the discarded readout, and include disconnected and matched recorded-partner controls. An explicit-fact control with own and partner facts varied separately would check role binding and the remaining correct-note/wrong-action failure. Fix a finite exploratory scope before those outputs and retain negative cases. This proposal is not a new execution authorization; no samples, settings or formal protocol were changed here.

## Operational closure

At the independent state check, the provider was actually running, the GPU had no compute process, both exact diagnostic processes had exited and the original local/remote hold guardians were healthy. The job-completion heartbeat was paused. The allocation remains held as the PI requested; the original USD8/four-hour origin, 2GiB egress cap, 18:32:18 Chicago stop-request time and 18:37:18 lifecycle limit are unchanged. No routine stop, restart, further job or budget reset occurred. This is completion of the diagnostic, not confirmation that the future fixed stop has already happened.

Offline validation: 1260 passed, 10 skipped and one GPU test deselected (44.16 seconds). Original scientific files, old failures and unadmitted optimized numerical paths remain unchanged.

Evidence: SD directory `v6/replacement-clarity-20261019-channel-diagnostic1/`; private closure receipts and scripts under the same execution root's `channel-diagnostic-1/`, including `sealed_inventory_receipt.json`, `backup_verified.json`, `analysis.json`, `displayed_rule_crosscheck.json` and `actual_state.json`. No access credentials or connection/instance identifiers belong in this report.

## Every round and side

Beacons are A/B; D=Dim, B=Bright. A reported pair includes both sides even when only one component is correct. Each row preserves the committed action and all diagnostic answers; detailed rule-error choices are above.

### Case 1, LIVE

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | B/D | G1 / G0 | Down / Up | True | True | Unknown | B/B |
| 1/B | B/D | G0 / G1 | Down / Left | True | True | Unknown | D/D |
| 2/A | D/B | G1 / G3 | Down / Down | True | False | Unknown | D/B |
| 2/B | D/B | G3 / G1 | Up / Down | True | True | Unknown | B/B |
| 3/A | B/D | G1 / G3 | Down / Up | True | False | Unknown | B/B |
| 3/B | B/D | G3 / G1 | Down / Up | True | True | Unknown | D/B |

### Case 1, OFF

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | B/D | G1 / G0 | Down / Up | True | True | Unknown | B/B |
| 1/B | B/D | G0 / G1 | Right / Left | True | True | Dim | D/D |
| 2/A | D/D | G1 / G3 | Down / Up | True | True | Bright | D/B |
| 2/B | D/D | G3 / G1 | Down / Down | True | True | Dim | D/D |
| 3/A | B/B | G1 / G3 | Down / Down | True | True | Unknown | B/B |
| 3/B | B/B | G3 / G1 | Up / Up | True | True | Unknown | D/B |

### Case 1, LIVE_SELF_REPORT

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | B/D | G1 / G0 | Left / Up | True | False | Unknown | B/B |
| 1/B | B/D | G0 / G1 | Left / Left | True | True | Unknown | D/D |
| 2/A | D/B | G1 / G3 | Left / Down | True | False | Unknown | D/B |
| 2/B | D/B | G3 / G1 | Up / Down | True | True | Unknown | B/D |
| 3/A | B/D | G1 / G3 | Left / Up | True | False | Unknown | B/B |
| 3/B | B/D | G3 / G1 | Up / Up | True | True | Unknown | D/D |

### Case 1, OFF_SELF_REPORT

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | B/D | G1 / G0 | Down / Up | True | True | Unknown | B/B |
| 1/B | B/D | G0 / G1 | Right / Left | True | True | Dim | D/D |
| 2/A | D/D | G1 / G3 | Up / Up | True | True | Unknown | D/B |
| 2/B | D/D | G3 / G1 | Down / Down | True | True | Unknown | D/D |
| 3/A | D/B | G1 / G3 | Up / Down | True | True | Unknown | D/B |
| 3/B | D/B | G3 / G1 | Up / Down | True | True | Unknown | B/B |

### Case 1, TEXT_FACTS

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | B/D | G1 / G0 | Up / Up | True | True | Dim | B/D |
| 1/B | B/D | G0 / G1 | Left / Left | True | True | Bright | B/B |
| 2/A | B/B | G1 / G3 | Down / Down | True | True | Bright | B/B |
| 2/B | B/B | G3 / G1 | Up / Up | True | True | Bright | B/B |
| 3/A | B/D | G1 / G3 | Up / Up | True | True | Dim | B/D |
| 3/B | B/D | G3 / G1 | Up / Up | True | True | Bright | B/B |

### Case 2, LIVE

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | D/B | G2 / G0 | Right / Down | True | False | Unknown | D/D |
| 1/B | D/B | G0 / G2 | Right / Up | True | True | Unknown | B/B |
| 2/A | D/B | G1 / G0 | Right / Up | True | False | Unknown | D/D |
| 2/B | D/B | G0 / G1 | Right / Up | True | True | Bright | B/B |
| 3/A | D/D | G1 / G0 | Right / Right | True | True | Unknown | D/D |
| 3/B | D/D | G0 / G1 | Right / Up | True | True | Unknown | B/D |

### Case 2, OFF

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | D/B | G2 / G0 | Left / Down | True | True | Unknown | D/D |
| 1/B | D/B | G0 / G2 | Right / Up | True | True | Bright | B/B |
| 2/A | B/B | G1 / G0 | Right / Up | True | True | Dim | B/D |
| 2/B | B/B | G0 / G1 | Right / Right | True | True | Bright | B/B |
| 3/A | D/D | G1 / G0 | Up / Right | True | True | Unknown | D/B |
| 3/B | D/D | G0 / G1 | Right / Up | True | True | Bright | B/D |

### Case 2, LIVE_SELF_REPORT

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | D/B | G2 / G0 | Left / Down | True | True | Unknown | D/D |
| 1/B | D/B | G0 / G2 | Left / Up | True | False | Bright | B/B |
| 2/A | B/D | G1 / G0 | Up / Right | True | False | Unknown | B/D |
| 2/B | B/D | G0 / G1 | Up / Right | True | True | Unknown | B/D |
| 3/A | B/B | G1 / G0 | Up / Up | True | True | Unknown | B/B |
| 3/B | B/B | G0 / G1 | Right / Right | True | True | Unknown | B/B |

### Case 2, OFF_SELF_REPORT

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | D/B | G2 / G0 | Left / Down | True | True | Unknown | D/D |
| 1/B | D/B | G0 / G2 | Right / Up | True | True | Unknown | B/B |
| 2/A | B/B | G1 / G0 | Up / Up | True | True | Unknown | B/B |
| 2/B | B/B | G0 / G1 | Right / Right | True | True | Unknown | B/B |
| 3/A | B/D | G1 / G0 | Up / Right | True | True | Unknown | B/B |
| 3/B | B/D | G0 / G1 | Up / Right | True | True | Unknown | B/D |

### Case 2, TEXT_FACTS

| Round/side | Actual A/B beacons | Own/partner goals | Action / required | Goal correct | Rule correct | Partner report | Reported A/B pair |
|---|---|---|---|---|---|---|---|
| 1/A | D/B | G2 / G0 | Left / Down | True | True | Bright | D/B |
| 1/B | D/B | G0 / G2 | Up / Up | True | True | Dim | D/B |
| 2/A | B/D | G1 / G0 | Right / Right | True | True | Dim | B/D |
| 2/B | B/D | G0 / G1 | Right / Right | True | True | Bright | B/D |
| 3/A | D/D | G1 / G0 | Right / Right | True | True | Dim | D/D |
| 3/B | D/D | G0 / G1 | Up / Up | True | True | Dim | D/D |

