"""Torch-free model identity and asset-integrity tests; no model downloads."""

import hashlib
import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import pytest

from mb.conditions import ArmConfig
from mb.model_profiles import LLAMA31, QWEN, resolve_profile


def config_for(profile):
    return {"model_type": profile.model_type, "hidden_size": profile.hidden_size,
            "num_hidden_layers": profile.n_layers, "num_attention_heads": profile.n_heads,
            "num_key_value_heads": profile.n_kv_heads, "head_dim": profile.head_dim,
            "vocab_size": profile.vocab_size, "sliding_window": None}


def manifest_fixture(tmp_path, profile=LLAMA31):
    # These are dummy integrity-test assets, not usable native model/tokenizer files.
    files = {"config.json": config_for(profile), "generation_config.json": {},
             "tokenizer_config.json": {}, "tokenizer.json": {"test_only": True}}
    entries = {}
    for name, value in files.items():
        payload = json.dumps(value).encode()
        (tmp_path / name).write_bytes(payload)
        entries[name] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"repo_id": profile.repo_id, "revision": profile.revision,
                               "local_dir": str(tmp_path), "files": entries}))
    return path


def test_profiles_are_explicit_and_pinned():
    assert resolve_profile() == QWEN
    assert resolve_profile(LLAMA31.key) == LLAMA31
    assert LLAMA31.revision == "0e9e39f249a16976918f6564b8830bc894c89659"
    assert LLAMA31.n_layers == 32 and LLAMA31.hidden_size == 4096
    with pytest.raises(ValueError, match="unknown model profile"):
        resolve_profile("llama-latest")
    with pytest.raises(ValueError, match="registered pinned"):
        resolve_profile(replace(LLAMA31, revision="main"))


def test_manifest_checks_actual_bytes_and_revision(tmp_path):
    path = manifest_fixture(tmp_path)
    assert LLAMA31.validate_manifest(path, tmp_path)["revision"] == LLAMA31.revision
    (tmp_path / "tokenizer.json").write_text("changed")
    with pytest.raises(ValueError, match="integrity"):
        LLAMA31.validate_manifest(path, tmp_path)
    path = manifest_fixture(tmp_path)
    data = json.loads(path.read_text())
    data["revision"] = "main"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="pinned model profile"):
        LLAMA31.validate_manifest(path, tmp_path)


def test_manifest_requires_native_config_and_external_template(tmp_path):
    path = manifest_fixture(tmp_path)
    (tmp_path / "chat_template.jinja").write_text("untracked template")
    with pytest.raises(ValueError, match="external chat_template"):
        LLAMA31.validate_manifest(path, tmp_path)
    (tmp_path / "chat_template.jinja").unlink()
    data = json.loads(path.read_text())
    data["files"].pop("generation_config.json")
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="must include"):
        LLAMA31.validate_manifest(path, tmp_path)


@pytest.mark.parametrize("name", ["special_tokens_map.json", "added_tokens.json"])
def test_manifest_covers_optional_tokenizer_inputs(tmp_path, name):
    path = manifest_fixture(tmp_path)
    (tmp_path / name).write_text("{}")
    with pytest.raises(ValueError, match=name):
        LLAMA31.validate_manifest(path, tmp_path)


@pytest.mark.parametrize("change", [{"hidden_size": 2560}, {"num_hidden_layers": 36},
                                    {"num_key_value_heads": 4}, {"head_dim": 64},
                                    {"sliding_window": 4096}, {"quantization_config": {"bits": 4}}])
def test_architecture_mismatch_is_rejected(change):
    with pytest.raises(ValueError):
        LLAMA31.validate_model_config(config_for(LLAMA31) | change)


def test_layer_and_mask_limits_follow_profile():
    ArmConfig("ONE", gain=1, layer=32, model_profile=LLAMA31.key)
    ArmConfig("MASK", gain=.1, layer=21, k=4096, energy_mode="fixed", model_profile=LLAMA31.key)
    with pytest.raises(ValueError, match="1..32"):
        ArmConfig("ONE", gain=1, layer=33, model_profile=LLAMA31.key)
    with pytest.raises(ValueError, match="1..2560"):
        ArmConfig("MASK", gain=.1, k=4096, energy_mode="fixed")


def test_frozen_qwen_arm_hashes_are_unchanged():
    # Captured from the unmodified conditions.py at the pre-adapter HEAD.
    examples = [(ArmConfig("C0"), "9a1379cae61d8dce"),
                (ArmConfig("ONE", gain=.3), "0715af154eab3e45"),
                (ArmConfig("ONE", gain=1, interface="kv", kv_scope="P"), "687af6bff2e00ad3")]
    for arm, expected in examples:
        assert arm.config_hash("cal1", "none", "tmpl") == expected
        assert "model_profile" not in arm.identity("cal1", "none", "tmpl")
    other = ArmConfig("ONE", gain=1, interface="kv", kv_scope="P", model_profile=LLAMA31.key)
    assert other.config_hash("cal1", "none", "tmpl") != examples[-1][1]
    assert other.identity("cal1", "none", "tmpl")["model_revision"] == LLAMA31.revision


def fetch_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "fetch_model_assets.py"
    spec = importlib.util.spec_from_file_location("fetch_model_assets_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_weight_download_guard_requires_explicit_linux_gpu(monkeypatch):
    script = fetch_script()
    monkeypatch.setattr(script.platform, "system", lambda: "Darwin")
    with pytest.raises(ValueError, match="rented Linux GPU"):
        script.require_remote_gpu(True)
    monkeypatch.setattr(script.platform, "system", lambda: "Linux")
    with pytest.raises(ValueError, match="remote-gpu"):
        script.require_remote_gpu(False)
    monkeypatch.setattr(script.subprocess, "run", lambda *a, **k: type("Probe", (), {"stdout": ""})())
    with pytest.raises(ValueError, match="no NVIDIA GPU"):
        script.require_remote_gpu(True)


def test_fetch_does_not_bless_a_partial_directory(tmp_path, monkeypatch):
    from mb import model_profiles
    script = fetch_script()
    monkeypatch.setattr(model_profiles, "REPO_ROOT", tmp_path)
    LLAMA31.tokenizer_dir.mkdir(parents=True)
    (LLAMA31.tokenizer_dir / "tokenizer.json").write_text("fabricated")
    monkeypatch.setattr(script, "HfApi", lambda: pytest.fail("must inspect partial local state first"))
    with pytest.raises(FileNotFoundError):
        script.fetch_assets(LLAMA31)
    assert not LLAMA31.manifest_path.exists()


def test_cli_failure_does_not_print_authentication_details(monkeypatch, capsys):
    script = fetch_script()
    monkeypatch.setattr("sys.argv", ["fetch_model_assets.py"])
    def fail(profile):
        raise RuntimeError("Authorization: Bearer synthetic-test-secret")
    monkeypatch.setattr(script, "fetch_assets", fail)
    with pytest.raises(SystemExit) as exc:
        script.main()
    assert exc.value.code == 1
    stderr = capsys.readouterr().err
    assert "synthetic-test-secret" not in stderr
    assert "RuntimeError" in stderr and "no model was run" in stderr
