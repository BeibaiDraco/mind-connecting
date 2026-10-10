"""Boundary tests for named exceptions, raw evidence, migration and separate freezes."""
from __future__ import annotations

from copy import deepcopy
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from mb import ledger, provenance_tasks, run, tasks, v5_continuation as c, v5_provenance as prov


def module(name):
    spec = importlib.util.spec_from_file_location(name, c.ROOT / "scripts" / f"{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def quality(drop=0):
    return {"n": 80, "CAP_ACC": .946875 - drop, "cap_drop": drop, "label_mass": .99, "mass_drop": 0.}


def summary(study):
    if study == "provenance":
        return {"gate": "fail", "quality": {"C0": quality(), "KV": quality(.05625), "CONFLICT": quality(.05)},
                "donor_own_access": {"rule": {"pass": True}}, "donor_robin_specificity": {"rule": {"pass": True}}}
    return {"gate": "fail", "baseline": {"pass": True}, "matched": True, "K1_access": {"pass": True},
            "content_K1": {"rule": {"pass": True}}, "access_table": [dict(arm=arm, **quality(drop))
                for arm, drop in zip(c.static.roles(c.SELECTED, True).values(), (0, .0625, .01875, .059375))]}


@pytest.mark.parametrize("study", ["provenance", "static"])
def test_only_named_observed_failures_are_excepted(study):
    s = summary(study)
    result = c.named_exceptions(study, s)
    assert result["original_gate"] == "fail"
    assert result["retrospective_validation_pass"] is False
    assert result["new_general_cap_threshold"] is None
    rows = list(s["quality"].values()) if study == "provenance" else s["access_table"]
    rows[1]["cap_drop"] += .003125
    with pytest.raises(ValueError, match="unapproved"):
        c.named_exceptions(study, s)


@pytest.mark.parametrize("study", ["provenance", "static"])
@pytest.mark.parametrize("defect", ["format", "new_failure", "no_failure", "fake_pass", "nonfinite", "incomplete", "access"])
def test_exceptions_do_not_waive_other_requirements(study, defect):
    s = summary(study)
    rows = list(s["quality"].values()) if study == "provenance" else s["access_table"]
    if defect == "format": rows[1]["label_mass"] = .89
    elif defect == "new_failure": rows[0]["cap_drop"] = .07
    elif defect == "no_failure": rows[1]["cap_drop"] = .04
    elif defect == "fake_pass": s["gate"] = "pass"
    elif defect == "nonfinite": rows[1]["cap_drop"] = float("nan")
    elif defect == "incomplete": rows[1]["n"] = 79
    elif study == "provenance": s["donor_own_access"]["rule"]["pass"] = False
    else: s["matched"] = False
    with pytest.raises(ValueError):
        c.named_exceptions(study, s)


def evidence(study):
    inv = {} if study == "provenance" else {str(Path(c.RUNS["cal"]) / "calibration_metadata.json"): "a" * 64}
    return {"protocol": c.VERSION, "study": study, "inventory": inv,
            "admission": c.named_exceptions(study, summary(study))}


@pytest.mark.parametrize("study", ["provenance", "static"])
def test_config_yaml_and_json_roundtrip_preserves_fixed_collection(study):
    cfg = c.config_from_evidence(study, evidence(study), {"path": "evidence.json", "sha256": "b" * 64})
    assert cfg.post == [] and cfg.n_episodes == 600 and cfg.tag == "v5_continuation_" + study
    assert len(cfg.arm_configs()) == 3 and cfg.episodes_per_batch == 2 and cfg.max_rows == 16
    assert len(cfg.qids) == (12 if study == "provenance" else 10)
    for data in (json.loads(json.dumps(cfg.resolved())), yaml.safe_load(yaml.safe_dump(dataclasses.asdict(cfg)))):
        assert run.StageConfig(**data).resolved() == cfg.resolved()
    if study == "static":
        assert cfg.calibration == {"16": str(c.REMOTE_RESULTS / c.RUNS["cal"] / "calibration_L16.pt")}
        assert cfg.arm_configs()[2].layer == 16 and cfg.arm_configs()[2].gain == .5


def dump(path, value):
    path.write_text(json.dumps(value))


@pytest.fixture
def raw_run(tmp_path):
    cfg = c.config_from_evidence("provenance", evidence("provenance"), {"path": "unused", "sha256": "b" * 64})
    cfg.n_episodes = 2  # The raw checker is independent of the separately tested fixed-N config admission.
    identity = run.build_identity(cfg, None, "test-template", {}, prefix="test-prefix")
    hashes = {a.name: a.config_hash("none", "none", identity["template_hash"]) for a in cfg.arm_configs()}
    rows = []
    for ep in tasks.make_episodes(2, cfg.split, 0):
        for arm in cfg.arm_configs():
            for qid in cfg.qids:
                for rotation in ep.rotations:
                    text, options, meanings, cap = provenance_tasks.question_body(ep, "A", qid, rotation)
                    metadata = provenance_tasks.record_metadata(ep, "A", SimpleNamespace(qid=qid, options=options), arm.donor_robin_conflict)
                    rows.append({"episode_id": ep.episode_id, "arm": arm.name, "recipient": "A", "qid": qid,
                        "rotation_id": rotation, "status": "ok", "label_logits": [0., 1., 2., 3.],
                        "label_logprobs": [-4., -3., -2., -1.], "label_mass": .99,
                        "options": list(options), "label_meaning": list(meanings), "cap_item_id": cap,
                        "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16], "provenance": metadata,
                        "config_hash": hashes[arm.name], "split": cfg.split, "materials": "v1",
                        "condition": arm.condition, "interface": arm.interface, "kv_scope": arm.kv_scope,
                        "layer": arm.layer, "gain": arm.gain, "template_hash": identity["template_hash"],
                        "model_revision": identity["model_revision"], "readout_mode": arm.readout_mode,
                        "message_form": arm.form, "calibration_hash": "none", "mask_hash": "none"})
    dump(tmp_path / "identity.json", identity)
    dump(tmp_path / "arm_hashes.json", hashes)
    (tmp_path / "records").mkdir()
    shard = tmp_path / "records/attempt-000.jsonl"
    shard.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return tmp_path, cfg, identity, rows, shard


def test_raw_audit_does_not_write_or_require_a_gate_boolean(raw_run):
    path, cfg, _, rows, shard = raw_run
    before = shard.read_bytes()
    assert c.complete_records(path, cfg) == rows
    assert shard.read_bytes() == before
    assert not (path / "continuation_summary.json").exists()


@pytest.mark.parametrize("defect", ["missing", "duplicate", "nonfinite", "logprobs", "hash", "text", "truth", "extra", "truncated"])
def test_raw_audit_rejects_bad_sources(raw_run, defect):
    path, cfg, _, rows, shard = raw_run
    if defect == "missing": rows.pop()
    elif defect == "duplicate": rows.append(deepcopy(rows[0]))
    elif defect == "nonfinite": rows[0]["label_logits"][0] = None
    elif defect == "logprobs": rows[0]["label_logprobs"][0] = float("inf")
    elif defect == "hash": rows[0]["config_hash"] = "bad"
    elif defect == "text": rows[0]["text_hash"] = "bad"
    elif defect == "truth": rows[0]["provenance"]["expected_truth"] = "fake"
    elif defect == "extra": rows[0]["qid"] = "U"
    shard.write_text("".join(json.dumps(r) + "\n" for r in rows) + ('{"broken"' if defect == "truncated" else ""))
    with pytest.raises(ValueError):
        c.complete_records(path, cfg)


@pytest.mark.parametrize("defect", [None, "smoke", "source", "incomplete", "split"])
def test_historical_identity_requires_explicit_old_source_and_complete_non_smoke(raw_run, monkeypatch, defect):
    path, cfg, identity, _, _ = raw_run
    identity["source_hash"] = "old-frozen-source"
    monkeypatch.setattr(c, "native_hashes", lambda _: ("test-template", "test-prefix"))
    manifest = {k: identity[k] for k in ("model_profile", "tokenizer_manifest_sha", "template_hash", "prefix_hash")}
    manifest.update(smoke=False, stage=cfg.stage)
    (path / "config.yaml").write_text(yaml.safe_dump(dataclasses.asdict(cfg)))
    status = {"status": "complete"}
    if defect == "smoke": manifest["smoke"] = True
    elif defect == "source": identity["source_hash"] = run.source_hash()
    elif defect == "incomplete": status["status"] = "partial"
    elif defect == "split": identity["stage_config"]["split"] = "foreign"
    dump(path / "identity.json", identity)
    dump(path / "manifest.json", manifest)
    dump(path / "run_status.json", status)
    if defect is None:
        assert c.identity_contract(path, cfg, "old-frozen-source") == identity
    else:
        with pytest.raises(ValueError):
            c.identity_contract(path, cfg, "old-frozen-source")


def test_remote_source_mapping_and_tamper_fail_closed(tmp_path):
    file = tmp_path / "run/identity.json"
    file.parent.mkdir()
    file.write_text("original")
    pin = {"path": str(c.REMOTE_RESULTS / "run/identity.json"), "sha256": ledger.file_sha256(file)}
    assert c.check_pin(pin, tmp_path) == file
    file.write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        c.check_pin(pin, tmp_path)


def test_evidence_recomputed_and_configuration_cannot_change(tmp_path, monkeypatch):
    e = evidence("provenance")
    path = tmp_path / "evidence.json"
    dump(path, e)
    pin = {"path": str(path), "sha256": ledger.file_sha256(path)}
    cfg = c.config_from_evidence("provenance", e, pin)
    monkeypatch.setattr(c, "audit_history", lambda *_: deepcopy(e))
    assert c.verify_config_contract(cfg, results_root=tmp_path) == e
    cfg.arms[1]["gain"] = .5
    with pytest.raises(ValueError, match="fixed continuation"):
        c.verify_config_contract(cfg, results_root=tmp_path)
    cfg = c.config_from_evidence("provenance", e, pin)
    monkeypatch.setattr(c, "audit_history", lambda *_: {**e, "new_field": "foreign"})
    with pytest.raises(ValueError, match="does not reproduce"):
        c.verify_config_contract(cfg, results_root=tmp_path)


def test_generation_is_all_or_nothing_before_source_failure(tmp_path, monkeypatch):
    prep = module("prepare_v5_continuation")
    def rejected(*args):
        raise ValueError("missing historical source")
    monkeypatch.setattr(c, "prepare", rejected)
    with pytest.raises(ValueError, match="missing historical"):
        prep.prepare_all(tmp_path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_preflight_refuses_preexisting_formal_identity(tmp_path):
    prep = module("prepare_v5_continuation")
    cfg = c.config_from_evidence("provenance", evidence("provenance"), {"path": "unused", "sha256": "a" * 64})
    existing = tmp_path / "already"
    existing.mkdir()
    dump(existing / "identity.json", {"stage_config": cfg.resolved()})
    with pytest.raises(ValueError, match="already has a run"):
        prep.material_preflight(tmp_path, {"provenance": cfg})


def test_freeze_rejects_missing_source_and_wrong_protocol(tmp_path):
    freeze = module("freeze_v5_continuation")
    path = tmp_path / "freeze.json"
    dump(path, {"protocol": "v5", "kind": "stage", "files": {}})
    with pytest.raises(ValueError, match="not a continuation"):
        freeze.verify(path)
    dump(path, {"protocol": c.VERSION, "kind": "stage", "files": {str(tmp_path / "missing"): "a" * 64}})
    with pytest.raises(ValueError, match="missing"):
        freeze.verify(path)


def test_freeze_is_write_once(tmp_path):
    freeze = module("freeze_v5_continuation")
    path = tmp_path / "freeze.json"
    path.write_text("preserved")
    with pytest.raises(ValueError, match="already exists"):
        freeze.create("algorithm", path)
    assert path.read_text() == "preserved"


def test_external_analysis_keeps_original_qwen_outside_amended_family(tmp_path, monkeypatch):
    e = evidence("provenance")
    cfg = c.config_from_evidence("provenance", e, {"path": "unused", "sha256": "a" * 64})
    dump(tmp_path / "identity.json", {"stage_config": cfg.resolved()})
    calls = []
    monkeypatch.setattr(c, "verify_config_contract", lambda *a, **k: e)
    monkeypatch.setattr(c, "identity_contract", lambda *a: calls.append("identity"))
    monkeypatch.setattr(c, "complete_records", lambda *a: calls.append("raw") or ["verified-records"])
    synthetic = {"effect_sign": "negative-or-zero-is-not-a-stop"}
    monkeypatch.setattr(prov, "formal_summary", lambda *a: synthetic.copy())
    def combine(values):
        assert values[prov.MODEL_PROFILES[0]] is None
        assert values[c.LLAMA31.key] == synthetic
        calls.append("separate-family")
        return {"primary_family_size": 2, "secondary_family_size": 6}
    monkeypatch.setattr(prov, "combine_formal", combine)
    result = c.analyze_run(tmp_path)
    assert calls == ["identity", "raw", "separate-family"]
    assert result["consumable"] and result["gate"] == "pass"
    assert result["original_admission"]["original_gate"] == "fail"
    assert not (tmp_path / "continuation_summary.json").exists()


def test_external_analysis_never_scores_incomplete_raw_ledger(tmp_path, monkeypatch):
    e = evidence("provenance")
    cfg = c.config_from_evidence("provenance", e, {"path": "unused", "sha256": "a" * 64})
    dump(tmp_path / "identity.json", {"stage_config": cfg.resolved()})
    monkeypatch.setattr(c, "verify_config_contract", lambda *a, **k: e)
    monkeypatch.setattr(c, "identity_contract", lambda *a: None)
    def fail(*args):
        raise ValueError("raw ledger incomplete")
    monkeypatch.setattr(c, "complete_records", fail)
    monkeypatch.setattr(prov, "formal_summary", lambda *a: pytest.fail("must not score incomplete run"))
    with pytest.raises(ValueError, match="incomplete"):
        c.analyze_run(tmp_path)


def test_freeze_admits_only_original_llama_smoke(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(c.ROOT / "scripts"))
    generator = module("make_v5_provenance")
    freeze = module("freeze_v5_continuation")
    cfg = run.StageConfig(**generator.build_config("llama31", "smoke"))
    freeze.validate_config(cfg)
    cfg.arms[1]["gain"] = .5
    with pytest.raises(ValueError, match="frozen provenance"):
        freeze.validate_config(cfg)
    cfg = run.StageConfig(**generator.build_config("qwen", "smoke"))
    with pytest.raises(ValueError, match="only explicit"):
        freeze.validate_config(cfg)
