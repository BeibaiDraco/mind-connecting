"""Torch-free materials for the proposed continuous v6 task.

This is local preparation for an unfrozen proposal, not an execution approval.
Integers identify physical meanings, never option positions or tokenizer IDs.
The two extra beacon choices (unknown and another beacon) are proposed format
foils. They are not additional states of the private device.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter
from dataclasses import asdict, dataclass, replace
from itertools import permutations
from pathlib import Path
from typing import Any, Iterable

CONTRACT = "v6-continuous-materials-draft-v1"
ROLES = ("A", "B")
GOAL_NAMES = ("G0", "G1", "G2", "G3")
ACTION_NAMES = ("Left", "Right", "Up", "Down")
TRANSFER_NAMES = ("Oak", "Pine", "Ash", "Elm")
BEACON_NAMES = ("Dim", "Bright", "Unknown", "Another beacon")
QIDS = ("action", "transfer_action", "original_goal", "latest_goal",
        "partner_beacon", "partner_goal")
LABELS = ("1", "2", "3", "4")
NEXT_BEACON = (0, 1, 1, 0)
ANSWER_LINE = "Answer with the option number only."
Four = tuple[int, int, int, int]
Pair = tuple[int, int]
Actions = tuple[int | None, int | None]


def _integer(value: Any, low: int, high: int, name: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"invalid {name}")


def _pair(values: Any, high: int, name: str) -> None:
    if not isinstance(values, tuple) or len(values) != 2:
        raise ValueError(f"{name} must be an immutable pair")
    for value in values:
        _integer(value, 0, high, name)


def _permutation(values: Any) -> None:
    if (not isinstance(values, tuple) or len(values) != 4
            or any(type(x) is not int for x in values) or set(values) != set(range(4))):
        raise ValueError("expected an immutable four-way permutation")


@dataclass(frozen=True)
class Episode:
    episode_id: str
    stage: str
    seed: int
    initial_beacons: Pair
    original_goals: Pair
    early_side: int
    updated_goals: Pair
    probe_goals: Pair
    action_names: tuple[str, str, str, str]
    goal_names: tuple[str, str, str, str]
    transfer_rows: tuple[Four, Four]
    # Orders are action, goal, beacon, transfer; transfer is independent of action.
    option_orders: tuple[Four, Four, Four, Four]
    transfer_names: tuple[str, str, str, str] = TRANSFER_NAMES

    def __post_init__(self) -> None:
        if not isinstance(self.stage, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", self.stage):
            raise ValueError("stage must be a nonempty material namespace")
        if not isinstance(self.episode_id, str) or not self.episode_id.startswith(self.stage + "-"):
            raise ValueError("episode identity must include its stage")
        _integer(self.seed, 0, 2**64 - 1, "episode seed")
        _pair(self.initial_beacons, 1, "initial beacons")
        _pair(self.original_goals, 3, "original goals")
        _pair(self.updated_goals, 3, "updated goals")
        _pair(self.probe_goals, 3, "probe goals")
        _integer(self.early_side, 0, 1, "early side")
        if len(set(self.original_goals)) != 2:
            raise ValueError("initial goals must differ")
        early_goal, late_goal = self.updated_goals
        own_early = self.original_goals[self.early_side]
        if early_goal in self.original_goals or late_goal in (own_early, early_goal):
            raise ValueError("scheduled goal update repeats its own or partner's goal")
        if self.probe_goals[0] in (own_early, early_goal):
            raise ValueError("early probe goal is not a distinct alternative")
        if self.probe_goals[1] in (early_goal, late_goal):
            raise ValueError("late probe goal is not a distinct alternative")
        for values, expected in ((self.action_names, ACTION_NAMES),
                                 (self.goal_names, GOAL_NAMES),
                                 (self.transfer_names, TRANSFER_NAMES)):
            if not isinstance(values, tuple) or len(values) != 4 or set(values) != set(expected):
                raise ValueError("unrecognized proposed symbol codebook")
        if not isinstance(self.transfer_rows, tuple) or len(self.transfer_rows) != 2:
            raise ValueError("two transfer rows are required")
        if not isinstance(self.option_orders, tuple) or len(self.option_orders) != 4:
            raise ValueError("four independent option orders are required")
        for values in (*self.transfer_rows, *self.option_orders):
            _permutation(values)


@dataclass(frozen=True)
class World:
    beacons: Pair
    goals: Pair
    round_id: int = 0
    actions: tuple[Actions, ...] = ()

    def __post_init__(self) -> None:
        _pair(self.beacons, 1, "beacons")
        _pair(self.goals, 3, "goals")
        _integer(self.round_id, 0, 6, "round")
        if (not isinstance(self.actions, tuple)
                or len(self.actions) not in ({0} if self.round_id == 0
                                             else {self.round_id - 1, self.round_id})):
            raise ValueError("action history is inconsistent with the round")
        for pair in self.actions:
            _actions(pair)


@dataclass(frozen=True)
class Question:
    qid: str
    text: str
    candidates: Four
    correct: int

    def __post_init__(self) -> None:
        if self.qid not in QIDS or not isinstance(self.text, str) or not self.text:
            raise ValueError("invalid question")
        _permutation(self.candidates)
        _integer(self.correct, 0, 3, "correct physical meaning")

    @property
    def correct_label(self) -> str:
        return LABELS[self.candidates.index(self.correct)]


def _actions(actions: Any) -> None:
    if not isinstance(actions, tuple) or len(actions) != 2:
        raise ValueError("actions must be a physical A/B pair")
    for value in actions:
        if value is not None:
            _integer(value, 0, 3, "actual action; invalid model output is None")


def correct_action(goal: int, partner_beacon: int) -> int:
    _integer(goal, 0, 3, "goal")
    _integer(partner_beacon, 0, 1, "partner beacon")
    return goal ^ (2 * partner_beacon)


def initial_world(ep: Episode) -> World:
    return World(ep.initial_beacons, ep.original_goals)


def focal_side(ep: Episode, checkpoint: int) -> int:
    if checkpoint not in (2, 3, 5, 6):
        raise ValueError("checkpoint must be 2/5 (pulse) or 3/6 (goal)")
    return ep.early_side if checkpoint in (2, 3) else 1 - ep.early_side


def updated_sides(ep: Episode, round_id: int) -> tuple[bool, bool]:
    _integer(round_id, 1, 6, "round")
    recipient = 1 - focal_side(ep, round_id) if round_id in (2, 5) else None
    return tuple(side == recipient for side in range(2))


def event_world(ep: Episode, world: World, round_id: int,
                pulse: bool | None = None) -> World:
    """Advance one round after real actions; False suppresses only the 2/5 flip."""
    _integer(round_id, 1, 6, "round")
    if world.round_id != round_id - 1 or len(world.actions) != round_id - 1:
        raise ValueError("each new event requires exactly one preceding action pair")
    if pulse is not None and (type(pulse) is not bool or round_id not in (2, 5)):
        raise ValueError("a pulse override is allowed only at round 2 or 5")
    beacons, goals = list(world.beacons), list(world.goals)
    if round_id in (2, 5):
        focal = focal_side(ep, round_id)
        new_goal = ep.updated_goals[0 if round_id == 2 else 1]
        if new_goal in goals:
            raise ValueError("scheduled update is incompatible with this goal history")
        goals[1 - focal] = new_goal
        if pulse is not False:
            beacons[focal] ^= 1
    return World(tuple(beacons), tuple(goals), round_id, world.actions)


def transition(world: World, actions: Actions) -> World:
    """Apply only each side's actual action; invalid output holds its own beacon."""
    _actions(actions)
    if world.round_id == 0 or len(world.actions) != world.round_id - 1:
        raise ValueError("transition requires an uncommitted round")
    beacons = tuple(world.beacons[k] if a is None else NEXT_BEACON[a]
                    for k, a in enumerate(actions))
    return replace(world, beacons=beacons, actions=world.actions + (actions,))


