"""Separate write-once continuation freezes; never replace a historical v5 freeze."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess

from mb import ledger, run, v5_continuation as continuation
from mb.model_profiles import LLAMA31

ROOT = continuation.ROOT
ALGORITHM = ROOT / "docs/protocol/FREEZE_protocol_v5_continuation_algorithm.json"
PROTOCOL = ROOT / "docs/protocol/PROTOCOL_V5_CONTINUATION.md"


def name(path: Path) -> str:
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def algorithm_files() -> list[Path]:
    import freeze_v5

    files = freeze_v5.algorithm_files()
    files += [PROTOCOL, ROOT / continuation.HISTORICAL_FREEZE]
    for directory in ("scripts", "tests", "configs/v5_continuation"):
        files += [p for p in (ROOT / directory).rglob("*") if p.is_file()
                  and ("continuation" in p.name or directory.startswith("configs"))
                  and p.suffix in (".py", ".json", ".yaml") and not p.name.endswith("_freeze.json")]
    files += list((ROOT / "docs/runbooks").glob("*CONTINUATION*.md"))
    return sorted(set(files) - {ALGORITHM})


def validate_config(cfg: run.StageConfig, results_root: Path | None = None) -> None:
    if (cfg.params or {}).get("continuation"):
        continuation.verify_config_contract(cfg, results_root=results_root)
        return
    # The sole engineering config is the exact original four-episode Llama smoke.
    import make_v5_provenance

    continuation.require(cfg.model_profile == LLAMA31.key and cfg.stage == "v5_llama31_provenance_smoke",
                         "only explicit continuation formal or exact Llama smoke is allowed")
    make_v5_provenance.verify_config_contract(cfg)


def verify(path: Path, *, results_root: Path | None = None, require_kind: str | None = None) -> dict:
    doc = continuation.read(path)
    continuation.require(doc.get("protocol") == continuation.VERSION and doc.get("kind") in ("algorithm", "stage"),
                         "not a continuation freeze")
    continuation.require(require_kind is None or doc["kind"] == require_kind, "wrong freeze kind")
    continuation.require(isinstance(doc.get("files"), dict) and bool(doc["files"]), "empty freeze")
    for value, sha in doc["files"].items():
        continuation.check_pin({"path": value, "sha256": sha}, results_root)
    if doc["kind"] == "algorithm":
        required = {name(p) for p in algorithm_files()}
        continuation.require(required <= doc["files"].keys(), "algorithm freeze omits code/assets/configs")
        continuation.historical_code()
    else:
        algorithm = continuation.local_path(doc["algorithm_path"])
        config = continuation.local_path(doc["config_path"])
        verify(algorithm, results_root=results_root, require_kind="algorithm")
        cfg = run.StageConfig.load(config)
        validate_config(cfg, results_root)
        required = {name(algorithm), name(config)}
        pins = {**cfg.params.get("sources", {}), "model_assets": cfg.params["model_assets"]}
        required.update(pin["path"] for pin in pins.values())
        continuation.require(required <= doc["files"].keys(), "stage freeze omits direct or historical sources")
    return doc


def create(kind: str, output: Path, config: Path | None = None, *, results_root: Path | None = None) -> dict:
    continuation.require(not output.exists(), "freeze already exists")
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True).strip()
    continuation.require(not dirty, "commit tracked inputs before freezing")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if kind == "algorithm":
        continuation.historical_code()
        files = algorithm_files()
        for path in files:
            if path.is_relative_to(ROOT / "materials") and "tokenizer" in str(path):
                continue
            subprocess.run(["git", "ls-files", "--error-unmatch", name(path)], cwd=ROOT,
                           check=True, stdout=subprocess.DEVNULL)
        hashes = {name(p): ledger.file_sha256(p) for p in files}
        extra = {"paid_execution_authorized": False}
    elif kind == "stage":
        continuation.require(config is not None, "stage requires a config")
        verify(ALGORITHM, results_root=results_root, require_kind="algorithm")
        cfg = run.StageConfig.load(config)
        validate_config(cfg, results_root)
        hashes = {name(p): ledger.file_sha256(p) for p in (ALGORITHM, config)}
        for pin in {**cfg.params.get("sources", {}), "model_assets": cfg.params["model_assets"]}.values():
            continuation.check_pin(pin, results_root)
            hashes[pin["path"]] = pin["sha256"]
        extra = {"algorithm_path": name(ALGORITHM), "config_path": name(config),
                 "split": cfg.split, "n_episodes": cfg.n_episodes, "paid_execution_authorized": False}
    else:
        raise ValueError("unknown freeze kind")
    doc = {"protocol": continuation.VERSION, "kind": kind, "commit": commit,
           "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "files": hashes, **extra}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as handle:
        json.dump(doc, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return doc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", choices=("algorithm", "stage"))
    action.add_argument("--verify", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--results-root", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify(args.verify, results_root=args.results_root)
        print("continuation freeze verified")
    else:
        path = args.output or ALGORITHM
        create(args.write, path, args.config, results_root=args.results_root)
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
