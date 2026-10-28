"""Post hoc check of exchange symmetry at equal weight (exploratory, read-only).

If the receiver's computation depended only on the union of the two prefill banks, then for
every ordered rule pair the claim rate with (own=X, partner=Y) plus the rate with (own=Y,
partner=X) would equal 1. A home advantage makes the sum fall below 1. Episode is the unit:
answers are averaged over option rotations within an episode before anything else.

Usage: python scripts/explore_symmetry_check.py RUN_DIR ARM [QID]
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


def episode_claims(run_dir: Path, arm: str, qid: str) -> dict[str, tuple[str, str, float]]:
    per_ep: dict[str, list] = defaultdict(list)
    for shard in sorted((run_dir / "records").glob("attempt-*.jsonl")):
        if shard.name.startswith("._"):
            continue
        for line in shard.open():
            r = json.loads(line)
            if r["status"] != "ok" or r["arm"] != arm or r["qid"] != qid or r["recipient"] != "A":
                continue
            meaning = r["label_meaning"]
            own = r["options"][meaning.index("own")]
            partner = r["options"][meaning.index("partner")]
            choice = meaning[int(np.argmax(r["label_logits"]))]
            per_ep[r["episode_id"]].append((own, partner, choice == "partner"))
    out = {}
    for ep, rows in per_ep.items():
        own, partner = rows[0][0], rows[0][1]
        out[ep] = (own, partner, float(np.mean([c for _, _, c in rows])))
    return out


def pair_sums(claims: dict[str, tuple[str, str, float]]) -> tuple[dict, float]:
    by_pair: dict[tuple[str, str], list[float]] = defaultdict(list)
    for own, partner, c in claims.values():
        by_pair[(own, partner)].append(c)
    sums = {}
    for (x, y), v in by_pair.items():
        if x < y and (y, x) in by_pair:
            sums[(x, y)] = (np.mean(v), np.mean(by_pair[(y, x)]), len(v), len(by_pair[(y, x)]))
    total = float(np.mean([a + b for a, b, _, _ in sums.values()]))
    return sums, total


def bootstrap_total(claims: dict, n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    keys = list(claims)
    rng = random.Random(seed)
    stats = []
    for _ in range(n_boot):
        sample = {f"{k}#{i}": claims[k] for i, k in enumerate(rng.choice(keys) for _ in keys)}
        stats.append(pair_sums(sample)[1])
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def main() -> None:
    run_dir, arm = Path(sys.argv[1]), sys.argv[2]
    qid = sys.argv[3] if len(sys.argv) > 3 else "START"
    claims = episode_claims(run_dir, arm, qid)
    sums, total = pair_sums(claims)
    lo, hi = bootstrap_total(claims)
    print(f"{run_dir.name} | {arm} | {qid} | episodes {len(claims)} | mean claim "
          f"{np.mean([c for *_, c in claims.values()]):.3f}")
    for (x, y), (a, b, na, nb) in sorted(sums.items()):
        print(f"  {x:>11}/{y:<11} claim(own={x}) {a:.2f} (n={na})  claim(own={y}) {b:.2f} (n={nb})  sum {a + b:.2f}")
    print(f"  mean pair sum {total:.3f}  [95% episode bootstrap {lo:.3f}, {hi:.3f}]  (1 = symmetric, <1 = home advantage)")


if __name__ == "__main__":
    main()
