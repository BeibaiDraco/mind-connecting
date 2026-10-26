# Additional deciding-source checks by the coordinator

October 26, 2026. Primary-source reading, no model reproduction. These notes are supplementary for screening; the fixed questioner packet remains unchanged.

## Dense Latent Communication, v2

[Chen et al., See What I See, Know What I Think](https://arxiv.org/html/2606.13594), v2 October5, read §§1–4 and the three-agent setup description. The abstract's mind-reading language is implemented as context-aware, context-unaware and partial-aware task transfer. The same-model Qwen3-4B retention analysis encodes the source input without autoregressive generation; selected KV-group retention has different effects depending on whether the recipient already sees that input. Main heterogeneous results use trained cache-reconstruction and generation objectives and learned per-group transformations. In the three-agent task, two senders encode private supporting documents **before the question arrives**; the receiver later sees the question plus distractors. PhaseII trains that two-memory interface using task-specific supervision.

This directly precedes generic unknown-future-query memory use and combining distributed private documents. It does not establish belief-perspective separation or confidence-conditioned receiver action. A proposed native frozen experiment needs a consequential comparison beyond removing the learned adapter or reducing the number of agents. Do not use its mind-reading title as evidence that it tested false-belief prediction, but do not claim late recipient questions as novel.

## Confidence Laundering, v1

[Shi et al.](https://arxiv.org/html/2606.20662v1), independently opened AppendixA.8–A.12 after the field author and reviewer. A.8 trains logistic/MLP probes; A.9 explicitly names the downstream uncertainty predictor; A.11 uses AUROC and thresholded binary accuracy and calls these recoverability. This corroborates the reviewed boundary, not a distinct novel finding. The source's conceptual proposal already includes useful downstream verification/retry, so a new contribution cannot be the proposal alone; it must empirically or theoretically settle an important unresolved property of actual native use.
