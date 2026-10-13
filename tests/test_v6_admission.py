"""Prospective gate boundaries, paired-unit counterexamples and refusal paths."""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from mb import v6_admission as a
from mb import v6_neutral as n
from mb import v6_tasks as t
from mb.v6_contract import canonical_digest

MODEL = "qwen3_4b_instruct_2507"


def vector_fixture(stage="calibration"):
    count = a.SIZES[stage]
    families = (*a.FORMAT_FAMILIES, *(a.BASE_ASSIGNMENTS if stage == "baseline" else ()))
    answer = {}
    for policy in (("OFF",) if stage == "baseline" else ("OFF", "LIVE")):
        answer[policy] = {}
        for side in ("0", "1"):
            answer[policy][side] = {}
            for family in families:
                cell = {"legal_mass": [.98] * count}
                if family not in ("continuation_action", "continuation_fact"):
                    cell["accuracy"] = [(.25 if policy == "OFF" and family == "access_fact" else 1.)] * count
                answer[policy][side][family] = cell
    return answer, [f"e{i}" for i in range(count)]


def raw_fixture(tmp_path, stage="calibration", gain=.25, namespace="test"):
    episodes = n.make_episodes(a.SIZES[stage], stage, namespace=namespace)
    rows = []
    for ep in episodes:
        for policy in n.policies(stage):
            for stream in ("capability", "fact"):
                world = t.initial_world(ep.task) if stream == "capability" else n.FactWorld()
                for r in range(1, 7):
                    world = t.event_world(ep.task, world, r) if stream == "capability" else replace(world, round_id=r)
                    actual = []
                    for qid in n.qids(stage, stream):
                        for side in (0, 1):
                            q = n.question(ep, stream, world, side, qid)
                            choice = (q.correct+1)%4 if qid == "access_fact" and policy == "OFF" else q.correct
                            row = dict(zip(n.KEY_FIELDS, (ep.episode_id, MODEL, stage, gain,
                                           stream, policy, r, side, qid)))
                            row.update(contract=n.CONTRACT, proposal_status=n.STATUS, status="ok",
                                choice=choice, correct_choice=q.correct, correct=choice == q.correct,
                                candidate_map=list(q.candidates), cap_item_id=q.cap_item_id,
                                material_sha256=canonical_digest(n.episode_to_dict(ep)),
                                question_sha256=hashlib.sha256(q.text.encode()).hexdigest(),
                                world=json.loads(json.dumps(asdict(world))), token_ids=[10, 11, 12, 13],
                                top_token=10+q.candidates.index(choice), top_probability=.9,
                                legal_logits=[0., 0., 0., 0.], legal_mass=.98,
                                backend_kind="synthetic_fixture", scientific_data=False)
                            rows.append(row)
                            if qid.startswith("continuation_"):
                                actual.append(choice)
                    world = (t.transition(world, tuple(actual)) if stream == "capability" else
                             replace(world, answers=(*world.answers, tuple(actual))))
    material_path = tmp_path / f"{namespace}.json"
    n.write_materials(material_path, episodes)
    contract_path = tmp_path / "proposal.json"
    contract_path.write_text(json.dumps(a.recommended_contract()))
    plan = {"stage": stage, "model_profile": MODEL, "n": a.SIZES[stage],
            "runtime": {"work_tokens": 64, "preparation_tokens": 16, "window": 16,
                        "choice_labels": ["1", "2", "3", "4"], "gain": gain},
            "text_episode_ids": [], "material_pin": {"path": str(material_path), "sha256": a._sha(material_path)},
            "admission_contract_pin": {"path": str(contract_path), "sha256": a._sha(contract_path)}}
    return {"records": rows, "episodes": episodes, "normalized_plan": plan, "native_identity": None}


@pytest.fixture
def raw(tmp_path):
    return raw_fixture(tmp_path)


def test_proposal_is_not_a_ratification_switch():
    contract = a.recommended_contract()
    assert contract["status"] == "prospective_proposal" and "ratified" not in contract
    assert contract["sample_sizes"] == {"baseline": 60, "calibration": 40, "validation": 80}
    contract["gains"].append(2)
    assert a.recommended_contract()["gains"] == [.25, .5, 1]