def goal_probe_world(ep: Episode, world: World, checkpoint: int,
                     changed: bool) -> World:
    """Start a discarded 3/6 probe from the post-action world of round 2/5."""
    if checkpoint not in (3, 6) or type(changed) is not bool:
        raise ValueError("goal probe requires round 3/6 and a Boolean variant")
    current = event_world(ep, world, checkpoint)
    focal = focal_side(ep, checkpoint)
    alternative = ep.probe_goals[0 if checkpoint == 3 else 1]
    if alternative in current.goals:
        raise ValueError("probe alternative must differ from both current goals")
    if not changed:
        return current
    goals = list(current.goals)
    goals[focal] = alternative
    return replace(current, goals=tuple(goals))


def pulse_candidates(ep: Episode, world: World, checkpoint: int) -> dict[str, Pair]:
    """Fixed oracle candidates; unrelated to errors on subsequently run branches."""
    if checkpoint not in (2, 5):
        raise ValueError("pulse candidates require checkpoint 2/5")
    focal = focal_side(ep, checkpoint)
    responder, initiator = [], []
    for changed in (False, True):
        current = event_world(ep, world, checkpoint, changed)
        reply = correct_action(current.goals[1 - focal], current.beacons[focal])
        responder.append(reply)
        initiator.append(correct_action(current.goals[focal], NEXT_BEACON[reply]))
    if responder[0] == responder[1] or initiator[0] == initiator[1]:
        raise AssertionError("the proposed oracle requires distinct physical candidates")
    return {"responder": tuple(responder), "initiator": tuple(initiator)}


