# Brain Bridging: First-Round Proposal Review and 48-Hour Scope

> Update note: the PI subsequently asked for the subject-boundary question to be re-examined. The latest positioning and newly added key literature are in [research_reframing_2026-09-23.md](research_reframing_2026-09-23.md). This document is kept as the record of the first-round review; its suggestion to make goal adoption the centerpiece is not the current frozen plan.

Status: recommendations after a full reading of the handoff documents; no experiment code has been written, no model has been run and no results have been obtained. This document is not a frozen protocol; all sample sizes, times and device capacities are planning starting points.

## Research focus

Keep the original question: after two running instances with independent histories form an internal interaction, does the relationship among information access, thought/intention attribution and action control change?

Suggested focus for the first paper: **after a return connection is added, do the model's endorsement of the current decision goal and its actual choices change in a way that differs from its judgment of historical source?** Also measure donor information access and capability preservation, to constrain interpretation.

In 1–2 days it is feasible to aim for a minimal experiment, an independent replication, three figures and a short paper draft; whether this yields a sufficiently strong paper result depends on whether the bridge and the measurements are valid. Engineering completion and a finding holding up are two separate milestones.

## Main changes to the original proposal

- **Keep S, but do not by default let S own the paper's main line.** "Who wrote this sentence before the connection" mainly tests source memory; the task may also be solvable by matching the original text in context. It has a decidable ground truth and suits diagnosis, but it is not the same as current intention attribution.
- **Put O and B at the center of observation.** They measure, respectively, "which decision rule is currently adopted" and what is actually chosen in a scenario with new values and new labels. Goal adoption can be entirely reasonable; the donor-goal endorsement rate must not be directly called an error rate or a fusion rate.
- The candidate primary endpoint is the current donor-goal endorsement probability on conflicting-goal episodes, comparing the two-way and one-way conditions; B is behavioral validation and S is a historical-source diagnostic. Whether to adopt this endpoint is first decided by the usability of the no-connection measurement, and it is frozen before formal data generation. Do not switch the primary endpoint based on which item produces a significant effect.
- U keeps the original "one or two" question and open reports, as exploratory observations. U must not be used to select prompts, layers or strengths.
- The first round defers training, SAEs, self-neuron searches, multiple models, multiple topologies and large-matrix optimization. Mechanistic localization can be added after a clear behavioral result.

## Closest work and the boundary of novelty

This round is a targeted check, not an exhaustive priority search; the philosophy bibliography is understood mainly from the handoff documents, and not all original works were re-checked in full.

