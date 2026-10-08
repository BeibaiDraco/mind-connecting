# Protocol v4: cross-family replication of memory attribution and transfer route

Date: 2026-10-08. **Approved by the PI; implementation and verified assets pending freeze.**
The PI approved this complete design and budget in the task conversation on October 8.
No second-model experiment has run. This approved plan supersedes the preliminary
five-condition scope in `SECOND_MODEL_NAACL_PLAN.md` and the proposal in
`PROTOCOL_V4_DRAFT.md`. Frozen v1-v3 and their results are unchanged.

## 1. Decision and scope

The PI has authorized adding a second model and targeting NAACL 2027. Recommend
one cross-family replication of the existing task, covering attribution under a
fixed partner-memory link, an access-matched static direction, source-labeled
text, and cutting the memory link at readout. Do not rerun the entire v1-v3 program.

The PI approved these choices before any new-model pilot:

1. `meta-llama/Llama-3.1-8B-Instruct`, subject to official access and a pinned full
   revision. If access is unavailable before any outcome is inspected, a model
   change requires a new PI decision and protocol amendment. Mistral 7B Instruct
   v0.3 remains an unapproved alternative, not an automatic fallback.
2. The eight-condition design, new strength rule and fixed N=600 below, including
   removal of the old claiming-based signal gate and the new per-side baseline
   CAP >=0.90 gate.
3. A USD 60 total experiment ceiling, with at most USD 10 for correctness,
   suitability and throughput assessment before checking the remaining run
   against its measured cost estimate. Once the PI approves this plan and cap,
   stages that pass their gates and fit the remaining budget need no repeated
   spending confirmation. These are approved spending ceilings, not promised completion costs.
   Include setup, pilot and formal compute in the budget accounting; record any
   bandwidth charges available from the provider separately and count them toward
   the ceiling.

The official public model metadata identifies full revision
`0e9e39f249a16976918f6564b8830bc894c89659`. Gated asset access is still pending.
The model/config/tokenizer/generation-config hashes and native serialization checks
must be filled in from verified official assets before execution. Both A and B are independent
states of this same new checkpoint. No weight or interface training, mixed-model
  connection, or inference quantization is proposed.

## 2. Fixed task and statistical unit

- Retain v1 semantic materials, questions, option labels, counterbalancing and
  scoring. Use new named splits with seed 0; check stage identifiers and generated
  episode fingerprints for overlap before running. All calibration, pilot and
  formal episodes are disjoint; no old Qwen episode is reused as a new trial.
- Keep the private-note cap at 48 tokens and the reflection length at 48 tokens.
  Validate the new model's complete end-token set and the original fixed-length
  reflection/EOS handling. Token length is an experimental choice; do not silently
  increase it for a model that answers differently.
- Use the existing two balanced option orderings per episode. Four options do not
  mean four permutations. No extra four-permutation subset is in this plan.
- Formal readouts: `START`, `START_R`, `NOW`, `NOW_R`, `WORD`, `WORD_R`,
  `ACC_RULE`, `ACC_WORD`, `CAP0`, `CAP1`. No U_OPEN/U_CLOSED or manual open-report
  analysis is included; do not claim to replicate the self-report result.
- Baseline measures both A and B with these ten readouts. Strength, matching,
  validity and formal measurements use receiver A only. Calibration uses both
  sides' C0 trajectories. Strength, matching and validity use only
  `ACC_RULE`, `ACC_WORD`, `CAP0`, `CAP1`.
- Compute scores within each ordering, average within episode, then compare
  conditions within episode. Tokens, questions, orderings, A/B and branches are
  not independent observations. The formal sample contains 600 paired episodes,
  not 96,000 independent samples.

## 3. Formal conditions

| ID | Exact intervention | Role |
|---|---|---|
| C0 | No bridge or text message | Baseline |
| K1 | ONE / KV-P / w=1 / FULL | Fixed equal per-key weighting; target for STATIC matching |
| K* | ONE / KV-P / selected w* / FULL | Strong eligible content-transfer interface |
| RF | K* reflection state, bridge off before consuming the readout suffix | Link-cut contrast |
| CF | Same K* interface; only B's rule and code word replaced by the existing unused/distractor values | Content counterfactual |
| STATIC | Rule-conditional mean direction from independent new-model calibration, layer 21, raw, selected gain | Access-matched route comparison against K1 |
| TAG | Existing LANG_TAG header around B's same-episode C0 reflection | Explicit text-source attribution |
| UNTAG | Identical message body, existing LANG_UNTAG header | Source-header intervention |

