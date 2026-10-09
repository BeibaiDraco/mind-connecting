"""Run the frozen native GPU tests for one checkpoint, with durable evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform

from mb import ledger, run
from mb.model_profiles import QWEN, LLAMA31, resolve_profile

ROOT = Path(__file__).resolve().parents[1]
TESTS = {QWEN.key: ("tests/test_runtime.py", 17), LLAMA31.key: ("tests/test_llama_acceptance.py", 8)}


class Evidence:
    def __init__(self, path: Path, profile: str):
        self.path = path
        test_file, expected = TESTS[profile]
        self.doc = {"model_profile": profile, "source_hash": run.source_hash(),
                    "tokenizer_manifest_sha256": ledger.file_sha256(resolve_profile(profile).manifest_path),
                    "test_file": test_file, "test_sha256": ledger.file_sha256(ROOT / test_file),
                    "expected": expected, "collected": 0, "reports": [], "status": "running"}
        self.save()

    def save(self):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.doc, indent=2) + "\n")
        temporary.replace(self.path)

    def pytest_collection_finish(self, session):
        self.doc["collected"] = len(session.items)
        self.save()

    def pytest_runtest_logreport(self, report):
        self.doc["reports"].append({"nodeid": report.nodeid, "when": report.when, "outcome": report.outcome})
        self.save()

    def finish(self, code):
        calls = [r for r in self.doc["reports"] if r["when"] == "call"]
        passed = (code == 0 and self.doc["collected"] == self.doc["expected"] == len(calls)
                  and all(r["outcome"] == "passed" for r in self.doc["reports"]))
        self.doc.update(status="passed" if passed else "failed", exit_code=int(code))
        self.save()
        return passed


def verify(path: Path, profile: str) -> dict:
    doc = json.loads(path.read_text())
    test_file, expected = TESTS[profile]
    calls = [r for r in doc.get("reports", []) if r.get("when") == "call"]
    if (doc.get("model_profile") != profile or doc.get("source_hash") != run.source_hash()
            or doc.get("tokenizer_manifest_sha256") != ledger.file_sha256(resolve_profile(profile).manifest_path)
            or doc.get("test_file") != test_file or doc.get("test_sha256") != ledger.file_sha256(ROOT / test_file)
            or doc.get("status") != "passed" or doc.get("exit_code") != 0
            or doc.get("expected") != expected or doc.get("collected") != expected or len(calls) != expected
            or len({r.get("nodeid") for r in calls}) != expected
            or any(r.get("outcome") != "passed" for r in doc.get("reports", []))):
        raise ValueError("native GPU acceptance is absent, stale, skipped or failed")
    return doc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-profile", choices=TESTS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if platform.system() != "Linux":
        parser.error("native acceptance runs only on the rented Linux GPU host")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    import torch
    import pytest
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        parser.error("native BF16 CUDA GPU required")
    resolve_profile(args.model_profile).validate_manifest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x"):
        pass
    evidence = Evidence(args.output, args.model_profile)
    result = pytest.main([str(ROOT / TESTS[args.model_profile][0]), "-m", "gpu", "-q", "-x"], plugins=[evidence])
    return 0 if evidence.finish(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