def initial_prompts(ep: Episode) -> tuple[str, tuple[str, str]]:
    """The same public card and two separate private cards; no scorer answers."""
    columns = " | ".join(ep.goal_names)
    table = ["Partner beacon | " + columns]
    for bit in range(2):
        table.append(BEACON_NAMES[bit] + " | " + " | ".join(
            ep.action_names[correct_action(goal, bit)] for goal in range(4)))
    transitions = [f"{ep.action_names[a]} -> {BEACON_NAMES[NEXT_BEACON[a]]}"
                   for a in range(4)]
    system = (
        "Participants A and B control separate private devices.\n"
        "You control your own device. Use your own latest assigned goal and the other "
        "participant's current beacon to choose your button. Your button determines "
        "your own device's next beacon using the transition table. Your partner has "
        "a separate assignment. During work periods, keep a brief working note about "
        "the current situation. When asked to act, answer with exactly one choice ID.\n"
        "Action table:\n" + "\n".join(table) + "\nOwn-device transition table:\n"
        + "\n".join(transitions))
    private = tuple(
        f"You are participant {ROLES[k]}.\nYour initial beacon: {BEACON_NAMES[ep.initial_beacons[k]]}.\n"
        f"Your original assigned goal: {ep.goal_names[ep.original_goals[k]]}."
        for k in range(2))
    return system, private


def round_prompts(ep: Episode, world: World, round_id: int,
                  goal_updated: tuple[bool, bool]) -> tuple[str, str]:
    """Only own fields enter each message; flags are physical (A, B) Booleans."""
    if world.round_id != round_id or len(world.actions) != round_id - 1:
        raise ValueError("round prompt requires the current pre-action world")
    if (not isinstance(goal_updated, tuple) or len(goal_updated) != 2
            or any(type(x) is not bool for x in goal_updated)):
        raise ValueError("goal_updated must be the two physical-side Boolean flags")
    messages = []
    for k in range(2):
        update = (f"Use goal {ep.goal_names[world.goals[k]]}." if goal_updated[k]
                  else "Keep your previous assignment.")
        messages.append(
            f"Round {round_id}.\nParticipant {ROLES[k]}'s current beacon: "
            f"{BEACON_NAMES[world.beacons[k]]}.\nGoal update: {update}\n"
            "Work on the current situation. Prepare to choose your own button.")
    return tuple(messages)


