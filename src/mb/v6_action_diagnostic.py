"""Exploratory interventions on exposed short cases, without model dispatch."""
from __future__ import annotations

from dataclasses import dataclass

from mb import v6_task_clarity as clarity, v6_tasks as tasks

ARMS = ("joint_p2", "rule_pair", "oracle_pair", "oracle_button", "compact_joint")
WORK_ARMS = ("minimal_oracle_pair", "facts_first_nowork", "facts_first_work64")


@dataclass(frozen=True)
class Item:
    case_id: str
    arm: str
    system: str
    private: str
    question: str
    candidates: tuple[int, ...]
    correct: int


def make_item(case: clarity.ShortCase, arm: str) -> Item:
    if arm not in ARMS:
        raise ValueError("Unknown diagnostic arm")
    ep, w, side = case.episode, case.world, case.side
    system, users = clarity.initial_prompts(ep, "P2")
    q = clarity.question(ep, w, side, "P2", "fullinfo_action")
    goal = w.goals[side]
    pair = tuple(ep.action_names[tasks.correct_action(goal, b)] for b in (0, 1))
    correct, order, question = q.correct, q.candidates, q.text
    if arm == "rule_pair":
        correct = goal
        options = "\n".join(
            f"{label}. Dim: {ep.action_names[tasks.correct_action(g, 0)]}; "
            f"Bright: {ep.action_names[tasks.correct_action(g, 1)]}"
            for label, g in zip(tasks.LABELS, order))
        question = (f"Participant {tasks.ROLES[side]}'s latest assigned goal is "
            f"{ep.goal_names[goal]}. Which pair of buttons is specified by that "
            "goal's Action rule, in the order (partner Dim, partner Bright)? "
            "Select the pair; do not apply the device transition.\n"
            + options + "\n" + tasks.ANSWER_LINE)
    elif arm == "oracle_pair":
        question = (f"The correct rule has already been retrieved for your assignment: "
            f"if the OTHER beacon is Dim, press {pair[0]}; if it is Bright, press "
            f"{pair[1]}. Apply this rule.\n" + q.text)
    elif arm == "oracle_button":
        question = (f"The prescribed button has already been computed: "
            f"{ep.action_names[q.correct]}. Only select the choice ID that names "
            "this button; no rule lookup or transition calculation is needed.\n"
            + q.text.split("\n", 2)[-1])
    elif arm == "compact_joint":
        system = ("Use the assigned goal and the OTHER participant's beacon to "
            "look up a button. Answer with exactly one choice ID.\nAction rules:\n"
            + clarity.action_table(ep, "P2"))
    return Item(ep.episode_id, arm, system, users[side], question, order, correct)


def materials() -> tuple[Item, ...]:
    return tuple(make_item(case, arm) for arm in ARMS for case in clarity.make_short_cases())


def score(item: Item, token: int, legal_ids: tuple[int, ...]) -> dict:
    if len(legal_ids) != 4 or len(set(legal_ids)) != 4:
        raise ValueError("Four distinct answer IDs required")
    choice = item.candidates[legal_ids.index(token)] if token in legal_ids else None
    return {"choice": choice, "correct": choice == item.correct, "invalid": choice is None}


def work_item(case: clarity.ShortCase, arm: str) -> tuple[Item, int]:
    """Manually specified follow-up; no result-dependent dispatch or selection."""
    if arm not in WORK_ARMS:
        raise ValueError("Unknown work diagnostic arm")
    ep, w, side = case.episode, case.world, case.side
    x = make_item(case, "joint_p2")
    system, private, question = x.system, x.private, x.question
    if arm == "minimal_oracle_pair":
        goal = w.goals[side]
        pair = [ep.action_names[tasks.correct_action(goal, b)] for b in (0, 1)]
        system = "Apply the supplied rule. Answer with exactly one choice ID."
        private = (f"If the signal is Dim, press {pair[0]}. "
                   f"If the signal is Bright, press {pair[1]}. "
                   f"The signal is {tasks.BEACON_NAMES[w.beacons[1-side]]}.")
        question = ("Which button does the supplied rule require?\n"
                    + x.question.split("\n", 2)[-1])
    else:
        private += ("\n" + x.question.split("\n", 1)[0]
            + "\nWork through the decision: identify your assigned goal, retrieve "
            "its Dim/Bright rule, use the OTHER beacon, then identify the button. "
            "The own-device transition happens only after that decision.")
    return (Item(x.case_id, arm, system, private, question, x.candidates, x.correct),
            64 if arm == "facts_first_work64" else 0)


def work_materials() -> tuple[tuple[Item, int], ...]:
    return tuple(work_item(case, arm) for arm in WORK_ARMS for case in clarity.make_short_cases())
