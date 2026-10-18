# V6 action failures: offline diagnosis and a bounded diagnostic proposal

Date: 2026-10-18. PI request: distinguish task, prompt, code and model limitations using saved data and local checks; propose changes and small validation, without starting a GPU.

## Finding

The clearest established failure is **unreliable application of the task's decision rule, including when all required current facts are supplied**. The saved notes repeatedly describe the wrong computation: reversing the own-device transition table, treating an assignment code as a state to reach, and confusing own with partner beacon. This is stronger evidence for a task-presentation/context problem than for a pure memory-transfer failure. It does not prove a single causal mechanism or clear the GPU implementation.

No rendered-table/scoring/option-identity error was found in the checks below. The model can follow ordinary multiple-choice questions much better than this task in the same engineering fixtures. Therefore neither “the model is generally incapable” nor “everything is a code bug” is established. Task-specific capability under the present interface is inadequate in the inspected cases.

All data here are outcome-exposed engineering fixtures, not a completed scientific baseline, calibrated result or new confirmation. The frozen protocol, selectors, gains and sample sizes are unchanged. No model execution, GPU/provider call or automation change occurred.

## 1. Correct the premise: separately readable is not jointly used

The previous walkthrough found accurate beacon reports in the one TEXT case (12/12) but poor actions (2/12). It did **not** query that TEXT trajectory's latest goal. Goal questions in other conditions run on discarded clones with different prompts. Their answers never enter the continuing action history. It is consequently too strong to say “the same action computation demonstrably knew both facts and its goal.”

There is nonetheless a more direct existing diagnostic: `task_fullinfo` explicitly supplies the receiver's latest goal and the partner's current beacon **in the action question itself**. This removes the need to retrieve either current fact for that particular answer, though the earlier generated history and public rule table remain in context.

| Saved engineering fixture | Policy | Explicit full-information action | Ordinary continuing action | Ordinary CAP questions |
|---|---|---:|---:|---:|
| Baseline materials, two episodes, gain 0 | OFF | 6/24 | 6/24 | 68/72 |
| Different calibration materials, two episodes, gain 1 | OFF | 12/24 | 11/24 | 70/72 |
| Same calibration materials | LIVE | 8/24 | 6/24 | 70/72 |

Baseline episode-level full-information counts are 6/12 and 0/12. Calibration OFF counts are 5/12 and 7/12; LIVE counts are 2/12 and 6/12. These are descriptive counts over correlated repeated questions, not independent N24 experiments. Different baseline/calibration materials cannot support a paired gain comparison. OFF receives no foreign state even where the fixture runtime gain is 1.

The baseline's original/latest assignment questions are both 24/24, but their prompts explicitly supply those assignments: these demonstrate record copying, not independent memory retention. Supplied parcel questions are 24/24. In the baseline, adding both current facts to the action question changes the chosen button in only 2/24 comparisons with the ordinary sibling question; action accuracy remains 6/24.

An additional within-parent clue comes from the second full episode's LIVE discarded-goal probes: latest-goal reports are 8/8 while transfer-action queries are 5/8. The latter provide a new explicit one-row goal-to-button mapping and the partner beacon. Three wrong applications coexist with correct goal reports on sibling clones. The problem can therefore survive removal of the two-dimensional lookup, although this is not a controlled comparison of table formats and the prompt/state differ between probes.

## 2. What the saved model histories actually show

Eight original pair archives were rehashed and read with an allowlisted, metadata-only pickle reader. It constructs inert tensor placeholders, never reads tensor storage into a model, and imports no torch. The local tokenizer was checked against its manifest. Native token histories, role boundaries and all committed action turns in those archives match regenerated prompts and raw records. The eight overlapping snapshots contain 48 verified historical action appearances, representing 20 distinct decisions through round 5, not 48 independent actions.

Examples below are model-generated notes, not faithful access to an internal reasoning mechanism.

- **Full episode 000001, A, round 1:** for G0 the public table prescribes **Down** with a Dim partner and **Left** with a Bright partner. The actual partner is Bright, so Left is correct. The current own goal is correctly named G0, but the note uses the own Dim beacon and says: “According to transition table: Dim → Right. So I choose button: Right.” The committed answer is option 3, correctly decoded by the code as Right. Right is wrong under either partner state for this goal: own-beacon substitution alone does not explain this example; the rule is also misapplied.
- **Full episode 000000, A, round 2:** the note remembers G1 but asks “So from Bright, to reach G1? Wait,” then recopies the own-device transition table. G1 is a policy-column label, not a beacon state to reach.
- **Full episode 000000, B, round 5:** the note first states G0, later says “But goal is G3,” and ends “We need to reach G3 →”. This supports inconsistent use of the latest assignment as well as wrong task interpretation; it is not a uniform, single-source failure.

The latter two quoted periods nevertheless end in correct buttons. Their notes expose task confusion but cannot be treated as a faithful causal explanation for each scored action. Conversely, round 1 of the first example is an actual wrong decision with the wrong rule explicitly stated.

