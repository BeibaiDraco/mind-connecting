# Interpretation of the Llama v4 replication

Date: 2026-10-09. Independent interpretation review; no manuscript, protocol,
parameter, or result file changed by this review.

## Overall assessment

The completed Llama experiment extends several specific attribution findings to
one additional checkpoint. It supports partner-content claiming under the fixed
memory link, a dissociation between measured access and assigned-rule claiming,
an effect of the text-source header on current-rule adoption, and a strong
dependence of assigned-rule claiming on keeping the link during readout. It does
not independently validate the access-matched memory-versus-vector comparison,
the proposed positional mechanism, or the full original paper. The positive
adjusted code-word residue after cutting the link does not replicate.

All five prespecified primary condition contrasts are positive and significant
after Holm correction. That statistical statement is not equivalent to five
validated mechanisms or to five unrestricted replication claims: the
K1-minus-STATIC interpretation was explicitly conditional on access matching and
independent validity, which failed.

## Evidence and unit of analysis

The reviewed formal run is
`20261009-005433_v4_llama31_confirm_v4_confirm`, using
`meta-llama/Llama-3.1-8B-Instruct` at the frozen revision in
[PROTOCOL_V4.md](../protocol/PROTOCOL_V4.md). K*=K1 at w=1, so the eight planned
roles produce seven unique conditions. There are 600 paired episodes, each with
two option orderings, and 84,000 successful expected readouts. The 84,000 records
are not independent observations. Report rates as episode averages over the two
orderings; comparisons are paired within episode.

The source is the final `v4_contrasts.json` in that run, together with
`v4_match.json` from `20261008-230032_v4_llama31_match_v4_match` and
`v4_validity.json` from `20261009-000001_v4_llama31_validity_v4_validity`, under
`/Volumes/VERBATIM SD/mind-connecting-data/results/`. The formal artifact reports
complete, consumable data with no invalid records or truncated tails. This review
uses those outputs for interpretation; the independent raw-ledger and statistical
audits are separate evidence of their correctness.

Qwen comparisons below come from the actual condition tables in
[confirmatory_v2_main.md](../results/v2/confirmatory_v2_main.md),
[confirmatory_v3.md](../results/v3/confirmatory_v3.md), and
[story_checks.md](../results/story_checks.md), read against the current
[paper results](../../paper/sections/results.tex) and
[discussion](../../paper/sections/account_and_discussion.tex). Qwen v2 and v3 are
different samples; their rates must not be silently interchanged. All Llama
intervals below are 95% episode-bootstrap intervals unless stated otherwise.

## Findings addressed by the replication

