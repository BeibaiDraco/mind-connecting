"""Independent finite counterexample: receipt handling needs no perspective model."""

from pathlib import Path
import runpy


source = Path(__file__).resolve().parents[1] / "questions/mutual_access/logicalcheck.py"
checked = runpy.run_path(str(source))
worlds = checked["worlds"]
observation = checked["observation"]
knows = checked["knows"]


def direct_ack(local: tuple[int | None, bool]) -> bool:
    """Use only observed content presence and a visible receipt."""
    content, receipt = local
    return content is not None and not receipt


def perspective_ack(world: tuple[int, bool, bool]) -> bool:
    p, delivered, _ = world
    a_knows = lambda w: knows("A", w, lambda x: x[0] == p)
    return delivered and not knows("B", world, a_knows)


for world in worlds:
    assert direct_ack(observation("A", world)) == perspective_ack(world)

# If failed delivery is not a possible world, B knows A received without a receipt.
success_only = [w for w in worlds if w[1]]
for world in success_only:
    indistinguishable = [
        w for w in success_only if observation("B", w) == observation("B", world)
    ]
    assert all(w[1] for w in indistinguishable)

# Knowledge uncertainty alone does not select the utility-optimal action.
assert 0.5 * 2 + (1 - 0.5) * -4 < 0
assert 0.9 * 2 + (1 - 0.9) * -4 > 0

print("PASS: direct local lookup equals the perspective policy in all six worlds.")
print("PASS: removing failure worlds removes the no-receipt uncertainty.")
print("PASS: a different delivery prior changes launch preference without certainty.")
print("Scope: logic and conditional policy only; no model behavior or task validation.")
