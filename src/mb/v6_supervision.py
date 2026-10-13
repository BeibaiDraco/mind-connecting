"""One-stage external supervision for an explicitly admitted V6 native worker.

The provider/SSH implementation is a separately reviewed, pinned private adapter.
This module neither contains credentials nor invents observations. The remote
worker must be detached and independently deadline-guarded before launch returns.

Private adapter contract (not commissioned by this module's offline tests): every
response echoes request nonce, action and all four context hashes plus launch
nonce, and supplies a fresh observed_at_epoch and action-specific result. Refresh
atomically publishes the real remote admission and hash-addressed local evidence,
runs remote validate-only, and renews a <=60-second supervisor lease. Launch owns
an exclusive remote intent and detached process group; its guardian stops on hard
deadline, lease expiry or child exit after a bounded <=840-second backup grace.
Observe returns technical counts/status only. Backup creates a unique immutable
snapshot/inventory and local ACK bound to backup_nonce; it must support concurrent
refresh calls, preserve prior bytes, and truthfully verify the mounted destination.
Stop/status address only the pinned private target; accepted is not actual exited.

During paid work only new/changed bytes are hashed; cached immutable receipts are
explicitly identified. The full independent final SD hash occurs after actual
provider stop and is required before terminal success. One invocation admits one
stage only. No calibration selection or next-stage launch is implemented here.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import signal
import threading
import tempfile
import sys
import time
import uuid
from typing import Any, Callable

from mb.v6_contract import canonical_digest
from mb.v6_launch import ROOT, budget_projection, file_sha256, pin_value, read, require, validate_execution

VERSION = "v6-supervision-1"
ACTIONS = frozenset(("refresh", "launch_detached", "observe", "backup", "terminate_child", "stop_instance", "status"))
SPEC_FIELDS = {"version", "plan_pin", "adapter_pin", "binding_pin", "budget_anchor_pin",
               "remote_repository", "remote_python", "remote_plan_path", "remote_admission_path"}


def _sha(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _absolute(value: Any) -> str:
    require(type(value) is str and Path(value).is_absolute() and ".." not in Path(value).parts,
            "Expected an explicit absolute execution path")
    return value


def _atomic(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w") as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_spec(path: str | Path) -> tuple[dict, dict, dict, bytes]:
    spec = read(path)
    require(set(spec) == SPEC_FIELDS and spec["version"] == VERSION, "Invalid supervision specification")
    _, plan = pin_value(spec["plan_pin"])
    _, binding = pin_value(spec["binding_pin"])
    _, anchor = pin_value(spec["budget_anchor_pin"])
    adapter_pin = spec["adapter_pin"]
    require(type(adapter_pin) is dict and set(adapter_pin) == {"path", "sha256"}, "Invalid adapter pin")
    adapter = Path(_absolute(adapter_pin["path"]))
    require(adapter.is_file() and not adapter.is_symlink() and not adapter.resolve().is_relative_to(ROOT),
            "Provider adapter must be a separate private regular file")
    require(file_sha256(adapter) == adapter_pin["sha256"], "Private adapter bytes changed")
    require(anchor.get("instance_binding_sha256") == canonical_digest(binding), "Anchor names another private target")
    require(type(anchor.get("budget")) is dict and _sha(anchor.get("authorization_sha256")), "Invalid budget anchor")
    require(plan.get("version") == "v6-native-stage-1", "Expected a native stage plan")
    for key in ("remote_repository", "remote_python", "remote_plan_path", "remote_admission_path"):
        _absolute(spec[key])
    return spec, plan, anchor, adapter.read_bytes()


class PrivateAdapter:
    """Self-contained Python adapter; JSON only on stdin/stdout, stderr discarded.

    The adapter must not print credentials. Long remote work belongs in detached
    children; each control request has a hard external timeout. Its verified
    source is copied once so emergency stop does not depend on a mutable path.
    """
    def __init__(self, path: Path, digest: str):
        self.path, self.digest = path, digest
        self._pending: dict[str, tuple[str, Any]] = {}
        self._lock = threading.Lock()

    def cancel_pending(self, action: str) -> None:
        with self._lock:
            processes = [p for kind, p in self._pending.values() if kind == action]
        for process in processes:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)

    def __call__(self, request: dict, timeout: float) -> dict:
        require(file_sha256(self.path) == self.digest, "Pinned private adapter copy changed")
        process = subprocess.Popen([sys.executable, str(self.path)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
        key = request.get("nonce", uuid.uuid4().hex)
        with self._lock:
            self._pending[key] = (request.get("action", "unknown"), process)
        try:
            try:
                output, _ = process.communicate(json.dumps(request, sort_keys=True, allow_nan=False).encode(), timeout=timeout)
            except BaseException:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                with contextlib.suppress(Exception):
                    process.communicate(timeout=5)
                raise
        finally:
            with self._lock:
                self._pending.pop(key, None)
        require(process.returncode == 0 and len(output) <= 2 * 1024 * 1024,
                "Private adapter failed or returned excessive output")
        value = json.loads(output)
        require(type(value) is dict, "Private adapter did not return one JSON object")
        canonical_digest(value)
        return value


class Supervisor:
    def __init__(self, spec: dict, plan: dict, anchor: dict, control: Path,
                 adapter: Callable[[dict, float], dict], *, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep,
                 monotonic: Callable[[], float] = time.monotonic):
        self.spec, self.plan, self.anchor, self.control, self.adapter = spec, plan, anchor, control, adapter
        self.clock, self.sleep, self.monotonic = clock, sleep, monotonic
        self.context = {"spec_sha256": canonical_digest(spec), "plan_sha256": canonical_digest(plan),
            "instance_binding_sha256": anchor["instance_binding_sha256"],
            "budget_anchor_sha256": spec["budget_anchor_pin"]["sha256"]}
        self.launch_nonce: str | None = None
        self.worker_id: str | None = None
        self.budget = dict(anchor["budget"])
        self.phase = "initial" if plan["stage"] in ("acceptance", "smoke") else "full"
        self.proof_expires = 0.0
        self.last_refresh = 0.0
        self.last_backup = 0.0
        self.last_progress = -1
        self.backup_verified = False
        self.remote_complete = False
        self.completion_sha: str | None = None
        self.retained_files: dict[str, dict] = {}
        self.retained_stats: dict[str, tuple] = {}
        self.final_copy: dict | None = None
        self.backup_copied = False
        self._preflight_error = None
        try:
            remaining = budget_projection(self.budget, now=self.clock(), phase=self.phase)["remaining_seconds"]
        except ValueError as exc:
            self._preflight_error, remaining = exc, 0
        self.monotonic_deadline = self.monotonic() + remaining

    def event(self, name: str, **safe: Any) -> None:
        """Only caller-whitelisted technical metadata is retained."""
        with (self.control / "journal.jsonl").open("a") as handle:
            handle.write(json.dumps({"event": name, "at_epoch": self.clock(), **safe},
                                    sort_keys=True, allow_nan=False) + "\n")
            handle.flush(); os.fsync(handle.fileno())

    def quiet_event(self, name: str, **safe: Any) -> None:
        try:
            self.event(name, **safe)
        except Exception:
            pass

    def request(self, action: str, *, timeout: float = 45, **payload: Any) -> dict:
        require(action in ACTIONS, "Unknown private adapter operation")
        nonce = uuid.uuid4().hex
        request = {"version": "v6-operational-request-1", "action": action, "nonce": nonce,
                   **self.context, "launch_nonce": self.launch_nonce, "payload": payload}
        value = self.adapter(request, timeout)
        require(value.get("version") == "v6-operational-response-1" and value.get("action") == action
                and value.get("nonce") == nonce and all(value.get(k) == v for k, v in self.context.items())
                and value.get("launch_nonce") == self.launch_nonce, "Unbound adapter observation")
        stamp = value.get("observed_at_epoch")
        require(type(stamp) in (int, float) and math.isfinite(stamp)
                and 0 <= self.clock() - stamp <= 60, "Stale or future adapter observation")
        require(type(value.get("result")) is dict, "Missing adapter result")
        return value["result"]

    def deadline(self) -> float:
        remaining = self.monotonic_deadline - self.monotonic()
        require(remaining > 0, "Monotonic financial deadline exhausted")
        wall = budget_projection(self.budget, now=self.clock(), phase=self.phase)["effective_deadline_epoch"]
        return min(wall, self.clock() + remaining)

    def refresh(self) -> None:
        result = self.request("refresh", remote_plan_path=self.spec["remote_plan_path"],
            remote_admission_path=self.spec["remote_admission_path"],
            source_manifest_sha256=canonical_digest(self.plan["source_manifest"]),
            supervisor_lease_seconds=60)
        admission_path, proof = pin_value(result["admission_pin"])
        evidence = Path(_absolute(result["evidence_dir"]))
        # This is an external audit of copied remote paths, never native authority.
        checked = validate_execution(Path(self.spec["plan_pin"]["path"]), admission_path,
                                     now=self.clock(), evidence_dir=evidence)
        require(checked["_admission"]["historical_only"] is True
                and checked["plan_sha256"] == self.context["plan_sha256"], "Refreshed plan differs")
        require(proof["instance_binding_sha256"] == self.context["instance_binding_sha256"]
                and proof["budget_anchor_pin"]["sha256"] == self.context["budget_anchor_sha256"]
                and proof["phase"] == self.phase, "Refresh changed financial binding or phase")
        proposed = proof["budget"]
        require(set(proposed) == set(self.budget) and all(proposed[k] == self.budget[k]
                for k in self.budget if k != "accrued_bandwidth_usd")
                and proposed["accrued_bandwidth_usd"] >= self.budget["accrued_bandwidth_usd"],
                "Refreshed financial anchor changed or accrued charge decreased")
        remote = result["remote_validation"]
        require(remote == {"version": "v6-native-execution-1", "status": "admitted_not_executed", "plan_sha256": self.context["plan_sha256"],
                           "stage": self.plan["stage"], "model_or_gpu_used": False},
                "Remote real-time admission was not independently checked")
        self.budget = dict(proposed)
        self.monotonic_deadline = min(self.monotonic_deadline,
            self.monotonic() + budget_projection(self.budget, now=self.clock(), phase=self.phase)["remaining_seconds"])
        self.deadline()
        self.proof_expires = min(float(proof["expires_at_epoch"]), self.clock() + 60)
        self.last_refresh = self.clock()
        if not self.last_backup:
            self.last_backup = self.clock()
        _atomic(self.control / "latest_admission.json", {"admission_pin": result["admission_pin"],
            "evidence_dir": str(evidence), "budget": self.budget, "proof_expires_epoch": self.proof_expires})
        self.event("proof_refreshed", phase=self.phase, effective_deadline_epoch=self.deadline())

    def launch(self, *, resume: bool) -> None:
        require(not (self.control / "launch_intent.json").exists(), "An existing launch intent forbids a new launch")
        command = [self.spec["remote_python"], str(Path(self.spec["remote_repository"]) / "scripts/v6_execute.py"),
                   "--plan", self.spec["remote_plan_path"], "--admission", self.spec["remote_admission_path"]]
        if resume:
            command.append("--resume")
        self.launch_nonce = uuid.uuid4().hex
        intent = {**self.context, "launch_nonce": self.launch_nonce, "command": command,
                  "resume": resume, "created_at_epoch": self.clock()}
        with (self.control / "launch_intent.json").open("x") as handle:
            json.dump(intent, handle, sort_keys=True, allow_nan=False)
            handle.flush(); os.fsync(handle.fileno())
        # A timeout here is ambiguous: never send a second launch request.
        result = self.request("launch_detached", command=command, deadline_epoch=self.deadline(),
                              require_exclusive_remote_intent=True, refuse_competing_workers=True,
                              supervisor_lease_deadline_epoch=self.proof_expires, maximum_backup_grace_seconds=840)
        require(result.get("detached") is True and result.get("independent_deadline_guard") is True
                and result.get("exclusive_intent_persisted") is True and result.get("competing_workers_absent") is True
                and result.get("worker_exit_or_lease_expiry_stop") is True
                and _sha(result.get("worker_id_sha256")), "Detached identified deadline-guarded worker not confirmed")
        self.worker_id = result["worker_id_sha256"]
        _atomic(self.control / "launch_receipt.json", {**self.context, "launch_nonce": self.launch_nonce,
                 "worker_id_sha256": self.worker_id})
        self.event("launched", worker_id_sha256=self.worker_id)

    def observe(self) -> str:
        value = self.request("observe", worker_id_sha256=self.worker_id)
        require(value.get("worker_id_sha256") == self.worker_id, "Observed another native worker")
        state = value.get("state")
        require(state in ("running", "complete", "failed"), "Ambiguous native worker state")
        completed, expected = value.get("completed_episodes"), value.get("expected_episodes")
        require(type(completed) is int and 0 <= completed <= self.plan["n"]
                and expected == self.plan["n"], "Invalid technical progress counts")
        require(completed >= self.last_progress, "Technical progress regressed")
        if completed != self.last_progress or state != "running":
            self.event("progress", completed_episodes=completed, expected_episodes=expected, state=state)
            self.last_progress = completed
        if state in ("complete", "failed") and value.get("completion_sha256") is not None:
            require(_sha(value["completion_sha256"]) and completed == expected, "Invalid closed-run observation")
            self.completion_sha = value["completion_sha256"]
        if state == "complete":
            require(value.get("exit_code") == 0 and completed == expected
                    and _sha(value.get("completion_sha256")), "Completion is not a complete successful native child")
            self.completion_sha = value["completion_sha256"]
            self.remote_complete = True
        return state

    def _backup_tick(self, end: float, *, final: bool) -> None:
        require(self.monotonic() < end and self.deadline() - self.clock() > 120,
                "Bounded backup/hash window exhausted")
        if not final and self.clock() - self.last_refresh >= 30:
            self.refresh()

    def _backup_request(self, timeout: float, end: float, *, final: bool, **payload: Any) -> dict:
        # Copying a large immutable snapshot must not starve the live proof refresh.
        finished = threading.Event()
        answer: list[Any] = []
        def call():
            try:
                answer.append((True, self.request("backup", timeout=timeout, **payload)))
            except BaseException as exc:
                answer.append((False, exc))
            finally:
                finished.set()
        thread = threading.Thread(target=call, daemon=True)
        thread.start()
        try:
            while not finished.wait(5):
                self._backup_tick(end, final=final)
            self._backup_tick(end, final=final)
            ok, value = answer[0]
            if not ok:
                raise value
            return value
        finally:
            if thread.is_alive():
                cancel = getattr(self.adapter, "cancel_pending", None)
                if callable(cancel):
                    cancel("backup")
                thread.join(timeout=5)

    def _hash_backup(self, path: Path, size: int, end: float, *, final: bool) -> str:
        h = hashlib.sha256()
        with path.open("rb") as handle:
            remaining = size
            while remaining:
                self._backup_tick(end, final=final)
                chunk = handle.read(min(1024 * 1024, remaining))
                require(bool(chunk), "Retained scientific prefix is truncated")
                h.update(chunk); remaining -= len(chunk)
        return h.hexdigest()

    def backup(self, *, final: bool) -> None:
        available = self.deadline() - self.clock() - 120
        require(available > 0, "No bounded backup window remains")
        nonce = uuid.uuid4().hex
        timeout = min(840, available)
        end = self.monotonic() + timeout
        value = self._backup_request(timeout, end, final=final, backup_nonce=nonce,
            final_backup=final, worker_id_sha256=self.worker_id, output_dir=self.plan["output_dir"])
        inventory_path, inventory = pin_value(value["inventory_pin"])
        ack_path, ack = pin_value(value["ack_pin"])
        require(inventory.get("version") == "v6-backup-inventory-1"
                and inventory.get("backup_nonce") == nonce and all(inventory.get(k) == v for k, v in self.context.items())
                and inventory.get("launch_nonce") == self.launch_nonce, "Backup inventory names another execution")
        entries = inventory.get("files")
        require(type(entries) is list and bool(entries), "Empty scientific backup inventory")
        root = Path(_absolute(value["local_root"]))
        require(root.is_dir() and not root.is_symlink() and value.get("mount_verified") is True,
                "Durable backup mount is not verified")
        names = set()
        current_files = {}
        current_stats = {}
        rehashed, cached = 0, 0
        for item in entries:
            require(type(item) is dict and set(item) == {"path", "bytes", "sha256"}, "Malformed backup entry")
            name = item["path"]
            require(type(name) is str and name and not Path(name).is_absolute()
                    and ".." not in Path(name).parts and name not in names, "Unsafe or duplicate backup path")
            path = root / name
            require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
                    and type(item["bytes"]) is int and item["bytes"] >= 0 and _sha(item["sha256"])
                    and path.stat().st_size == item["bytes"], "Durable backup file missing or resized")
            stat = path.stat()
            signature = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
            previous = self.retained_files.get(name)
            # This is explicit reuse of an immutable hash receipt, not a new
            # proof from size/mtime. A full independent rehash follows actual stop.
            if previous == item and self.retained_stats.get(name) == signature:
                cached += 1
            else:
                require(self._hash_backup(path, item["bytes"], end, final=final) == item["sha256"],
                        "Durable backup bytes differ")
                rehashed += 1
                if previous is not None:
                    require(item["bytes"] >= previous["bytes"], "A retained backup file was truncated")
                    require(self._hash_backup(path, previous["bytes"], end, final=final) == previous["sha256"],
                            "Previously retained scientific bytes changed")
            names.add(name)
            current_files[name] = item
            current_stats[name] = signature
        require(self.retained_files.keys() <= current_files.keys(), "Previously retained backup files disappeared")
        require(ack.get("version") == "v6-backup-ack-1" and ack.get("verified") is True
                and ack.get("backup_nonce") == nonce and ack.get("inventory_sha256") == file_sha256(inventory_path)
                and all(ack.get(k) == v for k, v in self.context.items())
                and ack.get("launch_nonce") == self.launch_nonce and ack.get("file_count") == len(entries),
                "Backup ACK does not bind exact retained bytes")
        if final and (self.completion_sha is not None or inventory.get("complete_run") is True):
            closed_sha = inventory.get("completion_sha256")
            require(inventory.get("complete_run") is True and _sha(closed_sha)
                    and (self.completion_sha is None or closed_sha == self.completion_sha),
                    "Final backup does not include the observed complete native run")
            matches = [x for x in entries if Path(x["path"]).name == "completion.json" and x["sha256"] == closed_sha]
            require(len(matches) == 1, "Exact complete-run receipt absent from verified backup")
            completion_path = root / matches[0]["path"]
            completion = read(completion_path)
            require(completion.get("version") == "v6-native-completion-1" and completion.get("status") == "complete"
                    and completion.get("backend_kind") == "native" and completion.get("stage") == self.plan["stage"]
                    and completion.get("model_profile") == self.plan["model_profile"] and completion.get("n") == self.plan["n"]
                    and completion.get("source_manifest_sha256") == canonical_digest(self.plan["source_manifest"])
                    and completion.get("validation", {}).get("complete") is True,
                    "Backed-up completion is not this complete native stage")
            prefix = Path(matches[0]["path"]).parent
            expected = completion.get("file_pins")
            require(type(expected) is dict and bool(expected), "Completion lacks the native closed-file inventory")
            actual = {str(Path(name).relative_to(prefix)): {"bytes": item["bytes"], "sha256": item["sha256"]}
                      for name, item in current_files.items() if Path(name).is_relative_to(prefix)
                      and name != matches[0]["path"]}
            require(actual == expected, "Final backup omits or changes closed scientific files")
            require("identity.json" in expected, "Closed backup lacks immutable run identity")
            identity = read(completion_path.parent / "identity.json")
            require(canonical_digest(identity) == completion.get("identity_sha256")
                    and identity.get("plan") == {**self.plan, "plan_sha256": self.context["plan_sha256"]},
                    "Closed backup belongs to another exact native plan")
        self.last_backup = self.clock()
        self.retained_files, self.retained_stats = current_files, current_stats
        if final:
            self.backup_copied = True
            self.final_copy = {"root": str(root), "files": current_files,
                               "inventory_pin": value["inventory_pin"], "ack_pin": value["ack_pin"]}
        receipt = {"inventory_pin": value["inventory_pin"], "ack_pin": value["ack_pin"],
            "file_count": len(entries), "final": final, "verification": "incremental_with_cached_immutable_receipts",
            "freshly_rehashed_files": rehashed, "cached_files": cached, "full_final_rehash": False}
        _atomic(self.control / "last_backup.json", receipt)
        self.event("backup_copied", file_count=len(entries), final=final, freshly_rehashed_files=rehashed, cached_files=cached)

    def final_rehash(self, *, provider_stopped: bool) -> None:
        require(provider_stopped is True and self.final_copy is not None, "Full SD rehash requires actual provider stop first")
        root = Path(self.final_copy["root"])
        require(root.is_dir() and not root.is_symlink(), "Backup root disappeared before offline audit")
        # These bytes are now checked with no paid GPU running. No wall-clock
        # GPU deadline is applied to a potentially large independent SD audit.
        count, total = 0, 0
        for name, item in self.final_copy["files"].items():
            path = root / name
            require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
                    and path.stat().st_size == item["bytes"] and file_sha256(path) == item["sha256"],
                    "Independent final SD rehash failed")
            count += 1; total += item["bytes"]
        pin_value(self.final_copy["inventory_pin"])
        pin_value(self.final_copy["ack_pin"])
        self.backup_verified = True
        _atomic(self.control / "final_rehash.json", {"version": "v6-final-backup-rehash-1", **self.context,
            "inventory_pin": self.final_copy["inventory_pin"], "ack_pin": self.final_copy["ack_pin"],
            "provider_stopped_before_rehash": True, "all_files_rehashed": True,
            "file_count": count, "bytes": total, "at_epoch": self.clock()})
        self.event("offline_final_rehash_verified", file_count=count, bytes=total)

    def stop(self) -> bool:
        """No journal, backup or log-file write can prevent bounded stop attempts."""
        reserve = self.budget.get("shutdown_reserve_seconds", 180)
        limit = min(180, max(10, reserve)) if type(reserve) in (int, float) and math.isfinite(reserve) else 180
        end = self.monotonic() + limit
        for attempt in range(4):
            remaining = end - self.monotonic()
            if remaining <= 1:
                break
            try:
                self.request("stop_instance", timeout=min(20, max(0.1, remaining / 2)))
            except BaseException:
                pass
            try:
                value = self.request("status", timeout=min(20, max(0.1, end - self.monotonic())))
                if (value.get("actual_status") == "exited" and value.get("intended_status") == "stopped"
                        and value.get("cur_state") == "stopped" and value.get("next_state") == "stopped"):
                    self.quiet_event("provider_stopped", attempt=attempt + 1)
                    return True
            except BaseException:
                pass
            if attempt != 3:
                with contextlib.suppress(BaseException):
                    self.sleep(min(5, max(0, end - self.monotonic())))
        self.quiet_event("provider_stop_unverified")
        return False

    def run(self, *, resume: bool = False) -> dict:
        error = None
        stopped = False
        try:
            if self._preflight_error is not None:
                raise self._preflight_error
            self.refresh()
            self.launch(resume=resume)
            while True:
                self.deadline()
                if self.clock() - self.last_refresh >= 30:
                    try:
                        self.refresh()
                    except Exception:
                        # Observation can recover briefly; the remote task stays detached.
                        if self.clock() >= self.proof_expires:
                            raise
                try:
                    state = self.observe()
                except Exception:
                    if self.clock() >= self.proof_expires:
                        raise
                    self.sleep(5)
                    continue
                if state == "complete":
                    break
                if state == "failed":
                    raise RuntimeError("Native stage failed; no automatic new stage or launch")
                if self.clock() - self.last_backup >= 600:
                    self.backup(final=False)
                self.sleep(15)
        except BaseException as exc:
            error = type(exc).__name__
            self.quiet_event("supervision_failed", error_type=error)
        finally:
            try:
                if self.launch_nonce is not None and not self.remote_complete:
                    try:
                        self.request("terminate_child", timeout=45, worker_id_sha256=self.worker_id,
                                     term_seconds=20, kill_seconds=10)
                    except Exception:
                        pass
                try:
                    self.backup(final=True)
                except BaseException as exc:
                    self.quiet_event("final_backup_failed", error_type=type(exc).__name__)
                    error = error or "BackupUnverified"
            finally:
                stopped = self.stop()
        if stopped and self.final_copy is not None:
            try:
                self.final_rehash(provider_stopped=True)
            except BaseException as exc:
                self.quiet_event("offline_final_rehash_failed", error_type=type(exc).__name__)
                error = error or "FinalRehashUnverified"
        result = {"version": VERSION, **self.context, "remote_complete": self.remote_complete,
                  "backup_copied": self.backup_copied, "backup_verified": self.backup_verified, "provider_stopped": stopped,
                  "status": "complete" if self.remote_complete and self.backup_verified and stopped and error is None else "failed",
                  "error_type": error}
        try:
            _atomic(self.control / "terminal.json", result)
        except Exception:
            pass
        return result


@contextlib.contextmanager
def _termination_signals():
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    def interrupt(signum, frame):
        raise InterruptedError("External supervision interrupted")
    old = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGHUP)}
    try:
        for sig in old:
            signal.signal(sig, interrupt)
        yield
    finally:
        for sig, handler in old.items():
            signal.signal(sig, handler)


def supervise(spec_path: str | Path, control_dir: str | Path, *, resume: bool = False) -> dict:
    """Start one lifecycle only. A retained intent is evidence, never permission to relaunch."""
    import fcntl
    spec, plan, anchor, adapter_bytes = load_spec(spec_path)
    control = Path(control_dir)
    require(control.is_absolute() and not control.exists(), "Use a new explicit private control directory")
    control.mkdir(parents=True, exist_ok=False)
    os.chmod(control, 0o700)
    adapter_copy = control / "private_adapter.py"
    with adapter_copy.open("xb") as handle:
        handle.write(adapter_bytes); handle.flush(); os.fsync(handle.fileno())
    os.chmod(adapter_copy, 0o600)
    # The target-wide lease prevents two distinct control directories racing launches.
    lock_root = Path(tempfile.gettempdir()) / ("mb-v6-supervision-locks-" + str(os.getuid()))
    lock_root.mkdir(mode=0o700, exist_ok=True)
    require(not lock_root.is_symlink() and lock_root.stat().st_uid == os.getuid(), "Unsafe target lease root")
    lock = lock_root / (anchor["instance_binding_sha256"] + ".lock")
    require(not lock.is_symlink(), "Unsafe target lease")
    with lock.open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another external supervisor owns this exact target") from exc
        try:
            adapter = PrivateAdapter(adapter_copy, spec["adapter_pin"]["sha256"])
            with _termination_signals():
                return Supervisor(spec, plan, anchor, control, adapter).run(resume=resume)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--control-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true", help="Explicit exact-run native resume, never a fresh retry")
    args = parser.parse_args()
    result = supervise(args.spec, args.control_dir, resume=args.resume)
    print(json.dumps({k: result[k] for k in ("status", "remote_complete", "backup_verified", "provider_stopped", "error_type")},
                     sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "complete" else 1