- In **all ten archived round-1–5 work periods of full episode 000001**, the final 16 generated tokens are decorative checkmarks/formatting rather than explicit goal/beacon statements. The other episode's tails often contain incomplete transition-table reasoning. The 64-token work clock and 16-token incoming window make this relevant to signal quality. **A token's KV state is contextual**, so decorative decoded text does not prove absence of factual information in that state. Likewise, Unicode replacement characters from decoding a sliced token interval are not evidence of corrupted token storage.

The engine masks end-of-turn tokens during the fixed work period and closes the turn at the prescribed boundary. Sixteen preparation tokens and 64 work tokens can thus cut off a sentence or require additional continuation after a brief answer. This implements the frozen clock; it is a possible interface problem, not a newly discovered violation. We have no unmasked EOS trace establishing that this caused the wrong actions, and simply adding more tokens is not justified by these examples.

In the baseline fixture's ten full-information decisions where own and partner beacons imply different buttons, **9/10 choices match the own-beacon rule**. This descriptive signature is not universal: on the separate calibration OFF materials it is 0/6. Old-goal and literal-goal-number explanations also account for only subsets and overlap. Do not claim one substitution explains the entire dataset.

Actual TEXT conversations and neutral work notes were not archived in these fixtures. Their readout records and reconstructed question text are available; their unseen generated notes must not be invented. The LIVE decoded examples above cannot be relabeled as TEXT or OFF transcripts.

## 3. Code and data checks: what is and is not cleared

Completed locally:

- All 75 scientific source pins match the closed timing package. The two neutral material sets reproduce their original hashes and cohort order. Original record and completion hashes match; 216 baseline and 336 calibration rows pass complete world/question/native-token validation, without imputation.
- Independently parsed the **rendered public table**, question option text and transition text across all 24 action-name, 24 goal-name and 24 action-option permutations, four goals, two partner beacons and both physical sides: **221,184 action questions** and **884,736 labeled transition checks**, with no discrepancy. This is separate from merely asking the original scorer for its answer.
- The prior full-case reconstruction verified all 680 readouts. This inspection additionally matched saved initial/round/question text, numeric committed answer and actual action-driven world to the original eight pair archives. No A/B swap, stale committed option map, wrong answer-token conversion or oracle replacement was found in these records.
- Reference and cohort sources clone diagnostic questions, commit only the chosen action branch, and map native option IDs through each question's candidate order. Beacon/goal diagnostic answers are not fed into actions. The all-information question prefix is reconstructed and its hash matches the saved neutral row.
- Offline regression suite: 1,234 passed, 10 skipped, one GPU test deselected at task start. The end-of-task run is recorded in STATUS.

Limits:

- These checks establish logical/serialization consistency, not complete numerical equivalence of the optimized GPU backend. Qwen's earlier microchecks pass, but there is no same-input reference-versus-optimized comparison of these exact full-information failures. Llama's preserved numerical failure is a separate unresolved matter.
- A parser agreeing with generated rules does not show that a small model can reliably use the presentation. Conversely, poor performance does not establish that the abstract task is impossible for this model under clearer instructions.
- The full-information diagnostic sees existing generated history. It does not distinguish fresh single-turn rule lookup from contamination by earlier incorrect work notes. That distinction motivates the first short prospective check below.

## 4. Minimal proposed changes, not edits to frozen science

Keep the underlying world and causal question: both agents receive separate private inputs, their actual actions change their own signals, and the other agent must respond through the specified channel. Preserve arbitrary counterbalanced codebooks, actual-output transitions, six rounds, the early/late perturbations, cuts and Replay. Do not give partner ground truth to the real interaction conditions.

Prepare a separate prospective exploratory task version with at most two ordered prompt candidates:

**P1: distinguish the decision rule from the environmental consequence.** Preserve the existing tables and add plain instructions such as:

> An assigned goal such as G0 is a policy label, not a destination or beacon state. To choose a button, use your own latest assigned label and the OTHER participant's current beacon in the Action table. Your OWN current beacon is not the row selector. The Own-device transition table describes what happens AFTER you press the button; do not reverse it to decide which button to press.

Also make the action question explicitly name both operands: “Using A's latest assignment and B's current beacon, which button does the Action table prescribe for A?” This does not supply either hidden answer.

**P2, only the second finite candidate: P1 plus a less ambiguous table layout.** Render the same eight entries as explicit goal-conditioned rules, e.g. “G0: if partner beacon is Dim, press Down; if Bright, press Left” for full episode 000001. Values are unchanged and names remain permuted. Keep the consequence table separately labeled. Do not remove it or simplify the physical state transition.

Do not immediately add many demonstrations, rename every code, extend work time or search many gains. A structured note prompt is a separate secondary candidate only if the held-out history diagnostic implicates note corruption: ask the model to keep role/round, own beacon, latest assignment, partner estimate with uncertainty, and the two conditional buttons distinct, without decorative continuation. Such notes must be generated by the model, never populated with hidden partner truth by the controller. Changing this prompt changes the generated bridge content and needs its own prospective amendment; it is not a free engineering optimization.

