"""V7 variance-only step (protocol V7 §7 step 4).

Outputs only the paired standard deviations of the two co-primary episode differences and
what they imply for precision: the 95% half-width at the planned N and the N that gives a
5-point half-width. It prints no means, differences or intervals.

- P1: START partner-choice rate, trans_w2 minus orig_w2.
- D_use: tracking rate T_TRANS minus T_ORIG, where T pools the shown-N arm (choose 2N)
  and its counterfactual arm (choose 2N') with equal weight.

It runs only after the parameter seal: the tag ``protocol-v7-params`` must exist and this
script and ``src/mb/v7_scores.py`` must be byte-identical to their sealed versions. The
pilot must be complete and consumable, with all gates passed. The output file is written
once.

    python scripts/v7_variance.py RUN_DIR OUT_JSON
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping

from mb import ledger, run, v7_run
from mb import v7_scores as scores

SEAL_TAG = "protocol-v7-params"
SEALED_FILES = ("scripts/v7_variance.py", "src/mb/v7_scores.py")
Z95 = 1.959963984540054
HALF_WIDTH = 0.05
PLANNED_N = 600
P1_ARMS = ("orig_w2", "trans_w2")
USE_ARMS = {"orig": ("orig_w2", "orig_w2_cf"), "trans": ("trans_w2", "trans_w2_cf")}


def p1_differences(records: Iterable[Mapping[str, Any]]) -> dict[str, Fraction]:
    start = [r for r in records if r["qid"] == "START" and r["arm_id"] in P1_ARMS]
    orig, trans = (scores.episode_rates(start, arm, "START", "partner") for arm in P1_ARMS)
    return scores.paired_differences(trans, orig)


def d_use_differences(records: Iterable[Mapping[str, Any]]) -> dict[str, Fraction]:
    wanted = {arm for pair in USE_ARMS.values() for arm in pair}
    use = [r for r in records if r["qid"] == "USE" and r["arm_id"] in wanted]

    def tracking(placement: str) -> dict[str, Fraction]:
        shown, counterfactual = USE_ARMS[placement]
        fact = scores.episode_rates(use, shown, "USE", "fact")
        cf = scores.episode_rates(use, counterfactual, "USE", "cf")
        if set(fact) != set(cf):
            raise ValueError(f"{placement}: shown and counterfactual arms cover different episodes")
        return {ep: (fact[ep] + cf[ep]) / 2 for ep in fact}

    return scores.paired_differences(tracking("trans"), tracking("orig"))


def precision(differences: Mapping[str, Fraction]) -> dict[str, float | int]:
    if len(differences) < 2:
        raise ValueError("a paired SD needs at least two episodes")
    sd = statistics.stdev(float(d) for d in differences.values())
    return {"paired_sd": sd,
            "half_width_points_at_planned_n": 100 * Z95 * sd / math.sqrt(PLANNED_N),
            "n_for_5_point_half_width": math.ceil((Z95 * sd / HALF_WIDTH) ** 2)}


def summarize(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    records = list(records)
    p1, d_use = p1_differences(records), d_use_differences(records)
    if set(p1) != set(d_use):
        raise ValueError("P1 and D_use cover different episodes")
    return {"n_episodes": len(p1), "planned_n": PLANNED_N, "P1": precision(p1), "D_use": precision(d_use)}


def require_seal(repo: Path = run.REPO_ROOT) -> str:
    """Return the sealed commit; refuse if the tag is missing or a sealed file changed."""
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--verify", f"refs/tags/{SEAL_TAG}^{{commit}}"],
                                         cwd=repo, stderr=subprocess.DEVNULL, text=True).strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"the variance step runs only after the parameter seal (tag {SEAL_TAG})") from exc
    for name in SEALED_FILES:
        sealed = subprocess.check_output(["git", "show", f"{SEAL_TAG}:{name}"], cwd=repo)
        if sealed != (repo / name).read_bytes():
            raise SystemExit(f"{name} differs from its sealed version")
    return commit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    sealed_commit = require_seal()
    root = args.run_dir
    gates = run._read_json(root / "v7_pilot_gates.json")
    if not (gates.get("consumable") and gates.get("all_pass")):
        raise SystemExit("the variance step needs a consumable pilot whose gates all passed")
    comp = v7_run.run_completeness(root)
    if comp["status"] != "complete" or comp["smoke"]:
        raise SystemExit("the variance step needs a complete, non-smoke pilot")
    arm_hash = run._read_json(root / "arm_hashes.json")
    ok = [r for r in ledger.load_records(root).records
          if r.get("status") == "ok" and r.get("config_hash") == arm_hash.get(r["arm"])]
    out = {"run_dir": str(root), "sealed_commit": sealed_commit, **summarize(ok)}
    with args.out.open("x") as stream:
        json.dump(out, stream, indent=2)
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
