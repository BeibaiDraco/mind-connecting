#!/usr/bin/env python3
"""Offline materials/tokenizer audits and synthetic v6 execution, never GPU."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mb import chat
from mb.model_profiles import PROFILES
from mb.v6_contract import RuntimeSpec, canonical_digest
from mb.v6_tasks import (audit_tokenizer, balance_report, episode_to_dict,
                         make_episodes, materials_sha256, write_materials)
from mb.v6_run import run_synthetic, source_manifest


def check_materials(n: int, seed: int, *, tokenize: bool, output: Path | None) -> dict:
    stages = {"baseline": 60, "calibration025": 40, "calibration050": 40,
              "calibration100": 40, "validation": 80, "formal": n}
    manifest = {"status": "draft_local_only", "model_or_gpu_used": False,
                "scientific_settings_ratified": False, "source": source_manifest(),
                "materials": {}, "tokenizers": {}, "hardware_ready": False,
                "blockers": ["neutral_fact_and_probe_schedule_unratified",
                             "neutral_capability_aggregation_unratified",
                             "exact_N40_calibration_rule_unratified",
                             "prospective_settings_and_full_material_balance_review",
                             "native_GPU_and_control_token_acceptance_not_run",
                             "paid_acceptance_and_total_budget_not_approved"]}
    if output is not None:
        output.mkdir(parents=True, exist_ok=False)
    seen = set()
    formal = {}
    for model in PROFILES:
        manifest["materials"][model] = {}
        for stage, count in stages.items():
            episodes = make_episodes(count, stage=f"v6_{model}_{stage}", seed=seed)
            for ep in episodes:
                payload = episode_to_dict(ep)
                for key in ("stage", "seed", "episode_id"):
                    payload.pop(key)
                identity = canonical_digest(payload)
                if identity in seen:
                    raise ValueError("Repeated substantive episode material across stages/models")
                seen.add(identity)
            entry = {"n": count, "sha256": materials_sha256(episodes),
                     "purpose": "draft main-task materials" if stage == "formal" else
                         "main-task skeleton only; neutral admission collection is unimplemented",
                     "balance": balance_report(episodes)}
            manifest["materials"][model][stage] = entry
            if stage == "formal":
                formal[model] = episodes
            if output is not None:
                write_materials(output/f"{model}_{stage}.json", episodes)
    from mb.v6_tasks import select_text_subset
    for model, episodes in formal.items():
        selected = select_text_subset(episodes, n=min(60, len(episodes)))
        if selected is None:
            manifest["blockers"].append(f"balanced_text_subset_unavailable:{model}")
            manifest["materials"][model]["text_subset"] = {"available": False}
            continue
        manifest["materials"][model]["text_subset"] = {
            "episode_ids": [ep.episode_id for ep in selected], "n": len(selected),
            "balance": balance_report(selected)}
        if tokenize:
            # Only known existing paths are admitted. No download command is exposed.
            profile = PROFILES[model]
            if not profile.tokenizer_dir.is_dir():
                raise FileNotFoundError(f"Local tokenizer unavailable for {model}")
            tok = chat.load_tokenizer(profile=model)
            manifest["tokenizers"][model] = audit_tokenizer(tok, episodes)
    manifest["substantive_stage_and_model_materials_disjoint"] = True
    if output is not None:
        with (output/"preflight.json").open("x") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    materials = sub.add_parser("materials", help="Generate proposed materials without running a model")
    materials.add_argument("--n", type=int, default=240)
    materials.add_argument("--seed", type=int, default=0)
    materials.add_argument("--audit-tokenizers", action="store_true")
    materials.add_argument("--output", type=Path)
    demo = sub.add_parser("dry-run", help="Deterministic software fixture, not an LLM")
    demo.add_argument("--output", type=Path, required=True)
    demo.add_argument("--n", type=int, default=2)
    demo.add_argument("--seed", type=int, default=0)
    demo.add_argument("--model-schema", choices=list(PROFILES), default=next(iter(PROFILES)))
    demo.add_argument("--work-tokens", type=int, default=4)
    demo.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.command == "materials":
        result = check_materials(args.n, args.seed, tokenize=args.audit_tokenizers, output=args.output)
    else:
        episodes = make_episodes(args.n, "v6_synthetic_development", args.seed)
        spec = RuntimeSpec(work_tokens=args.work_tokens, preparation_tokens=2,
                           window=min(16,args.work_tokens))
        result = run_synthetic(args.output, episodes, spec, model_profile=args.model_schema,
                               text_episodes={episodes[0].episode_id}, resume=args.resume)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
