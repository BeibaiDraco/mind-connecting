"""Local synthetic dry-runs and append-only episode resume for the v6 draft.

The synthetic backend is a deterministic software fixture, not a language model.
No command in this module loads a model, acquires hardware, or launches a study.
"""

from __future__ import annotations

import copy
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from mb.v6_contract import Export, Probe, RuntimeSpec, canonical_digest
from mb.v6_runtime import EpisodeRunner, PairState, RoundTape
from mb import v6_tasks as tasks


KEY_FIELDS = ("model_profile", "episode_id", "kind", "policy", "checkpoint", "arm",
              "version", "round_id", "side", "qid")


class SyntheticBackend:
    """Hash-based test outputs with actual incoming dependencies, never model evidence."""

    kind = "synthetic_fixture"

    def __init__(self, *, invalid_every: int | None = None):
        self.invalid_every = invalid_every

    def create(self, system: str, user: str) -> dict:
        return {"history": [("system", system), ("user", user)], "open": True}

    def clone(self, state: dict) -> dict:
        return copy.deepcopy(state)

    def digest(self, state: dict) -> str:
        return canonical_digest(state)

    def decode(self, exports: tuple[Export, ...]) -> str:
        return " ".join(str(x.token) for x in exports)

    def begin_user(self, state: dict, text: str) -> None:
        if state["open"]:
            raise ValueError("Previous assistant turn is still open")
        state["history"].append(("user", text))
        state["open"] = True

    def finish_turn(self, state: dict, foreign: tuple[Export, ...] = (),
                    gain: float = 0.0) -> None:
        if state["open"]:
            state["history"].append(("close", self._incoming(foreign, gain)))
            state["open"] = False

    @staticmethod
    def _incoming(foreign: tuple[Export, ...], gain: float) -> list:
        return [x.digest for x in foreign] if gain else []

    def step(self, state: dict, foreign: tuple[Export, ...], gain: float) -> Export:
        if not state["open"]:
            raise ValueError("Work requires an open assistant turn")
        incoming = self._incoming(foreign, gain)
        token = 100 + int(canonical_digest([self.digest(state), incoming])[:8], 16) % 4
        state["history"].append(("generated", token, incoming))
        position = len(state["history"])-1
        payload = {"token": token, "position": position, "parent": self.digest(state)}
        return Export(token, position, canonical_digest(payload), payload)

    def probe(self, state: dict, question: str, choice_labels: tuple[str, str, str, str],
              foreign: tuple[Export, ...], gain: float) -> Probe:
        result = self.clone(state)
        self.finish_turn(result, foreign, gain)
        self.begin_user(result, question)
        value = int(canonical_digest([result, self._incoming(foreign, gain)])[:8], 16)
        index = value % 4
        token = 999 if self.invalid_every and value % self.invalid_every == 0 else 100+index
        return Probe(result, token, 0.7, tuple(1.0 if j == index else 0.0 for j in range(4)),
                     0.9, (100, 101, 102, 103))

    def commit_answer(self, probe: Probe, foreign: tuple[Export, ...], gain: float) -> dict:
        probe.state["history"].append(("actual_answer", probe.token, self._incoming(foreign, gain)))
        self.finish_turn(probe.state, foreign, gain)
        return probe.state


def record_key(record: dict) -> tuple:
    return tuple(record[field] for field in KEY_FIELDS)


def _write_new(path: Path, value: Any) -> None:
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


class EpisodeLedger:
    """Identity admission precedes every append, including an exact no-op resume."""

    def __init__(self, directory: Path, identity: dict, *, resume: bool = False,
                 key_fields: tuple[str, ...] = KEY_FIELDS):
        self.directory, self.identity = Path(directory), identity
        if not key_fields or len(set(key_fields)) != len(key_fields):
            raise ValueError("Ledger key fields must be nonempty and distinct")
        self.key_fields = tuple(key_fields)
        if resume:
            previous = json.loads((self.directory/"identity.json").read_text())
            if previous != identity:
                raise ValueError("V6 resume identity differs; no file was changed")
        else:
            self.directory.mkdir(parents=True, exist_ok=False)
            _write_new(self.directory/"identity.json", identity)
            (self.directory/"records").mkdir()
        self.records: dict[tuple, dict] = {}
        for path in sorted((self.directory/"records").glob("attempt-*.jsonl")):
            for line_no, line in enumerate(path.read_text().splitlines(), 1):
                try:
                    rec = json.loads(line)
                    key = tuple(rec[field] for field in self.key_fields)
                except (ValueError, KeyError) as exc:
                    raise ValueError(f"Corrupt retained record at {path.name}:{line_no}") from exc
                if key in self.records:
                    raise ValueError("Duplicate retained readout key")
                if rec.get("status") != "ok":
                    raise ValueError("Technical failures belong in attempt notes, not successful rows")
                self.records[key] = rec
        self._writer = None
        self._attempt = 1 + len(list((self.directory/"records").glob("attempt-*.jsonl")))

    def write(self, record: dict) -> None:
        canonical_digest(record)  # Reject NaN before writing anything.
        key = tuple(record[field] for field in self.key_fields)
        if key in self.records:
            if self.records[key] != record:
                raise ValueError("Successful readout changed during exact episode resume")
            return
        if self._writer is None:
            self._writer = (self.directory/"records"/f"attempt-{self._attempt:03d}.jsonl").open("x")
        self._writer.write(json.dumps(record, sort_keys=True, allow_nan=False)+"\n")
        self._writer.flush()
        os.fsync(self._writer.fileno())
        self.records[key] = record

    def note(self, value: dict) -> None:
        with (self.directory/"notes.jsonl").open("a") as handle:
            handle.write(json.dumps(value, sort_keys=True, allow_nan=False)+"\n")
            handle.flush()
            os.fsync(handle.fileno())

    def attempts(self, episode_id: str) -> int:
        path = self.directory/"notes.jsonl"
        if not path.exists():
            return 0
        return sum(r.get("event") == "episode_started" and r.get("episode_id") == episode_id
                   for r in map(json.loads, path.read_text().splitlines()))

    def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None


