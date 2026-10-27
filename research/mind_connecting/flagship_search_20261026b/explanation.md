# Explaining the alternatives question and its contribution threshold

October 26, 2026. This note explains the already reviewed proposal in response to the PI's request for its value, cleverness, existing evidence and experimental justification. It does not revise the plan, adopt an experiment or claim an observed effect. No new research decision, model run, scientific code, threshold or formal sample size is introduced.

## The question and the meaning of “unchosen”

Can a receiving LLM use a sender-supported alternative under private new evidence that the sender never saw, by importing the sender's native internal state? “Unchosen” means different from the actual choice committed on the exported trajectory. It does not mean unspoken, unconscious, inaccessible to the sender or already computed as an explicit hypothesis. Those stronger interpretations require separate evidence. The operational object is conditional decision competence supported by the transferred state.

The connection to the original vision is computational continuity: a past calculation by one instance may support a different future continuation by another. The recipient's later private evidence determines which continuation is appropriate. This measures a limited form of independent use of shared content. It does not measure identity fusion, consciousness, preservation of personal goals or necessity of reciprocal interaction. The initial one-way captured-state design prevents the late cue from reaching the sender; roles are counterbalanced across episodes.

## Why the comparison is informative

The reviewed six-cell illustration has donor counts (8,4,2,1) and (8,2,4,1) for four hypotheses A/B/C/D. Both task distributions favor A with probability 8/15 and have identical entropy. These are oracle task quantities, not measured beliefs of the LLM. The real materials must require combining private premises under public rules; the posterior table is not given as the scientific input.

| Receiver's later evidence | First donor evidence | Second donor evidence |
|---|---|---|
| All four classes remain possible | A | A |
| Only B/C remain possible | B | C |
| Only C/D remain possible | C | C |

The last row requires using the initially third-ranked option in the first world. The central row cannot be solved perfectly from a common winner/scalar message or the late cue alone. These predictions are stipulated correct actions, not model results. A fixed donor state is reused across recipient cues. Replace it with its paired counterfactual state to ask whether the recipient's actions track the altered residual support. The manipulation changes the evidence-induced state as a bundle; it is not a selective intervention on an identified hypothesis representation.

Record every actual donor commitment before export and retain all prospective families. Same task-optimal answer does not guarantee same actual donor answer or confidence. Report observed agreement, failures and actual donor-versus-recipient choices; no primary filtering on convenient donor agreement. All restored branches and counterfactual versions belong to one independent episode/layout.

## What the previous evidence actually supports

The following old findings were checked against [V3](../../../docs/results/v3/confirmatory_v3.md), [choice summaries](../../../docs/results/story_checks.md) and [V5](../../../docs/results/v5/provenance_post_collection_20261012.md), without reanalyzing raw data.

- In the Qwen matched setting, mean rule-access gains are 4.081 nats for KV w1 and 4.179 for STATIC g0.1. Donor-rule selections on the initial-own-assignment question are 52.3% and 0% respectively. This means the scalar access metric does not explain the attribution contrast. It does not establish full information matching or universal absence of STATIC effects; another STATIC setting has nonzero attribution errors.
- Removing the connection at readout after the same connected work history lowers donor selections on the historical question from 97.1% to 1.3%, and on the current-rule question from 94.9% to 17.5%. This shows dependence on ongoing access with readout-specific recovery, not proven erasure/restoration or changed identity.
- Conflicting donor records about the explicitly named third party Robin cause 49.92% rule errors in Qwen and 48.50% in Llama, from 0% in the aligned record condition. This limits a self-exclusive interpretation and motivates careful content-binding explanations.

The old findings justify measuring useful committed decisions and keeping source reports separate. They do not establish transferable alternatives, beneficial reasoning-state reuse or reliable native reciprocity. Their specific numbers are historical results, not feasibility rates for the new task.

## Closest papers: question, method, evidence boundary

