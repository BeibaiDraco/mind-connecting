"""Check logical response maps only; this is neither model data nor a sample plan."""

from __future__ import annotations

import itertools
import json
from fractions import Fraction


def main() -> None:
    permutations = tuple(itertools.permutations(range(3)))
    names = (
        "selective_transfer",
        "donor_contract",
        "donor_destination",
        "donor_class",
        "omit_dictionary",
        "drop_recipient_contract",
        "fixed_button",
        "literal_donor_button",
    )
    outputs: dict[str, list[int]] = {name: [] for name in names}
    distortion_matches = 0
    for f, recipient, donor, buttons in itertools.product(permutations, repeat=4):
        for x_recipient, x_donor in itertools.product(range(3), repeat=2):
            values = (
                buttons[recipient[f[x_recipient]]],
                buttons[donor[f[x_recipient]]],
                buttons[donor[f[x_donor]]],
                buttons[recipient[f[x_donor]]],
                buttons[recipient[x_recipient]],
                buttons[f[x_recipient]],
                0,
                3,  # Disjoint donor action vocabulary is invalid for the recipient.
            )
            for name, value in zip(names, values, strict=True):
                outputs[name].append(value)
            distorted_class = recipient.index(donor[f[x_recipient]])
            distortion_matches += (
                buttons[recipient[distorted_class]] == values[1]
            )

    target = outputs["selective_transfer"]
    fixed_distortion_possible = 0
    for f, donor, x_recipient in itertools.product(permutations, permutations, range(3)):
        fixed_distortion_possible += any(
            all(recipient[c] == donor[f[x_recipient]] for recipient in permutations)
            for c in range(3)
        )
    result = {
        "scope": "synthetic logical worlds; no model observations",
        "worlds": len(target),
        "distinct_complete_maps": len({tuple(v) for v in outputs.values()}),
        "accuracies": {
            name: str(Fraction(sum(a == b for a, b in zip(values, target)), len(target)))
            for name, values in outputs.items()
        },
        "goal_dependent_distortion_matches": distortion_matches,
        "fixed_class_distortion_cases_matching_all_recipient_contracts": fixed_distortion_possible,
        "fixed_distortion_cases_examined": len(permutations) ** 2 * 3,
    }
    assert result["worlds"] == 11664
    assert result["distinct_complete_maps"] == 8
    assert distortion_matches == len(target)
    assert fixed_distortion_possible == 0
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
