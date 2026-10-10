"""Audit both named historical chains and prepare immutable local continuation inputs."""
from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

import yaml

from mb import chat, ledger, run, tasks, provenance_tasks, v5_continuation as continuation
from mb.model_profiles import LLAMA31

ROOT = continuation.ROOT


def write_once(path: Path, text: str) -> None:
    if path.exists():
        if path.read_text() != text:
            raise ValueError(f"refusing to replace {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        handle.write(text)


def physical_hash(ep) -> str:
    obj = dataclasses.asdict(ep)
    for key in ("episode_id", "split", "index", "rotations", "s2"):
        obj.pop(key, None)
    return ledger.canonical_hash(obj, n=64)


def material_preflight(results_root: Path, configs: dict) -> dict:
    targets = {cfg.split for cfg in configs.values()}
    historical_specs = {}
    for path in sorted(results_root.glob("*/identity.json")):
        identity = json.loads(path.read_text())
        cfg = identity["stage_config"]
        if cfg["split"] in targets:
            raise ValueError("planned continuation formal split already has a run; do not regenerate")
        key = (cfg["split"], int(cfg.get("seed", 0)))
        historical_specs[key] = max(historical_specs.get(key, 0), int(cfg["n_episodes"]))
    for path in sorted((ROOT / "configs").rglob("*.yaml")):
        cfg = yaml.safe_load(path.read_text())
        if not isinstance(cfg, dict) or not {"split", "n_episodes"} <= cfg.keys() or cfg["split"] in targets:
            continue
        key = (cfg["split"], int(cfg.get("seed", 0)))
        historical_specs[key] = max(historical_specs.get(key, 0), int(cfg["n_episodes"]))
    seen = {physical_hash(ep): split for (split, seed), n in historical_specs.items()
            for ep in tasks.make_episodes(n, split, seed)}
    tok = chat.load_tokenizer(profile=LLAMA31)
    report = {}
    for study, cfg in configs.items():
        eps = tasks.make_episodes(600, cfg.split, 0)
        tasks.validate_episodes(eps)
        checks, hashes, lengths = 0, [], {}
        for ep in eps:
            h = physical_hash(ep)
            if h in seen:
                raise ValueError(f"formal material overlap with {seen[h]}")
            seen[h] = cfg.split
            hashes.append(h)
            for qid in cfg.qids:
                for rot in ep.rotations:
                    if cfg.provenance:
                        q = provenance_tasks.render_question(tok, ep, "A", qid, rot, False)
                        if q != provenance_tasks.render_question(tok, ep, "A", qid, rot, True):
                            raise ValueError("donor treatment changes receiver question tokens")
                    else:
                        q = tasks.readout_questions(tok, ep, "A", rotations=[rot], qids=[qid])[0]
                    if len(q.options) != 4 or len(set(q.options)) != 4 or not q.suffix_ids:
                        raise ValueError("invalid formal question")
                    lengths.setdefault(qid, []).append(len(q.suffix_ids))
                    checks += 1
        report[study] = {"split": cfg.split, "n_episodes": 600, "physical_fingerprints": hashes,
                         "question_ordering_checks": checks, "source_splits_disjoint": True,
                         "suffix_lengths": {q: [min(v), max(v)] for q, v in lengths.items()}}
    return {"protocol": continuation.VERSION, "historical_material_splits_checked": len(historical_specs),
            "formal_splits_previously_unused": True, "native_tokenizer_verified": True,
            "studies": report, "paid_execution_authorized": False}


def prepare_all(results_root: Path, out: Path) -> dict:
    results_root, out = results_root.resolve(), out.resolve()
    files, configs = {}, {}
    for study in ("provenance", "static"):
        evidence_path = out / f"{study}_evidence.json"
        evidence, cfg = continuation.prepare(study, results_root, evidence_path)
        files[evidence_path] = json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n"
        files[out / f"{study}_confirm.yaml"] = yaml.safe_dump(dataclasses.asdict(cfg), sort_keys=False)
        configs[study] = cfg
    preflight = material_preflight(results_root, configs)
    files[out / "material_preflight.json"] = json.dumps(preflight, indent=2, sort_keys=True) + "\n"
    # Audit every input and material before the first write; never mutate old runs.
    for path, text in files.items():
        if path.exists() and path.read_text() != text:
            raise ValueError(f"refusing to overwrite changed preparation: {path}")
    for path, text in files.items():
        write_once(path, text)
    for cfg in configs.values():
        continuation.verify_config_contract(cfg, results_root=results_root)
    return {"protocol": continuation.VERSION, "prepared": list(configs), "paid_execution_authorized": False,
            "configs": {s: str(out / f"{s}_confirm.yaml") for s in configs}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=ROOT / "data/results")
    parser.add_argument("--out", type=Path, default=ROOT / "configs/v5_continuation")
    parser.add_argument("--analyze", type=Path)
    parser.add_argument("--analysis-output", type=Path)
    args = parser.parse_args()
    if args.analyze:
        result = continuation.analyze_run(args.analyze, results_root=args.results_root)
        output = args.analysis_output or args.analyze / "continuation_summary.json"
        write_once(output, json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({"consumable": result["consumable"], "output": str(output)}))
    else:
        print(json.dumps(prepare_all(args.results_root, args.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
