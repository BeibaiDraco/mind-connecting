"""Independent execution of repair 1's proposed conjunction; synthetic only."""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path


def gate(native, swapped, no_message, summary, bc, third, retained, valid=F(1)):
    return {
        "validity": valid >= F(9, 10),
        "native_floor": native >= F(65, 100),
        "swap_margin": native - swapped >= F(1, 10),
        "no_message_margin": native - no_message >= F(1, 10),
        "summary_positive": native > summary,
        "paired_BC": bc >= 18,
        "third_rank": third >= 18,
        "retention": retained >= 40,
    }


def main() -> None:
    intended = dict(native=F(1), swapped=F(3, 4), no_message=F(5, 8),
                    summary=F(7, 8), bc=24, third=24, retained=48)
    cases = {
        "old_breaking_case": dict(intended, native=F(3, 4), swapped=F(1, 2), third=0),
        "intended_valid_case": intended,
        "raw_evidence_recomputation": dict(intended),
        "equal_summary": dict(intended, summary=F(1)),
        "insufficient_paired_reversals": dict(intended, bc=17),
        "insufficient_third_rank": dict(intended, third=17),
        "insufficient_retention": dict(intended, retained=39),
    }
    result = {}
    for name, inputs in cases.items():
        checks = gate(**inputs)
        result[name] = {"checks": checks, "pass": all(checks.values())}
    assert not result["old_breaking_case"]["pass"]
    assert result["intended_valid_case"]["pass"]
    assert result["raw_evidence_recomputation"]["pass"]
    assert all(not result[name]["pass"] for name in cases if name not in {
        "intended_valid_case", "raw_evidence_recomputation"})
    output = {
        "scope": "Exact stipulated outcome fixtures, not model performance or threshold justification.",
        "cases": result,
        "conclusion": "Repair 1 excludes the original failure and independently enforces each added requirement. It intentionally does not identify a representation mechanism.",
    }
    Path(__file__).with_name("review_check_repair1_output.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({name: record["pass"] for name, record in result.items()}, indent=2))


if __name__ == "__main__":
    main()
