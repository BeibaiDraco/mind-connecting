"""Engineering-only comparison and workload forecast; never scientific admission.

This module does not rent/start hardware or authorize a paid run. Its executor
requires a separately admitted deadline/lease callback and an already loaded
native backend. The public preparation command never loads torch or a model.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import traceback
import inspect
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Iterator

from mb import v6_neutral as neutral
from mb import v6_tasks as tasks
from mb.model_profiles import LLAMA31, QWEN, resolve_profile
from mb.v6_contract import RuntimeSpec, canonical_digest
from mb.v6_performance import PerformanceBackend, profile_backend
from mb.v6_run import NativeArchiveWriter, source_manifest
from mb.v6_runtime import EpisodeRunner

VERSION = "v6-engineering-comparison-1"
PROFILES = (QWEN.key, LLAMA31.key)
CASES = ("full_with_text", "baseline", "calibration")
GAIN = 1.0


def materials(profile: str) -> dict:
    if profile not in PROFILES:
        raise ValueError("Only the two approved pinned profiles may be compared")
    namespace = f"performance_only_20261014_{profile}"
    full = tasks.make_episodes(1, stage=namespace, seed=208741)[0]
    baseline = neutral.make_episodes(1, "baseline", seed=208742, namespace=namespace)[0]
    calibration = neutral.make_episodes(1, "calibration", seed=208743, namespace=namespace)[0]
    return {"full_with_text": tasks.episode_to_dict(full),
            "baseline": neutral.episode_to_dict(baseline),
            "calibration": neutral.episode_to_dict(calibration)}


def prepare(directory: Path) -> dict:
    """Write an inert reviewable package; no paid authority is created."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    values = {profile: materials(profile) for profile in PROFILES}
    package = {"version": VERSION, "purpose": "engineering_only",
               "scientific_data": False, "formal_authorized": False,
               "paid_launch_authorized": False, "source_manifest": source_manifest(),
               "models": values, "runtime": asdict(RuntimeSpec(gain=GAIN)),
               "order": {PROFILES[0]: ["reference", "candidate"],
                         PROFILES[1]: ["candidate", "reference"]},
               "small_comparison_gains": [0.0, 0.25, 0.5, 1.0],
               "stopping_rule": "any exact mismatch or technical/budget/lease failure",
               "proposed_incremental_cap_usd": 8.0,
               "proposed_lifecycle_limit_seconds": 14400,
               "hourly_cap_usd": 1.6, "cumulative_total_cap_usd": 100.0,
               "allowance_status": "pending_PI_amendment_of_initial_acceptance_boundary",
               "forecast_only": True, "automatic_formal_continuation": False}
    write_new(directory / "package.json", package)
    return package


def write_new(path: Path, value: Any) -> None:
    with Path(path).open("x") as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


class ComparisonMismatch(ValueError):
    def __init__(self, label: str, reference_sha256: str, candidate_sha256: str):
        super().__init__(f"Exact engineering comparison failed: {label}")
        self.evidence = {"label": label, "reference_sha256": reference_sha256,
                         "candidate_sha256": candidate_sha256}


def preserve_failure(function: Any) -> Any:
    """Retain failures only in a newly created attempt; never modify old attempts."""
    @wraps(function)
    def call(*args: Any, **kwargs: Any) -> Any:
        directory = Path(inspect.signature(function).bind(*args, **kwargs).arguments["directory"])
        existed = directory.exists()
        try:
            return function(*args, **kwargs)
        except BaseException as exc:
            if not existed and directory.is_dir():
                try:
                    write_new(directory / "failure.json", {"version": VERSION, "status": "failed",
                        "phase": function.__name__, "error_type": type(exc).__name__,
                        "comparison": getattr(exc, "evidence", None), "at_epoch": time.time(),
                        "scientific_data": False, "formal_authorized": False})
                    with (directory / "failure_traceback.txt").open("x") as handle:
                        handle.write(traceback.format_exc())
                        handle.flush(); os.fsync(handle.fileno())
                except OSError as evidence_error:
                    exc.add_note(f"Failure evidence could not be persisted: {type(evidence_error).__name__}")
            raise
    return call


def require_equal(reference: Any, candidate: Any, label: str) -> str:
    left, right = canonical_digest(reference), canonical_digest(candidate)
    if left != right:
        raise ComparisonMismatch(label, left, right)
    return left


