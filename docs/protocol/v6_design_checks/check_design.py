"""Offline logic and precision checks for an unfrozen proposal; no model use."""

from __future__ import annotations

import json
import math
from collections import Counter
from itertools import permutations, product
from statistics import NormalDist


def mapping_score(answer: int | None, old: int, new: int) -> float:
    if answer is None or answer == old:
        return 0.0
    return 1.0 if answer == new else -0.5


def check_round_trip() -> dict[str, object]:
    count = 0
    for f, g in product(permutations(range(4)), repeat=2):
        for x0, x1 in permutations(range(4), 2):
            assert g[f[x0]] != g[f[x1]]
            assert mapping_score(f[x1], f[x0], f[x1]) == 1.0
            alternatives = [r for r in range(4) if r != f[x0]]
            # Avoiding the old answer is not mapping-specific response.
            assert sum(mapping_score(r, f[x0], f[x1]) for r in alternatives) == 0
            assert mapping_score(f[x0], f[x0], f[x1]) == 0.0
            count += 1
    assert count == 6912
    # A one-way full-table broadcast can solve the composition without a loop.
    broadcast_accuracy = {arm: 1.0 for arm in ("L11", "L01")}
    assert broadcast_accuracy["L11"] - broadcast_accuracy["L01"] == 0
    # Old success must not establish path necessity for a new request.
    old = {"L11": 0.9, "L01": 0.1, "L10": 0.1, "RY": 0.9}
    new = {"L11": 0.5, "L01": 0.5, "L10": 0.5, "RY": 0.25}
    averaged = ((old["L11"] - old["L01"]) + (new["L11"] - new["L01"])) / 2
    assert averaged == 0.4 and new["L11"] - new["L01"] == 0
    return {
        "enumerated_cases": count,
        "responsive_oracle_specificity": 1.0,
        "random_nonold_switch_expected_specificity": 0.0,
        "stale_reply_specificity": 0.0,
        "oneway_full_table_broadcast_forward_necessity": 0.0,
        "counterexample_averaged_forward_effect": averaged,
        "counterexample_changed_forward_effect": 0.0,
        "scope": "Algebraic task checks, not observed LLM outcomes or engine tests",
    }


def check_goal_task() -> dict[str, object]:
    table = [[r ^ c for c in range(4)] for r in range(4)]
    for row in table:
        assert len(set(row)) == 4
    for col in zip(*table):
        assert len(set(col)) == 4
    for fact, goal in product(range(2), range(4)):
        assert table[2 * fact][goal] != table[2 * fact + 1][goal]
        assert table[fact][goal] != table[2 + fact][goal]
    cases = 0
    for g0, g1, h in permutations(range(4), 3):
        for facts in range(4):
            for new_map in permutations(range(4)):
                a0, a1, ah = new_map[g0], new_map[g1], new_map[h]
                assert len({a0, a1, ah}) == 3
                original_records = {"I": g0, "J": h}
                updated_records = {**original_records, "I": g1}
                old_actions = {side: new_map[goal] for side, goal in original_records.items()}
                new_actions = {side: new_map[goal] for side, goal in updated_records.items()}
                assert old_actions["J"] == new_actions["J"]
                assert old_actions["I"] != new_actions["I"]
                cases += 1
    triples = list(permutations(range(4), 3))
    joint_counts: Counter[tuple[int, int]] = Counter()
    for index, triple in enumerate(triples):
        within: Counter[tuple[int, int]] = Counter()
        for repetition in range(25):
            cell = (repetition + index) % 8
            key = (cell // 4, cell % 4)
            within[key] += 1
            joint_counts[key] += 1
        assert sum(within.values()) == 25
        assert max(within.values()) - min(within.values()) <= 1
    assert set(joint_counts.values()) == {75}
    # A foreign goal can drive a choice while the record report stays correct.
    truth_h, own_report, choice_after_update = 2, 2, 1
    assert own_report == truth_h and choice_after_update != truth_h
    return {
        "fact_complete_truth_cases": cases,
        "formal_goal_triples": len(triples),
        "episodes_per_triple": 25,
        "each_physical_initiator_by_fact_pair_cell": 75,
        "joint_cells": len(joint_counts),
        "own_fact_only_possible_actions": 2,
        "goal_control_and_record_accuracy_can_dissociate": True,
    }


def check_echo_counterexample() -> dict[str, float]:
    # Endpoint sensitivity can change through nonspecific echo alone.
    # s is p(new-action)-p(old-action); these values are all feasible.
    s_live = (-1.0, 1.0)
    s_replay = (-1.0, 0.0)
    delta_live = (s_live[1] - s_live[0]) / 2
    delta_replay = (s_replay[1] - s_replay[0]) / 2
    feedback = delta_live - delta_replay
    assert feedback == 0.5
    # Echoing an input from a disjoint request vocabulary is not a response ID.
    request_tokens = {"Amber", "Cobalt", "Ivory", "Violet"}
    response_tokens = {"Moon", "Leaf", "Sun", "Wave"}
    assert request_tokens.isdisjoint(response_tokens)
    assert mapping_score(None, 0, 1) == 0.0
    return {"possible_echo_feedback_score": feedback, "echo_mapping_specificity": 0.0}


def precision() -> dict[str, object]:
    normal = NormalDist()
    critical = normal.inv_cdf(1 - 0.05 / (2 * 12))
    rows = []
    for n, sd in product((240, 600), (0.25, 0.5, 1.0, 1.5)):
        se = sd / math.sqrt(n)
        rows.append({
            "n": n, "episode_score_sd": sd,
            "pointwise_95_half_width": round(normal.inv_cdf(0.975) * se, 6),
            "conservative_80pct_normal_mde": round((critical + normal.inv_cdf(0.8)) * se, 6),
        })
    power_rows = []
    for n, delta in product((240, 600), (0.0, 0.05, 0.15)):
        # A bounded paired-accuracy difference with P(nonzero)=0.30.
        discordance = 0.30
        se = math.sqrt(discordance - delta * delta) / math.sqrt(n)
        shift = delta / se
        approx_power = 1 - normal.cdf(critical - shift) + normal.cdf(-critical - shift)
        power_rows.append({"n": n, "mean": delta, "discordance": discordance,
                           "normal_approx_rejection_probability": round(approx_power, 6)})
    return {
        "method": "Synthetic normal approximation; worst Holm entry threshold alpha/12",
        "limitations": "Not empirical power or a simulation of the LLM; score variances remain unknown",
        "precision_grid": rows, "synthetic_null_small_large_grid": power_rows,
    }


def main() -> None:
    trajectories = (240 + 600) * 5 * 2 + 120 * 2 * 2
    held = 600 * 5 * 2 * 2 * 8
    cut = 600 * 2 * 2 * 2 * 3
    text = 120 * 2 * 2 * 8
    assert (trajectories, held, cut, text) == (8880, 96000, 14400, 3840)
    result = {
        "status": "offline_design_logic_passed_not_frozen",
        "round_trip": check_round_trip(), "goal_task": check_goal_task(),
        "echo_counterexample": check_echo_counterexample(),
        "workload_per_checkpoint": {"paired_postevent_trajectories": trajectories,
            "G_core_held_records": held, "G_cut_records": cut, "G_text_records": text},
        "precision": precision(),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
