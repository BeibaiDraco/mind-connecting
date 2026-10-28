# Symmetry check at equal weight (post hoc, exploratory, no GPU)

October 27, 2026, Claude Code. This settles the disagreement between Claude's dossier ("50% is forced by construction") and Codex's review ("an empirical result, not a theorem") with data. Script: `scripts/explore_symmetry_check.py`. It reads `records/attempt-*.jsonl` only and writes nothing.

## The argument, made precise

At w = 1 the joint softmax over [own keys, partner keys] equals ordinary attention over the union of the two banks (`src/mb/runtime.py:68-120`). Each side's prefill bank (card, its own greedy note, closing tokens, reflection prompt) is computed with the link off (`runtime.py:334-359`; `run.py:676-686`). So exchanging which row holds which prefill bank leaves everything after the prefill unchanged, except:

1. **C1**, the first reflection token, which is chosen from A's unlinked prefill logits (`runtime.py:335`);
2. **position offsets** from different note lengths, which shift the logical positions of everything after the notes.

Codex is right that this is not an exact theorem. It is an approximate symmetry with two identified exceptions, and it makes a testable prediction. For every ordered rule pair, claiming with (own = X, partner = Y) plus claiming with (own = Y, partner = X) should sum to 1. A home advantage pushes the sum below 1.

## Result

START, recipient A, 600 episodes per arm, answers averaged over option rotations within an episode, 95% episode bootstrap.

| Study | Arm | Mean claiming | Mean pair sum [95% CI] |
|---|---|---|---|
| Qwen V3 | KV-P w1, second person | 52.3% | **1.047** [0.985, 1.105] |
| Qwen V5 | KV-P w1 | 50.6% | **1.012** [0.950, 1.074] |
| Llama V4 | KV-P w1 | 51.3% | **1.027** [0.969, 1.083] |
| Llama V5 continuation | KV-P w1 | 47.3% | **0.947** [0.889, 1.002] |
| Qwen V3 | KV-P w1, strict third person | 47.7% | 0.955 [0.890, 1.017] |
| Qwen V3 | KV-P w2 | 97.1% | 1.942 [1.918, 1.964] |

**No detectable home advantage at equal weight in any of the four studies.** The intervals include 1, and the Llama V5 interval only just does. The strict third-person frame gives at most a small home advantage, consistent with its −3.2-nat M difference.

## What decides the answer: which rule, not whose

Per-pair rates (Qwen V3 w1). When A holds cost and B holds emissions, A answers emissions 90% of the time. When A holds emissions and B holds cost, A still answers emissions 87% of the time. In Qwen, "lowest cost" loses to every other rule 78–90% of the time regardless of owner. Emissions vs reliability and emissions vs speed are near 50/50, and reliability beats speed about two times in three (61% and 72% in the two orientations). The ordering is **model-specific**: in Llama V4, cost *beats* emissions (75% and 67%) and reliability (76% and 84%). The same orderings recur in each model's V5 replication.

So under superposition at equal weight, the receiver's answer to "which rule were you originally assigned?" is close to a function of the unordered pair of rules. Ownership contributes nothing measurable; a model-specific content preference decides. Doubling the partner weight then makes the partner's rule win almost regardless of content (pair sums near 2).

## Consequences

- **For the paper's account:** "about half" can be stated more sharply. At equal weight, owner identity has no measurable effect; the winning rule is predicted by the model's content preference. This is a post hoc descriptive result and should be labeled as such.
- **For the planned experiment:** rule identity is a large source of variance. Analyses should stratify by ordered rule pair, or include rule-strength terms. A placement effect should show up as pair sums dropping below 1 (an induced home advantage) at matched use.
- **For the earlier framing:** "zero home advantage" is now a measured description of this interface, not a discovery about the self. It is the baseline against which any added asymmetry is measured.

## Reproduction

```bash
.venv/bin/python scripts/explore_symmetry_check.py data/results/20260925-021307_v3_confirm_confirm ONE/KV-P/w1/FULL START
```

Other runs: `20261010-025849_v5_qwen_provenance_confirm_v5_qwen_provenance_confirm`, `20261009-005433_v4_llama31_confirm_v4_confirm`, `20261010-214856_v5_llama31_provenance_confirm_v5_continuation_provenance` (arm `ONE/KV-P/w1/FULL`), and V3 arms `ONE/KV-P/w1/3ps/FULL` and `ONE/KV-P/w2/FULL`.
