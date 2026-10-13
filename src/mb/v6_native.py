"""Isolated native backend for v6 local preparation, not a certified runner.

Importing this module needs no torch. Construction and weight loading require an
explicit hardware-acceptance authorization; loading is local-cache-only. The
legacy runtime and its attention context are never imported or modified.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import math
import threading
from dataclasses import dataclass, field
from typing import Any

from mb.model_profiles import QWEN, resolve_profile
from mb.v6_contract import Export, Probe, canonical_digest

ATTENTION_NAME = "mb_v6_isolated_kv"
STATUS = "draft_local_only_hardware_acceptance_required"
RECOVERY_VERSION = "v6-native-recovery-draft-1"
ARCHIVE_VERSION = "v6-native-archive-draft-1"
_FORWARD: contextvars.ContextVar[Any] = contextvars.ContextVar("mb_v6_forward", default=None)


@dataclass(frozen=True)
class Recovery:
    """Tokens appended AFTER consuming the actual answer, never an answer replacement."""

    category: str
    suffix: tuple[int, ...]


@dataclass
class NativeTokens:
    tokenizer: Any = field(repr=False)
    profile_key: str
    vocab_size: int
    close_ids: tuple[int, ...]
    control_ids: frozenset[int]
    defined_ids: frozenset[int]
    rules: dict[int, Recovery] = field(repr=False)

    @classmethod
    def from_tokenizer(cls, tok: Any) -> "NativeTokens":
        from mb import chat

        profile = chat.profile_for_tokenizer(tok)
        close = tuple(chat.close(tok))
        defined = frozenset(tok.get_vocab().values())
        # Qwen's tool/think/FIM controls are added tokens without special=True.
        names = {int(i): str(v) for i, v in tok.added_tokens_decoder.items()}
        controls = frozenset(set(names) | set(tok.all_special_ids))
        if not close or close[0] not in controls:
            raise ValueError("Unrecognized native end-of-turn contract")
        rules: dict[int, Recovery] = {}
        for token in controls:
            name = names.get(token, tok.convert_ids_to_tokens(token))
            if token == close[0]:
                rule = Recovery("native_end_of_turn", close[1:])
            elif profile == QWEN and name == "<|im_start|>":
                rule = Recovery("header_start", tuple(chat.encode(tok, "assistant\n")) + close)
            elif profile != QWEN and name == "<|start_header_id|>":
                rule = Recovery("header_start", tuple(chat.encode(tok, "assistant<|end_header_id|>\n\n")) + close)
            elif profile != QWEN and name == "<|end_header_id|>":
                rule = Recovery("header_end", tuple(chat.encode(tok, "\n\n")) + close)
            elif name in {"<|endoftext|>", "<|end_of_text|>", "<|eom_id|>"}:
                rule = Recovery("alternate_end_or_handoff", close)
            elif ((profile == QWEN and name in {
                    "<|object_ref_start|>", "<|object_ref_end|>", "<|box_start|>", "<|box_end|>",
                    "<|quad_start|>", "<|quad_end|>", "<|vision_start|>", "<|vision_end|>",
                    "<|vision_pad|>", "<|image_pad|>", "<|video_pad|>", "<tool_call>",
                    "</tool_call>", "<|fim_prefix|>", "<|fim_middle|>", "<|fim_suffix|>",
                    "<|fim_pad|>", "<|repo_name|>", "<|file_sep|>", "<tool_response>",
                    "</tool_response>", "<think>", "</think>"})
                  or (profile != QWEN and (name in {
                    "<|begin_of_text|>", "<|finetune_right_pad_id|>", "<|python_tag|>"}
                    or (isinstance(name, str) and name.startswith("<|reserved_special_token_")
                        and name.endswith("|>"))))):
                rule = Recovery("named_control_or_reserved", close)
            else:
                raise ValueError(f"Unsupported native control token: {name!r}")
            rules[token] = rule
        if not defined or min(defined) < 0 or max(defined) >= profile.vocab_size:
            raise ValueError("Tokenizer vocabulary differs from pinned output vocabulary")
        obj = cls(tok, profile.key, profile.vocab_size, close, controls, defined, rules)
        # Assert the complete public native assembly, including exactly one BOS.
        sample = [{"role": "system", "content": "System record."},
                  {"role": "user", "content": "Private record."}]
        if obj.initial(sample[0]["content"], sample[1]["content"]) != tuple(
                chat.native_conversation(tok, sample, add_generation_prompt=True)):
            raise ValueError("Initial native serialization differs from the official template")
        obj.choice_ids(("1", "2", "3", "4"))
        return obj

    def initial(self, system: str, user: str) -> tuple[int, ...]:
        from mb import chat
        self._content(system)
        self._content(user)
        return tuple(chat.turn(self.tokenizer, "system", system)
                     + chat.turn(self.tokenizer, "user", user) + chat.header(self.tokenizer))

    def user_turn(self, text: str) -> tuple[int, ...]:
        from mb import chat
        self._content(text)
        return tuple(chat.turn(self.tokenizer, "user", text) + chat.header(self.tokenizer))

    def _content(self, text: str) -> None:
        from mb import chat

        if not isinstance(text, str) or any(i in self.control_ids for i in chat.encode(self.tokenizer, text)):
            raise ValueError("Native message content must not inject control-token spellings")

    def choice_ids(self, labels: tuple[str, str, str, str]) -> tuple[int, int, int, int]:
        from mb import chat

        if len(labels) != 4 or len(set(labels)) != 4:
            raise ValueError("Four distinct choice labels required")
        ids = [chat.encode(self.tokenizer, label) for label in labels]
        if any(len(x) != 1 or not self.ordinary(x[0]) for x in ids):
            raise ValueError("Choice labels must each be a single ordinary token")
        prefix = self.initial("System record.", "Choose one ID.")
        rendered = self.tokenizer.decode(prefix, skip_special_tokens=False,
                                         clean_up_tokenization_spaces=False)
        for label, token in zip(labels, ids):
            if chat.encode(self.tokenizer, rendered + label) != [*prefix, *token]:
                raise ValueError("Choice label does not append after the native answer prefix")
        answer = tuple(x[0] for x in ids)
        if len(set(answer)) != 4:
            raise ValueError("Choice labels map to duplicate tokens")
        return answer

    def ordinary(self, token: int) -> bool:
        return token in self.defined_ids and token not in self.control_ids

    def recovery(self, token: int) -> Recovery:
        if isinstance(token, bool) or not isinstance(token, int) or not 0 <= token < self.vocab_size:
            raise ValueError("Answer token is outside the pinned model vocabulary")
        if token in self.rules:
            return self.rules[token]
        if token not in self.defined_ids:
            # Padded output-vocabulary IDs are still actual model outputs. Their
            # raw IDs remain in the history; no tokenizer decoding is invented.
            return Recovery("unassigned_output_id", self.close_ids)
        return Recovery("ordinary_answer", self.close_ids)

    def identity(self) -> dict[str, Any]:
        return {"version": RECOVERY_VERSION, "status": STATUS, "profile": self.profile_key,
                "vocab_size": self.vocab_size, "close_ids": list(self.close_ids),
                "defined_ids_sha256": canonical_digest(sorted(self.defined_ids)),
                "control_rules": {str(k): {"category": v.category, "suffix": list(v.suffix)}
                                  for k, v in sorted(self.rules.items())},
                "ordinary_suffix": list(self.close_ids),
                "unassigned_output_suffix": list(self.close_ids)}


def _tensor_stamp(tensor: Any) -> tuple[Any, ...]:
    return (tensor.data_ptr(), tensor._version, tuple(tensor.shape), str(tensor.dtype), str(tensor.device))


def _primitives(value: Any) -> Any:
    """Copy JSON primitives without admitting custom objects to a tensor archive."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) in (tuple, list):
        return [_primitives(x) for x in value]
    if type(value) is dict and all(type(k) is str for k in value):
        return {k: _primitives(v) for k, v in value.items()}
    raise ValueError("Archive metadata must contain finite plain primitives only")