If w*=1, K1 and K* are identical and are executed once, then referenced by both
analysis roles. This yields seven unique conditions and does not duplicate data.
RF must fork the same C48 state as K*, rather than generating a different
reflection. TAG and UNTAG must reuse the exact same saved donor text.

KV-P reads only B's fixed prefill memory, including private prompt, note and
reflection prompt, through all decoder layers. Keep the existing joint-softmax
mixture, original-position RoPE keys, valid-key mask and no-writing-during-prefill
contract. At w=1 the per-key weights are equal; this does not imply 50% partner
attention, because the content and number of keys matter.

For CF, A's external input, Robin, scenario, questions and option orders remain
unchanged; rebuild only B's private state. A's later generated reflection can
change as a consequence of the intervention. Counterfactual candidates remain
fixed physical rule/word identities in scoring.

STATIC uses a fresh 60-episode calibration with the existing rule-conditional
mean-message and RMS-normalization construction. No Qwen calibration is reused.
The layer is fixed by relative depth: round(24 * 32 / 36)=21. The project uses
**one-indexed layer numbers**; config `layer: 21` means `layers[20]`. Do not search
other layers or EMA forms. If a required rule direction has
RMS < 0.01 * sigma_in, it is unavailable; do not silently exclude episodes with
that rule. Stop that comparison branch and report the missing direction.

## 4. Ordered stages and data visibility

| Stage | Split suffix | Episodes and conditions | Visible outputs and next step |
|---|---|---|---|
| Offline and GPU correctness | `smoke` | 4 end-to-end episodes plus contract tests | Technical outputs; smoke is not consumable research data |
| Baseline | `base` | 60, C0 | Own/Robin task suitability, CAP and format |
| STATIC calibration | `cal` | 60, C0 trajectories | Normalization and rule-conditional directions only |
| KV strength | `strength` | 40, C0 plus w={0.3,0.5,1,2,3} | ACC/CAP/format only; select w* once |
| STATIC matching | `match` | 40, C0, K1 and 16 gains below | ACC/CAP/format only; select gain once |
| Independent validity | `validity` | 80, available formal arms, plus CF at w1 when distinct | ACC/CAP/format and content-counterfactual checks; no M or U outputs |
| Formal | `confirm` | **600**, available prespecified arms | Full ten-question readouts; analyze after completeness audit |

All split names have a model-specific `v4_llama31_` prefix once the model is
approved. A different approved checkpoint uses its own prefix and manifests.

The four-episode smoke checks may mechanically compute the full readout format,
but their reporting must expose only correctness, record counts and finite
values, not attribution summaries for tuning. Baseline necessarily checks the
six own/Robin task accuracies; do not use them to select a bridge or a claiming
effect. Freeze the approved algorithm before any new-model pilot, then write the
selected numerical settings and freeze the formal configuration before validity
and formal data collection. No formal outcomes are used to change this plan.

### Baseline

Require each of START/NOW/WORD and their Robin counterparts to have at least
90% argmax accuracy separately on A and B, and mean label mass at least 0.90 on
each side. Retain the 18-question CAP bank and report C0 CAP; require mean
`CAP_ACC` >=0.90 separately on A and B (average CAP0/CAP1 and option orderings
within episode, then average episodes). This new suitability gate prevents a
poor baseline from making a small CAP drop look reassuring. No prompt rewrite
or item deletion is pre-authorized in this draft.
Failure stops the proposed protocol and is reported to the PI.

### KV selection: one grid, no outcome-driven search

Engineering eligibility, relative to same-stage C0: CAP drop <=0.05, total label
mass >=0.90, label-mass drop <=0.05. These are screening criteria, not proof of
equivalent capability.

For the strong K* arm require ACC_RULE hit rate >=0.30, an increase of at least
0.10 over C0, and positive mean ACC_RULE logit gain. Among points satisfying both
sets of criteria, choose the largest mean ACC_RULE logit gain, breaking exact ties
toward smaller w. Report ACC_WORD separately. If none passes, stop this protocol's
formal experiment and report all pilots; a separate LANG/STATIC-only study needs
a new PI decision. Do not expand the grid, change prompt, switch model, or change
KV scope within this protocol.

This deliberately replaces v2's absolute 5-nat criterion with a hit-rate plus
positive-gain criterion. It requires PI approval. Within-model logit differences
remain valid ranking/readout quantities; they are not assumed to have the same
scale across models.

### STATIC matching to the fixed K1 arm

Use the finite union of the existing v2/v3 STATIC grids:

`{0.005, 0.01, 0.015, 0.02, 0.03, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0}`.

