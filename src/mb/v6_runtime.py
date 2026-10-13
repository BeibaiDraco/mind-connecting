"""Continuous v6 scheduling; no torch import or scientific launch permission."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from mb.v6_contract import Backend, Export, Probe, RuntimeSpec, canonical_digest
from mb import v6_tasks as tasks


POLICIES = ("LIVE", "A_TO_B", "B_TO_A", "OFF", "FRESH")
GOAL_QIDS = ("action", "transfer_action", "original_goal", "latest_goal",
             "partner_beacon", "partner_goal")


@dataclass
class PairState:
    models: tuple[Any, Any]
    world: tasks.World
    windows: tuple[tuple[Export, ...], tuple[Export, ...]] = ((), ())


@dataclass(frozen=True)
class RoundTape:
    round_id: int
    entries: tuple[tuple[Export, ...], tuple[Export, ...]]
    parent_digest: str

    def source(self, side: int, tick: int, window: int) -> tuple[Export, ...]:
        if side not in (0, 1) or not 0 <= tick <= len(self.entries[side]):
            raise ValueError("Tape cursor outside its declared round")
        return self.entries[side][max(0, tick-window):tick]

    def identity(self) -> dict:
        return {"round_id": self.round_id, "parent_digest": self.parent_digest,
                "entries": [[x.identity() for x in row] for row in self.entries]}


class EpisodeRunner:
    def __init__(self, backend: Backend, spec: RuntimeSpec, model_profile: str,
                 *, sink: Callable[[dict], None] | None = None,
                 artifact_sink: Callable[[dict], None] | None = None,
                 side_order: tuple[int, int] = (0, 1)):
        if sorted(side_order) != [0, 1]:
            raise ValueError("Each physical side must execute once per tick")
        self.backend, self.spec, self.model_profile = backend, spec, model_profile
        self.sink, self.side_order = sink, side_order
        self.artifact_sink = artifact_sink
        self._artifact_sequence = 0
        self._episode_id = None
        self.records: list[dict] = []
        self.audit: list[dict] = []

    def archive(self, kind: str, value: PairState | RoundTape, label: str) -> None:
        if self.artifact_sink is None:
            return
        identity = self.digest(value) if kind == "pair" else canonical_digest(value.identity())
        self.artifact_sink({"episode_id": self._episode_id, "sequence": self._artifact_sequence,
                            "kind": kind, "label": label, "digest": identity, "value": value})
        after = self.digest(value) if kind == "pair" else canonical_digest(value.identity())
        if after != identity:
            raise RuntimeError("Archive writer mutated a scientific state")
        self._artifact_sequence += 1

    def clone(self, pair: PairState) -> PairState:
        # World is immutable; exports are immutable backend-owned copies.
        return PairState(tuple(self.backend.clone(s) for s in pair.models),
                         pair.world, pair.windows)

    def digest(self, pair: PairState) -> str:
        return canonical_digest({"models": [self.backend.digest(s) for s in pair.models],
                                 "world": asdict(pair.world),
                                 "windows": [[x.identity() for x in w] for w in pair.windows]})

    def initialize(self, episode: tasks.Episode) -> PairState:
        system, users = tasks.initial_prompts(episode)
        pair = PairState(tuple(self.backend.create(system, user) for user in users),
                         tasks.initial_world(episode))
        for state in pair.models:
            for _ in range(self.spec.preparation_tokens):
                self.backend.step(state, (), 0.0)
            self.backend.finish_turn(state)
        return pair

    def prepare(self, episode: tasks.Episode, pair: PairState, round_id: int,
                *, pulse: bool | None = None, goal_changed: bool | None = None) -> None:
        if goal_changed is None:
            world = tasks.event_world(episode, pair.world, round_id, pulse=pulse)
            updated = tasks.updated_sides(episode, round_id)
        else:
            world = tasks.goal_probe_world(episode, pair.world, round_id, changed=goal_changed)
            focal = tasks.focal_side(episode, round_id)
            updated = tuple(goal_changed and side == focal for side in (0, 1))
        texts = tasks.round_prompts(episode, world, round_id, updated)
        pair.windows = ((), ())
        for side in (0, 1):
            self.backend.begin_user(pair.models[side], texts[side])
        pair.world = world

    def _incoming(self, pair: PairState, policy: str, side: int, tick: int,
                  tape: RoundTape | None, focal: int | None) -> tuple[Export, ...]:
        partner = 1-side
        if policy == "OFF" or (policy == "A_TO_B" and side == 0) or (
                policy == "B_TO_A" and side == 1):
            return ()
        if policy == "Fcut" and side == 1-focal:
            return ()
        if policy == "Rcut" and side == focal:
            return ()
        if policy == "FRESH" or (policy == "Replay" and side == focal):
            if tape is None or tape.round_id != pair.world.round_id:
                raise ValueError("Replay/FRESH requires its exact round tape")
            return tape.source(partner, tick, self.spec.window)
        return pair.windows[partner]

    def work(self, pair: PairState, policy: str, *, tape: RoundTape | None = None,
             focal: int | None = None) -> tuple[RoundTape, tuple[tuple[Export, ...], ...]]:
        if policy not in (*POLICIES, "L", "Fcut", "Rcut", "Replay"):
            raise ValueError("Unknown channel policy")
        if policy in ("Fcut", "Rcut", "Replay") and focal not in (0, 1):
            raise ValueError("Directional intervention requires a focal side")
        parent = self.digest(pair)
        if policy == "FRESH":
            shadow = self.clone(pair)
            tape, _ = self.work(shadow, "OFF")
            if self.digest(pair) != parent:
                raise RuntimeError("FRESH shadow contaminated the actual pair")
            self.archive("tape", tape, f"fresh_round{pair.world.round_id}")
        entries: list[list[Export]] = [[], []]
        for tick in range(self.spec.work_tokens):
            incoming = tuple(self._incoming(pair, policy, s, tick, tape, focal) for s in (0, 1))
            outgoing: list[Export | None] = [None, None]
            for side in self.side_order:
                outgoing[side] = self.backend.step(pair.models[side], incoming[side], self.spec.gain)
            for side in (0, 1):
                export = outgoing[side]
                if export is None:
                    raise RuntimeError("Uncommitted generation step")
                if entries[side] and export.position <= entries[side][-1].position:
                    raise RuntimeError("Generated source positions must increase")
                entries[side].append(export)
            # The next global tick sees both newly committed positions together.
            pair.windows = tuple(tuple(row[-self.spec.window:]) for row in entries)
            self.audit.append({"round_id": pair.world.round_id, "policy": policy, "tick": tick,
                               "incoming": [[x.identity() for x in w] for w in incoming]})
        held = tuple(self._incoming(pair, policy, s, self.spec.work_tokens, tape, focal)
                     for s in (0, 1))
        return RoundTape(pair.world.round_id, tuple(tuple(row) for row in entries), parent), held

    def text_work(self, pair: PairState) -> tuple[tuple[Export, ...], ...]:
        if self.spec.work_tokens % 2:
            raise ValueError("Two equal text exchanges require even work duration")
        for _ in range(2):
            messages = []
            for side in (0, 1):
                exports = tuple(self.backend.step(pair.models[side], (), 0.0)
                                for _ in range(self.spec.work_tokens//2))
                messages.append(self.backend.decode(exports))
            # No participant sees the exchange before both messages exist.
            for side in (0, 1):
                self.backend.finish_turn(pair.models[side])
                other = "B" if side == 0 else "A"
                self.backend.begin_user(pair.models[side], f"Message from participant {other}:\n"
                                        + messages[1-side])
        pair.windows = ((), ())
        return ((), ())

    def _read(self, episode: tasks.Episode, pair: PairState, side: int, qid: str,
              held: tuple[tuple[Export, ...], ...], checkpoint: int) -> tuple[Any, Probe, int | None]:
        q = tasks.question(episode, pair.world, side, qid, checkpoint=checkpoint or None)
        original = self.backend.digest(pair.models[side])
        p = self.backend.probe(pair.models[side], q.text, self.spec.choice_labels,
                               held[side], self.spec.gain)
        p.validate()
        if self.backend.digest(pair.models[side]) != original:
            raise RuntimeError("Readout mutated the continuing model state")
        choice = q.candidates[p.token_ids.index(p.token)] if p.token in p.token_ids else None
        return q, p, choice

    def emit(self, episode: tasks.Episode, pair: PairState, side: int, q: Any, p: Probe,
             choice: int | None, meta: dict, candidates: tuple[int, int] | None = None) -> dict:
        record = {"episode_id": episode.episode_id, "model_profile": self.model_profile,
                  "round_id": pair.world.round_id, "side": side, "qid": q.qid,
                  "status": "ok", "choice": choice, "correct_choice": q.correct,
                  "correct": choice == q.correct, "top_token": p.token,
                  "top_probability": p.probability, "legal_logits": list(p.legal_logits),
                  "legal_mass": p.legal_mass, "token_ids": list(p.token_ids),
                  "candidate_map": list(q.candidates), **meta}
        if getattr(self.backend, "kind", None) == "synthetic_fixture":
            record.update(backend_kind="synthetic_fixture", scientific_data=False)
        if candidates is not None:
            record.update(old_candidate=candidates[0], new_candidate=candidates[1])
        self.records.append(record)
        if self.sink is not None:
            self.sink(record)
        return record

    def actions(self, episode: tasks.Episode, pair: PairState,
                held: tuple[tuple[Export, ...], ...], meta: dict,
                *, candidates: dict[int, tuple[int, int]] | None = None,
                access: bool = False) -> None:
        reads = [self._read(episode, pair, side, "action", held, meta["checkpoint"])
                 for side in (0, 1)]
        if access:
            for side in (0, 1):
                q, p, choice = self._read(episode, pair, side, "partner_beacon", held, 0)
                self.emit(episode, pair, side, q, p, choice, meta)
        for side, (q, p, choice) in enumerate(reads):
            self.emit(episode, pair, side, q, p, choice, meta,
                      (candidates or {}).get(side))
        # Full-vocabulary choices for BOTH sides are sealed before either is consumed.
        pair.models = tuple(self.backend.commit_answer(reads[s][1], held[s], self.spec.gain)
                            for s in (0, 1))
        pair.world = tasks.transition(pair.world, tuple(read[2] for read in reads))

    def natural(self, episode: tasks.Episode, policy: str) -> dict[int, PairState]:
        pair = self.initialize(episode)
        checkpoints = {}
        for round_id in range(1, 7):
            if policy == "LIVE" and round_id in (2, 3, 5, 6):
                checkpoints[round_id] = self.clone(pair)
                self.archive("pair", checkpoints[round_id], f"live_before_round{round_id}")
            self.prepare(episode, pair, round_id)
            if policy == "TEXT":
                held = self.text_work(pair)
            else:
                _, held = self.work(pair, policy)
            meta = {"kind": "text" if policy == "TEXT" else "natural", "policy": policy,
                    "checkpoint": 0, "arm": policy, "version": 1}
            self.actions(episode, pair, held, meta, access=True)
        return checkpoints

    def pulses(self, episode: tasks.Episode, pre: PairState, checkpoint: int) -> None:
        focal = tasks.focal_side(episode, checkpoint)
        fixed = tasks.pulse_candidates(episode, pre.world, checkpoint)
        parent = self.digest(pre)
        reference: dict[int, RoundTape] = {}
        reference_end = None
        for arm in ("L", "Fcut", "Rcut", "Replay"):
            for version in (0, 1):
                pair = self.clone(pre)
                for round_id in (checkpoint, checkpoint+1):
                    self.prepare(episode, pair, round_id,
                                 pulse=bool(version) if round_id == checkpoint else None)
                    tape, held = self.work(pair, arm, tape=reference.get(round_id), focal=focal)
                    if arm == "L" and version == 0:
                        reference[round_id] = tape
                        self.archive("tape", tape, f"pulse{checkpoint}_q0_round{round_id}")
                    meta = {"kind": "pulse", "policy": "LIVE", "checkpoint": checkpoint,
                            "arm": arm, "version": version, "focal_side": focal}
                    target = 1-focal if round_id == checkpoint else focal
                    candidates = fixed["responder" if round_id == checkpoint else "initiator"]
                    self.actions(episode, pair, held, meta, candidates={target: candidates})
                if arm == "L" and version == 0:
                    reference_end = self.digest(pair)
                if arm == "Replay" and version == 0 and self.digest(pair) != reference_end:
                    raise RuntimeError("Unchanged two-round replay failed exact state equivalence")
        if self.digest(pre) != parent:
            raise RuntimeError("Pulse branch contaminated its parent")

    def goals(self, episode: tasks.Episode, pre: PairState, checkpoint: int) -> None:
        focal = tasks.focal_side(episode, checkpoint)
        old = pre.world.goals[focal]
        new = episode.probe_goals[0 if checkpoint == 3 else 1]
        row = episode.transfer_rows[0 if checkpoint == 3 else 1]
        candidates = (row[old], row[new])
        parent = self.digest(pre)
        reference = None
        reference_readouts = None
        for arm in ("L", "Fcut", "Replay"):
            for version in (0, 1):
                pair = self.clone(pre)
                self.prepare(episode, pair, checkpoint, goal_changed=bool(version))
                tape, held = self.work(pair, arm, tape=reference, focal=focal)
                if arm == "L" and version == 0:
                    reference = tape
                    self.archive("tape", tape, f"goal{checkpoint}_q0")
                meta = {"kind": "goal", "policy": "LIVE", "checkpoint": checkpoint,
                        "arm": arm, "version": version, "focal_side": focal}
                observed = []
                for side in (0, 1):
                    for qid in GOAL_QIDS:
                        q, p, choice = self._read(episode, pair, side, qid, held, checkpoint)
                        self.emit(episode, pair, side, q, p, choice, meta,
                                  candidates if qid == "transfer_action" else None)
                        observed.append((p.token, p.legal_logits, p.legal_mass))
                if arm == "L" and version == 0:
                    reference_readouts = observed
                if arm == "Replay" and version == 0 and observed != reference_readouts:
                    raise RuntimeError("Unchanged goal replay differs from live readouts")
        if self.digest(pre) != parent:
            raise RuntimeError("Goal probe contaminated its parent")

    def run_episode(self, episode: tasks.Episode, *, text_reference: bool = False) -> list[dict]:
        self.records, self.audit = [], []
        self._episode_id, self._artifact_sequence = episode.episode_id, 0
        checkpoints = self.natural(episode, "LIVE")
        for policy in POLICIES[1:]:
            self.natural(episode, policy)
        for checkpoint in (2, 5):
            self.pulses(episode, checkpoints[checkpoint], checkpoint)
        for checkpoint in (3, 6):
            self.goals(episode, checkpoints[checkpoint], checkpoint)
        if text_reference:
            self.natural(episode, "TEXT")
        expected = 328 + (24 if text_reference else 0)
        if len(self.records) != expected:
            raise RuntimeError(f"Episode expected {expected} records, got {len(self.records)}")
        return self.records
