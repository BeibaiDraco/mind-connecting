"""Opt-in real-checkpoint acceptance under the same production financial admission.

These tests are not run on the local Mac. No environment pointer means a skip;
providing pointers does not bypass PI approval, live guards or pinned source.
"""
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.gpu


def test_real_pinned_checkpoint_acceptance_and_readonly_receipt():
    plan_path = os.environ.get("MB_V6_ACCEPTANCE_PLAN")
    admission_path = os.environ.get("MB_V6_ACCEPTANCE_ADMISSION")
    if not plan_path or not admission_path:
        pytest.skip("explicit admitted acceptance plan and current proof are required")
    from mb import v6_execution as execution
    plan = execution._plan(Path(plan_path), Path(admission_path))
    assert plan["stage"] == "acceptance" and plan["n"] == 1
    assert not Path(plan["output_dir"]).exists(), "Acceptance test requires a fresh authorized output directory"
    result = execution.execute(plan_path, admission_path)
    assert result["backend_kind"] == "native" and result["scientific_data"] is False
    run = Path(plan["output_dir"])
    acceptance = execution.read_json(run/"acceptance.json")
    assert acceptance["checks"] == {name: True for name in execution.NATIVE_CHECKS}
    assert acceptance["foreign_attention_metrics"]["layers"] > 0
    assert acceptance["forced_tokens_engineering_only"] is True
    assert acceptance["peak_allocated_bytes"] > 0
    before = {str(p.relative_to(run)): execution.file_sha256(p) for p in run.rglob("*") if p.is_file()}
    bundle = execution.read_native_run(run)
    assert bundle["native_identity"]["native_model_identity"] == acceptance["native_model_identity"]
    after = {str(p.relative_to(run)): execution.file_sha256(p) for p in run.rglob("*") if p.is_file()}
    assert before == after
