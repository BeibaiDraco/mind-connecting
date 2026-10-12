"""Task algebra and synthetic rivals for an unfrozen design, without any model."""

from __future__ import annotations

import json
import math
from collections import Counter
from copy import deepcopy
from itertools import permutations, product
from statistics import NormalDist
from typing import Any


def action(goal: int, partner_beacon: int) -> int:
    return goal ^ (2 * partner_beacon)


def transition(own_beacon: int, own_action: int | None) -> int:
    return own_beacon if own_action is None else (0, 1, 1, 0)[own_action]


def specificity(answer: int | None, old: int, new: int) -> float:
    if answer is None or answer == old:
        return 0.0
    return 1.0 if answer == new else -0.5


def signed(answer: int | None, old: int, new: int) -> int:
    return int(answer == new) - int(answer == old)


def controller_message(world: dict[str, Any], side: int, round_id: int) -> str:
    return json.dumps({"round": round_id, "own_beacon": world["beacons"][side],
                       "own_update": world["updates"][side]}, sort_keys=True)


def two_rounds(beacons: tuple[int, int], goals: tuple[int, int], pulse: int,
               arm: str, replay: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    # I is side 0 here. Role mirroring is an independent material assignment.
    states = [beacons[0] ^ pulse, beacons[1]]
    rows = []
    for t in range(2):
        read_i, read_j = states[1], states[0]
        if arm == "Fcut":
            read_j = 0
        if arm == "Rcut":
            read_i = 0
        if arm == "Replay":
            assert replay is not None
            read_i = replay[t]["beacons"][1]
        # A fresh one-pass beacon exchange has the same oracle information.
        outputs = [action(goals[0], read_i), action(goals[1], read_j)]
        actual_correct = [outputs[k] == action(goals[k], states[1-k]) for k in range(2)]
        rows.append({"beacons": states[:], "actions": outputs, "actual_correct": actual_correct})
        states = [transition(states[k], outputs[k]) for k in range(2)]
    return rows


def check_pulse_paths() -> dict[str, Any]:
    cases = 0
    contrasts = {key: [] for key in ("forward", "return", "replay", "Q_chain")}
    stale_second_world = 0
    for beacons, goals in product(product(range(2), repeat=2), permutations(range(4), 2)):
        ref = two_rounds(beacons, goals, 0, "LIVE")
        changed = two_rounds(beacons, goals, 1, "LIVE")
        assert two_rounds(beacons, goals, 0, "Replay", ref) == ref
        assert two_rounds(beacons, goals, 1, "FRESH") == changed
        candidates = ((ref[0]["actions"][1], changed[0]["actions"][1]),
                      (ref[1]["actions"][0], changed[1]["actions"][0]))
        assert all(a0 != a1 for a0, a1 in candidates)
        deltas = {}
        for arm in ("LIVE", "Fcut", "Rcut", "Replay"):
            pair = [two_rounds(beacons, goals, q, arm, ref) for q in (0, 1)]
            deltas[arm] = [
                (signed(pair[1][t]["actions"][side], *candidates[j])
                 - signed(pair[0][t]["actions"][side], *candidates[j])) / 2
                for j, (t, side) in enumerate(((0, 1), (1, 0)))
            ]
            if arm == "Replay":
                stale_second_world += int(pair[1][1]["beacons"][1] != ref[1]["beacons"][1])
                # This simple oracle in q1 reads the old beacon and is wrong.
                assert pair[1][1]["actual_correct"][0] is False
        contrasts["forward"].append(deltas["LIVE"][0] - deltas["Fcut"][0])
        contrasts["return"].append(deltas["LIVE"][1] - deltas["Rcut"][1])
        contrasts["replay"].append(deltas["LIVE"][1] - deltas["Replay"][1])
        contrasts["Q_chain"].append(min(specificity(changed[t]["actions"][side], *candidates[j])
            for j, (t, side) in enumerate(((0, 1), (1, 0)))))
        cases += 1
    assert cases == 48 and stale_second_world == 48
    assert all(set(values) == {1.0} for values in contrasts.values())
    return {"initial_world_and_goal_cases": cases,
            "responsive_oracle_scores": {k: sum(v)/len(v) for k, v in contrasts.items()},
            "FRESH_oracle_equals_LIVE": True,
            "changed_replay_second_round_world_mismatches": stale_second_world}


def rollout(beacons: tuple[int, int], goals: tuple[int, int], early_i: int,
            new_early_j_goal: int, new_late_j_goal: int, policy: str) -> list[dict[str, Any]]:
    states, current_goals, rows = list(beacons), list(goals), []
    for r in range(1, 7):
        if r in (2, 5):
            focal = early_i if r == 2 else 1-early_i
            states[focal] ^= 1
            current_goals[1-focal] = new_early_j_goal if r == 2 else new_late_j_goal
        readings = states[::-1]
        if policy == "OFF":
            readings = [0, 0]
        if policy == "AtoB":
            readings[0] = 0
        if policy == "BtoA":
            readings[1] = 0
        outputs = [action(current_goals[k], readings[k]) for k in range(2)]
        rows.append({"beacons": states[:], "goals": current_goals[:], "actions": outputs,
                     "correct": [outputs[k] == action(current_goals[k], states[1-k]) for k in range(2)]})
        states = [transition(states[k], outputs[k]) for k in range(2)]
    return rows


def check_continuity_and_privacy() -> dict[str, Any]:
    count = 0
    for beacons, goals, early_i in product(product(range(2), repeat=2), permutations(range(4), 2), range(2)):
        early_j = 1-early_i
        for early_goal in set(range(4)) - set(goals):
            for late_goal in set(range(4)) - {goals[early_i], early_goal}:
                args = (beacons, goals, early_i, early_goal, late_goal)
                live, fresh = rollout(*args, "LIVE"), rollout(*args, "FRESH")
                assert live == fresh and all(all(row["correct"]) for row in live)
                for t in (0, 1, 2, 3, 4):
                    for k in range(2):
                        expected = transition(live[t]["beacons"][k], live[t]["actions"][k])
                        if t+2 in (2, 5):
                            focal = early_i if t+2 == 2 else early_j
                            expected ^= int(k == focal)
                        assert live[t+1]["beacons"][k] == expected
                count += 1
    assert count == 384
    visibility_checks = 0
    for own_bit, own_update, partner_bit, partner_update in product(range(2), range(4), range(2), range(4)):
        world = {"beacons": [own_bit, partner_bit], "updates": [own_update, partner_update]}
        original = controller_message(world, 0, 2)
        changed = deepcopy(world)
        changed["beacons"][1] ^= 1
        changed["updates"][1] = (partner_update+1) % 4
        assert controller_message(changed, 0, 2) == original
        for own_action in (*range(4), None):
            assert transition(own_bit, own_action) in (0, 1)
        visibility_checks += 1
    assert transition(0, None) == 0 and transition(1, None) == 1
    return {"six_round_oracle_schedules": count, "local_input_partner_invariance_cases": visibility_checks,
            "action_consequences_preserved": True, "invalid_action_holds_own_state": True,
            "scope": "Reference task kernel, not the unimplemented native model runner"}


def check_rivals_and_goals() -> dict[str, Any]:
    delta_random = ((1 + 0 + 0)/3 - (-1))/2
    q_random = (1 - 0.5 - 0.5)/3
    pair_q = sum(min(a, b) for a, b in product((1, -0.5, -0.5), repeat=2))/9
    assert abs(delta_random - 2/3) < 1e-12 and q_random == 0 and pair_q < 0
    echo_q = []
    for goal, old_bit in product(range(4), range(2)):
        old, new = action(goal, old_bit), action(goal, 1-old_bit)
        echo_q.append(specificity(2*(1-old_bit), old, new))
    assert sum(echo_q) == 0
    # Cross-side reuse of old physical candidates is unsound on ordinary rows.
    assert action(0, 0) == action(2, 1)
    fresh_cases = 0
    for row, goals in product(permutations(range(4)), permutations(range(4), 3)):
        g0, g1, h = goals
        assert len({row[g0], row[g1], row[h]}) == 3
        fresh_cases += 1
    # An artificial pulse leak selects the target without using incoming content.
    # Score that rival through the same signed/Delta estimator as the oracle.
    direct_contrasts = []
    for old, new in permutations(range(4), 2):
        deltas = {}
        for arm in ("LIVE", "Rcut"):
            outputs = []
            for pulse in (0, 1):
                incoming = "responsive" if arm == "LIVE" else None
                observation = {"leaked_pulse": pulse, "incoming": incoming}
                outputs.append((old, new)[observation["leaked_pulse"]])
            deltas[arm] = (signed(outputs[1], old, new)
                           - signed(outputs[0], old, new))/2
        assert deltas["LIVE"] == 1.0 and deltas["Rcut"] == 1.0
        direct_contrasts.append(deltas["LIVE"] - deltas["Rcut"])
    assert set(direct_contrasts) == {0.0}
    # Count balanced labels/physical roles; execution order is separately shuffled.
    pairs = list(permutations(range(4), 2))
    allocation: Counter[tuple[int, int]] = Counter()
    goal_totals: Counter[int] = Counter()
    for i in range(240):
        pair = pairs[i % 12]
        block = i // 12
        allocation[(block % 2, (block//2 + i%12) % 4)] += 1
        goal_totals.update(pair)
    assert set(allocation.values()) == {30} and set(goal_totals.values()) == {120}
    return {"random_nonold_switch_signed_Delta": delta_random,
            "random_nonold_switch_component_Q": q_random, "two_random_switches_chain_Q": pair_q,
            "goal_blind_echo_mean_Q": 0.0, "common_transfer_row_cases": fresh_cases,
            "ordinary_cross_side_candidate_collision_detected": True,
            "direct_initiator_response_return_contrast": sum(direct_contrasts)/len(direct_contrasts),
            "direct_initiator_response_cases": len(direct_contrasts),
            "initial_material_joint_cells_each": 30,
            "note": "Complete updated-goal, probe-alternative and text-subset balancing still requires a generator"}


def main() -> None:
    normal = NormalDist()
    critical = normal.inv_cdf(1 - 0.05/(2*22))
    n, sd = 240, 0.5
    precision = {"n": n, "assumed_episode_score_sd": sd,
        "pointwise_95_half_width": normal.inv_cdf(0.975)*sd/math.sqrt(n),
        "Holm22_conservative_80pct_normal_mde": (critical+normal.inv_cdf(0.8))*sd/math.sqrt(n),
        "scope": "Synthetic normal approximation, not empirical power"}
    natural, shadows, pulses, goals = 5*6, 6, 2*4*2*2, 2*3*2
    total = natural+shadows+pulses+goals
    assert total == 80 and total*240+60*6 == 19560
    result = {"status": "offline_proposal_checks_passed_not_model_evidence",
        "pulse_paths": check_pulse_paths(), "continuity": check_continuity_and_privacy(),
        "rivals_and_goals": check_rivals_and_goals(), "precision": precision,
        "workload": {"paired_work_periods_per_episode": total,
            "paired_work_periods_per_model_with_text": total*240+60*6,
            "two_models_paired_work_periods": 2*(total*240+60*6),
            "goal_probe_records_per_model": 240*2*3*2*2*6},
        "limitations": ["No LLM or GPU used", "No native runtime tested",
            "Complete material and exact-test simulation remain before freeze"]}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
