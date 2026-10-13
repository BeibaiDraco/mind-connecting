"""Admitted native V6 collection. Import is torch-free and performs no I/O.

The external supervisor owns provider shutdown and refreshes launch proofs. This
module never rents hardware, fetches weights, selects an outcome, or repairs raw
files. A retry restarts the exact episode and reconciles every retained success.
"""
from __future__ import annotations

import contextlib
import gc
import hashlib
import json
import math
import os
import shutil
import time
from pathlib import Path
from typing import Any

from mb import v6_analysis as analysis
from mb import v6_tasks as tasks
from mb.model_profiles import PROFILES
from mb.v6_contract import Probe, RuntimeSpec, canonical_digest
from mb.v6_run import EpisodeLedger, KEY_FIELDS, NativeArchiveWriter, _write_new
from mb.v6_runtime import EpisodeRunner, PairState, RoundTape

VERSION = "v6-native-execution-1"
NEUTRAL = ("baseline", "calibration", "validation")
ENGINEERING = ("acceptance", "smoke")
NATIVE_CHECKS = ("native_same_shape", "nonempty_zero_gain", "paired_order",
                 "persisted_pair_and_tape", "two_round_replay", "control_recovery",
                 "text_control_policy", "foreign_attention_reference")


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for part in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def read_json(path: str | Path) -> dict:
    value = json.loads(Path(path).read_text())
    if type(value) is not dict:
        raise ValueError("Expected a JSON object")
    canonical_digest(value)
    return value


def _pin(pin: dict, *, evidence_dir: Path | None = None, require_object: bool = True) -> tuple[Path, Any]:
    from mb.v6_launch import pin_value
    return pin_value(pin, root=Path(__file__).resolve().parents[2], evidence_dir=evidence_dir,
                     require_object=require_object)


def _plan(plan_path: Path, admission_path: Path) -> dict:
    from mb.v6_launch import validate_execution
    value = validate_execution(plan_path, admission_path)
    if value["_admission"].get("historical_only"):
        raise ValueError("Historical evidence never authorizes new execution")
    return value


def _runtime(plan: dict) -> RuntimeSpec:
    r = plan["runtime"]
    if set(r) != {"work_tokens", "preparation_tokens", "window", "gain", "choice_labels"}:
        raise ValueError("Runtime fields differ from the reviewed native contract")
    if (any(type(r[k]) is not int for k in ("work_tokens", "preparation_tokens", "window"))
            or (r["work_tokens"], r["preparation_tokens"], r["window"]) != (64, 16, 16)
            or r["choice_labels"] != ["1", "2", "3", "4"]
            or type(r["gain"]) not in (int, float) or not math.isfinite(r["gain"])):
        raise ValueError("Native production clocks/labels/gain differ")
    if r["gain"] not in ((0.0,) if plan["stage"] == "baseline" else (0.25, 0.5, 1.0)):
        raise ValueError("Gain is outside the prospective stage grid")
    return RuntimeSpec(**{**r, "choice_labels": tuple(r["choice_labels"])})


def _materials(plan: dict) -> tuple[list, str, tuple[str, ...]]:
    stage, profile = plan["stage"], plan["model_profile"]
    evidence = plan.get("_admission", {}).get("evidence_dir")
    path, _ = _pin(plan["material_pin"], evidence_dir=Path(evidence) if evidence else None, require_object=False)
    if stage in NEUTRAL:
        from mb import v6_neutral as neutral
        episodes = neutral.load_materials(path)
        if any(ep.stage != stage for ep in episodes):
            raise ValueError("Neutral material stage differs")
        digest, fields = neutral.materials_sha256(episodes), neutral.KEY_FIELDS
        material_stages = [ep.task.stage for ep in episodes]
    else:
        episodes = tasks.load_materials(path)
        digest, fields = tasks.materials_sha256(episodes), KEY_FIELDS
        material_stages = [ep.stage for ep in episodes]
    if stage in NEUTRAL:
        suffix = f"_g{int(float(plan['runtime']['gain'])*100):03d}" if stage == "calibration" else ""
        namespace = f"v6-neutral-{stage}-{profile}_{stage}{suffix}"
    else:
        namespace = f"v6_{profile}_{stage}"
    if (len(episodes) != plan["n"] or len({ep.episode_id for ep in episodes}) != len(episodes)
            or any(s != namespace for s in material_stages)):
        raise ValueError("Material count/profile/stage namespace differs")
    required_n = {"acceptance": 1, "baseline": 60, "calibration": 40, "validation": 80, "formal": 240}
    if (stage in required_n and len(episodes) != required_n[stage]) or (stage == "smoke" and not 1 <= len(episodes) <= 4):
        raise ValueError("Stage sample count differs from the fixed proposal")
    text = set(plan["text_episode_ids"])
    if not text <= {ep.episode_id for ep in episodes} or (stage not in ("formal", "smoke") and text):
        raise ValueError("Text episodes are outside this stage")
    if stage == "formal":
        subset = tasks.select_text_subset(episodes, n=60)
        if subset is None or text != {ep.episode_id for ep in subset}:
            raise ValueError("Formal text subset is not the balanced material-only selection")
    return episodes, digest, tuple(fields)