[Interlat v5](https://arxiv.org/html/2511.09149v5), section 5.2 and Appendix F, explicitly advances parallel hypotheses and examines top-k token-probability mass and task trajectories, including 32 latent steps. This is meaningful evidence for its interpretation. It does not identify which semantic residual alternative a native recipient correctly uses under the proposed donor-counterfactual/private-cue comparison. Trained actors/interfaces differ from our frozen setting, but that difference alone is not novelty.

[Confidence Laundering](https://arxiv.org/html/2606.20662v1), Appendices A.8–A.11 and B, explicitly models distributions over alternative commitments. Its inspected handoff experiment uses logistic/MLP uncertainty prediction with AUROC/binary classification. That establishes recoverability of uncertainty-related information under its protocol, rather than the proposed actual receiver choice between specific alternatives.

[Beyond Final Accuracy / ICR](https://arxiv.org/html/2610.01042), sections 3 and 4.2, already fixes initial trajectories and tests actual textual/native revision, including both-incorrect recovery and no-message extra reasoning. In its retained Qwen3-4B population, both-incorrect recovery for communication conditions is 0.30–2.55%, numerically below no-message except one StateBridge/GPQA-D comparison (11 versus 10 cases). This is a scoped result, not a general impossibility. It reinforces that richer influence or a few successful revisions need not establish useful access to residual possibilities.

[Dense Latent Communication](https://arxiv.org/html/2606.13594v2) and [LatComm](https://arxiv.org/html/2610.26840) already encode private context for later questions. Consequently neither delayed evidence nor query-independent internal memory is our novelty. The proposed contribution is a direct functional test of a substantive existing hypothesis, with semantic alternative identity and later evidence separately manipulated. No exhaustive absence claim or claim to originate parallel hypotheses is justified.

## Proposed experimental logic

The complete [reviewed plan](questions/alternatives/plan.md) is authoritative for the proposal. Two pinned frozen Qwen instances retain separate contexts. Archive a designated real native KV window after the sender's actual commitment, then expose only the recipient to the later cue. The proposed 16-position all-layer window and 64-token work periods are engineering choices awaiting task/runner admission, not validated settings.

Three linked questions organize the existing comparisons:

1. Does a native recipient correctly use residual content? Compare true, alternative-swapped and irrelevant native state, no message, actual answer/confidence, and the guaranteed identical oracle winner/scalar summary. Require donor-contingent B/C reversal together with A retention and third-rank C use; a pooled average can conceal failure.
2. What information and resources suffice? Include actual full alternatives reports, oracle full distributions and raw full evidence. Account separately for sender/receiver computation and tensor bytes. A native win over one answer token alone is weak evidence for a substantial paper. A full textual alternatives report working equally well is consistent with native functional preservation, and rules out native exclusivity.
3. Does sender processing help? Compare early evidence-stage state, inference-stage state and equal-length premise rehearsal. All three make a real choice before a common seal; the early branch therefore includes minimal decision computation. A positive inference-versus-rehearsal difference supports useful donor processing under this contract. It still bundles inference, retrieval, compression and binding, and does not identify a transferred hypothesis-space representation.

The most important alternative explanation is raw evidence transfer followed by receiver recomputation. It reproduces the ideal behavioral pattern exactly. The first conclusion must allow it. A stronger paper should explain the donor-processing contribution, survive resource/evidence controls and reproduce the functional comparison on a second independently specified reasoning structure. Optional actual-window substitutions can localize causal payload dependence without requiring a neural circuit claim.

The plan's proposed investment sequence remains task/runner audit, 12 fresh competence families, then 24 fresh development families. The latter entails 1,872 receiver commitments, 144 actual donor commitments and up to 192 supplemental readouts; these are workloads, not independent sample counts or a formal power calculation. A later confirmatory study requires a new approved frozen protocol and separate material. Native fact-transfer failure makes the main question untested. Working native facts plus working full-evidence decisions but failed conditional alternative use yields a bounded negative result for this carrier/task.

## How much of a paper each outcome warrants

A win over answer-only establishes an expected informational advantage and is insufficient for the proposed flagship story. Donor-specific, cue-appropriate reversals that survive the stronger controls establish functional access to revisable content beyond winner/scalar summaries. Adding a well-controlled donor-processing contribution and replication across a different reasoning structure would support a more consequential account of computation reuse across models. Claims about a unique hypothesis code, human selves, universal latent superiority or major-conference acceptance would still exceed that evidence.

The prospective field value is an explanatory evaluation of what a communication state lets another model do when circumstances change, and whether prior computation helps preserve that flexibility. If the observed benefit reduces to ordinary evidence transport or resource allocation, the claim should contract accordingly. The question remains worth testing because these explanations make different predictions under the planned comparisons; its importance is conditional on resolving them, not on the metaphor alone.