def test_baseline_separate_subscales_no_cap_or_fact_accuracy_floor():
    vectors, ids = vector_fixture("baseline")
    for side in ("0", "1"):
        for family in ("task_fullinfo", *a.BASE_ASSIGNMENTS):
            vectors["OFF"][side][family]["accuracy"] = [.90] * 60
        vectors["OFF"][side]["CAP"]["accuracy"] = [0.] * 60
        vectors["OFF"][side]["access_fact"]["accuracy"] = [0.] * 60
    result = a.evaluate_vectors("baseline", 0, ids, vectors)
    assert result["predicate_pass"] and not result["consumable"]
    vectors["OFF"]["1"]["assignment_latest"]["accuracy"][0] = .89
    assert not a.evaluate_vectors("baseline", 0, ids, vectors)["predicate_pass"]


def test_access_boundary_is_point75_and_strict_positive_paired_bound():
    vectors, ids = vector_fixture()
    vectors["LIVE"]["0"]["access_fact"]["accuracy"] = [.75] * 40
    assert a.evaluate_vectors("calibration", .25, ids, vectors)["predicate_pass"]
    vectors["OFF"]["0"]["access_fact"]["accuracy"] = [.75] * 40
    result = a.evaluate_vectors("calibration", .25, ids, vectors)
    assert result["metrics"]["0"]["access_fact"]["gain_lower95"] == 0
    assert not result["predicate_pass"]


def test_capability_upper_bound_not_only_point_loss_and_no_side_pooling():
    vectors, ids = vector_fixture()
    # Mean loss .025 would pass a point rule, but its paired upper95 > .05.
    vectors["OFF"]["1"]["CAP"]["accuracy"] = [1.] * 21 + [0.] * 19
    vectors["LIVE"]["1"]["CAP"]["accuracy"] = [0.] * 20 + [1.] * 20
    result = a.evaluate_vectors("calibration", .5, ids, vectors)
    assert result["metrics"]["1"]["CAP"]["accuracy_loss"] == .025
    assert result["metrics"]["1"]["CAP"]["loss_upper95"] > .05
    assert not result["predicate_pass"]


def test_format_cannot_be_hidden_by_cap_items_or_other_side():
    vectors, ids = vector_fixture()
    vectors["LIVE"]["1"]["continuation_action"]["legal_mass"] = [.89] * 40
    assert not a.evaluate_vectors("calibration", .5, ids, vectors)["predicate_pass"]
    vectors["LIVE"]["1"]["continuation_action"]["legal_mass"] = [.90] * 40
    vectors["OFF"]["1"]["continuation_action"]["legal_mass"] = [.95] * 40
    assert a.evaluate_vectors("calibration", .5, ids, vectors)["predicate_pass"]
    vectors["OFF"]["0"]["task_fullinfo"]["legal_mass"] = [.89] * 40
    assert not a.evaluate_vectors("calibration", .5, ids, vectors)["predicate_pass"]


@pytest.mark.parametrize("mutation", ["goal", "continuation_accuracy", "nonfinite", "unpaired", "one_side"])
def test_vector_contract_rejects_leakage_and_malformed_inputs(mutation):
    vectors, ids = vector_fixture()
    if mutation == "goal": vectors["LIVE"]["0"]["goal_influence"] = {"accuracy": [1.]*40}
    if mutation == "continuation_accuracy": vectors["LIVE"]["0"]["continuation_action"]["accuracy"] = [1.]*40
    if mutation == "nonfinite": vectors["LIVE"]["0"]["CAP"]["accuracy"][0] = float("nan")
    if mutation == "unpaired": vectors["LIVE"]["0"]["CAP"]["accuracy"].pop()
    if mutation == "one_side": del vectors["LIVE"]["1"]
    with pytest.raises(ValueError): a.evaluate_vectors("calibration", .25, ids, vectors)


def test_bootstrap_uses_paired_episode_indices_exactly():
    x = np.array([0., .2, -.1, .7] * 10)
    indices = np.random.default_rng(0).integers(0, 40, size=(10000, 40))
    expected = np.quantile(x[indices].mean(axis=1), .95)
    assert a.paired_bound(x, upper=True) == expected
    assert a.paired_bound([.05] * 40, upper=True) <= .05