Among engineering-eligible gains, minimize the absolute difference from K1's
mean ACC_RULE logit gain over C0; break exact ties toward the smaller gain. Match
on logit access gain, not on answer hit rate. Freeze the nearest eligible point.
Mark it matched only if the target gain is positive and the difference is at most
25% of that target. Otherwise keep the nearest eligible point and report it as
unmatched. If no eligible STATIC point exists, mark that branch unavailable; do
not spend formal compute on an ineligible substitute.

Do not apply K*'s strong-interface threshold to K1. K1 may carry useful content
below a 30% hit rate. Its separate validation requires engineering eligibility,
a positive one-sided 95% lower bound for ACC_RULE gain over C0, and the rule
content-counterfactual validity check at w1. The extra CF-w1 arm in validity is
access-only and is not an additional formal attribution hypothesis.

### Independent validity and stopping

For fixed candidates r0 (original donor content) and r1 (replacement), compute
per episode:

`C_content = [z(r1)-z(r0)]_CF - [z(r1)-z(r0)]_original`.

For K*, require the one-sided 95% bootstrap lower bound of rule `C_content` to exceed zero,
and engineering eligibility to hold on this independent sample. Report the word
check separately; failure prevents interpreting a WORD null as intact source
boundaries. Failure of the K* rule/engineering validity stops this core formal
replication; all pilot results remain reportable.

For the matched-route interpretation, recheck K1/STATIC engineering eligibility,
K1 access/content validity, positive gains and the <=25% matching gap. If this
interpretation check fails but K* is valid, continue the core experiment using
the frozen available arms, label the route comparison unvalidated/unmatched, and
do not reselect gain or target. If STATIC failed selection altogether, its
primary test remains a prespecified unavailable comparison.

Record TAG and UNTAG access and engineering checks, and RF CAP/format checks.
Control-quality failures limit the corresponding interpretation; do not reselect
parameters or drop conditions based on M. A KV-TAG difference does not eliminate
access-strength differences even if both transfer content. Only the independently
validated, matched K1-STATIC comparison carries the matched-access route claim.
No null claiming result is a stop criterion.

## 5. Fixed sample size and prespecified analysis

Set formal N=600 before pilots; do not use a claiming-based signal gate, interim
significance or attribution variance to decide whether to run or continue. This
is an explicit change from the exploratory resource-allocation rule in v2/v3.
600 retains the previous formal maximum; it is not a universal power guarantee.
Report uncertainty, and do not equate nonsignificance with equivalence.

Primary family: five two-sided paired t-tests, Holm familywise alpha=0.05, with
10,000-draw episode-bootstrap 95% intervals. Expected signs are positive but tests
remain two-sided:

| Contrast | Metric | Interpretation |
|---|---|---|
| K* - C0 | M | Assigned-rule source attribution |
| K1 - STATIC | M | Matched-route effect, conditional on matching/validity |
| K* - TAG | M | Internal-memory versus explicit-source text; report access differences |
| K* - RF | M | Assigned-rule attribution when the link is kept versus cut |
| UNTAG - TAG | M_NOW | Effect of the text source header on current-rule adoption |

Do not shrink the five-test family if a branch is unavailable: for multiplicity
bookkeeping treat an unestimable primary comparison as p=1, clearly label it
unavailable, and do not impute any observations or effect estimates. Each
hypothesis is reported separately; there is no all-or-nothing replication label.

Secondary family: K*-C0 on M_NOW and M_WORD, RF-C0 on M_NOW and M_WORD; four
two-sided paired tests with separate Holm correction and episode intervals.
Other comparisons are descriptive. Retain original score definitions, including
the Robin subtraction in M; show both raw components, actual claiming choice
rates, access, CAP and label mass. A logit shift without increased claiming
choices is described as a preference shift, not a behavioral takeover rate.

Report the K* content-counterfactual scores again on the formal sample; distinct
CF-w1 is validated only in the 80-episode validity stage and is not rerun formally.
Recheck actual
formal access differences and matching status without reselecting parameters.
Do not filter episodes by reflection content, successful claiming, CAP or effect
direction. Keep failed attempts; use the original one-retry rule, report missing
paired counts, and never fill missing observations with zero. Incomplete runs
must not be represented as completed confirmatory results.

Display Qwen and the new model separately; do not pool their episodes as a larger
cross-model sample or compare raw logit magnitudes as a calibrated common scale.
The permitted conclusion is replication or a boundary of specific effects in
one additional checkpoint, not a general law for LLMs.

## 6. Implementation and acceptance sequence