@contextmanager
def trace_backend(backend: Any, check: Callable[[], None]) -> Iterator[dict]:
    """Hash all generated exports and sealed readouts; expose no effect values."""
    digest = hashlib.sha256()
    counts: Counter = Counter()
    previous: dict = {}
    missing = object()
    result: dict = {}

    def wrap(name: str, method: Any) -> Any:
        def call(*args: Any, **kwargs: Any) -> Any:
            check()
            value = method(*args, **kwargs)
            check()
            counts[name] += 1
            if name == "_consume":
                return value
            if name == "step":
                payload = value.identity()
            elif name == "commit_answer":
                payload = {"state_sha256": backend.digest(value)}
            else:
                seal = getattr(value.state, "seal_checksum", None)
                payload = {"token": value.token, "probability": value.probability,
                           "legal_logits": value.legal_logits, "legal_mass": value.legal_mass,
                           "token_ids": value.token_ids, "sealed_state_sha256": seal}
                if getattr(backend, "kind", None) != "synthetic_fixture" and not seal:
                    raise ValueError("Native probe lacks its sealed-state digest")
            raw = json.dumps([name, payload], sort_keys=True, allow_nan=False).encode()
            digest.update(len(raw).to_bytes(8, "big")); digest.update(raw)
            check()
            return value
        return call

    try:
        for name in ("step", "probe", "commit_answer", "_consume"):
            if not hasattr(backend, name):
                continue
            previous[name] = backend.__dict__.get(name, missing)
            setattr(backend, name, wrap(name, getattr(backend, name)))
        yield result
    finally:
        for name, old in previous.items():
            if old is missing:
                delattr(backend, name)
            else:
                setattr(backend, name, old)
        result.update(sha256=digest.hexdigest(), calls=dict(counts))


def micro_compare(reference: Any, candidate: Any, *, check: Callable[[], None],
                  progress: Callable[[dict], None] = lambda value: None) -> dict:
    """Stop before costly complete episodes if the candidate changes any value."""
    def call(method: Any, *args: Any, **kwargs: Any) -> Any:
        check()
        result = method(*args, **kwargs)
        check()
        return result
    outcomes = []
    for gain in (0., .25, .5, 1.):
        progress({"event": "gain_started", "gain": gain})
        results = []
        for implementation, backend in (("reference", reference), ("candidate", candidate)):
            check()
            receiver = call(backend.create, "Keep your own private record.", "Your beacon is Dim; your goal is G0.")
            donor = call(backend.create, "Keep your own private record.", "Your beacon is Bright; your goal is G1.")
            foreign = tuple(call(backend.step, donor, (), 0.) for _ in range(16))
            exports = [call(backend.step, receiver, foreign, gain).identity() for _ in range(4)]
            root = backend.digest(receiver)
            probe = call(backend.probe, receiver, "Choose one ID.\n1. Left\n2. Right\n3. Up\n4. Down",
                                  ("1", "2", "3", "4"), foreign, gain)
            sealed = backend.digest(probe.state)
            continued = call(backend.commit_answer, probe, foreign, gain)
            if backend.digest(receiver) != root:
                raise ValueError("Microcomparison changed the readout parent")
            archive = call(backend.dump_state, continued)
            restored = call(backend.load_state, archive)
            if backend.digest(continued) != backend.digest(restored):
                raise ValueError("Microcomparison archive restore differs")
            results.append({"exports": exports, "root": root, "sealed": sealed,
                            "continued": backend.digest(continued), "archive": archive["sha256"],
                            "probe": [probe.token, probe.probability, probe.legal_logits,
                                      probe.legal_mass, probe.token_ids]})
            progress({"event": "backend_complete", "gain": gain, "implementation": implementation,
                      "comparison_sha256": canonical_digest(results[-1])})
        outcomes.append({"gain": gain, "comparison_sha256": require_equal(*results, f"gain={gain}")})
        progress({"event": "gain_passed", **outcomes[-1]})
    check()
    return {"passed": True, "exact": True, "cases": outcomes, "scientific_data": False}


