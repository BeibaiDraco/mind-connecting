#!/usr/bin/env python3
"""Prepare an inert V6 material/source package or one non-authorizing stage plan.

No credentials, provider calls, models, torch or execution grants are created.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mb.model_profiles import PROFILES
from mb.v6_admission import recommended_contract
from mb.v6_contract import canonical_digest
from mb.v6_launch import ROOT, file_sha256, read
from mb.v6_run import source_manifest
from mb import v6_neutral as neutral
from mb import v6_tasks as tasks


def write_new(path: Path, value: dict) -> None:
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def pin(path: Path) -> dict:
    return {"path": str(path.resolve()), "sha256": file_sha256(path)}


def prepare(directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=False)
    materials_dir = directory/"materials"; materials_dir.mkdir()
    contract_path = ROOT/"configs/v6/admission_proposal.json"
    if read(contract_path) != recommended_contract():
        raise ValueError("Proposed admission JSON does not match the reviewed scorer")
    catalog, seen_ids, seen_tasks = {}, set(), set()
    for profile in PROFILES:
        PROFILES[profile].validate_manifest()
        catalog[profile] = {}
        for name, stage, n, gain in (("acceptance", "acceptance", 1, .5),
                                     ("smoke", "smoke", 2, .5),
                                     ("baseline", "baseline", 60, 0.),
                                     ("calibration_025", "calibration", 40, .25),
                                     ("calibration_050", "calibration", 40, .5),
                                     ("calibration_100", "calibration", 40, 1.),
                                     ("validation", "validation", 80, None),
                                     ("formal", "formal", 240, None)):
            if stage in ("baseline", "calibration", "validation"):
                suffix = {"calibration_025": "calibration_g025", "calibration_050": "calibration_g050",
                          "calibration_100": "calibration_g100"}.get(name, stage)
                episodes = neutral.make_episodes(n, stage, namespace=f"{profile}_{suffix}")
                task_episodes = [ep.task for ep in episodes]
                path = materials_dir/f"{profile}_{name}.json"
                neutral.write_materials(path, episodes)
            else:
                episodes = tasks.make_episodes(n, f"v6_{profile}_{stage}", seed=0)
                task_episodes = episodes
                path = materials_dir/f"{profile}_{name}.json"
                tasks.write_materials(path, episodes)
            for ep in task_episodes:
                value = tasks.episode_to_dict(ep)
                for field in ("episode_id", "stage", "seed"):
                    value.pop(field)
                fingerprint = canonical_digest(value)
                if ep.episode_id in seen_ids or fingerprint in seen_tasks:
                    raise ValueError("Substantive task material repeats across stages or profiles")
                seen_ids.add(ep.episode_id); seen_tasks.add(fingerprint)
            text_ids = []
            if stage == "formal":
                chosen = tasks.select_text_subset(episodes, n=60)
                if chosen is None:
                    raise ValueError("Balanced preselected text subset unavailable")
                text_ids = [ep.episode_id for ep in chosen]
            elif stage == "smoke":
                text_ids = [episodes[0].episode_id]
            catalog[profile][name] = {"stage": stage, "n": n, "gain": gain,
                "material_pin": pin(path), "text_episode_ids": text_ids,
                "stage_material_identity": [ep.episode_id for ep in episodes]}
    package = {"version": "v6-prepared-package-1", "status": "prospective_proposal",
        "execution_authorized": False, "source_manifest": source_manifest(),
        "runtime": {"work_tokens": 64, "preparation_tokens": 16, "window": 16,
                    "choice_labels": ["1", "2", "3", "4"]},
        "admission_contract_pin": pin(contract_path), "materials": catalog,
        "substantive_task_materials_disjoint": True,
        "budget_proposal": {"total_cap_usd": 100, "initial_cap_usd": 12,
                            "hourly_cap_usd": 1.6, "shutdown_reserve_seconds": 300,
                            "remote_disk_gib": 650, "backup_reservation_gib": 600,
                            "maximum_transfer_usd_per_tb": 10},
        "unmeasured": ["native_acceptance", "actual_throughput", "archive_bytes", "backup_throughput"],
        "authorization": "requires a separate source-and-contract-bound PI receipt"}
    write_new(directory/"package.json", package)
    return package


def stage_plan(package_path: Path, profile: str, name: str, output_dir: Path,
               prerequisites: dict, selected_gain: float | None = None) -> dict:
    package = read(package_path)
    if package["source_manifest"] != source_manifest():
        raise ValueError("Prepared source changed; regenerate the inert package")
    entry = package["materials"][profile][name]
    gain = entry["gain"] if entry["gain"] is not None else selected_gain
    candidates = (.25, .5, 1.) if entry["gain"] is None else (0., .25, .5, 1.)
    if type(gain) not in (int, float) or gain not in candidates:
        raise ValueError("Conditional stage needs its independently selected gain")
    if not output_dir.is_absolute():
        raise ValueError("Use an explicit absolute execution output path")
    return {"version": "v6-native-stage-1", "stage": entry["stage"], "model_profile": profile,
        "n": entry["n"], "material_pin": entry["material_pin"],
        "runtime": {**package["runtime"], "gain": gain},
        "text_episode_ids": entry["text_episode_ids"], "output_dir": str(output_dir),
        "source_manifest": package["source_manifest"], "prerequisites": prerequisites,
        "admission_contract_pin": package["admission_contract_pin"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    package = sub.add_parser("package")
    package.add_argument("--output", type=Path, required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--package", type=Path, required=True)
    plan.add_argument("--model", choices=list(PROFILES), required=True)
    plan.add_argument("--name", required=True)
    plan.add_argument("--run-directory", type=Path, required=True)
    plan.add_argument("--prerequisites", type=Path, required=True)
    plan.add_argument("--selected-gain", type=float)
    plan.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "package":
        value = prepare(args.output)
        print(json.dumps({"status": value["status"], "execution_authorized": False,
                          "models": list(value["materials"]), "package": str(args.output/"package.json")}))
    else:
        value = stage_plan(args.package, args.model, args.name, args.run_directory,
                           read(args.prerequisites), args.selected_gain)
        write_new(args.output, value)
        print(json.dumps({"plan_sha256": canonical_digest(value), "execution_authorized": False}))


if __name__ == "__main__":
    main()