| Original finding | Llama evidence | Defensible interpretation |
|---|---|---|
| Reading the partner's fixed memory changes answers about one's own assigned rule. | K*−C0 on M: +10.823 [10.375, 11.253]; START partner choices 51.33% versus 0%. NOW partner choices are 51.50%, and WORD partner choices 48.75%, versus 0% for both under C0. | The core forced-choice attribution phenomenon replicates in this additional checkpoint. This is behavioral evidence in the question-answer task, not merely a logit shift. |
| At w=1, assigned-rule answers often select the partner's rule. | Qwen v3 START partner choices were 52.3% at w=1; Llama gives 51.33% at w=1. | A useful descriptive correspondence at the same nominal per-key weight. There is no prespecified cross-model equivalence test, and equal weight does not imply equal attention mass or equal effective intervention strength. |
| Content transfer follows the donor's particular assignment. | Formal rule content-counterfactual score +5.033, one-sided 95% lower bound +4.741; word +5.031, lower bound +4.803. Both checks also passed independent validity. | The access readout responds to changing donor content. These scores are computed on ACC_RULE/ACC_WORD; they are not themselves a counterfactual causal test of the ownership readout or of the positional mechanism. |
| Access and assigned-rule claiming dissociate between memory and source-tagged text. | TAG rule access is 86.58% with 0% START partner choices; K* access is 43.42% with 51.33% START partner choices. K*−TAG on M: +11.023 [10.573, 11.457]. Qwen v2 showed the same ordering (TAG 95.2% access/0% claiming; KV w2 70.1%/95.8%). | High measured access is insufficient for assigned-rule claiming, and greater measured access does not monotonically imply greater claiming across these conditions. This comparison is not access-matched and changes the content presentation as well as the channel. |
| At matched rule-access gain, memory and STATIC produce different claiming. | K1−STATIC on M: +10.451 [9.994, 10.891], with 51.33% versus 0% START partner choices. But formal access gains are 2.490 versus 0.421: the relative gap is 83.1%, exceeding the 25% criterion. Matching and independent route validation had already failed. | An estimable condition difference, not a replication of the matched-access route result. Keep this comparison in the five-test primary family, visibly labeled unmatched and route-unvalidated. |
| A text-source header reduces adoption of the partner's rule as one's current rule. | UNTAG−TAG on M_NOW: +3.725 [3.367, 4.082]; NOW partner choices 42.17% versus 2.25%, with exactly the same donor-message body. Qwen v2 rates were 42.6% versus 0.1%. | The specified header intervention replicates qualitatively. It reduces, rather than absolutely eliminates, current-rule adoption in Llama. CURRENT/NOW is a report about a rule, not a measured downstream decision. |
| Cutting the memory link before the readout largely reverses assigned-rule claiming. | K*−RF on M: +10.893 [10.455, 11.324]; START partner choices fall from 51.33% to 0%, using the same C48 state. Qwen v3 fell from 97.1% to 1.3% at its selected w2. | The dependence of assigned-rule claiming on answer-time access replicates. Different selected weights prevent treating the cross-model rates as a controlled comparison of recovery strength. |
| Some current-rule influence remains after the cut. | RF−C0 on M_NOW: +1.917 [1.631, 2.214]; NOW partner choices 7.08% versus 0%. Qwen v3 had positive M_NOW residue and 17.5% partner choices after the cut. | Qualitative replication of current-rule residue. It does not establish that explicit reflection text caused the residue. |
| Positive code-word source-score residue remains after the cut. | RF−C0 on M_WORD: −0.330 [−0.495, −0.162], Holm p=0.000106 in the separate four-test secondary family. RF WORD partner choices are 1%, versus 0% under C0 and 48.75% with the link kept. Qwen v3 had positive M_WORD residue (+10.490 [8.99, 12.03], descriptive) and 17.5% partner choices under RF. | The positive adjusted code-word residue does not replicate under the selected Llama setting. Do not convert the negative adjusted score into a claim of no remaining code-word influence. |

## Limits that materially change the wording

### Matched access and the proposed mechanism

STATIC is available, not missing: its observed comparison belongs in the primary
family. Its failure is the prespecified interpretation check. Matching selected
the closest eligible gain g=0.7, but its access gain was only 0.346 against K1's
2.800 in the matching sample, and 0.392 against 2.270 in independent validity.
The formal result does not repair this mismatch. Do not write that Llama
replicates "ownership follows the route, not access" as an access-controlled
mechanistic conclusion. The tagged-text result does support the narrower
access/claiming dissociation in this checkpoint.

The "two cards, one slot" account remains a proposed explanation. V4 did not
move the partner cache away from the receiver's positions, change card layout,
alter Robin's information, or causally edit a connected reflection. Reproducing
the effect with the same channel in another checkpoint broadens the empirical
scope; it does not identify the responsible property of that channel. Both
models still use an implementation deliberately retaining the donor's original
rotary positions.

### The contrary WORD result concerns an adjusted metric

M_WORD subtracts the Robin-question preference shift from the own-question
preference shift. Under RF versus C0, the raw own-WORD component increases by
0.3635 nats, while the WORD_R component increases by 0.6932 nats; their difference
is −0.3298. Thus a negative adjusted score coexists with a small positive raw
own-question shift and 1% partner-word answers. Report all three facts.

Neither "no residue at all" nor "source boundaries were fully preserved" follows.
Conversely, the Qwen narrative that the code word persists after the cut cannot
be presented as a result replicated across both checkpoints. Llama used w1 and
Qwen's RF comparison used w2, so this is a boundary of the tested replication
setting, not proof of an intrinsic family difference. A reflection-content
grouping, if later reported, must be explicitly exploratory and cannot establish
the causal claim that writing the word is necessary or sufficient for persistence.

