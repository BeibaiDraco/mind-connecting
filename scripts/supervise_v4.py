#!/usr/bin/env python3
"""Bounded v4 commands, cumulative budget checks, and an unconditional stop request.

Run this on the host that can invoke the provider stop command. A private JSON plan
is a list of {name, kind, command: [argv, ...], timeout_seconds, result_dir?}.
Commands may call SSH, but must sync their result files to result_dir before exit.
kind is command (engineering only), smoke, baseline, calibration, strength, match,
validity, or formal. Each scientific stage checks its fixed protocol gate.

Example (private files contain connection details; never commit them)::

    python scripts/supervise_v4.py --plan /private/tmp/acceptance-plan.json \
      --phase acceptance --hourly-usd 1.4 --prior-spend-usd 0.8 --bandwidth-usd 0.2 \
      --stop-command-file /private/tmp/stop-argv.json --journal /private/tmp/budget.jsonl

The stop file contains an argv JSON array. No shell is implied and command argv is
never copied into the journal. Stage output inherits the caller's output streams.
Later execution additionally requires --estimated-remaining-seconds from measured
throughput. Costs are conservative estimates, not provider billing. Prior spend
must include setup/idle time before this process; bandwidth includes known charges
and a conservative reserve. Optional bandwidth-file holds additional accrued USD
as {"additional_bandwidth_usd": number}; decreasing readings never refund budget.

A successful stop command means the stop request succeeded, not that provider
state was independently verified. The caller verifies stopped state separately.
This process cannot protect against host loss/SIGKILL; use a reliable supervisor
host and an independent provider timeout when available.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any, Callable, Sequence


KINDS = {"command", "smoke", "baseline", "calibration", "strength", "match", "validity", "formal"}
POST_FILES = {"baseline": "v4_baseline.json", "strength": "v4_strength.json", "match": "v4_match.json",
              "validity": "v4_validity.json", "formal": "v4_contrasts.json"}
SIZES = {"smoke": 4, "baseline": 60, "calibration": 60, "strength": 40, "match": 40,
         "validity": 80, "formal": 600}
SUFFIXES = {"smoke": "smoke", "baseline": "base", "calibration": "cal", "strength": "strength",
            "match": "match", "validity": "validity", "formal": "confirm"}


class BudgetExhausted(RuntimeError):
    pass


class CommandTimeout(RuntimeError):
    pass


class GateFailed(RuntimeError):
    pass


def finite_nonnegative(value: float, name: str, *, positive: bool = False) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0 or (positive and number == 0):
        raise ValueError(f"{name} must be finite and {'positive' if positive else 'nonnegative'}")
    return number


class Budget:
    """One cumulative clock for the entire invocation, never reset between stages."""

    def __init__(self, hourly_usd: float, prior_spend_usd: float, bandwidth_usd: float,
                 phase: str = "acceptance", *, clock: Callable[[], float] = time.monotonic,
                 bandwidth_reader: Callable[[], float] | None = None):
        if phase not in ("acceptance", "later"):
            raise ValueError("phase must be acceptance or later")
        self.hourly_usd = finite_nonnegative(hourly_usd, "hourly_usd", positive=True)
        self.prior_spend_usd = finite_nonnegative(prior_spend_usd, "prior_spend_usd")
        self.bandwidth_usd = finite_nonnegative(bandwidth_usd, "bandwidth_usd")
        self.phase, self.cap_usd = phase, (10.0 if phase == "acceptance" else 60.0)
        self.clock, self.started = clock, clock()
        self.bandwidth_reader = bandwidth_reader
        self.elapsed_seconds, self.additional_bandwidth_usd = 0.0, 0.0

    def spent(self, *, refresh_bandwidth: bool = True) -> float:
        self.elapsed_seconds = max(self.elapsed_seconds, self.clock() - self.started)
        if refresh_bandwidth and self.bandwidth_reader is not None:
            self.additional_bandwidth_usd = max(self.additional_bandwidth_usd, finite_nonnegative(
                self.bandwidth_reader(), "additional_bandwidth_usd"))
        return (self.prior_spend_usd + self.bandwidth_usd + self.additional_bandwidth_usd
                + self.elapsed_seconds * self.hourly_usd / 3600)

    def remaining_seconds(self, reserve_seconds: float = 0) -> float:
        return (self.cap_usd - self.spent()) * 3600 / self.hourly_usd - reserve_seconds

    def require_projection(self, seconds: float, reserve_seconds: float) -> None:
        seconds = finite_nonnegative(seconds, "estimated_remaining_seconds", positive=True)
        if seconds > self.remaining_seconds(reserve_seconds):
            raise BudgetExhausted("measured remaining-work projection exceeds the cumulative cap")


@dataclasses.dataclass(frozen=True)
class Stage:
    name: str
    kind: str
    command: list[str]
    timeout_seconds: float
    result_dir: Path | None = None

    def __post_init__(self) -> None:
        if not self.name or self.kind not in KINDS:
            raise ValueError("stage needs a name and an explicit supported kind")
        if (not isinstance(self.command, list) or not self.command
                or not all(isinstance(value, str) and value for value in self.command)):
            raise ValueError("stage command must be a nonempty argv list")
        finite_nonnegative(self.timeout_seconds, "timeout_seconds", positive=True)
        if self.kind != "command" and self.result_dir is None:
            raise ValueError("scientific stages require a readable result_dir")


def terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
    except ProcessLookupError:
        process.wait(timeout=5)


def run_command(argv: Sequence[str], timeout_seconds: float,
                remaining: Callable[[], float] | None = None) -> int:
    """Bound an entire process group; an SSH timeout still needs the provider stop."""
    deadline = time.monotonic() + timeout_seconds
    process = subprocess.Popen(list(argv), stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        while process.poll() is None:
            left = deadline - time.monotonic()
            if remaining is not None and remaining() <= 0:
                raise BudgetExhausted("cumulative budget reached its shutdown reserve")
            if left <= 0:
                raise CommandTimeout("stage command exceeded its time limit")
            time.sleep(min(0.25, left))
        return process.returncode
    finally:
        terminate_process(process)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def evidence(stage: Stage) -> dict[str, tuple[int, str]]:
    """Detect stale success artifacts without assuming synchronized wall clocks."""
    if stage.result_dir is None:
        return {}
    names = ["run_status.json", POST_FILES.get(stage.kind, "calibration_metadata.json")]
    found = {}
    for name in names:
        path = stage.result_dir / name
        if path.is_file():
            found[name] = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    return found


def check_gate(stage: Stage, previous: dict | None = None) -> None:
    if stage.kind == "command":
        return
    root = stage.result_dir
    if previous is not None and evidence(stage) == previous:
        raise GateFailed("stage did not produce fresh completion/gate evidence")
    status, manifest = read_json(root / "run_status.json"), read_json(root / "manifest.json")
    identity_bytes = (root / "identity.json").read_bytes()
    identity = json.loads(identity_bytes)
    config = identity["stage_config"]
    complete = read_json(root / "completeness.json")
    if status.get("status") != "complete" or complete.get("status") != "complete":
        raise GateFailed("stage is incomplete")
    split = "v4_llama31_" + SUFFIXES[stage.kind]
    expected_stage = "calibrate" if stage.kind == "calibration" else split
    if (config.get("model_profile") != "llama31_8b_instruct" or config.get("n_episodes") != SIZES[stage.kind]
            or config.get("stage") != expected_stage or config.get("split") != split
            or config.get("seed") != 0 or config.get("materials") != "v1"):
        raise GateFailed("stage identity differs from the approved v4 stage")
    if stage.kind == "smoke":
        if (manifest.get("smoke") is not True or identity.get("limit") != 4
                or complete.get("n_expected") != 480 or complete.get("n_ok") != 480
                or complete.get("n_missing") != 0):
            raise GateFailed("four-episode six-arm smoke requires all 480 readouts")
        return
    if manifest.get("smoke") is not False or identity.get("limit") is not None:
        raise GateFailed("smoke data cannot pass a research gate")
    if stage.kind == "calibration":
        meta = read_json(root / "calibration_metadata.json")["21"]
        if (meta.get("smoke") is not False or meta.get("n_episodes") != 60
                or meta.get("model_profile") != identity.get("model_profile")
                or identity.get("model_profile", {}).get("key") != "llama31_8b_instruct"
                or any(meta.get(field) != identity.get(field) for field in
                       ("model_revision", "tokenizer_manifest_sha", "prefix_hash", "template_hash"))
                or meta.get("split") != split or not isinstance(meta.get("static_unusable"), list)
                or not meta.get("file_sha256") or not meta.get("hash")):
            raise GateFailed("calibration metadata is not the approved complete layer-21 calibration")
        return  # unusable STATIC directions remain a generator decision, not a core stop
    gate = read_json(root / POST_FILES[stage.kind])
    if (gate.get("consumable") is not True
            or gate.get("step") != POST_FILES[stage.kind].removesuffix(".json")
            or gate.get("identity_sha256") != hashlib.sha256(identity_bytes).hexdigest()):
        raise GateFailed("gate is non-consumable or belongs to another run identity")
    if stage.kind in ("baseline", "strength") and gate.get("gate") != "pass":
        raise GateFailed("prespecified baseline/strength gate failed")
    if stage.kind == "validity" and gate.get("core_gate") != "pass":
        raise GateFailed("prespecified core validity gate failed")
    # Matching unavailability and route_validated=False do not veto a valid core.
    # Formal effect directions, p values and null results never control progression.


def supervise(stages: Sequence[Stage], budget: Budget, *, stop: Callable[[], None] | None,
              command_runner: Callable = run_command, emit: Callable[[dict], None] = lambda event: None,
              reserve_seconds: float = 70, estimated_remaining_seconds: float | None = None) -> dict:
    if stop is None:
        raise ValueError("paid execution requires an explicit bounded provider stop callback")
    reserve_seconds = finite_nonnegative(reserve_seconds, "reserve_seconds")
    completed, outcome, reason, code, stop_ok = [], "complete", "", 0, False
    active_stage, command_exit_code, detail = None, None, ""
    try:
        if not stages:
            raise ValueError("plan has no stages")
        if budget.phase == "acceptance" and any(s.kind not in ("command", "smoke", "baseline") for s in stages):
            raise ValueError("pilot/validity/formal stages require the later phase and measured cost projection")
        if budget.phase == "later" and estimated_remaining_seconds is None:
            raise ValueError("later execution requires a measured remaining-work estimate")
        if estimated_remaining_seconds is not None:
            budget.require_projection(estimated_remaining_seconds, reserve_seconds)
        emit({"event": "start", "phase": budget.phase, "cap_usd": budget.cap_usd,
              "hourly_usd": budget.hourly_usd, "prior_spend_usd": budget.prior_spend_usd,
              "bandwidth_usd": budget.bandwidth_usd, "spent_estimate_usd": budget.spent()})
        for stage in stages:
            active_stage = stage.name
            timeout = min(stage.timeout_seconds, budget.remaining_seconds(reserve_seconds))
            if timeout <= 0:
                raise BudgetExhausted("no budget remains beyond the shutdown reserve")
            previous = evidence(stage)
            emit({"event": "stage_start", "stage": stage.name, "kind": stage.kind,
                  "timeout_seconds": timeout, "spent_estimate_usd": budget.spent()})
            heartbeat_at = budget.clock()
            def remaining() -> float:
                nonlocal heartbeat_at
                seconds = budget.remaining_seconds(reserve_seconds)
                if budget.clock() - heartbeat_at >= 30:
                    emit({"event": "heartbeat", "stage": stage.name,
                          "spent_estimate_usd": budget.spent(), "elapsed_seconds": budget.elapsed_seconds})
                    heartbeat_at = budget.clock()
                return seconds

            result = command_runner(stage.command, timeout, remaining)
            command_exit_code = result
            if result != 0:
                raise RuntimeError(f"stage command exited with code {result}")
            if budget.remaining_seconds(reserve_seconds) <= 0:
                raise BudgetExhausted("budget exhausted at stage completion")
            check_gate(stage, previous)
            completed.append(stage.name)
            emit({"event": "stage_complete", "stage": stage.name, "spent_estimate_usd": budget.spent()})
    except KeyboardInterrupt:
        outcome, reason, code = "interrupted", "interrupted", 130
    except Exception as exc:
        outcome, reason = "stopped", type(exc).__name__
        code = 3 if isinstance(exc, BudgetExhausted) else 2
        if isinstance(exc, (BudgetExhausted, CommandTimeout, GateFailed)):
            detail = str(exc)
        # Exceptions may contain private argv or connection details; record type only.
    finally:
        try:
            stopped = stop()
            if stopped is not None and stopped is not True:
                raise RuntimeError("stop callback did not report success")
            stop_ok = True
        except Exception as exc:
            outcome, reason, code = "stop_failed", type(exc).__name__, 4
        summary = {"event": "finished", "outcome": outcome, "reason": reason, "exit_code": code,
                   "detail": detail, "last_stage": active_stage, "command_exit_code": command_exit_code,
                   "completed_stages": completed, "phase": budget.phase,
                   "spent_estimate_usd": budget.spent(refresh_bandwidth=False),
                   "elapsed_seconds": budget.elapsed_seconds,
                   "stop_command_succeeded": stop_ok, "provider_state_verified": False}
        emit(summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--phase", choices=("acceptance", "later"), required=True)
    parser.add_argument("--hourly-usd", required=True, type=float)
    parser.add_argument("--prior-spend-usd", required=True, type=float)
    parser.add_argument("--bandwidth-usd", required=True, type=float)
    parser.add_argument("--bandwidth-file", type=Path)
    parser.add_argument("--estimated-remaining-seconds", type=float)
    parser.add_argument("--stop-command-file", required=True, type=Path)
    parser.add_argument("--stop-timeout-seconds", type=float, default=60)
    parser.add_argument("--journal", required=True, type=Path)
    args = parser.parse_args(argv)
    stop_argv = read_json(args.stop_command_file)
    if not isinstance(stop_argv, list) or not stop_argv or not all(isinstance(s, str) and s for s in stop_argv):
        parser.error("stop command file must contain a nonempty argv array")
    finite_nonnegative(args.stop_timeout_seconds, "stop_timeout_seconds", positive=True)
    def stop() -> None:
        if run_command(stop_argv, args.stop_timeout_seconds) != 0:
            raise RuntimeError("provider stop command failed")

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        plan = read_json(args.plan)
        stages = [Stage(**(item | {"result_dir": Path(item["result_dir"]) if item.get("result_dir") else None}))
                  for item in plan]
        reader = ((lambda: read_json(args.bandwidth_file)["additional_bandwidth_usd"])
                  if args.bandwidth_file else None)
        budget = Budget(args.hourly_usd, args.prior_spend_usd, args.bandwidth_usd, args.phase,
                        bandwidth_reader=reader)
        args.journal.parent.mkdir(parents=True, exist_ok=True)
        with args.journal.open("a") as journal:
            def emit(event: dict) -> None:
                journal.write(json.dumps(event, allow_nan=False) + "\n")
                journal.flush()
            result = supervise(stages, budget, stop=stop, emit=emit,
                               reserve_seconds=args.stop_timeout_seconds + 10,
                               estimated_remaining_seconds=args.estimated_remaining_seconds)
        print(json.dumps(result, allow_nan=False))
        return result["exit_code"]
    except BaseException:
        # Configuration/read failures after the stop argv is known must also stop.
        try:
            stop()
        except BaseException:
            return 4
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