def _acceptance(plan: dict) -> dict | None:
    if plan["stage"] == "acceptance":
        if plan["prerequisites"]:
            raise ValueError("Initial native acceptance must not consume later-stage evidence")
        return None
    if "acceptance" not in plan["prerequisites"]:
        raise ValueError("Real native acceptance prerequisite is missing")
    evidence = plan.get("_admission", {}).get("evidence_dir")
    _, value = _pin(plan["prerequisites"]["acceptance"], evidence_dir=Path(evidence) if evidence else None)
    if (value.get("version") != "v6-native-acceptance-1" or value.get("status") != "passed"
            or value.get("backend_kind") != "native" or value.get("scientific_data") is not False
            or value.get("model_profile") != plan["model_profile"]
            or value.get("source_manifest_sha256") != plan["_admission"]["source_manifest_sha256"]
            or value.get("tokenizer_manifest_sha256") != file_sha256(PROFILES[plan["model_profile"]].manifest_path)
            or value.get("checks") != {name: True for name in NATIVE_CHECKS}
            or not isinstance(value.get("native_model_identity"), str)
            or len(value["native_model_identity"]) != 64):
        raise ValueError("Acceptance is not complete, native or source/model matched")
    bundle = _receipt_run(plan["prerequisites"]["acceptance"], plan)
    ident = bundle["native_identity"]
    if (bundle["plan"]["stage"] != "acceptance"
            or ident["native_model_identity"] != value["native_model_identity"]
            or value.get("identity_sha256") != canonical_digest(ident)):
        raise ValueError("Acceptance report is not bound to its completed native run")
    return value


def _receipt_run(pin: dict, plan: dict) -> dict:
    """Resolve authentic raw runs, including a hash-verified backup's sibling path."""
    original = Path(pin["path"])
    candidates = [original]
    evidence = plan.get("_admission", {}).get("evidence_dir")
    if evidence:
        candidates.append(Path(evidence).parent.parent / original.parent.name / original.name)
    for candidate in candidates:
        if candidate.is_file() and file_sha256(candidate) == pin["sha256"]:
            return read_native_run(candidate.parent)
    raise ValueError("Native prerequisite raw run is unavailable or changed")


def _prerequisites(plan: dict) -> dict | None:
    accepted = _acceptance(plan)
    if plan["stage"] not in ENGINEERING:
        receipts = {}
        for name in ("smoke", "resume"):
            if name not in plan["prerequisites"]:
                raise ValueError(f"Missing {name} prerequisite")
            evidence = plan.get("_admission", {}).get("evidence_dir")
            _, value = _pin(plan["prerequisites"][name], evidence_dir=Path(evidence) if evidence else None)
            expected_version = "v6-native-completion-1" if name == "smoke" else "v6-native-resume-1"
            if (value.get("version") != expected_version or value.get("stage") != "smoke"
                    or value.get("status") != "complete" or value.get("backend_kind") != "native"
                    or value.get("model_profile") != plan["model_profile"]
                    or value.get("source_manifest_sha256") != plan["_admission"]["source_manifest_sha256"]
                    or value.get("native_model_identity") != accepted["native_model_identity"]
                    or (name == "resume" and value.get("byte_identical") is not True)):
                raise ValueError(f"Invalid {name} prerequisite")
            receipts[name] = value
        if (receipts["resume"].get("completion_pin") != plan["prerequisites"]["smoke"]
                or receipts["resume"].get("identity_sha256") != receipts["smoke"].get("identity_sha256")
                or receipts["smoke"].get("scientific_data") is not False
                or receipts["smoke"].get("validation", {}).get("complete") is not True):
            raise ValueError("Smoke and no-op resume evidence are not the same complete run")
        smoke = _receipt_run(plan["prerequisites"]["smoke"], plan)
        if (smoke["plan"]["stage"] != "smoke"
                or canonical_digest(smoke["native_identity"]) != receipts["smoke"]["identity_sha256"]):
            raise ValueError("Smoke certificate differs from its native raw run")
    return accepted


def _identity(plan: dict, material_sha: str, fields: tuple[str, ...], native_identity: str) -> dict:
    immutable = {k: v for k, v in plan.items() if k != "_admission"}
    proof = plan["_admission"]
    return json.loads(json.dumps({"version": VERSION, "backend_kind": "native",
        "scientific_data": plan["stage"] not in ENGINEERING,
        "formal_authorized": plan["stage"] == "formal", "plan": immutable,
        "materials_sha256": material_sha, "record_key_fields": list(fields),
        "native_model_identity": native_identity,
        "profile": PROFILES[plan["model_profile"]].identity(),
        "tokenizer_manifest_sha256": file_sha256(PROFILES[plan["model_profile"]].manifest_path),
        "provenance": {k: proof[k] for k in ("authorization_sha256", "source_manifest_sha256",
                                             "admission_contract_sha256")}}, allow_nan=False))


