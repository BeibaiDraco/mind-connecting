#!/usr/bin/env python3
"""Write an inert prompt/material bundle. This entry point never loads a model."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from mb import v6_task_clarity as clarity, v6_tasks as tasks


def prepare(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    cases, history = clarity.make_short_cases(), clarity.make_history_episodes()
    short = []
    for c in cases:
        ep, w, s = c.episode, c.world, c.side
        for variant in clarity.VARIANTS:
            system, users = clarity.initial_prompts(ep, variant)
            q = clarity.question(ep, w, s, variant, "fullinfo_action")
            short.append({"case_id": ep.episode_id, "book": c.book, "variant": variant,
                "side": s, "own_beacon": w.beacons[s], "partner_beacon": w.beacons[1-s],
                "goal_label": ep.goal_names[w.goals[s]], "system": system,
                "initial_user": users[s], "question": q.text,
                "candidate_map": q.candidates, "correct_choice": q.correct,
                "correct_label": q.correct_label})
    files = {
        "short_inputs.json": short,
        "short_materials.json": [{"book": c.book, "side": c.side,
                                   "episode": tasks.episode_to_dict(c.episode)} for c in cases],
        "history_materials.json": [tasks.episode_to_dict(ep) for ep in history],
    }
    for name, value in files.items():
        with (output/name).open("x") as f:
            json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
            f.write("\n")
    repo = Path(__file__).resolve().parents[1]
    sources = ("src/mb/v6_task_clarity.py", "src/mb/v6_tasks.py", "src/mb/v6_contract.py",
               "scripts/prepare_v6_task_clarity.py", "tests/test_v6_task_clarity.py")
    manifest = {"contract": clarity.CONTRACT, "status": "prepared_local_not_frozen",
        "gpu_launch_authorized": False, "automatic_continuation": False,
        "scientific_admission": False, "profile": "qwen3_4b_instruct_2507",
        "short_codebooks": 8, "short_cases": 64, "short_prompt_variants": 3,
        "short_backend_labels": ["reference", "optimized"], "short_scored_answers": 384,
        "short_preparation_tokens": 0, "short_work_tokens": 0,
        "history_episodes": 8, "history_preparation_tokens": 16, "history_work_tokens": 64,
        "history_policy": "OFF", "history_gain": 0, "history_readouts": 384,
        "history_variant": None, "thresholds_ratified": False,
        "proposed_screens": {"short_correct_out_of_64": 58, "history_fullinfo_correct_out_of_96": 87},
        "history_focal_counts": dict(Counter(ep.early_side for ep in history)),
        "source_sha256": {name: hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in sources},
        "files": {name: {"bytes": (output/name).stat().st_size,
                          "sha256": hashlib.sha256((output/name).read_bytes()).hexdigest()} for name in files},
        "limits": "No real-model result, timing forecast, numerical admission, GPU worker or financial authority."}
    with (output/"manifest.json").open("x") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.output)
    print(json.dumps({key: result[key] for key in (
        "status", "short_cases", "short_scored_answers", "history_episodes", "gpu_launch_authorized")}))
