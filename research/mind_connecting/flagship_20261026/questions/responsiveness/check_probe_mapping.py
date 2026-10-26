"""Enumerate the proposed probe crossover; no models or project results."""

from collections import defaultdict
from itertools import product
import json
from pathlib import Path


def early_plan(button: str) -> dict[str, str]:
    """Stipulated pre-observation payload; not a native-cache audit."""
    return {"button": button, "component": {"L": "x", "R": "y"}[button]}


def timeline_check() -> int:
    checks = 0
    for cue in ("L", "R"):
        reference = early_plan(cue)
        for x, y, late_gate in product((0, 1), (0, 1), (False, True)):
            environment_only = {"x": x, "y": y, "late_gate": late_gate}
            observations: dict[str, int] = {}
            a_commitment = cue
            live = early_plan(a_commitment)
            yoked = early_plan({"L": "R", "R": "L"}[cue])
            assert not observations
            assert live == reference
            assert set(live) == set(yoked) == {"button", "component"}
            assert all(value in {"L", "R", "x", "y"}
                       for message in (live, yoked) for value in message.values())
            # Acquisition can inspect plans, never environment_only or late_gate.
            b_commitment = live["button"]
            assert a_commitment == cue
            assert b_commitment == reference["button"]
            assert not observations
            observations = {
                "A": int(environment_only[live["component"]]),
                "B": int(environment_only[{"L": "x", "R": "y"}[b_commitment]]),
            }
            assert len(observations) == 2
            checks += 1
    return checks


def main() -> None:
    timeline_cases = timeline_check()
    mappings = {"aligned": {"L": "x", "R": "y"},
                "crossed": {"L": "y", "R": "x"}}
    rows = defaultdict(list)
    for calibration, b_map in mappings.items():
        for a_button, x, y in product(("L", "R"), (0, 1), (0, 1)):
            a_component = {"L": "x", "R": "y"}[a_button]
            world = {"x": x, "y": y}
            b_choices = {
                "copy_button": a_button,
                "copy_component": next(k for k, v in b_map.items()
                                       if v == a_component),
                "coordinate_complement": next(k for k, v in b_map.items()
                                              if v != a_component),
            }
            for policy, b_button in b_choices.items():
                components = {a_component, b_map[b_button]}
                evidence = {k: world[k] for k in components}
                consistent_codes = sum(
                    all({"x": xx, "y": yy}[k] == v
                        for k, v in evidence.items())
                    for xx, yy in product((0, 1), repeat=2)
                )
                rows[(calibration, policy)].append({
                    "same_button": float(a_button == b_button),
                    "same_component": float(a_component == b_map[b_button]),
                    "information_rank_bits": float(len(components)),
                    "both_bits_acquired": float(len(components) == 2),
                    "ideal_code_accuracy_bound": 1.0 / consistent_codes,
                })
    summary = []
    for (calibration, policy), cases in sorted(rows.items()):
        item = {"calibration": calibration, "policy": policy,
                "world_action_cases": len(cases)}
        item.update({key: sum(case[key] for case in cases) / len(cases)
                     for key in cases[0]})
        summary.append(item)
        expected_rank = (2.0 if policy == "coordinate_complement" or
                         (policy == "copy_button" and calibration == "crossed")
                         else 1.0)
        assert item["information_rank_bits"] == expected_rank
        assert item["ideal_code_accuracy_bound"] == 2 ** (expected_rank - 2)
    output = {
        "scope": "Exact logical enumeration, not observed model behavior",
        "hidden_codes_per_calibration": 4,
        "a_button_cases_per_code": 2,
        "timeline_cases_checked": timeline_cases,
        "timeline_scope": "Stipulated fixed A commitment; all early live/yoked payloads precede observations; late gate hidden from acquisition",
        "imported_bit_values_before_acquisition": 0,
        "assumption": "Independent uniform bits; perfect calibrated probes; no side-channel evidence",
        "results": summary,
    }
    destination = Path(__file__).with_name("probe-mapping-check.json")
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