def test_exact_five_point_boundary_survives_float_subtraction_only():
    vectors, ids = vector_fixture()
    vectors["LIVE"]["0"]["CAP"]["accuracy"] = [.95] * 40
    assert 1-.95 > .05
    assert a.evaluate_vectors("calibration", .25, ids, vectors)["predicate_pass"]
    vectors["LIVE"]["0"]["CAP"]["accuracy"] = [.949999] * 40
    assert not a.evaluate_vectors("calibration", .25, ids, vectors)["predicate_pass"]


def test_raw_aggregation_is_per_episode_and_fixture_never_consumable(raw):
    result = a.evaluate_stage(**raw)
    assert result["complete"] and result["predicate_pass"]
    assert result["n"] == 40 and result["completeness"]["ok_records"] == 6720
    assert not result["consumable"] and result["synthetic_input"] and result["gate"] == "blocked"
    assert result["metrics"]["0"]["access_fact"]["LIVE"]["accuracy"] == 1
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("missing", ["deleted", "technical_failure"])
def test_incomplete_fixed_cohort_is_unavailable_not_gate_failure(raw, missing):
    if missing == "deleted": raw["records"].pop()
    else: raw["records"][-1] = {**raw["records"][-1], "status": "technical_failure"}
    result = a.evaluate_stage(**raw)
    assert not result["complete"] and result["predicate_pass"] is None
    assert not result["consumable"] and result["gate"] == "unavailable"


@pytest.mark.parametrize("mutation", ["duplicate", "truth", "nonfinite", "material", "contract", "clock"])
def test_raw_source_metadata_and_contract_tamper_rejected(raw, mutation):
    if mutation == "duplicate": raw["records"].append(raw["records"][0])
    if mutation == "truth": raw["records"][0]["correct"] = not raw["records"][0]["correct"]
    if mutation == "nonfinite": raw["records"][0]["legal_mass"] = float("inf")
    if mutation == "material": raw["normalized_plan"]["material_pin"]["sha256"] = "0"*64
    if mutation == "contract": raw["normalized_plan"]["admission_contract_pin"]["sha256"] = "0"*64
    if mutation == "clock": raw["normalized_plan"]["runtime"]["work_tokens"] = 32
    with pytest.raises(ValueError): a.evaluate_stage(**raw)


def test_complete_unmarked_or_smoke_data_cannot_self_attest(raw):
    for row in raw["records"]:
        row.pop("scientific_data"); row.pop("backend_kind")
    assert not a.evaluate_stage(**raw)["consumable"]
    raw["smoke"] = True
    assert a.evaluate_stage(**raw)["gate"] == "blocked"


def selection_bundles(monkeypatch, tmp_path, passing=(.5, 1.)):
    bundles = {}
    for gain in a.GAINS:
        eps = n.make_episodes(40, "calibration", namespace=f"gain{int(gain*100)}")
        plan = {"stage": "calibration", "runtime": {"gain": gain}}
        bundles[gain] = dict(records=[], episodes=eps, normalized_plan=plan, native_identity={})
    def evaluate(**bundle):
        g = bundle["normalized_plan"]["runtime"]["gain"]
        return {"model_profile": MODEL, "episode_ids": [ep.episode_id for ep in bundle["episodes"]],
                "consumable": True, "predicate_pass": g in passing,
                "bindings": {k: "0"*64 for k in ("authorization_sha256", "source_manifest_sha256",
                            "admission_contract_sha256", "native_model_identity")}}
    monkeypatch.setattr(a, "evaluate_stage", evaluate)
    return bundles, evaluate


def test_smallest_gain_all_candidates_and_no_fallback(monkeypatch, tmp_path):
    bundles, evaluate = selection_bundles(monkeypatch, tmp_path)
    result = a.select_calibration(bundles)
    assert result["selected_gain"] == .5 and result["consumable"]
    assert not result["reselection_allowed"]
    monkeypatch.setattr(a, "evaluate_stage", lambda **kw: {**evaluate(**kw), "consumable": False})
    assert a.select_calibration(bundles)["selected_gain"] is None
    bundles.pop(1.)
    with pytest.raises(ValueError, match="All three"): a.select_calibration(bundles)


