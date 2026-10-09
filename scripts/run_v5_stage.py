"""Instance-local v5 stage launcher with an independent deadline watchdog.

Private JSON supplies a newly approved cumulative budget and provider stop /
verification / backup argv files. No credentials or argv are copied to reports.
Default completion requests and verifies shutdown after verified backup. Only
short prerequisite stages may explicitly keep the session for the next stage.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

from mb import run
from freeze_v5 import ROOT, verify
from supervise_v4 import terminate_process


class StageBusy(RuntimeError):
    """A healthy owner already controls the stage; do not stop its instance."""


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def save(path: Path, obj: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def best_effort_save(path: Path, obj: dict) -> None:
    try:
        save(path, obj)
    except OSError:
        pass  # Evidence failure must never prevent a provider shutdown request.


def budget_deadline(doc: dict, now: float | None = None) -> float:
    now = time.time() if now is None else now
    if doc.get("approved") is not True or doc.get("scope") != "v5":
        raise ValueError("a newly approved v5 budget is required")
    keys = ("cap_usd", "hourly_usd", "prior_spend_usd", "bandwidth_reserve_usd",
            "shutdown_reserve_usd", "started_at_epoch")
    if any(isinstance(doc.get(k), bool) or not isinstance(doc.get(k), (int, float))
           or not math.isfinite(doc[k]) or doc[k] < 0 for k in keys):
        raise ValueError("invalid finite nonnegative budget fields")
    if doc["hourly_usd"] <= 0 or doc["cap_usd"] <= 0 or doc["started_at_epoch"] > now:
        raise ValueError("invalid rate, cap or future spending anchor")
    if doc["shutdown_reserve_usd"] < doc["hourly_usd"] / 12:
        raise ValueError("reserve at least five billed minutes for bounded shutdown retries")
    left = doc["cap_usd"] - sum(doc[k] for k in
             ("prior_spend_usd", "bandwidth_reserve_usd", "shutdown_reserve_usd"))
    deadline = doc["started_at_epoch"] + left * 3600 / doc["hourly_usd"]
    if deadline <= now:
        raise ValueError("cumulative spending cap has no remaining runtime")
    return deadline


def private_argv(doc: dict, key: str) -> list[str]:
    path = Path(doc[key])
    if not path.is_absolute():
        raise ValueError("private command files require absolute paths")
    if path.resolve().is_relative_to(ROOT):
        raise ValueError("private command files must not live in the repository")
    argv = json.loads(path.read_text())
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
        raise ValueError("private command must be a nonempty argv list")
    return argv


def quiet_command(argv: list[str], timeout: float = 45) -> bool:
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=timeout, check=False)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def stop_provider(doc: dict, control: Path, reason: str) -> bool:
    # Serialize competing completion/deadline stop paths without killing a guard.
    try:
        lock = (control / "shutdown.lock").open("a+")
    except OSError:
        lock = None
    with lock if lock is not None else nullcontext():
        if lock is not None:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX)
            except OSError:
                pass
        for attempt in range(3):
            requested = quiet_command(private_argv(doc, "stop_command_file"))
            verified = quiet_command(private_argv(doc, "verify_stopped_command_file"))
            best_effort_save(control / "shutdown.json", {"reason": reason, "attempt": attempt + 1,
                 "requested": requested, "verified_stopped": verified, "at_epoch": time.time()})
            if verified:
                return True
            time.sleep(5)
    return False


def watchdog(doc: dict, control: Path) -> int:
    with (control / "watchdog.lock").open("a+") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        deadline = budget_deadline(doc)
        monotonic_deadline = time.monotonic() + max(0, deadline - time.time())
        best_effort_save(control / "watchdog.json", {"pid": os.getpid(), "deadline_epoch": deadline,
             "budget_hash": hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()})
        while time.time() < deadline and time.monotonic() < monotonic_deadline:
            if (control / "shutdown.json").exists() and read(control / "shutdown.json").get("verified_stopped"):
                return 0
            time.sleep(min(5, max(0.01, deadline - time.time()), max(0.01, monotonic_deadline - time.monotonic())))
        return 0 if stop_provider(doc, control, "budget_deadline") else 1


def validate_launch(config: Path, freeze: Path, limit: int | None) -> run.StageConfig:
    frozen = verify(freeze, require_kind="stage")
    path = Path(frozen["config_path"])
    path = path if path.is_absolute() else ROOT / path
    if path.resolve() != config.resolve():
        raise ValueError("stage freeze belongs to another configuration")
    cfg = run.StageConfig.load(config)
    run.validate_stage_sources(cfg)
    if (cfg.params or {}).get("provenance_contract"):
        from make_v5_provenance import verify_config_contract
    else:
        from mb.v5_static import verify_config_contract
    verify_config_contract(cfg)
    smoke = bool((cfg.params or {}).get("smoke_only"))
    if smoke != (limit == 4) or (limit is not None and limit != 4):
        raise ValueError("only prescribed four-episode technical smoke may use --limit")
    return cfg


def guarded_child(argv: list[str], deadline: float, receipt: Path, stage: str) -> int:
    """A persisted intent blocks duplicate recovery even across SIGKILL gaps."""
    if receipt.exists() and read(receipt).get("active"):
        raise RuntimeError("unresolved prior child; verify stopped state and original run before recovery")
    save(receipt, {"active": True, "state": "launch_intent", "stage": stage, "at_epoch": time.time()})
    monotonic_deadline = time.monotonic() + max(0, deadline - time.time())
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        save(receipt, {"active": True, "state": "running", "stage": stage,
                       "pid": process.pid, "at_epoch": time.time()})
        while process.poll() is None:
            if time.time() >= deadline or time.monotonic() >= monotonic_deadline:
                raise RuntimeError("cumulative budget deadline reached")
            time.sleep(.25)
        return process.returncode
    finally:
        terminate_process(process)
        if process.poll() is not None:
            best_effort_save(receipt, {"active": False, "state": "finished", "stage": stage,
                 "pid": process.pid, "exit_code": process.returncode, "at_epoch": time.time()})


def collected_run(cfg: run.StageConfig, before: set[Path], resume: Path | None) -> Path:
    candidates = [resume] if resume else [p for p in run.results_dir().iterdir() if p not in before and p.is_dir()]
    found = []
    for path in candidates:
        if not path or not (path / "identity.json").exists():
            continue
        if read(path / "identity.json").get("stage_config") == json.loads(json.dumps(cfg.resolved())):
            found.append(path)
    if len(found) != 1:
        raise RuntimeError("cannot identify exactly one run from this invocation")
    return found[0]


def scientific_gate(cfg: run.StageConfig, root: Path) -> tuple[bool, dict]:
    if cfg.stage == "calibrate":
        from mb.v5_static import read_calibration
        result = read_calibration(root, cfg.params["model_assets"]["sha256"])
        return bool(result["available_layers"]), {"available_layers": result["available_layers"]}
    result = {}
    for step in cfg.post:
        result = run.run_post(step, root, cfg)
        if step in ("v5_static_contrasts", "v5_provenance_contrasts"):
            # Formal outcomes, including a failed matching recheck, are results
            # to report; only usable complete collection decides completion.
            return bool(result.get("consumable")), {"step": step, "gate": "complete_analysis",
                                                     "effect_based_gate": False}
        if not result.get("consumable") or result.get("gate") not in ("pass", "matched", "refine"):
            return False, {"step": step, "gate": result.get("gate"), "consumable": result.get("consumable")}
    return True, {"gate": result.get("gate")}


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--budget-file", type=Path, required=True)
    parser.add_argument("--control-dir", type=Path, required=True)
    parser.add_argument("--estimated-seconds", type=float)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--keep-session", action="store_true")
    parser.add_argument("--native-acceptance-output", type=Path)
    parser.add_argument("--native-evidence", type=Path)
    parser.add_argument("--smoke-run", type=Path)
    parser.add_argument("--smoke-before", type=Path)
    parser.add_argument("--detach", action="store_true", help="detach the entire supervisor from SSH")
    parser.add_argument("--log-file", type=Path)
    parser.add_argument("--watchdog", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if platform.system() != "Linux":
        parser.error("execution is restricted to the rented Linux GPU host")
    if args.control_dir.resolve().is_relative_to(ROOT) or args.budget_file.resolve().is_relative_to(ROOT):
        parser.error("private controls must be outside the repository")
    doc = read(args.budget_file)
    for key in ("stop_command_file", "verify_stopped_command_file", "backup_command_file"):
        private_argv(doc, key)
    args.control_dir.mkdir(parents=True, exist_ok=True)
    if args.watchdog:
        return watchdog(doc, args.control_dir)
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"received signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    if args.detach:
        if not args.log_file or args.log_file.resolve().is_relative_to(ROOT):
            parser.error("detached supervisor requires a private --log-file outside the repository")
        budget_deadline(doc)
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        with args.log_file.open("ab") as output:
            child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                      *[a for a in sys.argv[1:] if a != "--detach"]],
                                     stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                     start_new_session=True)
        print(json.dumps({"supervisor_pid": child.pid, "detached": True,
                          "note": "Check private control receipts for acceptance; PID alone is not startup success."}))
        return 0
    if not args.config or not args.freeze or not args.estimated_seconds:
        parser.error("stage requires config, freeze and measured/conservative time projection")
    deadline = budget_deadline(doc)
    if not math.isfinite(args.estimated_seconds) or args.estimated_seconds <= 0 or time.time() + args.estimated_seconds > deadline:
        parser.error("time projection exceeds cumulative approved budget")
    cfg = validate_launch(args.config, args.freeze, args.limit)
    if args.native_acceptance_output:
        if not (cfg.params or {}).get("smoke_only") or args.resume:
            parser.error("native acceptance uses the smoke config, never research/resume")
    else:
        from check_v5_acceptance import verify as verify_native
        if not args.native_evidence:
            parser.error("native GPU acceptance evidence is required before smoke/research")
        verify_native(args.native_evidence, cfg.model_profile)
        if not (cfg.params or {}).get("smoke_only"):
            from check_v5_smoke import audit
            if not args.smoke_run or not args.smoke_before:
                parser.error("research requires a complete audited smoke and no-op resume")
            result = audit(args.smoke_run, read(args.smoke_before))
            if result["model_profile"] != cfg.model_profile or not result["resume_verified"]:
                parser.error("smoke/resume evidence belongs to another checkpoint")
    if args.keep_session and cfg.n_episodes == 600:
        parser.error("formal completion must back up and stop; no keep-session")
    if not os.environ.get("MB_DATA_ROOT") or not Path(os.environ["MB_DATA_ROOT"]).is_dir():
        parser.error("an explicit existing MB_DATA_ROOT is required")
    with (args.control_dir / "stage.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise StageBusy("another supervisor already owns the stage; no second child launched")
        # One spending anchor is immutable for the entire rented session.
        budget_copy = args.control_dir / "budget.json"
        if budget_copy.exists() and read(budget_copy) != doc:
            raise ValueError("budget anchor changed; no implicit reset across stages")
        if not budget_copy.exists():
            with budget_copy.open("x") as fh:
                json.dump(doc, fh)
        if (args.control_dir / "shutdown.json").exists():
            raise ValueError("this session already requested shutdown; establish a new reviewed spending anchor")
        with (args.control_dir / "watchdog.log").open("ab") as log:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--watchdog",
                              "--budget-file", str(budget_copy), "--control-dir", str(args.control_dir)],
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        expected_hash = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
        ready = False
        for _ in range(30):
            if (args.control_dir / "watchdog.json").exists():
                state = read(args.control_dir / "watchdog.json")
                try:
                    os.kill(state["pid"], 0)
                    process_argv = Path(f"/proc/{state['pid']}/cmdline").read_bytes().split(b"\0")
                    ready = (str(Path(__file__).resolve()).encode() in process_argv
                             and b"--watchdog" in process_argv
                             and str(budget_copy).encode() in process_argv
                             and state["budget_hash"] == expected_hash and state["deadline_epoch"] == deadline)
                except (ProcessLookupError, FileNotFoundError):
                    ready = False
                if ready:
                    break
            time.sleep(0.1)
        if not ready:
            stop_provider(doc, args.control_dir, "watchdog_not_ready")
            raise RuntimeError("independent budget watchdog did not become ready")
        argv = [sys.executable, "-m", "mb.run", str(args.config)]
        if args.native_acceptance_output:
            argv = [sys.executable, str(ROOT / "scripts/check_v5_acceptance.py"),
                    "--model-profile", cfg.model_profile, "--output", str(args.native_acceptance_output)]
        elif args.limit:
            argv += ["--limit", str(args.limit)]
        if args.resume:
            argv += ["--resume", str(args.resume)]
        success = False
        try:
            results = run.results_dir()
            before_dirs = set(results.iterdir()) if results.exists() else set()
            exit_code = guarded_child(argv, deadline, args.control_dir / "active_child.json", cfg.stage)
            success = exit_code == 0
            if not success:
                raise RuntimeError("stage failed; original evidence retained")
            actual_run = None
            gate_ok, gate_detail = True, {"engineering": True}
            if args.native_acceptance_output:
                from check_v5_acceptance import verify as verify_native
                verify_native(args.native_acceptance_output, cfg.model_profile)
            else:
                actual_run = collected_run(cfg, before_dirs, args.resume)
                if (cfg.params or {}).get("smoke_only"):
                    from check_v5_smoke import audit
                    smoke_report = audit(actual_run, read(args.smoke_before) if args.smoke_before else None)
                    name = cfg.model_profile + ("_smoke_resume_audit.json" if args.smoke_before else "_smoke_before_audit.json")
                    path = args.control_dir / name
                    with path.open("x") as fh:
                        json.dump(smoke_report, fh, indent=2)
                else:
                    gate_ok, gate_detail = scientific_gate(cfg, actual_run)
            save(args.control_dir / "last_stage.json", {"stage": cfg.stage, "split": cfg.split,
                 "run_dir": str(actual_run) if actual_run else None, "collection_complete": True,
                 "gate_passed": gate_ok, "gate": gate_detail, "backup_verified": False, "at_epoch": time.time()})
            backup_ok = quiet_command(private_argv(doc, "backup_command_file"), timeout=900)
            if not backup_ok:
                success = False
                raise RuntimeError("backup verification failed; remote data retained")
            save(args.control_dir / "last_stage.json", {"stage": cfg.stage, "split": cfg.split,
                 "run_dir": str(actual_run) if actual_run else None, "collection_complete": True,
                 "gate_passed": gate_ok, "gate": gate_detail, "backup_verified": True, "at_epoch": time.time()})
            if not gate_ok:
                success = False
                raise RuntimeError("scientific prerequisite failed; branch stopped after backup")
        except BaseException:
            success = False
            raise
        finally:
            if not success or not args.keep_session:
                if not stop_provider(doc, args.control_dir, "completed" if success else "stage_failure"):
                    raise RuntimeError("provider stopped state could not be verified; action required")
    return 0


def main() -> int:
    """Once private stop controls are usable, even prelaunch failures stop billing."""
    try:
        return _main()
    except BaseException as exc:
        if isinstance(exc, StageBusy):
            raise
        if isinstance(exc, SystemExit) and exc.code in (None, 0):
            raise
        if platform.system() == "Linux":
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument("--budget-file", type=Path)
            parser.add_argument("--control-dir", type=Path)
            args, _ = parser.parse_known_args()
            if args.budget_file and args.control_dir:
                try:
                    if args.budget_file.resolve().is_relative_to(ROOT) or args.control_dir.resolve().is_relative_to(ROOT):
                        raise ValueError("private controls belong outside the repository")
                    doc = read(args.budget_file)
                    private_argv(doc, "stop_command_file")
                    private_argv(doc, "verify_stopped_command_file")
                    try:
                        args.control_dir.mkdir(parents=True, exist_ok=True)
                    except OSError:
                        pass
                    if not stop_provider(doc, args.control_dir, "launch_or_execution_failure"):
                        print("Provider stop could not be verified; immediate action required.", file=sys.stderr)
                except Exception:
                    print("Private shutdown controls unavailable; immediate provider check required.", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
