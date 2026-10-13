#!/usr/bin/env python3
"""Exercise the exact v6 record-validation, scoring and testing path with simulations.

These are analysis-code simulations, not task-engine/model runs or measured power.
The joint-quality null couples the two endpoint choices so its expectation is zero;
independent uniform endpoints instead give a negative min score, not a zero null.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import numpy as np
from scipy import stats

from mb.v6_analysis import KEY_FIELDS, MODELS, analyze, expected_keys


def synthetic_records(n: int = 60, *, seed: int = 0, mode: str = "null") -> tuple[list[dict], dict]:
    """Produce complete flat ledgers; truth metadata is synthetic, not material evidence."""
    if type(n) is not int or n < 2 or mode not in ("null", "alternative", "nonspecific"):
        raise ValueError("n >= 2 and a supported simulation mode required")
    rng = np.random.default_rng(seed)
    expected = {model: [f"synthetic-{model}-{index:04d}" for index in range(n)] for model in MODELS}
    records = []
    for model in MODELS:
        for index, ep in enumerate(expected[model]):
            joint_choices = {cp: int(rng.integers(4)) for cp in (2, 5)}
            for key in sorted(expected_keys(ep, model)):
                row: dict[str, Any] = dict(zip(KEY_FIELDS, key))
                kind, cp, arm = row["kind"], row["checkpoint"], row["arm"]
                side, version, r, qid = row["side"], row["version"], row["round_id"], row["qid"]
                focal = index % 2 if cp in (2, 3) else 1 - index % 2
                truth, choice = 0, int(rng.integers(4))
                if kind in ("pulse", "goal"):
                    row["focal_side"] = focal
                if kind == "pulse":
                    target = (r, side) in ((cp, 1 - focal), (cp + 1, focal))
                    truth = 2 * version
                    if target:
                        row.update(old_candidate=0, new_candidate=2)
                        if mode == "null" and arm == "L" and version == 1:
                            choice = joint_choices[cp]
                    if mode != "null":
                        cut = arm == "Fcut" and r == cp and side == 1 - focal or (
                            arm in ("Rcut", "Replay") and r == cp + 1 and side == focal)
                        choice = 0 if not version or cut else 2
                        if mode == "nonspecific" and target and arm == "L" and version == 1:
                            choice = (1, 2, 3)[index % 3]
                elif kind == "goal":
                    own = version if side == focal else 2
                    partner = 2 if side == focal else version
                    truth = {"action": 0, "transfer_action": own, "original_goal": side,
                             "latest_goal": own, "partner_beacon": 0, "partner_goal": partner}[qid]
                    if qid == "transfer_action":
                        row.update(old_candidate=0, new_candidate=1)
                    if mode != "null":
                        choice = truth
                    if mode == "alternative":
                        if qid == "transfer_action":
                            if arm == "L" and side != focal:
                                choice = version
                            elif arm == "Replay" and side == focal:
                                choice = 0
                        if qid == "latest_goal":
                            if arm == "L" and side != focal and version == 1:
                                choice = 0
                            elif arm == "Replay" and side == focal:
                                choice = 0
                elif mode != "null":
                    choice = truth
                    if mode == "alternative" and arm == "FRESH" and qid == "action":
                        choice = 1 if rng.random() < .5 else truth
                row.update(choice=choice, correct_choice=truth, correct=choice == truth, status="ok",
                           backend_kind="synthetic_analysis", scientific_data=False)
                records.append(row)
    return records, expected


def simulate(*, repetitions: int = 20, n: int = 60, n_boot: int = 200, seed: int = 0) -> dict:
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError("positive simulation repetition count required")
    family_false_rejections = 0
    secondary_false_rejections = 0
    sustained_false_rejections = 0
    endpoint_counts = {}
    for rep in range(repetitions):
        records, expected = synthetic_records(n, seed=seed + rep, mode="null")
        result = analyze(records, expected, n_boot=n_boot, seed=0)
        family_false_rejections += any(item["reject_two_sided_05"] for item in result["primary"])
        secondary_false_rejections += any(item["reject_two_sided_05"] for item in result["secondary"])
        sustained_false_rejections += any(result["sustained_response"].values())
        for item in result["primary"]:
            name = f"{item['model_profile']}:{item['endpoint']}"
            endpoint_counts[name] = endpoint_counts.get(name, 0) + int(item["reject_two_sided_05"])
    interval = stats.binomtest(family_false_rejections, repetitions).proportion_ci()
    checks = {}
    for mode in ("alternative", "nonspecific"):
        records, expected = synthetic_records(n, seed=seed, mode=mode)
        result = analyze(records, expected, n_boot=n_boot, seed=0)
        checks[mode] = {"sustained_response": result["sustained_response"],
                        "primary": [{key: item[key] for key in (
                            "model_profile", "endpoint", "mean", "p_two_sided", "p_holm")}
                                    for item in result["primary"]]}
    return {"purpose": "exact-code analysis simulation; no model or measured task power",
            "n_per_model": n, "repetitions": repetitions, "data_seed": seed,
            "bootstrap_draws": n_boot, "analysis_bootstrap_seed": 0,
            "null": {"description": "exchangeable path/action null; perfectly coupled endpoint Q null",
                     "primary_family_false_rejections": family_false_rejections,
                     "estimated_family_error": family_false_rejections / repetitions,
                     "binomial_95_interval": [interval.low, interval.high],
                     "sustained_false_rejections": sustained_false_rejections,
                     "secondary_family_false_rejections": secondary_false_rejections,
                     "endpoint_false_rejections": endpoint_counts},
            "checks": checks,
            "limitations": ["Finite Monte Carlo resolution, not proof of exact finite-sample t-test size.",
                            "Simulation outcomes do not authorize parameter selection, N changes or GPU execution.",
                            "Small simulation bootstrap count is explicit; formal default is 10000."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--n", type=int, default=60)
    parser.add_argument("--bootstrap", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(simulate(repetitions=args.repetitions, n=args.n, n_boot=args.bootstrap, seed=args.seed),
                     sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
