# Development: can a partner use alternatives your answer discarded?

October 26, 2026. Primary planner. This directory contains a completed synthetic deciding check and a proposed native behavioral study, awaiting independent plan review. Root owns shared governance, tests and git. No model execution, raw target-outcome analysis, training, protocol amendment or experiment adoption occurred.

## The first investment decision

The important uncertainty is whether the proposed task actually requires residual alternatives, rather than only an answer, confidence or a reflex to reject the winner. Before designing an estimator, I enumerated a finite family. Reproduce with:

```bash
.venv/bin/python research/mind_connecting/flagship_search_20261026b/questions/alternatives/finite_world_check.py
```

[Script](finite_world_check.py); [actual output](finite_world_output.json). The construction has four hypothesis classes with surviving micro-world counts 8, 4, 2, 1. All 24 assignments of these counts to labels are crossed with all 11 late cues retaining two, three or four classes. The 264 cells have the same maximum task probability, 8/15, and entropy, approximately 1.64022 bits. Comparisons fixing the leader also fix its identity. The sender never knows the late cue.

The task-optimal choice retains the initial leader in 168 cells, uses the prior runner-up in 72, and uses the prior third alternative in 24. Thus neither “always keep the answer” nor “always use the runner-up” solves the family. The best possible policy seeing only the leader, maximum probability, entropy and late cue achieves 212/264 = 53/66 overall and 44/96 = 11/24 on leader-excluded cells. Full distribution or full raw evidence permits 264/264. These are exact finite decision bounds under equal cell weights, not model-performance estimates.

A concrete counterexample fixes leader A and cue “B or C”: counts (8,4,2,1) require B, whereas (8,2,4,1) require C. Identical winner and scalar summaries cannot encode the difference. Cues retaining A and cues excluding the prior top two prevent a universal runner-up response. The generator specifies choices maximizing expected utility; “correct” here means the unique Bayes-optimal action, not certain identification of one sampled hidden truth. Equal cue weights define an intervention population rather than the natural frequency of observations.

**Decision:** proceed with bounded native planning. This establishes a nontrivial information requirement. It does not establish that Qwen computes these probabilities, naturally gives the same answer/confidence, preserves alternative representations, or can read its partner's native window.

## The stronger claim does not follow from this check

A recipient that retrieves every donor premise and recomputes the distribution passes every synthetic cell. Therefore raw-evidence recomputation **exactly reproduces the primary behavioral signature**. The primary claim must be functional access to residual alternatives **or their supporting evidence**, beyond a winner and scalar summaries. A simple private-fact relay alone is not the envisioned flagship result.

The plan adds a prospective comparison between evidence-stage and inference-stage exports with a matched rehearsal condition. It tests whether donor processing makes information more useful under a specified receiver budget. It does not, even if positive, uniquely identify an already-computed hypothesis distribution: processing can improve compression, binding or accessibility of raw premises. The strongest “continuing another's unfinished inference” interpretation remains conditional on further explanatory evidence and is not the primary claim.

## What changes understanding

The question tests a substantive implication of an existing idea: latent communication may retain parallel alternatives. A direct, action-level demonstration requires the recipient to preserve a winner when appropriate, abandon it when appropriate, and choose different residual alternatives according to both the donor's private evidence and its own unseen late cue. The important positive is reusable, counterfactually appropriate access; the informative negative is failure of that capability despite working native fact access and explicit task competence. An uninformative channel failure does not reject the idea.

Sources and the native runtime motivate the comparison; [plan.md](plan.md) specifies the measurement, comparators, resource accounting, finite gates and interpretation. A model pilot and task/runner implementation remain unperformed. Independent review must assess whether the conditional contribution warrants further investment; this document does not certify its own adequacy or publication priority.

## Bounded repair 1 after independent review

The independent [review](review.md) found two consequential issues. R1: the original continuation gate could pass a policy that solves both donor-dependent B/C cases but fails both C/D cases, despite performing worse than a summary control. R2: the original export trajectory had no actual donor choice; a sibling answer could not establish what that donor left unchosen. The plan now requires the measured summary contrast, explicit third-rank success, paired B/C reversal and leader retention, and commits an observed donor choice before each export seal. All families remain included; oracle leader, actual choice and observed agreement are separately reported. An extra 144 donor choices are included in the proposed Stage 2 ledger.

The review's 7/8 summary-policy bound concerns the stipulated six-cell abstract support, not observed Qwen performance. The repair therefore does not impose a universal .10 summary-arm margin. These corrections use exact logic, not model outcomes; thresholds remain proposals. A [small repair check](repair-check.json) records that the review's failure policy is rejected and the ideal full-information policy can pass. Raw-evidence recomputation still passes, so the stronger representation claim remains conditional. This is one substantive repair; the author does not certify it.
