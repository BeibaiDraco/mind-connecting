"""Meaningful scientific and provenance boundaries for the bounded STATIC study."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from mb import ledger, model_profiles, tasks, v5_static as study
from mb.conditions import ArmConfig
from mb.run import StageConfig


def generator():
    spec = importlib.util.spec_from_file_location("make_v5_static", study.ROOT / "scripts" / "make_v5_static.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def summary(spec, access=0, **extra):
    a = ArmConfig(**spec)
    return {"arm": a.name, "condition": a.condition, "interface": a.interface, "kv_scope": a.kv_scope,
            "layer": a.layer, "gain": a.gain, "n": 40, "acc_increment": access,
            "acc_word_increment": 0.0, "cap_drop": 0.0, "label_mass": 0.99,
            "mass_drop": 0.0, "partner_rate": 0.4, "partner_rate_c0": 0.1, **extra}


def grid(layers=(16, 21, 27), target=4.0):
    return [summary(study.arm("C0")), summary(study.arm("ONE"), target),
            *[summary(study.arm("STATIC", l, g), 0.1) for l in layers for g in study.GAINS]]


def point(rows, layer, gain):
    return next(r for r in rows if r["condition"] == "STATIC" and r["layer"] == layer and r["gain"] == gain)


def test_matching_screens_quality_and_has_total_tie_order():
    rows = grid()
    point(rows, 16, 0.1)["acc_increment"] = 4
    point(rows, 21, 0.1)["acc_increment"] = 4
    point(rows, 27, 0.1)["acc_increment"] = 4
    point(rows, 16, 0.3).update(acc_increment=4, cap_drop=0.051)
    out = study.select(rows, study.LAYERS)
    assert out["gate"] == "matched" and out["selection"]["layer"] == 21
    point(rows, 21, 0.1)["cap_drop"] = 0.051
    assert study.select(rows, study.LAYERS)["selection"]["layer"] == 16


@pytest.mark.parametrize("target", [0, -1, float("nan"), float("inf")])
def test_nonpositive_nonfinite_target_stops_without_refinement(target):
    out = study.select(grid(target=target), study.LAYERS)
    assert out["gate"] == "stop" and out["next"] is None and out["selection"] is None


def test_selector_rejects_leakage_missing_duplicate_and_unplanned_points():
    rows = grid()
    for bad in ([*rows, rows[-1]], rows[1:], [*rows, summary(study.arm("STATIC", 16, 0.2), 4)]):
        with pytest.raises(ValueError, match="duplicate|complete prescribed"):
            study.select(bad, study.LAYERS)
    rows[-1]["M"] = 999
    with pytest.raises(ValueError, match="only access"):
        study.select(rows, study.LAYERS)
    rows = grid()
    rows[-1]["n"] = 39
    with pytest.raises(ValueError, match="incomplete"):
        study.select(rows, study.LAYERS)


def test_refinement_quality_barrier_and_exhaustion():
    rows = grid((21,))
    point(rows, 21, 0.3)["acc_increment"] = 2
    point(rows, 21, 0.5)["acc_increment"] = 6
    point(rows, 21, 0.7)["cap_drop"] = 0.1
    first = study.select(rows, [21])
    assert first["next"] == {"layer": 21, "gain": 0.4, "bracket": [0.3, 0.5]}
    rows.append(summary(study.arm("STATIC", 21, 0.4), 4, mass_drop=0.051))
    out = study.select(rows, [21], [{"layer": 21, "gain": 0.4}])
    assert out["gate"] == "stop"  # neither endpoint may skip the ineligible midpoint
    rows[-1].update(acc_increment=2, mass_drop=0)
    out = study.select(rows, [21], [{"layer": 21, "gain": 0.4}])
    assert out["next"]["gain"] == 0.45
    rows.append(summary(study.arm("STATIC", 21, 0.45), 2))
    out = study.select(rows, [21], [{"layer": 21, "gain": 0.4}, {"layer": 21, "gain": 0.45}])
    assert out["gate"] == "stop" and out["reason"] == "two refinements exhausted"


def test_refinement_stops_on_match_and_cannot_select_runner_up():
    rows = grid((21,))
    point(rows, 21, 0.3)["acc_increment"] = 2
    point(rows, 21, 0.5)["acc_increment"] = 6
    rows.append(summary(study.arm("STATIC", 21, 0.4), 3))
    assert study.select(rows, [21], [{"layer": 21, "gain": 0.4}])["matched"]
    rows.append(summary(study.arm("STATIC", 21, 0.45), 4))
    with pytest.raises(ValueError, match="deterministic search"):
        study.select(rows, [21], [{"layer": 21, "gain": 0.4}, {"layer": 21, "gain": 0.45}])


def test_bracket_requires_positive_access_at_both_endpoints():
    rows = grid((21,))
    for row in rows[2:]:
        row["acc_increment"] = -1
    point(rows, 21, 0.5)["acc_increment"] = 6
    assert study.select(rows, [21])["gate"] == "stop"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


@pytest.fixture
def sources(tmp_path, monkeypatch):
    # A tiny sealed manifest stands in for assets; no tokenizer/model is loaded by these tests.
    monkeypatch.setattr(model_profiles, "REPO_ROOT", tmp_path)
    monkeypatch.setattr("mb.run.source_hash", lambda: "code")
    manifest = model_profiles.resolve_profile(study.PROFILE).manifest_path
    manifest.parent.mkdir()
    dump(manifest, {"repo_id": model_profiles.LLAMA31.repo_id, "revision": model_profiles.LLAMA31.revision})
    assets = study.pin(manifest)
    gen = generator()
    calrun = tmp_path / "cal"
    calrun.mkdir()
    cfg = StageConfig(**gen.config("cal", assets, {}))
    identity = fake_identity(cfg, assets)
    dump(calrun / "identity.json", identity)
    dump(calrun / "manifest.json", {"smoke": False})
    dump(calrun / "run_status.json", {"status": "complete"})
    metadata = {}
    for layer in study.LAYERS:
        blob = calrun / f"calibration_L{layer}.pt"
        blob.write_bytes(f"synthetic calibration for layer {layer}".encode())
        metadata[str(layer)] = {key: identity[key] for key in
                               ("model_profile", "model_revision", "tokenizer_manifest_sha", "prefix_hash", "template_hash")}
        metadata[str(layer)].update(split=study.PREFIX + "cal", n_episodes=60, smoke=False,
                                    run_dir=str(calrun), path=str(blob), file_sha256=ledger.file_sha256(blob),
                                    hash=f"cal{layer}", hidden_size=4096, static_unusable=[])
    dump(calrun / "calibration_metadata.json", metadata)
    return gen, assets, calrun, tmp_path


def fake_identity(cfg, assets, metadata=None):
    profile = model_profiles.resolve_profile(study.PROFILE)
    calibration = {}
    for layer, path in (cfg.calibration or {}).items():
        info = metadata[str(layer)]
        calibration[str(layer)] = {"path": path, "hash": info["hash"], "smoke": False,
                                   "file_sha256": info["file_sha256"]}
    return {"stage_config": json.loads(json.dumps(cfg.resolved())), "limit": None,
            "model_profile": profile.identity(), "model_revision": profile.revision,
            "tokenizer_manifest_sha": assets["sha256"], "cap_bank_hash": tasks.cap_bank_hash(),
            "source_hash": "code", "template_hash": "template", "prefix_hash": "prefix", "calibration": calibration}


def records_for(cfg, identity, access=None, cf_quality=True):
    access = access or {}
    records = []
    hashes = {a.name: a.config_hash(identity["calibration"][str(a.layer)]["hash"] if a.needs_calibration else
                                   "none", "none", identity["template_hash"]) for a in cfg.arm_configs()}
    for ep in tasks.make_episodes(cfg.n_episodes, cfg.split):
        for a in cfg.arm_configs():
            for qid in cfg.qids:
                for rot in ep.rotations:
                    question_ep = tasks.make_donor_variant(ep, "CF").donor_episode if a.condition == "CF" else ep
                    text, options, meanings, cap_id = tasks._question_body(question_ep, "A", qid, rot)
                    logits = [10.0 if m == "own" else access.get(a.name, 0.0) if m == "partner" else 0.0 for m in meanings]
                    if qid.startswith("CAP"):
                        logits = [10.0 if m == "correct" else 0.0 for m in meanings]
                        if not cf_quality and a.condition == "CF":
                            logits = [0.0 if m == "correct" else 10.0 for m in meanings]
                    extra = {}
                    if a.condition == "CF":
                        extra = dict(cf_r0_rule=ep.rule.B, cf_r1_rule=ep.rule.spare,
                                     cf_r0_word=ep.word.B, cf_r1_word=ep.word.spare)
                        if qid.startswith("ACC"):
                            logits = [10.0 if m == "own" else 4.0 if m == "partner" else 0.0 for m in meanings]
                    records.append({"episode_id": ep.episode_id, "arm": a.name, "condition": a.condition,
                                    "recipient": "A", "qid": qid, "rotation_id": rot,
                                    "label_logits": logits, "label_meaning": list(meanings), "label_mass": 0.99,
                                    "label_logprobs": [-1.0, -1.0, -1.0, -1.0],
                                    "options": list(options), "cap_item_id": cap_id,
                                    "split": cfg.split, "materials": "v1", "template_hash": identity["template_hash"],
                                    "model_revision": identity["model_revision"], "readout_mode": a.readout_mode,
                                    "message_form": a.form, "mask_hash": "none",
                                    "calibration_hash": identity["calibration"][str(a.layer)]["hash"] if a.needs_calibration else "none",
                                    "status": "ok", "layer": a.layer, "gain": a.gain,
                                    "interface": a.interface, "kv_scope": a.kv_scope,
                                    "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
                                    "config_hash": hashes[a.name], **extra})
    return records, hashes


def make_run(path, cfg_dict, assets, calrun, access=None, cf_quality=True):
    path.mkdir()
    cfg = StageConfig(**cfg_dict)
    identity = fake_identity(cfg, assets, json.loads((calrun / "calibration_metadata.json").read_text()))
    dump(path / "identity.json", identity)
    dump(path / "manifest.json", {"smoke": False})
    dump(path / "run_status.json", {"status": "complete"})
    records, hashes = records_for(cfg, identity, access, cf_quality)
    dump(path / "arm_hashes.json", hashes)
    (path / "records").mkdir()
    (path / "records" / "attempt-000.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    notes = [{"key": tasks.note_key(ep, role, "v1"), "episode_id": ep.episode_id, "role": role,
              "ids": [10, 20], "note": "test note", "n_tokens": 2}
             for ep in tasks.make_episodes(cfg.n_episodes, cfg.split) for role in tasks.ROLES]
    (path / "notes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in notes))
    out = study.postprocess(path, cfg, {"status": "complete"})
    return cfg, out


def matching_run(sources, name="match", refine=False):
    gen, assets, calrun, temp = sources
    _, cfg, _ = gen.prepare("match", assets, calibration_run=calrun)
    target = study.name(study.arm("ONE"))
    values = {target: 4.0}
    if refine:
        values[study.name(study.arm("STATIC", 21, 0.3))] = 2.0
        values[study.name(study.arm("STATIC", 21, 0.5))] = 6.0
        # Avoid a second equal bracket to the right of the high point.
        values[study.name(study.arm("STATIC", 21, 0.7))] = 6.0
        values[study.name(study.arm("STATIC", 21, 1.0))] = 6.0
    else:
        values[study.name(study.arm("STATIC", 21, 0.5))] = 4.0
    run = temp / name
    make_run(run, cfg, assets, calrun, values)
    return run


def test_generator_full_chain_and_four_arm_cf_quality(sources):
    gen, assets, calrun, temp = sources
    matchrun = matching_run(sources)
    phase, cfg_dict, _ = gen.prepare("next", assets, calibration_run=calrun, match_run=matchrun)
    assert phase == "validity" and len(cfg_dict["arms"]) == 4
    rr = cfg_dict["params"]["roles"]
    values = {rr["K1"]: 4.0, rr["STATIC"]: 4.0}
    cfg, out = make_run(temp / "validity", cfg_dict, assets, calrun, values)
    assert out["gate"] == "pass" and not out["equivalence_test"]
    phase, formal, _ = gen.prepare("confirm", assets, calibration_run=calrun, match_run=matchrun,
                                   validity_run=temp / "validity")
    assert phase == "confirm" and formal["n_episodes"] == 600 and len(formal["arms"]) == 3
    study.verify_config_contract(StageConfig(**formal))
    records, _ = records_for(cfg, fake_identity(cfg, assets, json.loads((calrun / "calibration_metadata.json").read_text())),
                             values, cf_quality=False)
    assert study.validity(records, cfg.params["selected"], 80, n_boot=100)["gate"] == "fail"


def test_midpoint_new_run_reuses_original_baseline_and_notes(sources):
    gen, assets, calrun, temp = sources
    matchrun = matching_run(sources, refine=True)
    phase, cfg, _ = gen.prepare("next", assets, calibration_run=calrun, match_run=matchrun)
    assert phase == "refine1" and len(cfg["arms"]) == 1 and cfg["arms"][0]["gain"] == 0.4
    assert cfg["split"] == study.PREFIX + "match"
    assert cfg["params"]["sources"]["reuse_notes"] == study.pin(matchrun / "notes.jsonl")
    _, out = make_run(temp / "refine1", cfg, assets, calrun, {study.name(cfg["arms"][0]): 4.0})
    assert out["matched"] and len(out["access_table"]) == 18
    phase, valid, _ = gen.prepare("next", assets, calibration_run=calrun, match_run=matchrun,
                                  refine_runs=[temp / "refine1"])
    assert phase == "validity" and valid["params"]["selected"]["gain"] == 0.4


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "nonfinite", "nonfinite_logprobs", "smoke", "wrongsplit", "tampered", "leakage"])
def test_source_rejection_uses_actual_records_and_identity(sources, corruption):
    gen, assets, calrun, temp = sources
    matchrun = matching_run(sources)
    shard = matchrun / "records" / "attempt-000.jsonl"
    lines = shard.read_text().splitlines()
    if corruption == "missing":
        shard.write_text("\n".join(lines[1:]) + "\n")
    elif corruption == "duplicate":
        shard.write_text("\n".join([*lines, lines[0]]) + "\n")
    elif corruption == "nonfinite":
        row = json.loads(lines[0])
        row["label_logits"][0] = None
        shard.write_text(json.dumps(row) + "\n" + "\n".join(lines[1:]) + "\n")
    elif corruption == "nonfinite_logprobs":
        row = json.loads(lines[0])
        row["label_logprobs"][0] = None
        shard.write_text(json.dumps(row) + "\n" + "\n".join(lines[1:]) + "\n")
    elif corruption == "leakage":
        row = json.loads(lines[0])
        row["qid"] = "START"
        shard.write_text(json.dumps(row) + "\n" + "\n".join(lines[1:]) + "\n")
    elif corruption == "smoke":
        dump(matchrun / "manifest.json", {"smoke": True})
    elif corruption == "wrongsplit":
        identity = json.loads((matchrun / "identity.json").read_text())
        identity["stage_config"]["split"] = "old_match"
        dump(matchrun / "identity.json", identity)
    else:
        blob = calrun / "calibration_L16.pt"
        blob.write_bytes(b"changed calibration contents")
    with pytest.raises(ValueError):
        gen.prepare("next", assets, calibration_run=calrun, match_run=matchrun)


def test_foreign_code_calibration_rejected_before_next_stage(sources):
    gen, assets, calrun, _ = sources
    identity = json.loads((calrun / "identity.json").read_text())
    identity["source_hash"] = "older code"
    dump(calrun / "identity.json", identity)
    with pytest.raises(ValueError, match="identity differs"):
        gen.prepare("match", assets, calibration_run=calrun)


def test_validation_failure_has_no_runner_up_or_new_batch(sources):
    gen, assets, calrun, temp = sources
    matchrun = matching_run(sources)
    _, cfg, _ = gen.prepare("next", assets, calibration_run=calrun, match_run=matchrun)
    rr = cfg["params"]["roles"]
    _, out = make_run(temp / "validity", cfg, assets, calrun, {rr["K1"]: 4.0, rr["STATIC"]: 0.1})
    assert out["gate"] == "fail"
    with pytest.raises(ValueError, match="validity failed"):
        gen.prepare("confirm", assets, calibration_run=calrun, match_run=matchrun, validity_run=temp / "validity")
    with pytest.raises(ValueError, match="no reselection"):
        gen.prepare("next", assets, calibration_run=calrun, match_run=matchrun, validity_run=temp / "validity")


def test_frozen_selected_and_calibration_sources_cannot_be_swapped(sources):
    gen, assets, calrun, temp = sources
    matchrun = matching_run(sources)
    _, cfg, _ = gen.prepare("next", assets, calibration_run=calrun, match_run=matchrun)
    cfg["params"]["selected"]["gain"] = 0.7
    with pytest.raises(ValueError, match="selected setting"):
        study.verify_config_contract(StageConfig(**cfg))
    _, cfg, _ = gen.prepare("next", assets, calibration_run=calrun, match_run=matchrun)
    cfg["params"]["sources"].pop("history_0_records_attempt-000.jsonl")
    with pytest.raises(ValueError, match="fingerprints"):
        study.verify_config_contract(StageConfig(**cfg))


def test_split_manifest_and_no_writes_without_verified_assets(tmp_path, monkeypatch):
    gen = generator()
    manifest = gen.split_manifest()
    values = [f for s in manifest["splits"].values() for f in s["fingerprints"]]
    assert len(values) == len(set(values)) == sum(study.SIZES.values())
    def missing(self):
        raise FileNotFoundError("official assets unavailable")
    monkeypatch.setattr(model_profiles.ModelProfile, "validate_manifest", missing)
    monkeypatch.setattr("sys.argv", ["make_v5_static.py", "initial", "--out", str(tmp_path / "out")])
    with pytest.raises(FileNotFoundError, match="assets unavailable"):
        gen.main()
    assert not (tmp_path / "out").exists()
