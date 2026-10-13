"""Prospective neutral admission predicates, never an execution authorization.

The proposal remains a proposal even after a separate PI authorization pins it.
Every statistic uses paired episode averages, with physical sides and readout
families kept separate. Source/authorization/native checks are additional to
the numerical predicates; synthetic fixtures can never select a setting.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Iterable

import numpy as np

from mb.v6_contract import canonical_digest

VERSION = "v6-neutral-admission-1"
GAINS = (0.25, 0.5, 1.0)
SIZES = {"baseline": 60, "calibration": 40, "validation": 80}
FORMAT_FAMILIES = ("task_fullinfo", "CAP", "continuation_action", "access_fact", "continuation_fact")
BASE_ASSIGNMENTS = ("assignment_original", "assignment_latest")
ACCURACY_FAMILIES = ("task_fullinfo", "CAP", "access_fact")
BOUNDARY_EPS = 1e-12


def recommended_contract() -> dict:
    """Exact proposed package. Ratification belongs in a separate pinned receipt."""
    return {
        "version": VERSION, "status": "prospective_proposal",
        "sample_sizes": dict(SIZES), "gains": list(GAINS),
        "runtime": {"rounds": 6, "work_tokens": 64, "preparation_tokens": 16,
                    "window": 16, "choice_labels": ["1", "2", "3", "4"]},
        "baseline_accuracy_min": 0.90, "access_accuracy_min": 0.75,
        "access_gain_lower_bound_strict_min": 0.0,
        "capability_loss_upper_bound_max": 0.05,
        "legal_mass_min": 0.90, "legal_mass_drop_max": 0.05,
        "bootstrap": {"draws": 10000, "seed": 0, "lower_quantile": 0.05,
                      "upper_quantile": 0.95},
        "format_families": list(FORMAT_FAMILIES),
        "baseline_extra_format_families": list(BASE_ASSIGNMENTS),
        "format_absolute_floor_policies": "each_observed_policy",
        "baseline_accuracy_families": ["task_fullinfo", *BASE_ASSIGNMENTS],
        "capability_accuracy_families": ["task_fullinfo", "CAP"],
        "format_bounds": "point_estimates",
        "floating_point_boundary_tolerance": BOUNDARY_EPS,
        "calibration_same_predicate_as_validation": True,
        "calibration_cohorts": "disjoint_40_per_gain_with_paired_OFF",
        "all_gains_complete": True, "selection": "smallest_passing_gain",
        "validation_reselection": False,
    }


def _require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def _mean(values: Iterable[float]) -> float:
    xs = list(values)
    return math.fsum(xs) / len(xs)


def _at_least(value: float, threshold: float) -> bool:
    return value >= threshold or math.isclose(value, threshold, rel_tol=0, abs_tol=BOUNDARY_EPS)


def _at_most(value: float, threshold: float) -> bool:
    return value <= threshold or math.isclose(value, threshold, rel_tol=0, abs_tol=BOUNDARY_EPS)


def _vector(value: Any, n: int) -> list[float]:
    _require(type(value) is list and len(value) == n, "Complete paired episode vector required")
    _require(all(type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1.000001
                 for x in value), "Neutral vectors must contain finite observed rates")
    return [float(x) for x in value]


def paired_bound(differences: Iterable[float], *, upper: bool) -> float:
    """One-sided percentile bound, resampling whole paired episodes only."""
    values = np.asarray(list(differences), dtype=float)
    _require(values.ndim == 1 and len(values) > 0 and np.isfinite(values).all(),
             "Finite paired episode differences required")
    indices = np.random.default_rng(0).integers(0, len(values), size=(10000, len(values)))
    means = values[indices].mean(axis=1)
    return float(np.quantile(means, 0.95 if upper else 0.05, method="linear"))


def _scope(stage: str, gain: float, episode_ids: list[str]) -> None:
    _require(stage in SIZES, "Unknown neutral admission stage")
    _require(type(gain) in (float, int) and math.isfinite(gain)
             and gain in ((0.0,) if stage == "baseline" else GAINS), "Invalid fixed neutral gain")
    _require(type(episode_ids) is list and len(episode_ids) == SIZES[stage]
             and all(type(x) is str and x for x in episode_ids)
             and len(set(episode_ids)) == len(episode_ids), "Wrong fixed N or duplicate episode IDs")


def evaluate_vectors(stage: str, gain: float, episode_ids: list[str], vectors: dict) -> dict:
    """Diagnostic-only predicate evaluation; vectors alone never prove admission.

    Input: policy -> string physical side -> family -> accuracy/legal_mass vector.
    Continuation accuracy is deliberately not accepted as a selection variable.
    """
    _scope(stage, gain, episode_ids)
    n = len(episode_ids)
    policies = ("OFF",) if stage == "baseline" else ("OFF", "LIVE")
    families = (*FORMAT_FAMILIES, *(BASE_ASSIGNMENTS if stage == "baseline" else ()))
    accuracy = (*ACCURACY_FAMILIES, *(BASE_ASSIGNMENTS if stage == "baseline" else ()))
    _require(type(vectors) is dict and set(vectors) == set(policies), "Unexpected neutral policies")
    checked = {}
    for policy in policies:
        _require(type(vectors[policy]) is dict and set(vectors[policy]) == {"0", "1"},
                 "Both physical sides must be assessed separately")
        checked[policy] = {}
        for side in ("0", "1"):
            source = vectors[policy][side]
            _require(type(source) is dict and set(source) == set(families), "Non-neutral or missing metric family")
            checked[policy][side] = {}
            for family in families:
                names = {"legal_mass", *( ["accuracy"] if family in accuracy else [])}
                _require(type(source[family]) is dict and set(source[family]) == names,
                         "Non-neutral or missing metric; continuation accuracy cannot select")
                checked[policy][side][family] = {key: _vector(source[family][key], n) for key in names}
                if "accuracy" in names:
                    _require(max(checked[policy][side][family]["accuracy"]) <= 1,
                             "Accuracy cannot exceed one")
    metrics, predicates = {}, {}
    for side in ("0", "1"):
        metrics[side] = {}
        for family in families:
            off = checked["OFF"][side][family]
            current = checked[policies[-1]][side][family]
            cell = {"OFF": {name: _mean(xs) for name, xs in off.items()}}
            if stage != "baseline":
                cell["LIVE"] = {name: _mean(xs) for name, xs in current.items()}
            mass = _mean(current["legal_mass"])
            predicates[f"side{side}.{family}.mass"] = _at_least(mass, 0.90)
            # OFF must itself satisfy the same absolute-format floor, so poor
            # reference formatting cannot make a degradation look acceptable.
            predicates[f"side{side}.{family}.OFF_mass"] = _at_least(_mean(off["legal_mass"]), 0.90)
            if stage != "baseline":
                loss = _mean(a-b for a, b in zip(off["legal_mass"], current["legal_mass"]))
                cell["mass_loss"] = loss
                predicates[f"side{side}.{family}.mass_loss"] = _at_most(loss, 0.05)
            if stage == "baseline" and family in ("task_fullinfo", *BASE_ASSIGNMENTS):
                predicates[f"side{side}.{family}.accuracy"] = _at_least(_mean(off["accuracy"]), 0.90)
            if stage != "baseline" and family in ("task_fullinfo", "CAP"):
                diff = [a-b for a, b in zip(off["accuracy"], current["accuracy"])]
                cell["accuracy_loss"] = _mean(diff)
                cell["loss_upper95"] = paired_bound(diff, upper=True)
                predicates[f"side{side}.{family}.loss_upper95"] = _at_most(cell["loss_upper95"], 0.05)
            if stage != "baseline" and family == "access_fact":
                diff = [b-a for a, b in zip(off["accuracy"], current["accuracy"])]
                cell["accuracy_gain"] = _mean(diff)
                cell["gain_lower95"] = paired_bound(diff, upper=False)
                predicates[f"side{side}.access_fact.accuracy"] = _at_least(_mean(current["accuracy"]), 0.75)
                predicates[f"side{side}.access_fact.gain_lower95"] = cell["gain_lower95"] > BOUNDARY_EPS
            metrics[side][family] = cell
    return {"version": VERSION, "stage": stage, "gain": float(gain), "n": n,
            "episode_ids": episode_ids, "unit": "paired_episode", "metrics": metrics,
            "predicates": predicates, "predicate_pass": all(predicates.values()),
            "consumable": False, "gate": "blocked", "selection_eligible": False,
            "reason": "Vectors alone do not verify raw data, source or prospective authorization"}


def _vectors(records: list[dict], episode_ids: list[str], stage: str) -> dict:
    """Aggregate all scheduled rounds/items within each physical-side episode."""
    policies = ("OFF",) if stage == "baseline" else ("OFF", "LIVE")
    families = (*FORMAT_FAMILIES, *(BASE_ASSIGNMENTS if stage == "baseline" else ()))
    accuracy = (*ACCURACY_FAMILIES, *(BASE_ASSIGNMENTS if stage == "baseline" else ()))
    groups: dict[tuple, list[dict]] = {}
    for row in records:
        family = "CAP" if row["qid"] in ("CAP0", "CAP1", "CAP2") else row["qid"]
        groups.setdefault((row["policy"], str(row["side"]), family, row["episode_id"]), []).append(row)
    result = {}
    for policy in policies:
        result[policy] = {}
        for side in ("0", "1"):
            result[policy][side] = {}
            for family in families:
                batches = [groups[policy, side, family, ep] for ep in episode_ids]
                result[policy][side][family] = {"legal_mass": [_mean(r["legal_mass"] for r in rs) for rs in batches]}
                if family in accuracy:
                    result[policy][side][family]["accuracy"] = [_mean(float(r["correct"]) for r in rs) for rs in batches]
    return result


def _sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _pinned_path(plan: dict, pin: dict) -> Path:
    _require(type(pin) is dict and set(pin) == {"path", "sha256"}, "Invalid scientific input pin")
    evidence = plan.get("_admission", {}).get("evidence_dir")
    path = Path(evidence) / (pin["sha256"] + ".json") if evidence else Path(pin["path"])
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    _require(path.is_file() and not path.is_symlink() and _sha(path) == pin["sha256"], "Pinned scientific input differs")
    return path


def _plan_contract(plan: dict, episodes: list) -> None:
    from mb import v6_neutral as neutral
    from mb.model_profiles import PROFILES

    _require(type(plan) is dict and plan.get("model_profile") in PROFILES, "Unknown neutral model profile")
    stage, gain = plan.get("stage"), plan.get("runtime", {}).get("gain")
    _scope(stage, gain, [ep.episode_id for ep in episodes])
    _require(plan.get("n") == SIZES[stage] and all(ep.stage == stage for ep in episodes),
             "Material/stage count differs from proposal")
    runtime = {k: v for k, v in recommended_contract()["runtime"].items() if k != "rounds"}
    _require(plan.get("runtime") == {**runtime, "gain": gain} and plan.get("text_episode_ids") == [],
             "Neutral clocks/labels/text scope differs")
    pin = plan.get("material_pin", {})
    material_path = _pinned_path(plan, pin)
    _require(pin["sha256"] == neutral.materials_sha256(episodes), "Neutral material pin differs")
    _require(neutral.load_materials(material_path) == episodes, "Declared episodes differ from pinned materials")
    contract = plan.get("admission_contract_pin", {})
    path = _pinned_path(plan, contract)
    _require(json.loads(path.read_text()) == recommended_contract(), "Unreviewed admission contract")


def _verify_evidence(plan: dict, episodes: list, native_identity: dict, records: list[dict]) -> dict:
    """Reverify archived launch evidence, then actual native row/identity binding.

    This is historical collection admission, never permission for a new run.
    The launch caller must archive its envelope and every mutable referenced
    proof before collection; a rewritten or missing archived pin fails closed.
    """
    from mb import v6_execution as execution
    from mb import v6_neutral as neutral

    evidence = plan.get("_admission")
    _require(type(evidence) is dict, "Archived prospective admission is absent")
    issued = evidence.get("validated_at_epoch")
    _require(type(issued) in (float, int) and math.isfinite(issued) and 0 <= issued <= time.time(),
             "Invalid recorded launch-admission time")
    _require(type(evidence.get("evidence_dir")) is str, "Immutable archived launch evidence is absent")
    checked = execution.historical_plan(Path(evidence["evidence_dir"]).parent)
    _require(checked == plan, "Archived admission differs from collection plan")
    _require(checked["_admission"].get("historical_only") is True,
             "Scientific audit cannot reuse a mutable live launch envelope")
    accepted = execution._prerequisites(checked)
    _require(type(accepted) is dict, "Real native acceptance is absent")
    expected = execution._identity(checked, neutral.materials_sha256(episodes),
                                   neutral.KEY_FIELDS, accepted["native_model_identity"])
    _require(native_identity == expected, "Native execution identity differs from verified acceptance")
    digest = canonical_digest(expected)
    _require(all(row.get("backend_kind") == "native" and row.get("scientific_data") is True
                 and row.get("execution_identity_sha256") == digest for row in records),
             "Native raw row lacks the verified execution identity")
    return {"authorization_sha256": evidence["authorization_sha256"],
            "source_manifest_sha256": evidence["source_manifest_sha256"],
            "admission_contract_sha256": evidence["admission_contract_sha256"],
            "plan_sha256": checked["plan_sha256"], "native_identity_sha256": digest,
            "native_model_identity": accepted["native_model_identity"]}


def evaluate_stage(records: Iterable[dict], episodes: Iterable, normalized_plan: dict, *,
                   native_identity: dict | None = None, smoke: bool = False) -> dict:
    """Evaluate a fixed complete neutral stage with explicit raw/source admission.

    Malformed/contradictory input raises. Missing trials are unavailable without
    imputation. Complete synthetic or unratified data can expose only diagnostic
    predicates, never a usable gate. An invalid supplied authority also raises.
    """
    from mb import v6_neutral as neutral

    rows, eps = list(records), list(episodes)
    _plan_contract(normalized_plan, eps)
    stage, profile = normalized_plan["stage"], normalized_plan["model_profile"]
    gain = normalized_plan["runtime"]["gain"]
    audit = neutral.validate_records(rows, eps, profile, gain, require_complete=False)
    base = {"version": VERSION, "stage": stage, "model_profile": profile, "gain": gain,
            "n": len(eps), "episode_ids": [ep.episode_id for ep in eps], "complete": audit["complete"],
            "completeness": audit, "consumable": False, "selection_eligible": False,
            "predicate_pass": None, "gate": "unavailable", "smoke": smoke,
            "synthetic_input": audit["synthetic"], "raw_sha256": canonical_digest(rows),
            "materials_sha256": neutral.materials_sha256(eps)}
    _require(type(smoke) is bool, "Smoke must be an explicit boolean")
    if not audit["complete"]:
        return {**base, "reason": "Fixed neutral sample is incomplete; no complete-case gate"}
    diagnostic = evaluate_vectors(stage, gain, base["episode_ids"], _vectors(rows, base["episode_ids"], stage))
    result = {**diagnostic, **base, "predicate_pass": diagnostic["predicate_pass"],
              "metrics": diagnostic["metrics"], "predicates": diagnostic["predicates"]}
    if smoke or audit["synthetic"] or native_identity is None or "_admission" not in normalized_plan:
        return {**result, "gate": "blocked", "reason": "Smoke, synthetic or missing prospective/native admission"}
    bindings = _verify_evidence(normalized_plan, eps, native_identity, rows)
    predecessors = validate_stage_prerequisites(normalized_plan)
    passed = result["predicate_pass"]
    return {**result, "consumable": True, "gate": "pass" if passed else "fail",
            "selection_eligible": passed, "bindings": bindings, "predecessors": predecessors,
            "reason": "All neutral predicates pass" if passed else "Neutral predicate failed; no fallback/reselection"}


def select_calibration(candidates: dict[float, dict]) -> dict:
    """Recompute every candidate from raw bundles; never consume pass booleans.

    Each bundle contains records, episodes, normalized_plan, native_identity and
    optionally smoke. All three disjoint fixed cohorts must be consumable before
    selecting the smallest passing gain. Failure never substitutes a new sample.
    """
    _require(type(candidates) is dict and set(candidates) == set(GAINS)
             and all(type(k) in (int, float) for k in candidates), "All three fixed calibration gains required")
    results, ids, fingerprints, task_fingerprints = {}, set(), set(), set()
    model = bindings = None
    for gain in GAINS:
        bundle = candidates[gain]
        required = {"records", "episodes", "normalized_plan", "native_identity"}
        _require(type(bundle) is dict and required <= set(bundle) <= required | {"smoke"},
                 "Calibration selection requires raw source bundles only")
        plan = bundle["normalized_plan"]
        _require(plan.get("stage") == "calibration" and plan.get("runtime", {}).get("gain") == gain,
                 "Calibration candidate identity differs")
        result = evaluate_stage(**bundle)
        current_model = result["model_profile"]
        _require(model in (None, current_model), "Cannot select across model checkpoints")
        model = current_model
        current_ids = set(result["episode_ids"])
        _require(not ids & current_ids, "Calibration cohorts overlap")
        ids |= current_ids
        for ep in bundle["episodes"]:
            digest = _scientific_fingerprint(ep)
            _require(digest not in fingerprints, "Calibration scientific material repeats under another ID")
            fingerprints.add(digest)
            task_digest = _task_fingerprint(ep)
            _require(task_digest not in task_fingerprints, "Calibration task material repeats under another ID")
            task_fingerprints.add(task_digest)
        if result["consumable"]:
            current = {k: result["bindings"][k] for k in ("authorization_sha256", "source_manifest_sha256",
                      "admission_contract_sha256", "native_model_identity")}
            _require(bindings is None or current == bindings, "Calibration authority/source/native identity differs")
            bindings = current
        results[str(gain)] = result
    usable = all(r["consumable"] for r in results.values())
    chosen = next((g for g in GAINS if results[str(g)]["predicate_pass"]), None) if usable else None
    return {"version": VERSION, "stage": "calibration_selection", "model_profile": model,
            "consumable": usable, "gate": ("pass" if chosen is not None else "fail") if usable else "unavailable",
            "selected_gain": chosen, "candidates": results, "bindings": bindings,
            "rule": "smallest_passing_gain_after_all_three_complete", "reselection_allowed": False}


def _raw_bundle(plan: dict, name: str) -> dict:
    from mb import v6_execution as execution

    pin = plan.get("prerequisites", {}).get(name)
    _require(type(pin) is dict and set(pin) == {"path", "sha256"}, f"Missing raw prerequisite: {name}")
    path = Path(pin["path"])
    if not path.is_file():
        # Restored runs keep their original stage paths in their immutable plan;
        # only the identical completion file in the adjacent run can substitute.
        evidence = plan.get("_admission", {}).get("evidence_dir")
        parent = Path(evidence).parent.parent if evidence else Path(plan["output_dir"]).parent
        path = parent / path.parent.name / path.name
    _require(path.name == "completion.json" and path.is_file() and _sha(path) == pin["sha256"],
             f"Prerequisite completion bytes changed: {name}")
    bundle = execution.read_native_run(path)
    return {"records": bundle["records"], "episodes": bundle["episodes"],
            "normalized_plan": bundle["plan"], "native_identity": bundle["native_identity"]}


def _same_package(plan: dict, result: dict) -> None:
    _require(result["model_profile"] == plan["model_profile"], "Prerequisite uses another model")
    _require(result.get("consumable") is True, "Prerequisite data are not scientifically consumable")
    admission = plan.get("_admission", {})
    for name in ("authorization_sha256", "source_manifest_sha256", "admission_contract_sha256"):
        _require(result["bindings"][name] == admission.get(name), "Prerequisite approval/source/contract differs")


def _scientific_fingerprint(ep: Any) -> str:
    from mb import v6_neutral as neutral
    from mb import v6_tasks as tasks

    if isinstance(ep, neutral.NeutralEpisode):
        value = neutral.episode_to_dict(ep)
        value["task"] = {k: v for k, v in value["task"].items() if k not in ("episode_id", "stage", "seed")}
        value.pop("stage")
    else:
        value = {k: v for k, v in tasks.episode_to_dict(ep).items() if k not in ("episode_id", "stage", "seed")}
    return canonical_digest(value)


def _task_fingerprint(ep: Any) -> str:
    from mb import v6_neutral as neutral
    from mb import v6_tasks as tasks
    task = ep.task if isinstance(ep, neutral.NeutralEpisode) else ep
    return canonical_digest({k: v for k, v in tasks.episode_to_dict(task).items()
                             if k not in ("episode_id", "stage", "seed")})


def _material_scope(episodes: list) -> dict:
    return {"episode_ids": sorted(ep.episode_id for ep in episodes),
            "scientific_fingerprints": sorted(_scientific_fingerprint(ep) for ep in episodes),
            "task_fingerprints": sorted(_task_fingerprint(ep) for ep in episodes)}


def validate_stage_prerequisites(plan: dict) -> dict:
    """Recompute raw neutral predecessors before a new model/write operation.

    Native/smoke/resume prerequisites are independently checked by execution.
    This routine does not grant a launch permission or refresh a budget proof.
    """
    stage = plan["stage"]
    _require(stage in (*SIZES, "formal"), "Unknown stage requiring neutral prerequisites")
    from mb import v6_neutral as neutral
    from mb import v6_tasks as tasks
    material_path = _pinned_path(plan, plan["material_pin"])
    current = (tasks.load_materials(material_path) if stage == "formal" else neutral.load_materials(material_path))
    current_scope = _material_scope(current)
    if stage == "baseline":
        return {"stage": stage, "scientific_prerequisites": [], "selection": None,
                "material_ancestry": [current_scope]}
    bundles, reports = [], []
    ancestry = []
    selection = None
    if stage == "calibration":
        base = _raw_bundle(plan, "baseline")
        _require(base["normalized_plan"]["stage"] == "baseline", "Baseline prerequisite is another stage")
        result = evaluate_stage(**base)
        _same_package(plan, result)
        _require(result["gate"] == "pass", "Baseline failed; calibration cannot proceed")
        bundles.append(base); reports.append(result)
        ancestry.append(_material_scope(base["episodes"]))
    elif stage == "validation":
        candidates = {}
        for gain, name in zip(GAINS, ("calibration_025", "calibration_050", "calibration_100")):
            candidate = _raw_bundle(plan, name)
            previous = validate_stage_prerequisites(candidate["normalized_plan"])
            ancestry.extend(previous["material_ancestry"])
            candidates[gain] = candidate
            bundles.append(candidate)
        selection = select_calibration(candidates)
        _require(selection["consumable"] and selection["gate"] == "pass", "No usable selected calibration gain")
        _require(plan["runtime"]["gain"] == selection["selected_gain"], "Validation cannot test a runner-up gain")
        for result in selection["candidates"].values():
            _same_package(plan, result)
            reports.append(result)
    else:
        validation = _raw_bundle(plan, "validation")
        _require(validation["normalized_plan"]["stage"] == "validation", "Validation prerequisite is another stage")
        previous = validate_stage_prerequisites(validation["normalized_plan"])
        ancestry.extend(previous["material_ancestry"])
        result = evaluate_stage(**validation)
        _same_package(plan, result)
        _require(result["gate"] == "pass", "Independent validation failed; no formal collection or fallback")
        _require(plan["runtime"]["gain"] == result["gain"], "Formal gain differs from independent validation")
        selection = previous["selection"]
        bundles.append(validation); reports.append(result)
    for bundle in bundles:
        ancestry.append(_material_scope(bundle["episodes"]))
    for earlier in ancestry:
        for key in current_scope:
            _require(not set(current_scope[key]) & set(earlier[key]), "Current stage repeats ancestor material")
    ancestry = list({canonical_digest(value): value for value in ancestry}.values())
    return {"stage": stage, "scientific_prerequisites": [{"stage": r["stage"], "gain": r["gain"],
             "raw_sha256": r["raw_sha256"], "bindings": r["bindings"]} for r in reports],
            "selection": selection, "material_ancestry": [*ancestry, current_scope]}
