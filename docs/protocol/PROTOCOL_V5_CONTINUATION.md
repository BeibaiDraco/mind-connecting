# V5 continuation: two fixed Llama comparisons after capability-gate exceptions

Date: 2026-10-10. Status: **local preparation authorized; revised paid execution
not yet authorized**. The PI accepted the observed STATIC capability loss in
principle, then requested complete preparation for both recommended Llama studies
and said the budget need not remain USD 60. This document makes the proposed
combined continuation concrete. Final launch approval must ratify this package
and specify a numerical spending ceiling before any restart or paid action.
Budget flexibility is not an unlimited spending authorization.

## 1. Scope, order and preserved history

Run the fixed Llama source-conflict comparison first, then the fixed Llama
STATIC comparison. Each uses 600 fresh formal episodes. No new model, prompt,
readout, layer, gain, calibration, selection search, N80 validation sample or
mechanism experiment is added. The model remains
`meta-llama/Llama-3.1-8B-Instruct` at revision
`0e9e39f249a16976918f6564b8830bc894c89659`, with the existing verified native
tokenizer, BF16 execution and v1 materials.

[PROTOCOL_V5.md](PROTOCOL_V5.md), its algorithm freeze, original runs and their
failed gate verdicts remain unchanged. Original v5 Llama provenance and STATIC
formal comparisons remain unavailable **under that original protocol**. New
observations belong to this separately identified continuation, whose decision
to collect them follows inspection of capability/access pilot data. No formal
Qwen attribution outcome or significance was inspected to choose this package.

The existing N80 samples inform this amendment; they are not independent
validation of a tolerance chosen after seeing them. Fresh N600 data remain
independent of those development observations. Another validation sample is not
required merely to ratify the same fixed comparisons, and is not authorized here.

## 2. Exact exceptions and prerequisites

These are exceptions for named, completed runs and fixed comparisons, not a new
general capability cutoff. Do not replace five points with 6.25, 7.5, 10 or any
other universal threshold. All other original prerequisite requirements remain.

| Study | Historical prerequisite | Proposed named exception for final package ratification |
|---|---|---|
| Provenance | `20261010-002651_v5_llama31_provenance_validity_v5_llama31_provenance_validity` | Ordinary KV: 5.625 percentage points; original verdict remains fail. Conflict KV drops exactly five points and already passes. |
| STATIC | `20261010-164716_v5_llama_static_validity_v5_static_validity` | Ordinary KV: 6.25 points; donor-own CF: 5.9375 points; original verdict remains fail. Selected STATIC drops 1.875 points and already passes. |

Both validity baselines have CAP accuracy 94.6875%. Their required rule-access,
content-specificity and label-format checks passed; the original capability
failures are the scientific exceptions. The provenance baseline is
`20261010-000737_v5_llama31_provenance_base_v5_llama31_provenance_base`.
For STATIC, retain the exact calibration
`20261010-154140_calibrate_v5_static_cal` and coarse search
`20261010-154353_v5_llama_static_match_v5_static_match`. The search selected
one-indexed layer 16 (tensor index 15), raw direction, gain 0.5 without refinement.
There is no runner-up selection.

STATIC validity mean rule-access gains were 2.040513885 nats for KV and
1.562524045 nats for STATIC, with a 23.425% relative gap. The original positive-
gain, 25% point-mean match passed. Its validity checker nevertheless crashed
before writing its output because it compared CF label meanings with the
unmutated episode. Preserve that failure separately from the independent,
producer-aware metadata audit and unchanged gate recomputation, as documented
in [the terminal audit](../reviews/v5_static_terminal_audit_20261010.md).

Continuation preparation must verify exact source-run hashes, complete unique
finite records, all question and physical-candidate metadata, unchanged
calibration bytes and original gate recomputation. Never change an old gate
Boolean to authorize a new run. The new continuation receipt instead records
the original failure and the exact exception applying to it. Any additional
prerequisite discrepancy blocks launch; these exceptions do not waive missing
records, identity errors, failed access, failed format or a failed STATIC match.

## 3. Fixed fresh formal collection

Retain the two unused, originally planned material splits, seed 0. A new run tag,
continuation identity and stage freeze distinguish their amended use from an
original-v5 confirmatory run.

| Study | Split | Arms, measured recipient A | Readouts | Expected records |
|---|---|---|---:|---:|
| Provenance | `v5_llama31_provenance_confirm` | C0, KV-P w1, KV-P w1 with donor-only Robin conflict | 12 | 43,200 |
| STATIC | `v5_llama_static_confirm` | C0, KV-P w1, STATIC layer16/raw/g0.5 | 10 | 36,000 |

Each row has 600 episodes, three arms and two balanced answer orderings. Retain
the original two-episode batches, 48 reflection tokens, FULL readout and separate
cloned readout branches. Provenance keeps the eight source-qualified questions,
old START/WORD anchors and CAP0/1. STATIC keeps the ten original v4 questions.
CF is a historical STATIC validity condition, not a new formal arm.

The preparation check reproduced both split-manifest fingerprints and found no
within-split, between-split or prior-material overlap against 41 historical
configurations and the other ten v5 splits, using the original preflight's
physical-material hash. None of the 56 mirrored SD run identities used either
formal split. Content hashes are `6778957754fb0a3a` (provenance) and
`1ecf0b1bc68620fb` (STATIC), as recorded in
`configs/v5/split_manifest.json`. Recheck local and remote run inventories before
launch; an unexpected prior execution requires investigation, not silent reuse.

