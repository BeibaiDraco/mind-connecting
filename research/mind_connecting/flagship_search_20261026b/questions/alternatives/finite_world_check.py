"""Exact synthetic information check; no model, empirical outcomes or dependencies."""
from __future__ import annotations

import itertools
import json
import math
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


def main() -> None:
    labels = range(4)
    cues = [tuple(c) for n in (2, 3, 4) for c in itertools.combinations(labels, n)]
    rows = []
    summary_groups = defaultdict(Counter)
    for masses in itertools.permutations((8, 4, 2, 1)):
        winner = masses.index(8)
        runner_up = masses.index(4)
        for cue in cues:
            correct = max(cue, key=lambda k: masses[k])
            row = {
                "masses": masses, "winner": winner, "cue_survivors": cue,
                "correct": correct, "correct_prior_rank": sorted(masses, reverse=True).index(masses[correct]) + 1,
                "winner_retained": winner in cue,
                "always_winner_correct": correct == winner,
                "always_runner_up_correct": correct == runner_up,
            }
            rows.append(row)
            summary_groups[(winner, cue)][correct] += 1
    total = len(rows)
    changing = [r for r in rows if not r["winner_retained"]]
    bound = sum(max(c.values()) for c in summary_groups.values())
    ambiguous = [c for c in summary_groups.values() if len(c) > 1]
    output = {
        "scope": "Stipulated task distribution, not model confidence or model behavior.",
        "construction": "Uniform prior over 15 surviving micro-worlds, with hypothesis counts a permutation of [8,4,2,1]; late truthful clue reveals membership in a surviving set of size 2,3,4. Decisions maximize conditional probability; all cue branches equally weighted by design, not sampled in natural frequency.",
        "donor_worlds": 24, "cues_per_world": len(cues), "decision_cells": total,
        "common_max_probability": "8/15", "common_entropy_bits": -sum((v/15) * math.log2(v/15) for v in (8,4,2,1)),
        "correct_rank_counts": dict(sorted(Counter(r["correct_prior_rank"] for r in rows).items())),
        "winner_retained_cells": total-len(changing), "winner_excluded_cells": len(changing),
        "summary_indistinguishability_groups": len(summary_groups), "ambiguous_groups": len(ambiguous),
        "best_winner_maxprob_entropy_and_cue_policy_accuracy": str(Fraction(bound,total)),
        "same_summary_policy_on_winner_excluded_accuracy": str(Fraction(bound-(total-len(changing)),len(changing))),
        "always_winner_accuracy": str(Fraction(sum(r["always_winner_correct"] for r in rows), total)),
        "always_runner_up_accuracy": str(Fraction(sum(r["always_runner_up_correct"] for r in rows), total)),
        "full_distribution_or_raw_evidence_oracle_accuracy": "1",
        "counterexample_same_visible_summary": [r for r in rows if r["masses"] in [(8,4,2,1),(8,2,4,1)] and r["cue_survivors"] == (1,2)],
    }
    assert total == 264 and len(changing) == 96 and bound == 212
    assert Counter(r["correct_prior_rank"] for r in rows) == {1:168,2:72,3:24}
    assert len(ambiguous) == 16
    target = Path(__file__).with_name("finite_world_output.json")
    target.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k:v for k,v in output.items() if k not in ("rows", "counterexample_same_visible_summary")}, indent=2))


if __name__ == "__main__":
    main()
