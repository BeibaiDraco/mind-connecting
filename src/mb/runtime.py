"""Batched two-instance runtime (protocol v0.5 §5).

Rows are interleaved pairs: row 2p is instance A of pair p, row 2p+1 is instance B, so
the partner of row i is i ^ 1. A tick is one forward in which every row consumes exactly
one token; all rows read the mailbox committed at the end of the previous tick, so no row
can see its partner's message from the same tick. Mailboxes hold BF16 messages
m = BF16(N(e)); transforms and gains act on m.float(). Snapshots and branches are
independent tensor copies (never ``crop``). Greedy decisions use the model's native bf16
logits; readout scores are recomputed in fp32 from the final hidden state.

Protocol v2 adds a second interface, KV reading (§4 of PROTOCOL_V2.md): during ticks the
receiver's attention in every layer also reads its partner's cached keys/values (appended,
never modifying either cache), weighted by w, excluding the partner's current-tick key.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Callable

import torch
from transformers import AttentionInterface, AutoModelForCausalLM, DynamicCache, PreTrainedTokenizerBase
from transformers.integrations.sdpa_attention import sdpa_attention_forward
from transformers.masking_utils import AttentionMaskInterface, sdpa_mask

from mb import chat
from mb.bridge import (MESSAGE_DTYPE, BridgeHook, LayerCalibration, apply_transform, ema_update,
                       message, rms, scram_matrix)
from mb.conditions import MODEL_REVISION, ArmConfig
from mb.kv_geometry import Span, bank_metadata, digest, rephase_keys, resolve_geometry
from mb.model_profiles import ModelProfile, QWEN, resolve_profile
from mb.tasks import NOTE_MAX_TOKENS, REFLECTION_TICKS, U_OPEN_TOKENS  # noqa: F401 (re-exported)

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
KV_ATTENTION = "mb_kv"  # sdpa, plus partner-cache reading while a KV plan is active


# ---------------------------------------------------------------------------
# KV reading (protocol v2 §4)
# ---------------------------------------------------------------------------


@dataclass
class KVPlan:
    receivers: torch.Tensor  # [rows] bool: rows whose attention also reads the partner (row ^ 1)
    log_w: float  # added to the attention logits of partner keys (prefill segment for scope PC)
    scope: str  # "C": partner's C/R tokens; "ALL": partner's whole valid cache; "P": prefill only; "PC": split weights
    log_w_live: float | None = None  # scope PC: added to partner keys in the C/R segment
    position: str = "native"
    log_spans: bool = False


class _KVContext:
    """Per-forward state read by ``kv_attention``; only set by ``Engine.step`` around tick forwards."""

    def __init__(self) -> None:
        self.active = False
        self.receivers: torch.Tensor | None = None  # [rows] long indices of receiving rows
        self.readable: torch.Tensor | None = None  # [rows, L] bool: partner positions each receiver may read
        self.log_w = 0.0
        self.pos_bias: torch.Tensor | None = None  # [L] log-weight per partner position
        self.mass_sum: torch.Tensor | None = None  # [n_receivers] partner attention mass summed over layers
        self.mass_cr_sum: torch.Tensor | None = None  # same, restricted to the partner's C/R tokens
        self.c_start = 0
        self.n_layers = 0
        self.delta = self.rephase_mask = self.inv_freq = self.rotate_half = None
        self.own_spans = self.donor_spans = self.span_valid = None
        self.span_mass: dict[int, torch.Tensor] = {}
        self.bank_mass: dict[int, torch.Tensor] = {}


KV_CONTEXT = _KVContext()


def kv_attention(module, query, key, value, attention_mask, dropout=0.0, scaling=None, is_causal=None, **kwargs):
    """Plain sdpa for every row; receivers additionally read the partner's keys.

    The joint softmax over [own keys, partner keys] is evaluated as a mixture of the plain output
    and a partner-only output: o = o_own + β (o_par − o_own), with β = σ(lse_par − lse_own), the
    total attention mass on partner keys (log w already inside lse_par). At w = 0, β = 0 and the
    receiver's output is bit-identical to the plain path. query [B, H, q, D]; key/value
    [B, KVH, L, D] (full cache incl. this tick); attention_mask is HF's boolean sdpa mask or None.
    """
    ctx = KV_CONTEXT
    if ctx.active and query.shape[1] % key.shape[1]:
        raise RuntimeError("query heads must be divisible by KV heads")
    out, weights = sdpa_attention_forward(module, query, key, value, attention_mask, dropout=dropout,
                                          scaling=scaling, is_causal=is_causal, **kwargs)
    if not ctx.active or ctx.receivers is None or ctx.receivers.numel() == 0:
        return out, weights
    if query.shape[2] != 1:
        raise RuntimeError("KV reading is defined for single-token ticks only")
    recv = ctx.receivers
    partner = recv ^ 1
    n, heads, dim = recv.numel(), query.shape[1], query.shape[3]
    kv_heads, length = key.shape[1], key.shape[2]
    groups = heads // kv_heads
    scale = scaling if scaling is not None else dim ** -0.5
    q = query.index_select(0, recv).float().view(n, kv_heads, groups, 1, dim)
    if attention_mask is not None:
        own_ok = attention_mask.index_select(0, recv)[:, 0, -1, :length]  # [n, L]
    else:
        own_ok = torch.ones(n, length, dtype=torch.bool, device=query.device)
    par_ok = ctx.readable.index_select(0, recv)[:, :length]
    k_own = key.index_select(0, recv).float().unsqueeze(2)  # [n, KVH, 1, L, D]
    k_par = key.index_select(0, partner).float().unsqueeze(2)
    if ctx.delta is not None:
        k_par = rephase_keys(k_par, ctx.delta, ctx.rephase_mask[:, :length],
                            ctx.inv_freq, ctx.rotate_half)
    v_par = value.index_select(0, partner).float().unsqueeze(2)
    own_logits = torch.matmul(q, k_own.transpose(-1, -2)) * scale  # [n, KVH, G, 1, L]
    own_logits = own_logits.masked_fill(~own_ok[:, None, None, None, :], -math.inf)
    par_logits = torch.matmul(q, k_par.transpose(-1, -2)) * scale + ctx.pos_bias[:length]
    par_logits = par_logits.masked_fill(~par_ok[:, None, None, None, :], -math.inf)
    lse_own = torch.logsumexp(own_logits, dim=-1, keepdim=True)
    lse_par = torch.logsumexp(par_logits, dim=-1, keepdim=True)  # -inf when nothing is readable
    beta = torch.sigmoid(lse_par - lse_own)  # [n, KVH, G, 1, 1]; 0 when lse_par = -inf
    p_par = torch.where(torch.isfinite(lse_par), torch.exp(par_logits - lse_par), torch.zeros_like(par_logits))
    o_par = torch.matmul(p_par, v_par)  # [n, KVH, G, 1, D]
    o_own = out.index_select(0, recv).transpose(1, 2).float().view(n, kv_heads, groups, 1, dim)
    mixed = o_own + beta * (o_par - o_own)
    out = out.clone()
    out[recv] = mixed.view(n, heads, 1, dim).transpose(1, 2).to(out.dtype)
    # Manipulation check: partner mass overall and on the partner's C/R segment (no prompt sinks).
    mass = beta.mean(dim=(1, 2, 3, 4))
    seg = torch.arange(length, device=query.device) >= ctx.c_start
    mass_cr = (beta * (p_par * seg).sum(dim=-1, keepdim=True)).mean(dim=(1, 2, 3, 4))
    ctx.mass_sum = mass if ctx.mass_sum is None else ctx.mass_sum + mass
    ctx.mass_cr_sum = mass_cr if ctx.mass_cr_sum is None else ctx.mass_cr_sum + mass_cr
    ctx.n_layers += 1
    if ctx.own_spans is not None:
        p_own = torch.exp(own_logits - lse_own)
        own_joint = ((1 - beta) * p_own).view(n, heads, length)
        donor_joint = (beta * p_par).view(n, heads, length)
        masses = (torch.einsum("nhl,nsl->nhs", own_joint, ctx.own_spans[:, :, :length].float())
                  + torch.einsum("nhl,nsl->nhs", donor_joint, ctx.donor_spans[:, :, :length].float()))
        layer = module.layer_idx  # zero-based layer index, query-head order matches native GQA
        if layer in ctx.span_mass:
            raise RuntimeError(f"duplicate attention diagnostic for layer {layer}")
        ctx.span_mass[layer] = masses.masked_fill(~ctx.span_valid[:, None, :], math.nan)
        bank_beta = beta.view(n, heads, 1)
        ctx.bank_mass[layer] = torch.cat((1 - bank_beta, bank_beta), dim=-1)
    return out, weights


AttentionInterface.register(KV_ATTENTION, kv_attention)
AttentionMaskInterface.register(KV_ATTENTION, sdpa_mask)


def load_model(device: str = "cuda", revision: str | None = None, dtype: torch.dtype = torch.bfloat16,
               *, profile: str | ModelProfile | None = None, tokenizer: PreTrainedTokenizerBase | None = None):
    selected = resolve_profile(profile)
    if revision is not None and revision != selected.revision:
        raise ValueError("model revision differs from the pinned profile")
    if selected != QWEN:
        if tokenizer is None:
            raise ValueError("load the manifest-verified tokenizer before loading a new model")
        chat.require_verified_tokenizer(tokenizer, selected)
    elif tokenizer is not None:
        chat.require_verified_tokenizer(tokenizer, selected)
    model = AutoModelForCausalLM.from_pretrained(
        selected.repo_id, revision=selected.revision, dtype=dtype, attn_implementation=KV_ATTENTION,
        trust_remote_code=False)
    selected.validate_model_config(model.config)
    if selected != QWEN and getattr(model.config, "_commit_hash", None) != selected.revision:
        raise ValueError("loaded model did not resolve to the pinned revision")
    model._mb_profile_key = selected.key
    return model.to(device).eval()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


@dataclass
class State:
    cache: DynamicCache
    attn: torch.Tensor  # [rows, L] long; 1 = valid, 0 = left padding
    next_pos: torch.Tensor  # [rows] position id of the next consumed token
    pending: torch.Tensor  # [rows] next token to consume (chosen, not yet in the cache)
    logits: torch.Tensor  # [rows, V] fp32 raw logits that produced ``pending``
    mailbox: torch.Tensor  # [rows, d] BF16 committed messages
    ema: torch.Tensor  # [rows, d] fp32 integrated raw states e
    consumed: list[torch.Tensor] = field(default_factory=list)  # per tick [rows]
    tick: int = 0  # logical ticks consumed since the prefix
    phase: str = "P"  # "P" after prefill, "C" during/after reflection, "R" inside a readout branch
    c_start: int = 0  # physical cache index of the first C token (= prefill length)
    kv_banks: list[dict] | None = None  # opt-in, immutable P-token/span provenance in logical coordinates

    @property
    def rows(self) -> int:
        return int(self.pending.shape[0])

    def consumed_matrix(self) -> torch.Tensor:
        if not self.consumed:
            return torch.empty(self.rows, 0, dtype=torch.long, device=self.pending.device)
        return torch.stack(self.consumed, dim=1)


def cache_layers(cache: DynamicCache) -> list[tuple[torch.Tensor, torch.Tensor]]:
    return [(layer.keys, layer.values) for layer in cache.layers]


def select_rows(state: State, idx: torch.Tensor | list[int], config) -> State:
    """Independent copy of the given rows (all tensors are materialized, nothing is shared)."""
    idx_t = torch.as_tensor(idx, dtype=torch.long, device=state.pending.device)
    kv = [(k.index_select(0, idx_t).clone(), v.index_select(0, idx_t).clone()) for k, v in cache_layers(state.cache)]
    return State(
        cache=DynamicCache(ddp_cache_data=kv, config=config),
        attn=state.attn.index_select(0, idx_t).clone(),
        next_pos=state.next_pos.index_select(0, idx_t).clone(),
        pending=state.pending.index_select(0, idx_t).clone(),
        logits=state.logits.index_select(0, idx_t).clone(),
        mailbox=state.mailbox.index_select(0, idx_t).clone(),
        ema=state.ema.index_select(0, idx_t).clone(),
        consumed=[t.index_select(0, idx_t).clone() for t in state.consumed],
        tick=state.tick,
        phase=state.phase,
        c_start=state.c_start,
        kv_banks=([copy.deepcopy(state.kv_banks[i]) for i in idx_t.tolist()]
                  if state.kv_banks is not None else None),
    )


# ---------------------------------------------------------------------------
# Injection plan
# ---------------------------------------------------------------------------


@dataclass
class Plan:
    """Per-row write plan for one batch (constant over ticks)."""

    tau: int
    gain: float
    transform: str
    donor: torch.Tensor  # [rows] long, -1 = row receives nothing
    static: torch.Tensor | None = None  # [rows, d] fp32 for STATIC
    q: torch.Tensor | None = None
    idx: torch.Tensor | None = None
    kv: KVPlan | None = None  # protocol v2 KV reading (no residual write)

    @property
    def writes(self) -> bool:
        return self.gain > 0 and (self.static is not None or bool((self.donor >= 0).any()))


def make_plan(arm: ArmConfig, roles: list[str], static_rules: list[str | None], cal: LayerCalibration | None,
              device: torch.device, mask_idx: torch.Tensor | None = None, d: int | None = None) -> Plan:
    """Rows are interleaved (partner = i ^ 1); ``roles`` gives 'A'/'B' per row."""
    if arm.model_profile is not None and d is not None and d != resolve_profile(arm.model_profile).hidden_size:
        raise ValueError("arm profile and runtime hidden size differ")
    rows = len(roles)
    donor = torch.full((rows,), -1, dtype=torch.long, device=device)
    static = None
    if arm.interface == "kv":
        receivers = torch.tensor([arm.direction == "two" or role == "A" for role in roles], device=device)
        live = None
        if arm.kv_scope == "PC":
            live = math.log(arm.kv_w_live) if arm.kv_w_live > 0 else -math.inf
        return Plan(arm.tau, 0.0, "none", donor,
                    kv=KVPlan(receivers, math.log(arm.gain), arm.kv_scope, live,
                              arm.kv_position, arm.kv_log_spans))
    if arm.condition == "STATIC":
        assert cal is not None and d is not None
        static = torch.zeros(rows, d, device=device)
        for i, (role, rule) in enumerate(zip(roles, static_rules)):
            if role == "A":
                key = f"{arm.form}:{rule}"
                if key not in cal.static:
                    raise KeyError(f"STATIC vector {key} unavailable (unusable or missing)")
                static[i] = cal.static[key]
    elif arm.direction in ("one", "two"):
        for i, role in enumerate(roles):
            if arm.direction == "two" or role == "A":
                donor[i] = i ^ 1
    if arm.condition == "MASK" and (mask_idx is None or mask_idx.numel() != arm.k):
        raise ValueError("MASK arm needs its k mask indices")
    q = scram_matrix(d, arm.scram_seed, device) if arm.transform == "scram" else None
    return Plan(arm.tau, arm.gain, arm.transform, donor, static, q, mask_idx)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


@dataclass
class TickLog:
    """Per-tick diagnostics for one phase; stacked to [rows, ticks] (cos: [pairs, ticks])."""

    tokens: list[torch.Tensor] = field(default_factory=list)
    inj_ratio: list[torch.Tensor] = field(default_factory=list)
    msg_norm: list[torch.Tensor] = field(default_factory=list)
    unmatched: list[torch.Tensor] = field(default_factory=list)
    energy_ratio: list[torch.Tensor] = field(default_factory=list)
    cos_pair: list[torch.Tensor] = field(default_factory=list)
    kv_mass: list[torch.Tensor] = field(default_factory=list)  # partner attention mass (NaN: not reading)
    kv_mass_cr: list[torch.Tensor] = field(default_factory=list)  # ... on the partner's C/R tokens only
    kv_span_mass: list[torch.Tensor] = field(default_factory=list)  # [rows,layers,query_heads,span_slots]
    kv_bank_mass: list[torch.Tensor] = field(default_factory=list)  # [rows,layers,query_heads,own/donor]
    kv_query_pos: list[torch.Tensor] = field(default_factory=list)  # logical query coordinate

    def stacked(self) -> dict[str, torch.Tensor]:
        return {k: torch.stack(v, dim=1).cpu() for k, v in vars(self).items() if v}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class Engine:
    def __init__(self, model, tok: PreTrainedTokenizerBase, layer: int, cal: LayerCalibration | None):
        self.profile = chat.profile_for_tokenizer(tok)
        chat.require_verified_tokenizer(tok, self.profile)
        self.profile.validate_model_config(model.config)
        if self.profile != QWEN and getattr(model, "_mb_profile_key", None) != self.profile.key:
            raise ValueError("new-model engine requires a model loaded through its pinned profile")
        n_layers = model.config.num_hidden_layers
        if not 1 <= layer <= n_layers:
            raise ValueError(f"layer {layer} outside 1..{n_layers}")
        if cal is not None and cal.layer != layer:
            raise ValueError(f"calibration for layer {cal.layer} given to an engine at layer {layer}")
        self.model = model
        self.tok = tok
        self.layer = layer
        self.device = next(model.parameters()).device
        self.cal = cal.to(self.device) if cal is not None else None
        self.hook = BridgeHook(model.model.layers[layer - 1], layer)
        self.d = model.config.hidden_size
        tokens = chat.runtime_tokens(tok)
        self.eos = torch.tensor(tokens.eos_ids, device=self.device)
        self.label_ids = torch.tensor(tokens.label_ids, device=self.device)
        self.pad_id = tokens.pad_id
        self._w32: torch.Tensor | None = None
        self.last_kv_mass: torch.Tensor | None = None
        self.last_kv_mass_cr: torch.Tensor | None = None
        self.last_kv_span_mass: torch.Tensor | None = None
        self.last_kv_bank_mass: torch.Tensor | None = None
        self._kv_rotary = None
        model.config._attn_implementation = KV_ATTENTION

    def close(self) -> None:
        self.hook.remove()

    # -- low level -----------------------------------------------------------------

    def _lm_logits(self, hidden: torch.Tensor) -> torch.Tensor:
        return self.model.lm_head(hidden).float()

    def fp32_logits(self, hidden: torch.Tensor) -> torch.Tensor:
        if self._w32 is None:
            self._w32 = self.model.lm_head.weight.detach().float()
        return hidden.float() @ self._w32.T

    def no_eos_argmax(self, logits: torch.Tensor) -> torch.Tensor:
        masked = logits.clone()
        masked[:, self.eos] = -math.inf
        return masked.argmax(dim=-1)

    def _messages(self, ema: torch.Tensor) -> torch.Tensor:
        if self.cal is None:
            return torch.zeros(ema.shape, dtype=MESSAGE_DTYPE, device=ema.device)
        return message(ema, self.cal)

    @torch.no_grad()
    def prefill(self, sequences: list[list[int]], *, attention_spans: list[list[Span]] | None = None) -> State:
        """Left-padded prefill with bridge writes off; captures z0 (seed) and chooses C1."""
        banks = None
        if attention_spans is not None:
            if len(attention_spans) != len(sequences):
                raise ValueError("attention_spans must contain one declaration list per row")
            banks = [bank_metadata(seq, spans) for seq, spans in zip(sequences, attention_spans)]
        rows, length = len(sequences), max(len(s) for s in sequences)
        ids = torch.full((rows, length), self.pad_id, dtype=torch.long, device=self.device)
        attn = torch.zeros(rows, length, dtype=torch.long, device=self.device)
        for i, seq in enumerate(sequences):
            ids[i, length - len(seq):] = torch.tensor(seq, device=self.device)
            attn[i, length - len(seq):] = 1
        pos = (attn.cumsum(dim=-1) - 1).clamp(min=0)
        cache = DynamicCache(config=self.model.config)
        self.hook.write_enabled = False
        self.hook.injection = None
        self.hook.mode = "prefill"
        try:
            out = self.model.model(input_ids=ids, attention_mask=attn, position_ids=pos,
                                   past_key_values=cache, use_cache=True)
        finally:
            self.hook.mode = "tick"
        h = out.last_hidden_state[:, -1, :]
        logits = self._lm_logits(h)
        z0 = self.hook.captured
        if z0 is None or z0.shape != (rows, self.d):
            raise RuntimeError("prefill seed capture failed")
        ema = z0.clone()
        return State(cache, attn, pos[:, -1] + 1, self.no_eos_argmax(logits), logits, self._messages(ema), ema,
                     c_start=length, kv_banks=banks)

    def _rotary_spec(self) -> tuple[torch.Tensor, Callable, dict]:
        """Use the pinned model's stationary frequencies and its actual pairing function."""
        rotary = self.model.model.rotary_emb
        if rotary.rope_type not in ("default", "llama3"):
            raise ValueError("read-time translation requires validated stationary rotary frequencies")
        if self._kv_rotary is None:
            if self.model.config.model_type == "qwen3":
                from transformers.models.qwen3.modeling_qwen3 import rotate_half
            elif self.model.config.model_type == "llama":
                from transformers.models.llama.modeling_llama import rotate_half
            else:
                raise ValueError("no validated rotary pairing for this model")
            inv_freq = rotary.inv_freq.detach().float().clone()
            identity = {"rope_type": rotary.rope_type, "pairing": rotate_half.__module__ + ".rotate_half",
                        "inv_freq_sha256": digest(inv_freq.cpu().tolist()),
                        "cached_attention_scaling": float(rotary.attention_scaling),
                        "rephase_attention_scaling": 1.0}
            self._kv_rotary = inv_freq, rotate_half, identity
        if not torch.equal(self._kv_rotary[0], rotary.inv_freq.float()):
            raise ValueError("rotary frequencies changed after the geometry was resolved")
        return self._kv_rotary

    def kv_condition_identity(self, state: State, kv: KVPlan | None) -> list[dict | None] | None:
        """Resolved row identities, kept beside the constant arm identity in records."""
        if kv is None or (kv.position == "native" and not kv.log_spans):
            return None
        if state.rows % 2 or kv.receivers.shape != (state.rows,):
            raise ValueError("KV geometry requires complete interleaved pairs")
        if kv.position not in ("native", "before_own"):
            raise ValueError("unknown KV position")
        if kv.position != "native" and kv.scope != "P":
            raise ValueError("whole-P translation requires KV-P scope")
        if state.kv_banks is None:
            raise ValueError("V7 geometry requires attention_spans at prefill (empty row lists are allowed)")
        lengths = state.attn[:, :state.c_start].sum(dim=1).tolist()
        if lengths != [bank["length"] for bank in state.kv_banks]:
            raise ValueError("P-bank provenance disagrees with valid logical lengths")
        _, _, rotary = self._rotary_spec()
        result = []
        for row, receiving in enumerate(kv.receivers.tolist()):
            if not receiving:
                result.append(None)
                continue
            entry = resolve_geometry(state.kv_banks[row], state.kv_banks[row ^ 1], kv.position,
                                     log_spans=kv.log_spans)
            entry["rotary"] = rotary
            entry["sha256"] = digest({k: v for k, v in entry.items() if k != "sha256"})
            result.append(entry)
        return result

    def _kv_geometry_begin(self, state: State, kv: KVPlan) -> None:
        ctx = KV_CONTEXT
        metadata = self.kv_condition_identity(state, kv)
        ctx.delta = ctx.rephase_mask = ctx.inv_freq = ctx.rotate_half = None
        ctx.own_spans = ctx.donor_spans = ctx.span_valid = None
        ctx.span_mass = {}
        ctx.bank_mass = {}
        if metadata is None:
            return
        rows = ctx.receivers.tolist()
        logical = state.attn.cumsum(dim=-1) - 1
        if kv.position != "native":
            ctx.delta = torch.tensor([metadata[r]["delta"] for r in rows], device=self.device)
            ctx.rephase_mask = ctx.readable.index_select(0, ctx.receivers)
            ctx.inv_freq, ctx.rotate_half, _ = self._rotary_spec()
        if not kv.log_spans:
            return
        width = max((len(metadata[r]["spans"]) for r in rows), default=0)
        shape = (len(rows), width, state.attn.shape[1])
        ctx.own_spans = torch.zeros(shape, dtype=torch.bool, device=self.device)
        ctx.donor_spans = torch.zeros_like(ctx.own_spans)
        ctx.span_valid = torch.zeros((len(rows), width), dtype=torch.bool, device=self.device)
        for i, row in enumerate(rows):
            for j, span in enumerate(metadata[row]["spans"]):
                own = span["bank"] == "own"
                source = row if own else row ^ 1
                mask = ((logical[source] >= span["start"]) & (logical[source] < span["end"])
                        & state.attn[source].bool())
                (ctx.own_spans if own else ctx.donor_spans)[i, j] = mask
                ctx.span_valid[i, j] = True

    def _kv_begin(self, state: State, kv: KVPlan) -> None:
        """Partner positions each receiver may read this tick (state.attn already has this tick's column)."""
        length = state.attn.shape[1]
        pos = torch.arange(length, device=self.device)
        partner = torch.arange(state.rows, device=self.device) ^ 1
        readable = state.attn.index_select(0, partner).bool() & (pos < length - 1)  # partner's newest key hidden
        if kv.scope == "C":
            readable &= pos >= state.c_start
        elif kv.scope == "P":
            readable &= pos < state.c_start
        bias = torch.full((length,), kv.log_w, device=self.device)
        if kv.scope == "PC":
            bias = torch.where(pos < state.c_start, bias, torch.full_like(bias, kv.log_w_live))
        ctx = KV_CONTEXT
        ctx.receivers = kv.receivers.nonzero(as_tuple=True)[0]
        ctx.readable = readable
        ctx.log_w = kv.log_w
        ctx.pos_bias = bias
        ctx.c_start = state.c_start
        ctx.mass_sum = ctx.mass_cr_sum = None
        ctx.n_layers = 0
        self._kv_geometry_begin(state, kv)
        ctx.active = True

    def _kv_end(self, rows: int, kv: KVPlan | None, completed: bool = True) -> None:
        ctx = KV_CONTEXT
        mass = torch.full((rows,), math.nan, device=self.device)
        mass_cr = torch.full((rows,), math.nan, device=self.device)
        span_mass = None
        bank_mass = None
        try:
            if kv is not None and ctx.active and ctx.receivers is not None and ctx.receivers.numel():
                if completed and ctx.n_layers != self.model.config.num_hidden_layers:
                    raise RuntimeError(f"KV reading ran in {ctx.n_layers} layers, expected "
                                       f"{self.model.config.num_hidden_layers} (attention implementation changed?)")
                if ctx.n_layers:
                    mass[ctx.receivers] = ctx.mass_sum / ctx.n_layers
                    mass_cr[ctx.receivers] = ctx.mass_cr_sum / ctx.n_layers
                if completed and kv.log_spans:
                    layers = self.model.config.num_hidden_layers
                    if sorted(ctx.span_mass) != list(range(layers)):
                        raise RuntimeError("missing layer in attention span diagnostics")
                    received = torch.stack([ctx.span_mass[i] for i in range(layers)], dim=1)
                    span_mass = torch.full((rows, *received.shape[1:]), math.nan, device=self.device)
                    span_mass[ctx.receivers] = received
                    received_bank = torch.stack([ctx.bank_mass[i] for i in range(layers)], dim=1)
                    bank_mass = torch.full((rows, *received_bank.shape[1:]), math.nan, device=self.device)
                    bank_mass[ctx.receivers] = received_bank
        finally:
            self.last_kv_mass, self.last_kv_mass_cr = mass, mass_cr
            self.last_kv_span_mass = span_mass
            self.last_kv_bank_mass = bank_mass
            ctx.active = False
            ctx.receivers = ctx.readable = ctx.mass_sum = ctx.mass_cr_sum = ctx.pos_bias = None
            ctx.n_layers = 0
            ctx.delta = ctx.rephase_mask = ctx.inv_freq = ctx.rotate_half = None
            ctx.own_spans = ctx.donor_spans = ctx.span_valid = None
            ctx.span_mass = {}
            ctx.bank_mass = {}

    @torch.no_grad()
    def step(self, state: State, tokens: torch.Tensor, injection: torch.Tensor | None,
             kv: KVPlan | None = None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """One tick. Returns (bf16-derived logits fp32 [rows,V], last hidden [rows,d], raw block output z)."""
        if tokens.shape != (state.rows,):
            raise ValueError(f"a tick consumes exactly one token per row; got {tuple(tokens.shape)}")
        state.attn = torch.cat([state.attn, torch.ones(state.rows, 1, dtype=torch.long, device=self.device)], dim=1)
        self.hook.mode = "tick"
        self.hook.injection = injection
        self.hook.write_enabled = injection is not None
        completed = False
        try:
            if kv is not None:
                self._kv_begin(state, kv)
            out = self.model.model(input_ids=tokens[:, None], attention_mask=state.attn,
                                   position_ids=state.next_pos[:, None], past_key_values=state.cache,
                                   use_cache=True)
            completed = True
        finally:
            self.hook.write_enabled = False
            self.hook.injection = None
            self._kv_end(state.rows, kv, completed)
        state.next_pos = state.next_pos + 1
        state.consumed.append(tokens.clone())
        state.tick += 1
        h = out.last_hidden_state[:, -1, :]
        z = self.hook.captured
        if z is None or z.shape != (state.rows, self.d):
            raise RuntimeError("step capture failed")
        return self._lm_logits(h), h, z

    def injection(self, state: State, plan: Plan, log: TickLog | None = None) -> torch.Tensor | None:
        rows = state.rows
        if not plan.writes:
            if log is not None:
                log.unmatched.append(torch.zeros(rows, dtype=torch.bool, device=self.device))
                log.energy_ratio.append(torch.full((rows,), math.nan, device=self.device))
            return None
        if plan.static is not None:
            inj = plan.gain * plan.static
            unmatched = torch.zeros(rows, dtype=torch.bool, device=self.device)
            energy = torch.full((rows,), math.nan, device=self.device)
        else:
            receive = plan.donor >= 0
            src = state.mailbox.index_select(0, plan.donor.clamp(min=0)).float()
            res = apply_transform(src, plan.transform, q=plan.q, idx=plan.idx)
            inj = plan.gain * res.message
            inj[~receive] = 0.0
            unmatched = (res.unmatched & receive) if res.unmatched is not None else \
                torch.zeros(rows, dtype=torch.bool, device=self.device)
            energy = torch.where(receive, res.energy_ratio, torch.full_like(res.energy_ratio, math.nan)) \
                if res.energy_ratio is not None else torch.full((rows,), math.nan, device=self.device)
        if log is not None:
            log.unmatched.append(unmatched)
            log.energy_ratio.append(energy)
        return inj

    def _log_tick(self, log: TickLog, state: State, tokens: torch.Tensor, inj: torch.Tensor | None,
                  z: torch.Tensor) -> None:
        host = self.hook.host_rms
        log.tokens.append(tokens.clone())
        log.inj_ratio.append(rms(inj) / torch.clamp(host, min=1e-12) if inj is not None
                             else torch.zeros(state.rows, device=self.device))
        log.msg_norm.append(state.mailbox.float().norm(dim=-1))
        nan = torch.full((state.rows,), math.nan, device=self.device)
        log.kv_mass.append(self.last_kv_mass if self.last_kv_mass is not None else nan)
        log.kv_mass_cr.append(self.last_kv_mass_cr if self.last_kv_mass_cr is not None else nan)
        if self.last_kv_span_mass is not None:
            log.kv_span_mass.append(self.last_kv_span_mass.cpu())
            log.kv_query_pos.append((state.next_pos - 1).cpu())
        if self.last_kv_bank_mass is not None:
            log.kv_bank_mass.append(self.last_kv_bank_mass.cpu())
        if state.rows % 2 == 0:
            log.cos_pair.append(torch.nn.functional.cosine_similarity(z[0::2], z[1::2], dim=-1))

    def advance(self, state: State, logits: torch.Tensor, z: torch.Tensor, tau: int, update_messages: bool) -> None:
        """Commit the tick: EMA/mailbox update (all active rows) and next pending token."""
        if update_messages:
            state.ema = ema_update(state.ema, z, tau)
            state.mailbox = self._messages(state.ema)
        state.logits = logits
        state.pending = self.no_eos_argmax(logits)

    # -- phases -----------------------------------------------------------------------

    @torch.no_grad()
    def generate_notes(self, prefixes: list[list[int]], max_new: int = NOTE_MAX_TOKENS) -> list[list[int]]:
        """Greedy notes (bridge off, EOS allowed); returns token ids without EOS.

        Rows that finished keep receiving padding here only because notes are discarded
        states: the note tokens are re-prefilled into fresh prefixes afterwards.
        """
        state = self.prefill(prefixes)
        logits = state.logits
        notes: list[list[int]] = [[] for _ in prefixes]
        done = torch.zeros(len(prefixes), dtype=torch.bool, device=self.device)
        for _ in range(max_new):
            nxt = logits.argmax(dim=-1)
            is_eos = torch.isin(nxt, self.eos)
            for i in range(len(prefixes)):
                if not done[i] and not is_eos[i]:
                    notes[i].append(int(nxt[i]))
            done |= is_eos
            if bool(done.all()):
                break
            feed = torch.where(done, torch.full_like(nxt, self.pad_id), nxt)
            logits, _, _ = self.step(state, feed, None)
        return notes

    @torch.no_grad()
    def run_reflection(self, state: State, plan: Plan, ticks: int = REFLECTION_TICKS, write: bool = True
                       ) -> dict[str, Any]:
        """Phase C: ``ticks`` lockstep ticks; with write=False (RO) messages still update.

        Returns stacked per-tick diagnostics (tokens, injection/host RMS ratio, message norm,
        energy-matching failures, energy ratio, A-B cosine).
        """
        log = TickLog()
        state.phase = "C"
        for _ in range(ticks):
            inj = self.injection(state, plan, log) if write else None
            if not write:
                log.unmatched.append(torch.zeros(state.rows, dtype=torch.bool, device=self.device))
                log.energy_ratio.append(torch.full((state.rows,), math.nan, device=self.device))
            tokens = state.pending
            logits, _, z = self.step(state, tokens, inj, kv=plan.kv if write else None)
            self.advance(state, logits, z, plan.tau, update_messages=True)
            self._log_tick(log, state, tokens, inj, z)
        result = log.stacked()
        geometry = self.kv_condition_identity(state, plan.kv)
        if geometry is not None:
            result["kv_geometry"] = geometry
        return result

    @torch.no_grad()
    def run_readout(self, snapshot: State, branches: list[tuple[int, str]], suffixes: torch.Tensor,
                    arm: ArmConfig, static_rules: list[str | None], generate: int = 0,
                    mask_idx: torch.Tensor | None = None,
                    require_tick: int | None = REFLECTION_TICKS) -> dict[str, Any]:
        """Phase R for a chunk of branches with equal suffix length.

        ``branches``: (pair index in the snapshot, recipient role). ``suffixes``: [n, L] tokens
        the recipients consume. FULL/RO keep the bridge on with the donor continuing its own
        reflection; RF runs recipients alone with the bridge off (donor frozen).
        Returns per branch: fp32 label logits/logprobs/mass, bridge diagnostics for the
        recipient row, and exactly ``generate`` EOS-masked tokens if requested.
        """
        if resolve_profile(arm.model_profile) != self.profile:
            raise ValueError("readout arm and engine model profiles differ")
        if snapshot.phase != "C" or (require_tick is not None and snapshot.tick != require_tick):
            raise RuntimeError(f"readouts must branch from the C{require_tick} snapshot "
                               f"(phase={snapshot.phase}, tick={snapshot.tick})")
        n, length = suffixes.shape
        full = arm.readout_mode in ("FULL", "RO") and arm.direction != "none"
        rec_rows, don_rows = [], []
        for p, role in branches:
            rec_rows.append(2 * p + (0 if role == "A" else 1))
            don_rows.append(2 * p + (1 if role == "A" else 0))
        if full:
            idx = [r for pair in zip(rec_rows, don_rows) for r in pair]
            roles: list[str] = []
            rules: list[str | None] = []
            for i, (_, role) in enumerate(branches):
                partner = "B" if role == "A" else "A"
                roles += [role, partner]
                # STATIC writes only into A rows; the vector encodes the pair's B rule.
                rules += [static_rules[i] if role == "A" else None, static_rules[i] if partner == "A" else None]
            state = select_rows(snapshot, idx, self.model.config)
            plan = make_plan(arm, roles, rules, self.cal, self.device, mask_idx, self.d)
            recip = torch.arange(0, 2 * n, 2, device=self.device)
        else:
            state = select_rows(snapshot, rec_rows, self.model.config)
            plan = Plan(arm.tau, 0.0, "none", torch.full((n,), -1, dtype=torch.long, device=self.device))
            recip = torch.arange(n, device=self.device)
        state.phase = "R"
        geometry = self.kv_condition_identity(state, plan.kv)
        suffixes = suffixes.to(self.device)
        log = TickLog()
        last_h = None
        for t in range(length):
            tokens = state.pending.clone()
            tokens[recip] = suffixes[:, t]
            inj = self.injection(state, plan, log) if full else None
            logits, h, z = self.step(state, tokens, inj, kv=plan.kv if full else None)
            self.advance(state, logits, z, plan.tau, update_messages=full)
            if full:
                self._log_tick(log, state, tokens, inj, z)
            last_h = h
        rec_h = last_h.index_select(0, recip)
        logits32 = self.fp32_logits(rec_h)
        logprobs = torch.log_softmax(logits32, dim=-1)
        out = {
            "label_logits": logits32.index_select(1, self.label_ids),
            "label_logprobs": logprobs.index_select(1, self.label_ids),
            "label_mass": logprobs.index_select(1, self.label_ids).exp().sum(dim=-1),
        }
        if geometry is not None:
            out["kv_geometry"] = [geometry[i] for i in recip.tolist()]
        if log.kv_span_mass:
            out["r_kv_span_mass"] = torch.stack(log.kv_span_mass, 1).index_select(0, recip.cpu())
            out["r_kv_query_pos"] = torch.stack(log.kv_query_pos, 1).index_select(0, recip.cpu())
        if log.kv_bank_mass:
            out["r_kv_bank_mass"] = torch.stack(log.kv_bank_mass, 1).index_select(0, recip.cpu())
        if full and log.inj_ratio:
            # Per-tick recipient diagnostics [n, L]; donors sit at recip + 1 in the paired layout.
            out["r_inj_ratio"] = torch.stack(log.inj_ratio, 1).index_select(0, recip)
            out["r_unmatched"] = torch.stack(log.unmatched, 1).index_select(0, recip)
            out["r_energy_ratio"] = torch.stack(log.energy_ratio, 1).index_select(0, recip)
            out["r_donor_tokens"] = torch.stack(log.tokens, 1).index_select(0, recip + 1)
            out["r_inj_ratio_mean"] = out["r_inj_ratio"].mean(dim=1)
            out["r_unmatched_ticks"] = out["r_unmatched"].sum(dim=1)
            if plan.kv is not None:
                out["r_kv_mass"] = torch.stack(log.kv_mass, 1).index_select(0, recip)  # [n, L] per tick
                out["r_kv_mass_mean"] = out["r_kv_mass"].mean(dim=1)
                out["r_kv_mass_cr_mean"] = torch.stack(log.kv_mass_cr, 1).index_select(0, recip).mean(dim=1)
        if generate:
            generated = torch.empty(n, generate, dtype=torch.long, device=self.device)
            rec_logits = state.logits.index_select(0, recip)
            glog = TickLog()
            for g in range(generate):
                nxt = self.no_eos_argmax(rec_logits)
                generated[:, g] = nxt
                if g == generate - 1:
                    break  # the last output token need not be consumed
                tokens = state.pending.clone()
                tokens[recip] = nxt
                inj = self.injection(state, plan, glog) if full else None
                logits, _, z = self.step(state, tokens, inj, kv=plan.kv if full else None)
                self.advance(state, logits, z, plan.tau, update_messages=full)
                if full and plan.kv is not None and plan.kv.log_spans:
                    self._log_tick(glog, state, tokens, inj, z)
                rec_logits = logits.index_select(0, recip)
            out["generated"] = generated
            if glog.kv_span_mass:
                out["g_kv_span_mass"] = torch.stack(glog.kv_span_mass, 1).index_select(0, recip.cpu())
                out["g_kv_query_pos"] = torch.stack(glog.kv_query_pos, 1).index_select(0, recip.cpu())
            if glog.kv_bank_mass:
                out["g_kv_bank_mass"] = torch.stack(glog.kv_bank_mass, 1).index_select(0, recip.cpu())
            if full and glog.unmatched:
                out["g_unmatched_ticks"] = torch.stack(glog.unmatched, 1).index_select(0, recip).sum(dim=1)
        return out
