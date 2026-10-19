"""Fixed fresh diagnostic material; no gate, selector or model dispatcher."""
from itertools import permutations
import random

from mb import v6_action_diagnostic as diagnostic, v6_task_clarity as clarity
from mb import v6_tasks as tasks


def cases() -> tuple[clarity.ShortCase, ...]:
    rng = random.Random(202610190032)
    old = clarity.make_short_cases()
    def draw(values: tuple, attribute: str) -> list:
        used = {getattr(x.episode, attribute) for x in old}
        if attribute == "option_orders":
            used = {x.episode.option_orders[0] for x in old}
        return rng.sample([p for p in permutations(values) if p not in used], 4)
    actions = draw(tasks.ACTION_NAMES, "action_names")
    goals = draw(tasks.GOAL_NAMES, "goal_names")
    options = draw(tuple(range(4)), "option_orders")
    out = []
    for book in range(4):
        side, match = book % 2, book // 2
        for goal in range(4):
            for partner in range(2):
                beacons = [partner, partner]
                beacons[side] = partner if match else 1-partner
                assigned = [(goal+1) % 4] * 2
                assigned[side] = goal
                ep = clarity._episode(book*8+goal*2+partner,
                    "v6_action_work_holdout_20261019", rng,
                    actions[book], goals[book], options[book],
                    beacons=tuple(beacons), assigned=tuple(assigned), focal=side)
                out.append(clarity.ShortCase(book, side, ep))
    return tuple(out)


def work_materials() -> tuple[tuple[diagnostic.Item, int], ...]:
    return tuple(diagnostic.work_item(case, arm)
                 for arm in ("facts_first_nowork", "facts_first_work64")
                 for case in cases())


score = diagnostic.score
