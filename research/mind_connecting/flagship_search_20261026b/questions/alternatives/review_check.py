"""Independent exact check of the proposed six-cell rule; no model or data use."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


def main() -> None:
    worlds = ((8, 4, 2, 1), (8, 2, 4, 1))
    cues = ((0, 1, 2, 3), (1, 2), (2, 3))
    rows = [(d, c, max(c, key=lambda x: worlds[d][x]))
            for d in range(2) for c in cues]

    def utility(policy) -> Fraction:
        retained = [int(policy(d, c) == a) for d, c, a in rows if 0 in c]
        excluded = [int(policy(d, c) == a) for d, c, a in rows if 0 not in c]
        return (Fraction(sum(retained), len(retained))
                + Fraction(sum(excluded), len(excluded))) / 2

    def intended(d, c):
        return max(c, key=lambda x: worlds[d][x])

    def defective_native(d, c):
        return 3 if c == (2, 3) else intended(d, c)

    def defective_no_message(d, c):
        return 0 if 0 in c else (1 if c == (1, 2) else 3)

    groups = defaultdict(Counter)
    for d, c, a in rows:
        groups[c][a] += 1
    summary_choice = {c: max(count, key=count.get) for c, count in groups.items()}
    summary = utility(lambda d, c: summary_choice[c])
    perfect = utility(intended)
    swapped = utility(lambda d, c: intended(1 - d, c))
    bad = utility(defective_native)
    bad_swap = utility(lambda d, c: defective_native(1 - d, c))
    baseline = utility(defective_no_message)
    raw_recomputation = utility(lambda d, c: max(c, key=lambda x: worlds[d][x]))
    assert (perfect, swapped, summary) == (1, Fraction(3, 4), Fraction(7, 8))
    assert (bad, bad_swap, baseline) == (Fraction(3, 4), Fraction(1, 2), Fraction(5, 8))
    assert bad >= Fraction(65, 100)
    assert bad - bad_swap >= Fraction(1, 10) and bad - baseline >= Fraction(1, 10)
    assert all(defective_native(d, (1, 2)) == intended(d, (1, 2)) for d in range(2))
    assert all(defective_native(d, (2, 3)) != intended(d, (2, 3)) for d in range(2))
    assert raw_recomputation == perfect
    result = {
        "scope": "Exact synthetic six-cell rule; not evidence of model performance.",
        "perfect_native_U": str(perfect), "perfect_alternative_swap_U": str(swapped),
        "best_summary_rule_U_given_fixed_six_cell_support": str(summary),
        "ideal_advantage_over_that_optimal_summary_rule": str(perfect - summary),
        "bound_scope": "Conditional on the fixed abstract labeling/support; not an upper bound on the observed model-arm effect. Public generator information and private relabeling determine the implementable summary-only rule.",
        "breaking_case_native_U": str(bad), "breaking_case_swapped_U": str(bad_swap),
        "breaking_case_no_message_U": str(baseline),
        "breaking_case_passes_written_numeric_stage2_gate": True,
        "breaking_case_BC_reversals_correct": True,
        "breaking_case_CD_actions_both_wrong": True,
        "raw_evidence_recomputation_U": str(raw_recomputation),
        "implication": "Written Stage 2 gate can advance a policy worse than the summary control; the primary signature does not distinguish hypothesis transfer from evidence recomputation."
    }
    Path(__file__).with_name("review_check_output.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
