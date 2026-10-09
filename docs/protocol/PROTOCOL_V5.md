# Protocol v5: provenance and bounded STATIC supplements

2026-10-09. **IMPLEMENTED DRAFT, NOT FROZEN.** The PI approved local preparation
of the recommended minimal package and explicitly chose to leave gate thresholds
and sample sizes unfrozen. All numerical rules below are implemented planning
defaults, not approved execution parameters. Paid execution is deferred to a
later GPU launch and requires a separate spending cap. Finalize and freeze this
contract after the PI selects the parameters and before collecting new data.

## 1. Scope and immutable history

Two independent studies extend the completed Qwen and Llama experiments:

1. Source-qualified donor-Robin conflict, separately in the pinned Qwen3-4B-
   Instruct-2507 and Llama-3.1-8B-Instruct checkpoints.
2. One finite Llama STATIC calibration/selection/validation attempt, followed by
   a fresh three-arm formal comparison only if matching validates independently.

No weight training, model substitution, adaptive formal N or effect-based
advancement is permitted. Historical protocols, source freezes, records and
manuscript v1 remain intact. New implementation changes require a new source
freeze; old frozen experiments are reproducible at their recorded Git commits,
not by pretending the new implementation has the same code hash.

## 2. Common contracts

Use the registered full checkpoint revisions, verified tokenizer manifests,
native chat serialization, BF16 inference and existing v1 materials. P notes use
the original maximum length and C consumes exactly 48 reflection tokens. Each
question and ordering clones the complete saved C48 state independently. The
statistical unit is the episode; two answer orderings are averaged within it.

All new splits use the `v5_` namespace, seed 0 and disjoint stage identifiers.
The implemented planning default is fixed formal N600 per model/study. Source-study calibration of questions,
validation and formal data are disjoint. STATIC uses separate 60/40/80/600
calibration/selection/validation/formal episodes; midpoint refinements reuse the
same 40 selection episodes and exact original note token IDs. Nothing is selected
from a formal outcome. Smoke data are never consumable scientific evidence.

Preserve failed trials, incomplete runs and original shards. Retry a failed trial
once through the native runner; any remaining failure makes a stage incomplete.
No missing value is zero-filled. Formal reporting includes all fixed episodes;
no post-treatment filtering. Resume requires identical pinned identity and code.
No `--allow-code-change` is part of this protocol.

## 3. Provenance materials and questions

The three formal arms are C0, KV-P w1, and KV-P w1 with donor-only Robin conflict.
In the receiver A's original card, A owns a and Robin owns r. In donor B's card,
B always owns b; Robin owns r normally and d in the conflict variant. Apply this
to both rule and code word. All four physical candidates stay fixed across arms.
A's full external input is unchanged. The donor mutation changes only B's Robin
assignment and resulting private note/cache. Never relabel a physical candidate
as a different foil or owner in scoring after an intervention.

Eight source-qualified questions separately retrieve the own and Robin fields
from the receiver's original card and donor's original card, for rules and words.
The exact stems are versioned in `src/mb/provenance_tasks.py`. Add original START
and WORD questions as secondary anchors, and CAP0/1: 12 question types. Original
global Robin questions are omitted because the two cards may disagree.

When B is measured in the no-link baseline, the same question semantics are
relative to B: its own original Robin record is d in the conflict condition.
The receiver is not expected to know an unseen donor card in C0. Native B recall
is tested independently rather than using A's failed donor recall as a baseline
failure. Original self/Robin rehearsal remains unequal; no self-specificity claim
is supported by this three-arm design.

## 4. Provenance ordered stages and gates

Run stages separately for each checkpoint; never pool their scores.

| Stage | Episodes and arms | Allowed use |
|---|---|---|
| Technical smoke | 4, C0/C0-conflict/KV/KV-conflict, A and B, all12 questions | Engineering completeness, identity, branches, resume and timing only |
| Baseline | 60, C0 and C0-conflict, A and B | Four own-card qualified questions, old START/WORD, CAP0/1 |
| Independent validity | 80, C0/KV/KV-conflict, A | Four donor-card access questions and CAP0/1 only |
| Formal | 600, C0/KV/KV-conflict, A, all12 | Prespecified primary/secondary results and diagnostics |

Baseline requires each of the six task questions to have at least 90% correct
answers on each side in each arm; mean CAP and mean label mass must each be at
least 90%. No prompt search is authorized. Failure stops that model's source
study and preserves evidence for PI review.

Validity requires C0 CAP at least 90%; for both KV arms, CAP drop at most five
percentage points, total label mass at least 90%, and label-mass drop at most
five points against the same-split C0. Require two positive one-sided 95%
episode-bootstrap lower bounds for rules:

* Donor-own access: `[z(b)-z(d)]` on the donor-own question in ordinary KV minus
  C0. In these two arms d remains unused; do not extend that interpretation to
  the conflicting donor card.
* Donor-Robin content specificity: `[z(d)-z(r)]` on the donor-Robin question in
  conflict KV minus ordinary KV, with fixed physical d and r.