def test_material_clone_under_new_ids_and_seed_cannot_enter_selection(monkeypatch, tmp_path):
    bundles, _ = selection_bundles(monkeypatch, tmp_path)
    source = bundles[.25]["episodes"][0]
    bundles[.5]["episodes"][0] = replace(source, task=replace(source.task,
        episode_id="other-different", stage="other", seed=888))
    with pytest.raises(ValueError, match="scientific material repeats"):
        a.select_calibration(bundles)


def test_saved_pass_boolean_is_not_a_selector_input():
    with pytest.raises(ValueError, match="raw source bundles"):
        a.select_calibration({g: {"gate": "pass", "consumable": True} for g in a.GAINS})


def predecessor_fixture(monkeypatch, tmp_path):
    """Mock only completed raw loading/scoring; exercise the real source-chain rules."""
    bindings = {k: "a"*64 for k in ("authorization_sha256", "source_manifest_sha256",
                "admission_contract_sha256", "native_model_identity")}
    bundles = {}
    for key, stage, gain in (("baseline", "baseline", 0.), ("calibration_025", "calibration", .25),
            ("calibration_050", "calibration", .5), ("calibration_100", "calibration", 1.),
            ("validation", "validation", .25), ("formal", "formal", .25)):
        eps = (t.make_episodes(240, key) if stage == "formal" else
               n.make_episodes(a.SIZES[stage], stage, namespace=key))
        path = tmp_path / f"{key}.json"
        (t.write_materials if stage == "formal" else n.write_materials)(path, eps)
        prerequisites = ({"baseline": "baseline"} if stage == "calibration" else
                         {x: x for x in ("calibration_025", "calibration_050", "calibration_100")}
                         if stage == "validation" else {"validation": "validation"} if stage == "formal" else {})
        plan = {"stage": stage, "model_profile": MODEL, "runtime": {"gain": gain},
                "material_pin": {"path": str(path), "sha256": a._sha(path)},
                "_admission": bindings, "prerequisites": prerequisites}
        bundles[key] = dict(records=[], episodes=eps, normalized_plan=plan, native_identity={})
    def evaluate(**bundle):
        plan = bundle["normalized_plan"]
        return {"stage": plan["stage"], "gain": plan["runtime"]["gain"], "model_profile": MODEL,
                "episode_ids": [ep.episode_id for ep in bundle["episodes"]],
                "consumable": True, "predicate_pass": True, "gate": "pass",
                "bindings": bindings, "raw_sha256": "b"*64}
    monkeypatch.setattr(a, "_raw_bundle", lambda plan, name: bundles[plan["prerequisites"][name]])
    monkeypatch.setattr(a, "evaluate_stage", evaluate)
    return bundles, evaluate


def test_validation_uses_frozen_smallest_gain_and_no_runner_up(monkeypatch, tmp_path):
    bundles, _ = predecessor_fixture(monkeypatch, tmp_path)
    plan = bundles["validation"]["normalized_plan"]
    assert a.validate_stage_prerequisites(plan)["selection"]["selected_gain"] == .25
    plan["runtime"]["gain"] = .5
    with pytest.raises(ValueError, match="runner-up"):
        a.validate_stage_prerequisites(plan)


@pytest.mark.parametrize("failed", ["baseline", "validation"])
def test_failed_predecessor_cannot_be_reclassified_by_next_stage(monkeypatch, tmp_path, failed):
    bundles, evaluate = predecessor_fixture(monkeypatch, tmp_path)
    monkeypatch.setattr(a, "evaluate_stage", lambda **b: {**evaluate(**b),
        "gate": "fail" if b["normalized_plan"]["stage"] == failed else "pass"})
    target = "calibration_025" if failed == "baseline" else "formal"
    with pytest.raises(ValueError, match="failed"):
        a.validate_stage_prerequisites(bundles[target]["normalized_plan"])


@pytest.mark.parametrize("target,ancestor", [("validation", "baseline"),
    ("formal", "baseline"), ("formal", "calibration_050"), ("formal", "validation")])
