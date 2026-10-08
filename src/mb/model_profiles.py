"""Pinned model identities and torch-free asset checks.

Adding a profile does not certify its tokenizer or GPU runtime. New-model execution
also requires the actual hashed tokenizer assets and chat contract checks.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ASSETS = ("config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json")
OPTIONAL_TOKENIZER_ASSETS = ("chat_template.jinja", "special_tokens_map.json", "added_tokens.json")


@dataclass(frozen=True)
class ModelProfile:
    key: str
    repo_id: str
    revision: str
    model_type: str
    n_layers: int
    hidden_size: int
    n_heads: int
    n_kv_heads: int
    head_dim: int
    vocab_size: int
    serializer_version: str
    tokenizer_subdir: str
    manifest_name: str
    date_string: str | None = None

    @property
    def tokenizer_dir(self) -> Path:
        return REPO_ROOT / "materials" / self.tokenizer_subdir

    @property
    def manifest_path(self) -> Path:
        return REPO_ROOT / "materials" / self.manifest_name

    def identity(self) -> dict[str, Any]:
        return asdict(self)

    def validate_model_config(self, config: Mapping[str, Any] | Any) -> None:
        data = config if isinstance(config, Mapping) else vars(config)
        expected = {"model_type": self.model_type, "num_hidden_layers": self.n_layers,
                    "hidden_size": self.hidden_size, "num_attention_heads": self.n_heads,
                    "num_key_value_heads": self.n_kv_heads, "vocab_size": self.vocab_size}
        for field, value in expected.items():
            if data.get(field) != value:
                raise ValueError(f"{self.key}: {field} must be {value!r}, got {data.get(field)!r}")
        head_dim = data.get("head_dim", self.hidden_size // self.n_heads)
        if head_dim != self.head_dim:
            raise ValueError(f"{self.key}: unexpected head_dim {head_dim!r}")
        if data.get("sliding_window") is not None or data.get("use_sliding_window", False):
            raise ValueError("the current KV bridge requires a full, non-sliding cache")
        if data.get("quantization_config") is not None:
            raise ValueError("inference quantization is not part of the model profile")

    def validate_manifest(self, path: str | Path | None = None,
                          tokenizer_dir: str | Path | None = None) -> dict[str, Any]:
        """Check actual local assets before a new model can be instantiated.

        The manifest must be created from authorized official downloads at the
        pinned revision. This function verifies integrity, not download access.
        """
        manifest_path = Path(path) if path is not None else self.manifest_path
        data = json.loads(manifest_path.read_text())
        if data.get("repo_id") != self.repo_id or data.get("revision") != self.revision:
            raise ValueError("asset manifest does not match the pinned model profile")
        if not re.fullmatch(r"[0-9a-f]{40}", self.revision):
            raise ValueError("model revision must be a full commit SHA")
        root = Path(tokenizer_dir) if tokenizer_dir is not None else self.tokenizer_dir
        files = data.get("files", {})
        if not isinstance(files, dict) or not set(REQUIRED_ASSETS) <= files.keys():
            raise ValueError(f"asset manifest must include {REQUIRED_ASSETS}")
        for name, spec in files.items():
            if Path(name).name != name or name in (".", "..") or not isinstance(spec, dict):
                raise ValueError(f"invalid asset entry {name!r}")
            payload = (root / name).read_bytes()
            if len(payload) != spec.get("bytes") or hashlib.sha256(payload).hexdigest() != spec.get("sha256"):
                raise ValueError(f"asset integrity check failed: {name}")
        for name in OPTIONAL_TOKENIZER_ASSETS:
            if (root / name).exists() and name not in files:
                raise ValueError(f"external {name} must be included in the asset manifest")
        self.validate_model_config(json.loads((root / "config.json").read_text()))
        return data


QWEN = ModelProfile(
    "qwen3_4b_instruct_2507", "Qwen/Qwen3-4B-Instruct-2507",
    "cdbee75f17c01a7cc42f958dc650907174af0554", "qwen3", 36, 2560, 32, 8, 128, 151936,
    "chatml-v1", "tokenizer", "tokenizer_manifest.json")

# Revision and native template date checked against the official model API on 2026-10-08:
# https://huggingface.co/api/models/meta-llama/Llama-3.1-8B-Instruct
# Actual gated tokenizer/config assets still have to pass validate_manifest and chat validation.
LLAMA31 = ModelProfile(
    "llama31_8b_instruct", "meta-llama/Llama-3.1-8B-Instruct",
    "0e9e39f249a16976918f6564b8830bc894c89659", "llama", 32, 4096, 32, 8, 128, 128256,
    "llama31-native-v1", "tokenizer_llama31_8b_instruct", "tokenizer_llama31_8b_instruct_manifest.json",
    date_string="26 Jul 2024")

PROFILES = {profile.key: profile for profile in (QWEN, LLAMA31)}


def resolve_profile(value: str | ModelProfile | None = None) -> ModelProfile:
    if value is None:
        return QWEN
    if isinstance(value, ModelProfile):
        if PROFILES.get(value.key) != value:
            raise ValueError("only the registered pinned model profiles are supported")
        return value
    try:
        return PROFILES[value]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"unknown model profile {value!r}") from exc
