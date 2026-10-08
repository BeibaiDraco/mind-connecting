"""Torch-free protocol-v4 gates and episode-level analysis.

Pilots expose only access, capability and format. Selection is a separate step
from formal attribution analysis; unavailable hypotheses retain their place in
the prespecified multiplicity family without inventing an effect estimate.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from mb import analyze, ledger, readouts, tasks

ACCESS_QIDS = ("ACC_RULE", "ACC_WORD", "CAP0", "CAP1")
TASK_QIDS = ("START", "START_R", "NOW", "NOW_R", "WORD", "WORD_R")
FORMAL_QIDS = (*TASK_QIDS, *ACCESS_QIDS)
KV_GRID = (0.3, 0.5, 1.0, 2.0, 3.0)
STATIC_GRID = (0.005, 0.01, 0.015, 0.02, 0.03, 0.05, 0.1, 0.15,
               0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0)
PRIMARY = (("K*", "C0", "M"), ("K1", "STATIC", "M"), ("K*", "TAG", "M"),
           ("K*", "RF", "M"), ("UNTAG", "TAG", "M_NOW"))
SECONDARY = (("K*", "C0", "M_NOW"), ("K*", "C0", "M_WORD"),
             ("RF", "C0", "M_NOW"), ("RF", "C0", "M_WORD"))
POST_NAMES = ("v4_baseline", "v4_strength", "v4_match", "v4_validity", "v4_contrasts")
SUMMARY_COLUMNS = {"arm", "condition", "interface", "kv_scope", "layer", "gain", "n",
                   "acc_increment", "acc_word_increment", "cap_drop", "label_mass",
                   "mass_drop", "partner_rate", "partner_rate_c0"}


def _finite(*values: Any) -> bool:
    return all(v is not None and math.isfinite(float(v)) for v in values)


def _selector_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    for row in rows:
        if set(row) - SUMMARY_COLUMNS:
            raise ValueError("v4 selectors accept only access/CAP/format summaries")


def engineering_eligible(row: Mapping[str, Any], expected_n: int | None = None) -> bool:
    """A tiny rounding tolerance protects exact 5-point floating-point boundaries."""
    if not _finite(*(row.get(k) for k in ("cap_drop", "label_mass", "mass_drop", "n"))):
        return False
    return bool(row["n"] > 0 and (expected_n is None or row["n"] == expected_n)
                and row["cap_drop"] <= 0.05 + 1e-12 and row["label_mass"] >= 0.90 - 1e-12
                and row["mass_drop"] <= 0.05 + 1e-12)


def select_strength(rows: Sequence[Mapping[str, Any]], expected_n: int = 40) -> dict:
    """Screen every criterion before ranking; attribution columns are rejected."""
    _selector_rows(rows)
    eligible = []
    checks = []
    for row in rows:
        if row["condition"] != "ONE" or row.get("interface") != "kv" or row.get("kv_scope") != "P":
            continue
        engineering = engineering_eligible(row, expected_n)
        strong = bool(engineering and _finite(row.get("acc_increment"), row.get("partner_rate"),
                                              row.get("partner_rate_c0"))
                      and row["acc_increment"] > 0 and row["partner_rate"] >= 0.30 - 1e-12
                      and row["partner_rate"] - row["partner_rate_c0"] >= 0.10 - 1e-12)
        checks.append({**row, "engineering_eligible": engineering, "strong": strong})
        if strong:
            eligible.append(dict(row))
    selected = min(eligible, key=lambda r: (-r["acc_increment"], r["gain"], r["arm"])) if eligible else None
    return {"gate": "pass" if selected else "fail", "selection": selected, "candidates": checks}


def select_static(rows: Sequence[Mapping[str, Any]], target_arm: str,
                  expected_n: int = 40) -> dict:
    """Nearest engineering-eligible point; nonpositive targets never count as matched."""
    _selector_rows(rows)
    targets = [r for r in rows if r["arm"] == target_arm]
    if len(targets) != 1:
        raise ValueError("STATIC matching requires exactly one fixed K1 target")
    target = targets[0]
    t = target.get("acc_increment")
    candidates = [dict(r) for r in rows if r["condition"] == "STATIC"
                  and engineering_eligible(r, expected_n) and _finite(r.get("acc_increment"), r.get("gain"))]
    if not _finite(t) or target["n"] != expected_n:
        raise ValueError("K1 target is incomplete or non-finite")
    best = min(candidates, key=lambda r: (abs(r["acc_increment"] - t), r["gain"], r["arm"])) if candidates else None
    gap = abs(best["acc_increment"] - t) if best else None
    return {"target": dict(target), "selection": best, "available": best is not None,
            "gap": gap, "matched": bool(best and t > 0 and gap <= 0.25 * t + 1e-12)}


def baseline_gate(records: Sequence[dict], expected_n: int = 60) -> dict:
    """Average orderings within episode; never pool A and B suitability gates."""
    rows = []
    for r in records:
        if r["condition"] != "C0":
            raise ValueError("the baseline gate only accepts C0")
        if not readouts._ok(r) or not _finite(r.get("label_mass")):
            raise ValueError("baseline inputs must contain finite successful readouts")
        correct = "robin" if r["qid"].endswith("_R") else "correct" if r["qid"].startswith("CAP") else "own"
        rows.append({"episode_id": r["episode_id"], "side": r["recipient"], "qid": r["qid"],
                     "rotation": r["rotation_id"], "hit": float(readouts.argmax_meaning(r) == correct),
                     "mass": r.get("label_mass")})
    df = pd.DataFrame(rows)
    sides = {}
    for side in ("A", "B"):
        sub = df[df["side"] == side] if not df.empty else df
        accuracy = {}
        complete = not sub.empty
        for qid in TASK_QIDS:
            q = sub[sub["qid"] == qid] if not sub.empty else sub
            grouped = q.groupby("episode_id")["hit"].mean() if not q.empty else pd.Series(dtype=float)
            accuracy[qid] = float(grouped.mean()) if len(grouped) else None
            complete &= len(grouped) == expected_n
        if not sub.empty:
            counts = sub.groupby(["episode_id", "qid"])["rotation"].nunique()
            complete &= (len(counts) == expected_n * len(FORMAL_QIDS) and bool((counts == 2).all())
                         and not sub.duplicated(["episode_id", "qid", "rotation"]).any())
            caps = sub[sub["qid"].isin(("CAP0", "CAP1"))].groupby("episode_id")["hit"].mean()
            masses = sub.groupby("episode_id")["mass"].mean()
            cap, mass = float(caps.mean()), float(masses.mean())
            complete &= len(caps) == expected_n and len(masses) == expected_n
        else:
            cap, mass = None, None
        passed = bool(complete and _finite(cap, mass, *accuracy.values()) and cap >= 0.90 - 1e-12
                      and mass >= 0.90 - 1e-12 and all(v >= 0.90 - 1e-12 for v in accuracy.values()))
        sides[side] = {"accuracy": accuracy, "CAP_ACC": cap, "LABEL_MASS": mass,
                       "complete": bool(complete), "pass": passed}
    return {"gate": "pass" if all(s["pass"] for s in sides.values()) else "fail", "sides": sides}


def access_table(records: Sequence[dict], expected_n: int) -> list[dict]:
    """Summaries from four access-only questions; no attribution score is exported."""
    subset = [r for r in records if r["recipient"] == "A" and r["qid"] in ACCESS_QIDS]
    scores = readouts.score_records(subset, readouts.ScoreOptions(rotations=None))
    if scores.empty:
        raise ValueError("no access records")
    c0 = scores[scores["condition"] == "C0"]
    if c0["arm"].nunique() != 1:
        raise ValueError("exactly one C0 arm is required")
    base = c0.set_index("episode_id")
    hit_rows = [{"arm": r["arm"], "episode_id": r["episode_id"],
                 "hit": float(readouts.argmax_meaning(r) == "partner")}
                for r in subset if r["qid"] == "ACC_RULE"]
    hits = pd.DataFrame(hit_rows).groupby(["arm", "episode_id"])["hit"].mean()
    meta = {r["arm"]: r for r in subset}
    rows = []
    for arm, group in scores.groupby("arm"):
        j = group.set_index("episode_id").join(base, rsuffix="_c0", how="inner")
        cols = ["ACC_RULE", "ACC_WORD", "CAP_ACC", "LABEL_MASS"]
        if len(j) != expected_n or not np.isfinite(j[cols + [k + "_c0" for k in cols]].to_numpy(dtype=float)).all():
            raise ValueError(f"{arm}: incomplete/non-finite episode access summaries")
        m = meta[arm]
        rows.append({"arm": arm, "condition": m["condition"], "interface": m.get("interface", "residual"),
                     "kv_scope": m.get("kv_scope"), "layer": m["layer"], "gain": float(m["gain"]),
                     "n": len(j), "acc_increment": float((j.ACC_RULE - j.ACC_RULE_c0).mean()),
                     "acc_word_increment": float((j.ACC_WORD - j.ACC_WORD_c0).mean()),
                     "cap_drop": float((j.CAP_ACC_c0 - j.CAP_ACC).mean()),
                     "label_mass": float(j.LABEL_MASS.mean()),
                     "mass_drop": float((j.LABEL_MASS_c0 - j.LABEL_MASS).mean()),
                     "partner_rate": float(hits.loc[arm].mean()),
                     "partner_rate_c0": float(hits.loc[str(c0.arm.iloc[0])].mean())})
    return rows


def _paired(scores: pd.DataFrame, arm1: str | None, arm2: str | None, metric: str) -> np.ndarray:
    if scores.empty or metric not in scores or arm1 is None or arm2 is None:
        return np.array([], dtype=float)
    present = set(scores.arm)
    if arm1 not in present or arm2 not in present:
        return np.array([], dtype=float)
    values = analyze.paired_differences(scores, arm1, arm2, metric).to_numpy(dtype=float)
    return values[np.isfinite(values)]


def _bound(values: Sequence[float], expected_n: int, n_boot: int) -> dict:
    x = np.asarray(values, dtype=float)
    finite = x[np.isfinite(x)]
    lower = analyze.one_sided_lower_bound(finite, n_boot=n_boot)
    return {"n": int(finite.size), "n_missing": expected_n - int(finite.size),
            "mean": float(finite.mean()) if finite.size else None,
            "lb95_one_sided": lower if math.isfinite(lower) else None,
            "pass": bool(finite.size == expected_n and math.isfinite(lower) and lower > 0)}


def content_check(records: Sequence[dict], original: str, cf: str | None,
                  expected_n: int, n_boot: int = 10_000) -> dict:
    a = [r for r in records if r["arm"] == original and r["recipient"] == "A"]
    b = [r for r in records if r["arm"] == cf and r["recipient"] == "A"]
    result = {}
    for kind, qid in (("rule", "ACC_RULE"), ("word", "ACC_WORD")):
        scored = readouts.content_cf_score(a, b, qid)
        vals = scored.C_content.to_numpy(dtype=float) if not scored.empty else []
        result[kind] = _bound(vals, expected_n, n_boot)
    return result


def validity_summary(records: Sequence[dict], roles: Mapping[str, str | None], expected_n: int = 80,
                     n_boot: int = 10_000) -> dict:
    if roles["K1"] != roles["K*"] and not roles.get("CF1"):
        raise ValueError("distinct K1 needs its own independent CF-w1 validity arm")
    table = access_table(records, expected_n)
    by_arm = {row["arm"]: row for row in table}
    engineering = {role: bool(arm in by_arm and engineering_eligible(by_arm[arm], expected_n))
                   for role, arm in roles.items()}
    core = content_check(records, roles["K*"], roles["CF"], expected_n, n_boot)
    k1 = content_check(records, roles["K1"], roles.get("CF1", roles["CF"]), expected_n, n_boot)
    scores = readouts.score_records([r for r in records if r["qid"] in ACCESS_QIDS], readouts.ScoreOptions(rotations=None))
    k1_access = _bound(_paired(scores, roles["K1"], roles["C0"], "ACC_RULE"), expected_n, n_boot)
    target, static = by_arm.get(roles["K1"]), by_arm.get(roles.get("STATIC"))
    gap = abs(target["acc_increment"] - static["acc_increment"]) if target and static else None
    matched = bool(target and static and target["acc_increment"] > 0 and static["acc_increment"] > 0
                   and gap <= 0.25 * target["acc_increment"] + 1e-12)
    route = bool(engineering.get("K1") and engineering.get("STATIC") and k1_access["pass"]
                 and k1["rule"]["pass"] and matched)
    return {"core_gate": "pass" if engineering.get("K*") and core["rule"]["pass"] else "fail",
            "engineering": engineering, "access_table": table, "content_Kstar": core, "content_K1": k1,
            "K1_access": k1_access, "route_validated": route, "matched": matched, "match_gap": gap}


def analyze_families(scores: pd.DataFrame, roles: Mapping[str, str | None], n_boot: int = 10_000) -> dict:
    families = {}
    for name, contrasts in (("primary", PRIMARY), ("secondary", SECONDARY)):
        rows = []
        for role1, role2, metric in contrasts:
            a, b = roles.get(role1), roles.get(role2)
            values = _paired(scores, a, b, metric)
            estimable = len(values) >= 2
            row = {"role1": role1, "role2": role2, "arm1": a, "arm2": b, "metric": metric,
                   "available": estimable, "n": len(values), "mean": None, "sd": None, "se": None,
                   "t": None, "p_two_sided": None, "ci95_lo": None, "ci95_hi": None,
                   "p_for_adjustment": 1.0}
            if estimable:
                t = analyze.paired_t(values)
                lo, hi = analyze.bootstrap_ci(values, n_boot=n_boot)
                row.update(mean=t.mean, sd=t.sd, se=t.se, t=t.t, p_two_sided=t.p_two_sided,
                           ci95_lo=lo, ci95_hi=hi, p_for_adjustment=t.p_two_sided)
            else:
                row["reason"] = "arm unavailable or fewer than two finite paired episodes"
            rows.append(row)
        for row, adjusted in zip(rows, analyze.holm([r["p_for_adjustment"] for r in rows])):
            row["p_holm"] = adjusted
        families[name] = rows
    return families


def descriptive(records: Sequence[dict]) -> dict:
    """Include both Robin-subtracted components and rotation-level choice rates."""
    rows = []
    for r in records:
        if r["recipient"] != "A":
            continue
        row = {"arm": r["arm"], "episode_id": r["episode_id"], "qid": r["qid"],
               "partner_choice": float(readouts.argmax_meaning(r) == "partner"),
               "label_mass": r["label_mass"]}
        if r["qid"] in TASK_QIDS:
            row["partner_minus_correct"] = readouts.log_ratio(r, "partner", "robin" if r["qid"].endswith("_R") else "own")
        rows.append(row)
    if not rows:
        return {}
    df = pd.DataFrame(rows).groupby(["arm", "episode_id", "qid"]).mean(numeric_only=True)
    return {str(arm): group.groupby("qid").mean(numeric_only=True).to_dict(orient="index")
            for arm, group in df.groupby(level="arm")}


def _checked_records(run_dir: Path, cfg: Any, status: Mapping[str, Any]) -> tuple[list[dict], dict]:
    identity = json.loads((run_dir / "identity.json").read_text())
    manifest = json.loads((run_dir / "manifest.json").read_text())
    arm_hash = json.loads((run_dir / "arm_hashes.json").read_text())
    report = ledger.load_records(run_dir)
    episodes = tasks.make_episodes(cfg.n_episodes, cfg.split, cfg.seed)
    arms = cfg.arm_configs()
    if set(arm_hash) != {arm.name for arm in arms} or not all(isinstance(h, str) and h for h in arm_hash.values()):
        raise ValueError("v4 requires a registered nonempty hash for every configured arm")
    expected = ledger.expected_trials([ledger.ArmSpec(a.name, a.recipients) for a in arms],
                                      [(e.episode_id, e.rotations) for e in episodes], cfg.qids, set())
    comp = ledger.completeness(report.records, expected, arm_hash)
    smoke = bool(manifest.get("smoke", True) or identity.get("limit") is not None or cfg.split.endswith("_smoke"))
    consumable = bool(not smoke and status.get("status") == "complete" and comp["status"] == "complete")
    if identity.get("stage_config") != json.loads(json.dumps(cfg.resolved())):
        raise ValueError("post-processing config differs from stored run identity")
    if cfg.all_rotations_first:
        raise ValueError("v4 uses exactly the two balanced episode orderings")
    if ledger.conflicting_hashes(report.records, arm_hash):
        raise ValueError("v4 records contain conflicting arm hashes")
    expected_set = set(expected)
    records = [r for r in report.records if r.get("status") == "ok"
               and r.get("config_hash") == arm_hash.get(r["arm"]) and ledger.trial_key(r) in expected_set]
    keys = [ledger.trial_key(r) for r in records]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate successful v4 records")
    invalid = [ledger.trial_key(r) for r in records if not readouts._ok(r)
               or not _finite(r.get("label_mass")) or not 0 <= r["label_mass"] <= 1 + 1e-6]
    consumable &= not invalid
    return records, {"consumable": bool(consumable), "smoke": smoke, "completeness": comp,
                     "invalid_records": [list(k) for k in invalid[:20]], "truncated_tails": report.truncated_tails,
                     "identity_sha256": ledger.file_sha256(run_dir / "identity.json")}


def postprocess(run_dir: Path, cfg: Any, status: Mapping[str, Any]) -> dict:
    """Runner entry point; recompute completeness before any scientific output."""
    run_dir = Path(run_dir)
    steps = ([status["post_step"]] if status.get("post_step") in POST_NAMES
             else [step for step in cfg.post if step in POST_NAMES])
    if len(steps) != 1:
        raise ValueError("a v4 stage must specify exactly one v4 post step")
    step = steps[0]
    sizes = {"v4_baseline": 60, "v4_strength": 40, "v4_match": 40, "v4_validity": 80, "v4_contrasts": 600}
    wanted_qids = FORMAL_QIDS if step in ("v4_baseline", "v4_contrasts") else ACCESS_QIDS
    if cfg.n_episodes != sizes[step] or cfg.seed != 0 or set(cfg.qids) != set(wanted_qids):
        raise ValueError("v4 post step has the wrong prespecified N, seed or readouts")
    if getattr(cfg, "model_profile", None) != "llama31_8b_instruct":
        raise ValueError("v4 post step requires the approved second-model profile")
    if getattr(cfg, "materials", None) != "v1":
        raise ValueError("v4 requires the original v1 materials")
    records, out = _checked_records(run_dir, cfg, status)
    out.update(step=step, split=cfg.split, n_episodes=cfg.n_episodes)
    if out["consumable"]:
        params = cfg.params or {}
        roles = params.get("roles", {})
        if step == "v4_baseline":
            out.update(baseline_gate(records, cfg.n_episodes))
        elif step in ("v4_strength", "v4_match"):
            table = access_table(records, cfg.n_episodes)
            out.update(select_strength(table, cfg.n_episodes) if step == "v4_strength"
                       else select_static(table, roles["K1"], cfg.n_episodes))
            out["access_table"] = table
        elif step == "v4_validity":
            out.update(validity_summary(records, roles, cfg.n_episodes))
        else:
            if cfg.n_episodes != 600:
                raise ValueError("v4 confirmatory N is fixed at 600")
            scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
            out["families"] = analyze_families(scores, roles)
            out["descriptive"] = descriptive(records)
            out["content_Kstar"] = content_check(records, roles["K*"], roles["CF"], cfg.n_episodes)
            out["access_table"] = access_table(records, cfg.n_episodes)
            by_arm = {r["arm"]: r for r in out["access_table"]}
            k1, static = by_arm[roles["K1"]], by_arm.get(roles.get("STATIC"))
            out["formal_matched"] = bool(static and k1["acc_increment"] > 0 and static["acc_increment"] > 0
                                          and abs(k1["acc_increment"] - static["acc_increment"]) <= 0.25 * k1["acc_increment"] + 1e-12)
            out["independent_route_validated"] = bool(params.get("route_validated", False))
    else:
        out["reason"] = "smoke, incomplete, non-finite, or unfinished run: no research decision"
    out = ledger.sanitize(out)
    (run_dir / f"{step}.json").write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    return out
