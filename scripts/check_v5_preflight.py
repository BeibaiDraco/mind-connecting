"""Torch-free full-split/material/tokenizer checks and planning precision report."""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from scipy.stats import norm

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from mb import chat, ledger, tasks, provenance_tasks as p, run
from mb.model_profiles import QWEN, LLAMA31

ROOT = Path(__file__).resolve().parents[1]


def split_specs() -> dict[str, int]:
    result = {f"v5_{model}_provenance_{phase}": n for model in ("qwen", "llama31")
              for phase, n in (("smoke", 4), ("base", 60), ("validity", 80), ("confirm", 600))}
    result.update({f"v5_llama_static_{phase}": n for phase, n in
                   (("cal", 60), ("match", 40), ("validity", 80), ("confirm", 600))})
    return result


def physical_hash(ep: tasks.Episode) -> str:
    data = dataclasses.asdict(ep)
    for key in ("episode_id", "split", "index", "rotations", "s2"):
        data.pop(key, None)
    return ledger.canonical_hash(data)


def precision(n: int = 600) -> dict:
    return {"n": n, "mean_95ci_halfwidth_per_paired_sd": float(norm.ppf(.975) / n ** .5),
            "normal_approx_80pct_power_standardized_effect": {
                str(family): float((norm.ppf(1-.05/(2*family)) + norm.ppf(.8)) / n ** .5)
                for family in (1, 2, 6)},
            "worst_case_binary_paired_difference_95ci_halfwidth": float(norm.ppf(.975) / n ** .5),
            "raw_logit_precision_known": False,
            "interpretation": "Planning approximation; no new outcomes, power guarantee or equivalence assertion."}


def historical_v4() -> dict:
    manifest = ROOT / "docs/protocol/FREEZE_protocol_v4.txt"
    lines = manifest.read_text().splitlines()
    commit = next(line.split(": ", 1)[1] for line in lines if line.startswith("# commit:"))
    count = 0
    for line in lines:
        if not line or line.startswith("#"):
            continue
        sha, rel = line.split("  ", 1)
        blob = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT,
                              capture_output=True, check=False)
        payload = blob.stdout if blob.returncode == 0 else (ROOT / rel).read_bytes()
        if hashlib.sha256(payload).hexdigest() != sha:
            raise ValueError(f"historical v4 frozen input no longer recoverable: {rel}")
        count += 1
    return {"verified": True, "commit": commit, "files": count,
            "scope": "Original commit for tracked inputs; locally hash-verified untracked model assets."}


def material_check(episodes: list[tasks.Episode], tok) -> dict:
    questions = 0
    lengths: dict[str, list[int]] = {}
    for ep in episodes:
        donor = p.donor_episode(ep)
        # Rendering A must use original ep. Only B receives the altered view.
        if ep.own_rule("B") != donor.own_rule("B") or ep.own_word("B") != donor.own_word("B"):
            raise ValueError("donor mutation changed its own content")
        if tasks.note_key(ep, "B") == tasks.note_key(donor, "B"):
            raise ValueError("donor note collision")
        if tasks.private_prefix_ids(tok, ep, "B") == tasks.private_prefix_ids(tok, donor, "B"):
            raise ValueError("donor conflict has no token-level intervention")
        for recipient in tasks.ROLES:
            for qid in p.ALL_QIDS:
                for rotation in ep.rotations:
                    old = p.render_question(tok, ep, recipient, qid, rotation, False)
                    changed = p.render_question(tok, ep, recipient, qid, rotation, True)
                    if old != changed:
                        raise ValueError("treatment changes question text, options or tokenization")
                    if len(old.options) != 4 or len(set(old.options)) != 4:
                        raise ValueError("answers must keep four unique physical candidates")
                    if not old.suffix_ids or old.suffix_ids[-1] not in range(len(tok)):
                        raise ValueError("invalid native readout suffix")
                    for conflict in (False, True):
                        meta = p.record_metadata(ep, recipient, old, conflict)
                        truth = meta["expected_truth"]
                        if truth is not None and truth not in old.options:
                            raise ValueError("source truth is absent from fixed answer set")
                    if recipient == "A" and (p.record_metadata(ep, recipient, old, False)["receiver_card_sha256"]
                                             != p.record_metadata(ep, recipient, old, True)["receiver_card_sha256"]):
                        raise ValueError("receiver card changed with donor-only mutation")
                    questions += 1
                    lengths.setdefault(qid, []).append(len(old.suffix_ids))
    return {"episodes": len(episodes), "question_ordering_recipient_checks": questions,
            "suffix_length_ranges": {qid: [min(vals), max(vals)] for qid, vals in lengths.items()},
            "donor_only_mutation": True, "fixed_question_tokens": True}


def preflight() -> tuple[dict, dict]:
    tokenizers = {"qwen": chat.load_tokenizer(profile=QWEN), "llama31": chat.load_tokenizer(profile=LLAMA31)}
    for model, profile in (("qwen", QWEN), ("llama31", LLAMA31)):
        profile.validate_manifest()
        chat.require_verified_tokenizer(tokenizers[model], profile)
    # Compare content, not just renamed IDs, to all previous stage materials.
    seen: dict[str, str] = {}
    for path in sorted((ROOT / "configs").rglob("*.yaml")):
        if "v5" in path.parts:
            continue
        try:
            cfg = run.StageConfig.load(path)
        except (ValueError, TypeError):
            continue
        for ep in tasks.make_episodes(cfg.n_episodes, cfg.split, cfg.seed):
            seen[physical_hash(ep)] = cfg.split
    splits, materials = {}, {}
    for split, n in split_specs().items():
        episodes = tasks.make_episodes(n, split, seed=0)
        tasks.validate_episodes(episodes)
        hashes = [physical_hash(ep) for ep in episodes]
        if len(set(hashes)) != n:
            raise ValueError("duplicate materials within a new split")
        overlap = [h for h in hashes if h in seen]
        if overlap:
            raise ValueError(f"new split {split} overlaps prior material from {seen[overlap[0]]}")
        seen.update({h: split for h in hashes})
        splits[split] = {"n": n, "seed": 0, "content_sha256": ledger.canonical_hash(hashes),
                         "episode_ids_sha256": ledger.canonical_hash([ep.episode_id for ep in episodes])}
        if "provenance" in split:
            model = "llama31" if "llama31" in split else "qwen"
            materials[split] = material_check(episodes, tokenizers[model])
    if "torch" in sys.modules:
        raise RuntimeError("offline preparation imported torch")
    report = {"local_checks_passed": True, "gpu_acceptance_passed": False,
              "scientific_gates_passed": False, "paid_execution_authorized": False,
              "historical_v4": historical_v4(), "precision": precision(), "materials": materials,
              "note": "Local readiness is not a scientific gate or a GPU execution result."}
    return {"protocol": "v5", "seed": 0, "splits": splits}, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits-out", type=Path, default=ROOT / "configs/v5/split_manifest.json")
    parser.add_argument("--report-out", type=Path, default=ROOT / "docs/results/v5/local_preflight.json")
    args = parser.parse_args()
    splits, report = preflight()
    for path, doc in ((args.splits_out, splits), (args.report_out, report)):
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(doc, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if path.exists() and path.read_text() != content:
            raise ValueError(f"refusing to replace changed preflight evidence: {path}")
        if not path.exists():
            path.write_text(content)
    print(json.dumps({"local_checks_passed": True, "new_splits": len(splits["splits"]),
                      "gpu_run": False, "report": str(args.report_out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
