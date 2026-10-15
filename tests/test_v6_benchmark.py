"""Engineering comparison tests with fixtures only; never GPU speed evidence."""

import copy
import json
from dataclasses import asdict

import pytest

from mb import v6_benchmark as bench
from mb.v6_contract import RuntimeSpec, canonical_digest
from mb.v6_run import SyntheticBackend


class FixtureArchive:
    def __init__(self, *args):
        self.index = {}

    def __call__(self, event):
        self.index[str(event["sequence"])] = event["digest"]

    def load(self, name):
        return self.index[name]


def run_fixture(path, case="full_with_text", **kwargs):
    profile = bench.PROFILES[0]
    return bench.run_case(SyntheticBackend(), profile, case, bench.materials(profile)[case], path,
        check=kwargs.get("check", lambda: None), synchronize=kwargs.get("synchronize", lambda: None),
        archive_factory=FixtureArchive, spec=RuntimeSpec(work_tokens=2, preparation_tokens=1, window=2, gain=1.))


def test_prepare_is_inert_and_cannot_overwrite(tmp_path):
    package = bench.prepare(tmp_path / "package")
    assert package["paid_launch_authorized"] is package["formal_authorized"] is False
    assert package["automatic_formal_continuation"] is False
    assert package["proposed_incremental_cap_usd"] == 8.
    assert set(package["models"]) == set(bench.PROFILES)
    saved = json.loads((tmp_path / "package/package.json").read_text())
    for profile in bench.PROFILES:
        bench.validate_materials(profile, saved["models"][profile])
    changed = copy.deepcopy(saved["models"][bench.PROFILES[0]])
    changed.pop("baseline")
    with pytest.raises(ValueError):
        bench.validate_materials(bench.PROFILES[0], changed)
    with pytest.raises(FileExistsError):
        bench.prepare(tmp_path / "package")


def test_fixed_materials_are_deterministic_and_engineering_only():
    hashes = []
    for profile in bench.PROFILES:
        value = bench.materials(profile)
        assert value == bench.materials(profile)
        for name in bench.CASES:
            task = value[name] if name == "full_with_text" else value[name]["task"]
            assert "performance_only" in task["episode_id"]
            hashes.append(canonical_digest(task))
    assert len(set(hashes)) == 6
    with pytest.raises(ValueError):
        bench.materials("unapproved-model")


def test_trace_is_observational_and_restored_on_failure():
    backend = SyntheticBackend()
    before = dict(backend.__dict__)
    state = backend.create("System", "User")
    with bench.trace_backend(backend, lambda: None) as trace:
        backend.step(state, (), 1.)
        backend.probe(state, "Pick", ("1", "2", "3", "4"), (), 1.)
    assert trace["calls"] == {"step": 1, "probe": 1}
    assert len(trace["sha256"]) == 64 and backend.__dict__ == before
    with pytest.raises(RuntimeError):
        with bench.trace_backend(backend, lambda: None):
            raise RuntimeError("failure")
    assert backend.__dict__ == before


def test_full_case_compares_outputs_trace_and_all_archives(tmp_path):
    a, b = run_fixture(tmp_path / "a"), run_fixture(tmp_path / "b")
    assert a["readout_count"] == 352 and a["restored_archives"] == 16
    assert a["backend_kind"] == "synthetic_fixture" and a["native_model_identity"] is None
    assert bench.compare_cases(a, b)["exact"]
    b["trace"]["sha256"] = "0" * 64
    with pytest.raises(bench.ComparisonMismatch) as error:
        bench.compare_cases(a, b)
    assert error.value.evidence["reference_sha256"] != error.value.evidence["candidate_sha256"]
    rows = [json.loads(line) for line in (tmp_path / "a/engineering_rows.jsonl").read_text().splitlines()]
    assert all(row["scientific_data"] is False and row["purpose"] == "engineering_only" for row in rows)


def test_expiry_after_last_synchronization_cannot_emit_success(tmp_path):
    expired, syncs = False, 0
    def sync():
        nonlocal expired, syncs
        syncs += 1
        expired = syncs >= 2
    def check():
        if expired:
            raise TimeoutError("engineering lease expired")
    path = tmp_path / "expiry"
    with pytest.raises(TimeoutError):
        run_fixture(path, "baseline", check=check, synchronize=sync)
    assert not (path / "summary.json").exists()
    assert json.loads((path / "failure.json").read_text())["error_type"] == "TimeoutError"
    assert "engineering lease expired" in (path / "failure_traceback.txt").read_text()
    assert (path / "engineering_rows.jsonl").stat().st_size > 0


def test_attempt_never_appends_to_an_existing_directory(tmp_path):
    path = tmp_path / "previous"
    path.mkdir()
    (path / "identity.json").write_text("preserve")
    with pytest.raises(FileExistsError):
        run_fixture(path, "baseline")
    assert sorted(p.name for p in path.iterdir()) == ["identity.json"]
    assert (path / "identity.json").read_text() == "preserve"


def test_failure_to_save_evidence_does_not_mask_original_error(tmp_path, monkeypatch):
    @bench.preserve_failure
    def failing(directory):
        directory.mkdir()
        raise TimeoutError("original deadline failure")
    def cannot_write(*args, **kwargs):
        raise OSError("disk unavailable")
    monkeypatch.setattr(bench, "write_new", cannot_write)
    with pytest.raises(TimeoutError, match="original deadline failure") as error:
        failing(tmp_path / "attempt")
    assert "could not be persisted" in error.value.__notes__[0]


