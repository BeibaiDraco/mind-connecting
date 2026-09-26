"""Offline tests for scripts/run_chain.sh: a failed stage or failed tests stop the chain with ABORT."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Stands in for python: "-m pytest ..." passes unless FAIL_TESTS is set; "-m mb.run CFG" records CFG
# and fails for configs whose name contains "fail".
FAKE_PY = """#!/usr/bin/env bash
if [ "$2" = pytest ]; then [ -z "${FAIL_TESTS:-}" ]; exit $?; fi
case "$1" in *freeze_protocol.py) [ -z "${FAIL_VERIFY:-}" ]; exit $? ;; esac
echo "$3" >> "$TRACE"
case "$3" in *fail*) exit 3 ;; esac
exit 0
"""


def _chain(tmp_path: Path, *configs: str, **env: str) -> tuple[int, str, list[str]]:
    fake = tmp_path / "fake_py"
    fake.write_text(FAKE_PY)
    fake.chmod(0o755)
    log, trace = tmp_path / "chain.log", tmp_path / "trace.txt"
    full_env = {**os.environ, "PY": str(fake), "TRACE": str(trace), "MB_ENV": str(tmp_path / "none"), **env}
    rc = subprocess.run(["bash", str(ROOT / "scripts" / "run_chain.sh"), str(log), *configs], env=full_env).returncode
    ran = trace.read_text().split() if trace.exists() else []
    return rc, log.read_text(), ran


def test_chain_runs_every_stage(tmp_path):
    rc, log, ran = _chain(tmp_path, "a.yaml", "b.yaml")
    assert rc == 0 and ran == ["a.yaml", "b.yaml"]
    assert "END a.yaml exit=0" in log and "ALL DONE" in log and "ABORT" not in log


def test_failed_stage_stops_the_chain(tmp_path):
    rc, log, ran = _chain(tmp_path, "a.yaml", "fail.yaml", "c.yaml")
    assert rc == 3 and ran == ["a.yaml", "fail.yaml"]
    assert "END fail.yaml exit=3" in log and "ABORT: fail.yaml exit=3" in log and "ALL DONE" not in log


def test_failed_tests_stop_before_any_stage(tmp_path):
    rc, log, ran = _chain(tmp_path, "a.yaml", FAIL_TESTS="1")
    assert rc != 0 and ran == [] and "ABORT: offline tests failed" in log


def test_freeze_check_runs_before_each_stage(tmp_path):
    rc, log, ran = _chain(tmp_path, "a.yaml", FREEZE_VERSION="v3", FAIL_VERIFY="1")
    assert rc != 0 and ran == [] and "ABORT: freeze verification failed before a.yaml" in log
    rc, log, ran = _chain(tmp_path, "b.yaml", FREEZE_VERSION="v3")
    assert rc == 0 and ran == ["b.yaml"]
