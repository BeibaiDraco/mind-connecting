"""Model-aware run preparation and resume checks without torch or model execution."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

from mb import chat, ledger, model_profiles, run
from mb.model_profiles import LLAMA31, QWEN


def cfg(**changes):
    values = dict(stage="unit", tag="profile", split="unit_profile", n_episodes=2,
                  arms=[{"condition": "C0"}], qids=["START", "CAP0"])
    values.update(changes)
    return run.StageConfig(**values)


def config_file(root: Path, config: run.StageConfig) -> Path:
    path = root / "stage.yaml"
    path.write_text(yaml.safe_dump(dataclasses.asdict(config)))
    return path


def files(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer()


def test_legacy_stage_omits_new_identity_fields():
    config = cfg()
    resolved = config.resolved()
    assert "model_profile" not in resolved
    assert "model_profile" not in resolved["arms"][0]
    identity = run.build_identity(config, None, "template", {})
    assert "model_profile" not in identity and "c48_snapshot_contract" not in identity
    assert identity["model_revision"] == QWEN.revision


def test_model_profile_inherits_into_arms_and_rejects_conflicts():
    config = cfg(model_profile=LLAMA31.key, calibration_layers=[21])
    assert all(arm.model_profile == LLAMA31.key for arm in config.arm_configs())
    assert config.resolved()["arms"][0]["model_profile"] == LLAMA31.key
    with pytest.raises(ValueError, match="arm model_profile"):
        cfg(model_profile=LLAMA31.key, arms=[{"condition": "C0", "model_profile": QWEN.key}])
    with pytest.raises(ValueError, match="layer"):
        cfg(model_profile=LLAMA31.key, calibration_layers=[33])
    with pytest.raises(ValueError, match="layer"):
        cfg(model_profile=LLAMA31.key, arms=[{"condition": "C0", "layer": 33}])


def test_explicit_profile_pins_manifest_and_serializer(tmp_path, monkeypatch, tok):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    config = cfg(model_profile=QWEN.key)
    prepared = run.prepare_run(config, config_file(tmp_path, config), None, None, tok=tok)
    identity = prepared.identity
    assert identity["model_profile"] == QWEN.identity()
    assert identity["tokenizer_manifest_sha"] == ledger.file_sha256(QWEN.manifest_path)
    assert identity["chat_build"] == QWEN.serializer_version
    assert identity["c48_snapshot_contract"] == "shared-c48-sha256-v1"
    manifest = json.loads((prepared.run_dir / "manifest.json").read_text())
    assert manifest["model_profile"] == identity["model_profile"]
    assert manifest["template_hash"] == identity["template_hash"]
    before = files(prepared.run_dir)
    resumed = run.prepare_run(config, config_file(tmp_path, config), None, prepared.run_dir, tok=tok)
    assert resumed.resumed
    assert {k: v for k, v in files(prepared.run_dir).items() if k != "resume_log.jsonl"} == before


def test_changed_model_refuses_resume_before_any_write(tmp_path, monkeypatch, tok):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    config = cfg(model_profile=QWEN.key)
    prepared = run.prepare_run(config, config_file(tmp_path, config), None, None, tok=tok)
    before = files(prepared.run_dir)
    changed = cfg(model_profile=LLAMA31.key)
    # Synthetic routing test only; the public gated assets are unavailable offline.
    monkeypatch.setattr(model_profiles.ModelProfile, "validate_manifest", lambda self: {})
    monkeypatch.setattr(chat, "require_verified_tokenizer", lambda *args: None)
    monkeypatch.setattr(run, "template_hash", lambda *args: "different-model-template")
    monkeypatch.setattr(run, "prefix_hash", lambda *args: "different-model-prefix")
    monkeypatch.setattr(model_profiles.ModelProfile, "manifest_path", property(lambda self: QWEN_MANIFEST))
    with pytest.raises(SystemExit, match="resume refused"):
        run.prepare_run(changed, config_file(tmp_path, changed), None, prepared.run_dir,
                        allow_code_change=True, tok=tok)
    assert files(prepared.run_dir) == before


QWEN_MANIFEST = QWEN.manifest_path


def test_model_tokenizer_mismatch_fails_before_run_creation(tmp_path, monkeypatch, tok):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(model_profiles.ModelProfile, "validate_manifest", lambda self: {})
    config = cfg(model_profile=LLAMA31.key)
    with pytest.raises(ValueError, match="profiles differ"):
        run.prepare_run(config, config_file(tmp_path, config), None, None, tok=tok)
    assert not (tmp_path / "results").exists()


def test_manifest_and_prefix_changes_refuse_resume(tmp_path, monkeypatch, tok):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    config = cfg(model_profile=QWEN.key)
    prepared = run.prepare_run(config, config_file(tmp_path, config), None, None, tok=tok)
    before = files(prepared.run_dir)
    original_prefix = run.prefix_hash
    monkeypatch.setattr(run, "prefix_hash", lambda *args: "changed-native-template")
    with pytest.raises(SystemExit, match="resume refused"):
        run.prepare_run(config, config_file(tmp_path, config), None, prepared.run_dir,
                        allow_code_change=True, tok=tok)
    assert files(prepared.run_dir) == before
    monkeypatch.setattr(run, "prefix_hash", original_prefix)
    sha = ledger.file_sha256
    monkeypatch.setattr(ledger, "file_sha256", lambda path: "a" * 64 if Path(path) == QWEN_MANIFEST else sha(path))
    with pytest.raises(SystemExit, match="tokenizer_manifest_sha"):
        run.prepare_run(config, config_file(tmp_path, config), None, prepared.run_dir,
                        allow_code_change=True, tok=tok)
    assert files(prepared.run_dir) == before


def test_latest_calibration_is_scoped_to_profile_and_prefix(tmp_path, monkeypatch):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    for number, profile, prefix in ((1, LLAMA31, "matching"), (2, QWEN, "matching"),
                                     (3, LLAMA31, "different")):
        path = tmp_path / "results" / f"20261008-00000{number}_calibrate_test"
        path.mkdir(parents=True)
        (path / "calibration.json").write_text(json.dumps({"21": f"cal{number}.pt"}))
        (path / "manifest.json").write_text(json.dumps({"smoke": False}))
        (path / "run_status.json").write_text(json.dumps({"status": "complete"}))
        (path / "identity.json").write_text(json.dumps({"model_profile": profile.identity(),
                                                        "model_revision": profile.revision,
                                                        "prefix_hash": prefix}))
    assert run.resolve_calibration("latest", profile=LLAMA31.key, prefix="matching") == {21: "cal1.pt"}
    assert run.resolve_calibration("latest") == {21: "cal2.pt"}


def test_calibration_uses_profile_dimension_and_provenance(monkeypatch):
    current = {"model_revision": LLAMA31.revision, "model_profile": LLAMA31.identity(),
               "prefix_hash": "prefix", "tokenizer_manifest_sha": "assets", "hidden_size": 4096}
    cal = SimpleNamespace(layer=21, mu=np.zeros(4096), sd=np.ones(4096), static={})
    blob = {"meta": {**current, "smoke": False}}
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(load=lambda *args, **kwargs: blob, isfinite=np.isfinite))
    monkeypatch.setitem(sys.modules, "mb.bridge", SimpleNamespace(
        LayerCalibration=SimpleNamespace(from_state_dict=lambda value: cal)))
    assert run.load_calibration("synthetic.pt", 21, current, False)[0] is cal
    cal.mu = np.zeros(2560)
    with pytest.raises(SystemExit, match="shape"):
        run.load_calibration("synthetic.pt", 21, current, False)
    cal.mu = np.zeros(4096)
    blob["meta"]["model_profile"] = QWEN.identity()
    with pytest.raises(SystemExit, match="model_profile"):
        run.load_calibration("synthetic.pt", 21, current, False)
    blob["meta"]["model_profile"] = LLAMA31.identity()
    blob["meta"]["tokenizer_manifest_sha"] = "other-assets"
    with pytest.raises(SystemExit, match="tokenizer_manifest_sha"):
        run.load_calibration("synthetic.pt", 21, current, False)


def test_consumed_artifact_mutation_and_smoke_only_are_rejected(tmp_path, monkeypatch, tok):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    source = tmp_path / "selection.json"
    source.write_text('{"selected": 1}')
    config = cfg(params={"sources": {"selection": {"path": str(source), "sha256": ledger.file_sha256(source)}}})
    run.validate_stage_sources(config)
    source.write_text('{"selected": 2}')
    with pytest.raises(ValueError, match="source integrity"):
        run.prepare_run(config, config_file(tmp_path, config), None, None, tok=tok)
    assert not (tmp_path / "results").exists()
    smoke = cfg(params={"smoke_only": True})
    with pytest.raises(ValueError, match="requires --limit"):
        run.prepare_run(smoke, config_file(tmp_path, smoke), None, None, tok=tok)


def test_v4_post_dispatch_preserves_original_config(tmp_path, monkeypatch):
    config = cfg(post=["v4_strength", "v4_match"])
    (tmp_path / "manifest.json").write_text('{"smoke": false}')
    monkeypatch.setattr(run, "run_completeness", lambda path: {"status": "complete"})
    calls = []
    monkeypatch.setitem(sys.modules, "mb.v4", SimpleNamespace(
        postprocess=lambda path, config, status: calls.append((path, config, status)) or {"ok": True}))
    # Remove a previously loaded real module attribute so from mb import v4 uses this test double.
    import mb
    monkeypatch.delattr(mb, "v4", raising=False)
    assert run.run_post("v4_match", tmp_path, config) == {"ok": True}
    assert calls[0][1] is config
    assert calls[0][2]["post_step"] == "v4_match" and calls[0][2]["consumable"]


def test_calibration_blob_must_match_pinned_sidecar(tmp_path):
    blob = tmp_path / "calibration_L21.pt"
    blob.write_bytes(b"synthetic calibration bytes; no torch deserialization")
    sidecar = tmp_path / "calibration_metadata.json"
    sidecar.write_text(json.dumps({"21": {"path": str(blob), "file_sha256": ledger.file_sha256(blob)}}))
    config = cfg(calibration={"21": str(blob)}, params={"sources": {"calibration_metadata": {
        "path": str(sidecar), "sha256": ledger.file_sha256(sidecar)}}})
    run.validate_stage_sources(config)
    blob.write_bytes(b"different calibration with unchanged pinned metadata")
    with pytest.raises(ValueError, match="pinned calibration_metadata"):
        run.validate_stage_sources(config)
    with pytest.raises(ValueError, match="explicit calibration paths"):
        run.validate_stage_sources(dataclasses.replace(config, calibration="latest"))
