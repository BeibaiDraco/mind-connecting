"""Run bookkeeping without torch: identity, shards, resume checks, completeness.

Records are written to immutable attempt shards ``records/attempt-NNN.jsonl`` (one per
invocation). Loading tolerates a truncated *final* line of a shard (a crash mid-write),
keeps that evidence untouched and reports it; a corrupt line anywhere else stops the
load. A trial counts as done only with status ``ok`` under the arm's config hash.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

TrialKey = tuple[str, str, str, str, int | None]  # episode_id, arm, recipient, qid, rotation


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def sanitize(obj: Any) -> Any:
    """Replace non-finite floats with None so records stay strict JSON."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    return obj


def canonical_hash(obj: Any, n: int = 16) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:n]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Shards
# ---------------------------------------------------------------------------


@dataclass
class LoadReport:
    records: list[dict[str, Any]]
    truncated_tails: list[str] = field(default_factory=list)  # shard names with an ignored partial last line


def shard_paths(run_dir: Path) -> list[Path]:
    return sorted((Path(run_dir) / "records").glob("attempt-*.jsonl"))


def load_records(run_dir: Path) -> LoadReport:
    report = LoadReport([])
    for shard in shard_paths(run_dir):
        raw = shard.read_bytes()
        lines = raw.split(b"\n")
        complete_tail = raw.endswith(b"\n")
        body, tail = (lines[:-1], None) if complete_tail else (lines[:-1], lines[-1])
        for i, line in enumerate(body):
            if not line.strip():
                continue
            try:
                report.records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{shard.name}: corrupt line {i + 1}: {exc}") from exc
        if tail is not None and tail.strip():
            try:
                report.records.append(json.loads(tail))
            except json.JSONDecodeError:
                report.truncated_tails.append(shard.name)
    return report


class ShardWriter:
    """Append-only writer for a fresh attempt shard; never reopens an older shard."""

    def __init__(self, run_dir: Path):
        rec_dir = Path(run_dir) / "records"
        rec_dir.mkdir(parents=True, exist_ok=True)
        k = len(shard_paths(run_dir))
        self.path = rec_dir / f"attempt-{k:03d}.jsonl"
        if self.path.exists():
            raise FileExistsError(self.path)
        self._fh = self.path.open("x")

    def write(self, rec: dict[str, Any]) -> None:
        self._fh.write(json.dumps(sanitize(rec), ensure_ascii=False, allow_nan=False) + "\n")

    def flush(self) -> None:
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def close(self) -> None:
        if not self._fh.closed:
            self.flush()
            self._fh.close()


def trial_key(rec: dict[str, Any]) -> TrialKey:
    return (str(rec["episode_id"]), str(rec["arm"]), str(rec["recipient"]), str(rec["qid"]), rec.get("rotation_id"))


def done_keys(records: Iterable[dict[str, Any]], arm_hash: dict[str, str] | None = None) -> set[TrialKey]:
    """Trials with an ok record; if ``arm_hash`` is given, only under that arm's config hash."""
    done: set[TrialKey] = set()
    for rec in records:
        if rec.get("status") != "ok":
            continue
        if arm_hash is not None and rec.get("config_hash") != arm_hash.get(str(rec["arm"])):
            continue
        done.add(trial_key(rec))
    return done


def conflicting_hashes(records: Iterable[dict[str, Any]], arm_hash: dict[str, str]) -> dict[str, set[str]]:
    """Arms whose stored records carry a config hash different from the current one."""
    bad: dict[str, set[str]] = {}
    for rec in records:
        arm = str(rec["arm"])
        if arm in arm_hash and rec.get("config_hash") not in (None, arm_hash[arm]):
            bad.setdefault(arm, set()).add(str(rec.get("config_hash")))
    return bad


# ---------------------------------------------------------------------------
# Identity and resume
# ---------------------------------------------------------------------------


def compare_identity(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """Field names whose values differ between two run identities."""
    keys = sorted(set(old) | set(new))
    return [k for k in keys if old.get(k) != new.get(k)]


# ---------------------------------------------------------------------------
# Expected trials and completeness
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArmSpec:
    name: str
    recipients: tuple[str, ...]


def expected_trials(arms: Iterable[ArmSpec], episodes: Iterable[tuple[str, tuple[int, ...]]],
                    qids: Iterable[str], all_rotation_ids: set[str], n_rotations: int = 4) -> list[TrialKey]:
    """episodes: (episode_id, planned rotations). U_OPEN has no rotation."""
    qids = list(qids)
    out: list[TrialKey] = []
    eps = list(episodes)
    for arm in arms:
        for ep_id, rots in eps:
            use = tuple(range(n_rotations)) if ep_id in all_rotation_ids else tuple(rots)
            for recipient in arm.recipients:
                for qid in qids:
                    if qid == "U_OPEN":
                        out.append((ep_id, arm.name, recipient, qid, None))
                    else:
                        out.extend((ep_id, arm.name, recipient, qid, r) for r in use)
    return out


def completeness(records: Iterable[dict[str, Any]], expected: list[TrialKey],
                 arm_hash: dict[str, str]) -> dict[str, Any]:
    ok = done_keys(records, arm_hash)
    missing = [k for k in expected if k not in ok]
    by_arm: dict[str, int] = {}
    for k in missing:
        by_arm[k[1]] = by_arm.get(k[1], 0) + 1
    return {
        "status": "complete" if not missing else "incomplete",
        "n_expected": len(expected),
        "n_ok": len(expected) - len(missing),
        "n_missing": len(missing),
        "missing_by_arm": by_arm,
        "missing_sample": [list(k) for k in missing[:20]],
    }


def mismatch_donor_map(episode_ids: list[str]) -> dict[str, str]:
    """Fixed MISMATCH donor scenario source: the next episode of the *full* stage list."""
    if len(episode_ids) < 2:
        raise ValueError("MISMATCH needs at least two episodes in the stage")
    return {e: episode_ids[(i + 1) % len(episode_ids)] for i, e in enumerate(episode_ids)}
