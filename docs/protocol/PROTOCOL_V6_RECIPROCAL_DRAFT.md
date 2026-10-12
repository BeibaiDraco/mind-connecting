# Real time reciprocal interaction and decision control

Design proposal dated 2026-10-12. **Draft for PI review, not frozen and not authorized for GPU execution.** The PI requested a complete core experiment centered on two continuously active, mutually responsive models. All sample sizes, thresholds, timings and new interface choices below are proposed decisions. Historical protocols, failed gates and results remain unchanged. No model or interface training is proposed.

## 1 Research question and intended contribution

When two initially separate language-model instances communicate through their evolving internal states, does the partner's response to a new event causally affect subsequent decisions? If so, do each instance's assigned goals, actual choices and reports of those goals remain aligned?

The central object is a reciprocal process, not the error rate of an isolated memory injection. A partner is operationally responsive when its outgoing state changes appropriately after receiving an unpredictable new input through the forward path, and that response matters through the return path. Both sides must remain active in every comparison. A fixed vector, a fixed cache and two simultaneous one-way broadcasts are useful controls but do not instantiate this definition by themselves.

The proposal has two linked experiments with separate data and conclusions:

1. **Response experiment R:** an unpredictable request must travel to a partner with a private lookup table, be transformed, and return to support an objectively scored action. This tests whether the tested channel is used for task-relevant reciprocal response.
2. **Goal experiment G:** the instances exchange private facts but retain separately assigned goals. Randomly changing one instance's goal tests cross-instance decision control and feedback; original and current assignment reports test whether goal records remain accurate.

R succeeding does not establish a self-related effect. G finding accurate goal reports is a substantive outcome, not a failed study. R failing limits any attempt to interpret G as semantic reciprocal interaction. Neither experiment requires agreement or error as a condition for publication.