The current G0/G1/etc. labels and 1–4 answer IDs should initially remain unchanged. There is no evidence of a code-level label conversion bug that would justify changing response format now.

## 5. Small, sequential validation proposal

These are proposed development checks, not an adopted new N/gate, paid dispatch or replacement for the original confirmatory protocol. Freeze the exact materials, prompts, backend checks and maximum scope before collection. Retain all attempted variants and results. No core feedback effect or significance may select a prompt or gain.

### A. Short rule-understanding and backend diagnostic

- Qwen only; **eight fresh codebooks, eight full-information cases each = 64 cases**. Within each codebook cover four assignment labels × two partner beacons. Predetermine role and own-beacon allocation across the eight codebooks so each target cell is balanced for A/B and own-beacon match/mismatch; do not take the first generated block and assume balance.
- Compare P0 (original), P1 and P2 on the identical cases. Fresh conversation, explicit current facts, unchanged four native answer IDs, one scored answer token; no bilateral work, pulse archives or full performance campaign. These short questions diagnose the rule interface, not real-time interaction.
- Run the same 64 inputs for each version through both reference and optimized backends: **384 scored answers total**. Preserve numeric records under the existing comparison contract; do not loosen tolerances because an answer looks reasonable. If the candidate comparison fails, hold that backend and report the reference diagnostic; do not start another open-ended optimization loop.
- Proposed development screen: at least **58/64 correct** on each admitted backend, with all physical/option subgroups shown. Choose the first passing clarified candidate in fixed order P1 then P2; keep P0 as the control. This is a feasibility screen over eight materials, not a confidence-bound certification. If P0 already performs well in fresh context, the old six-round history becomes the leading suspect; if P1/P2 both fail, stop before interaction work.

### B. Held-out six-round context diagnostic

- **Eight further fresh episodes**, role/early-side balance explicitly verified, using the selected fixed prompt; keep six rounds and 16/64/16 preparation/work/window. Run **OFF only**, not a gain search.
- At each side/round, keep the ordinary action as the only continuing answer. Add discarded sibling queries for (i) latest assignment, (ii) action with both current inputs explicitly supplied, and (iii) that same action with the unchanged public decision table repeated next to it. That is **96 continuing decisions plus 288 diagnostic answers** over eight episodes. The all-information snippets do not enter the actual history.
- Save the actual token history and final-window tokens. The comparison localizes history/goal-use failure: correct goal with poor explicit-input action implicates rule application/context; recovery when the public table is repeated implicates retrieval/format sensitivity. A public-table repeat is diagnostic assistance, not automatically adopted for the main study.
- Proposed screen before any interaction test: explicit-input action at least **87/96** with per-episode/role results reported. This is still a development screen, not replacement of the frozen 95% confidence-bound capability gate. If poor, stop and report the diagnosed failure; do not make the bridge stronger to hide it. Preserve any note-prompt change for a new explicitly bounded version.

### C. First small interaction feasibility step, only after A/B

- A separately approved **eight fresh paired episodes** with OFF, TEXT and LIVE, keeping both agents' private inputs and the full clock. At this point do not repeat every original branch/model.
- TEXT checks whether the clarified task can exploit a communication channel in context. LIVE tests whether partner information becomes usable through the bridge at a prospectively selected neutral-only gain. The two existing full cases do not authorize using gain 1 or choosing gains from favorable feedback effects.
- This stage is descriptive discovery and **cannot distinguish mutual response from information transfer by itself**. If it produces interpretable behavior, the next bounded core pilot must retain early/late forward cuts, return cuts and Replay, rather than infer reciprocity from better accuracy alone. No automatic C/core/formal dispatch is authorized here.

A/B are the immediate recommendation; C is a conditional next step. There is no need to run the two-model N240 package before understanding the simple action failure. No new measured ETA is claimed for the unimplemented diagnostic package.

## 6. Reproducible evidence

Private offline derivatives: `/private/tmp/mb-v6-action-diagnosis-20261018/`.

- `neutral_diagnosis.py` / `.json`: both saved neutral fixtures, exact regenerated materials/questions/worlds, descriptive error signatures.
- `decode_archives.py`, `decoded_live_histories.json`: hash-verified metadata-only read of the eight original pair archives; no torch or model.
- `audit_logic.py`, `logic_audit.json`: exhaustive rendered-table/option/transition check and actual-history cross-check; saved last-window text.
- `check_sources.py`, `source_check.json`: closed-package source bindings.

Raw evidence remains under the closed Qwen timing backup, unchanged. A separate SD derivative copy is independently rehashed; its receipt is retained with the private analysis. Exposed neutral engineering materials and both full cases remain excluded from independent validation and formal data. Original backend failures, engineering labels, protocol freezes and numerical-admission hold are retained.