Word analogues are reported separately. If rule gates pass but word access does
not, continue the rule experiment and label word conclusions access-limited.
No receiver-original attribution question, old START/WORD response, effect sign
or significance is used for validity or parameter selection.

## 5. Provenance analysis

The primary contrast is conflict KV minus ordinary KV on receiver-original
Robin RULE `z(d)-z(r)`. One contrast per checkpoint makes a fixed Holm family
of two two-sided paired t-tests. Report 95% intervals from 10,000 episode
bootstrap draws, paired SD, error rates, and the raw condition components.

The separate secondary family contains six tests, three per checkpoint:

1. The same Robin contrast for WORD.
2. The source-qualification interaction for self RULE: ordinary KV minus C0 on
   `(old START z(b)-z(a)) - (qualified own-card self RULE z(b)-z(a))`.
3. The corresponding WORD interaction.

Other self contrasts, all choice rates, donor access, label mass and CAP are
descriptive. A positive logit contrast is preference movement; increased wrong
choices require actual error-rate evidence. Null Robin movement with poor access
does not imply an intact boundary. Null movement with adequate access does not
establish special-self processing under unequal rehearsal.

If a checkpoint fails a prespecified gate, keep the family sizes two and six;
use p=1 only for multiple-testing bookkeeping and mark its comparisons unavailable.
Never impute an observation or effect. No post hoc pooling or smaller family.

## 6. Bounded Llama STATIC

Keep KV-P w1 fixed and retain the raw, rule-conditional static direction. Calibrate
60 fresh episodes simultaneously at one-indexed layers 16,21,27 (tensor indices
15,20,26). Any layer missing a required raw rule direction is unavailable as a
whole; do not select favorable rules. On 40 other episodes, run C0, KV-P w1 and
the available layers at gains 0.1,0.3,0.5,0.7,1.0. Read only ACC_RULE, ACC_WORD,
CAP0/1 under the two episode orderings.

Eligible STATIC requires the same CAP/mass screens as above. Both KV and STATIC
access increments over C0 must be finite and positive. Match iff
`abs(G_STATIC-G_KV)/G_KV <= 0.25`. This is a point-mean operational match, not an
equivalence proof. A nonpositive/nonfinite KV target ends selection.

If no match exists, test at most two additional midpoint gains total, using the
same40 episodes and note tokens. An eligible bracket consists of adjacent tested
same-layer gains, both quality-eligible, that straddle the target.
Both endpoint access gains must also be finite and positive. Choose the
lexicographically smallest `(max endpoint relative gap, interval width,
abs(layer-21), layer, lower gain, upper gain)`; evaluate its midpoint. An
ineligible midpoint breaks the bracket. Recompute after each test. Stop at a
match, no eligible bracket, or two midpoint evaluations. No extrapolation, gain
above1, new layer, duplicate evaluation or new selection split.

Choose the eligible matching candidate nearest the target; ties prefer lower
gain, then nearer layer21, then lower layer. Freeze once before validation.
No match ends this branch. There is no runner-up after independent failure.

Validate on80 fresh episodes with C0, KV, selected STATIC and existing donor-own
CF. Require all four conditions complete; C0 CAP>=90%; KV/STATIC/CF quality
screens; finite positive KV/STATIC access increments; one-sided95% episode-
bootstrap lower bound>0 for KV rule access and rule content specificity; and
the same25% matching criterion. Word specificity is diagnostic. New CF quality
checking is prospective and does not change the historical v4 gate verdict.

If validation passes, freeze and collect600 new episodes in C0/KV/STATIC using
the ten original v4 question types. Primary: KV minus STATIC on M (two-sided
paired test, bootstrap95% CI). Separate secondary Holm family: same contrast on
M_NOW and M_WORD. Raw components, choices, C0 contrasts, access and quality are
descriptive. Report formal matching drift; do not repair it or remove episodes.
Rule matching does not establish matched word transmission. Similar claiming
under matched STATIC changes the interpretation and is not a failed experiment.

## 7. Precision, freeze and deployment

N600 gives a nominal mean95% CI half-width near0.080 times paired SD. Normal-
approximation80% power corresponds to a standardized paired effect about0.126
for the two-test family at its most stringent threshold, and0.142 for the six-
test family. These are planning calculations, not known raw-logit precision or
guaranteed power. Worst-case nominal binary paired-difference half-width is
about8 percentage points; modest role differences may remain unresolved.

Freeze algorithms, stems, grids, splits, metrics and complete analysis families
before first new-model execution. Later STATIC selected settings and each formal
config receive separate immutable stage manifests incorporating prerequisites.
Use raw-ledger reproduction, not a hand-edited gate Boolean, for continuation.

Local tests do not establish real-GPU correctness or model suitability. On the
GPU first verify assets/environment, run native runtime acceptance and the new
four-episode smoke/resume audit, then independent scientific gates. Record actual
throughput and project all remaining stages before formal collection. Require a
new approved cumulative budget and instance-local deadline shutdown independent
of the Mac connection, append-only backup and verified provider stop. No rental,
restart, download or scientific model execution is authorized by local preparation.