Collect all 600 episodes without outcome-dependent stopping, expansion or
exclusion. Capability or matching drift in formal data is reported and limits
interpretation; it does not select a replacement arm or sample. Operational
failures preserve all evidence and use only identity-preserving resume. A
completed provenance effect, including a null or contrary effect, does not
decide whether the separately approved STATIC comparison proceeds. Verified
completion/backup and the numerical budget remain operational prerequisites.

## 4. Analysis and multiplicity

All endpoint formulas, contrast directions and statistical methods remain those
of original v5. Average the two orderings within episode before paired
contrasts. Use all 600 paired episodes, two-sided paired t-tests, and 95%
percentile intervals from 10,000 episode-bootstrap draws with seed 0. Report
paired SD, raw components and actual choice/error rates with episode-based
uncertainty. The 1,200 choices per condition/readout are not 1,200 independent
samples. Missing observations are never filled with zero.

### Provenance

Keep physical candidates fixed: receiver A's own assignment a, donor B's own
assignment b, receiver-card Robin r, and conflicting donor-card Robin d. The
primary contrast is conflict KV minus ordinary KV on receiver-original Robin
RULE `z(d)-z(r)`. The three secondary contrasts remain:

1. The same Robin contrast for WORD.
2. Ordinary KV minus C0 on the difference between old START and source-qualified
   own-card SELF RULE, each scored `z(b)-z(a)`.
3. The corresponding old WORD versus qualified SELF WORD interaction.

Preserve two separate report layers. The **original v5** report retains Qwen and
the unavailable original Llama slots, with Holm families of two primary and six
secondary tests. Never replace those unavailable slots with amended observations.
The **amended Llama** report retains the same conservative family sizes: its one
primary test plus one non-estimated slot with p=1, and its three secondary tests
plus three non-estimated slots with p=1. These additional slots preserve the
original multiplicity burden; they are not new Qwen observations or imputed
effects. Label the reports separately, do not pool episodes or describe them as
one original-prespecified cross-model family, and do not choose between report
layers according to significance. Unadjusted p-values and the fixed adjustments
are both shown.

All other source contrasts, raw self and Robin scores, per-arm choice rates,
paired Robin error-rate differences, donor access, CAP and label mass remain
descriptive. Retain Qwen's already established WORD access limitation. Report
Llama word access separately rather than assuming equal access from rule success.

### STATIC

The single primary contrast remains KV minus STATIC on Robin-subtracted M.
The separate two-test Holm secondary family remains the same arm contrast on
M_NOW and M_WORD. Keep raw self/Robin components, actual choices, C0 contrasts,
access, capability and label mass descriptive. Preserve the original direction
of all contrasts. Recheck and report formal matching drift without repairing it.
Do not combine this family with the provenance family or historical Qwen STATIC.

## 5. Interpretation limits fixed before collection

The capability losses are real measured costs. Neither continuation may be
described as satisfying the original capability-preservation gate, preserving
general capability or isolating attribution from all general performance
changes. Report per-arm formal CAP and label mass alongside attribution outcomes.
A large additional formal loss further limits interpretation; do not invent a
new retrospective cutoff or remove poorly performing episodes.

The source-conflict study tests sensitivity to an added conflicting Robin entry
with explicit original-record ground truth. It does not isolate a special self
mechanism: own-content conflict is already present and rehearsal is unequal.
Positive logit movement is not automatically an increase in wrong choices.
Null movement with inadequate access cannot establish intact attribution; even
with adequate access it does not prove self specificity. The old-question
anchors expose a possible wording boundary rather than justify prompt changes.

STATIC matching concerns one mean rule-access logit gain, not all information,
word access or intervention strength. The 25% bound is not an equivalence test;
the existing paired interval extends outside its tolerance region. Unequal CAP
losses and remaining interface differences constrain any causal route claim.
Similar claiming, contrary results and formal matching drift remain informative
outcomes, not reasons to repeat selection. No consciousness, identity-fusion or
specific positional-mechanism conclusion follows.

## 6. Engineering correction, freeze and launch approval

Before formal collection, independently review the minimal CF checker repair
against the unchanged producer, including real donor-view metadata and mutation-
rejection regressions. This is a versioned validation repair, not a change to
collected tokens, model behavior, physical CF scoring or numerical gates. Keep
the old algorithm manifest and failure evidence intact. Historical source hashes
must be checked against their frozen source version; they must not be falsely
required to equal a repaired current checkout or silently overwritten.

Freeze this continuation protocol, new source/configuration identity, exact
prerequisite audits, selected STATIC calibration and complete reporting contract
before either fresh formal run. New files must preserve the original and
amended verdicts separately. Verify append-only records, exact resume identity,
backup acknowledgments and independent instance-local shutdown. Source changes
must not be introduced into an existing run through `--allow-code-change`.

The current work authorizes local preparation only. The prepared launch request
must state both fixed studies in order, the named pilot exceptions, a numerical
incremental and cumulative spending allowance, retained prior spend, a new
deadline, backup reserve and the actual quoted host rate. Estimates are about
11.5 hours nominal / 17.8 conservative for provenance and 6.9 / 13.9 for STATIC,
before additional setup/backup allowance. They are planning estimates, not
promised completion times or authorization to spend. The PI can ratify the
complete prepared package when topping up and explicitly instructing launch;
no additional experiment is authorized by that action.