def _validate_rows(rows: list[dict], episodes: list, plan: dict, identity: dict) -> dict:
    expected_id = canonical_digest(identity)
    for row in rows:
        if (row.get("backend_kind") != "native" or row.get("execution_identity_sha256") != expected_id
                or row.get("scientific_data") is not (plan["stage"] not in ENGINEERING)):
            raise ValueError("Retained record is synthetic or has another execution identity")
        if not {"legal_logits", "legal_mass", "top_probability", "top_token", "token_ids"} <= row.keys():
            raise ValueError("Retained record lacks native readout evidence")
    if plan["stage"] in NEUTRAL:
        from mb.v6_neutral import validate_records
        return validate_records(rows, episodes, plan["model_profile"], plan["runtime"]["gain"], require_complete=False)
    return analysis.validate_records(rows, {plan["model_profile"]: [ep.episode_id for ep in episodes]},
        text_episodes={plan["model_profile"]: list(set(plan["text_episode_ids"]) & {ep.episode_id for ep in episodes})})


def _archive_inventory(directory: Path, episodes: list, *, complete: bool) -> None:
    archive = directory / "archives"
    index = archive / "inventory.jsonl"
    entries = [] if not index.exists() else [json.loads(line) for line in index.read_text().splitlines()]
    names = set()
    pairs = set()
    for row in entries:
        name = row["file"]
        if Path(name).name != name or name in names:
            raise ValueError("Duplicate or unsafe native archive name")
        path = archive / name
        if not path.is_file() or path.stat().st_size != row["bytes"] or file_sha256(path) != row["sha256"]:
            raise ValueError("Native archive bytes differ")
        meta = row["meta"]
        key = (meta["episode_id"], meta["sequence"])
        if key in pairs or key[0] not in {ep.episode_id for ep in episodes} or type(key[1]) is not int or not 0 <= key[1] < 16:
            raise ValueError("Native archive sequence differs")
        names.add(name); pairs.add(key)
    if {p.name for p in archive.glob("*.pt")} != names:
        raise ValueError("Unindexed interrupted native archive retained; no automatic repair")
    if complete and pairs != {(ep.episode_id, i) for ep in episodes for i in range(16)}:
        raise ValueError("Complete main ledger lacks its sixteen artifacts per episode")


def _files(directory: Path) -> dict[str, dict]:
    return {str(path.relative_to(directory)): {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
            for path in sorted(directory.rglob("*")) if path.is_file() and path != directory / "completion.json"}


def _completed(directory: Path, identity: dict) -> dict | None:
    path = directory / "completion.json"
    if not path.exists():
        return None
    report = read_json(path)
    if (report.get("version") != "v6-native-completion-1" or report.get("status") != "complete"
            or report.get("identity_sha256") != canonical_digest(identity) or report.get("file_pins") != _files(directory)):
        raise ValueError("Completed run bytes or identity changed")
    return report


class _Bounds:
    def __init__(self, admission_path: Path, output: Path):
        from mb.v6_launch import budget_projection
        proof = read_json(admission_path)
        now = time.time()
        value = budget_projection(proof["budget"], now=now, phase=proof["phase"])
        self.deadline = value["effective_deadline_epoch"]
        self.monotonic_deadline = time.monotonic() + self.deadline - now
        _, storage = _pin(proof["storage_pin"])
        self.minimum_free = storage["remote_required_bytes"]
        self.output = output
        self.initial_bytes = sum(p.stat().st_size for p in output.rglob("*") if p.is_file()) if output.exists() else 0

    def check(self, *, disk: bool = False) -> None:
        if time.time() >= self.deadline or time.monotonic() >= self.monotonic_deadline:
            raise TimeoutError("Admitted stage budget/deadline exhausted")
        if disk:
            written = sum(p.stat().st_size for p in self.output.rglob("*") if p.is_file()) - self.initial_bytes
            if shutil.disk_usage(self.output.parent).free + max(0, written) < self.minimum_free:
                raise OSError("Admitted remote storage reservation was consumed by other work")


@contextlib.contextmanager
def _exclusive(parent: Path):
    import fcntl
    if not parent.is_dir():
        raise ValueError("Prepared execution data directory is missing")
    with (parent / ".v6-native-execution.lock").open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another native stage owns this data directory's execution lease") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _load_native(profile: str):
    from mb.v6_native import NativeBackend
    return NativeBackend.from_local_cache(profile=profile, hardware_acceptance_authorized=True)


def _check_backend(backend: Any, profile: str, accepted: dict | None) -> None:
    from mb.v6_native import NativeBackend
    if (not isinstance(backend, NativeBackend) or getattr(backend, "kind", None) == "synthetic_fixture"
            or backend.tokens.profile_key != profile):
        raise ValueError("Execution requires the real admitted native backend")
    if accepted is not None and backend.model_identity != accepted["native_model_identity"]:
        raise ValueError("Loaded model parameter identity differs from real acceptance")


def _stable_recheck(plan_path: Path, admission_path: Path, plan: dict) -> None:
    current = _plan(plan_path, admission_path)
    if current["plan_sha256"] != plan["plan_sha256"] or any(
            current["_admission"][k] != plan["_admission"][k] for k in
            ("authorization_sha256", "source_manifest_sha256", "admission_contract_sha256")):
        raise ValueError("Execution approval/source changed during the stage")


def _capture_admission(directory: Path, plan_path: Path, admission_path: Path) -> dict:
    """Preserve original JSON bytes; historical resolution uses hashes, never edited paths."""
    from mb.v6_launch import validate_execution
    current = _plan(plan_path, admission_path)
    payloads: dict[str, bytes] = {}
    def capture(path: Path) -> str:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        payloads[digest] = raw
        walk(json.loads(raw))
        return digest
    visited = set()
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if set(value) == {"path", "sha256"}:
                if value["sha256"] in visited:
                    return
                visited.add(value["sha256"])
                path, _ = _pin(value, require_object=False)
                if capture(path) != value["sha256"]:
                    raise ValueError("Evidence changed during capture")
            else:
                for child in value.values():
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    plan_sha, admission_sha = capture(plan_path), capture(admission_path)
    if canonical_digest(json.loads(payloads[plan_sha])) != current["plan_sha256"]:
        raise ValueError("Stage plan changed during evidence capture")
    evidence = directory / "evidence"
    evidence.mkdir(exist_ok=True)
    for digest, raw in payloads.items():
        path = evidence / f"{digest}.json"
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError("Immutable evidence blob changed")
        else:
            with path.open("xb") as handle:
                handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    when = current["_admission"]["validated_at_epoch"]
    historical = validate_execution(evidence / f"{plan_sha}.json", evidence / f"{admission_sha}.json",
                                    now=when, evidence_dir=evidence)
    if historical["plan_sha256"] != current["plan_sha256"]:
        raise ValueError("Captured evidence changed the admitted stage")
    entry = {"version": "v6-launch-evidence-1", "plan_file_sha256": plan_sha,
             "admission_file_sha256": admission_sha, "validated_at_epoch": when,
             "plan_sha256": current["plan_sha256"]}
    with (directory / "admission_history.jsonl").open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True, allow_nan=False) + "\n")
        handle.flush(); os.fsync(handle.fileno())
    historical["_admission"]["evidence_dir"] = str(evidence)
    return historical