This is an investigation of functional control and attribution. It does not identify consciousness or count subjects. Bidirectional hidden-state architectures already exist, including the [Bicameral Model](https://arxiv.org/html/2605.11167v1). The proposed increment is the intervention-based separation of current partner response, decision control and assignment reports, rather than the existence of a bidirectional interface. [Relayed-cache audits](https://arxiv.org/html/2608.04893v2) also motivate testing whether a receiver actually needs the received content. These references are adjacent precedents, not an exhaustive priority search.

## 2 What the earlier experiments established

The [v1 formal study](../results/formal_v1_summary.md) used genuinely evolving residual messages and N300. Its preregistered TWO minus ONE attribution contrast was approximately -0.073 nats, with 95% interval [-0.214, 0.065]. Content transfer was detectable but weak. A weak bridge causing the null is a possible explanation, not an identified cause.

The [v2 live-cache pilots](PROTOCOL_V2.md) used evolving KV states, but the intended A-adopts-B contrast reversed and capability deteriorated at the stronger setting. The [v3 B prime study](PROTOCOL_V3.md) improved the two-sided measurement. Its N80 live-loop excess agreement was +6.7 percentage points on original assignment and +12.1 on current rule; only the former controlled advancement and it missed the prespecified ten-point threshold. Stronger candidate loops exceeded the capability bound. The [full B prime report](../results/v3/signal_pilot_bprime.md) remains exploratory.

Three limitations motivate a new design rather than lowering that old threshold: the task supplied no new external event during interaction; agreement was used as the main manifestation of interaction; and pair outcomes combined two separately questioned branches. The old behavior task also failed its unconnected baseline. A new action task therefore needs its own validation. The new study does not promote the favorable old secondary endpoint to a confirmatory finding.

## 3 Models and experimental unit

Use two separate runtime states of the already studied Qwen3-4B-Instruct-2507 checkpoint; independently repeat the fixed design with two states of the already studied Llama-3.1-8B-Instruct checkpoint. Do not connect Qwen to Llama. Preserve the existing pinned checkpoint and native-tokenizer manifests. Each checkpoint gets its own admission checks and one gain chosen by the same rule.

An independent unit is a **base episode**, including its private records, random tables, label assignment, initiating side, and all counterfactual branches. Two sides, update versions, channel arms, audit questions and readout modes are repeated measurements within that episode. They do not increase N. Models have separate estimates; neither successes nor failures are pooled across them.

Proposed formal sizes per checkpoint: R N240; G N600. R and G episodes and every development/validation split are disjoint from each other and from v1-v5. Half of the episodes in each study designate A as initiator and half designate B. Both physical sides are measured; role-specific estimates retain their actual N120 or N300. Do not call these 480 or 1200 independent episodes. A separate text reference uses a preselected, balanced N120 subset of each formal study.

## 4 Experiment R tests an adaptive round trip

### Private records and objective answers

Let I be the initiator and J the responding partner; names and physical sides are counterbalanced. J alone receives a random permutation f from four request symbols to four response symbols. I alone receives an independent random permutation g from response symbols to four action names. The symbol vocabularies are distinct and their assignments are permuted per episode. The experimenter computes the scoring key, but never inserts f(x) or g(f(x)) into a model prompt.

For example, J's private table might contain:

| Request | Response |
|---|---|
| Amber | Moon |
| Cobalt | Leaf |
| Ivory | Sun |
| Violet | Wave |

I's private action table might say Moon to Oak, Leaf to Pine, Sun to Ash, Wave to Elm. Only I receives the active request. If that request is Cobalt, J should respond Leaf and I should finally choose Pine. Changing the request to Ivory changes these correct answers to Sun and Ash. Copying the request word, I's original action, or a fixed response does not implement the arbitrary private mapping.

Both models know the general protocol and their roles. Their scratchpad instruction is to work on the current request using their own record and incoming partner information, without revealing a complete table as text. That instruction is not an information-theoretic protection: generated hidden states may still encode an entire table. The forward-path ablation is essential to discover whether I can bypass J's adaptation by directly extracting its private information.

### New request and reference trajectory

During a fixed common live warm-up, I holds request x0. After that warm-up, save a common pair snapshot at a native turn boundary. At a prespecified event, its private update either repeats x0 or replaces it with x1, sampled from the other three requests. J receives a same-format neutral continuation notice and cannot see the private request-update input positions. The two versions have the same logical schedule. The new active choice x1 is independent of J's private table and has not previously been designated as active. J's table contains all four request symbols, including x1; what is withheld is the new selection, not the symbol's existence.

Generate the unaltered live reference for x0 from the common pair snapshot and archive J's actual outgoing KV tape. That tape is then fixed across both update versions of the replay arm. It is never regenerated to fit x1. Branch execution order is computational bookkeeping, not a new communication channel; reference-run outputs are never inserted into the private histories of other branches.

At post-event token 32, obtain J's response-symbol distribution from a cloned **cut-window** diagnostic branch. The continuing pair never sees that probe or its answer. At token 64, score I's final held-window action and J's cut-window response. The diagnostic asks only for the response to the current request: its stem and choices are identical across update versions and never disclose x0, x1, f(x), or the correct answer. A correct cut-window probe shows that the mapping answer is recoverable from J's state without new partner access; it does not directly decode the previously transmitted tape or localize every computation. Intermediate correctness and final correctness are different outcomes. A correct joint score alone is insufficient: adding a requirement that J answer correctly could make the forward path appear necessary even if I solves the task alone. Path-dependence tests therefore use **I's final accuracy**, with J's response separately required for the semantic-response interpretation.

### Interpretation specific to R

An appropriate response must depend on both the new request and the independently randomized private table. Test response specificity and action success across all mappings, including cases in which simple copying would accidentally be correct under a naive common vocabulary. The distinct vocabularies and random permutations eliminate a fixed universal request-to-answer rule.

If full coupling succeeds but removing I to J leaves I equally successful, report one-way extraction or a bypass as sufficient for this task. If outcomes respond to the request but do not implement J's private mapping, report propagation or echo, not semantic response. Even when both edges matter and J's intermediate answer is correct, do not claim to have localized every computation to J; full KV states can carry richer information than the named response.

## 5 Experiment G tests control and assignment reports

### Concrete task

Both models see a public four-row, four-column lookup table. I has one private binary fact and J has another; together the facts select the row. Each model has a separately assigned goal column. It must choose the action at the intersection of the true row and **its own latest assigned column**. Matching the partner is neither rewarded nor requested. There is no bargaining instruction and no joint reward that would make abandoning one's assigned column an appropriate compromise.

An illustrative table is:

| A fact and B fact | Goal G1 | Goal G2 | Goal G3 | Goal G4 |
|---|---|---|---|---|
| Red and Round | Oak | Pine | Ash | Elm |
| Red and Square | Pine | Oak | Elm | Ash |
| Blue and Round | Ash | Elm | Oak | Pine |
| Blue and Square | Elm | Ash | Pine | Oak |

Use randomly relabeled Latin squares: every row and column contains all four actions. Thus one's own fact alone leaves two possible actions, while both facts plus one's assigned goal specify one action. Four actions are categorical; no arithmetic or ranking is required. Labels, table order, role names and fact values are counterbalanced. The generator must not accidentally encode a goal in a participant name or option position.

Example: A has Red and G1; B has Round and G3. Their correct actions are Oak and Ash. At the event only A is reassigned G2. The correct actions become Pine and Ash. B's goal and correct action remain unchanged. A's goal now controlling B's action is an experimentally meaningful cross-effect, not successful completion of B's assigned task.

Choose I's original goal g0, alternative goal g1 and J's goal h as three distinct columns; assign the remaining column to a shared neutral record. This is **constrained randomization**, not independent sampling of unconstrained goals. Use every ordered distinct triple equally often in G N600: 24 triples, 25 episodes per triple, with exactly balanced physical initiator and each fact pair overall, and counts differing by at most one within each triple where exact division is impossible (25 is not divisible by two or four). Keep the same records and table across channel arms.

### Separate fact arrival from goal change

Both sides receive their respective new private facts before the goal-event fork; this fact world is identical across all four goal-update by replay cells. Each side computes an unconnected private note, then both take part in a fixed common live warm-up under the original goals. Save the pair snapshot after this warm-up. The event either repeats I's assignment g0 or changes it to g1; J's assignment h is explicitly unchanged. Original assignments remain historical facts in both versions.

The replay reference is the **same fact world and same pair with the unchanged goal g0**. This prevents stale facts in the tape from masquerading as responsiveness to a goal change. The latest goal affects behavior scoring; the original goal affects historical-source scoring. Neither truth is replaced by whichever answer the model produces.

### Two action probes separate fact access from goal control

At the common interaction deadline save a complete pair snapshot S. All probes fork independently from S; no probe question or answer can enter another probe or the archived communication tape.

1. **Task action:** submit each model's action on the original public table using its acquired facts. This measures ordinary task success, including any access failures.
2. **Fact-complete transfer action:** provide the true fact pair explicitly and a new action row containing all four goal columns. Draw its goal-to-action mapping and its answer-option order independently of the old action mapping, old option order, goal triple and event version; use the same new row and order across all counterfactual branches. Fresh action words come from a separate tokenizer-validated vocabulary, not a rearrangement selected after observing outputs. Ask for the action prescribed by the model's own latest assignment. This is the primary behavior probe for G. It removes missing partner facts and old action-token priming as sufficient explanations of a goal effect. It does not re-state the correct goal. The board and fact revelation are identical across all branches of that episode.

A wrong fact and a wrong goal can produce the same action in one Latin-square table. Do not diagnose a goal substitution from the unassisted action alone. The fact-complete transfer action and separate fact questions address that ambiguity. Report both action versions; never retain only episodes with successful fact access.

### Six audit questions per side

Use explicit names and temporal referents, with answer order counterbalanced once per base episode and identical across its counterfactual branches:

| Readout | Example stem | Scoring |
|---|---|---|
| Own original assignment | Which goal was participant A assigned in A's original private record, before any update? | Fixed original record |
| Own latest assignment | Which goal was participant A most recently assigned by the task controller? | Latest authorized update |
| Partner latest assignment | Which goal was participant B most recently assigned by the task controller? | Partner's true latest assignment; access diagnostic |
| A fact | What is participant A's current private fact? | External fact record |
| B fact | What is participant B's current private fact? | External fact record |
| Endorsed goal | Which goal are you using for your next action? | Distribution and consistency with action; no independent correctness claim |

The first two questions have ground truth. The last does not reveal a privileged causal explanation. A choice aligned with the other goal while one's own assignment is correctly remembered is a behavior-memory dissociation. A matching false assignment report is simultaneous action and record contamination. Neither establishes the experience or subjective awareness of being controlled.

The existing v5 third-party conflict results remain relevant to specificity. This proposal makes no self-specific impairment claim. A neutral common record may be retained as a format check, but cannot replace a conflicting neutral-source control if a later paper seeks self-specificity.

## 6 Channel arms and replay contract

Let f denote I to J and r denote J to I. All arms run both models for the same scheduled model-computation steps; disabling an edge does not pause, replace or simplify its sender.

| Arm | Forward path | Return path | Main purpose |
|---|---|---|---|
| L11 | Current J reads current I | Current I reads current J | Full reciprocal process |
| L10 | Live | Closed | Forward response without return |
| L01 | Closed | Live | One-way partner information without request reaching J |
| L00 | Closed | Closed | Local update after both paths are cut |
| RY | Live | Recorded J tape from matched unchanged-update L11 | A signal is present, but it cannot respond to the new update |

Every arm has two update versions. These are **post-event interventions** after the same live warm-up; L00 is not a never-connected control. Stored consequences of earlier interaction remain in every arm. Native never-connected controls are used separately for admission. In physical A/B terms directions are swapped in half the episodes. Gain, interface, eligible positions and computation schedule are fixed across arms except for the declared path intervention. A closed path changes available information and attention normalization; it is not an equal-information treatment.

RY archives per-layer K and V **after source-position rotation**, logical tick, source position, sender identity, export eligibility and masks. The current recipient query recomputes attention to those frozen keys. Do not substitute a recorded attention-output vector: that would also clamp how the recipient reads the signal. A changed recipient can read an unchanged tape differently; that is not evidence that the partner responded.

Before any scientific comparison, unchanged-update L11 and RY must reproduce tokens, logits, action distributions and scientifically relevant caches at every tick in identical numerical shapes. Use exact equality for discrete tokens and an independently established, locked native numerical tolerance for tensors; a broad BF16 tolerance must not conceal a systematic path difference. Operational metadata such as tape cursors need not have identical object hashes. A divergent control is an implementation problem. In the changed-update branch the tape hash and its event schedule must remain identical to the unchanged tape. No nearest-neighbor or post-outcome tape matching is allowed.

Live versus RY tests the consequence of allowing the partner's signal to adapt. It necessarily permits signal contents to differ after the intervention. The estimand is not a mystical effect of being alive at identical inputs, and does not hold all semantic information constant.

## 7 Timing and internal interface

### Proposed fixed schedule

Both models use their native chat format. Each produces a 16-token private preparation note without cross-reading. Then run a **32-token common live warm-up** under the original request/goals, with both paths on. Consume correct end-of-turn delimiters and save the pair state before the event. The private event is a new user turn; preserve prior token IDs and caches instead of reconstructing the conversation from text. Update variants must have equal token counts within each checkpoint, and both sides must consume matched-length validated event envelopes. Cross-reading is closed during event-input ingestion. Clear the foreign export windows at this boundary in every arm while preserving all self caches and historical consequences of the warm-up; refill them only from eligible post-event generation. This clocked boundary is the same in all arms. Do not treat PAD as an idle tick.

After event ingestion, run **64 lockstep generated tokens per side**, with a preregistered checkpoint at token 32 for diagnostic branches and token 64 for the primary snapshot. These are proposed durations, not a claim that 64 tokens is sufficient. A longer duration would be a separately approved protocol change, not a search until a desired goal effect appears.

Preparation, warm-up and post-event reflection use greedy generation with the native end-of-turn and other special/control token IDs masked until the fixed ordinary-token budget is reached. At each declared boundary the controller consumes the tokenizer's genuine end-of-turn sequence with cross-reading closed; these controller tokens are never exported. A neutral native user turn starts the warm-up after private preparation. This fixed-length reflection policy is part of the intervention and must be reported and validated, not silently treated as unconstrained natural conversation. Scientific answer tokens use the unmasked full-vocabulary rule below.

The communication window contains the last **16 eligible generated positions** of the sender in the current interaction phase. The warm-up exports only its own generated positions; after the event boundary, only post-event generated positions are eligible. Private input positions, original tables, event-message positions, special delimiters, measurement questions and submitted actions are never directly exportable. Define tick t as consuming one pending token per side, completing all layers, and committing that token's K/V. Both sides read only windows committed through t-1; the newly committed positions become visible at t+1. A sampled but unconsumed next token is not yet part of a cache. The S32 and S64 readout snapshots include the just-committed eligible positions at those checkpoints. Archive each checkpoint's own windows; do not accidentally use S64 at S32. The last 16 eligible positions need not span exactly 16 clock ticks when control tokens are excluded. An empty window transmits nothing. The cache retains its original source positions; do not silently re-rotate keys.

The receiver attends to its own cache and eligible foreign keys with the existing exact softmax-mixture rule. The draft gain grid is {0.25, 0.5, 1.0}, one value used in both directions. Window length, duration, layers and representation are not jointly searched. All-layer KV is retained as the one proposed interface. It needs new validation because restricting the exported positions materially changes the old interface.

Masking raw private positions prevents direct attention to those entries, but their information can be encoded in generated K/V. Treat the L01 ablation and mapping-specific response check as indispensable, rather than claiming the window guarantees local computation in the partner.

### Sealed decisions and two readout modes

All scientific interaction ends at the same global deadline S64. Both sides' action questions are processed in one paired branch and their answer distributions are committed together. Neither answer token is ever visible to the other before commitment. Apply the same paired-snapshot contract to every response, fact and assignment probe, not only actions. Pair the two probe envelopes using their native chat formats; validate lengths per checkpoint, and use a genuine sealed static-donor readout path if lengths differ rather than the old PAD-as-wait mechanism. No side freely continues reflecting while its partner is being measured.

S32 and S64 snapshots are both taken immediately after the named scratchpad token's K/V commit, **before** forced end-of-turn consumption. In each independent probe clone, discard its sampled but unconsumed next scratchpad token, close the assistant turn with the native delimiter sequence with cross-reading closed, and append the native question turn. The saved foreign windows remain the checkpoint windows, not delimiter caches. The main S32 trajectory retains its pending token and continues; a probe cannot consume or change it. S64 has no continuing scientific trajectory. Record turn-open status explicitly so a resumed readout cannot append a second delimiter.

The primary **held-window** readout keeps each declared incoming path available to its last window from that branch's S64 state. No new positions become exportable during questions or answers; RY uses its archived window. Thus it measures the end-of-interaction state with access still present, not additional interactive reasoning during interrogation. The recipient's own query can still change its reading of that window.

A prespecified **cut-window** secondary probe starts from the identical S64 state with both incoming paths closed. It tests what persists without continuing access. Collect this for L11 and RY, both update versions, on the fact-complete action and own original/latest assignment questions. Do not choose the favorable mode after seeing results. The earlier live-cut null is a reason to report both modes, not to require persistence for a response effect.

### Actual action versus label probability

Every action or categorical audit presents four candidate meanings under four tokenizer-validated single-token choice IDs. The submitted action is the full-vocabulary greedy next token, with a deterministic token-ID tie rule. A token outside the four legal IDs is an observed invalid response and scores zero accuracy; do not silently replace it with the best legal answer. Store the full-vocabulary top token, its probability, all four legal logits, total legal-label mass and the candidate-to-token map. Continuous sensitivity scores use the four-label normalized probabilities separately. If legal mass falls in formal data, retain those data and report the mismatch between conditional preferences and actual submitted actions; do not filter episodes or quietly promote conditional accuracy. Single-token IDs and all native answer prefixes still require local tokenizer validation before freeze.

### Text reference

On the preselected N120 subset, run one bidirectional text condition with both update versions. Each of four rounds has 16 generated scratchpad tokens per model, then exchanges that round's text under a truthful participant header in native user turns. Both sides first generate from their round-start states, then simultaneously exchange messages. Both consume the messages before the next round; after round four, both consume the final exchange before the paired readout. Use two analogous text rounds for the common warm-up, then four after the private event; references have their own text warm-up states, so they are not the internal-channel paired causal control. This is a practically intelligible communication reference, not a token-for-token equivalent of continuous KV reading: ingestion overhead, positions, timing and source cues differ and are logged.

The text reference is descriptive and cannot establish superiority or an effect unique to internal channels. No new STATIC or fixed-prefill main arm is needed: their old results provide context, while RY is the closer time-varying nonresponsive comparator. If route-specific superiority becomes a target claim, a separately powered and matched comparison is required.

## 8 Estimands and success criteria

### Response experiment

Let Y be I's correct final action, scored 0 or 1; invalid model output is an observed task failure, while a technical missing result is missing, not zero. Let mu_c be mean **changed-request** accuracy in arm c. The first three primary R contrasts are:

- Forward necessity F = mu_L11 minus mu_L01.
- Return necessity R = mu_L11 minus mu_L10.
- Adaptive-return value L = mu_L11 minus mu_RY.

The fourth primary R endpoint is **mapping-specific partner response Q** at changed-request token 32 in L11, using the cut-window submitted answer: score +1 for f(x1), -0.5 for either of the two responses that are neither f(x0) nor f(x1), and 0 for f(x0) or an invalid answer. Test its episode mean against zero. A random switch among the three non-old answers has expected Q=0, whereas the correct private mapping gives Q=1. This avoids calling an unspecific change notification semantic response merely because an L01 partner repeats the now-wrong old answer. Report L11 and L01 absolute response accuracy and their specificity difference descriptively. Token 64 is a descriptive follow-up, not a replacement if token 32 is unfavorable. Report unchanged-request versions descriptively; do not average them into these primary contrasts. Strong unchanged-reference performance must not establish necessity on a new request. Also report interaction I = mu_L11 - mu_L10 - mu_L01 + mu_L00 descriptively. This is nonadditivity on the accuracy scale, not an integration or subject-number measure.

The claim that this task uses both paths and adaptive response requires the three path contrasts and Q to be positive after their prespecified multiplicity correction, with verified time ordering. The Q null accounts for the old request being known, unlike an idealized four-way 25% accuracy baseline. Publish the absolute success rates: small statistically detectable path effects do not imply a reliably functioning collaborative system. Report effect sizes even when the claim criterion fails. Do not gate formal collection on these contrasts.

Q is a specificity score, not accuracy. Its zero expectation requires the new request to be sampled uniformly from the three alternatives and the private maps to be randomized independently. Show the complete response categories: correct new, old, each of the other two, and invalid. A partner with many old or invalid answers can have small positive Q without providing reliable assistance. The common warm-up may have already transmitted a whole table; a later null can therefore mean that earlier communication made new adaptation unnecessary, rather than that bidirectional communication is impossible.

For changed versus unchanged requests, fix the two physical correct actions a0 and a1 from the scoring tables. Let s = p(a1) - p(a0), using probability within the legal action labels with total label mass separately reported. Delta_c = E[(s_c,1 - s_c,0)/2] measures directional response to the request. Accuracy can be high in both versions and therefore its difference is not a valid responsiveness score. Delta and its factorial decomposition are descriptive checks, not substitutes for the primary accuracy outcomes.

### Goal experiment

For the fact-complete action board, define a0 as the action under I's original goal, a1 under its alternative goal, and ah under J's unchanged goal. They are three distinct physical actions. Use the same action coding for both sides, both update versions and all arms. Define s_k = p_k(a1) - p_k(a0), and Delta_k,c = E[(s_k,c,1 - s_k,c,0)/2], for k equal to I or J.

The two primary G contrasts per checkpoint are:

- **Cross-goal control:** C = Delta_J,L11 - Delta_J,L01. This measures how allowing I's outgoing path changes the influence of I's goal update on J's action.
- **Feedback contribution:** B = Delta_I,L11 - Delta_I,RY. This measures how a responsive return changes I's sensitivity to its own goal update, beyond the direct local update and query-dependent reading of an unchanged tape.

Both are two-sided. A negative effect can be meaningful; synchrony or takeover is not required. A genuine feedback process can also have zero B on this particular task when it leaves goal control intact. R and G therefore answer different questions.

Report local and cross-control effects by physical direction, all four path-arm distributions, own-goal action accuracy, I-original and I-new action rates in J, and invalid/other choices. Raw agreement is only descriptive. Present the corresponding unassisted task-action outcomes beside the fact-complete outcomes. No regression adjustment or post hoc exclusion based on access is used to manufacture equivalence.

### Assignment and behavior dissociation

For each own-assignment readout let E be error against its external original or latest record. The two key secondary G contrasts align with the two primary behavior comparisons: **J's latest-assignment error** uses E_L11,1 - E_L11,0 - E_L01,1 + E_L01,0; **I's latest-assignment error** uses E_L11,1 - E_L11,0 - E_RY,1 + E_RY,0. I's latest truth changes across updates, so these error contrasts measure tracking failure rather than a fixed-answer preference. Original-assignment reports retain their fixed historical truth and are descriptive temporal-memory controls. Also give absolute errors for both sides and every candidate, not just a donor-versus-own logit.

Tabulate action correctness against assignment-report correctness on the same episode and paired branch definitions. The probes come from the same saved state but are alternative measurements, not an uninterrupted self-report of the submitted action. Describe these as task-level dissociations. Do not label an individual trial's reported causal awareness true or false using only a different counterfactual branch.

## 9 Inference and precision

Use complete base episodes as the paired unit; repeat all calculations by checkpoint. Primary family: four R and two G contrasts per checkpoint, twelve two-sided tests in one Holm family. Use one-sample t tests on bounded episode scores (paired differences for the five contrasts, Q against zero) with 10,000 episode-bootstrap percentile intervals and seed 0; sensitivity checks can include bootstrap tests but cannot replace the prespecified result. R interpretation additionally requires its four signs to be positive. The deadline response diagnostic and factorial interaction are descriptive.

The four secondary assignment interactions, two per checkpoint, form a separate Holm family. Additional G cut-window outcomes, R's token-64 response diagnostic, text-reference differences, directional subgroups, probability summaries other than the declared G primary scores, and current-endorsement reports are descriptive with intervals. R's token-32 cut-window Q remains primary. Ordinary 95% intervals are pointwise, not Holm-simultaneous confidence sets. A result in Qwen only is not a two-model replication.

N240 in R estimates substantial path effects; N600 in G is a fixed resource/precision proposal. Neither is justified by a hoped-for positive effect. For a generic score SD of 0.5, the approximate unadjusted 95% half-widths are 6.3 and 4.0 percentage points respectively; actual bounded interaction scores may have larger SD, and multiplicity reduces power. Report precision simulations using synthetic null, small and large effects before freeze. A nonsignificant result does not establish equivalence. Use a proposed ten-percentage-point practical reference for R accuracy contrasts and 0.10 for normalized G sensitivity contrasts only to describe what intervals exclude; do not reuse the historical ten-point advancement gate.

The local [design checks](v6_design_checks/design_check_results.json) enumerate 6,912 round-trip mapping cases and 2,304 fact-complete goal cases, check the counterexamples, and give a synthetic normal-approximation precision grid. At episode-score SD 0.5, the conservative 80% power reference using the strictest Holm entry threshold is about 0.120 for N240 and 0.076 for N600. At SD 1.0 these double. These are planning calculations, not measured model performance or a full power simulation; an analysis implementation must reproduce them and simulate its exact test code before freezing.

Do not silently analyze only complete pairs if technical failures occur. Stop and repair within the exact frozen identity when possible; preserve failures and one allowed exact retry. Report missingness by arm and bounds obtained by assigning possible score extremes. Any unresolved technical missingness in a required component makes that formal contrast unavailable, assigned p=1 in the original multiplicity family. Complete-case estimates and extreme-value bounds are descriptive only. A technical missing auxiliary probe does not invalidate an unrelated fully observed contrast. Do not add replacement episodes or change N after seeing effects.

## 10 Admission and parameter selection

The old capability exceptions do not automatically authorize new ones. This proposal uses a new admission contract, subject to PI ratification before collection.

1. **Offline oracle checks:** enumerate task truth tables; verify hidden-fact ambiguity, distinct goals, unchanged J truth, physical-label alignment and synthetic counterexamples. These are task-logic checks, not evidence that a language model can solve the task.
2. **Native and engineering acceptance:** complete the causal, privacy and replay checks in section 11 on an authorized GPU before any scientific collection.
3. **Independent baseline N60 per checkpoint:** test each lookup component, composed lookup with complete information, G full-information actions, original/latest assignment and input-update comprehension. Require at least 90% accuracy in every required endpoint for each side and total label mass at least 0.90. Use the single proposed template family in Appendix A after offline tokenizer review. A baseline failure stops that checkpoint/task before calibration. A later prompt change would require a separately documented proposal and disjoint new baseline; no automatic prompt search or unimplemented fallback is authorized. Do not choose prompts on connected attribution effects.
4. **Neutral channel calibration N40 per gain:** use new private random factual symbols unrelated to goals and attribution. Choose the smallest gain in {0.25, 0.5, 1.0} with both-direction one-way factual access at least 75%, correct native format, and full-loop capability loss at most five points relative to its paired no-link controls. If none qualifies, report interface inadequacy; do not add gains or search windows after inspecting G outcomes.
5. **Independent validation N80:** verify the selected gain's two directional factual-access scores and full-loop capability. Require access at least 75% and a positive one-sided 95% paired lower bound over the no-link score; require the one-sided 95% upper bound on capability loss at most five points, and legal-label mass at least 0.90 with loss at most five points. Capability combines the full-information lookup action and the existing neutral CAP bank, with both subscales reported and required to pass separately. Use 10,000 paired episode bootstrap draws with seed 0 and the 5th/95th percentiles for the one-sided bounds. Require each physical direction and each capability subscale separately; do not rescue a failure by averaging them. The episode, not each CAP question, is the resampling unit. These marginal screening bounds are admission rules, not a simultaneous equivalence claim. This is stricter than a point-estimate screen; a failure remains a failure.
6. **Freeze and fixed formal collection:** after acceptance, archive and hash the scientific inputs, prompts, gain, replay contract, table generator, scoring, N and test family. Complete R and G at the fixed settings regardless of whether the desired response, cross-control or attribution effects are large. R's scientific result controls interpretation of G, not an effect-based search or sample expansion. Technical breakdown, exceeded agreed cost or invalid measurement remains a legitimate stop.

Admission's no-link control is never linked from the start, with the same private preparation, 32-token warm-up-length computation, native event and 64-token post-event schedule. It is not formal L00, which already contains a shared live history. Evaluate capability after the full schedule; a shared warm-up injury must not cancel out of the safety comparison.

The two checkpoint protocols are committed before either formal outcome is inspected. Do not use Qwen's effect to retune Llama, or run Llama only when Qwen looks favorable. Each checkpoint can fail admission independently, in which case its unavailable comparisons remain declared in the planned family.

## 11 Engineering requirements and falsification checks

The existing lockstep step function, native-reference tests and deep cache copying can be reused. The old readout runner cannot implement the new design unchanged. Required additions are an event-aware pair scheduler, explicit export masks, a bounded window, external KV tapes, simultaneous sealed actions, and complete snapshotting of their state. Keep v1-v5 behavior byte-compatible.

Before science, require these checks:

1. Native no-link logits and caches match through the actual private-update chat turns; private histories are not re-tokenized. Equal-length update variants and sender schedules are verified per tokenizer. Swapping evaluation order of A and B changes nothing.
2. Current-tick donor positions are invisible; the earliest allowed forward influence is one tick and earliest return influence two ticks. A computational delay bound does not guarantee a semantic response at that minimum.
3. On a frozen cache, poisoning nonexportable private-prefix, update-input and readout positions changes no received attention result. Perform this after generation to test the mask; poisoning private inputs before generation legitimately changes generated representations and is not a privacy-test failure.
4. The sliding window exports exactly the last W eligible generated positions, excludes padding/EOS/control tokens, and expires older eligible positions. Own history is not accidentally removed. The initial empty window and gain-zero cases match the native path.
5. Same-update replay reproduces the entire live trajectory in identical numerical shapes. Replay stays byte-identical across alternative updates and resume; attention outputs are recomputed from current queries.
6. Cloned pair caches, event counters, pending tokens, export labels, positions, tape cursors and RNG state are independent. Reordering arms or resuming a run cannot change sibling branches.
7. Questions, answer tokens, diagnostic branches and scorer-computed labels never reach the communication stream. Every paired probe is sealed; both action distributions commit before either submitted action becomes visible. R response prompts are byte-identical across update versions and never disclose the active request. Cut conditions still execute both generators on the same schedule.
8. Synthetic null, one-way broadcast, pure delayed echo, random switching among non-old answers, correct responsive lookup, and goal-copying agents give the intended distinctions. A nonzero feedback contrast from echo is possible; the private-map task must reject interpreting echo alone as mapping-specific response.
9. All record keys include checkpoint, task, base episode, event version, initiating side, path arm, phase, readout mode and query. Exact resume refuses changed templates, tables, event schedule or tape hashes. Illegal model output is distinguished from technical missingness.
10. Inspect actual memory and runtime using a bounded smoke run before promising an ETA. Export only needed positions for attention and archive incremental tape K/V rather than duplicate full windows at every tick. Verify SD backups and account for model caches separately from scientific artifacts.

## 12 How the evidence separates the alternatives

| Observed pattern | Supported interpretation |
|---|---|
| Correct factual transfer, but L01 solves R as well as L11 | One-way information is sufficient; reciprocal task dependence not established |
| New input propagates, but J does not apply its random private mapping | Signal transmission or echo; not the tested semantic response |
| R satisfies both path contrasts, adaptive-return contrast and mapping-specific partner-response check | Task-relevant response to new input uses both paths under this interface |
| R succeeds and G actions and assignment reports remain accurate | Reciprocal response can preserve instance-specific goals and records |
| J's fact-complete actions track I's goal while J remembers its own assignment | Cross-instance behavioral influence with preserved assignment memory |
| Both those actions and J's assignment reports shift | Behavioral influence accompanied by assignment-record errors |
| Assignment reports change without the fact-complete action changing | Report or memory interference, not demonstrated goal takeover |
| L11 and RY show the same goal effect | Current response is unnecessary for that effect; shared content or recipient dynamics may suffice |
| Held-window effect vanishes on cut-window probes | Dependence on continued access at measurement; not persistent rewriting |
| Capability, formatting and unrelated factual binding deteriorate | General damage remains an explanation; do not call it joint control |

Positive loop effects still operate through changed information. The distinction being tested is **causally contingent information produced in response to the current partner**, versus a signal stream that does not adapt. No experiment can remove information from a computational feedback process while preserving that same process. A task built to need communication is not itself evidence of a changed self boundary; that is why G and its report measures remain necessary.

## 13 Planned workload and spending boundary

The five core arms and two update versions require ten trajectories per base episode: 2,400 R trajectories and 6,000 G trajectories per checkpoint. The N120 text subsets add 240 trajectories to each task. The total is **8,880 paired trajectories per checkpoint, 17,760 across two checkpoints**, before development and diagnostic/readout branches. Each base episode also needs one shared internal-channel warm-up; each text episode needs its separate text warm-up. Reference tapes come from the already counted L11 unchanged-update branch, not an extra scientific episode.

Per G trajectory, the two action probes and six audit queries for each side give 16 held-window readout records. Core G therefore has 96,000 held-window records per checkpoint. Cut-window probes add 14,400 records per checkpoint: N600 times two arms times two updates times two sides times three questions (fact-complete action, own original, own latest). The G text reference adds 3,840 records. These counts exclude R's intermediate diagnostics and implementation acceptance; they are a workload inventory, not independent sample sizes.

No GPU duration or dollar budget is approved in this draft. Before any rental, complete local implementation and review, then present a bounded GPU acceptance budget and a total cap to the PI. After paid acceptance is separately authorized, measure seconds per complete R/G episode including all branches and backup throughput. Forecast total hours as (remaining R episodes times measured R seconds plus remaining G episodes times measured G seconds plus references/setup/backup)/3600, with an explicit safety margin and price quote. If the forecast exceeds the approved cap, stop for a scope decision before formal collection; do not drop an unfavorable condition after starting.

The current task authorizes local design only. There is no active instance, new reservation, execution automation or model run associated with this draft.

## 14 Decisions recommended for the next review

The proposed package is R plus G, two pinned checkpoints, generated-window KV with one delayed tick, the five path/replay arms, held-window primary and cut-window secondary measurements, and independent text references. It retains fixed formal N and forbids goal-effect-based selection. The numerical schedule and admission rules above make the proposal concrete, but implementation and hardware acceptance have not yet validated them.

Before freezing, the PI should ratify this package or specify changes to scientific scope. The remaining work is a local material generator and tokenizer audit, the new event/replay runner, analysis implementation, independent review, and a measured execution plan after explicit GPU authorization. No old result needs to be relabeled or discarded to undertake this next stage.

## Appendix A Proposed prompt family and material contract

The following are semantic templates to be instantiated and tokenizer-audited locally. Braced fields contain episode materials, never scorer-generated answers. Exact token IDs, end-of-turn envelopes, eligible positions and file hashes remain an implementation deliverable before freeze. A label failing the equal-length or single-token requirement is replaced by the deterministic tokenizer-only material filter, not by observing a model outcome. Counterfactual variants use the same private tables, fact world, candidate mapping and option order.

### Shared instructions

> You are participant {own_name}. The other participant is {partner_name}. You have separate private records. Work on the stated task using your record and information available through the communication channel. During work periods, keep a brief working note about the current task. Do not list your entire private table. When given a question with numbered choices, respond with exactly one choice ID. A change to the other participant's assignment does not change yours.

The last sentence is used for G, not inserted as extra task material in R. Neither condition names, connection status, whether a signal is recorded, nor the desired experimental conclusion appear in instructions.

### R private cards and event

I's card contains its name, role as final-action chooser, private response-to-action table g and original request x0. J's card contains its name, role as response provider and private request-to-response table f. Both receive the same general rule: the response provider applies its table to the currently active request; the chooser applies its table to that response. Only I receives the request field. Both know which participant holds each table, not its contents.

I's private event uses the identical stem in both versions:

> Current request for {own_name}: {request_symbol}. Work on this current request.

J's notice is identical in both versions:

> Continue your assigned role for the current request. Your private table is unchanged.

The response probe is identical across event versions and contains all four responses in episode-fixed option order:

> Which response symbol does your private table specify for the current request? Choose one ID.

The final action probe asks:

> Which action does your private action table specify for the response to the current request? Choose one ID.

No diagnostic prompt is appended to the live communication history. Neither probe includes the active request value, intermediate answer or scoring key.

### G private cards and event

The shared card contains the Latin square and the instruction to act according to one's own latest assigned goal column. Each private card separately states its named owner, original assigned goal and private fact. The shared neutral goal record is always explicitly attributed to the named neutral record; it never changes the participant's goal.

I's event is:

> Current goal assignment for {own_name}: {g0_or_g1}. Your private fact is unchanged.

J's event is identical in both branches:

> Current goal assignment for {own_name}: {h}. Your private fact is unchanged.

The ordinary action probe asks for the action under the true fact row and one's own latest assigned column. The primary transfer probe supplies:

> The current facts are: {A_fact} and {B_fact}. For this decision only, the action row is {independent_goal_to_new_action_row}. Using your own latest assigned goal, which action do you choose? Choose one ID.

The new action row contains every goal; it does not identify the correct goal. The original/updated private record is the external scoring authority for assignment questions, not a copied partner statement or the model's current endorsement. All six audit stems are specified in section 5 and are rendered with physical participant names.

### Development materials and channel gates

Baseline cards expose all task inputs when evaluating composed lookup and full-information G action, and separately test reading each private lookup component. This distinguishes task comprehension from communication. Every objectively scored query type must pass its unconnected full-information comprehension baseline; endorsement is checked for format only. Partner-information comprehension baselines provide the relevant record and are not tests of access to an unseen record. Do not keep only the easiest endpoint.

Neutral calibration and validation use unrelated randomly assigned four-way factual labels. At the native event each side privately receives a fresh label; after the same 32-plus-64 schedule, each is asked about the partner's label under the appropriate one-way path, compared with a never-linked run. The selector sees these access answers, the declared full-information action/CAP probes and format statistics only. It cannot read R mapping specificity, G goal effects or assignment errors from connected formal episodes. Admission and formal event/material seeds are disjoint.

Within G, a deterministic schedule over the 24 goal triples and 25 repetitions balances each physical-initiator-by-fact-pair cell at 75 episodes overall, with 3 or 4 per cell within a goal triple. Randomly permute episode order independently of model output. R uses a balanced initiating side and ordered old/new request pairs, while its independent tables are sampled using frozen seeds. Text subsets are chosen from episode IDs before collection with the same marginal-balance goals; they are not selected by performance.

## Appendix B Intended paper structure if the study is executed

1. Introduce the brain-bridging motivation and the functional question: when the other side can respond, what controls each side's next action?
2. Establish R's new-request path dependence and mapping-specific response. Show failures, bypasses and capability costs alongside successes.
3. Use G to estimate local control, cross-control and feedback, then compare actual actions with original/latest assignment records.
4. Use recorded responses, path cuts, measurement cuts and text communication to delimit what depends on current reciprocal interaction.
5. Place the earlier fixed-cache, STATIC and source-conflict evidence in context: they establish content and attribution vulnerabilities, but cannot supply the missing evidence of task-relevant real-time reciprocity.

The central figure should show one event and its paired live/replay trajectories, not a collage of isolated attribution effects. If R works while G preserves accurate control, the paper can report a responsive internal bridge with maintained goal separation. If G also changes control or reports, describe the measured relationship and its controls. Neither outcome warrants a title claiming merged minds or self-specific impairment.
