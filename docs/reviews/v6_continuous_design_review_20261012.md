# Review of the sustained-interaction proposal

Date: 2026-10-12. Status: revised local proposal; no scientific freeze, native implementation or GPU execution.

Reviewed artifact: `docs/protocol/PROTOCOL_V6_CONTINUOUS_DRAFT.md`. The prior `PROTOCOL_V6_RECIPROCAL_DRAFT.md` and its review remain intact. This record consolidates independent read-only construct, causal/statistical and engineering reviews; the author applied the revisions.

## Main findings and resolutions

| Finding | Resolution in the revised proposal | Remaining boundary |
|---|---|---|
| A single request and reply do not test continuing interaction. | Six actual decision rounds retain both native histories. Each actual action changes only its owner's next private device state. Early and late perturbations reverse physical roles. | Evidence at two planned sites does not establish response at every possible time or necessity of a long history. |
| A controller could accidentally transmit the other side's answer or reward. | Local updates contain only one's own device state and authorized event; no partner action, joint score or corrective answer is returned. | Native isolation still requires implementation and hardware tests. |
| Old replay can lose current task information. | Add FRESH, two current-round shadow tapes exchanged once. Explicitly recognize its cross-round feedback and oracle-perfect solvability. Label second-round old replay as a total frozen-return intervention. | LIVE-FRESH is not an equal-information or equal-compute comparison. |
| Any changed answer can look responsive. | Require separate path contrasts and a specific-response chain-quality score Q_chain at both early and late sites. | Q_chain is conservative; failure does not imply feedback is absent. |
| A model might react directly to its own event without needing a returning signal. | Cut each path and score a synthetic directly pulse-aware policy, whose return contrast is zero despite perfect raw sensitivity. | A positive response without the required cut contrast is insufficient. |
| Actual worlds diverge after different actions. | Use fixed pre-branch oracle candidates for causal chain fidelity and separately report actual-world task accuracy. | These answer different questions and must not be substituted for one another. |
| Adaptation to a changed partner state could be miscalled goal takeover. | Separate natural task adaptation from fixed-world, fact-complete goal probes, alongside original/latest assignment reports. | Reports and actions are separate counterfactual measurements, not proof of causal unawareness. |
| Ordinary action codes collide across different beacon rows. | Use the same fresh goal-to-action row for both recipients in the fact-complete probes, explicitly overriding the normal table for that query. | Ordinary actions use recipient-specific task rows. |
| Repeated sides, rounds and branches could inflate N. | Cluster by the base episode. Proposed N240 per model; 22 primary tests across both checkpoints in one Holm family. | Planning precision is assumed, not measured; exact analysis simulations remain pending. |
| A branch-continuation sentence excluded the second pulse round. | Both natural and two-round pulse trajectories consume their actual actions; only diagnostic/shadow branches are discarded. | Native cache continuation is not yet implemented. |
| Full-vocabulary invalid actions can be native control tokens. | Specify a predeclared token-category recovery table, preserve the actual output, prevent double closure, and exclude recovery tokens from exports. Replay retains donor positions and aligns by round/work tick. | Both tokenizer/native contracts must pass acceptance before collection. |

## Offline evidence and its limits

The standard-library checker and saved JSON are in `docs/protocol/v6_continuous_checks/`. The engineering reviewer independently reproduced the initial JSON byte-for-byte and identified a vacuous direct-response assertion. It was replaced with 12 explicit synthetic policies evaluated by the same signed/Delta calculation; saved output was regenerated and independently reproduced byte-for-byte again, with no remaining issue in that narrow check. The checker covers 48 pulse worlds, 384 six-round schedules, 64 controller-input privacy cases, random-switch/goal-blind rivals, 576 common-row mappings and workload arithmetic.

FRESH and LIVE deliberately use the same ideal information in the reference kernel: their equality demonstrates task information sufficiency, not a native implementation test. Neither this checker nor the existing regression suite establishes that Qwen or Llama can perform the task. Full materials, exact native prompts, statistical-code simulations, a separate reviewed runner and later hardware acceptance remain necessary.

Final local verification: saved checker output reproduced exactly, relative document links resolved, and the existing offline regression suite passed with 428 passed and five skipped. No v6 native model tests exist yet.

The design can identify sustained reciprocal action-state control and test whether assigned goals remain behaviorally separate. It cannot by itself establish autonomous joint planning, an irreducible shared subject, a consciousness claim, or superiority to all steering/memory systems. Adaptive steering is compatible with reciprocity; the scientifically useful contrast is whether specific responsive causal paths matter and what happens to each participant's authorized goal.

## Authorization and handoff

The PI requested a better design and explicitly prohibited GPU startup. Proposed N240, events, timings, gains, thresholds and the multiplicity family are recommendations, not ratified settings. No model weights, frozen protocol, old result, failure, manuscript, instance, budget or automation was changed. The next work is scientific review followed by local implementation; any paid hardware phase needs its own authorization after preparation.