def historical_plan(run_dir: str | Path) -> dict:
    from mb.v6_launch import validate_execution
    directory = Path(run_dir)
    entries = [json.loads(line) for line in (directory / "admission_history.jsonl").read_text().splitlines()]
    if not entries or any(row.get("version") != "v6-launch-evidence-1" for row in entries):
        raise ValueError("Missing immutable launch history")
    row = entries[-1]
    evidence = directory / "evidence"
    files = [evidence / (row[k] + ".json") for k in ("plan_file_sha256", "admission_file_sha256")]
    if any(file_sha256(path) != row[k] for path, k in zip(files, ("plan_file_sha256", "admission_file_sha256"))):
        raise ValueError("Historical plan or admission bytes changed")
    plan = validate_execution(*files, now=row["validated_at_epoch"], evidence_dir=evidence)
    if plan["plan_sha256"] != row["plan_sha256"]:
        raise ValueError("Historical plan digest differs")
    plan["_admission"]["evidence_dir"] = str(evidence)
    return plan


def read_native_run(path: str | Path) -> dict:
    """Offline raw integrity/material/source audit, never statistical outcome selection."""
    directory = Path(path)
    if directory.name == "completion.json":
        directory = directory.parent
    identity = read_json(directory / "identity.json")
    report = _completed(directory, identity)
    if report is None:
        raise ValueError("Prerequisite native run is incomplete")
    plan = historical_plan(directory)
    evidence = Path(plan["_admission"]["evidence_dir"])
    material_path, _ = _pin(plan["material_pin"], evidence_dir=evidence, require_object=False)
    if plan["stage"] in NEUTRAL:
        from mb import v6_neutral as neutral
        episodes = neutral.load_materials(material_path)
        digest, fields = neutral.materials_sha256(episodes), tuple(neutral.KEY_FIELDS)
    else:
        episodes = tasks.load_materials(material_path)
        digest, fields = tasks.materials_sha256(episodes), KEY_FIELDS
    expected = _identity(plan, digest, fields, identity["native_model_identity"])
    if expected != identity or len(episodes) != plan["n"]:
        raise ValueError("Prerequisite material/identity differs")
    ledger = EpisodeLedger(directory, identity, resume=True, key_fields=fields)
    try:
        rows = list(ledger.records.values())
        if plan["stage"] != "acceptance":
            if not _validate_rows(rows, episodes, plan, identity)["complete"]:
                raise ValueError("Prerequisite raw keys are incomplete")
            if plan["stage"] not in NEUTRAL:
                _archive_inventory(directory, episodes, complete=True)
        return {"records": rows, "episodes": episodes, "plan": plan, "native_identity": identity}
    finally:
        ledger.close()


