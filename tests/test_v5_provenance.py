"""Physical truth, stage visibility, paired sampling and fixed v5 families."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest

from mb import analyze, ledger, provenance_tasks as pt, tasks, v5_provenance as vp
from mb.conditions import ArmConfig


ROLES = {"C0": "base", "KV": "kv", "CONFLICT": "conflict"}
BASE_ROLES = {"C0": "base", "CONFLICT": "conflict"}


def records(qids, n=4, baseline=False, split="v5-test"):
    output = []
    for i, ep in enumerate(tasks.make_episodes(n, split, seed=0)):
        for role, arm in (BASE_ROLES if baseline else ROLES).items():
            for side in (("A", "B") if baseline else ("A",)):
                for qid in qids:
                    for rot in ep.rotations:
                        kind = "word" if "WORD" in qid else "rule"
                        physical = pt.candidates(ep)[kind]
                        cap = qid.startswith("CAP")
                        content, options, meanings, cap_id = pt.question_body(ep, side, qid, rot)
                        options = list(options)
                        question = SimpleNamespace(qid=qid, options=tuple(options))
                        meta = pt.record_metadata(ep, side, question, role == "CONFLICT")
                        truth = options[meanings.index("correct")] if cap else meta["expected_truth"]
                        zs = {option: (6.0 if option == truth else 0.0) for option in options}
                        if not baseline and not cap:
                            a, b, r, d = (physical[k] for k in "abrd")
                            if qid in vp.DONOR_QIDS:
                                if "ROBIN" in qid:
                                    zs.update({r: 4.0, d: (8.0 + i / 10 if role == "CONFLICT" else 0.0)})
                                else:
                                    zs.update({b: (0.0 if role == "C0" else 4 + i / 10), d: 0.0})
                            elif "ROBIN" in qid:
                                zs.update({r: 4.0, d: (7.0 + i / 10 if role == "CONFLICT" else 0.0)})
                            elif role != "C0":
                                zs.update({a: 1.0, b: 5.0 + i / 10 + (2.0 if qid in ("START", "WORD") else 0.0)})
                        output.append({"episode_id": ep.episode_id, "arm": arm, "recipient": side,
                                       "qid": qid, "rotation_id": rot, "status": "ok", "label_mass": .98,
                                       "options": options, "label_logits": [zs[x] for x in options],
                                       "label_logprobs": [-4.0] * 4,
                                       "label_meaning": list(meanings), "cap_item_id": cap_id,
                                       "text_hash": hashlib.sha256(content.encode()).hexdigest()[:16], "provenance": meta})
    return output


def test_question_constants_match_runner_contract():
    assert vp.BASELINE_QIDS == pt.BASELINE_QIDS
    assert vp.ACCESS_QIDS == pt.VALIDITY_QIDS
    assert vp.FORMAL_QIDS == pt.ALL_QIDS
    assert len(vp.FORMAL_QIDS) == 12


def test_baseline_checks_both_roles_and_changed_b_truth():
    rows = records(vp.BASELINE_QIDS, baseline=True)
    result = vp.baseline_gate(rows, BASE_ROLES, 4)
    assert result["gate"] == "pass"
    changed = [r for r in rows if r["arm"] == "conflict" and r["recipient"] == "B" and r["qid"] == "PROV_ROBIN_RULE"]
    assert all(r["provenance"]["expected_truth"] == r["provenance"]["candidates"]["rule"]["d"] for r in changed)
    for r in changed:
        r["label_logits"] = [8.0 if x == r["provenance"]["candidates"]["rule"]["r"] else 0.0 for x in r["options"]]
    assert vp.baseline_gate(rows, BASE_ROLES, 4)["gate"] == "fail"


def test_baseline_cap_mass_and_single_question_are_not_pooled_away():
    for qid in ("CAP0", "START"):
        rows = records(vp.BASELINE_QIDS, baseline=True)
        for r in rows:
            if r["recipient"] == "B" and r["arm"] == "conflict" and r["qid"] == qid:
                r["label_logits"] = [-x for x in r["label_logits"]]
        assert vp.baseline_gate(rows, BASE_ROLES, 4)["gate"] == "fail"
    rows = records(vp.BASELINE_QIDS, baseline=True)
    for r in rows:
        if r["recipient"] == "B" and r["arm"] == "conflict":
            r["label_mass"] = .89
    assert vp.baseline_gate(rows, BASE_ROLES, 4)["gate"] == "fail"


@pytest.mark.parametrize("mutation,match", [
    (lambda rs: rs.append(deepcopy(rs[0])), "duplicate"),
    (lambda rs: rs.pop(), "incomplete"),
    (lambda rs: rs[0].update(label_logits=[0, 0, float("nan"), 0]), "finite"),
    (lambda rs: rs[0].update(label_mass=None), "finite"),
    (lambda rs: rs[0].update(label_logprobs=[0, float("nan"), 0, 0]), "finite"),
    (lambda rs: rs[0].update(status="failed"), "successful"),
    (lambda rs: rs[0].update(rotation_id=3), "ordering|incomplete|paired"),
    (lambda rs: rs[0]["provenance"].update(expected_truth="fabricated"), "truth"),
    (lambda rs: rs[0]["provenance"].update(candidate_labels={}), "labels"),
    (lambda rs: rs[0]["provenance"].update(donor_robin_conflict=True), "truth|mutation"),
    (lambda rs: rs[0].update(text_hash="unpaired"), "paired question"),
])
def test_rejects_bad_physical_or_sampling_contract(mutation, match):
    rows = records(vp.ACCESS_QIDS)
    mutation(rows)
    with pytest.raises(ValueError, match=match):
        vp.validity_summary(rows, ROLES, 4, n_boot=20)


def test_access_gate_never_accepts_attribution_or_anchors():
    for qid in ("PROV_SELF_RULE", "PROV_ROBIN_RULE", "START", "WORD"):
        rows = records(vp.ACCESS_QIDS) + records((qid,))
        with pytest.raises(ValueError, match="access-only"):
            vp.validity_summary(rows, ROLES, 4, n_boot=20)
    result = vp.validity_summary(records(vp.ACCESS_QIDS), ROLES, 4, n_boot=20)
    assert result["gate"] == "pass"
    assert "primary" not in result and "descriptive" not in result


def test_physical_specificity_not_treatment_relabeled_partner():
    rows = records(vp.ACCESS_QIDS)
    result = vp.validity_summary(rows, ROLES, 4, n_boot=100)
    assert result["donor_robin_specificity"]["rule"]["mean"] == pytest.approx(8.15)
    assert result["donor_own_access"]["rule"]["mean"] == pytest.approx(4.15)
    # Meaning labels may follow a legacy convention; physical scoring does not.
    for r in rows:
        if not r["qid"].startswith("CAP"):
            r["label_meaning"] = ["partner", "robin", "own", "unused"]
    assert vp.validity_summary(rows, ROLES, 4, n_boot=100) == result
    for r in rows:
        if r["arm"] == "conflict" and r["qid"] == "PROV_DONOR_ROBIN_RULE":
            physical = r["provenance"]["candidates"]["rule"]
            r["label_logits"][r["options"].index(physical["d"])] = 0.0
    assert vp.validity_summary(rows, ROLES, 4, n_boot=100)["gate"] == "fail"


def test_word_specificity_is_diagnostic_only_and_quality_is_required():
    rows = records(vp.ACCESS_QIDS)
    for r in rows:
        if r["qid"].endswith("WORD"):
            r["label_logits"] = [0.0] * 4
    result = vp.validity_summary(rows, ROLES, 4, n_boot=20)
    assert result["gate"] == "pass" and not result["donor_robin_specificity"]["word"]["pass"]
    for r in rows:
        if r["arm"] == "conflict" and r["qid"].startswith("CAP"):
            r["label_logits"] = [-x for x in r["label_logits"]]
    assert vp.validity_summary(rows, ROLES, 4, n_boot=20)["gate"] == "fail"


def test_formal_averages_orderings_and_keeps_anchor_interaction_separate():
    rows = records(vp.FORMAL_QIDS)
    result = vp.formal_summary(rows, ROLES, vp.MODEL_PROFILES[0], 4, n_boot=100)
    assert result["primary"][0]["n"] == 4
    assert result["primary"][0]["mean"] == pytest.approx(7.15)
    assert [r["name"] for r in result["secondary"]] == list(vp.SECONDARY_NAMES)
    assert result["secondary"][1]["mean"] == 2
    assert result["secondary"][2]["mean"] == 2
    assert result["descriptive"]["CONFLICT"]["questions"]["PROV_ROBIN_RULE"]["n_choices"] == 8
    assert result["descriptive"]["C0"]["questions"]["PROV_ROBIN_RULE"]["error_rate"] == 0
    assert result["descriptive"]["CONFLICT"]["questions"]["PROV_ROBIN_RULE"]["error_rate"] == 1
    assert result["paired_error_differences"]["PROV_ROBIN_RULE"]["error_rate_difference"] == 1
    assert result["paired_error_differences"]["PROV_ROBIN_RULE"]["error_difference_ci95"] == [1, 1]
    assert result["descriptive"]["CONFLICT"]["questions"]["PROV_ROBIN_RULE"]["candidate_choice_counts"]["d"] == 8
    reversed_rows = list(reversed(rows))
    assert vp.formal_summary(reversed_rows, ROLES, vp.MODEL_PROFILES[0], 4, n_boot=100) == result


def test_logit_shift_can_exist_without_new_error_choices():
    rows = records(vp.FORMAL_QIDS)
    for r in rows:
        if r["qid"] == "PROV_ROBIN_RULE":
            candidates = r["provenance"]["candidates"]["rule"]
            r["label_logits"][r["options"].index(candidates["r"])] = 20.0
    out = vp.formal_summary(rows, ROLES, vp.MODEL_PROFILES[0], 4, n_boot=20)
    assert out["primary"][0]["mean"] > 0
    assert out["descriptive"]["CONFLICT"]["questions"]["PROV_ROBIN_RULE"]["error_rate"] == 0


def certificate(profile):
    def item(name, p):
        return {"name": name, "available": True, "n": 600, "mean": 1.0, "sd": 1.0, "se": .1,
                "t": 10.0, "p_two_sided": p, "p_for_adjustment": p, "ci95_lo": .8, "ci95_hi": 1.2}
    return {"version": vp.VERSION, "model_profile": profile, "n_episodes": 600, "n_readouts": 43_200,
            "bootstrap_draws": 10_000, "bootstrap_seed": 0, "primary": [item("robin_rule_conflict", .02)],
            "secondary": [item(name, .01 + i * .02) for i, name in enumerate(vp.SECONDARY_NAMES)]}


def test_cross_model_holm_has_fixed_2_and_6_including_unavailable():
    inputs = {vp.MODEL_PROFILES[0]: certificate(vp.MODEL_PROFILES[0]), vp.MODEL_PROFILES[1]: None}
    out = vp.combine_formal(inputs)
    assert len(out["families"]["primary"]) == 2
    assert len(out["families"]["secondary"]) == 6
    assert out["families"]["primary"][0]["p_holm"] == .04
    for family in out["families"].values():
        assert [r["p_holm"] for r in family] == analyze.holm([r["p_for_adjustment"] for r in family])
        unavailable = [r for r in family if not r["available"]]
        assert all(r["p_for_adjustment"] == 1 and r["mean"] is None and r["n"] == 0 for r in unavailable)
    assert not out["pooled_episodes"]
    inputs[vp.MODEL_PROFILES[0]]["n_episodes"] = 599
    with pytest.raises(ValueError, match="600"):
        vp.combine_formal(inputs)


def config(phase="validity"):
    from mb.run import StageConfig
    from mb.model_profiles import resolve_profile
    base = phase == "base"
    arms = [ArmConfig("C0", layer=24, recipients=("A", "B") if base else ("A",)),
            ArmConfig("C0" if base else "ONE", layer=24, recipients=("A", "B") if base else ("A",),
                      interface="residual" if base else "kv", kv_scope=None if base else "P",
                      gain=0 if base else 1, donor_robin_conflict=True)]
    if not base:
        arms.insert(1, ArmConfig("ONE", layer=24, interface="kv", kv_scope="P", gain=1))
    from dataclasses import asdict
    stage = "v5_qwen_provenance_" + phase
    return StageConfig(stage=stage, tag="test", split=stage, n_episodes={"base": 60, "validity": 80, "confirm": 600}[phase],
                       arms=[asdict(a) for a in arms], model_profile=vp.MODEL_PROFILES[0],
                       episodes_per_batch=2, max_rows=16,
                       qids=list({"base": vp.BASELINE_QIDS, "validity": vp.ACCESS_QIDS, "confirm": vp.FORMAL_QIDS}[phase]),
                       post=[{"base": vp.POST_NAMES[0], "validity": vp.POST_NAMES[1], "confirm": vp.POST_NAMES[2]}[phase]],
                       params={"protocol": "v5", "provenance_contract": vp.VERSION,
                               "model_assets": {"path": str(resolve_profile(vp.MODEL_PROFILES[0]).manifest_path),
                                                "sha256": ledger.file_sha256(resolve_profile(vp.MODEL_PROFILES[0]).manifest_path)},
                               "roles": {role: arm.name for role, arm in zip(("C0", "CONFLICT") if base else ("C0", "KV", "CONFLICT"), arms)}})


def test_config_contract_and_identity_fail_closed(tmp_path):
    cfg = config()
    assert vp._validate_config(cfg, vp.POST_NAMES[1]) == cfg.params["roles"]
    cfg.qids.append("START")
    with pytest.raises(ValueError, match="question"):
        vp._validate_config(cfg, vp.POST_NAMES[1])
    cfg = config()
    (tmp_path / "identity.json").write_text(json.dumps({"stage_config": {}}))
    (tmp_path / "manifest.json").write_text(json.dumps({"smoke": False}))
    (tmp_path / "arm_hashes.json").write_text("{}")
    with pytest.raises(ValueError, match="identity"):
        vp._checked_records(tmp_path, cfg, {"status": "complete"})


@pytest.mark.parametrize("field,value", [("partner_frame", "third"), ("scram_seed", 7), ("layer", 18)])
def test_config_rejects_unplanned_arm_fields_even_with_matching_role_names(field, value):
    cfg = config()
    cfg.arms[1][field] = value
    cfg.params["roles"]["KV"] = cfg.arm_configs()[1].name
    with pytest.raises(ValueError, match="canonical fixed"):
        vp._validate_config(cfg, vp.POST_NAMES[1])


def test_raw_completeness_is_recomputed_not_claimed_by_status(tmp_path):
    from mb.model_profiles import resolve_profile
    from mb.run import source_hash
    cfg = config()
    profile = resolve_profile(cfg.model_profile)
    identity = {"stage_config": json.loads(json.dumps(cfg.resolved())), "limit": None,
                "source_hash": source_hash(), "template_hash": "fixture-template", "model_profile": profile.identity(), "model_revision": profile.revision,
                "tokenizer_manifest_sha": cfg.params["model_assets"]["sha256"]}
    (tmp_path / "identity.json").write_text(json.dumps(identity))
    (tmp_path / "manifest.json").write_text(json.dumps({"smoke": False}))
    (tmp_path / "arm_hashes.json").write_text(json.dumps({a.name: a.config_hash("none", "none", identity["template_hash"]) for a in cfg.arm_configs()}))
    result = vp.postprocess(tmp_path, cfg, {"status": "complete", "post_step": vp.POST_NAMES[1]})
    assert not result["consumable"] and result["gate"] == "unavailable"
    assert result["completeness"]["n_ok"] == 0 and "donor_own_access" not in result
    (tmp_path / "arm_hashes.json").write_text(json.dumps({a.name: "fabricated" for a in cfg.arm_configs()}))
    with pytest.raises(ValueError, match="registered arm hashes"):
        vp._checked_records(tmp_path, cfg, {"status": "complete"})


def test_complete_raw_roundtrip_and_consistent_forged_question_rejected(tmp_path):
    from mb.model_profiles import resolve_profile
    from mb.run import source_hash
    cfg = config()
    profile = resolve_profile(cfg.model_profile)
    identity = {"stage_config": json.loads(json.dumps(cfg.resolved())), "limit": None,
                "source_hash": source_hash(), "template_hash": "fixture-template", "model_profile": profile.identity(), "model_revision": profile.revision,
                "tokenizer_manifest_sha": cfg.params["model_assets"]["sha256"]}
    (tmp_path / "identity.json").write_text(json.dumps(identity))
    (tmp_path / "manifest.json").write_text(json.dumps({"smoke": False}))
    (tmp_path / "arm_hashes.json").write_text(json.dumps({a.name: a.config_hash("none", "none", identity["template_hash"]) for a in cfg.arm_configs()}))
    rows = records(vp.ACCESS_QIDS, n=80, split=cfg.split)
    names = {old: cfg.params["roles"][role] for role, old in ROLES.items()}
    for r in rows:
        r.update(arm=names[r["arm"]])
        r["config_hash"] = next(a.config_hash("none", "none", identity["template_hash"])
                                for a in cfg.arm_configs() if a.name == r["arm"])
    (tmp_path / "records").mkdir()
    shard = tmp_path / "records/attempt-000.jsonl"
    shard.write_text("".join(json.dumps(r) + "\n" for r in rows))
    before = shard.read_bytes()
    out = vp.postprocess(tmp_path, cfg, {"status": "complete", "post_step": vp.POST_NAMES[1]})
    assert out["consumable"] and out["gate"] == "pass"
    assert out["completeness"]["n_ok"] == 80 * 3 * 6 * 2
    assert shard.read_bytes() == before
    # Identical tampering across all arms defeats only-paired checks, but not rederivation.
    for r in rows:
        if r["qid"] == "PROV_DONOR_ROBIN_RULE":
            r["text_hash"] = "f" * 16
    shard.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="deterministic text"):
        vp.postprocess(tmp_path, cfg, {"status": "complete", "post_step": vp.POST_NAMES[1]})
