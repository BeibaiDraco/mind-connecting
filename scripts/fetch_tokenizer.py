"""Download the pinned Qwen3-4B-Instruct-2507 tokenizer files into materials/tokenizer and verify hashes.

Only small tokenizer/config files are fetched; model weights are never downloaded here.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "materials" / "tokenizer_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    out_dir = ROOT / manifest["local_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, meta in manifest["files"].items():
        target = out_dir / name
        if not target.exists() or sha256(target) != meta["sha256"]:
            cached = hf_hub_download(manifest["repo_id"], name, revision=manifest["revision"])
            shutil.copyfile(cached, target)
        digest = sha256(target)
        if digest != meta["sha256"]:
            print(f"hash mismatch for {name}: {digest}", file=sys.stderr)
            return 1
        print(f"ok  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