def execute(plan_path: str | Path, admission_path: str | Path, *, resume: bool = False,
            validate_only: bool = False) -> dict:
    """Admit first, then execute native data only; complete resume performs no writes."""
    plan_path, admission_path = Path(plan_path), Path(admission_path)
    plan = _plan(plan_path, admission_path)
    spec = _runtime(plan)
    episodes, material_sha, fields = _materials(plan)
    accepted = _prerequisites(plan)
    if plan["stage"] not in ENGINEERING:
        from mb.v6_admission import validate_stage_prerequisites
        validate_stage_prerequisites(plan)
    directory = Path(plan["output_dir"])
    if validate_only:
        return {"version": VERSION, "status": "admitted_not_executed", "stage": plan["stage"],
                "model_or_gpu_used": False, "plan_sha256": plan["plan_sha256"]}
    existing_identity = read_json(directory / "identity.json") if resume else None
    if resume:
        native_id = accepted["native_model_identity"] if accepted else existing_identity["native_model_identity"]
        identity = _identity(plan, material_sha, fields, native_id)
        if existing_identity != identity:
            raise ValueError("Native resume identity changed before model loading or write")
        report = _completed(directory, identity)
        if report is not None:
            if plan["stage"] != "acceptance":
                ledger = EpisodeLedger(directory, identity, resume=True, key_fields=fields)
                try:
                    check = _validate_rows(list(ledger.records.values()), episodes, plan, identity)
                    if not check["complete"]:
                        raise ValueError("Completed receipt has an incomplete ledger")
                    if plan["stage"] not in NEUTRAL:
                        _archive_inventory(directory, episodes, complete=True)
                finally:
                    ledger.close()
            return report
        if plan["stage"] == "acceptance":
            raise ValueError("Incomplete acceptance is retained; explicit new engineering attempt required")
    elif directory.exists():
        raise FileExistsError("Native output exists; use explicit exact resume")
    with _exclusive(directory.parent):
        _stable_recheck(plan_path, admission_path, plan)
        if resume:
            ledger = EpisodeLedger(directory, identity, resume=True, key_fields=fields)
            try:
                _validate_rows(list(ledger.records.values()), episodes, plan, identity)
                for ep in episodes:
                    retained = [r for r in ledger.records.values() if r["episode_id"] == ep.episode_id]
                    if not _episode_finished(ledger, ep, retained, plan, identity) and ledger.attempts(ep.episode_id) >= 2:
                        raise RuntimeError("Episode's original attempt and one retry are exhausted")
                if plan["stage"] not in NEUTRAL:
                    _archive_inventory(directory, episodes, complete=False)
            finally:
                ledger.close()
        stage_started = time.monotonic()
        backend = _load_native(plan["model_profile"])
        _check_backend(backend, plan["model_profile"], accepted)
        _stable_recheck(plan_path, admission_path, plan)
        identity = _identity(plan, material_sha, fields, backend.model_identity)
        bounds = _Bounds(admission_path, directory)
        bounds.check(disk=True)
        ledger = EpisodeLedger(directory, identity, resume=resume, key_fields=fields)
        try:
            _capture_admission(directory, plan_path, admission_path)
            if plan["stage"] == "acceptance":
                report = _run_acceptance(backend, episodes[0], spec, directory, identity, bounds)
                _write_new(directory / "acceptance.json", report)
                validation = {"complete": True, "expected_records": 0, "ok_records": 0}
            else:
                validation = _collect(backend, episodes, spec, plan, identity, ledger, bounds,
                                      plan_path, admission_path)
            ledger.close()
            result = {"version": "v6-native-completion-1", "status": "complete", "backend_kind": "native",
                "scientific_data": plan["stage"] not in ENGINEERING, "stage": plan["stage"],
                "model_profile": plan["model_profile"], "native_model_identity": backend.model_identity,
                "source_manifest_sha256": plan["_admission"]["source_manifest_sha256"],
                "identity_sha256": canonical_digest(identity), "validation": validation,
                "n": len(episodes), "elapsed_seconds": time.monotonic()-stage_started,
                "peak_allocated_bytes": _peak_memory(backend),
                "archive_bytes": sum(p.stat().st_size for p in directory.rglob("*.pt")),
                "file_pins": _files(directory)}
            _write_new(directory / "completion.json", result)
            return result
        except BaseException as exc:
            ledger.note({"event": "stage_failed", "error_type": type(exc).__name__, "time_epoch": time.time()})
            raise
        finally:
            ledger.close()


def _peak_memory(backend: Any) -> int:
    import torch
    return int(torch.cuda.max_memory_allocated(backend.device))


def _episode_finished(ledger: EpisodeLedger, episode: Any, retained: list,
                      plan: dict, identity: dict) -> bool:
    notes_path = ledger.directory / "notes.jsonl"
    notes = [json.loads(line) for line in notes_path.read_text().splitlines()] if notes_path.exists() else []
    finished = [note for note in notes if note.get("episode_id") == episode.episode_id
                and note.get("event") in ("episode_started", "episode_complete")]
    return bool(_validate_rows(retained, [episode], plan, identity)["complete"]
                and finished and finished[-1]["event"] == "episode_complete")


