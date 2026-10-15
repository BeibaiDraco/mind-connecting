"""Engineering-only homogeneous cohort/prefill adapter, never runner-selected.

No ragged packing, scientific admission, numerical equivalence certificate,
resume certification or automatic model loading is provided here.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass, field, replace
from typing import Any

from mb.v6_contract import Export, canonical_digest
from mb.v6_efficient import JointKernel, Layout, VERSION
from mb.v6_native import NativeBackend, NativeState

ATTENTION_NAME = "mb_v6_efficiency_engineering_only"
_CONTEXT: contextvars.ContextVar[Any] = contextvars.ContextVar("v6_efficiency", default=None)


@dataclass
class Context:
    modules: dict[int, int]
    foreign: tuple[tuple[Any, Any], ...]
    gain: float
    kernel: JointKernel
    seen: set[int] = field(default_factory=set)
    mask_checks: list[Any] = field(default_factory=list)


def _attention(module: Any, query: Any, key: Any, value: Any, attention_mask: Any,
               dropout: float = 0., scaling: float | None = None,
               is_causal: bool | None = None, **kwargs: Any) -> tuple[Any, None]:
    import torch
    from transformers.integrations.sdpa_attention import sdpa_attention_forward
    context = _CONTEXT.get()
    if context is None:
        raise RuntimeError("Engineering attention called without its context")
    index = context.modules.get(id(module))
    if index is None or index in context.seen or dropout:
        raise RuntimeError("Unexpected/repeated attention module or dropout")
    context.seen.add(index)
    if not context.foreign:
        return sdpa_attention_forward(module, query, key, value, attention_mask,
            dropout=dropout, scaling=scaling, is_causal=is_causal, **kwargs)
    foreign_k, foreign_v = context.foreign[index]
    layout = Layout(query.shape[0], query.shape[1], key.shape[1], query.shape[2],
        key.shape[2] - query.shape[2], foreign_k.shape[2], query.shape[3], context.gain)
    if scaling is not None and scaling != layout.dimension ** -.5:
        raise ValueError("Nonstandard attention scaling is outside this prototype")
    if attention_mask is not None:
        if (attention_mask.ndim != 4 or attention_mask.shape[0] not in (1, layout.batch)
                or attention_mask.shape[1] not in (1, layout.heads)
                or tuple(attention_mask.shape[2:]) != (layout.queries, layout.own)):
            raise ValueError("Unsupported own attention mask shape")
        expected = torch.arange(layout.own, device=query.device)[None] <= (
            layout.prefix + torch.arange(layout.queries, device=query.device)[:, None])
        if attention_mask.dtype != torch.bool:
            expected = torch.where(expected, 0., -torch.inf)
        # Keep every layer's check on-device; validate before publishing states.
        context.mask_checks.append((attention_mask == expected[None, None]).all())
    output = context.kernel(layout, (query, key, value, foreign_k, foreign_v))
    return output.transpose(1, 2).contiguous(), None


def cohort_shape(states: tuple[NativeState, ...], inputs: tuple[tuple[int, ...], ...],
                 vocabulary: int) -> tuple[int, int]:
    """Refuse ragged/aliased histories; never silently pad or repack lanes."""
    if (type(states) is not tuple or type(inputs) is not tuple or not states
            or len(states) != len(inputs) or len({id(s) for s in states}) != len(states)):
        raise ValueError("Distinct states and one input per fixed lane required")
    if any(type(s.consumed_tokens) is not tuple for s in states) or any(type(t) is not tuple for t in inputs):
        raise ValueError("Immutable input and consumed-history tuples required")
    lengths = {len(state.consumed_tokens) for state in states}
    sizes = {len(tokens) for tokens in inputs}
    if len(lengths) != 1 or len(sizes) != 1 or 0 in sizes:
        raise ValueError("Ragged histories/inputs are outside this prototype")
    if any(type(token) is not int or not 0 <= token < vocabulary for tokens in inputs for token in tokens):
        raise ValueError("Nonempty in-vocabulary integer inputs required")
    if len({id(state.cache) for state in states}) != len(states):
        raise ValueError("Cohort caches must be independently owned")
    return next(iter(lengths)), next(iter(sizes))


class EfficientPrototype(NativeBackend):
    """Existing checked native boundaries with opt-in linked prefill/cohort calls.

    The ordinary V6 runner cannot construct/select this class. Explicit cohort
    calls consume already-known tokens with held foreign windows; they do not
    implement a complete batched live scheduler. Full native finite checks are
    retained at every linked input position.
    """

    status = "engineering_prototype_not_admitted"

    def __init__(self, model: Any, tokenizer: Any, *, kernel: str, chunk: int = 4,
                 hardware_acceptance_authorized: bool = False):
        if type(chunk) is not int or chunk not in (1, 2, 4, 8, 16, 32):
            raise ValueError("Select a fixed supported chunk before hardware")
        self.joint_kernel = JointKernel(kernel)
        self.chunk = chunk
        super().__init__(model, tokenizer, hardware_acceptance_authorized=hardware_acceptance_authorized)
        from transformers import AttentionInterface
        from transformers.masking_utils import AttentionMaskInterface, sdpa_mask
        self.model_identity = canonical_digest({"native": self.model_identity,
            "prototype": VERSION, "kernel": kernel, "chunk": chunk, "scientific_admission": False})
        AttentionInterface.register(ATTENTION_NAME, _attention)
        AttentionMaskInterface.register(ATTENTION_NAME, sdpa_mask)

    @classmethod
    def from_local_cache(cls, **kwargs: Any) -> "EfficientPrototype":
        raise PermissionError("No automatic loading; use a separately authorized engineering harness")

    def _consume(self, state: NativeState, ids: tuple[int, ...],
                 foreign: tuple[Export, ...] = (), gain: float = 0.) -> None:
        if not foreign or gain == 0:
            return super()._consume(state, ids, foreign, gain)
        self.consume_cohort((state,), (ids,), (foreign,), gain)

    def consume_cohort(self, states: tuple[NativeState, ...], inputs: tuple[tuple[int, ...], ...],
                       windows: tuple[tuple[Export, ...], ...], gain: float) -> None:
        import torch
        from transformers import DynamicCache
        for state in states:
            self._check_state(state)
            if type(state) is not NativeState or state.seal is not None:
                raise ValueError("Unsealed native states required for engineering cohort")
        prefix, count = cohort_shape(states, inputs, self.tokens.vocab_size)
        if type(windows) is not tuple or any(type(w) is not tuple for w in windows) or len(windows) != len(states):
            raise ValueError("One fixed incoming window per lane required")
        if not prefix:
            raise ValueError("Initialize histories individually before cohort feasibility")
        layers = tuple(self._foreign(window, gain) for window in windows)
        if len({len(lane) for lane in layers}) != 1:
            raise ValueError("Mixed active/empty donor lanes are unsupported")
        merged_foreign = ()
        if layers[0]:
            if len({lane[0][0].shape[2] for lane in layers}) != 1:
                raise ValueError("Ragged foreign windows are unsupported")
            merged_foreign = tuple(tuple(torch.cat([lane[i][part] for lane in layers], dim=0)
                                         for part in (0, 1)) for i in range(len(self.modules)))
        copied = tuple(tuple(torch.cat([getattr(s.cache.layers[i], name) for s in states], dim=0)
                             for name in ("keys", "values")) for i in range(len(self.modules)))
        cache = DynamicCache(ddp_cache_data=copied, config=self.model.config)
        with self._lock, torch.no_grad():
            try:
                for offset in range(0, count, self.chunk):
                    group = tuple(tokens[offset:offset+self.chunk] for tokens in inputs)
                    length, size = prefix + offset, len(group[0])
                    ids = torch.tensor(group, device=self.device, dtype=torch.long)
                    positions = torch.arange(length, length + size, device=self.device)
                    context = Context(self.modules, merged_foreign, gain, self.joint_kernel)
                    previous = [c._attn_implementation for c in self._configs]
                    handle = _CONTEXT.set(context)
                    try:
                        for config in self._configs:
                            config._attn_implementation = ATTENTION_NAME
                        result = self.model.model(input_ids=ids,
                            attention_mask=torch.ones(len(states), length+size, device=self.device, dtype=torch.long),
                            position_ids=positions[None].expand(len(states), -1), cache_position=positions,
                            past_key_values=cache, use_cache=True)
                        if context.seen != set(range(len(self.modules))):
                            raise RuntimeError("A layer bypassed engineering attention")
                        hidden = result.last_hidden_state
                        logits = self.model.lm_head(hidden).float()
                        finite = torch.isfinite(hidden).all() & torch.isfinite(logits).all()
                        if context.mask_checks:
                            finite = finite & torch.stack(context.mask_checks).all()
                        if not bool(finite):
                            raise ValueError("Invalid own mask or non-finite hidden/logits at a consumed position")
                    finally:
                        _CONTEXT.reset(handle)
                        for config, implementation in zip(self._configs, previous):
                            config._attn_implementation = implementation
                # Own all resulting lane tensors; failure never commits half a
                # cohort. This copy cost is part of the prototype measurement.
                updates = []
                for lane in range(len(states)):
                    data = tuple((layer.keys[lane:lane+1].detach().clone(),
                                  layer.values[lane:lane+1].detach().clone()) for layer in cache.layers)
                    candidate = replace(states[lane],
                        cache=DynamicCache(ddp_cache_data=data, config=self.model.config),
                        last_hidden=hidden[lane:lane+1, -1].detach().clone(),
                        native_logits=logits[lane:lane+1, -1].detach().clone(),
                        consumed_tokens=states[lane].consumed_tokens + inputs[lane])
                    self._check_state(candidate)
                    updates.append(candidate)
                for state, candidate in zip(states, updates):
                    state.cache = candidate.cache
                    state.last_hidden = candidate.last_hidden
                    state.native_logits = candidate.native_logits
                    state.consumed_tokens = candidate.consumed_tokens
            except BaseException:
                for state in states:
                    state.failed = True
                raise
