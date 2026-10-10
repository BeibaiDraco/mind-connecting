"""Run one fixed continuation after explicit funding approval and guarded startup.

This controller never starts an instance. Preparation and inspection are local;
execution is restricted to Linux, an approved cumulative budget, live guards and
one persisted controller intent. Every formal completion backs up and stops.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import run_v5_stage as stage
from mb import ledger

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v5-continuation-launch-1"
PHASES = ("native", "smoke", "resume", "formal")
FORMAL_SECONDS = {"provenance": 63_990.0, "static": 50_062.5}
ENGINEERING_SECONDS = (600.0, 600.0, 300.0)
REMOTE_CONTROLS_SHA = "b3c199a428671a66619e25346193d53a9add1d65bdd5685a6bf324150caa04c4"


def once(path: Path, obj: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if path.exists():
        if path.read_text() != payload:
            raise ValueError("refusing to replace a preparation artifact")
        return
    with path.open("x") as fh:
        fh.write(payload)


def plan(study: str, control: Path, budget_file: Path, guard_command_file: Path,
         remote_controls: Path, remaining_other_seconds: float) -> dict:
    if study not in FORMAL_SECONDS:
        raise ValueError("unknown fixed study")
    return {"version": VERSION, "study": study, "phases": list(PHASES),
            "control_dir": str(control), "budget_file": str(budget_file),
            "guard_command_file": str(guard_command_file),
            "remote_controls": str(remote_controls), "remote_controls_sha256": REMOTE_CONTROLS_SHA,
            "config": f"configs/v5_continuation/{study}_confirm.yaml",
            "freeze": f"configs/v5_continuation/{study}_freeze.json",
            "smoke_config": "configs/v5/provenance/llama31_smoke.yaml",
            "smoke_freeze": "configs/v5_continuation/smoke_freeze.json",
            "estimated_seconds": [*ENGINEERING_SECONDS, FORMAL_SECONDS[study]],
            "remaining_other_seconds": remaining_other_seconds,
            "controller_sha256": ledger.file_sha256(Path(__file__)),
            "paid_start_authorized_by_this_plan": False}


def validate_plan(doc: dict) -> None:
    study = doc.get("study")
    if study not in FORMAL_SECONDS:
        raise ValueError("unknown fixed study")
    expected = plan(study, Path(doc["control_dir"]), Path(doc["budget_file"]),
                    Path(doc["guard_command_file"]), Path(doc["remote_controls"]),
                    doc["remaining_other_seconds"])
    if doc != expected:
        raise ValueError("controller plan changed")
    for key in ("control_dir", "budget_file", "guard_command_file", "remote_controls"):
        value = Path(doc[key])
        if not value.is_absolute() or value.resolve().is_relative_to(ROOT):
            raise ValueError("private controls require absolute paths outside the repository")
    reserve = doc["remaining_other_seconds"]
    if type(reserve) not in (int, float) or not math.isfinite(reserve) or reserve < 0:
        raise ValueError("invalid remaining package reserve")
    minimum = sum(ENGINEERING_SECONDS) + FORMAL_SECONDS["static"] if study == "provenance" else 0
    if reserve < minimum:
        raise ValueError("first study must reserve the entire approved STATIC continuation")


def admission(doc: dict, budget: dict, now: float | None = None) -> float:
    validate_plan(doc)
    receipt_path = Path(budget["continuation_approval_file"])
    if receipt_path.resolve().is_relative_to(ROOT) or not receipt_path.is_absolute():
        raise ValueError("approval receipt must remain private")
    if ledger.file_sha256(receipt_path) != budget.get("continuation_approval_sha256"):
        raise ValueError("approval receipt changed")
    receipt = stage.read(receipt_path)
    if (receipt.get("approved") is not True or receipt.get("scope") != "v5_llama_fixed_continuations"
            or receipt.get("studies") != ["provenance", "static"]
            or receipt.get("cumulative_cap_usd") != budget.get("cap_usd")
            or not receipt.get("authorization_text")
            or receipt.get("original_full_plan_sha256") != budget.get("original_full_plan_sha256")):
        raise ValueError("explicit approval of both fixed continuations and a numerical cap is required")
    original_path = Path(budget["original_full_plan_file"])
    if ledger.file_sha256(original_path) != budget["original_full_plan_sha256"]:
        raise ValueError("original cumulative budget provenance changed")
    original = stage.read(original_path)["budget"]
    for key in ("scope", "hourly_usd", "prior_spend_usd", "bandwidth_reserve_usd",
                "shutdown_reserve_usd", "started_at_epoch"):
        if budget.get(key) != original.get(key):
            raise ValueError("original spending anchor, rate or reserves changed")
    return stage.budget_deadline(budget, now=now)


def require_room(doc: dict, index: int, deadline: float, now: float) -> None:
    remaining = sum(doc["estimated_seconds"][index:]) + doc["remaining_other_seconds"]
    if now + remaining + 120 >= deadline:
        raise ValueError("remaining fixed package does not fit the approved cumulative budget")


def stage_argv(doc: dict, index: int, smoke_run: Path | None) -> list[str]:
    control = Path(doc["control_dir"])
    formal = PHASES[index] == "formal"
    argv = [sys.executable, str(ROOT / "scripts/run_v5_stage.py"),
            "--config", str(ROOT / doc["config" if formal else "smoke_config"]),
            "--freeze", str(ROOT / doc["freeze" if formal else "smoke_freeze"]),
            "--budget-file", doc["budget_file"], "--control-dir", str(control),
            "--estimated-seconds", str(doc["estimated_seconds"][index])]
    if not formal:
        argv += ["--limit", "4", "--keep-session"]
    if index == 0:
        argv += ["--native-acceptance-output", str(control / "native.json")]
    else:
        argv += ["--native-evidence", str(control / "native.json")]
    if index in (2, 3):
        if smoke_run is None:
            raise ValueError("complete smoke run required")
        argv += ["--smoke-before", str(control / "llama31_8b_instruct_smoke_before_audit.json")]
        argv += ["--resume" if index == 2 else "--smoke-run", str(smoke_run)]
    return argv


def guard_proof(doc: dict) -> None:
    command = stage.private_argv(doc, "guard_command_file")
    if not stage.quiet_command(command, timeout=30):
        raise ValueError("fresh exact-instance guard proof is required")


def prior_completion(doc: dict, budget: dict) -> None:
    if doc["study"] != "static":
        return
    parent = Path(doc["control_dir"]).parent
    prior = parent / "provenance"
    receipt = stage.read(parent / "provenance_stopped_backup.json")
    last = stage.read(prior / "last_stage.json")
    ack = stage.read(prior / "backup_ack.json")
    request = stage.read(prior / "backup_request.json")
    original = stage.read(Path(budget["original_full_plan_file"]))
    target = original.get("container_id_sha256")
    if not isinstance(target, str) or len(target) != 64 or any(c not in "0123456789abcdef" for c in target):
        raise ValueError("original instance target binding is missing")
    if (receipt.get("provider_stopped_verified") is not True
            or receipt.get("target_sha256") != target
            or receipt.get("prior_control_dir") != str(prior)
            or receipt.get("last_stage_sha256") != ledger.file_sha256(prior / "last_stage.json")
            or receipt.get("backup_ack_sha256") != ledger.file_sha256(prior / "backup_ack.json")
            or receipt.get("backup_request_sha256") != ledger.file_sha256(prior / "backup_request.json")
            or not (last.get("collection_complete") and last.get("gate_passed") and last.get("backup_verified"))
            or last.get("stage") != "v5_llama31_provenance_confirm"
            or ack.get("verified") is not True
            or any(ack.get(k) != request.get(k) for k in ("nonce", "inventory_sha256", "identity_sha256"))
            or request.get("run_dir") != last.get("run_dir")):
        raise ValueError("STATIC requires verified provenance completion, backup and prior provider stop")
    checked = receipt.get("checked_epoch")
    if type(checked) not in (int, float) or not last.get("at_epoch", math.inf) <= checked <= time.time():
        raise ValueError("invalid prior completion receipt time")


def execute(doc: dict) -> None:
    if platform.system() != "Linux":
        raise ValueError("execution is restricted to the rented Linux GPU host")
    budget = stage.read(Path(doc["budget_file"]))
    deadline = admission(doc, budget)
    prior_completion(doc, budget)
    control = Path(doc["control_dir"])
    control.mkdir(parents=True, exist_ok=True)
    # All study directories share this lease; a crashed controller needs explicit reconciliation.
    with (control.parent / "continuation-gpu.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise stage.StageBusy("another continuation controller owns the GPU")
        global_intent = control.parent / "continuation-active.json"
        if global_intent.exists() and stage.read(global_intent).get("active"):
            raise stage.StageBusy("unresolved continuation intent; reconcile the original child first")
        if (control / "controller_intent.json").exists():
            raise stage.StageBusy("existing controller intent requires explicit identity-preserving recovery")
        guard_proof(doc)
        require_room(doc, 0, deadline, time.time())
        gpu = subprocess.run(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
                             capture_output=True, check=True, timeout=15)
        if gpu.stdout.strip():
            raise stage.StageBusy("an existing GPU process must be reconciled before launch")
        once(control / "controller_intent.json", {"study": doc["study"], "at_epoch": time.time(),
             "plan_sha256": ledger.canonical_hash(doc, n=64)})
        stage.save(global_intent, {"active": True, "study": doc["study"], "control_dir": str(control)})
        def interrupted(signum, frame):
            raise KeyboardInterrupt(f"signal {signum}")
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGHUP, interrupted)
        smoke_run = None
        try:
            for index, phase in enumerate(PHASES):
                guard_proof(doc)
                require_room(doc, index, deadline, time.time())
                argv = stage_argv(doc, index, smoke_run)
                once(control / f"{phase}_command.json", argv)
                stage.save(control / "current_phase.json", {"phase": phase, "index": index})
                with (control / f"{phase}.log").open("xb") as output:
                    proc = subprocess.Popen(argv, cwd=ROOT, stdin=subprocess.DEVNULL,
                         stdout=output, stderr=output, start_new_session=True,
                         env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                              "TOKENIZERS_PARALLELISM": "false"})
                    try:
                        code = proc.wait(timeout=max(1, deadline - time.time()))
                    finally:
                        stage.terminate_process(proc)
                last = stage.read(control / "last_stage.json")
                if code or not (last.get("collection_complete") and last.get("gate_passed")
                                and last.get("backup_verified")):
                    raise RuntimeError("stage incomplete, failed or not durably backed up")
                once(control / f"{phase}_complete.json", last)
                if phase == "smoke":
                    smoke_run = Path(last["run_dir"])
        finally:
            stopped = stage.stop_provider(budget, control, "continuation_controller_terminal")
            # Provider stop commonly terminates this process; the independent local controller
            # must reconcile this receipt with a fresh provider query before the next restore.
            if stopped:
                stage.save(global_intent, {"active": False, "study": doc["study"],
                                          "provider_stopped_verified": True})


def backup(doc: dict) -> None:
    """Use the previously reviewed inventory/ACK transport, including failed collections."""
    if platform.system() != "Linux":
        raise ValueError("remote backup inventory must be created on Linux")
    validate_plan(doc)
    helper = Path(doc["remote_controls"])
    if ledger.file_sha256(helper) != REMOTE_CONTROLS_SHA:
        raise ValueError("reviewed backup helper changed")
    spec = importlib.util.spec_from_file_location("continuation_remote_controls", helper)
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    control = Path(doc["control_dir"])
    budget = stage.read(Path(doc["budget_file"]))
    deadline = stage.budget_deadline(budget)
    data = Path(os.environ["MB_DATA_ROOT"])
    if data != Path("/workspace/mb-data") or not data.is_dir():
        raise ValueError("explicit existing deployment data root required")
    phase = stage.read(control / "current_phase.json")["phase"]
    if phase not in PHASES:
        raise ValueError("unknown backup phase")
    dest = data / "engineering/v5/continuation-20261010" / doc["study"] / phase
    dest.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / doc[k] for k in ("config", "freeze", "smoke_config", "smoke_freeze")]
    sources += [ROOT / "docs/protocol/FREEZE_protocol_v5_continuation_algorithm.json"]
    sources += [p for p in (control / "native.json",
          control / "llama31_8b_instruct_smoke_before_audit.json",
          control / "llama31_8b_instruct_smoke_resume_audit.json") if p.is_file()]
    sources.append(control / "last_stage.json")
    paths, receipt = [], None
    for source in sources:
        raw = source.read_bytes()
        target = dest / (hashlib.sha256(raw).hexdigest()[:16] + "_" + source.name)
        if target.exists() and target.read_bytes() != raw:
            raise ValueError("immutable backup evidence changed")
        if not target.exists():
            with target.open("xb") as fh:
                fh.write(raw)
        relative = str(target.relative_to(data))
        paths.append(relative)
        if source.name == "last_stage.json":
            receipt = relative
    evidence = {"paths": sorted(paths), "acceptance_json": receipt}
    evidence_path = control / (phase + "_backup_" + ledger.canonical_hash(evidence) + ".json")
    once(evidence_path, evidence)
    rc.backup(SimpleNamespace(control_dir=control, evidence_plan=evidence_path, deadline=deadline))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "check", "execute", "backup"))
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--study", choices=FORMAL_SECONDS)
    parser.add_argument("--control-dir", type=Path)
    parser.add_argument("--budget-file", type=Path)
    parser.add_argument("--guard-command-file", type=Path)
    parser.add_argument("--remote-controls", type=Path)
    parser.add_argument("--remaining-other-seconds", type=float)
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    if args.action == "plan":
        doc = plan(args.study, args.control_dir, args.budget_file, args.guard_command_file,
                   args.remote_controls, args.remaining_other_seconds)
        validate_plan(doc)
        once(args.plan, doc)
    else:
        doc = stage.read(args.plan)
        validate_plan(doc)
        if args.action == "execute":
            try:
                if args.detach:
                    if platform.system() != "Linux":
                        raise ValueError("detached execution is restricted to Linux")
                    control = Path(doc["control_dir"])
                    if (control / "controller.log").exists():
                        raise stage.StageBusy("existing detached controller requires reconciliation")
                    budget = stage.read(Path(doc["budget_file"]))
                    admission(doc, budget)
                    prior_completion(doc, budget)
                    guard_proof(doc)
                    control.mkdir(parents=True, exist_ok=True)
                    try:
                        output = (control / "controller.log").open("xb")
                    except FileExistsError as exc:
                        raise stage.StageBusy("another detached controller claimed the log") from exc
                    with output:
                        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                             "execute", "--plan", str(args.plan.resolve())], cwd=ROOT,
                             stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                             start_new_session=True)
                    print(json.dumps({"controller_pid": proc.pid, "detached": True,
                                      "health_receipts_required": True}))
                    return 0
                execute(doc)
            except stage.StageBusy:
                raise
            except BaseException:
                if platform.system() == "Linux":
                    stage.stop_provider(stage.read(Path(doc["budget_file"])), Path(doc["control_dir"]),
                                        "continuation_controller_failure")
                raise
        elif args.action == "backup":
            backup(doc)
    print(json.dumps({"prepared": True, "study": doc["study"], "action": args.action}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
