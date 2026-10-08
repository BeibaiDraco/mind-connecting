#!/usr/bin/env python3
"""Run only the pinned Llama GPU contract tests, offline, with durable evidence.

Weights and verified tokenizer assets must already exist. This is a correctness
checkpoint, not baseline suitability, throughput certification, or research data.
The caller supervises the approved compute/time budget.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Evidence:
    def __init__(self, output: Path, metadata: dict):
        self.path = output / "acceptance.json"
        self.data = {**metadata, "status": "running", "consumable": False,
                     "purpose": "engineering correctness only", "collected": 0, "reports": []}
        self.started = time.monotonic()
        self.save()

    def save(self) -> None:
        self.data["elapsed_seconds"] = time.monotonic() - self.started
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n")
        temporary.replace(self.path)

    def pytest_collection_finish(self, session) -> None:
        self.data["collected"] = len(session.items)
        self.save()

    def pytest_runtest_logreport(self, report) -> None:
        self.data["reports"].append({"nodeid": report.nodeid, "phase": report.when,
                                     "outcome": report.outcome, "duration_seconds": report.duration,
                                     "properties": dict(report.user_properties),
                                     "failure": str(report.longrepr) if report.failed else None})
        self.save()

    def finish(self, exit_code: int) -> bool:
        calls = [r for r in self.data["reports"] if r["phase"] == "call" and r["outcome"] == "passed"]
        passed = (exit_code == 0 and self.data["collected"] == 8 and len(calls) == 8
                  and all(r["outcome"] == "passed" for r in self.data["reports"]))
        self.data.update(status="passed" if passed else "failed", pytest_exit_code=int(exit_code))
        self.save()
        return passed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="new directory for JSON/JUnit evidence; existing paths are refused")
    args = parser.parse_args(argv)
    if platform.system() != "Linux":
        parser.error("real-model acceptance runs only on the Linux GPU host")
    # Set before importing Transformers/Hub. Authentication and network downloads
    # belong to the separately authorized asset-fetch step, not to acceptance.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    import pytest
    from mb import chat
    from mb.model_profiles import LLAMA31

    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        parser.error("a CUDA GPU with native BF16 support is required; skips cannot pass acceptance")
    LLAMA31.validate_manifest()
    chat.load_tokenizer(profile=LLAMA31)
    source_paths = ["src/mb/runtime.py", "src/mb/bridge.py", "src/mb/chat.py", "src/mb/conditions.py",
                    "src/mb/model_profiles.py", "src/mb/tasks.py", "src/mb/run.py",
                    "tests/test_llama_acceptance.py", "scripts/check_llama_acceptance.py",
                    "docs/reviews/v4_padding_acceptance_2026-10-08.md"]
    metadata = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "profile": LLAMA31.identity(), "tokenizer_manifest_sha256": _hash(LLAMA31.manifest_path),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: _hash(ROOT / name) for name in source_paths},
        "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name)
                     for name in ("torch", "transformers", "tokenizers", "huggingface-hub", "pytest")},
        "gpu": torch.cuda.get_device_name(), "gpu_total_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
        "cuda_version": torch.version.cuda,
        "numerical_contract": {
            "version": "llama-native-matched-shape-v2",
            "same_shape": "bitwise equality with unhooked native SDPA logits and every cached K/V tensor",
            "cross_shape": "runtime discrepancy equals native discrepancy bitwise; raw difference is diagnostic",
            "cross_shape_top1": "agreement and margin are diagnostic; the former margin>0.5 equality gate is replaced",
            "same_shape_top1": "exact equality follows from bitwise identical logits",
            "padding": "masked pad-ID changes must leave logits bitwise unchanged at prefill and cached ticks",
            "precision": "BF16 unchanged; independent FP32 diagnostic is documented separately",
            "correction_record": "docs/reviews/v4_padding_acceptance_2026-10-08.md",
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    evidence = Evidence(args.output_dir, metadata)
    torch.cuda.reset_peak_memory_stats()
    result = pytest.main([str(ROOT / "tests/test_llama_acceptance.py"), "-m", "gpu", "-v", "-x",
                          "--tb=short", "-o", "junit_family=legacy",
                          f"--junitxml={args.output_dir / 'junit.xml'}"], plugins=[evidence])
    torch.cuda.synchronize()
    evidence.data["peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
    evidence.data["peak_reserved_bytes"] = torch.cuda.max_memory_reserved()
    passed = evidence.finish(int(result))
    print(f"Llama acceptance {'PASSED' if passed else 'FAILED'}: {evidence.path}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
