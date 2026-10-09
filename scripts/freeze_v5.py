"""Write-once algorithm and stage freezes for protocol v5, without model execution."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess

from mb import ledger, run
from mb.model_profiles import QWEN, LLAMA31

ROOT = Path(__file__).resolve().parents[1]
ALGORITHM = ROOT / "docs/protocol/FREEZE_protocol_v5_algorithm.json"


def algorithm_files() -> list[Path]:
    files = [ROOT / name for name in ("docs/protocol/PROTOCOL_V5.md", "requirements.txt", "pyproject.toml",
             "scripts/setup_replication_gpu.sh", "scripts/check_llama_acceptance.py", "scripts/supervise_v4.py")]
    files += list((ROOT / "src/mb").glob("*.py"))
    files += list((ROOT / "scripts").glob("*v5*.py"))
    files += list((ROOT / "tests").glob("*v5*.py"))
    files += list((ROOT / "tests").glob("*provenance*.py"))
    files += [ROOT / "tests/test_llama_acceptance.py", ROOT / "tests/test_runtime.py"]
    files += list((ROOT / "configs/v5").rglob("*.yaml"))
    files += list((ROOT / "configs/v5").rglob("*.json"))
    files += [ROOT / "docs/results/v5/local_preflight.json"]
    for profile in (QWEN, LLAMA31):
        assets = profile.validate_manifest()
        files += [profile.manifest_path]
        files += [profile.tokenizer_dir / name for name in assets["files"]]
    return sorted(set(files))


def verify(path: Path, *, require_kind: str | None = None) -> dict:
    doc = json.loads(path.read_text())
    if doc.get("protocol") != "v5" or doc.get("kind") not in ("algorithm", "stage"):
        raise ValueError("not a v5 freeze")
    if require_kind and doc["kind"] != require_kind:
        raise ValueError("wrong freeze kind")
    if not isinstance(doc.get("files"), dict) or not doc["files"]:
        raise ValueError("empty freeze")
    for name, sha in doc["files"].items():
        file = Path(name)
        file = file if file.is_absolute() else ROOT / file
        if not file.is_file() or ledger.file_sha256(file) != sha:
            raise ValueError(f"frozen input changed: {name}")
    if doc["kind"] == "algorithm":
        protocol = (ROOT / "docs/protocol/PROTOCOL_V5.md").read_text()
        if "Execution contract approved by the PI" not in protocol[:1200]:
            raise ValueError("v5 numerical execution contract is not approved")
        # Later generated stage configs do not retrospectively expand this freeze.
        required = {str(p.relative_to(ROOT)) for p in algorithm_files()
                    if not str(p.relative_to(ROOT)).startswith("configs/v5/")}
        if not required <= doc["files"].keys():
            raise ValueError("algorithm freeze omits current code or model assets")
    else:
        required_paths = []
        for field in ("config_path", "algorithm_path"):
            value = Path(doc[field])
            value = value if value.is_absolute() else ROOT / value
            required_paths.append(value)
        cfg = run.StageConfig.load(required_paths[0])
        pins = dict((cfg.params or {}).get("sources", {}))
        pins["model_assets"] = (cfg.params or {})["model_assets"]
        for pin in pins.values():
            value = Path(pin["path"])
            required_paths.append(value if value.is_absolute() else ROOT / value)
        if any(relative(path) not in doc["files"] for path in required_paths):
            raise ValueError("stage freeze omits its configuration, algorithm or source inputs")
        verify(required_paths[1], require_kind="algorithm")
    return doc


def write_once(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True, allow_nan=False)
        fh.write("\n")


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def create(kind: str, output: Path, config: Path | None = None) -> dict:
    if output.exists():
        raise ValueError("freeze already exists; never replace it")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"],
                                    cwd=ROOT, text=True).strip()
    if dirty:
        raise ValueError("commit tracked inputs before freezing")
    if kind == "algorithm":
        if "Execution contract approved by the PI" not in (ROOT / "docs/protocol/PROTOCOL_V5.md").read_text()[:1200]:
            raise ValueError("execution contract approval pending")
        files = algorithm_files()
        # Source/config files must be tracked; downloaded assets are explicitly pinned.
        assets = {p for profile in (QWEN, LLAMA31) for p in profile.tokenizer_dir.iterdir() if p.is_file()}
        for file in files:
            if file not in assets:
                subprocess.run(["git", "ls-files", "--error-unmatch", str(file.relative_to(ROOT))],
                               cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        extra = {}
    else:
        verify(ALGORITHM, require_kind="algorithm")
        if config is None:
            raise ValueError("stage freeze requires --config")
        cfg = run.StageConfig.load(config)
        run.validate_stage_sources(cfg)
        if (cfg.params or {}).get("provenance_contract"):
            from make_v5_provenance import verify_config_contract
            verify_config_contract(cfg)
        else:
            from mb.v5_static import verify_config_contract
            verify_config_contract(cfg)
        files = [ALGORITHM, config]
        pins = dict((cfg.params or {}).get("sources", {}))
        pins["model_assets"] = (cfg.params or {})["model_assets"]
        for pin in pins.values():
            file = Path(pin["path"])
            files.append(file if file.is_absolute() else ROOT / file)
        extra = {"config_path": relative(config), "algorithm_path": relative(ALGORITHM),
                 "split": cfg.split, "n_episodes": cfg.n_episodes}
    doc = {"protocol": "v5", "kind": kind, "commit": commit,
           "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "files": {relative(p): ledger.file_sha256(p) for p in sorted(set(files))}, **extra}
    write_once(output, doc)
    return doc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", choices=("algorithm", "stage"))
    group.add_argument("--verify", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify(args.verify)
        print("v5 freeze verified")
    else:
        output = args.output or ALGORITHM
        create(args.write, output, args.config)
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
