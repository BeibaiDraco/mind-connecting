#!/usr/bin/env python3
"""Fetch and validate a profile's official tokenizer assets without loading a model.

Uses Hugging Face's existing authentication mechanism; accepts no credential
arguments and never prints credentials. Weight downloads are opt-in and require
an explicitly declared remote Linux NVIDIA GPU environment. No torch import.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download, snapshot_download
from huggingface_hub.utils import disable_progress_bars

from mb import chat
from mb.model_profiles import LLAMA31, PROFILES, REQUIRED_ASSETS, ModelProfile, REPO_ROOT, resolve_profile

OPTIONAL_ASSETS = ("special_tokens_map.json", "added_tokens.json", "chat_template.jinja")


def require_remote_gpu(explicit_remote: bool) -> None:
    if not explicit_remote or platform.system() != "Linux":
        raise ValueError("weight download requires --remote-gpu on the rented Linux GPU host")
    probe = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                           capture_output=True, text=True, check=True, timeout=15)
    if not probe.stdout.strip():
        raise ValueError("no NVIDIA GPU is visible on this host")


def verify_assets(profile: ModelProfile) -> None:
    profile.validate_manifest()
    tok = chat.load_tokenizer(profile=profile)
    chat.require_verified_tokenizer(tok, profile)


def fetch_assets(profile: ModelProfile) -> None:
    root, manifest_path = profile.tokenizer_dir, profile.manifest_path
    if root.exists() or manifest_path.exists():
        # A partial or mismatched directory is evidence to inspect, not something
        # this script is allowed to overwrite or bless by hashing it afresh.
        verify_assets(profile)
        return
    files = set(HfApi().list_repo_files(profile.repo_id, revision=profile.revision, repo_type="model"))
    missing = set(REQUIRED_ASSETS) - files
    if missing:
        raise ValueError(f"official pinned repository is missing required assets: {sorted(missing)}")
    names = [*REQUIRED_ASSETS, *(name for name in OPTIONAL_ASSETS if name in files)]
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".model-assets-", dir=root.parent) as temporary:
        stage = Path(temporary) / "tokenizer"
        stage.mkdir()
        entries = {}
        for name in names:
            cached = Path(hf_hub_download(profile.repo_id, name, revision=profile.revision, repo_type="model"))
            payload = cached.read_bytes()
            (stage / name).write_bytes(payload)
            entries[name] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                             "source": f"https://huggingface.co/{profile.repo_id}/resolve/{profile.revision}/{name}"}
        manifest = {"repo_id": profile.repo_id, "revision": profile.revision,
                    "local_dir": str(root.relative_to(REPO_ROOT)), "files": entries}
        staged_manifest = Path(temporary) / "manifest.json"
        staged_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
        profile.validate_manifest(staged_manifest, stage)
        tok = chat.load_tokenizer(str(stage), profile=profile, manifest_path=staged_manifest)
        chat.require_verified_tokenizer(tok, profile)
        if root.exists() or manifest_path.exists():
            raise FileExistsError("model assets appeared during validation; refusing to overwrite")
        # Both sources were fetched at the pinned revision and passed the native
        # tokenizer contract before they become the profile's default assets.
        stage.rename(root)
        with manifest_path.open("x") as output:
            output.write(staged_manifest.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), default=LLAMA31.key)
    parser.add_argument("--verify-only", action="store_true", help="validate existing assets without network access")
    parser.add_argument("--download-weights", action="store_true", help="also populate the HF cache on the GPU host")
    parser.add_argument("--remote-gpu", action="store_true", help="explicitly affirm execution on the rented GPU host")
    args = parser.parse_args()
    if args.verify_only and args.download_weights:
        parser.error("--verify-only cannot be combined with --download-weights")
    profile = resolve_profile(args.profile)
    disable_progress_bars()
    try:
        if args.download_weights:
            require_remote_gpu(args.remote_gpu)
        if args.verify_only:
            verify_assets(profile)
        else:
            fetch_assets(profile)
        if args.download_weights:
            # The cache is also used by runtime.load_model's pinned from_pretrained
            # call; downloaded weights are never placed in this repository.
            snapshot_download(profile.repo_id, revision=profile.revision, repo_type="model",
                              allow_patterns=["*.safetensors", "*.safetensors.index.json", "config.json",
                                              "generation_config.json"])
    except Exception as exc:
        # Library exceptions can include request details. Keep credentials and
        # authentication response bodies out of shared terminal logs.
        parser.exit(1, f"Asset preparation failed ({type(exc).__name__}). Check official access, pinned files, "
                       "and the local validation requirements; no model was run.\n")
    print(f"Validated tokenizer assets: {profile.key} at {profile.revision}")
    if args.download_weights:
        print("Official weights downloaded to the Hugging Face cache; no model was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