def source_manifest() -> dict[str, str]:
    import hashlib
    root = Path(__file__).resolve().parents[2]
    names = [*sorted((root/"src"/"mb").glob("v6_*.py")),
             *sorted((root/"scripts").glob("v6_*.py")),
             root/"src/mb/chat.py", root/"src/mb/model_profiles.py", root/"src/mb/tasks.py",
             root/"materials/tokenizer_manifest.json",
             root/"materials/tokenizer_llama31_8b_instruct_manifest.json",
             root/"docs/protocol/PROTOCOL_V6_CONTINUOUS_DRAFT.md",
             root/"configs/v6/local_draft.yaml", root/"requirements.txt", root/"pyproject.toml"]
    names += [p for p in (root/"scripts/prepare_v6_launch.py", root/"scripts/supervise_v6.py",
                         root/"docs/protocol/V6_EXECUTION_ADDENDUM_DRAFT.md",
                         root/"configs/v6/admission_proposal.json") if p.exists()]
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in names}


class NativeArchiveWriter:
    """Future authorized-CUDA artifact sink; no model loading or process launch.

    Plain tensors/primitives are stored; loads use weights_only=True after both
    identity and file digest checks. Archives can be large and need a measured
    storage reservation before hardware execution. This is not a GPU approval.
    """

    def __init__(self, directory: Path, backend: Any, identity: dict, *, resume: bool = False):
        from mb.v6_native import NativeBackend
        if not isinstance(backend, NativeBackend):
            raise TypeError("Native archives require an already-authorized native backend")
        self.backend, self.directory = backend, Path(directory)
        self.identity = json.loads(json.dumps(identity))
        self.identity_digest = canonical_digest(self.identity)
        if resume:
            if json.loads((self.directory/"identity.json").read_text()) != self.identity:
                raise ValueError("Native archive identity mismatch before write")
        else:
            self.directory.mkdir(parents=True, exist_ok=False)
            _write_new(self.directory/"identity.json", self.identity)
        self.index = {}
        path = self.directory/"inventory.jsonl"
        if path.exists():
            for row in map(json.loads, path.read_text().splitlines()):
                name = row["file"]
                if Path(name).name != name or name in self.index:
                    raise ValueError("Invalid native archive inventory")
                retained = self.directory/name
                if (not retained.is_file() or retained.stat().st_size != row["bytes"]
                        or self._file_digest(retained) != row["sha256"]):
                    raise ValueError("Retained native archive integrity failed before append")
                self.index[name] = row

    @staticmethod
    def _file_digest(path: Path) -> str:
        import hashlib
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(4*1024*1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def __call__(self, event: dict) -> None:
        import torch
        meta = {key: event[key] for key in ("episode_id", "sequence", "kind", "label", "digest")}
        name = canonical_digest([meta["episode_id"], meta["sequence"]])+".pt"
        path = self.directory/name
        if name in self.index:
            previous = self.index[name]
            if previous["meta"] != meta or self._file_digest(path) != previous["sha256"]:
                raise ValueError("Retained native archive changed on resume")
            return
        value = event["value"]
        if event["kind"] == "pair":
            body = {"world": asdict(value.world),
                    "states": [self.backend.dump_state(s) for s in value.models],
                    "windows": [[self.backend.dump_export(x) for x in w] for w in value.windows]}
        elif event["kind"] == "tape":
            body = {"round_id": value.round_id, "parent_digest": value.parent_digest,
                    "entries": [[self.backend.dump_export(x) for x in side] for side in value.entries]}
        else:
            raise ValueError("Unknown native artifact kind")
        payload = {"identity_sha256": self.identity_digest, "meta": meta, "body": body}
        # Interrupted files are retained and require explicit recovery; never overwrite them.
        with path.open("xb") as handle:
            torch.save(payload, handle)
            handle.flush()
            os.fsync(handle.fileno())
        row = {"file": name, "sha256": self._file_digest(path), "bytes": path.stat().st_size,
               "meta": meta}
        with (self.directory/"inventory.jsonl").open("a") as handle:
            handle.write(json.dumps(row, sort_keys=True)+"\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.index[name] = row

    def load(self, filename: str) -> PairState | RoundTape:
        import torch
        if filename not in self.index or Path(filename).name != filename:
            raise ValueError("Native artifact is not in the verified inventory")
        row = self.index[filename]
        path = self.directory/filename
        if self._file_digest(path) != row["sha256"]:
            raise ValueError("Native artifact file hash differs")
        payload = torch.load(path, map_location="cpu", weights_only=True)
        if payload["identity_sha256"] != self.identity_digest or payload["meta"] != row["meta"]:
            raise ValueError("Native artifact source identity differs")
        body, meta = payload["body"], payload["meta"]
        if meta["kind"] == "pair":
            world = body["world"]
            state = PairState(tuple(self.backend.load_state(s) for s in body["states"]),
                              tasks.World(tuple(world["beacons"]), tuple(world["goals"]),
                                          world["round_id"], tuple(tuple(x) for x in world["actions"])),
                              tuple(tuple(self.backend.load_export(x) for x in w) for w in body["windows"]))
            actual = EpisodeRunner(self.backend, RuntimeSpec(), "archive_check").digest(state)
        elif meta["kind"] == "tape":
            state = RoundTape(body["round_id"],
                              tuple(tuple(self.backend.load_export(x) for x in w) for w in body["entries"]),
                              body["parent_digest"])
            actual = canonical_digest(state.identity())
        else:
            raise ValueError("Unknown saved artifact kind")
        if actual != meta["digest"]:
            raise ValueError("Restored scientific artifact differs from its original snapshot")
        return state


def synthetic_identity(episodes: Iterable[tasks.Episode], spec: RuntimeSpec,
                       model_profile: str, text_episodes: set[str]) -> dict:
    import importlib.metadata
    import platform
    return {"version": "v6-local-draft-1", "backend": "synthetic_fixture",
            "scientific_data": False, "formal_authorized": False,
            "model_profile": model_profile, "runtime": asdict(spec),
            "episodes": [tasks.episode_to_dict(ep) for ep in episodes],
            "text_episodes": sorted(text_episodes), "source": source_manifest(),
            "software": {"python": platform.python_version(), **{
                key: importlib.metadata.version(key) for key in ("numpy", "scipy", "transformers", "tokenizers")}}}


def run_synthetic(directory: Path, episodes: list[tasks.Episode], spec: RuntimeSpec,
                  *, model_profile: str = "qwen3_4b_instruct_2507", text_episodes: set[str] | None = None,
                  resume: bool = False) -> dict:
    from mb.v6_analysis import validate_records

    text_episodes = set(text_episodes or ())
    if not text_episodes <= {ep.episode_id for ep in episodes}:
        raise ValueError("Text subset contains an undeclared base episode")
    declared = {model_profile: [ep.episode_id for ep in episodes]}
    text_declared = {model_profile: sorted(text_episodes)} if text_episodes else None
    validate_records([], declared, text_episodes=text_declared)
    identity = synthetic_identity(episodes, spec, model_profile, text_episodes)
    # JSON normalizes tuples; compare exactly the representation persisted on disk.
    identity = json.loads(json.dumps(identity))
    ledger = EpisodeLedger(directory, identity, resume=resume)
    try:
        # Even incomplete historical ledgers are admitted before notes or computation.
        validate_records(list(ledger.records.values()), declared, text_episodes=text_declared)
        for ep in episodes:
            # Expected-key validation below must not infer completeness from a count alone.
            retained = [r for r in ledger.records.values() if r["episode_id"] == ep.episode_id]
            expected_count = 352 if ep.episode_id in text_episodes else 328
            if len(retained) == expected_count:
                checked = validate_records(retained, {model_profile: [ep.episode_id]},
                                           text_episodes={model_profile: [ep.episode_id]} if ep.episode_id in text_episodes else None)
                if not checked["complete"]:
                    raise ValueError("Retained episode count hides a missing expected key")
                continue
            if ledger.attempts(ep.episode_id) >= 2:
                raise RuntimeError("Original attempt and one exact-identity retry are exhausted")
            ledger.note({"event": "episode_started", "episode_id": ep.episode_id})
            runner = EpisodeRunner(SyntheticBackend(), spec, model_profile, sink=ledger.write)
            try:
                runner.run_episode(ep, text_reference=ep.episode_id in text_episodes)
            except Exception as exc:
                ledger.note({"event": "technical_failure", "episode_id": ep.episode_id,
                             "error_type": type(exc).__name__})
                raise
            ledger.note({"event": "episode_complete", "episode_id": ep.episode_id,
                         "readouts": len(runner.records), "synthetic": True})
        validation = validate_records(list(ledger.records.values()),
                                      {model_profile: [ep.episode_id for ep in episodes]},
                                      text_episodes={model_profile: sorted(text_episodes)} if text_episodes else None)
        if not validation["complete"]:
            raise RuntimeError("Synthetic run did not produce its complete declared ledger")
        return {"status": "synthetic_dry_run_complete", "scientific_data": False,
                "formal_authorized": False, "episodes": len(episodes),
                "records": len(ledger.records), "identity_sha256": canonical_digest(identity),
                "validation": validation}
    finally:
        ledger.close()