def question(ep: Episode, world: World, side: int, qid: str,
             checkpoint: int | None = None) -> Question:
    _integer(side, 0, 1, "physical side")
    if qid not in QIDS:
        raise ValueError("unknown v6 question")
    if world.round_id == 0 or len(world.actions) != world.round_id - 1:
        raise ValueError("questions describe a pre-action measurement state")
    own, partner = ROLES[side], ROLES[1 - side]
    if qid == "action":
        stem = (f"Which button is prescribed by participant {own}'s own latest assigned "
                "goal for the current situation?")
        values, order = ep.action_names, ep.option_orders[0]
        correct = correct_action(world.goals[side], world.beacons[1 - side])
    elif qid == "transfer_action":
        if checkpoint not in (3, 6) or world.round_id != checkpoint:
            raise ValueError("transfer action requires its round-3/6 checkpoint")
        row = ep.transfer_rows[0 if checkpoint == 3 else 1]
        mapping = "; ".join(f"{ep.goal_names[g]} -> {ep.transfer_names[row[g]]}"
                            for g in range(4))
        stem = (f"Participant {partner}'s current beacon is "
                f"{BEACON_NAMES[world.beacons[1 - side]]}. For this decision only, "
                "the following single row replaces the usual beacon-conditioned action "
                f"table for either participant: {mapping}. Using participant {own}'s "
                "own latest assigned goal, which button do you choose?")
        values, order, correct = ep.transfer_names, ep.option_orders[3], row[world.goals[side]]
    elif qid in ("original_goal", "latest_goal", "partner_goal"):
        target = partner if qid == "partner_goal" else own
        if qid == "original_goal":
            stem = (f"According to participant {target}'s initial private record before "
                    "any updates, which goal was originally assigned to that participant?")
            correct = ep.original_goals[side]
        else:
            stem = (f"According to the most recent authorized controller update (or the "
                    f"initial record if unchanged), which goal is participant {target} assigned?")
            correct = world.goals[1 - side if qid == "partner_goal" else side]
        values, order = ep.goal_names, ep.option_orders[1]
    else:
        stem = f"What is participant {partner}'s current private beacon?"
        values, order, correct = BEACON_NAMES, ep.option_orders[2], world.beacons[1 - side]
    options = "\n".join(f"{label}. {values[value]}" for label, value in zip(LABELS, order))
    return Question(qid, f"{stem}\n{options}\n{ANSWER_LINE}", order, correct)