class TimedEpisodeRunner(EpisodeRunner):
    def __init__(self, *args: Any, synchronize: Callable[[], None], **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.synchronize, self.text_seconds = synchronize, 0.0

    def natural(self, episode: Any, policy: str) -> Any:
        if policy != "TEXT":
            return super().natural(episode, policy)
        self.synchronize(); start = time.perf_counter()
        value = super().natural(episode, policy)
        self.synchronize(); self.text_seconds += time.perf_counter() - start
        return value


@preserve_failure
def run_case(backend: Any, profile: str, name: str, material: dict, directory: Path,
             *, check: Callable[[], None], synchronize: Callable[[], None],
             archive_factory: Any = NativeArchiveWriter,
             spec: RuntimeSpec | None = None) -> dict:
    if name not in CASES or profile not in PROFILES:
        raise ValueError("Unknown engineering workload")
    spec = spec or RuntimeSpec(gain=GAIN)
    if name == "baseline":
        from dataclasses import replace
        spec = replace(spec, gain=0.)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    identity = {"version": VERSION, "purpose": "engineering_only", "scientific_data": False,
                "profile": profile, "case": name, "material_sha256": canonical_digest(material),
                "runtime": asdict(spec), "source_manifest_sha256": canonical_digest(source_manifest()),
                "backend_kind": "synthetic_fixture" if getattr(backend, "kind", None) == "synthetic_fixture" else "native",
                "native_model_identity": getattr(backend, "model_identity", None)}
    write_new(directory / "identity.json", identity)
    archive = None
    events = []

    def save_event(event: dict) -> None:
        check()
        archive(event)
        check()
        events.append({k: event[k] for k in ("episode_id", "sequence", "kind", "label", "digest")})

    with (directory / "engineering_rows.jsonl").open("x") as handle:
        def sink(row: dict) -> None:
            handle.write(json.dumps({**row, "scientific_data": False,
                                     "purpose": "engineering_only"}, sort_keys=True, allow_nan=False) + "\n")
            handle.flush(); os.fsync(handle.fileno())

        if name == "full_with_text":
            episode = tasks.episode_from_dict(material)
            archive = archive_factory(directory / "archives", backend, identity)
            runner = TimedEpisodeRunner(backend, spec, profile, sink=sink,
                                       artifact_sink=save_event, synchronize=synchronize)
            collect = lambda: runner.run_episode(episode, text_reference=True)
        else:
            episode = neutral.episode_from_dict(material)
            if episode.stage != name:
                raise ValueError("Engineering neutral material stage differs")
            runner = neutral.NeutralRunner(backend, spec, profile, sink=sink)
            collect = lambda: runner.run_episode(episode)
        check(); synchronize(); start = time.perf_counter()
        with trace_backend(backend, check) as trace, profile_backend(backend) as timings:
            records = collect()
        synchronize(); seconds = time.perf_counter() - start
        check()

    restored = 0
    restore_start = time.perf_counter()
    if archive is not None:
        if len(archive.index) != 16:
            raise ValueError("Engineering snapshot/tape archive count differs")
        for name_in_archive in archive.index:
            check()
            value = archive.load(name_in_archive)
            check()
            restored += 1
            del value
    synchronize()
    check()
    summary = {**identity, "status": "complete", "elapsed_seconds": seconds,
               "text_seconds": getattr(runner, "text_seconds", 0.),
               "archive_restore_seconds": time.perf_counter() - restore_start,
               "readout_count": len(records), "records_sha256": canonical_digest(records),
               "archive_events_sha256": canonical_digest(events), "restored_archives": restored,
               "trace": trace, "timings": timings,
               "bytes": sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())}
    check(); write_new(directory / "summary.json", summary)
    return summary


def compare_cases(left: dict, right: dict) -> dict:
    fields = ("profile", "case", "material_sha256", "readout_count", "records_sha256",
              "archive_events_sha256", "restored_archives", "trace")
    digest = require_equal({k: left[k] for k in fields}, {k: right[k] for k in fields}, left["case"])
    return {"case": left["case"], "exact": True, "comparison_sha256": digest,
            "reference_seconds": left["elapsed_seconds"], "candidate_seconds": right["elapsed_seconds"],
            "speed_ratio": left["elapsed_seconds"] / right["elapsed_seconds"]}


def validate_materials(profile: str, material_set: dict) -> None:
    if canonical_digest(material_set) != canonical_digest(materials(profile)):
        raise ValueError("Engineering materials changed")