def _collect(backend: Any, episodes: list, spec: RuntimeSpec, plan: dict, identity: dict,
             ledger: EpisodeLedger, bounds: _Bounds, plan_path: Path, admission_path: Path) -> dict:
    identity_sha = canonical_digest(identity)
    archive = None
    if plan["stage"] not in NEUTRAL:
        archive = NativeArchiveWriter(ledger.directory / "archives", backend, identity,
                                     resume=(ledger.directory / "archives").exists())
    def record(row: dict) -> None:
        bounds.check()
        if row.get("scientific_data") is False or str(row.get("backend_kind", "")).startswith("synthetic"):
            raise ValueError("A synthetic record cannot enter native collection")
        ledger.write({**row, "backend_kind": "native", "scientific_data": plan["stage"] not in ENGINEERING,
                      "execution_identity_sha256": identity_sha})
    def artifact(event: dict) -> None:
        bounds.check(disk=True)
        archive(event)
    for ep in episodes:
        retained = [row for row in ledger.records.values() if row["episode_id"] == ep.episode_id]
        if _episode_finished(ledger, ep, retained, plan, identity):
            continue
        while True:
            _stable_recheck(plan_path, admission_path, plan)
            bounds.check(disk=True)
            if ledger.attempts(ep.episode_id) >= 2:
                raise RuntimeError("Episode's original attempt and one retry are exhausted")
            _capture_admission(ledger.directory, plan_path, admission_path)
            ledger.note({"event": "episode_started", "episode_id": ep.episode_id, "time_epoch": time.time()})
            started = time.monotonic()
            try:
                if plan["stage"] in NEUTRAL:
                    from mb.v6_neutral import NeutralRunner
                    runner = NeutralRunner(backend, spec, plan["model_profile"], sink=record)
                    runner.run_episode(ep)
                else:
                    runner = EpisodeRunner(backend, spec, plan["model_profile"], sink=record, artifact_sink=artifact)
                    runner.run_episode(ep, text_reference=ep.episode_id in plan["text_episode_ids"])
                retained = [row for row in ledger.records.values() if row["episode_id"] == ep.episode_id]
                if not _validate_rows(retained, [ep], plan, identity)["complete"]:
                    raise ValueError("Native episode returned without all expected records")
                ledger.note({"event": "episode_complete", "episode_id": ep.episode_id,
                             "elapsed_seconds": time.monotonic() - started, "time_epoch": time.time()})
                break
            except Exception as exc:
                ledger.note({"event": "technical_failure", "episode_id": ep.episode_id,
                             "error_type": type(exc).__name__, "elapsed_seconds": time.monotonic()-started})
                # Replaying a structurally corrupt ledger/archive cannot repair it.
                if isinstance(exc, (ValueError, PermissionError, TimeoutError, OSError)) or ledger.attempts(ep.episode_id) >= 2:
                    raise
                if archive is not None:
                    _archive_inventory(ledger.directory, episodes, complete=False)
                gc.collect()
            finally:
                if "runner" in locals():
                    del runner
    validation = _validate_rows(list(ledger.records.values()), episodes, plan, identity)
    if not validation["complete"]:
        raise ValueError("Native stage is incomplete")
    if archive is not None:
        _archive_inventory(ledger.directory, episodes, complete=True)
    if plan["stage"] in NEUTRAL:
        from mb.v6_admission import evaluate_stage
        gate = evaluate_stage(list(ledger.records.values()), episodes, historical_plan(ledger.directory),
                              native_identity=identity)
        target = ledger.directory / "gate.json"
        if target.exists():
            if read_json(target) != gate:
                raise ValueError("Retained scientific gate differs from immutable raw recomputation")
        else:
            _write_new(target, gate)
        # Failed scientific gates are complete data, never permission to advance.
        validation = {**validation, "gate": gate.get("gate"), "consumable": gate.get("consumable", False)}
    return validation