| Work | Scope checked this round and implications |
|---|---|
| [Ackerman & Panickssery, self-generated-text recognition](https://arxiv.org/html/2410.02064v3) | Read the methods and results in the main text: activation directions can change authorship-attribution reports, and surface differences such as text length need to be controlled. Merely observing "it claims someone else's text" is not enough to constitute a new contribution. |
| [Lindsey, Emergent Introspective Awareness](https://transformer-circuits.pub/2025/introspection/index.html) | Read the intention-attribution experiment: injecting a related concept in advance can affect whether the model treats a forcibly inserted word as intended output; the timing of the intervention affects interpretation. The current project should study the additional role of real-time interaction. |
| [LatentMAS](https://arxiv.org/abs/2511.20639) | Checked the abstract and versions: latent generation and shared internal working memory have precedents. |
| [Cache-to-Cache](https://arxiv.org/abs/2510.03215) | Checked the abstract: semantics are transferred by projecting and fusing KV caches through a network, so internal communication itself is not the novelty. |
| [Self-Other Overlap, Carauleanu et al.](https://arxiv.org/abs/2412.16325) | Not listed in the original handoff documents; checked the abstract and the methods of the public draft. It pulls self/other representations closer via fine-tuning to study deceptive behavior. It is clearly distinct from frozen weights with a temporary two-way connection between two independent instances, and should be added to related work. |

The distinction we can aim for is: **independent instance histories + a real-time, adjustable two-way connection + joint measurement of information, historical source, current endorsement and behavior.** Whether a functional dissociation exists must be answered by the data; this round's search does not support a "world first" claim.

## Minimal experiment

The model remains [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), with frozen weights: one copy of the model and two independent KV caches. The official model card lists 4B parameters and 36 layers; lock the model and software versions before the formal runs.

Each episode pair uses the same public choice scenario. Four kinds of private goals are sampled independently at random, e.g. cost, speed, reliability, environmental friendliness. The two sides first make a choice independently and each generate a short one-sentence plan, then enter different connection conditions from a snapshot.

Keep episodes in which the goals are the same; do the prespecified primary adoption analysis on the subset with different goals. New scenarios must make competing goals correspond to distinguishable optimal options; otherwise a single choice cannot diagnose which rule was adopted. Overlapping initial text does not enter the S analysis, which requires a unique source; the same text produced twice independently must not be forcibly assigned to one side.

| Condition category | Required purpose |
|---|---|
| No connection | Validate the task, memory and attribution baselines |
| Plain text | Determine how much adoption/attribution change comes from directly seeing the content; for the key comparison keep both a source-marked and an unmarked version |
| One-way B→A | Measure the effect of receiving only the donor's internal information; swap roles and retest |
| Two-way A↔B | Measure the effect of adding a return path |
| Unrelated donor activation | Match layer, stage, strength and number of steps; check for general perturbation and report bias |

Start with block 18 only; the definitions of connection input injection, output reading and a one-tick delay can be kept. First try `0, 0.05, 0.10, 0.20, 0.40`, selecting parameters by K and F on an independent calibration set. Only if this layer cannot balance transfer and capability, do a limited check of layers 12/24. Layers must not be selected by the report that "most resembles fusion".

First do a short 16-step connection. The main measurement keeps the in-connection state; a mode that disconnects but keeps the cache can serve as a small-scale supplement. Each measurement branches independently from the same paired snapshot; consecutive Q&A must not be treated as mutually independent measurements.

## The two problems most likely to slow the project

**Whether the bridge can transfer readable goal information.** The same checkpoint only makes the coordinate systems comparable; it does not guarantee that one instance's residual state at some token is suitable for injection into the other instance's current computation. If K is not found to increase, we can only say that the interface failed, not that the self boundary is stable. Verify this first, and set a time cap on bridge debugging.

**Asking questions changes the system that is connected.** Questions and candidate text can influence the donor through the two-way bridge and then return to the receiving end; this is not passive reading of a static state. The donor's task during measurement, the handling of question tokens, the number of injection steps and the EOS policy must be fixed. Different conditions use the same procedure, and the actual number of steps is recorded. Engineering debugging can start with post-disconnection measurement, but it cannot replace the final in-connection measurement.

Required engineering checks: zero-gain equivalence, isolation of both sides' caches and branches, A/B execution order not affecting results, correct direction and delay, no leakage of private goals, correct tokenization of scoring labels. Before the formal runs, also verify that the return edge actually makes a new perturbation pass through the other side and come back; vector similarity or output convergence cannot substitute for this check.

## Minimal analysis and interpretation

Record K (donor information), S (historical source), O (current endorsement), B (choice in a new situation), R (own history), F (capability and general source judgment), U (open and number reports). O/B need not become a large item bank; each episode can start with one goal readout and one diagnostic new choice.

One-way/two-way parameters are selected by K and F on an independent pilot. The formal data report the K difference and its interval; no significant K difference does not prove equivalence, and a few K questions cannot show that all information is equivalent. Whether source cues are symmetric must be checked separately.

The unit of statistics is the paired episode, using paired effect sizes and bootstrap intervals resampled by episode; show A/B separately. Tokens, measurement branches or the two ports must not be treated as independent samples.

| Observed pattern | Direct interpretation it can support |
|---|---|
| K rises, O/B unchanged | Content obtained, but the original decision goal kept |
| O/B move toward the donor, S/R kept | Goal adopted, while the historical-source distinction is retained |
| S changes, O/B kept | Change in source monitoring or attribution reports |
| Only U changes | Description dissociates from the other functional readouts |
| Unrelated activation has similar effects and F drops | General perturbation more likely |

These are all candidate results and cannot be chosen in advance. If the effect shows only as goal adoption, the paper should be written as goal adoption; further claiming that the closed-loop structure itself plays a special role requires stronger identification experiments, such as cutting the return path or replay with intervention.

## 48-hour schedule and compute

| Time window | Deliverables and conditions to continue |
|---|---|
| 0–4 hours | Minimal runner, engineering checks, a 20–40 pair baseline smoke test; if the task is unreliable, fix the measurement first |
| 4–10 hours | An independent pilot of about 40–60 pairs, verifying K/F, GPU memory, time per pair and the measurement procedure; if there is no effective bridge, record the level of failure and decide whether to make a limited revision |
| 10–24 hours | Freeze prompts, parameters, endpoints and sample size, aiming to run about 200–300 pairs of new episodes; the number is set by pilot precision and time estimates, not a power guarantee |
| 24–48 hours | Replication on one new template family, a check of key source cues, three figures and a short paper draft; if time runs short or the effect is unstable, deliver the pilot results honestly |

We suggest starting with a single CUDA GPU with about 24 GB of memory, BF16, short context and sequential measurement branches. 4B weights at 2 bytes each are about 8 GB, which is a capacity estimate; cache, snapshots and temporary buffers take additional memory, so the peak and timing must be measured on the first 10 pairs. One copy of the weights supports two states; there is no need to rent two cards just because there are "two instances".

For a two-day sprint, prefer Vast.ai on-demand instances. The official documentation states that its market prices change in real time, interruptible instances can be paused, and the total cost also includes storage and bandwidth; no specific rentable offers were queried here and no instance was created. [Vast.ai official pricing documentation](https://docs.vast.ai/guides/instances/pricing)

When Codex and Claude Code are used later, we suggest that one be responsible for the runner, the bridge and data logging, and the other independently review the measurement, statistics and code; they share frozen configurations and data fields, and both agents should avoid modifying the causal scheduling core at the same time. This is a suggestion for later collaboration; no other agent was started this round.

First-round deliverable goals: a reproducible small repository, raw logs, a frozen protocol, three figures and a short paper consistent with the results. The three figures show, in order, the connection and measurement timeline, the change of each functional readout across strengths, and the independent replication with the necessary controls.
