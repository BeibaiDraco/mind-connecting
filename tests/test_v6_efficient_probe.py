"""Feasibility preparation and reporting only; no torch/model/GPU invocation."""

import copy
import json
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest

from mb import v6_efficient_probe as probe


def test_preparation_is_bound_inert_and_write_once(tmp_path):
    package = probe.prepare(tmp_path / "plan", "compiled_flex")
    probe.validate_package(json.loads((tmp_path / "plan/package.json").read_text()))
    assert package["formal_authorized"] is package["paid_launch_authorized"] is False
    assert package["scientific_admission"] is package["whole_experiment_forecast_allowed"] is False
    assert len(package["operator_cases"]) == 16
    with pytest.raises(FileExistsError):
        probe.prepare(tmp_path / "plan", "compiled_flex")


@pytest.mark.parametrize("key,value", [("kernel", "auto"), ("seed", 1),
    ("engineering_max_abs_over_value_scale", 1.), ("source_sha256", {}),
    ("formal_authorized", True), ("operator_cases", []), ("timing_repeats", 1)])
def test_tampered_plan_refused(tmp_path, key, value):
    package = probe.prepare(tmp_path / "plan", "efficient_sdpa")
    changed = copy.deepcopy(package)
    changed[key] = value
    with pytest.raises(ValueError):
        probe.validate_package(changed)


def test_default_execution_and_expired_lease_refuse_before_cuda_or_output(tmp_path):
    package = probe.prepare(tmp_path / "plan", "compiled_flex")
    with pytest.raises(PermissionError):
        probe.run_operator_probe(package, tmp_path / "attempt", check=lambda: None)
    assert not (tmp_path / "attempt").exists()
    def expired():
        raise TimeoutError("expired")
    with pytest.raises(TimeoutError):
        probe.run_operator_probe(package, tmp_path / "attempt", check=expired, hardware_authorized=True)
    assert not (tmp_path / "attempt").exists()


def test_engineering_ceiling_never_confers_admission():
    target = np.zeros(4)
    good = probe.error_screen(target, target + 2**-8, (np.ones(4),))
    bad = probe.error_screen(target, target + .01, (np.ones(4),))
    zero = probe.error_screen(target, target, (target,))
    assert good["engineering_screen_pass"] and zero["engineering_screen_pass"]
    assert not bad["engineering_screen_pass"]
    assert all(report["admitted"] is False for report in (good, bad, zero))


def test_covering_set_contains_all_required_dimensions():
    cases = probe.layouts()
    assert {x.batch for x in cases} == {1, 2, 4, 8}
    assert {x.queries for x in cases} == {1, 2, 4}
    assert {x.foreign for x in cases} == {0, 1, 16}
    assert {x.gain for x in cases} == {0., .25, .5, 1.}


def fake_runtime(monkeypatch):
    api = SimpleNamespace(bfloat16="fixture", no_grad=nullcontext,
        tensor=lambda values, **kwargs: np.asarray(values, dtype=np.float32))
    monkeypatch.setitem(sys.modules, "torch", api)
    monkeypatch.setattr(probe, "runtime_environment", lambda kernel: {"fixture": True, "kernel": kernel})


def test_failed_case_retains_partial_progress_and_never_overwrites(tmp_path, monkeypatch):
    fake_runtime(monkeypatch)
    package = probe.prepare(tmp_path / "plan", "compiled_flex")
    def fail(layout, values, kernel, check, evidence, emit, order_offset):
        emit({"phase": "candidate_numeric", "error": .001})
        emit({"phase": "timing_sample", "seconds": .2})
        raise TimeoutError("injected late lease expiry")
    monkeypatch.setattr(probe, "inspect_case", fail)
    target = tmp_path / "attempt"
    with pytest.raises(TimeoutError):
        probe.run_operator_probe(package, target, check=lambda: None, hardware_authorized=True)
    progress = target / "case-000-evidence/progress.jsonl"
    assert len(progress.read_text().splitlines()) == 2
    assert json.loads((target / "failure.json").read_text())["error_type"] == "TimeoutError"
    before = progress.read_bytes()
    with pytest.raises(FileExistsError):
        probe.run_operator_probe(package, target, check=lambda: None, hardware_authorized=True)
    assert progress.read_bytes() == before and not (target / "summary.json").exists()


def test_numeric_failure_and_last_check_cannot_emit_success(tmp_path, monkeypatch):
    fake_runtime(monkeypatch)
    package = probe.prepare(tmp_path / "plan", "compiled_flex")
    monkeypatch.setattr(probe, "inspect_case", lambda *args: {"status": "failed", "scientific_admission": False})
    with pytest.raises(ValueError, match="screen failed"):
        probe.run_operator_probe(package, tmp_path / "numeric", check=lambda: None, hardware_authorized=True)
    assert (tmp_path / "numeric/case-000.json").exists()
    monkeypatch.setattr(probe, "inspect_case", lambda *args: {"status": "engineering_screen_pass"})
    calls = 0
    def expires_last():
        nonlocal calls
        calls += 1
        if calls == 2 + 2 * len(probe.layouts()):
            raise TimeoutError("expiry at final boundary")
    with pytest.raises(TimeoutError):
        probe.run_operator_probe(package, tmp_path / "expired", check=expires_last, hardware_authorized=True)
    assert not (tmp_path / "expired/summary.json").exists()


def test_paired_timing_alternates_and_preserves_pre_expiry_samples(monkeypatch):
    fake = SimpleNamespace(cuda=SimpleNamespace(synchronize=lambda: None), isfinite=np.isfinite)
    monkeypatch.setitem(sys.modules, "torch", fake)
    observed, events = [], []
    functions = {name: (lambda n=name: observed.append(n) or np.ones(1)) for name in ("candidate", "reference")}
    result = probe.paired_timing(functions, lambda: None, events.append, 0)
    assert observed == ["candidate", "reference", "reference", "candidate", "candidate", "reference",
                        "reference", "candidate", "candidate", "reference"]
    assert len(events) == 10 and all(len(row["seconds"]) == 5 for row in result.values())
    events.clear()
    def expire_after_sample():
        if events:
            raise TimeoutError("expired after measured call")
    with pytest.raises(TimeoutError):
        probe.paired_timing(functions, expire_after_sample, events.append, 0)
    assert len(events) == 1 and events[0]["seconds"] >= 0
