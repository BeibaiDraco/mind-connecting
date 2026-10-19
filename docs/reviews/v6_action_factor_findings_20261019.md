# Action decomposition and numerical discrepancy findings

Date: 2026-10-19. Codex root source review and separate raw-data reconstruction; no independent-agent review is claimed.

## First finite diagnostic

All572 scheduled readouts completed. The589-file archive was copied to the SD card and independently rehashed; all572 full-vocabulary arrays were checked for shape, finiteness and native argmax. Question/material/scoring identities were regenerated separately. Raw evidence is in the private execution root's `action-diagnostic-1` and the corresponding `replacement-clarity-20261019-action-diagnostic1` SD directory. These are exposed debugging cases, not independent confirmation or scientific admission.

| Reference task intervention | Correct /64 | Invalid |
|---|---:|---:|
| Original P2 joint decision |29|0|
| Retrieve assigned Dim/Bright rule pair |59|0|
| Apply an explicitly supplied correct pair in the full scenario |49|0|
| Map an explicitly supplied correct button to its option ID |63|0|
| Joint decision with the device-transition/working-note context removed |33|0|

Of the35 failed joint decisions,33 have a correct rule-pair response in the separate branch;34 have correct supplied-button mapping;23 become correct when supplied the pair. These are diagnostic interventions on separate branches, not proof that the failed joint computation internally retrieved the correct rule. The results locate substantial difficulty in combining rules and current facts in context. They do not support describing every failure as missing information, illegal output, or inability to map a button to an option. Removing context alone improved only4 aggregate responses; it is not a demonstrated adequate repair.

## The four numerical differences

The four original disagreements and eight fixed agreement controls were tested under five paths. All24 reference/packed replays matched their saved complete native-logit arrays bitwise, with identical input tokens. Reference repeats were also bitwise identical. This reproduces the failure rather than explaining it away as different prompts or one accidental draw.

For each of the four discrepancies, changing only the native question-ingestion grouping to16-token chunks already changes the first layer's Q projection while its preceding normalization is unchanged. This is a forward-shape-dependent arithmetic effect before attention; it changes the final answer in two of the four cases. Within the packed layout, substituting SDPA for flex leaves that Q projection unchanged but changes the first attention output; it changes the final answer in one of the four cases. Native-chunked versus packed-SDPA additionally differs in packing/padding and related execution shape, so that contrast does not isolate one unique operation. All differences propagate through decoder outputs from layer0. Recomputing the output head on the same final hidden row is bitwise identical in all60 observed readouts, excluding this particular output-head-shape hypothesis for the observed examples.

The data support multiple execution-shape/kernel numerical contributions, not a single universal diagnosis for all model families or linked inference. The original numerical failure remains failed. No tolerance was relaxed and no tie was excused.

## Bounded candidate repair

When a single-history consumption has no effective incoming state, the private candidate delegates to the original native implementation rather than unnecessarily using packed/chunked computation. All192 old variant/case inputs reproduce the saved reference's complete vocabulary arrays bitwise. This resolves those observed single-history empty-window discrepancies without changing scientific content, argmax or native precision.

`src/mb/v6_empty_path_native.py` isolates the same delegation in an explicitly unadmitted class with a distinct model identity. The original75 frozen source pins and original native/packed implementations remain unchanged. This class does not certify `consume_many`, `step_many` or real incoming-window execution. It is not wired into a formal runner. Four hardware integration checks of the class are assigned to the bounded work follow-up.

## Generated-work follow-up

The manually specified follow-up compares a minimal rule-only oracle and identical facts-first prompts with zero versus64 generated work tokens. The first attempt preserved128 completed records before a text-recording interface error. All146 files were backed up and rehashed. A separately bound recording-only repair collects the remaining64 work cases and four class integrations, retaining the old worker deadline and allocation limits. The original failure and its one computed-but-unpersisted work readout remain explicit; no result is imputed and no completed row is rerun. See the dedicated follow-up plan. Final results are recorded in a separate closure review after raw verification.
