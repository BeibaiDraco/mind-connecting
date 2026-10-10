# V5 STATIC terminal audit — 2026-10-10

## Decision

Do not launch the conditional Llama STATIC N600 comparison. Independent validation meets the frozen mean access-match bound, but both the ordinary KV condition and content-counterfactual KV condition exceed the unchanged five-percentage-point capability-drop limit. No runner-up, fresh validation sample or threshold relaxation is permitted by the approved branch.

This is separate from an engineering failure: the original frozen postprocessor stopped with an incorrect CF metadata expectation before its usual backup. The full collected data were recovered, independently validated against the exact frozen producer, and the unchanged statistical gate was recomputed twice with identical results. No original record or scientific source was changed, and no ownership effect or significance was inspected to decide continuation.

## Collection and recovery

- Calibration: `20261010-154140_calibrate_v5_static_cal`, 60 episodes and three layer blobs, already backed up.
- Coarse search: `20261010-154353_v5_llama_static_match_v5_static_match`, all 5,440 records, selected layer16/raw/gain0.5; no refinement was needed. Its 681-file backup was verified.
- Independent validity: `20261010-164716_v5_llama_static_validity_v5_static_validity`, all80 episodes and2,560 records completed at17:27:59UTC. The model child exited1 during postprocessing immediately afterward. The actual instance was stopped when checked at17:43UTC; formal intent and freeze did not exist.

A reviewed evidence-only recovery restored the same instance under the original USD60 anchor/deadline, a fresh remote guard and an unacknowledged600-second local stop guard. It verified no model/GPU task, archived the old controls, and copied the exact existing validity run via the reviewed inventory-and-ACK mechanism. No model was rerun. All294 files /4,739,318 bytes were rehashed against the inventory; the recovery then explicitly stopped the instance and verified actual stopped state. The idle backup observer and terminal local guards were retired by exact process identity. The heartbeat was paused.

Evidence digests:

| Evidence | SHA256 |
|---|---|
| Validity run identity | `212c99f65139e73155b7b392f605eaa1369015737f6f4b397cbbfd0e60a81234` |
| Recovered validity inventory | `a426c6aee4afcf93c0e9fab155be665585fe67b6c507a66431ff2fddf3ed956a` |
| Original controls archive | `66c397c9a2343726be4a153f510f2528c0c9a71e26dc87768ce5f320a7783ed7` |
| Independent producer-aware audit | `b59773d7b098cfdb2992fbf0b7d8a29b499c2cd6f71fbd5a3122271bab7afba2` |

Independent technical review verified17 stage-frozen files,56 algorithm-frozen files,16 prerequisite pins, the selected calibration blob, all four arm hashes, and the complete reconstructed runtime identity. All2,560 expected records are unique and finite:80 complete episodes,640 records per arm, no missing/unexpected/duplicate/failed records or truncated tails.

## Original checker defect

The frozen producer in `src/mb/run.py` intentionally builds A's readout label meanings from the connected donor view. `tasks.make_donor_variant(..., "CF")` swaps the donor's assigned and spare values while keeping A's physical prompt, question text and options fixed. The frozen `v5_static._checked_records` instead constructed its expected `label_meaning` from the original episode for every arm.

The mismatch is exactly320 CF access records:80 episodes x2 rotations x2 access questions. All640 CF records, including capability questions, match the actual frozen producer. All other compared metadata, physical CF candidates, question hashes/options, native source pins and non-CF records also match. The original exception and absence of its gate output are retained; the independent producer-aware audit is a separate artifact, not an overwritten or fabricated successful original pipeline output.

The downstream `v5_static.validity()` calculation was used unchanged, including its sample unit, metrics, bootstraps and thresholds. The two independent recomputations match exactly across88 leaf fields, including61 numeric fields. The numerical gate below is therefore distinct from both the original checker failure and any proposed future code repair. Before future use, repair the validator in an explicitly reviewed version with a regression test using real CF donor-view metadata; do not overwrite the frozen algorithm manifest or silently reinterpret old execution as successful.

## Frozen validity result

| Condition | CAP accuracy | Drop from baseline | Five-point limit |
|---|---:|---:|---|
| C0 |94.6875%|0|Pass|
| KV-P w1 |88.4375%|6.25 points|Fail|
| Content-counterfactual KV-P w1 |88.75%|5.9375 points|Fail|
| STATIC layer16 g0.5 |92.8125%|1.875 points|Pass|

Baseline and label-format checks pass. The KV rule-access gain is2.040513885 nats; STATIC gain is1.562524045 nats. The absolute gap is0.477989841 nats, or23.425% of the positive KV gain, within the frozen25% bound. Required KV access and counterfactual content-transfer gates pass, including both rule and word content diagnostics. Nevertheless the independent capability failures make the overall gate **fail**.

This mean matching result is not an equivalence test. The paired95% interval for STATIC gain minus0.75x KV gain is[-0.371043028,0.435554783], so uncertainty extends outside the tolerance region. No formal matched-route attribution comparison was collected, and no such conclusion is licensed by this validation result.

## Overall v5 disposition

Qwen provenance: formal N600 complete and backed up; retain the prespecified WORD access limitation. Llama provenance: unavailable after its independent5.625-point CAP failure. Llama STATIC: independently matched at the validation point estimate, but formal comparison unavailable after the6.25/5.9375-point CAP failures. Preserve all failed-stage evidence and frozen multiplicity families. No approved GPU work remains; any new research plan requires a separate PI decision.

Recovery controls passed13 private regression tests and independent review. Offline repository suite:361 passed,5 skipped. No scientific code was edited during this recovery.
