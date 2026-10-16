"""Isolated numerical prototype; importing it neither imports torch nor runs models.

This module is not wired to any scientific runner. It cannot certify a numerical
amendment, authorize hardware, or infer a whole-experiment speedup.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from mb.v6_flex_compile import FlexCompilation, mark_structure

VERSION = "v6-efficient-prototype-3"
KERNELS = ("efficient_sdpa", "compiled_flex")


def bias_policy() -> dict[str, str]:
    """Declare the new engineering candidate without replacing the v1 contract."""
    return {"version": VERSION,
            "efficient_sdpa": "query_dtype_before_aligned_slice",
            "compiled_flex": "float32_score_bias",
            "oracle": "float64_scores_with_unrounded_log_gain",
            "scope": "unadopted_engineering_candidate"}


@dataclass(frozen=True)
class Layout:
    batch: int
    heads: int
    kv_heads: int
    queries: int
    prefix: int
    foreign: int
    dimension: int
    gain: float

    def __post_init__(self) -> None:
        for key in ("batch", "heads", "kv_heads", "queries", "dimension"):
            value = getattr(self, key)
            if type(value) is not int or value < 1:
                raise ValueError(f"Positive integer required: {key}")
        if (type(self.prefix) is not int or self.prefix < 0
                or type(self.foreign) is not int or not 0 <= self.foreign <= 16):
            raise ValueError("Invalid own prefix or foreign window")
        if self.heads % self.kv_heads:
            raise ValueError("Query heads must be divisible by KV heads")
        if isinstance(self.gain, bool) or not math.isfinite(self.gain) or self.gain < 0:
            raise ValueError("Finite nonnegative gain required")

    @property
    def own(self) -> int:
        return self.prefix + self.queries

    @property
    def shapes(self) -> tuple[tuple[int, ...], ...]:
        b, h, t, d = self.batch, self.kv_heads, self.queries, self.dimension
        return ((b, self.heads, t, d), (b, h, self.own, d), (b, h, self.own, d),
                (b, h, self.foreign, d), (b, h, self.foreign, d))

    def check_shapes(self, arrays: tuple[Any, ...]) -> None:
        if len(arrays) != 5 or tuple(tuple(x.shape) for x in arrays) != self.shapes:
            raise ValueError("Unsupported/ragged layout; no padding or implicit broadcast")


def validate_numpy(layout: Layout, arrays: tuple[np.ndarray, ...]) -> None:
    layout.check_shapes(arrays)
    if any(not np.issubdtype(x.dtype, np.floating) or not np.isfinite(x).all() for x in arrays):
        raise ValueError("Finite floating arrays required")


def scalar_oracle(layout: Layout, arrays: tuple[np.ndarray, ...]) -> np.ndarray:
    """Independent FP64 loops: no vector mask/score builder or candidate helper.

    On hardware, supply the already quantized tensor values, not pre-cast random
    samples. This oracle tests an operator; it is not a complete-model oracle.
    """
    validate_numpy(layout, arrays)
    q, k, v, fk, fv = arrays
    output = np.empty(layout.shapes[0], dtype=np.float64)
    for lane in range(layout.batch):
        for head in range(layout.heads):
            kv_head = head // (layout.heads // layout.kv_heads)
            for token in range(layout.queries):
                scores, values = [], []
                for position in range(layout.prefix + token + 1):
                    score = math.fsum(float(q[lane, head, token, i]) * float(k[lane, kv_head, position, i])
                                      for i in range(layout.dimension)) / math.sqrt(layout.dimension)
                    scores.append(score)
                    values.append(v[lane, kv_head, position])
                if layout.gain > 0:
                    for position in range(layout.foreign):
                        score = math.fsum(float(q[lane, head, token, i]) * float(fk[lane, kv_head, position, i])
                                          for i in range(layout.dimension)) / math.sqrt(layout.dimension)
                        scores.append(score + math.log(layout.gain))
                        values.append(fv[lane, kv_head, position])
                peak = max(scores)
                weights = [math.exp(x - peak) for x in scores]
                total = math.fsum(weights)
                for i in range(layout.dimension):
                    output[lane, head, token, i] = math.fsum(
                        w * float(value[i]) for w, value in zip(weights, values)) / total
    if not np.isfinite(output).all():
        raise ValueError("Oracle overflow/nonfinite output")
    return output


def numpy_joint(layout: Layout, arrays: tuple[np.ndarray, ...]) -> np.ndarray:
    """Separate vector implementation, for offline adversarial oracle checks."""
    validate_numpy(layout, arrays)
    q, k, v, fk, fv = (x.astype(np.float64) for x in arrays)
    own_mask = np.arange(layout.own)[None] <= layout.prefix + np.arange(layout.queries)[:, None]
    mask = np.where(own_mask, 0., -np.inf)
    if layout.gain > 0 and layout.foreign:
        k, v = np.concatenate((k, fk), axis=2), np.concatenate((v, fv), axis=2)
        mask = np.concatenate((mask, np.full((layout.queries, layout.foreign), math.log(layout.gain))), axis=1)
    repeats = layout.heads // layout.kv_heads
    k, v = np.repeat(k, repeats, axis=1), np.repeat(v, repeats, axis=1)
    scores = np.matmul(q, k.swapaxes(-1, -2)) * (layout.dimension ** -.5) + mask
    weights = np.exp(scores - scores.max(axis=-1, keepdims=True))
    return np.matmul(weights / weights.sum(axis=-1, keepdims=True), v)


def diagnostic_error(reference: np.ndarray, actual: np.ndarray, value_scale: float) -> dict:
    """Report errors without conferring numerical/scientific admission."""
    if (reference.shape != actual.shape or not np.isfinite(reference).all()
            or not np.isfinite(actual).all() or not math.isfinite(value_scale) or value_scale < 0):
        raise ValueError("Malformed numerical comparison")
    difference = np.asarray(actual, dtype=np.float64) - reference
    maximum = float(np.max(np.abs(difference)))
    return {"max_abs": maximum, "rms": float(np.sqrt(np.mean(difference ** 2))),
            "max_abs_over_value_scale": maximum / value_scale if value_scale else None,
            "exact": bool(np.array_equal(reference, actual)), "admitted": False}


class JointKernel:
    """Explicit fused-only CUDA candidate; no silent math fallback.

    Callers validate finite, owned inputs before timing and check outputs after
    each operation. Concatenation, mask creation, casts and head expansion remain
    inside the measured call. No source tensor is mutated.
    """

    def __init__(self, kind: str):
        if kind not in KERNELS:
            raise ValueError("Select an explicit supported kernel")
        self.kind = kind
        self._compiled = None

    def __call__(self, layout: Layout, arrays: tuple[Any, ...]) -> Any:
        layout.check_shapes(arrays)
        import torch
        q, k, v, fk, fv = arrays
        if (q.device.type != "cuda" or q.dtype not in (torch.bfloat16, torch.float32)
                or any(x.device != q.device or x.dtype != q.dtype or x.requires_grad for x in arrays)):
            raise ValueError("Homogeneous CUDA BF16/FP32 inference tensors required")
        active = bool(layout.foreign and layout.gain > 0)
        if active:
            k, v = torch.cat((k, fk), dim=2), torch.cat((v, fv), dim=2)
        if self.kind == "compiled_flex":
            if self._compiled is None:
                from torch.nn.attention.flex_attention import flex_attention

                def fused(query, key, value, own_end, prefix, log_gain):
                    mark_structure(query, key, value)
                    def modify(score, batch, head, query_index, key_index):
                        foreign = key_index >= own_end
                        visible = foreign | (key_index <= prefix + query_index)
                        biased = score + torch.where(foreign, log_gain, 0.)
                        return torch.where(visible, biased, -float("inf"))
                    return flex_attention(query, key, value, score_mod=modify, enable_gqa=True)

                self._compiled = FlexCompilation(fused)
            return self._compiled(q, k, v,
                torch.tensor(layout.own, device=q.device),
                torch.tensor(layout.prefix, device=q.device),
                torch.tensor(math.log(layout.gain) if active else 0., device=q.device, dtype=torch.float32))
        from torch.nn.attention import SDPBackend, sdpa_kernel
        # The pinned efficient CUDA kernel requires bias and query dtypes to
        # match. Allocate in that dtype before slicing to retain aligned rows;
        # casting a sliced mask can compact away the stride padding. BF16 gain
        # rounding remains subject to the unchanged independent oracle screen.
        width = k.shape[2]
        mask = torch.zeros((layout.queries, ((width + 7) // 8) * 8), device=q.device, dtype=q.dtype)
        mask = mask[:, :width]
        visible = torch.arange(layout.own, device=q.device)[None] <= (
            layout.prefix + torch.arange(layout.queries, device=q.device)[:, None])
        mask[:, :layout.own].masked_fill_(~visible, -math.inf)
        if active:
            mask[:, layout.own:] = math.log(layout.gain)
        groups = layout.heads // layout.kv_heads
        # Explicit expansion avoids reliance on unsupported fused GQA dispatch.
        k, v = k.repeat_interleave(groups, dim=1), v.repeat_interleave(groups, dim=1)
        with sdpa_kernel(SDPBackend.EFFICIENT_ATTENTION):
            return torch.nn.functional.scaled_dot_product_attention(q, k, v,
                attn_mask=mask[None, None], dropout_p=0., is_causal=False)

    def compilation_report(self) -> dict | None:
        return self._compiled.report() if self._compiled is not None else None


@dataclass(frozen=True)
class TickSnapshot:
    """Immutable logical windows for one engineering-only paired tick."""
    tick: int
    windows: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]

    def __post_init__(self) -> None:
        if type(self.tick) is not int or self.tick < 0 or type(self.windows) is not tuple or not self.windows:
            raise ValueError("Nonnegative tick and immutable nonempty cohort required")
        for pair in self.windows:
            if type(pair) is not tuple or len(pair) != 2:
                raise ValueError("Exactly two immutable sides per pair required")
            for window in pair:
                if type(window) is not tuple or len(window) > 16 or any(
                        not isinstance(x, str) or not x for x in window):
                    raise ValueError("Immutable bounded windows required")

    def incoming(self) -> tuple[tuple[str, ...], ...]:
        return tuple(window for pair in self.windows for window in (pair[1], pair[0]))

    def publish(self, exports: tuple[str, ...], *, window: int = 16) -> "TickSnapshot":
        if (len(exports) != 2 * len(self.windows) or type(window) is not int
                or not 1 <= window <= 16 or any(not isinstance(x, str) or not x for x in exports)):
            raise ValueError("A complete paired barrier and bounded window are required")
        updated = tuple(tuple((pair[s] + (exports[2*i+s],))[-window:] for s in (0, 1))
                        for i, pair in enumerate(self.windows))
        return TickSnapshot(self.tick + 1, updated)
