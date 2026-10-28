"""Pure V7 choice scoring shared by the pilot gates, the variance step and the formal analysis.

A choice is the argmax over the four label logits of one rotation; an episode's rate is the
mean over its rotations. Rates are exact fractions, so gate comparisons have no
floating-point edge cases. Callers select records by ``arm_id`` and ``qid`` before calling,
so no other outcome is read.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Iterable, Mapping

from mb import readouts

Record = Mapping[str, object]
CAP_QIDS = ("CAP0", "CAP1")


def episode_rates(records: Iterable[Record], arm_id: str, qid: str, meaning: str) -> dict[str, Fraction]:
    """Per episode: fraction of rotations whose argmax label has ``meaning``."""
    hits: dict[str, dict[object, bool]] = defaultdict(dict)
    for rec in records:
        if rec["arm_id"] != arm_id or rec["qid"] != qid:
            continue
        episode, rotation = str(rec["episode_id"]), rec["rotation_id"]
        if rotation in hits[episode]:
            raise ValueError(f"duplicate {arm_id}/{qid} record for {episode} rotation {rotation}")
        choice = readouts.argmax_meaning(rec)
        if choice is None:
            raise ValueError(f"invalid {arm_id}/{qid} record for {episode} rotation {rotation}")
        hits[episode][rotation] = choice == meaning
    if not hits:
        raise ValueError(f"no {arm_id}/{qid} records")
    if len({len(by_rotation) for by_rotation in hits.values()}) != 1:
        raise ValueError(f"{arm_id}/{qid}: episodes have different numbers of rotations")
    return {ep: Fraction(sum(v.values()), len(v)) for ep, v in hits.items()}


def cap_rates(records: Iterable[Record], arm_id: str) -> dict[str, Fraction]:
    """Per episode: CAP accuracy pooled over CAP0 and CAP1 and their rotations."""
    records = list(records)
    parts = [episode_rates(records, arm_id, qid, "correct") for qid in CAP_QIDS]
    if set(parts[0]) != set(parts[1]):
        raise ValueError(f"{arm_id}: CAP0 and CAP1 cover different episodes")
    return {ep: (parts[0][ep] + parts[1][ep]) / 2 for ep in parts[0]}


def paired_differences(a: Mapping[str, Fraction], b: Mapping[str, Fraction]) -> dict[str, Fraction]:
    """Per episode a − b; both sides must cover exactly the same episodes."""
    if set(a) != set(b):
        raise ValueError("paired contrast over different episode sets")
    return {ep: a[ep] - b[ep] for ep in a}


def mean(values: Mapping[str, Fraction]) -> Fraction:
    if not values:
        raise ValueError("mean of no episodes")
    return sum(values.values(), Fraction(0)) / len(values)
