"""Finite counterexample; no model data or performance claims."""

from itertools import product


def value(u: int, v: int, x: int) -> int:
    return (u * x + v) % 5


def main() -> None:
    worlds = list(product(range(5), repeat=2))
    checked = 0
    for u, v in worlds:
        p, q = value(u, v, 0), value(u, v, 1)
        a_worlds = [(a, b) for a, b in worlds if value(a, b, 0) == p]
        b_worlds = [(a, b) for a, b in worlds if value(a, b, 1) == q]
        assert len(a_worlds) == len(b_worlds) == 5
        for x in (2, 3, 4):
            assert len({value(a, b, x) for a, b in a_worlds}) == 5
            assert len({value(a, b, x) for a, b in b_worlds}) == 5
            stored_rule = value(u, v, x)
            recomputed = ((q - p) * x + p) % 5
            assert stored_rule == recomputed
            checked += 1
    # One prior answer at x=2 still leaves all possible answers at x=3.
    for prior_answer in range(5):
        compatible = [(u, v) for u, v in worlds if value(u, v, 2) == prior_answer]
        assert len({value(u, v, 3) for u, v in compatible}) == 5
    print(f"PASS: {len(worlds)} worlds, {checked} held-out applications.")
    print("Each private observation is insufficient; combined premises identify the rule.")
    print("Fresh accuracy cannot distinguish a stored rule from retained-premise recomputation.")
    print("One saved earlier answer alone is insufficient for the new challenge family.")


if __name__ == "__main__":
    main()