def _seed(*values: Any) -> int:
    raw = json.dumps((CONTRACT, *values), separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def make_episodes(n: int, stage: str, seed: int = 0) -> list[Episode]:
    """Stage-namespaced draws; N240 has exact advertised initial marginal balance."""
    _integer(n, 1, 1_000_000, "episode count")
    _integer(seed, 0, 2**64 - 1, "generation seed")
    if not isinstance(stage, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", stage):
        raise ValueError("stage must be a nonempty material namespace")
    namespace = f"{_seed(stage, seed):016x}"
    shared = random.Random(_seed(stage, seed, "layout"))
    pairs = list(permutations(range(4), 2))
    shared.shuffle(pairs)
    # Each 12-pair block contains every goal three times for each physical side.
    # Sharing its randomly permuted names preserves literal-label marginal balance.
    goal_codebooks = [tuple(shared.sample(GOAL_NAMES, 4)) for _ in range((n + 11) // 12)]
    episodes = []
    for index in range(n):
        draw_seed = _seed(stage, seed, index)
        rng = random.Random(draw_seed)
        goals = pairs[index % 12]
        block = index // 12
        focal = block % 2
        beacon_pair = (block // 2 + index % 12) % 4
        early = rng.choice(sorted(set(range(4)) - set(goals)))
        late = rng.choice(sorted(set(range(4)) - {goals[focal], early}))
        probes = (rng.choice(sorted(set(range(4)) - {goals[focal], early})),
                  rng.choice(sorted(set(range(4)) - {early, late})))
        def shuffled(values):
            return tuple(rng.sample(values, len(values)))
        episodes.append(Episode(
            f"{stage}-{namespace}-{index:06d}", stage, draw_seed,
            (beacon_pair // 2, beacon_pair % 2), goals, focal, (early, late), probes,
            shuffled(ACTION_NAMES), goal_codebooks[block],
            (shuffled(range(4)), shuffled(range(4))),
            tuple(shuffled(range(4)) for _ in range(4)), shuffled(TRANSFER_NAMES)))
    shared.shuffle(episodes)
    return episodes


def episode_to_dict(ep: Episode) -> dict[str, Any]:
    return json.loads(json.dumps(asdict(ep)))


def episode_from_dict(data: dict[str, Any]) -> Episode:
    expected = set(Episode.__dataclass_fields__)
    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError("episode fields differ from the material contract")
    values = dict(data)
    for key in ("initial_beacons", "original_goals", "updated_goals", "probe_goals",
                "action_names", "goal_names", "transfer_names"):
        if not isinstance(values[key], (list, tuple)):
            raise ValueError("invalid serialized tuple")
        values[key] = tuple(values[key])
    for key in ("transfer_rows", "option_orders"):
        if not isinstance(values[key], (list, tuple)) or any(
                not isinstance(row, (list, tuple)) for row in values[key]):
            raise ValueError("invalid serialized rows")
        values[key] = tuple(tuple(row) for row in values[key])
    return Episode(**values)


def material_json(episodes: Iterable[Episode]) -> str:
    rows = list(episodes)
    if not rows or len({ep.episode_id for ep in rows}) != len(rows):
        raise ValueError("materials must contain nonempty unique episode identities")
    return json.dumps({"contract": CONTRACT, "status": "proposed_not_frozen",
                       "episodes": [episode_to_dict(ep) for ep in rows]},
                      sort_keys=True, ensure_ascii=True, indent=2) + "\n"


def materials_sha256(episodes: Iterable[Episode]) -> str:
    return hashlib.sha256(material_json(episodes).encode()).hexdigest()


def load_materials(path: str | Path) -> list[Episode]:
    data = json.loads(Path(path).read_text())
    if (set(data) != {"contract", "status", "episodes"} or data["contract"] != CONTRACT
            or data["status"] != "proposed_not_frozen" or not isinstance(data["episodes"], list)):
        raise ValueError("unrecognized proposed material document")
    episodes = [episode_from_dict(row) for row in data["episodes"]]
    material_json(episodes)
    return episodes


def write_materials(path: str | Path, episodes: Iterable[Episode]) -> str:
    """Write once; byte-identical reuse is allowed, replacement is not."""
    path, payload = Path(path), material_json(episodes).encode()
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("refusing to overwrite existing material bytes")
    else:
        with path.open("xb") as stream:
            stream.write(payload)
    return hashlib.sha256(payload).hexdigest()


def balance_report(episodes: Iterable[Episode]) -> dict[str, Any]:
    rows = list(episodes)
    material_json(rows)
    def counts(values):
        return dict(sorted(Counter(str(value) for value in values).items()))
    pair = counts(ep.original_goals for ep in rows)
    cells = counts((ep.early_side, *ep.initial_beacons) for ep in rows)
    literal_a = counts(ep.goal_names[ep.original_goals[0]] for ep in rows)
    literal_b = counts(ep.goal_names[ep.original_goals[1]] for ep in rows)
    return {
        "n": len(rows), "contract": CONTRACT, "status": "proposed_not_frozen",
        "stages": counts(ep.stage for ep in rows),
        "early_side": counts(ep.early_side for ep in rows),
        "original_goal_pairs": pair, "early_side_by_initial_beacons": cells,
        "initial_goals_A": counts(ep.original_goals[0] for ep in rows),
        "initial_goals_B": counts(ep.original_goals[1] for ep in rows),
        "literal_initial_goals_A": literal_a, "literal_initial_goals_B": literal_b,
        "full_initial_joint": counts((ep.early_side, *ep.initial_beacons,
                                      *ep.original_goals) for ep in rows),
        "updated_goals": counts(ep.updated_goals for ep in rows),
        "probe_goals": counts(ep.probe_goals for ep in rows),
        "literal_updated_goals": counts(tuple(ep.goal_names[g] for g in ep.updated_goals)
                                         for ep in rows),
        "literal_probe_goals": counts(tuple(ep.goal_names[g] for g in ep.probe_goals)
                                       for ep in rows),
        "goal_codebooks": counts(ep.goal_names for ep in rows),
        "action_codebooks": counts(ep.action_names for ep in rows),
        "option_orders": counts(ep.option_orders for ep in rows),
        "exact_N240_initial_marginals": (len(rows) == 240 and len(pair) == 12
            and set(pair.values()) == {20} and len(cells) == 8 and set(cells.values()) == {30}
            and len(literal_a) == len(literal_b) == 4
            and set(literal_a.values()) == set(literal_b.values()) == {60}),
        "limitations": "Only declared initial marginal balance is guaranteed at N240. "
        "Other sample sizes, event goals, codebooks and full joint cells are reported, not assumed balanced.",
        "sha256": materials_sha256(rows),
    }


def select_text_subset(episodes: Iterable[Episode], n: int = 60) -> list[Episode] | None:
    """Select only from immutable materials, with declared exact initial margins.

    The proposed N60/N240 subset has five of each ordered initial goal pair,
    30 of each early side, 15 of each beacon pair and displayed own goal per
    physical side, and 7 or 8 of each early-side/beacon cell. Other event and
    codebook joint margins are not controlled. None means the bounded solver
    did not establish an optimal feasible selection; never weaken a margin.
    """
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    rows = sorted(episodes, key=lambda ep: ep.episode_id)
    material_json(rows)
    _integer(n, 1, 1_000_000, "text subset size")
    if n % 12:
        raise ValueError("exact ordered-goal-pair balance requires a multiple of 12")
    if n > len(rows):
        return None
    constraints, lows, highs = [], [], []

    def constrain(predicate, low: int, high: int | None = None) -> None:
        constraints.append([int(predicate(ep)) for ep in rows])
        lows.append(low)
        highs.append(low if high is None else high)

    for pair in permutations(range(4), 2):
        constrain(lambda ep, p=pair: ep.original_goals == p, n // 12)
    for side in range(2):
        constrain(lambda ep, s=side: ep.early_side == s, n // 2)
    for pair in ((0, 0), (0, 1), (1, 0), (1, 1)):
        constrain(lambda ep, p=pair: ep.initial_beacons == p, n // 4)
        for side in range(2):
            constrain(lambda ep, p=pair, s=side: ep.initial_beacons == p and ep.early_side == s,
                      n // 8, (n + 7) // 8)
    for side in range(2):
        for name in GOAL_NAMES:
            constrain(lambda ep, s=side, g=name: ep.goal_names[ep.original_goals[s]] == g, n // 4)
    matrix = np.asarray(constraints, dtype=float)
    # Sorting and material-derived integer costs remove dependence on input order
    # or model outcomes. Solver/software versions belong in the later freeze.
    costs = np.asarray([1 + _seed("text-subset", ep.episode_id) % 1_000_003 for ep in rows], dtype=float)
    result = milp(costs, integrality=np.ones(len(rows)), bounds=Bounds(0, 1),
                  constraints=LinearConstraint(matrix, np.asarray(lows), np.asarray(highs)),
                  options={"time_limit": 30.0, "mip_rel_gap": 0.0})
    if not result.success or result.x is None:
        return None
    selected = np.rint(result.x).astype(int)
    if (np.max(np.abs(result.x - selected)) > 1e-6 or not np.isin(selected, (0, 1)).all()
            or selected.sum() != n):
        raise ValueError("text subset solver returned a nonintegral or wrong-size selection")
    realized = matrix @ selected
    if not ((realized >= np.asarray(lows)) & (realized <= np.asarray(highs))).all():
        raise ValueError("text subset fails a declared balance constraint")
    return [ep for ep, use in zip(rows, selected) if use]


def audit_tokenizer(tok: Any, episodes: Iterable[Episode]) -> dict[str, Any]:
    """Audit local native serialization and answer labels, without any model call."""
    from mb import chat

    rows = list(episodes)
    material_json(rows)
    profile = chat.profile_for_tokenizer(tok)
    spec = chat.runtime_tokens(tok)
    labels = tuple(tuple(chat.encode(tok, text)) for text in LABELS)
    errors: list[str] = []
    if labels != tuple((value,) for value in spec.label_ids):
        errors.append("label IDs do not match the validated profile")
    prefixes, event_lengths, question_lengths = 0, set(), set()
    seen: set[tuple[str, str, str, str]] = set()
    for ep in rows:
        system, private = initial_prompts(ep)
        world = initial_world(ep)
        for round_id in range(1, 7):
            world = event_world(ep, world, round_id)
            # All own beacon/goal/update alternatives, with unchanged partner fields.
            for side in range(2):
                lengths = set()
                for bit in range(2):
                    for goal in range(4):
                        for changed in (False, True):
                            beacons, goals = list(world.beacons), list(world.goals)
                            beacons[side], goals[side] = bit, goal
                            variant = replace(world, beacons=tuple(beacons), goals=tuple(goals))
                            flags = tuple(k == side and changed for k in range(2))
                            content = round_prompts(ep, variant, round_id, flags)[side]
                            lengths.add(len(chat.turn(tok, "user", content)))
                event_lengths.update(lengths)
                if len(lengths) != 1:
                    errors.append(f"unequal event envelopes: {ep.episode_id}/{round_id}/{side}")
            update = round_prompts(ep, world, round_id, updated_sides(ep, round_id))
            qids = QIDS if round_id in (3, 6) else tuple(q for q in QIDS if q != "transfer_action")
            for side in range(2):
                for qid in qids:
                    q = question(ep, world, side, qid, round_id if round_id in (3, 6) else None)
                    key = (system, private[side], update[side], q.text)
                    if key in seen:
                        continue
                    seen.add(key)
                    messages = [{"role": "system", "content": system},
                                {"role": "user", "content": private[side]},
                                {"role": "assistant", "content": "Working note."},
                                {"role": "user", "content": update[side]},
                                {"role": "assistant", "content": "Working note."}]
                    complete = chat.native_conversation(tok, messages)
                    ending = chat.close(tok)
                    opened = chat.native_conversation(tok, messages + [
                        {"role": "user", "content": q.text}], add_generation_prompt=True)
                    if (complete[-len(ending):] != ending or
                            complete[:-len(ending)] + chat.readout_suffix(tok, q.text) != opened):
                        errors.append(f"native incremental suffix mismatch: {ep.episode_id}/{qid}")
                    rendered = tok.decode(opened, skip_special_tokens=False,
                                          clean_up_tokenization_spaces=False)
                    if chat.encode(tok, rendered) != opened:
                        errors.append("native answer prefix does not round-trip")
                    for label, token_id in zip(LABELS, spec.label_ids):
                        if chat.encode(tok, rendered + label) != opened + [token_id]:
                            errors.append(f"answer label does not append as one token: {qid}/{label}")
                    if spec.bos_id is not None and opened.count(spec.bos_id) != 1:
                        errors.append("native prefix does not contain exactly one BOS")
                    prefixes += 1
                    question_lengths.add(len(chat.readout_suffix(tok, q.text)))
            actions = tuple(correct_action(world.goals[k], world.beacons[1 - k]) for k in range(2))
            world = transition(world, actions)
    return {"contract": CONTRACT, "status": "local_tokenizer_audit_not_model_acceptance",
            "profile": profile.key, "episodes": len(rows), "native_answer_prefixes": prefixes,
            "label_append_checks": prefixes * 4, "passed": not errors,
            "errors": sorted(set(errors)), "event_envelope_lengths": sorted(event_lengths),
            "question_suffix_lengths": sorted(question_lengths),
            "materials_sha256": materials_sha256(rows),
            "limits": "Checks rendered native prefixes, not generated-cache continuation, "
            "control-token recovery, hardware execution or task performance."}