def _run_acceptance(backend: Any, episode: tasks.Episode, spec: RuntimeSpec, directory: Path,
                    identity: dict, bounds: _Bounds) -> dict:
    """Real checkpoint engineering checks, including deliberately forced control tokens.

    These probes never enter a scientific ledger or a performance-based gate.
    Native-reference calls bypass our registered attention callback entirely.
    """
    import torch
    from transformers import DynamicCache
    from mb.v6_native import NativeBackend, _FORWARD

    checks = {name: False for name in NATIVE_CHECKS}
    started = time.monotonic()
    torch.cuda.reset_peak_memory_stats(backend.device)

    def reference(ids: tuple[int, ...], cache: Any = None):
        bounds.check()
        if _FORWARD.get() is not None or backend.model.config._attn_implementation != "sdpa":
            raise ValueError("Independent reference is not native SDPA")
        cache = DynamicCache(config=backend.model.config) if cache is None else cache
        pos = cache.get_seq_length()
        tensor = torch.tensor([ids], device=backend.device, dtype=torch.long)
        positions = torch.arange(pos, pos + len(ids), device=backend.device)
        with torch.no_grad():
            output = backend.model.model(input_ids=tensor, past_key_values=cache, use_cache=True,
                attention_mask=torch.ones(1, pos + len(ids), device=backend.device, dtype=torch.long),
                position_ids=positions[None], cache_position=positions)
            logits = backend.model.lm_head(output.last_hidden_state[:, -1]).float()
        return cache, logits

    def same(state: Any, cache: Any, logits: Any) -> None:
        if not torch.equal(state.native_logits, logits) or state.cache.get_seq_length() != cache.get_seq_length():
            raise ValueError("Native logits/cache length differs from independent reference")
        if len(state.cache.layers) != len(cache.layers) or any(
                not torch.equal(a.keys, b.keys) or not torch.equal(a.values, b.values)
                for a, b in zip(state.cache.layers, cache.layers)):
            raise ValueError("Native K/V differs from independent reference")

    system, users = tasks.initial_prompts(episode)
    state = backend.create(system, users[0])
    cache, logits = reference(state.consumed_tokens)
    same(state, cache, logits)
    sender = backend.create(system, users[1])
    foreign = (backend.step(sender, (), 0.0),)
    for _ in range(3):
        export = backend.step(state, foreign, 0.0)
        cache, logits = reference((export.token,), cache)
        same(state, cache, logits)
    checks["native_same_shape"] = checks["nonempty_zero_gain"] = True
    attention_metrics = _check_foreign_attention(backend, state, foreign)
    checks["foreign_attention_reference"] = True

    # Full work clocks with both active histories, then actual native decisions.
    engine = EpisodeRunner(backend, spec, identity["profile"]["key"])
    initial = engine.initialize(episode)
    engine.prepare(episode, initial, 1)
    first, reversed_pair = engine.clone(initial), engine.clone(initial)
    tape, held = engine.work(first, "LIVE")
    swapped = EpisodeRunner(backend, spec, identity["profile"]["key"], side_order=(1, 0))
    swapped.work(reversed_pair, "LIVE")
    if engine.digest(first) != swapped.digest(reversed_pair):
        raise ValueError("A/B evaluation order changes the paired state")
    checks["paired_order"] = True

    bounds.check(disk=True)
    writer = NativeArchiveWriter(directory / "acceptance_archives", backend, identity)
    for seq, (kind, value, digest) in enumerate((
            ("pair", initial, engine.digest(initial)),
            ("tape", tape, canonical_digest(tape.identity())))):
        writer({"episode_id": episode.episode_id, "sequence": seq, "kind": kind,
                "label": "hardware_acceptance", "digest": digest, "value": value})
    # Rebind restored tensors to an independent backend owner with the same weights.
    restored_backend = NativeBackend(backend.model, backend.tokenizer, hardware_acceptance_authorized=True)
    reader = NativeArchiveWriter(directory / "acceptance_archives", restored_backend, identity, resume=True)
    restored = {row["meta"]["kind"]: reader.load(name) for name, row in reader.index.items()}
    replay_engine = EpisodeRunner(restored_backend, spec, identity["profile"]["key"])
    if replay_engine.digest(restored["pair"]) != engine.digest(initial):
        raise ValueError("Persisted pair/world differs after restore")
    replay_engine.work(restored["pair"], "Replay", tape=restored["tape"], focal=0)
    if replay_engine.digest(restored["pair"]) != engine.digest(first):
        raise ValueError("Persisted zero-change tape does not reproduce live K/V")
    checks["persisted_pair_and_tape"] = True
    del restored, restored_backend, reader, reversed_pair

    engine.actions(episode, first, held, {"kind": "natural", "policy": "LIVE", "checkpoint": 0,
                                         "arm": "LIVE", "version": 1})
    parent = engine.digest(first)
    engine.pulses(episode, first, 2)
    if engine.digest(first) != parent:
        raise ValueError("Two-round branches changed their parent")
    checks["two_round_replay"] = True

    # The complete finite table is audited offline. Execute every distinct native
    # recovery envelope, including header starts/ends, EOT, other controls and holes.
    categories = {}
    for token in sorted(backend.tokens.control_ids):
        rule = backend.tokens.recovery(token)
        categories.setdefault((rule.category, rule.suffix), token)
    ordinary = next(i for i in sorted(backend.tokens.defined_ids) if backend.tokens.ordinary(i)
                    and i not in backend.tokens.choice_ids(("1", "2", "3", "4")))
    categories[("ordinary_answer", backend.tokens.close_ids)] = ordinary
    missing = set(range(backend.tokens.vocab_size)) - backend.tokens.defined_ids
    if missing:
        categories[("unassigned_output_id", backend.tokens.close_ids)] = min(missing)
    tested = []
    source = backend.create(system, users[0])
    for (category, suffix), token in categories.items():
        bounds.check()
        probe = backend.probe(source, "Select one ID: 1 left; 2 right; 3 up; 4 down.",
                              ("1", "2", "3", "4"), (), 0.0)
        before = probe.state.consumed_tokens
        layers = tuple((layer.keys.clone(), layer.values.clone()) for layer in probe.state.cache.layers)
        ref = DynamicCache(ddp_cache_data=layers, config=backend.model.config)
        # Explicit engineering token forcing, not substituted scientific behavior.
        probe.token = token
        probe.state.seal["token"] = token
        probe.state.seal_checksum = backend.digest(probe.state)
        result = backend.commit_answer(probe, (), 0.0)
        ref, logits = reference((token,), ref)
        if suffix:
            ref, logits = reference(suffix, ref)
        same(result, ref, logits)
        if result.open or result.consumed_tokens != (*before, token, *suffix):
            raise ValueError("Actual control token was replaced or closed twice")
        backend.begin_user(result, "Next private round. Keep the declared record.")
        backend.step(result, (), 0.0)
        tested.append({"category": category, "token": token, "suffix": list(suffix)})
    checks["control_recovery"] = True
    spelling = backend.tokenizer.convert_ids_to_tokens(backend.tokens.close_ids[0])
    try:
        backend.tokens.user_turn("Partner text " + spelling)
    except ValueError:
        checks["text_control_policy"] = True
    else:
        raise ValueError("Text reference admits native control-token injection")
    bounds.check(disk=True)
    if not all(checks.values()):
        raise ValueError("Native acceptance checks are incomplete")
    return {"version": "v6-native-acceptance-1", "status": "passed", "backend_kind": "native",
        "scientific_data": False, "model_profile": identity["profile"]["key"],
        "native_model_identity": backend.model_identity,
        "source_manifest_sha256": identity["provenance"]["source_manifest_sha256"],
        "tokenizer_manifest_sha256": identity["tokenizer_manifest_sha256"],
        "checks": checks, "foreign_attention_metrics": attention_metrics, "recovery_cases": tested, "forced_tokens_engineering_only": True,
        "work_tokens": spec.work_tokens, "identity_sha256": canonical_digest(identity),
        "elapsed_seconds": time.monotonic()-started,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(backend.device),
        "limitations": ["Text-reference native control spellings fail closed; no escaping policy is applied.",
                        "Acceptance passes engineering invariants, not scientific admission or throughput projection."]}


