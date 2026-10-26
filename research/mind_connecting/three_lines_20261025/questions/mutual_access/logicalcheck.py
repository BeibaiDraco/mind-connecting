"""Finite information-set check; no model or experimental data."""
from itertools import product

World = tuple[int, bool, bool]
worlds: list[World] = [
    (p, delivered, receipt)
    for p, delivered, receipt in product((0, 1), (False, True), (False, True))
    if not receipt or delivered
]


def observation(agent: str, world: World) -> tuple[int | None, bool]:
    p, delivered, receipt = world
    return (p if agent == "B" or delivered else None, receipt)


def knows(agent: str, world: World, proposition) -> bool:
    return all(
        proposition(other)
        for other in worlds
        if observation(agent, other) == observation(agent, world)
    )


for p in (0, 1):
    private = (p, True, False)
    public = (p, True, True)
    a_knows_p = lambda w: knows("A", w, lambda x: x[0] == p)
    assert a_knows_p(private) and a_knows_p(public)
    assert knows("B", private, lambda w: w[0] == p)
    assert knows("B", public, lambda w: w[0] == p)
    assert not knows("B", private, a_knows_p)
    assert knows("B", public, a_knows_p)
    assert knows("A", private, lambda w: not knows("B", w, a_knows_p))

private_launch = 0.5 * 2 + 0.5 * -4
public_launch = 2
assert private_launch < 0 < public_launch
assert public_launch - 0.25 > 0
print("PASS: equal first-order knowledge, different warranted second-order knowledge.")
print("Expected launch utility: private=-1; acknowledged=2; wait=0.")
print("Synthetic logical result only; no model/task/channel validation.")