### Capability and specificity

K*'s formal CAP drop is exactly 5.000 percentage points, at the inclusive
screening tolerance; CF's is 5.083 points, slightly beyond it. The independent
validity sample passed the core engineering and content checks. Do not reselect,
drop conditions, or retroactively redefine the formal sample. Report the formal
control-quality drift alongside the attribution results. A finite item bank and
a screening tolerance are not evidence of unchanged general capability.

For K*−C0, the raw START component shifts by +12.072 nats and START_R by +1.249,
giving the positive adjusted M effect. START_R and NOW_R have no partner-choice
answers under K*, but WORD_R has 1.83%. The attribution change is differential;
the categorical statement that every error is confined to ownership is too
strong for these Llama data without the full error and capability breakdown.

### Current adoption is not original assignment

UNTAG gives 42.17% NOW partner choices but 0% START partner choices in Llama.
Qwen v2 had 42.6% NOW and 14.6% START partner choices under UNTAG. The replicated
header effect is on the prespecified current-rule endpoint. Do not generalize it
to a demonstrated header effect on Llama's assigned-rule choice rate, which is
zero under both text conditions. Likewise, TAG's 0% assigned-rule claiming does
not mean all its attribution/preference readouts are unchanged.

## Original findings not tested in v4

- Open self-reports, denial of anything unusual, and U_CLOSED judgments. V4
  collected neither U_OPEN nor U_CLOSED; forced-choice answers cannot establish
  the original claim-and-denial result or absence of awareness of the intervention.
- The strict third-person/name-in-memory manipulation, its retention criterion,
  and the code-name question. A second-person wording alternative is not newly
  excluded by the Llama experiment.
- Balanced rehearsal of own and Robin information. V4 retains v1 materials; it
  does not replicate the Qwen balanced-rehearsal control.
- The Qwen claiming dose-response curve, near-ceiling w2/w3 claiming, sharp
  individual answer probabilities, and near-independence of rule/word claiming.
  Higher Llama weights were screened out on capability before formal selection;
  v4 does not supply a formal multi-weight attribution curve.
- Stranger and "your own earlier thoughts" headers. The reversal for the latter
  header remains a Qwen finding.
- Mutual reading, live feedback, swapping, excess same-rule agreement, and
  recovery of both sides after a cut. V4's fixed one-way donor memory has no
  reciprocal loop.
- The earlier residual-link dose, layer and dimension studies, and a causal test
  of whether deleting reflection content removes later residue.

These are scope exclusions, not failed replications. No result here tests human
brain bridging, consciousness, a number of subjects, or integrated information.

## Recommended wording

Suggested results paragraph, subject to the accompanying statistical audit:

> In a prespecified replication with Llama 3.1 8B Instruct and 600 new paired
> episodes, the memory link at the selected weight w=1 raised partner-rule answers
> about the receiver's original assignment from 0% to 51.3%
> (ΔM=10.82, 95% CI [10.37, 11.25]). Source-tagged text provided higher measured
> rule access (86.6% versus 43.4%) without assigned-rule claiming. Removing the
> text-source header increased current-rule adoption from 2.3% to 42.2%.
> Cutting the memory link before questioning reduced assigned-rule claiming to
> 0%, while some current-rule influence remained. The positive adjusted code-word
> residue observed in Qwen did not replicate. The static-direction control did
> not meet the prespecified access-matching criterion, so this experiment does
> not independently establish the matched-access route comparison.

Suggested discussion sentence:

> These results extend the fixed-memory attribution effect and several control
> contrasts to one additional checkpoint, while identifying limits in access
> matching and post-cut code-word persistence; the proposed positional mechanism
> and the original self-report and reciprocal-coupling findings remain untested
> in this replication.

Keep model-specific rates, effects and intervals in separate rows. Do not pool
episodes across models, divide their raw logit effects to rank susceptibility,
claim equal effect sizes from similar percentages, or describe this as a universal
property of language models. The stronger contribution is a prespecified,
fixed-N replication with no claiming-based pilot gate, together with explicit
reporting of its mismatched control and contrary secondary result.