def test_new_stage_rejects_task_reused_from_any_ancestor(monkeypatch, tmp_path, target, ancestor):
    bundles, _ = predecessor_fixture(monkeypatch, tmp_path)
    bundle = bundles[target]
    source = bundles[ancestor]["episodes"][0].task
    source = replace(source, episode_id="newstage-renamed", stage="newstage", seed=999)
    eps = bundle["episodes"]
    eps[0] = source if target == "formal" else replace(eps[0], task=source)
    plan = bundle["normalized_plan"]
    path = Path(plan["material_pin"]["path"])
    path.write_text(t.material_json(eps) if target == "formal" else n.material_json(eps))
    plan["material_pin"]["sha256"] = a._sha(path)
    with pytest.raises(ValueError, match="ancestor material"):
        a.validate_stage_prerequisites(plan)


def test_raw_prerequisite_completion_pin_checked_before_reader(monkeypatch, tmp_path):
    from mb import v6_execution as execution
    path = tmp_path / "baseline" / "completion.json"
    path.parent.mkdir(); path.write_text('{"status":"complete"}')
    plan = {"prerequisites": {"baseline": {"path": str(path), "sha256": a._sha(path)}}}
    called = []
    monkeypatch.setattr(execution, "read_native_run", lambda path: called.append(path))
    path.write_text('{"status":"changed"}')
    with pytest.raises(ValueError, match="completion bytes"):
        a._raw_bundle(plan, "baseline")
    assert called == []


def test_restored_history_can_resolve_only_byte_identical_adjacent_run(monkeypatch, tmp_path):
    from mb import v6_execution as execution
    path = tmp_path / "baseline" / "completion.json"
    path.parent.mkdir(); path.write_text('{"status":"complete"}')
    evidence = tmp_path / "calibration" / "evidence"
    evidence.mkdir(parents=True)
    plan = {"_admission": {"evidence_dir": str(evidence)}, "output_dir": "/unavailable/calibration",
            "prerequisites": {"baseline": {"path": "/unavailable/baseline/completion.json", "sha256": a._sha(path)}}}
    called = []
    monkeypatch.setattr(execution, "read_native_run", lambda p: called.append(p) or {
        "records": [], "episodes": [], "plan": {}, "native_identity": {}})
    a._raw_bundle(plan, "baseline")
    assert called == [path]
    path.write_text('{"status":"different"}')
    with pytest.raises(ValueError, match="completion bytes"):
        a._raw_bundle(plan, "baseline")


def test_historical_and_native_identity_rechecked_not_boolean_attested(raw, monkeypatch, tmp_path):
    from mb import v6_execution as execution
    plan = raw["normalized_plan"]
    plan["plan_sha256"] = "1"*64
    plan["_admission"] = {"validated_at_epoch": 100., "historical_only": True,
        "evidence_dir": str(tmp_path / "evidence"), **{k: "2"*64 for k in
        ("authorization_sha256", "source_manifest_sha256", "admission_contract_sha256")}}
    monkeypatch.setattr(execution, "historical_plan", lambda path: deepcopy(plan))
    monkeypatch.setattr(execution, "_prerequisites", lambda plan: {"native_model_identity": "3"*64})
    identity = execution._identity(plan, n.materials_sha256(raw["episodes"]), n.KEY_FIELDS, "3"*64)
    for row in raw["records"]:
        row.update(backend_kind="native", scientific_data=True, execution_identity_sha256=canonical_digest(identity))
    assert a._verify_evidence(plan, raw["episodes"], identity, raw["records"])["native_model_identity"] == "3"*64
    raw["records"][0]["execution_identity_sha256"] = "4"*64
    with pytest.raises(ValueError, match="raw row"):
        a._verify_evidence(plan, raw["episodes"], identity, raw["records"])
    raw["records"][0]["execution_identity_sha256"] = canonical_digest(identity)
    monkeypatch.setattr(execution, "historical_plan", lambda path: {**plan, "plan_sha256": "5"*64})
    with pytest.raises(ValueError, match="Archived admission"):
        a._verify_evidence(plan, raw["episodes"], identity, raw["records"])