@preserve_failure
def run_model(reference: Any, profile: str, material_set: dict, directory: Path, *,
              check: Callable[[], None], synchronize: Callable[[], None],
              expected_native_identity: str, expected_source_manifest: dict) -> dict:
    """Called only by a reviewed external budget/lease supervisor, one model at a time."""
    from mb.v6_native import NativeBackend
    if type(reference) is not NativeBackend or reference.tokens.profile_key != profile:
        raise ValueError("An authorized pinned native reference is required")
    selected = resolve_profile(profile)
    selected.validate_model_config(reference.model.config)
    if (getattr(reference.model.config, "_commit_hash", None) != selected.revision
            or reference.model_identity != expected_native_identity
            or len(expected_native_identity) != 64
            or source_manifest() != expected_source_manifest):
        raise ValueError("Pinned checkpoint/accepted native identity/source differs")
    validate_materials(profile, material_set)
    directory.mkdir(parents=True, exist_ok=False)
    write_new(directory / "attempt.json", {"version": VERSION, "at_epoch": time.time(),
        "profile": profile, "native_model_identity": expected_native_identity,
        "source_manifest": expected_source_manifest, "material_sha256": canonical_digest(material_set),
        "scientific_data": False, "formal_authorized": False})
    check()
    candidate = PerformanceBackend(reference.model, reference.tokenizer,
                                    hardware_acceptance_authorized=True)
    check()
    if reference.model_identity != candidate.model_identity:
        raise ValueError("Candidate model identity differs")
    def progress(value: dict) -> None:
        with (directory / "progress.jsonl").open("a") as handle:
            handle.write(json.dumps({"at_epoch": time.time(), **value}, sort_keys=True) + "\n")
            handle.flush(); os.fsync(handle.fileno())
    micro = micro_compare(reference, candidate, check=check, progress=progress)
    write_new(directory / "micro.json", micro)
    engines = {"reference": reference, "candidate": candidate}
    order = ("reference", "candidate") if profile == PROFILES[0] else ("candidate", "reference")
    summaries = {key: {} for key in engines}
    comparisons = []
    for name in CASES:
        for implementation in order:
            check()
            progress({"event": "case_started", "case": name, "implementation": implementation})
            summaries[implementation][name] = run_case(engines[implementation], profile, name,
                material_set[name], directory / implementation / name, check=check,
                synchronize=synchronize)
        comparisons.append(compare_cases(summaries["reference"][name], summaries["candidate"][name]))
        progress({"event": "case_compared", **comparisons[-1]})
    result = {"version": VERSION, "status": "complete", "profile": profile,
              "scientific_data": False, "formal_authorized": False, "micro": micro,
              "backend_kind": "native", "native_model_identity": expected_native_identity,
              "source_manifest_sha256": canonical_digest(expected_source_manifest),
              "pinned_native_identity_verified": True,
              "comparisons": comparisons, "summaries": summaries,
              "candidate_counts": dict(candidate.performance_counts)}
    check(); write_new(directory / "comparison.json", result)
    return result