class ArchiveFixture(SyntheticBackend):
    def dump_state(self, state):
        return {"state": copy.deepcopy(state), "sha256": self.digest(state)}

    def load_state(self, value):
        return copy.deepcopy(value["state"])


def test_short_comparison_logs_progress_and_rejects_difference():
    progress = []
    result = bench.micro_compare(ArchiveFixture(), ArchiveFixture(), check=lambda: None,
                                progress=progress.append)
    assert result["passed"] and len(result["cases"]) == 4
    assert sum(row["event"] == "gain_passed" for row in progress) == 4
    class Different(ArchiveFixture):
        def probe(self, *args, **kwargs):
            result = super().probe(*args, **kwargs)
            result.probability = .6
            return result
    progress.clear()
    with pytest.raises(bench.ComparisonMismatch):
        bench.micro_compare(ArchiveFixture(), Different(), check=lambda: None, progress=progress.append)
    assert progress[0] == {"event": "gain_started", "gain": 0.}
    assert sum(row["event"] == "backend_complete" for row in progress) == 2
    assert not any(row["event"] == "gain_passed" for row in progress)


def measured_fixture():
    """Mock receipts for arithmetic validation, never measured native data."""
    result = {}
    for profile in bench.PROFILES:
        candidate = {}
        for name, seconds in zip(bench.CASES, (100., 5., 20.)):
            candidate[name] = {"profile": profile, "case": name,
                "material_sha256": canonical_digest(bench.materials(profile)[name]),
                "readout_count": 352 if name == "full_with_text" else 100,
                "records_sha256": "a" * 64, "archive_events_sha256": "b" * 64,
                "restored_archives": 16 if name == "full_with_text" else 0, "trace": {"sha256": "c" * 64},
                "elapsed_seconds": seconds, "text_seconds": 10. if name == "full_with_text" else 0.,
                "bytes": 1000, "status": "complete", "backend_kind": "native",
                "native_model_identity": "d" * 64, "source_manifest_sha256": "e" * 64,
                "runtime": asdict(RuntimeSpec(gain=0. if name == "baseline" else 1.))}
        reference = copy.deepcopy(candidate)
        for row in reference.values():
            row["elapsed_seconds"] *= 1.1
        comparisons = [bench.compare_cases(reference[name], candidate[name]) for name in bench.CASES]
        result[profile] = {"status": "complete", "profile": profile, "formal_authorized": False,
            "backend_kind": "native", "pinned_native_identity_verified": True,
            "micro": {"passed": True, "exact": True, "cases": [
                {"gain": gain, "comparison_sha256": "f" * 64} for gain in (0., .25, .5, 1.)]},
            "native_model_identity": "d" * 64,
            "source_manifest_sha256": "e" * 64, "comparisons": comparisons,
            "summaries": {"reference": reference, "candidate": candidate}}
    return result


def forecast(value):
    return bench.project(value, hourly_usd=1.6, observed_transfer_bytes_per_second=1000.,
                         transfer_usd_per_tb=10., setup_seconds_per_stage=0., backup_fixed_seconds_per_stage=0.)


def test_forecast_covers_both_models_and_all_remaining_stages():
    value = forecast(json.loads(json.dumps(measured_fixture())))
    assert value["forecast_only"] and value["formal_authorized"] is False
    assert value["models"][bench.PROFILES[0]]["illustrative_compute_hours"] == pytest.approx(26500 / 3600)
    assert value["models"][bench.PROFILES[0]]["conservative_compute_hours"] == pytest.approx(66450 / 3600)
    assert len(value["limitations"]) == 5


@pytest.mark.parametrize("fault", ("missing_model", "synthetic", "no_micro", "reference_different",
    "source_different", "wrong_material", "short_clock", "forged_comparison", "negative_time", "text_time",
    "cross_model_source", "missing_gain", "reference_incomplete", "reference_nan"))
def test_forecast_refuses_incomplete_unbound_or_synthetic_evidence(fault):
    value = measured_fixture()
    entry = value[bench.PROFILES[0]]
    row = entry["summaries"]["candidate"]["full_with_text"]
    if fault == "missing_model":
        del value[bench.PROFILES[1]]
    elif fault == "synthetic":
        row["backend_kind"] = "synthetic_fixture"
    elif fault == "no_micro":
        del entry["micro"]
    elif fault == "reference_different":
        entry["summaries"]["reference"]["full_with_text"]["records_sha256"] = "x" * 64
    elif fault == "source_different":
        row["source_manifest_sha256"] = "x" * 64
    elif fault == "wrong_material":
        row["material_sha256"] = "x" * 64
    elif fault == "short_clock":
        row["runtime"]["work_tokens"] = 4
    elif fault == "forged_comparison":
        entry["comparisons"][0]["reference_seconds"] += 1
    elif fault == "negative_time":
        row["elapsed_seconds"] = -1
    elif fault == "cross_model_source":
        other = value[bench.PROFILES[1]]
        other["source_manifest_sha256"] = "f" * 64
        for implementation in other["summaries"].values():
            for case in implementation.values():
                case["source_manifest_sha256"] = "f" * 64
    elif fault == "missing_gain":
        entry["micro"]["cases"].pop()
    elif fault == "reference_incomplete":
        entry["summaries"]["reference"]["full_with_text"]["status"] = "failed"
    elif fault == "reference_nan":
        entry["summaries"]["reference"]["full_with_text"]["elapsed_seconds"] = float("nan")
    else:
        row["text_seconds"] = row["elapsed_seconds"] + 1
    with pytest.raises(ValueError):
        forecast(value)
