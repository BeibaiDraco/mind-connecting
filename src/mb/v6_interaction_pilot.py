"""Finite exploratory interaction cases; no GPU loader or formal dispatcher."""
from __future__ import annotations

from dataclasses import asdict
from itertools import permutations
import random
from typing import Any, Callable

from mb import v6_task_clarity as clarity, v6_tasks as tasks
from mb.v6_contract import canonical_digest
from mb.v6_runtime import EpisodeRunner, PairState

CONTRACT = "v6-two-pair-interaction-exploration-20261019-v1"
SEED = 202610190052
GAIN = 1.0
POLICIES = ("LIVE", "OFF", "FRESH")
WORK_INSTRUCTION = (
    "Work through the decision: identify your assigned goal, retrieve its Dim/Bright "
    "rule, use the OTHER beacon, then identify the button. The own-device transition "
    "happens only after that decision. Keep the two participants' facts separate.")


def materials() -> tuple[tasks.Episode, ...]:
    rng = random.Random(SEED)
    actions = rng.sample(list(permutations(tasks.ACTION_NAMES)), 2)
    goals = rng.sample(list(permutations(tasks.GOAL_NAMES)), 2)
    options = rng.sample(list(permutations(range(4))), 2)
    return tuple(clarity._episode(i, "v6_interaction_explore_20261019", rng,
        actions[i], goals[i], options[i], beacons=(i, 1-i),
        assigned=(2*i, 2*i+1), focal=i) for i in range(2))


def round_messages(ep: tasks.Episode, world: tasks.World,
                   updated: tuple[bool, bool]) -> tuple[str, str]:
    return tuple(text + "\n" + WORK_INSTRUCTION
                 for text in tasks.round_prompts(ep, world, world.round_id, updated))


class PilotRunner(EpisodeRunner):
    """Reuse the original synchronous channel, action commit and exact replay."""

    def __init__(self, *args: Any, probe_sink: Callable | None = None,
                 trace_sink: Callable | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.probe_sink, self.trace_sink = probe_sink, trace_sink
        self._pending: dict[int, dict] = {}

    def initialize(self, episode: tasks.Episode) -> PairState:
        system, users = clarity.initial_prompts(episode, "P2")
        pair = PairState(tuple(self.backend.create(system, user) for user in users),
                         tasks.initial_world(episode))
        for state in pair.models:
            for _ in range(self.spec.preparation_tokens):
                self.backend.step(state, (), 0.0)
            self.backend.finish_turn(state)
        return pair

    def prepare(self, episode: tasks.Episode, pair: PairState, round_id: int,
                *, pulse: bool | None = None, goal_changed: bool | None = None) -> None:
        if goal_changed is not None:
            raise ValueError("Goal intervention is outside this finite pilot")
        world = tasks.event_world(episode, pair.world, round_id, pulse=pulse)
        texts = round_messages(episode, world, tasks.updated_sides(episode, round_id))
        pair.windows = ((), ())
        for side in (0, 1):
            self.backend.begin_user(pair.models[side], texts[side])
        pair.world = world

    def _read(self, episode, pair, side, qid, held, checkpoint):
        q = (clarity.question(episode, pair.world, side, "P2", "action")
             if qid == "action" else tasks.question(episode, pair.world, side, qid))
        before = self.backend.digest(pair.models[side])
        p = self.backend.probe(pair.models[side], q.text, self.spec.choice_labels,
                               held[side], self.spec.gain)
        p.validate()
        if self.backend.digest(pair.models[side]) != before:
            raise RuntimeError("Diagnostic readout mutated continuing history")
        choice = q.candidates[p.token_ids.index(p.token)] if p.token in p.token_ids else None
        detail = {"question": q.text, "world": asdict(pair.world)}
        if self.probe_sink:
            detail.update(self.probe_sink(p))
        self._pending[id(p)] = detail
        return q, p, choice

    def emit(self, episode, pair, side, q, p, choice, meta, candidates=None):
        extra = self._pending.pop(id(p))
        return super().emit(episode, pair, side, q, p, choice,
            {**meta, **extra, "exploratory": True, "formal_authorized": False}, candidates)

    def actions(self, episode, pair, held, meta, *, candidates=None, access=False):
        for side in (0, 1):
            q, p, choice = self._read(episode, pair, side, "latest_goal", held, 0)
            self.emit(episode, pair, side, q, p, choice, meta)
        super().actions(episode, pair, held, meta, candidates=candidates, access=True)

    def work(self, pair, policy, *, tape=None, focal=None):
        result, held = super().work(pair, policy, tape=tape, focal=focal)
        if self.trace_sink:
            self.trace_sink({"episode_id": self._episode_id, "policy": policy,
                "focal_side": focal, "world": asdict(pair.world),
                "parent_digest": result.parent_digest,
                "tokens": [[x.token for x in row] for row in result.entries],
                "text": [self.backend.decode(row) for row in result.entries]})
        return result, held

    def run_pilot(self, episode: tasks.Episode) -> list[dict]:
        self.records, self.audit, self._pending = [], [], {}
        self._episode_id, self._artifact_sequence = episode.episode_id, 0
        checkpoint = None
        for policy in POLICIES:
            pair = self.initialize(episode)
            for round_id in (1, 2, 3):
                if policy == "LIVE" and round_id == 2:
                    checkpoint = self.clone(pair)
                    self.archive("pair", checkpoint, "live_before_round2")
                self.prepare(episode, pair, round_id)
                _, held = self.work(pair, policy)
                self.actions(episode, pair, held, {"kind": "natural", "policy": policy,
                    "checkpoint": 0, "arm": policy, "version": 1})
        if checkpoint is None:
            raise RuntimeError("Missing common causal checkpoint")
        self.pulses(episode, checkpoint, 2)
        if len(self.records) != 150 or self._pending:
            raise RuntimeError("Incomplete finite pilot")
        return self.records


def plan() -> dict:
    return {"contract": CONTRACT, "seed": SEED, "episodes": [asdict(e) for e in materials()],
        "gain": GAIN, "work_tokens": 64, "preparation_tokens": 16, "window": 16,
        "natural_policies": list(POLICIES), "rounds": [1, 2, 3], "pulse_checkpoint": 2,
        "pulse_arms": ["L", "Fcut", "Rcut", "Replay"], "pulse_versions": [0, 1],
        "records": 300, "backend": "original_native", "formal_authorized": False,
        "scientific_admission": False, "automatic_continuation": False}
