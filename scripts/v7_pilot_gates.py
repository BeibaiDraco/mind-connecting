"""V7 pilot gates U1–U3 and Q1 (protocol V7 §7 step 2).

Reads only three things: USE in the four arms the gates name (c0, c0_fullinfo, orig_w2,
orig_w2_cf), CAP0/CAP1 in every arm, and the label mass of closed questions. No ownership,
detection or report outcome is read, and USE is not read in any translated arm. The gates
check that the instrument works; they say nothing about the results.

Q1's CAP part follows the v2–v5 screen: the paired drop from C0 (C0 minus arm) is at most
5 points. Label mass is checked per arm, over all closed questions.

    python scripts/v7_pilot_gates.py RUN_DIR
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping

from mb import ledger, run, v7_run
from mb import v7_scores as scores

U1_MIN = Fraction(9, 10)
U2_MAX = Fraction(2, 5)
U3_MIN = Fraction(1, 4)
CAP_DROP_MAX = Fraction(1, 20)
MASS_MIN = 0.95
C0, FULLINFO, ORIG, ORIG_CF = "c0", "c0_fullinfo", "orig_w2", "orig_w2_cf"
USE_ARMS = (C0, FULLINFO, ORIG, ORIG_CF)
BASE_ARMS = tuple(a.arm_id for a in v7_run.arms_for("base"))
LINKED_ARMS = tuple(a.arm_id for a in v7_run.arms_for("base") if a.condition != "C0")


def _gate(value: Fraction | float, threshold: Fraction | float, passed: bool) -> dict[str, Any]:
    return {"value": float(value), "threshold": float(threshold), "pass": bool(passed)}


def evaluate(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """U1–U3 and Q1 from ok records of one complete base pilot."""
    use, cap, mass = [], [], {arm: [] for arm in BASE_ARMS}
    for rec in records:
        arm, qid = rec["arm_id"], rec["qid"]
        if arm not in mass:
            raise ValueError(f"unregistered base arm {arm}")
        if qid == "U_OPEN":
            continue
        mass[arm].append(float(rec["label_mass"]))
        if qid == "USE" and arm in USE_ARMS:
            use.append(rec)
        elif qid in scores.CAP_QIDS:
            cap.append(rec)
    fact = {arm: scores.episode_rates(use, arm, "USE", "fact") for arm in USE_ARMS}
    cf = {arm: scores.episode_rates(use, arm, "USE", "cf") for arm in (C0, ORIG_CF)}
    u1, u2 = scores.mean(fact[FULLINFO]), scores.mean(fact[C0])
    u3_fact = scores.mean(scores.paired_differences(fact[ORIG], fact[C0]))
    u3_cf = scores.mean(scores.paired_differences(cf[ORIG_CF], cf[C0]))
    cap_by_arm = {arm: scores.cap_rates(cap, arm) for arm in BASE_ARMS}
    drops = {arm: scores.mean(scores.paired_differences(cap_by_arm[C0], cap_by_arm[arm])) for arm in LINKED_ARMS}
    if any(not values for values in mass.values()):
        raise ValueError("an arm has no closed-question records")
    mass_by_arm = {arm: sum(v) / len(v) for arm, v in mass.items()}
    gates = {
        "U1": _gate(u1, U1_MIN, u1 >= U1_MIN),
        "U2": _gate(u2, U2_MAX, u2 <= U2_MAX),
        "U3_fact": _gate(u3_fact, U3_MIN, u3_fact >= U3_MIN),
        "U3_cf": _gate(u3_cf, U3_MIN, u3_cf >= U3_MIN),
        "Q1_cap": {"max_drop": float(max(drops.values())), "threshold": float(CAP_DROP_MAX),
                   "pass": all(d <= CAP_DROP_MAX for d in drops.values())},
        "Q1_mass": {"min_mass": min(mass_by_arm.values()), "threshold": MASS_MIN,
                    "pass": all(m >= MASS_MIN for m in mass_by_arm.values())},
    }
    use_ok = all(gates[g]["pass"] for g in ("U1", "U2", "U3_fact", "U3_cf"))
    quality_ok = gates["Q1_cap"]["pass"] and gates["Q1_mass"]["pass"]
    return {
        "gates": gates, "use_assay_valid": use_ok, "quality_ok": quality_ok, "all_pass": use_ok and quality_ok,
        "n_episodes": len(fact[C0]),
        "use_rates": {"fact": {arm: float(scores.mean(v)) for arm, v in fact.items()},
                      "cf": {arm: float(scores.mean(v)) for arm, v in cf.items()}},
        "cap_by_arm": {arm: float(scores.mean(v)) for arm, v in cap_by_arm.items()},
        "cap_drop_by_arm": {arm: float(d) for arm, d in drops.items()},
        "label_mass_by_arm": mass_by_arm,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)
    root = args.run_dir
    identity = run._read_json(root / "identity.json")
    cfg = v7_run.V7Config(**identity["stage_config"])
    if cfg.variant != "base":
        raise SystemExit("the pilot gates apply to the base variant only")
    comp = v7_run.run_completeness(root)
    out: dict[str, Any] = {"run_dir": str(root), "stage": cfg.stage, "completeness": comp,
                           "smoke": comp["smoke"]}
    if comp["status"] != "complete":
        out.update(result="incomplete", consumable=False)
    else:
        arm_hash = run._read_json(root / "arm_hashes.json")
        ok = [r for r in ledger.load_records(root).records
              if r.get("status") == "ok" and r.get("config_hash") == arm_hash.get(r["arm"])]
        out.update(evaluate(ok), result="evaluated",
                   consumable=not comp["smoke"] and cfg.split == "v7_pilot" and identity["limit"] is None)
    (root / "v7_pilot_gates.json").write_text(json.dumps(out, indent=2))
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
