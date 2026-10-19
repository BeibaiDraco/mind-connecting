"""Isolated task-clarity diagnostics; no model loader or scientific dispatch.

The old task/world is reused unchanged. Prompt variants are prospective research
candidates, and synthetic collection cannot establish model performance.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from itertools import permutations
import random
from typing import Any, Callable

from mb import v6_tasks as tasks
from mb.v6_contract import Backend, Probe, canonical_digest

CONTRACT = "v6-task-clarity-local-20261019-v1"
VARIANTS = ("P0", "P1", "P2")
QIDS = ("latest_goal", "fullinfo_action", "repeated_table_action", "action")
SEED = 20261019
CLARIFICATION = (
    "An assigned goal such as G0 is a policy label, not a destination or a beacon state. "
    "To choose a button, use your own latest assigned label and the OTHER participant's "
    "current beacon in the Action table. Your OWN current beacon is not the row selector. "
    "The Own-device transition table describes what happens AFTER you press the button; "
    "do not reverse it to decide which button to press.")


def _variant(value: str) -> None:
    if value not in VARIANTS:
        raise ValueError("Unknown task-clarity variant")


def action_table(ep: tasks.Episode, variant: str) -> str:
    _variant(variant)
    if variant != "P2":
        system, _ = tasks.initial_prompts(ep)
        return system.split("Action table:\n", 1)[1].split(
            "\nOwn-device transition table:\n", 1)[0]
    return "\n".join(
        f"{ep.goal_names[g]}: if the OTHER participant's current beacon is Dim, "
        f"press {ep.action_names[tasks.correct_action(g, 0)]}; if it is Bright, "
        f"press {ep.action_names[tasks.correct_action(g, 1)]}."
        for g in range(4))


def initial_prompts(ep: tasks.Episode, variant: str) -> tuple[str, tuple[str, str]]:
    _variant(variant)
    system, private = tasks.initial_prompts(ep)
    if variant == "P0":
        return system, private
    before, rest = system.split("Action table:\n", 1)
    _, after = rest.split("\nOwn-device transition table:\n", 1)
    return (before + CLARIFICATION + "\nAction table:\n" + action_table(ep, variant)
            + "\nOwn-device transition table:\n" + after), private


def question(ep: tasks.Episode, world: tasks.World, side: int, variant: str,
             qid: str = "action") -> tasks.Question:
    _variant(variant)
    if qid not in QIDS:
        raise ValueError("Unknown task-clarity diagnostic")
    if qid == "latest_goal":
        return tasks.question(ep, world, side, "latest_goal")
    q = tasks.question(ep, world, side, "action")
    own, other = tasks.ROLES[side], tasks.ROLES[1-side]
    if variant != "P0":
        _, options = q.text.split("\n", 1)
        q = replace(q, text=f"Using participant {own}'s own latest assigned goal and "
                    f"participant {other}'s CURRENT beacon, which button does the Action "
                    f"table prescribe for participant {own}?\n" + options)
    if qid != "action":
        prefix = (f"Current authorized record: participant {own}'s latest goal is "
                  f"{ep.goal_names[world.goals[side]]}; participant {other}'s current "
                  f"beacon is {tasks.BEACON_NAMES[world.beacons[1-side]]}.\n")
        if qid == "repeated_table_action":
            prefix += "Action table (unchanged rules):\n" + action_table(ep, variant) + "\n"
        q = replace(q, text=prefix + q.text)
    return q


def _episode(index: int, stage: str, rng: random.Random, actions: tuple[str, ...],
             goals: tuple[str, ...], options: tuple[int, ...], *,
             beacons: tuple[int, int], assigned: tuple[int, int], focal: int) -> tasks.Episode:
    base = tasks.make_episodes(1, stage=stage, seed=SEED + index)[0]
    early = rng.choice(sorted(set(range(4)) - set(assigned)))
    late = rng.choice(sorted(set(range(4)) - {assigned[focal], early}))
    probes = (rng.choice(sorted(set(range(4)) - {assigned[focal], early})),
              rng.choice(sorted(set(range(4)) - {early, late})))
    return replace(base, initial_beacons=beacons, original_goals=assigned,
                   early_side=focal, updated_goals=(early, late), probe_goals=probes,
                   action_names=actions, goal_names=goals,
                   option_orders=(options, *base.option_orders[1:]))


@dataclass(frozen=True)
class ShortCase:
    book: int
    side: int
    episode: tasks.Episode

    def __post_init__(self) -> None:
        if type(self.book) is not int or not 0 <= self.book < 8 or self.side not in (0, 1):
            raise ValueError("Invalid short-case allocation")

    @property
    def world(self) -> tasks.World:
        return tasks.event_world(self.episode, tasks.initial_world(self.episode), 1)


def make_short_cases() -> tuple[ShortCase, ...]:
    """Eight codebooks, each covering all four labels and both partner beacons."""
    rng = random.Random(canonical_digest([CONTRACT, SEED, "short"]))
    action_books = rng.sample(list(permutations(tasks.ACTION_NAMES)), 8)
    goal_books = rng.sample(list(permutations(tasks.GOAL_NAMES)), 8)
    option_books = rng.sample(list(permutations(range(4))), 8)
    cases = []
    for book in range(8):
        side, match = book % 2, (book // 2) % 2
        for goal in range(4):
            for partner in range(2):
                beacons = [partner, partner]
                beacons[side] = partner if match else 1-partner
                assigned = [(goal+1) % 4] * 2
                assigned[side] = goal
                index = book*8 + goal*2 + partner
                ep = _episode(index, "v6_clarity_short_20261019", rng,
                    action_books[book], goal_books[book], option_books[book],
                    beacons=tuple(beacons), assigned=tuple(assigned), focal=side)
                cases.append(ShortCase(book, side, ep))
    return tuple(cases)


def make_history_episodes() -> tuple[tasks.Episode, ...]:
    """Fresh eight-pair allocation: each focal side sees every initial beacon pair."""
    rng = random.Random(canonical_digest([CONTRACT, SEED, "history"]))
    action_books = rng.sample(list(permutations(tasks.ACTION_NAMES)), 8)
    goal_book = tuple(rng.sample(tasks.GOAL_NAMES, 4))
    option_books = rng.sample(list(permutations(range(4))), 8)
    return tuple(_episode(i, "v6_clarity_history_20261019", rng,
        action_books[i], goal_book, option_books[i], beacons=((i % 4)//2, i % 2),
        assigned=(i % 4, (i+1+i//4) % 4), focal=i//4) for i in range(8))


def _identity(backend: Backend, backend_label: str) -> dict:
    if backend_label not in ("reference", "optimized"):
        raise ValueError("Declare reference or optimized backend")
    synthetic = getattr(backend, "kind", None) == "synthetic_fixture"
    model = getattr(backend, "model_identity", None)
    if not synthetic:
        if getattr(getattr(backend, "tokens", None), "profile_key", None) != "qwen3_4b_instruct_2507":
            raise ValueError("Task-clarity hardware diagnostics are Qwen-only")
        if not isinstance(model, str) or not model:
            raise ValueError("Missing actual backend identity")
    return {"backend": backend_label, "model_identity": model, "synthetic": synthetic,
            "scientific_data": False, "scientific_admission": False}


def _read(backend: Backend, state: Any, ep: tasks.Episode, world: tasks.World,
          side: int, variant: str, qid: str, identity: dict, stage: str) -> tuple[Probe, dict]:
    q = question(ep, world, side, variant, qid)
    before = backend.digest(state)
    p = backend.probe(state, q.text, tasks.LABELS, (), 0.0)
    p.validate()
    if backend.digest(state) != before:
        raise RuntimeError("Diagnostic query changed its continuing parent")
    choice = q.candidates[p.token_ids.index(p.token)] if p.token in p.token_ids else None
    row = {"contract": CONTRACT, "stage": stage, "episode_id": ep.episode_id,
        "variant": variant, "side": side, "round_id": world.round_id, "qid": qid,
        "world": asdict(world), "material_sha256": canonical_digest(tasks.episode_to_dict(ep)),
        "question": q.text, "candidate_map": list(q.candidates), "choice": choice,
        "correct_choice": q.correct, "correct": choice == q.correct, "status": "ok",
        "top_token": p.token, "token_ids": list(p.token_ids), "legal_logits": list(p.legal_logits),
        "legal_mass": p.legal_mass, "top_probability": p.probability, **identity}
    return p, row


def collect_short(backend: Backend, variant: str, backend_label: str, *,
                  sink: Callable[[dict], None] | None = None) -> list[dict]:
    """No loading/rental/retry: caller must bind hardware authority and persistence."""
    _variant(variant)
    identity = _identity(backend, backend_label)
    if not identity["synthetic"] and sink is None:
        raise ValueError("Real diagnostics require a persistent record sink")
    rows = []
    for case in make_short_cases():
        ep = case.episode
        system, users = initial_prompts(ep, variant)
        state = backend.create(system, users[case.side])
        # No generated preparation/work tokens. Probe closes the empty assistant
        # turn before the question, identically in both native implementations.
        _, row = _read(backend, state, ep, case.world, case.side, variant,
                       "fullinfo_action", identity, "short")
        row["book"] = case.book
        rows.append(row)
        if sink is not None:
            sink(deepcopy(row))
    return rows


def _tokens(state: Any, synthetic: bool) -> Any:
    if synthetic:
        return deepcopy(state["history"])
    tokens = getattr(state, "consumed_tokens", None)
    if not isinstance(tokens, tuple) or any(type(t) is not int for t in tokens):
        raise ValueError("Native history tokens unavailable")
    return list(tokens)


def collect_history(backend: Backend, ep: tasks.Episode, variant: str, backend_label: str, *,
                    sink: Callable[[dict], None] | None = None,
                    history_sink: Callable[[dict], None] | None = None) -> list[dict]:
    """OFF-only six-round diagnostic; supplied facts exist only on discarded clones."""
    _variant(variant)
    if ep not in make_history_episodes():
        raise ValueError("Use an independently allocated history diagnostic episode")
    identity = _identity(backend, backend_label)
    if not identity["synthetic"] and (sink is None or history_sink is None):
        raise ValueError("Real diagnostics require record and token-history sinks")
    system, users = initial_prompts(ep, variant)
    states = [backend.create(system, user) for user in users]
    for state in states:
        for _ in range(16):
            backend.step(state, (), 0.0)
        backend.finish_turn(state)
    world, rows = tasks.initial_world(ep), []
    for r in range(1, 7):
        world = tasks.event_world(ep, world, r)
        for state, prompt in zip(states, tasks.round_prompts(ep, world, r, tasks.updated_sides(ep, r))):
            backend.begin_user(state, prompt)
        exports = [[], []]
        for _ in range(64):
            for side in (0, 1):
                exports[side].append(backend.step(states[side], (), 0.0))
        if history_sink is not None:
            history_sink({"episode_id": ep.episode_id, "variant": variant, "round_id": r,
                "world": asdict(world), "before_actions": [_tokens(s, identity["synthetic"]) for s in states],
                "work_tokens": [[e.token for e in part] for part in exports],
                "tail16_text": [backend.decode(tuple(part[-16:])) for part in exports], **identity})
        actual = []
        for qid in QIDS:
            for side in (0, 1):
                p, row = _read(backend, states[side], ep, world, side, variant, qid, identity, "history")
                rows.append(row)
                if sink is not None:
                    sink(deepcopy(row))
                if qid == "action":
                    actual.append((p, row["choice"]))
        # Seal both real choices before publishing either action-driven world.
        states = [backend.commit_answer(p, (), 0.0) for p, _ in actual]
        world = tasks.transition(world, tuple(c for _, c in actual))
    if history_sink is not None:
        history_sink({"episode_id": ep.episode_id, "variant": variant, "round_id": 6,
            "world": asdict(world), "after_final_actions": [_tokens(s, identity["synthetic"]) for s in states],
            **identity})
    return rows


def validate_short(rows: list[dict], variant: str, backend_label: str) -> dict:
    """Complete data integrity only; no prompt selection or numerical admission."""
    _variant(variant)
    cases = {c.episode.episode_id: c for c in make_short_cases()}
    if len(rows) != 64 or len({r["episode_id"] for r in rows}) != 64:
        raise ValueError("Short diagnostics require exactly 64 distinct cases")
    totals: Counter = Counter()
    by_book = {i: [0, 0] for i in range(8)}
    for row in rows:
        c = cases[row["episode_id"]]
        q = question(c.episode, c.world, c.side, variant, "fullinfo_action")
        if any((row["variant"] != variant, row["backend"] != backend_label,
                row["contract"] != CONTRACT, row["stage"] != "short", row["status"] != "ok",
                row["side"] != c.side, row["round_id"] != 1, row["qid"] != "fullinfo_action",
                row["book"] != c.book, row["question"] != q.text,
                canonical_digest(row["world"]) != canonical_digest(asdict(c.world)),
                row["material_sha256"] != canonical_digest(tasks.episode_to_dict(c.episode)),
                row["candidate_map"] != list(q.candidates), row["correct_choice"] != q.correct,
                row["scientific_data"] is not False, row["scientific_admission"] is not False)):
            raise ValueError("Short diagnostic identity/question mismatch")
        ids = tuple(row["token_ids"])
        Probe(None, row["top_token"], row["top_probability"], tuple(row["legal_logits"]),
              row["legal_mass"], ids).validate()
        choice = q.candidates[ids.index(row["top_token"])] if row["top_token"] in ids else None
        if row["choice"] != choice or row["correct"] != (choice == q.correct):
            raise ValueError("Short native-token scoring mismatch")
        by_book[c.book][0] += row["correct"]
        by_book[c.book][1] += 1
        totals["correct"] += row["correct"]
        totals["invalid"] += choice is None
    if len({(r["model_identity"], r["synthetic"]) for r in rows}) != 1:
        raise ValueError("Mixed backend identities")
    return {"complete": True, "cases": 64, "codebooks": 8, **totals, "by_book": by_book,
            "synthetic": rows[0]["synthetic"], "scientific_admission": False,
            "automatic_continuation": False}


def validate_history(rows: list[dict], ep: tasks.Episode, variant: str, backend_label: str) -> dict:
    """Reconstruct this episode from its actual actions, never oracle continuations."""
    _variant(variant)
    if ep not in make_history_episodes() or len(rows) != 48:
        raise ValueError("History diagnostic requires its exact episode and 48 records")
    index = {(r["round_id"], r["side"], r["qid"]): r for r in rows}
    expected = {(r, s, q) for r in range(1, 7) for s in (0, 1) for q in QIDS}
    if set(index) != expected or len(index) != len(rows):
        raise ValueError("Missing or duplicate history diagnostic")
    if len({(r["model_identity"], r["synthetic"]) for r in rows}) != 1:
        raise ValueError("Mixed backend identities")
    world = tasks.initial_world(ep)
    counts = {q: [0, 0] for q in QIDS}
    for r in range(1, 7):
        world = tasks.event_world(ep, world, r)
        for side in (0, 1):
            for qid in QIDS:
                row = index[r, side, qid]
                q = question(ep, world, side, variant, qid)
                if any((row["contract"] != CONTRACT, row["stage"] != "history",
                        row["episode_id"] != ep.episode_id, row["variant"] != variant,
                        row["backend"] != backend_label, row["status"] != "ok",
                        row["material_sha256"] != canonical_digest(tasks.episode_to_dict(ep)),
                        canonical_digest(row["world"]) != canonical_digest(asdict(world)),
                        row["question"] != q.text, row["candidate_map"] != list(q.candidates),
                        row["correct_choice"] != q.correct, row["scientific_data"] is not False,
                        row["scientific_admission"] is not False)):
                    raise ValueError("History diagnostic identity/question/world mismatch")
                ids = tuple(row["token_ids"])
                Probe(None, row["top_token"], row["top_probability"], tuple(row["legal_logits"]),
                      row["legal_mass"], ids).validate()
                choice = q.candidates[ids.index(row["top_token"])] if row["top_token"] in ids else None
                if row["choice"] != choice or row["correct"] != (choice == q.correct):
                    raise ValueError("History native-token scoring mismatch")
                counts[qid][0] += row["correct"]
                counts[qid][1] += 1
        world = tasks.transition(world, tuple(index[r, s, "action"]["choice"] for s in (0, 1)))
    return {"complete": True, "episodes": 1, "counts": counts,
            "synthetic": rows[0]["synthetic"], "scientific_admission": False,
            "automatic_continuation": False}