def _hex_digest(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _tensor_hash(metadata: Any, tensors: tuple[Any, ...]) -> str:
    """One bounded payload transfer for small exports; streamed transfer for full state."""
    import torch

    digest = hashlib.sha256(json.dumps(metadata, sort_keys=True, allow_nan=False).encode())
    for tensor in tensors:
        shape = json.dumps([list(tensor.shape), str(tensor.dtype)], separators=(",", ":")).encode()
        digest.update(len(shape).to_bytes(8, "big")); digest.update(shape)
    # Export records contain at most a few hundred KiB; state caches may be large.
    pending, size = [], 0
    for tensor in tensors:
        raw = tensor.detach().contiguous().reshape(-1).view(torch.uint8)
        for part in raw.split(4 * 1024 * 1024):
            if size + part.numel() > 4 * 1024 * 1024 and pending:
                digest.update(torch.cat(pending).cpu().numpy().tobytes())
                pending, size = [], 0
            pending.append(part); size += part.numel()
    if pending:
        digest.update(torch.cat(pending).cpu().numpy().tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class NativeKVPayload:
    """Owned copies, never views of a sender cache. Caller must not write tensors."""

    layers: tuple[tuple[Any, Any], ...] = field(repr=False)
    token: int
    position: int
    model_identity: str
    digest: str
    stamps: tuple[tuple[Any, ...], ...] = field(repr=False)
    owner: Any = field(repr=False, compare=False)

    def check(self, export: Export, model_identity: str, owner: Any) -> None:
        if (export.token, export.position, export.digest) != (self.token, self.position, self.digest):
            raise ValueError("Export metadata differs from its native payload")
        if self.model_identity != model_identity or self.owner is not owner:
            raise ValueError("Foreign K/V belongs to a different model/tokenizer")
        tensors = tuple(t for layer in self.layers for t in layer)
        if tuple(_tensor_stamp(t) for t in tensors) != self.stamps:
            raise ValueError("An immutable exported K/V tensor was modified")


@dataclass
class NativeState:
    cache: Any = field(repr=False)
    consumed_tokens: tuple[int, ...]
    native_logits: Any = field(repr=False)
    last_hidden: Any = field(repr=False)
    open: bool
    model_identity: str
    recoveries: tuple[dict[str, Any], ...] = ()
    failed: bool = False
    seal: dict[str, Any] | None = None
    seal_checksum: str | None = field(default=None, repr=False)
    owner: Any = field(default=None, repr=False, compare=False)


@dataclass
class _AttentionContext:
    modules: dict[int, int]
    layers: tuple[tuple[Any, Any], ...]
    gain: float
    seen: set[int] = field(default_factory=set)


def _attention(module: Any, query: Any, key: Any, value: Any, attention_mask: Any,
               dropout: float = 0.0, scaling: float | None = None,
               is_causal: bool | None = None, **kwargs: Any) -> tuple[Any, Any]:
    import torch
    from transformers.integrations.sdpa_attention import sdpa_attention_forward

    output, weights = sdpa_attention_forward(module, query, key, value, attention_mask,
        dropout=dropout, scaling=scaling, is_causal=is_causal, **kwargs)
    ctx = _FORWARD.get()
    if ctx is None:
        return output, weights
    index = ctx.modules.get(id(module))
    if index is None or index in ctx.seen:
        raise RuntimeError("Unexpected/repeated attention module in v6 forward")
    ctx.seen.add(index)
    if not ctx.layers or ctx.gain == 0:
        return output, weights
    if query.shape[0] != 1 or query.shape[2] != 1 or dropout:
        raise RuntimeError("Foreign attention requires one inference token in one history")
    foreign_k, foreign_v = ctx.layers[index]
    heads, kv_heads, dim = query.shape[1], key.shape[1], query.shape[-1]
    if heads % kv_heads or foreign_k.shape[:2] != key.shape[:2] or foreign_k.shape[-1] != dim:
        raise RuntimeError("Foreign K/V head dimensions differ")
    q = query.float().view(1, kv_heads, heads // kv_heads, 1, dim)
    scale = scaling if scaling is not None else dim ** -0.5
    own_logits = torch.matmul(q, key.float().unsqueeze(2).transpose(-1, -2)) * scale
    if attention_mask is not None:
        if attention_mask.ndim != 4:
            raise RuntimeError("Unsupported native attention mask rank")
        mask = attention_mask[..., -1:, :key.shape[-2]]
        if mask.shape[1] not in (1, heads):
            raise RuntimeError("Unsupported native attention mask heads")
        mask = mask.expand(1, heads, 1, key.shape[-2]).reshape(1, kv_heads, heads // kv_heads, 1, -1)
        own_logits = (own_logits.masked_fill(~mask, -math.inf) if mask.dtype == torch.bool
                      else own_logits + mask.float())
    foreign_logits = torch.matmul(q, foreign_k.float().unsqueeze(2).transpose(-1, -2)) * scale
    foreign_logits = foreign_logits + math.log(ctx.gain)
    own_lse = torch.logsumexp(own_logits, dim=-1, keepdim=True)
    foreign_lse = torch.logsumexp(foreign_logits, dim=-1, keepdim=True)
    beta = torch.sigmoid(foreign_lse - own_lse)
    foreign_out = torch.matmul(torch.softmax(foreign_logits, dim=-1), foreign_v.float().unsqueeze(2))
    own_out = output.transpose(1, 2).float().view(1, kv_heads, heads // kv_heads, 1, dim)
    mixed = own_out + beta * (foreign_out - own_out)
    return mixed.view(1, heads, 1, dim).transpose(1, 2).to(output.dtype), weights


class NativeBackend:
    """Single-model, single-history forwards; callers schedule the paired barrier.

    Supplied tiny random models are useful for hardware engineering tests. Only
    ``from_local_cache`` additionally verifies the pinned scientific architecture.
    Neither constructor confers a passed acceptance certificate or a formal mode.
    """

    status = STATUS

    def __init__(self, model: Any, tokenizer: Any, *, hardware_acceptance_authorized: bool = False):
        if hardware_acceptance_authorized is not True:
            raise PermissionError("Explicit hardware-acceptance authorization required")
        import torch
        from transformers import AttentionInterface
        from transformers.masking_utils import AttentionMaskInterface, sdpa_mask

        self.tokens = NativeTokens.from_tokenizer(tokenizer)
        self.model, self.tokenizer = model, tokenizer
        self.device = next(model.parameters()).device
        if self.device.type != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("The native v6 backend may run only on an authorized CUDA host")
        cfg = model.config
        if (cfg.model_type not in {"qwen3", "llama"} or getattr(cfg, "sliding_window", None)
                or getattr(cfg, "use_sliding_window", False) or getattr(cfg, "quantization_config", None)):
            raise ValueError("Only full-cache, unquantized Qwen/Llama models are supported")
        if cfg.model_type != resolve_profile(self.tokens.profile_key).model_type:
            raise ValueError("Model family differs from the native tokenizer")
        if cfg.vocab_size != self.tokens.vocab_size:
            raise ValueError("Model output vocabulary differs from the tokenizer profile")
        if any(p.device != self.device for p in model.parameters()):
            raise ValueError("Model sharding/offload is outside this backend")
        if not hasattr(model, "model") or not hasattr(model, "lm_head"):
            raise ValueError("Unsupported causal-LM architecture")
        self.modules = {id(layer.self_attn): i for i, layer in enumerate(model.model.layers)}
        if len(self.modules) != cfg.num_hidden_layers:
            raise ValueError("Unexpected attention layer count")
        self._configs = list({id(c): c for c in [cfg, *[layer.self_attn.config for layer in model.model.layers]]}.values())
        if any(getattr(c, "_attn_implementation", "sdpa") not in {"sdpa", "eager"} for c in self._configs):
            raise ValueError("Use an unhooked native model, not the legacy bridged runtime")
        # A config/revision label alone cannot distinguish different random or
        # modified weights. This bounded one-time hash is part of acceptance cost.
        params = tuple(model.named_parameters())
        self.weights_digest = _tensor_hash({"names": [name for name, _ in params]},
                                           tuple(p for _, p in params))
        self.model_identity = canonical_digest({"config": cfg.to_dict(), "tokens": self.tokens.identity(),
                                                "weights_sha256": self.weights_digest})
        self._owner = object()
        self._lock = threading.RLock()
        self._w32 = None
        self._forbidden = torch.tensor(sorted(set(range(cfg.vocab_size)) - (
            self.tokens.defined_ids - self.tokens.control_ids)), device=self.device, dtype=torch.long)
        model.eval()
        AttentionInterface.register(ATTENTION_NAME, _attention)
        AttentionMaskInterface.register(ATTENTION_NAME, sdpa_mask)

    @classmethod
    def from_local_cache(cls, *, profile: str | None = None,
                         hardware_acceptance_authorized: bool = False) -> "NativeBackend":
        if hardware_acceptance_authorized is not True:
            raise PermissionError("Explicit hardware-acceptance authorization required")
        from mb import chat
        selected = resolve_profile(profile)
        selected.validate_manifest()
        tok = chat.load_tokenizer(profile=selected)
        chat.require_verified_tokenizer(tok, selected)
        import torch
        from transformers import AutoModelForCausalLM
        if not torch.cuda.is_available():
            raise RuntimeError("Authorized CUDA hardware is required before loading weights")
        model = AutoModelForCausalLM.from_pretrained(selected.repo_id, revision=selected.revision,
            local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16, attn_implementation="sdpa")
        selected.validate_model_config(model.config)
        if getattr(model.config, "_commit_hash", None) != selected.revision:
            raise ValueError("Loaded weights did not resolve to the pinned model revision")
        return cls(model.to("cuda").eval(), tok, hardware_acceptance_authorized=True)

    def _check_state(self, state: NativeState, *, open_required: bool | None = None) -> None:
        if state.model_identity != self.model_identity or state.owner is not self._owner or state.failed:
            raise ValueError("State belongs to another backend or an incomplete failed forward")
        if open_required is not None and state.open != open_required:
            raise ValueError("Unexpected native assistant-turn boundary")
        if state.cache.get_seq_length() != len(state.consumed_tokens):
            raise ValueError("Native cache and consumed token history differ")

    def _foreign(self, exports: tuple[Export, ...], gain: float) -> tuple[tuple[Any, Any], ...]:
        import torch
        if not math.isfinite(gain) or gain < 0:
            raise ValueError("Channel gain must be finite and nonnegative")
        if len(exports) > 16:
            raise ValueError("The draft allows at most sixteen eligible foreign positions")
        if any(a.position >= b.position for a, b in zip(exports, exports[1:])):
            raise ValueError("Foreign positions must be unique and increasing")
        for export in exports:
            if export.position < 0 or not self.tokens.ordinary(export.token) or not isinstance(export.payload, NativeKVPayload):
                raise ValueError("Only ordinary native generated K/V positions may be exported")
            export.payload.check(export, self.model_identity, self._owner)
            if len(export.payload.layers) != len(self.modules):
                raise ValueError("Foreign payload has the wrong number of layers")
            cfg = self.model.config
            dim = getattr(cfg, "head_dim", cfg.hidden_size // cfg.num_attention_heads)
            shape = (1, cfg.num_key_value_heads, 1, dim)
            dtype = next(self.model.parameters()).dtype
            if any(tuple(t.shape) != shape or t.device != self.device or t.dtype != dtype
                   for layer in export.payload.layers for t in layer):
                raise ValueError("Foreign K/V shape, precision or device differs")
        if not exports or gain == 0:
            return ()
        return tuple((torch.cat([e.payload.layers[i][0] for e in exports], dim=2),
                      torch.cat([e.payload.layers[i][1] for e in exports], dim=2))
                     for i in range(len(self.modules)))

    def _consume(self, state: NativeState, ids: tuple[int, ...],
                 foreign: tuple[Export, ...] = (), gain: float = 0.0) -> None:
        import torch
        self._check_state(state)
        layers = self._foreign(foreign, gain)
        if not ids or any(not 0 <= token < self.tokens.vocab_size for token in ids):
            raise ValueError("Native input must be a nonempty in-vocabulary token sequence")
        # No padding: multi-token inputs are native prefill only without a donor.
        groups = [(token,) for token in ids] if layers else [ids]
        with self._lock, torch.no_grad():
            for group in groups:
                length = len(state.consumed_tokens)
                tensor = torch.tensor([group], dtype=torch.long, device=self.device)
                positions = torch.arange(length, length + len(group), device=self.device)[None, :]
                mask = torch.ones(1, length + len(group), dtype=torch.long, device=self.device)
                ctx = _AttentionContext(self.modules, layers, gain)
                previous = [c._attn_implementation for c in self._configs]
                handle = _FORWARD.set(ctx)
                try:
                    for cfg in self._configs:
                        cfg._attn_implementation = ATTENTION_NAME
                    result = self.model.model(input_ids=tensor, attention_mask=mask,
                        position_ids=positions, cache_position=positions[0],
                        past_key_values=state.cache, use_cache=True)
                    if ctx.seen != set(range(len(self.modules))):
                        raise RuntimeError("Not every layer used the v6 attention callback")
                    hidden = result.last_hidden_state[:, -1, :]
                    logits = self.model.lm_head(hidden).float()
                    if not torch.isfinite(hidden).all() or not torch.isfinite(logits).all():
                        raise ValueError("Non-finite native hidden state or logits")
                    state.last_hidden, state.native_logits = hidden.detach().clone(), logits.detach()
                    state.consumed_tokens += group
                except BaseException:
                    state.failed = True
                    raise
                finally:
                    _FORWARD.reset(handle)
                    for cfg, impl in zip(self._configs, previous):
                        cfg._attn_implementation = impl
        self._check_state(state)

    def create(self, system: str, user: str) -> NativeState:
        from transformers import DynamicCache
        state = NativeState(DynamicCache(config=self.model.config), (), None, None, True,
                            self.model_identity, owner=self._owner)
        self._consume(state, self.tokens.initial(system, user))
        return state

    def clone(self, state: NativeState) -> NativeState:
        from copy import deepcopy
        from transformers import DynamicCache
        self._check_state(state)
        copied = tuple((layer.keys.clone(), layer.values.clone()) for layer in state.cache.layers)
        return NativeState(DynamicCache(ddp_cache_data=copied, config=self.model.config),
            state.consumed_tokens, state.native_logits.clone(), state.last_hidden.clone(),
            state.open, state.model_identity, deepcopy(state.recoveries), state.failed,
            deepcopy(state.seal), state.seal_checksum, self._owner)

    def digest(self, state: NativeState) -> str:
        tensors = (state.native_logits, state.last_hidden, *tuple(
            t for layer in state.cache.layers for t in (layer.keys, layer.values)))
        return _tensor_hash(self._state_metadata(state), tensors)

    @staticmethod
    def _state_metadata(state: NativeState) -> dict[str, Any]:
        return {"tokens": state.consumed_tokens, "open": state.open,
            "model_identity": state.model_identity, "recoveries": state.recoveries,
            "failed": state.failed, "seal": state.seal,
            "cache_type": type(state.cache).__name__, "length": state.cache.get_seq_length()}

    def _archive(self, kind: str, metadata: dict[str, Any], tensors: tuple[Any, ...]) -> dict[str, Any]:
        payload = {"version": ARCHIVE_VERSION, "kind": kind, "model_identity": self.model_identity,
                   "metadata": _primitives(metadata)}
        copies = [t.detach().to("cpu").contiguous().clone() for t in tensors]
        return {**payload, "tensors": copies, "sha256": _tensor_hash(payload, tuple(copies))}

    def _read_archive(self, archive: dict[str, Any], kind: str) -> tuple[dict[str, Any], tuple[Any, ...]]:
        import torch

        if (type(archive) is not dict or set(archive) != {
                "version", "kind", "model_identity", "metadata", "tensors", "sha256"}
                or archive["version"] != ARCHIVE_VERSION or archive["kind"] != kind
                or archive["model_identity"] != self.model_identity):
            raise ValueError("Native archive schema/version/model identity differs")
        metadata = _primitives(archive["metadata"])
        tensors = archive["tensors"]
        if (type(metadata) is not dict or type(tensors) is not list or not tensors
                or not _hex_digest(archive["sha256"])):
            raise ValueError("Invalid native archive metadata/tensors/checksum")
        if any(type(t) is not torch.Tensor or t.device.type != "cpu" or t.layout != torch.strided
               or not t.is_contiguous() or t.requires_grad for t in tensors):
            raise ValueError("Load native archives with weights_only=True and map_location='cpu'")
        header = {k: archive[k] for k in ("version", "kind", "model_identity", "metadata")}
        if _tensor_hash(header, tuple(tensors)) != archive["sha256"]:
            raise ValueError("Native archive full-payload checksum mismatch")
        return metadata, tuple(tensors)

    def _check_archived_tensors(self, tensors: tuple[Any, ...], length: int, *, state: bool) -> None:
        import torch

        cfg = self.model.config
        dtype = next(self.model.parameters()).dtype
        dim = getattr(cfg, "head_dim", cfg.hidden_size // cfg.num_attention_heads)
        shapes = [((1, cfg.num_key_value_heads, length, dim), dtype)] * (2 * len(self.modules))
        if state:
            shapes = [((1, cfg.vocab_size), torch.float32), ((1, cfg.hidden_size), dtype), *shapes]
        if len(tensors) != len(shapes) or any(tuple(t.shape) != shape or t.dtype != precision
                for t, (shape, precision) in zip(tensors, shapes)):
            raise ValueError("Native archive tensor shape/precision differs")
        if any(not bool(torch.isfinite(t).all()) for t in tensors):
            raise ValueError("Native archive contains non-finite tensor values")

    def dump_state(self, state: NativeState) -> dict[str, Any]:
        """Return CPU tensors/primitives; caller may torch.save this, never the state.

        Restore with torch.load(..., weights_only=True, map_location='cpu') and
        load_state. No file I/O, model execution, or ownership object is serialized.
        """
        with self._lock:
            self._check_state(state)
            checksum = self.digest(state)
            if (state.seal is None) != (state.seal_checksum is None) or (
                    state.seal is not None and checksum != state.seal_checksum):
                raise ValueError("Cannot archive a changed sealed state")
            tensors = (state.native_logits, state.last_hidden, *tuple(
                t for layer in state.cache.layers for t in (layer.keys, layer.values)))
            return self._archive("state", {"state": self._state_metadata(state),
                "state_digest": checksum, "seal_checksum": state.seal_checksum}, tensors)

    def load_state(self, archive: dict[str, Any]) -> NativeState:
        """Verify CPU bytes before allocating restored tensors on the backend device."""
        from transformers import DynamicCache

        metadata, tensors = self._read_archive(archive, "state")
        if set(metadata) != {"state", "state_digest", "seal_checksum"}:
            raise ValueError("Invalid state archive metadata")
        m = metadata["state"]
        if (type(m) is not dict or set(m) != {"tokens", "open", "model_identity", "recoveries",
                "failed", "seal", "cache_type", "length"} or m["model_identity"] != self.model_identity
                or m["cache_type"] != "DynamicCache" or m["failed"] is not False
                or type(m["open"]) is not bool or type(m["tokens"]) is not list or not m["tokens"]
                or any(type(t) is not int or not 0 <= t < self.tokens.vocab_size for t in m["tokens"])
                or type(m["length"]) is not int or m["length"] != len(m["tokens"])
                or not _hex_digest(metadata["state_digest"])):
            raise ValueError("Invalid or failed native state archive")
        if type(m["recoveries"]) is not list:
            raise ValueError("Invalid native recovery history")
        for recovery in m["recoveries"]:
            if (type(recovery) is not dict or set(recovery) != {"token", "legal", "category", "suffix"}
                    or type(recovery["legal"]) is not bool):
                raise ValueError("Invalid native recovery record")
            rule = self.tokens.recovery(recovery["token"])
            if recovery["category"] != rule.category or recovery["suffix"] != list(rule.suffix):
                raise ValueError("Native recovery policy differs")
        seal = m["seal"]
        if seal is None:
            if metadata["seal_checksum"] is not None:
                raise ValueError("Unsealed state has a seal checksum")
        else:
            if (type(seal) is not dict or set(seal) != {"token", "probability", "legal_logits",
                    "legal_mass", "token_ids", "foreign", "gain"} or not m["open"]
                    or metadata["seal_checksum"] != metadata["state_digest"]):
                raise ValueError("Invalid sealed state archive")
            self.tokens.recovery(seal["token"])
            Probe(None, seal["token"], seal["probability"], tuple(seal["legal_logits"]),
                  seal["legal_mass"], tuple(seal["token_ids"])).validate()
            if (tuple(seal["token_ids"]) != self.tokens.choice_ids(("1", "2", "3", "4"))
                    or type(seal["gain"]) not in (int, float) or seal["gain"] < 0
                    or type(seal["foreign"]) is not list or len(seal["foreign"]) > 16):
                raise ValueError("Invalid sealed choice/window contract")
            previous = -1
            for export in seal["foreign"]:
                if (type(export) is not dict or set(export) != {"token", "position", "digest"}
                        or type(export["token"]) is not int or not self.tokens.ordinary(export["token"])
                        or type(export["position"]) is not int or export["position"] <= previous
                        or not _hex_digest(export["digest"])):
                    raise ValueError("Invalid sealed foreign identities")
                previous = export["position"]
        self._check_archived_tensors(tensors, m["length"], state=True)
        if _tensor_hash(m, tensors) != metadata["state_digest"]:
            raise ValueError("Native state checksum differs")
        restored = tuple(t.to(self.device).clone() for t in tensors)
        layers = tuple(zip(restored[2::2], restored[3::2]))
        state = NativeState(DynamicCache(ddp_cache_data=layers, config=self.model.config),
            tuple(m["tokens"]), restored[0], restored[1], m["open"], self.model_identity,
            tuple(m["recoveries"]), False, seal, metadata["seal_checksum"], self._owner)
        self._check_state(state)
        if self.digest(state) != metadata["state_digest"]:
            raise ValueError("Restored native state differs from its archive")
        return state

    def dump_export(self, export: Export) -> dict[str, Any]:
        """Archive one incremental token; tapes are ordered lists of these records."""
        self._foreign((export,), 0.0)
        tensors = tuple(t for layer in export.payload.layers for t in layer)
        metadata = {"token": export.token, "position": export.position, "model_identity": self.model_identity}
        if _tensor_hash(metadata, tensors) != export.digest:
            raise ValueError("Export payload checksum differs before archive")
        return self._archive("export", {**metadata, "payload_digest": export.digest}, tensors)

    def load_export(self, archive: dict[str, Any]) -> Export:
        metadata, tensors = self._read_archive(archive, "export")
        if (set(metadata) != {"token", "position", "model_identity", "payload_digest"}
                or metadata["model_identity"] != self.model_identity
                or type(metadata["token"]) is not int or not self.tokens.ordinary(metadata["token"])
                or type(metadata["position"]) is not int or metadata["position"] < 0
                or not _hex_digest(metadata["payload_digest"])):
            raise ValueError("Invalid native export archive metadata")
        self._check_archived_tensors(tensors, 1, state=False)
        header = {k: metadata[k] for k in ("token", "position", "model_identity")}
        if _tensor_hash(header, tensors) != metadata["payload_digest"]:
            raise ValueError("Native export payload checksum differs")
        restored = tuple(t.to(self.device).clone() for t in tensors)
        layers = tuple(zip(restored[::2], restored[1::2]))
        payload = NativeKVPayload(layers, metadata["token"], metadata["position"], self.model_identity,
            metadata["payload_digest"], tuple(_tensor_stamp(t) for t in restored), self._owner)
        export = Export(payload.token, payload.position, payload.digest, payload)
        self._foreign((export,), 0.0)
        return export

    def begin_user(self, state: NativeState, text: str) -> None:
        self._check_state(state, open_required=False)
        if state.seal is not None:
            raise ValueError("A sealed answer must first be committed")
        self._consume(state, self.tokens.user_turn(text))
        state.open = True

    def finish_turn(self, state: NativeState, foreign: tuple[Export, ...] = (), gain: float = 0.0) -> None:
        self._check_state(state, open_required=True)
        if state.seal is not None:
            raise ValueError("A sealed answer must first be committed")
        self._consume(state, self.tokens.close_ids, foreign, gain)
        state.open = False

    def step(self, state: NativeState, foreign: tuple[Export, ...], gain: float) -> Export:
        self._check_state(state, open_required=True)
        if state.seal is not None:
            raise ValueError("Cannot continue reflection from a sealed answer")
        logits = state.native_logits.clone()
        logits[:, self._forbidden] = -math.inf
        token = int(logits.argmax(dim=-1).item())
        if not self.tokens.ordinary(token):
            raise ValueError("No ordinary token is available for reflection")
        position = len(state.consumed_tokens)
        self._consume(state, (token,), foreign, gain)
        layers = tuple((layer.keys[:, :, -1:, :].detach().clone(),
                        layer.values[:, :, -1:, :].detach().clone()) for layer in state.cache.layers)
        tensors = tuple(t for layer in layers for t in layer)
        digest = _tensor_hash({"token": token, "position": position,
                              "model_identity": self.model_identity}, tensors)
        payload = NativeKVPayload(layers, token, position, self.model_identity, digest,
                                  tuple(_tensor_stamp(t) for t in tensors), self._owner)
        return Export(token, position, digest, payload)

    def probe(self, state: NativeState, question: str, choice_labels: tuple[str, str, str, str],
              foreign: tuple[Export, ...], gain: float) -> Probe:
        import torch
        ids = self.tokens.choice_ids(choice_labels)
        branch = self.clone(state)
        self.finish_turn(branch, foreign, gain)
        self._consume(branch, self.tokens.user_turn(question), foreign, gain)
        branch.open = True
        if self._w32 is None:
            self._w32 = self.model.lm_head.weight.detach().float()
        with torch.no_grad():
            scores = torch.nn.functional.linear(branch.last_hidden.float(), self._w32,
                self.model.lm_head.bias.detach().float() if self.model.lm_head.bias is not None else None)
            probabilities = torch.softmax(scores, dim=-1)
        token = int(branch.native_logits.argmax(dim=-1).item())
        result = Probe(branch, token, float(probabilities[0, token].item()),
            tuple(float(scores[0, i].item()) for i in ids),
            float(probabilities[0, list(ids)].sum().item()), ids)
        result.validate()
        branch.seal = {"token": result.token, "probability": result.probability,
            "legal_logits": list(result.legal_logits), "legal_mass": result.legal_mass,
            "token_ids": list(result.token_ids), "foreign": [e.identity() for e in foreign], "gain": gain}
        branch.seal_checksum = self.digest(branch)
        return result

    def commit_answer(self, probe: Probe, foreign: tuple[Export, ...], gain: float) -> NativeState:
        probe.validate()
        state = probe.state
        self._check_state(state, open_required=True)
        expected = {"token": probe.token, "probability": probe.probability,
            "legal_logits": list(probe.legal_logits), "legal_mass": probe.legal_mass,
            "token_ids": list(probe.token_ids), "foreign": [e.identity() for e in foreign], "gain": gain}
        if state.seal != expected or state.seal_checksum != self.digest(state):
            raise ValueError("Sealed answer, branch state or held window changed before commitment")
        rule = self.tokens.recovery(probe.token)
        state.seal = None; state.seal_checksum = None
        self._consume(state, (probe.token,), foreign, gain)
        if rule.suffix:
            # Recovery/closure is a controller boundary, never new communication.
            self._consume(state, rule.suffix)
        state.recoveries += ({"token": probe.token, "legal": probe.token in probe.token_ids,
                              "category": rule.category, "suffix": list(rule.suffix)},)
        state.open = False
        return state

    def decode(self, exports: tuple[Export, ...]) -> str:
        for export in exports:
            if not self.tokens.ordinary(export.token):
                raise ValueError("Text reference cannot decode special/control exports")
        return self.tokenizer.decode([e.token for e in exports], skip_special_tokens=False,
                                      clean_up_tokenization_spaces=False)
