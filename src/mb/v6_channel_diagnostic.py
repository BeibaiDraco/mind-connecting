"""Small exploratory channel/task decomposition, without model dispatch."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import permutations
import random

from mb import v6_interaction_pilot as pilot, v6_task_clarity as clarity, v6_tasks as tasks
from mb.v6_runtime import PairState

CONTRACT = "v6-channel-rule-exploration-20261019-v1"
SEED = 202610190071
CONDITIONS = ("LIVE", "OFF", "LIVE_SELF_REPORT", "OFF_SELF_REPORT", "TEXT_FACTS")
QIDS = ("action", "latest_goal", "own_rule", "partner_beacon", "beacon_pair")
SELF_REPORT = (
    "Begin your working note by stating your own participant identity, your own "
    "current beacon, and your own latest assigned goal from your records. Then "
    "work on your button decision. Make clear whose state or rule each statement "
    "describes. Do not treat the other participant's assignment as your own.")


def materials() -> tuple[tasks.Episode, ...]:
    rng = random.Random(SEED)
    actions = rng.sample(list(permutations(tasks.ACTION_NAMES)), 2)
    goals = rng.sample(list(permutations(tasks.GOAL_NAMES)), 2)
    options = rng.sample(list(permutations(range(4))), 2)
    return tuple(clarity._episode(i, "v6_channel_explore_20261019", rng,
        actions[i], goals[i], options[i], beacons=(1-i, i),
        assigned=(i, 3-i), focal=i) for i in range(2))


def round_messages(ep: tasks.Episode, world: tasks.World,
                   updated: tuple[bool, bool], condition: str) -> tuple[str, str]:
    if condition not in CONDITIONS:
        raise ValueError("Unknown diagnostic condition")
    messages = list(pilot.round_messages(ep, world, updated))
    for side in (0, 1):
        if condition.endswith("SELF_REPORT"):
            messages[side] += "\n" + SELF_REPORT
        if condition == "TEXT_FACTS":
            messages[side] += (f"\nController observation of participant {tasks.ROLES[1-side]}: "
                f"their CURRENT beacon is {tasks.BEACON_NAMES[world.beacons[1-side]]}.")
    return tuple(messages)


@dataclass(frozen=True)
class DiagnosticQuestion:
    qid: str
    text: str
    candidates: tasks.Four
    correct: int


def question(ep: tasks.Episode, world: tasks.World, side: int, qid: str):
    if qid not in QIDS:
        raise ValueError("Unknown diagnostic readout")
    if qid == "action":
        return clarity.question(ep, world, side, "P2", "action")
    if qid not in ("own_rule", "beacon_pair"):
        return tasks.question(ep, world, side, qid)
    if qid == "own_rule":
        order, correct = ep.option_orders[1], world.goals[side]
        stem = (f"For participant {tasks.ROLES[side]}'s OWN latest assignment, which "
                "pair of buttons does the Action rule specify, in the order "
                "(OTHER beacon Dim, OTHER beacon Bright)? Select the rule pair "
                "without applying the device transition.")
        values = tuple(f"Dim: {ep.action_names[tasks.correct_action(g, 0)]}; "
                       f"Bright: {ep.action_names[tasks.correct_action(g, 1)]}" for g in range(4))
    else:
        order, correct = ep.option_orders[2], 2*world.beacons[0]+world.beacons[1]
        stem = "Which pair of CURRENT device beacons best fits the available information?"
        values = tuple(f"A: {tasks.BEACON_NAMES[v//2]}; B: {tasks.BEACON_NAMES[v%2]}"
                       for v in range(4))
    options = "\n".join(f"{label}. {values[v]}" for label, v in zip(tasks.LABELS, order))
    return DiagnosticQuestion(qid, stem+"\n"+options+"\n"+tasks.ANSWER_LINE, order, correct)


class ChannelRunner(pilot.PilotRunner):
    """Five histories from a common fresh pair; diagnostic probes are discarded."""

    condition: str = "LIVE"

    def prepare(self, ep, pair, round_id, *, pulse=None, goal_changed=None):
        if pulse is not None or goal_changed is not None:
            raise ValueError("No extra intervention branches in this diagnostic")
        world = tasks.event_world(ep, pair.world, round_id)
        messages = round_messages(ep, world, tasks.updated_sides(ep, round_id), self.condition)
        pair.windows = ((), ())
        for side in (0, 1):
            self.backend.begin_user(pair.models[side], messages[side])
        pair.world = world

    def _read(self, ep, pair, side, qid, held, checkpoint):
        q = question(ep, pair.world, side, qid)
        before = self.backend.digest(pair.models[side])
        p = self.backend.probe(pair.models[side], q.text, self.spec.choice_labels,
                               held[side], self.spec.gain)
        p.validate()
        if self.backend.digest(pair.models[side]) != before:
            raise RuntimeError("Diagnostic probe mutated continuing history")
        choice = q.candidates[p.token_ids.index(p.token)] if p.token in p.token_ids else None
        detail = {"question": q.text, "world": asdict(pair.world)}
        if self.probe_sink:
            detail.update(self.probe_sink(p))
        self._pending[id(p)] = detail
        return q, p, choice

    def actions(self, ep, pair, held, meta, *, candidates=None, access=False):
        for side in (0, 1):
            for qid in ("own_rule", "beacon_pair"):
                q, p, choice = self._read(ep, pair, side, qid, held, 0)
                self.emit(ep, pair, side, q, p, choice, meta)
        super().actions(ep, pair, held, meta)

    def run_diagnostic(self, ep: tasks.Episode, *, reverse_order: bool = False) -> list[dict]:
        self.records, self.audit, self._pending = [], [], {}
        self._episode_id, self._artifact_sequence = ep.episode_id, 0
        initial = self.initialize(ep)
        parent = self.digest(initial)
        self.archive("pair", initial, "common_initial_pair")
        for condition in CONDITIONS[::-1] if reverse_order else CONDITIONS:
            self.condition = condition
            policy = "LIVE" if condition.startswith("LIVE") else "OFF"
            pair = self.clone(initial)
            for rd in (1, 2, 3):
                self.prepare(ep, pair, rd)
                _, held = self.work(pair, policy)
                self.actions(ep, pair, held, {"kind": "channel_diagnostic", "policy": policy,
                    "arm": condition, "checkpoint": 0, "version": 1})
            if self.digest(initial) != parent:
                raise RuntimeError("A condition contaminated its common parent")
        if len(self.records) != 150 or self._pending:
            raise RuntimeError("Incomplete channel diagnostic")
        return self.records


def plan() -> dict:
    return {"contract": CONTRACT, "seed": SEED, "episodes": [asdict(ep) for ep in materials()],
        "conditions": list(CONDITIONS), "qids": list(QIDS), "rounds": [1, 2, 3],
        "records": 300, "gain": 1.0, "work_tokens": 64, "preparation_tokens": 16,
        "window": 16, "backend": "original_native", "formal_authorized": False,
        "scientific_admission": False, "automatic_continuation": False,
        "second_episode_condition_order": "reversed", "outcome_threshold": None}