def audit_noop_resume(plan_path: str | Path, admission_path: str | Path) -> dict:
    plan = _plan(Path(plan_path), Path(admission_path))
    if plan["stage"] != "smoke":
        raise ValueError("Engineering no-op resume certification requires the smoke stage")
    directory = Path(plan["output_dir"])
    before = {**_files(directory), "completion.json": {"bytes": (directory/"completion.json").stat().st_size,
                                                      "sha256": file_sha256(directory/"completion.json")}}
    report = execute(plan_path, admission_path, resume=True)
    after = {**_files(directory), "completion.json": {"bytes": (directory/"completion.json").stat().st_size,
                                                     "sha256": file_sha256(directory/"completion.json")}}
    if before != after:
        raise ValueError("Completed native resume changed retained bytes")
    return {"version": "v6-native-resume-1", "stage": "smoke", "status": "complete",
        "backend_kind": "native", "model_profile": plan["model_profile"],
        "native_model_identity": report["native_model_identity"],
        "source_manifest_sha256": plan["_admission"]["source_manifest_sha256"],
        "identity_sha256": report["identity_sha256"], "byte_identical": True,
        "file_count": len(before), "inventory_sha256": canonical_digest(before),
        "completion_pin": {"path": str(directory/"completion.json"), "sha256": file_sha256(directory/"completion.json")}}


def _check_foreign_attention(backend: Any, state: Any, foreign: tuple) -> dict:
    """Audit positive-link math on each actual checkpoint attention layer.

    A separate joint softmax retains the native own-SDPA rounding contribution.
    This checks the proposed interface; it does not establish a scientific effect.
    """
    import torch
    from transformers import AttentionInterface
    from transformers.integrations.sdpa_attention import sdpa_attention_forward
    from mb.v6_native import ATTENTION_NAME, _FORWARD, _attention

    seen, errors = set(), []
    def checked(module, query, key, value, mask, **kwargs):
        actual, weights = _attention(module, query, key, value, mask, **kwargs)
        context = _FORWARD.get()
        index = context.modules[id(module)]
        fk, fv = context.layers[index]
        repeats = query.shape[1] // key.shape[1]
        k = torch.cat((key, fk), 2).repeat_interleave(repeats, dim=1).float()
        v = torch.cat((value, fv), 2).repeat_interleave(repeats, dim=1).float()
        scale = kwargs.get("scaling") or query.shape[-1] ** -.5
        scores = (query.float() @ k.transpose(-1, -2)) * scale
        own_n = key.shape[-2]
        if mask is not None:
            own_mask = mask[..., -1:, :own_n]
            scores[..., :own_n] = (scores[..., :own_n].masked_fill(~own_mask, -torch.inf)
                                   if own_mask.dtype == torch.bool else scores[..., :own_n]+own_mask.float())
        scores[..., own_n:] += math.log(context.gain)
        probabilities = torch.softmax(scores, dim=-1)
        joint = probabilities @ v
        own_manual = torch.softmax(scores[..., :own_n], dim=-1) @ v[..., :own_n, :]
        own_native, _ = sdpa_attention_forward(module, query, key, value, mask, **kwargs)
        own_mass = probabilities[..., :own_n].sum(-1, keepdim=True)
        expected = (joint + own_mass * (own_native.transpose(1, 2).float()-own_manual)).transpose(1, 2)
        tolerance = 2 * torch.finfo(actual.dtype).eps * max(1.0, float(expected.abs().max())) + 2e-6
        error = float((actual.float()-expected).abs().max())
        if not math.isfinite(error) or error > tolerance:
            raise ValueError("Positive foreign attention differs from independent joint softmax")
        errors.append({"layer": index, "max_abs_error": error, "tolerance": tolerance})
        seen.add(index)
        return actual, weights
    AttentionInterface.register(ATTENTION_NAME, checked)
    try:
        backend.step(backend.clone(state), foreign, 0.5)
    finally:
        AttentionInterface.register(ATTENTION_NAME, _attention)
    if seen != set(range(len(backend.model.model.layers))) or _FORWARD.get() is not None:
        raise ValueError("Foreign attention audit missed a layer or leaked context")
    return {"gain": .5, "layers": len(seen), "errors": errors,
            "reference": "independent joint softmax with native-own SDPA rounding retained"}
