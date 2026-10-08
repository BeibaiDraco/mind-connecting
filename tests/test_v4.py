"""Scientific boundary cases for v4, without loading a model."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from mb import analyze, ledger, tasks, v4
from mb.conditions import ArmConfig

ROOT = Path(__file__).resolve().parents[1]


def script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summary(weight: float, **extra) -> dict:
    return {"arm": f"ONE/KV-P/w{weight:g}/FULL", "condition": "ONE", "interface": "kv", "kv_scope": "P",
            "layer": 21, "gain": weight, "n": 40, "acc_increment": 3.0, "acc_word_increment": 2.0,
            "cap_drop": 0.03, "label_mass": 0.96, "mass_drop": 0.03, "partner_rate": 0.4,
            "partner_rate_c0": 0.2, **extra}


def record(ep: str, arm: str, qid: str, side: str = "A", rot: int = 0, **extra) -> dict:
    meanings = ["own", "partner", "robin", "distractor" if "WORD" in qid else "unused"]
    target = "robin" if qid.endswith("_R") else "partner" if qid.startswith("ACC") else "own"
    if qid.startswith("CAP"):
        meanings, target = ["correct", "wrong1", "wrong2", "wrong3"], "correct"
    logits = [5.0 if meaning == target else 0.0 for meaning in meanings]
    spec = {"episode_id": ep, "arm": arm, "condition": arm.split("/")[0], "recipient": side,
            "qid": qid, "rotation_id": rot, "label_logits": logits, "label_meaning": meanings,
            "options": ["r-own", "r-original", "r-robin", "r-replacement"], "label_mass": 0.97,
            "status": "ok", "layer": 21, "gain": 0.0, "text_hash": f"{ep}:{qid}:{rot}"}
    return {**spec, **extra}


def baseline_records(n: int = 10) -> list[dict]:
    return [record(str(i), "C0/FULL", q, side, rot) for i in range(n) for side in ("A", "B")
            for q in v4.FORMAL_QIDS for rot in (0, 2)]


def test_strength_screens_all_criteria_before_maximum():
    rows = [summary(3, acc_increment=50, partner_rate=0.29), summary(2, acc_increment=20, cap_drop=0.06),
            summary(1, acc_increment=4), summary(0.5, acc_increment=4)]
    out = v4.select_strength(rows)
    assert out["gate"] == "pass" and out["selection"]["gain"] == 0.5
    assert len(out["candidates"]) == 4


@pytest.mark.parametrize("changes", [{"acc_increment": 0}, {"acc_increment": -1},
                                      {"partner_rate": 0.31, "partner_rate_c0": 0.22},
                                      {"label_mass": 0.89}, {"n": 39}, {"acc_increment": float("nan")}])
def test_strength_rejects_invalid_candidates(changes):
    assert v4.select_strength([summary(1, **changes)])["selection"] is None


def test_strength_inclusive_boundaries_and_no_attribution_inputs():
    row = summary(1, partner_rate=0.3, partner_rate_c0=0.2, cap_drop=0.05, mass_drop=0.05, label_mass=0.90)
    assert v4.select_strength([row])["gate"] == "pass"
    with pytest.raises(ValueError, match="only access"):
        v4.select_strength([{**row, "M": 100}])


def test_matching_positive_target_nearest_eligible_and_tie():
    target = summary(1, acc_increment=4)
    candidates = [summary(g, condition="STATIC", arm=f"static-{g}", interface="residual", kv_scope=None,
                          acc_increment=a, **kw) for g, a, kw in [(0.1, 3, {}), (0.2, 5, {}),
                                                                 (0.3, 4, {"cap_drop": 0.1})]]
    out = v4.select_static([target, *candidates], target["arm"])
    assert out["selection"]["gain"] == 0.1 and out["matched"]
    target["acc_increment"] = -4
    assert not v4.select_static([target, *candidates], target["arm"])["matched"]
    missing = v4.select_static([target], target["arm"])
    assert missing["selection"] is None and not missing["available"]


def test_matching_keeps_unmatched_nearest_instead_of_reselection():
    target = summary(1, acc_increment=1)
    static = summary(0.1, condition="STATIC", arm="static", acc_increment=5)
    out = v4.select_static([target, static], target["arm"])
    assert out["available"] and out["selection"]["gain"] == 0.1 and not out["matched"]


def test_baseline_does_not_hide_failing_side_or_cap_in_pooled_mean():
    records = baseline_records()
    assert v4.baseline_gate(records, 10)["gate"] == "pass"
    for r in records:
        if r["recipient"] == "B" and r["episode_id"] in ("0", "1") and r["qid"] == "START":
            r["label_logits"] = [0, 5, 0, 0]
    out = v4.baseline_gate(records, 10)
    assert out["sides"]["A"]["pass"] and not out["sides"]["B"]["pass"]
    assert out["sides"]["B"]["accuracy"]["START"] == 0.8
    records = baseline_records()
    for r in records:
        if r["recipient"] == "B" and r["episode_id"] in ("0", "1") and r["qid"].startswith("CAP"):
            r["label_logits"] = [0, 5, 0, 0]
    assert v4.baseline_gate(records, 10)["sides"]["B"]["CAP_ACC"] == 0.8
    assert v4.baseline_gate(records, 10)["gate"] == "fail"


def test_baseline_format_and_missing_ordering_fail():
    records = baseline_records()
    for r in records:
        if r["recipient"] == "B":
            r["label_mass"] = 0.89
    assert v4.baseline_gate(records, 10)["gate"] == "fail"
    assert v4.baseline_gate(baseline_records()[1:], 10)["gate"] == "fail"
    broken = baseline_records()
    broken[0]["label_mass"] = None
    with pytest.raises(ValueError, match="finite"):
        v4.baseline_gate(broken, 10)


def test_content_bound_uses_fixed_physical_options_and_is_strict():
    records = []
    for i in range(4):
        for rot in (0, 2):
            for qid in ("ACC_RULE", "ACC_WORD"):
                original = record(str(i), "ONE/KV-P/w1/FULL", qid, rot=rot)
                cf = record(str(i), "CF/KV-P/w1/FULL", qid, rot=rot,
                            label_logits=[0, 0, 0, 5], cf_r0_rule="r-original", cf_r1_rule="r-replacement",
                            cf_r0_word="r-original", cf_r1_word="r-replacement")
                records.extend((original, cf))
    out = v4.content_check(records, "ONE/KV-P/w1/FULL", "CF/KV-P/w1/FULL", 4, n_boot=100)
    assert out["rule"]["mean"] == 10 and out["rule"]["pass"]
    for r in records:
        if r["condition"] == "CF":
            r["label_logits"] = [0, 5, 0, 0]
    out = v4.content_check(records, "ONE/KV-P/w1/FULL", "CF/KV-P/w1/FULL", 4, n_boot=100)
    assert out["rule"]["lb95_one_sided"] == 0 and not out["rule"]["pass"]
    records[-1]["text_hash"] = "changed receiver question"
    with pytest.raises(ValueError, match="question text differs"):
        v4.content_check(records, "ONE/KV-P/w1/FULL", "CF/KV-P/w1/FULL", 4, n_boot=100)


def test_validity_separates_core_pass_from_unmatched_route_without_M():
    gen = script("make_v4_configs")
    arms, roles = gen.formal_arms(2, 0.1)
    cf1 = gen._kv(1, "CF")
    arms.append(cf1)
    roles["CF1"] = gen._name(cf1)
    records = []
    for i in range(4):
        for spec in arms:
            arm = ArmConfig(**spec)
            for qid in v4.ACCESS_QIDS:
                for rot in (0, 2):
                    r = record(str(i), arm.name, qid, rot=rot, gain=arm.gain,
                               interface=arm.interface, kv_scope=arm.kv_scope)
                    if qid.startswith("ACC"):
                        # K1 transfers less content than K*, but still passes its own validity.
                        access = 0 if arm.condition == "C0" else 8 if arm.condition == "STATIC" else arm.gain + 1
                        r["label_logits"] = [10, access, 0, 0]
                    if arm.condition == "CF":
                        r.update(cf_r0_rule="r-original", cf_r1_rule="r-replacement",
                                 cf_r0_word="r-original", cf_r1_word="r-replacement")
                        if qid.startswith("ACC"):
                            r["label_logits"] = [10, 0, 0, 5]
                    records.append(r)
    out = v4.validity_summary(records, roles, 4, n_boot=100)
    assert out["core_gate"] == "pass" and not out["route_validated"] and not out["matched"]
    assert out["K1_access"]["pass"] and out["content_K1"]["rule"]["pass"]
    assert all(not key.startswith("M") for key in out)
    with pytest.raises(ValueError, match="own independent"):
        v4.validity_summary(records, {k: val for k, val in roles.items() if k != "CF1"}, 4, n_boot=100)
    for r in records:
        if r["arm"] == roles["CF"] and r["qid"] == "ACC_RULE":
            r["label_logits"] = [10, 3, 0, 0]  # no response to the donor content change
    assert v4.validity_summary(records, roles, 4, n_boot=100)["core_gate"] == "fail"


def test_five_test_holm_includes_unavailable_without_imputed_effects():
    roles = {"C0": "base", "K*": "kv", "K1": "kv", "STATIC": None, "RF": "rf", "TAG": "tag", "UNTAG": "untag"}
    scores = pd.DataFrame([{"episode_id": str(i), "recipient": "A", "arm": arm, "M": value + 0.1 * i,
                            "M_NOW": value + 0.2 * i, "M_WORD": value + 0.3 * i}
                           for i in range(8) for arm, value in [("base", 0), ("kv", 1), ("rf", 0.2), ("tag", 0.1), ("untag", 0.5)]])
    out = v4.analyze_families(scores, roles, n_boot=100)
    assert len(out["primary"]) == 5 and len(out["secondary"]) == 4
    missing = out["primary"][1]
    assert not missing["available"] and missing["p_for_adjustment"] == 1 and missing["mean"] is None
    assert missing["p_two_sided"] is None and missing["n"] == 0
    expected = analyze.holm([r["p_for_adjustment"] for r in out["primary"]])
    assert [r["p_holm"] for r in out["primary"]] == expected
    zero = v4.analyze_families(scores.assign(M=0, M_NOW=0, M_WORD=0), roles, n_boot=100)
    assert zero["primary"][0]["p_two_sided"] == 1


def test_generator_deduplication_access_only_pilots_and_disjoint_splits():
    gen = script("make_v4_configs")
    assets = {"path": "manifest.json", "sha256": "a" * 64}
    initial = gen.build_configs("initial", assets)
    assert initial["base"]["arms"][0]["recipients"] == ["A", "B"]
    assert initial["smoke"]["params"]["smoke_only"]
    assert set(initial["strength"]["qids"]) == set(v4.ACCESS_QIDS)
    assert initial["cal"]["calibration_layers"] == [21]
    assert not any("signal" in post for cfg in initial.values() for post in cfg["post"])
    assert len(gen.formal_arms(1, 0.1)[0]) == 7
    assert len(gen.formal_arms(2, 0.1)[0]) == 8
    splits = gen.split_manifest()
    fingerprints = [x for s in splits["splits"].values() for x in s["fingerprints"]]
    assert len(fingerprints) == len(set(fingerprints)) == sum(gen.SPLITS.values())


def test_generator_failure_gates_and_frozen_unmatched_controls():
    gen = script("make_v4_configs")
    args = {"assets": {"path": "manifest.json", "sha256": "a" * 64},
            "baseline": {"consumable": True, "gate": "pass"}, "calibration": "/gpu/calibration_L21.pt",
            "calibration_metadata": {"21": {"static_unusable": []}},
            "strength": {"consumable": True, "gate": "pass", "selection": {"gain": 2}},
            "match": {"consumable": True, "selection": {"gain": 0.1}, "matched": False}}
    validity = gen.build_configs("validity", **args)["validity"]
    assert validity["n_episodes"] == 80 and len(validity["arms"]) == 9  # CF-w1 is validity-only
    assert set(validity["qids"]) == set(v4.ACCESS_QIDS)
    with pytest.raises(ValueError, match="independent"):
        gen.build_configs("confirm", **args)
    passed = {"consumable": True, "core_gate": "pass", "route_validated": False}
    formal = gen.build_configs("confirm", **args, validity=passed)["confirm"]
    assert formal["n_episodes"] == 600 and len(formal["arms"]) == 8
    assert not formal["params"]["route_validated"] and "CF1" not in formal["params"]["roles"]
    args["match"]["selection"] = None
    formal = gen.build_configs("confirm", **args, validity=passed)["confirm"]
    assert formal["params"]["roles"]["STATIC"] is None and len(formal["arms"]) == 7
    args["baseline"]["gate"] = "fail"
    with pytest.raises(ValueError, match="baseline"):
        gen.build_configs("validity", **args)


def test_generator_refuses_unusable_calibration_direction():
    gen = script("make_v4_configs")
    with pytest.raises(ValueError, match="direction unavailable"):
        gen.build_configs("match", {}, baseline={"consumable": True, "gate": "pass"}, calibration="cal.pt",
                          strength={"consumable": True, "gate": "pass", "selection": {"gain": 1}},
                          calibration_metadata={"21": {"static_unusable": ["raw:fastest"]}})


def test_generator_requires_strength_before_matching_and_assets_before_writes(tmp_path, monkeypatch):
    gen = script("make_v4_configs")
    with pytest.raises(ValueError, match="strength"):
        gen.build_configs("match", {}, baseline={"consumable": True, "gate": "pass"})
    from mb.model_profiles import ModelProfile

    def unavailable(self):
        raise FileNotFoundError("verified official assets missing")

    monkeypatch.setattr(ModelProfile, "validate_manifest", unavailable)
    monkeypatch.setattr("sys.argv", ["make_v4_configs.py", "initial", "--out", str(tmp_path / "configs")])
    with pytest.raises(FileNotFoundError, match="assets missing"):
        gen.main()
    assert not (tmp_path / "configs").exists()


def test_postprocess_recomputes_completeness_and_blocks_smoke(tmp_path):
    cfg = SimpleNamespace(n_episodes=60, split="v4_llama31_base", seed=0, qids=list(v4.FORMAL_QIDS),
                          all_rotations_first=0, post=["v4_baseline"], params={}, materials="v1",
                          model_profile="llama31_8b_instruct")
    cfg.arm_configs = lambda: [ArmConfig("C0", recipients=("A", "B"))]
    cfg.resolved = lambda: {"n_episodes": 60, "split": cfg.split}
    episodes = tasks.make_episodes(60, cfg.split)
    records = [record(ep.episode_id, "C0/FULL", qid, side, rot, config_hash="hash")
               for ep in episodes for side in ("A", "B") for qid in cfg.qids for rot in ep.rotations]
    (tmp_path / "identity.json").write_text(json.dumps({"stage_config": cfg.resolved(), "limit": None}))
    (tmp_path / "manifest.json").write_text(json.dumps({"smoke": False}))
    (tmp_path / "arm_hashes.json").write_text(json.dumps({"C0/FULL": "hash"}))
    (tmp_path / "records").mkdir()
    shard = tmp_path / "records" / "attempt-000.jsonl"
    shard.write_text("".join(json.dumps(r) + "\n" for r in records[1:]))
    out = v4.postprocess(tmp_path, cfg, {"status": "complete"})
    assert not out["consumable"] and "gate" not in out
    shard.write_text("".join(json.dumps(r) + "\n" for r in records))
    out = v4.postprocess(tmp_path, cfg, {"status": "complete"})
    assert out["consumable"] and out["gate"] == "pass"
    cfg.materials = "balanced"
    with pytest.raises(ValueError, match="original v1 materials"):
        v4.postprocess(tmp_path, cfg, {"status": "complete"})
    cfg.materials = "v1"
    (tmp_path / "manifest.json").write_text(json.dumps({"smoke": True}))
    out = v4.postprocess(tmp_path, cfg, {"status": "complete"})
    assert not out["consumable"] and "gate" not in out


def test_freeze_versions_and_phases_do_not_retarget_legacy_files():
    freeze = script("freeze_protocol")
    freeze.configure("v4", "algorithm")
    assert freeze.FREEZE.name == "FREEZE_protocol_v4_algorithm.txt"
    assert "v4_confirm" not in freeze.FORMAL_CONFIGS
    freeze.configure("v4", "settings")
    assert freeze.FREEZE.name == "FREEZE_protocol_v4_settings.txt" and "v4_validity" in freeze.FORMAL_CONFIGS
    freeze.configure("v4")
    assert freeze.FREEZE.name == "FREEZE_protocol_v4.txt" and "v4_confirm" in freeze.FORMAL_CONFIGS
    freeze.configure("v1")
    assert freeze.FREEZE.name == "FREEZE_protocol_v1.txt" and freeze.FORMAL_CONFIGS[0] == "main"