1. Pin official checkpoint and tokenizer assets; record license/access status,
   hidden size/layers, stop tokens and any explicit template date. Keep original
   Qwen assets separate. Use BF16 weights, greedy decoding and FP32 readout logits;
   record all software versions, retaining Transformers 4.57.1 and tokenizers
   0.22.1 unless a separately justified change is approved. Local work remains
   torch-free.
2. Add an explicit model profile through loading, chat serialization, task
   tokenization, calibration, condition identities, resume and report tooling.
   Retain byte-compatible Qwen behavior and all existing offline tests.
3. Check full versus incremental template tokenization, one BOS, complete end
   tokens, prefix stability, single-token labels at actual response positions,
   paired question lengths, and CF receiver-input invariance. Freeze any approved
   departure from a native template. In particular, Mistral requires a separate
   policy for system text and consecutive user messages.
4. On GPU, reuse and parameterize existing tests for no-link/zero-weight equality,
   causal masks, donor isolation, snapshot/branch isolation, FULL/RF and every
   attention layer. Validate left padding, position IDs and prefill boundaries.
   Current `run_arm_chunk` recomputes C48 separately for FULL/RF. Implement reuse
   of an immutable C48 snapshot, or verify exact equality of every snapshot field
   after deterministic recomputation before allowing the readout contrast.
5. Run the four-episode smoke with conservative batches. Check expected ledger
   counts, finite logits, peak VRAM and per-condition elapsed time. Verify that
   completed-run resume adds no records, and changed model/template identity
   refuses resume before writing. Do not use old batch sizes without measuring.
6. Implement the v4 selector's exact order: screen all engineering and strong
   access criteria first, then maximize gain. The current selector chooses an
   engineering-eligible winner before its strong check and lacks the >=0.10
   hit-rate improvement rule; changing YAML thresholds is insufficient. Add
   focused tests for eligibility order, strict positive gain and deterministic ties.
   Implement the baseline's side-specific task, format and CAP gates: current
   `post_g1` pools A/B task accuracy and does not gate CAP, so its existing pass
   flag is not sufficient for this draft.
   Also handle unavailable primary comparisons explicitly: retain a null effect
   with `p_for_adjustment=1`, and verify five-test Holm correction. The existing
   missing-arm path raises `KeyError`, and passing NaN to the current Holm helper
   would incorrectly reduce the planned family.
7. Extend the freeze tool, which currently accepts only v1-v3, to include v4
   protocol, model assets, generators, profiles and configs. Prepare a run chain
   that stops on errors, syncs records, and is supervised by an actual provider
   shutdown action; the existing `run_chain.sh` does not itself stop Vast.
8. Run the stage sequence above only after PI approval. Use a new remote checkout
   such as `/workspace/mind-connecting-v4`; do not sync into old frozen checkouts.
   Confirm the SD-card mount before syncing, and preserve every failed attempt.

## 7. Workload, budget and schedule

Eight unique arms * 600 episodes * 10 questions * two orderings = **96,000 formal
readouts**. If K*=K1, seven arms give 84,000. Pilots and calibration are additional.
These counts exclude model-token generation costs and are not independent N.

The old Qwen v3 confirmatory run produced 92,400 readouts in 3h23m24s on the H100.
96,000 at that same aggregate throughput would be about 3.52 hours, but arm mix,
8B model size, tokenization and memory use differ. Use per-arm new-model smoke
measurements to estimate each full stage, including note/reflection generation,
calibration, retries, downloads and setup. Do not promise the Qwen runtime for Llama.

The PI rented a replacement A100 SXM4 80GB. Provider inspection on October 8
reported approximately USD 1.3284/hour, plus applicable bandwidth charges. A clean
200 GB disk and Python 3.12 were verified. Recheck rate and state at each start. If the projected
remaining cost exceeds the approved ceiling, stop before formal data collection
and ask the PI to revise scope or defer; never decide from partial formal M.

Parallelize offline adaptation with bounded GPU environment preparation. Do not
leave the instance running solely to wait for external access approval. Environment
acceptance does not establish that the new-model bridge works. After paid stages finish or fail, verify provider state
is stopped, rather than assuming an exited shell stopped GPU compute charges.
Retained storage may continue to incur its separate provider charges.

Target order: October 8 protocol/model/access decision and offline adapter;
October 9 correctness, suitability and frozen settings; October 10 formal run;
October 11 audit and writing; October 12 final anonymous ARR submission. This is
a conditional work schedule, not a completion promise. The eight-page ACL-format
paper, OpenReview/ORCID and review-service arrangements run in parallel. The
current arXiv first version remains unchanged.

Third-person memory, reciprocal live loops, extra layers, extensive dose curves
and open-report coding are outside this first replication. Adding them requires
a recorded decision before looking at the corresponding attribution outcomes.