def project(models: dict, *, hourly_usd: float, observed_transfer_bytes_per_second: float,
            transfer_usd_per_tb: float, setup_seconds_per_stage: float = 600.,
            backup_fixed_seconds_per_stage: float = 840.) -> dict:
    """Both-model descriptive estimate and conservative component; not admission.

    One example per workload cannot quantify a tail or choose a gain. Calibration
    at gain1 is a runtime proxy for all nonzero neutral stages; state this openly.
    The unchanged full-stage admission rule remains a separate, stricter gate.
    """
    if set(models) != set(PROFILES):
        raise ValueError("Both models are required for a whole-package forecast")
    for value in (hourly_usd, observed_transfer_bytes_per_second, transfer_usd_per_tb,
                  setup_seconds_per_stage, backup_fixed_seconds_per_stage):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Forecast inputs must be finite and nonnegative")
    if not 0 < hourly_usd <= 1.6 or observed_transfer_bytes_per_second <= 0:
        raise ValueError("Measured rate/throughput is required")
    source_hashes = {record.get("source_manifest_sha256") for record in models.values()}
    if (len(source_hashes) != 1 or any(type(value) is not str or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value) for value in source_hashes)):
        raise ValueError("Both models must use the same pinned candidate source")
    output = {}
    for profile in PROFILES:
        record = models[profile]
        if (record.get("status") != "complete" or record.get("profile") != profile
                or record.get("formal_authorized") is not False
                or record.get("backend_kind") != "native" or record.get("pinned_native_identity_verified") is not True
                or record.get("micro", {}).get("passed") is not True
                or record.get("micro", {}).get("exact") is not True
                or {v["case"] for v in record["comparisons"] if v["exact"] is True} != set(CASES)):
            raise ValueError("Only complete exact comparisons support a projection")
        micro_cases = record["micro"].get("cases", [])
        if (len(micro_cases) != 4 or [row.get("gain") for row in micro_cases] != [0., .25, .5, 1.]
                or any(type(row.get("comparison_sha256")) is not str
                       or len(row["comparison_sha256"]) != 64
                       or any(char not in "0123456789abcdef" for char in row["comparison_sha256"])
                       for row in micro_cases)):
            raise ValueError("All four exact micro comparisons are required")
        rows = record["summaries"]["candidate"]
        if set(rows) != set(CASES) or set(record["summaries"]["reference"]) != set(CASES):
            raise ValueError("Exactly three paired measured workloads are required")
        full, baseline, calibration = (rows[k] for k in CASES)
        for name, row in rows.items():
            if (row.get("status") != "complete" or row.get("profile") != profile
                    or row.get("case") != name or row.get("backend_kind") != "native"
                    or row.get("native_model_identity") != record["native_model_identity"]
                    or row.get("source_manifest_sha256") != record["source_manifest_sha256"]
                    or row.get("material_sha256") != canonical_digest(materials(profile)[name])
                    or canonical_digest(row.get("runtime")) != canonical_digest(asdict(RuntimeSpec(gain=0. if name == "baseline" else GAIN)))
                    or type(row.get("elapsed_seconds")) not in (float, int)
                    or not math.isfinite(row["elapsed_seconds"]) or row["elapsed_seconds"] <= 0
                    or type(row.get("bytes")) is not int or row["bytes"] < 0):
                raise ValueError("Incomplete or invalid measured workload")
            reference = record["summaries"]["reference"][name]
            if (reference.get("status") != "complete"
                    or type(reference.get("elapsed_seconds")) not in (int, float)
                    or not math.isfinite(reference["elapsed_seconds"]) or reference["elapsed_seconds"] <= 0):
                raise ValueError("Incomplete or invalid reference workload")
            for field in ("backend_kind", "native_model_identity", "source_manifest_sha256", "runtime"):
                if canonical_digest(reference.get(field)) != canonical_digest(row[field]):
                    raise ValueError("Reference provenance differs from the candidate")
            comparison = compare_cases(reference, row)
            if comparison not in record["comparisons"]:
                raise ValueError("Saved exact comparison differs from recomputation")
        text = full["text_seconds"]
        if not math.isfinite(text) or not 0 <= text < full["elapsed_seconds"]:
            raise ValueError("Invalid measured text duration")
        formal = 240 * (full["elapsed_seconds"] - text) + 60 * text
        neutral_seconds = 60 * baseline["elapsed_seconds"] + 200 * calibration["elapsed_seconds"]
        # Keep the old conservative fallback when a stage/gain has no direct
        # complete pilot: the maximum observed full/neutral episode, times1.5.
        worst_neutral = max(row["elapsed_seconds"] for row in rows.values())
        conservative_compute = 1.5 * (240 * full["elapsed_seconds"]
                                       + 60 * baseline["elapsed_seconds"] + 200 * worst_neutral)
        bytes_estimate = 240 * full["bytes"] + 60 * baseline["bytes"] + 200 * calibration["bytes"]
        backup = 1.25 * bytes_estimate / observed_transfer_bytes_per_second
        overhead = 6 * (setup_seconds_per_stage + backup_fixed_seconds_per_stage)
        output[profile] = {"illustrative_compute_hours": (formal + neutral_seconds) / 3600,
                           "conservative_compute_hours": conservative_compute / 3600,
                           "backup_hours": backup / 3600, "stage_overhead_hours": overhead / 3600,
                           "projected_bytes": bytes_estimate,
                           "transfer_usd": 1.25 * bytes_estimate / 1e12 * transfer_usd_per_tb}
    hours = sum(x["conservative_compute_hours"] + x["backup_hours"] + x["stage_overhead_hours"]
                for x in output.values())
    return {"version": VERSION, "forecast_only": True, "formal_authorized": False,
            "models": output, "conservative_remaining_hours_component": hours,
            "conservative_remaining_usd_component": hours * hourly_usd + sum(x["transfer_usd"] for x in output.values()),
            "limitations": ["One engineering example per model/workload, no sampling uncertainty interval.",
                "Gain1 neutral timing proxies other gains and validation; no scientific gate was evaluated.",
                "Assumes both models pass all future gates; actual gate failure ends that model.",
                "Prior/session costs, new-source acceptance, further smoke, shutdown and storage after completion must be added.",
                "Not a replacement for the frozen full-stage admission/affordability check."]}
