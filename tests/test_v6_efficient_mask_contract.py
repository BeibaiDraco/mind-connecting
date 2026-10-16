"""Exercise real mask-building code through a CPU API double, never CUDA.

Dtype tags are symbolic: these checks catch dispatch/layout regressions, not
BF16 rounding, kernel correctness or model equivalence.
"""

import math
import sys
from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import pytest

from mb.v6_efficient import JointKernel, Layout


class ArrayTensor:
    device = SimpleNamespace(type="cuda")
    requires_grad = False

    def __init__(self, array, dtype):
        self.array, self.dtype = array, dtype

    @property
    def shape(self):
        return self.array.shape

    def __getitem__(self, index):
        return ArrayTensor(self.array[index], self.dtype)

    def __setitem__(self, index, value):
        self.array[index] = value

    def masked_fill_(self, mask, value):
        self.array[mask] = value
        return self

    def repeat_interleave(self, repeats, dim):
        return ArrayTensor(np.repeat(self.array, repeats, axis=dim), self.dtype)


@pytest.mark.parametrize("dtype", ("bfloat16", "float32"))
@pytest.mark.parametrize("prefix,queries,foreign,gain", (
    (0, 1, 0, .5), (7, 4, 16, 0.), (7, 1, 1, .25),
    (7, 4, 16, .25), (7, 4, 16, .5), (7, 4, 16, 1.),
))
def test_sdpa_dispatch_dtype_alignment_and_mask_semantics(monkeypatch, dtype, prefix, queries, foreign, gain):
    layout = Layout(2, 4, 2, queries, prefix, foreign, 16, gain)
    tensors = tuple(ArrayTensor(np.arange(np.prod(shape), dtype=np.float32).reshape(shape), dtype)
                    for shape in layout.shapes)
    originals = tuple(x.array.copy() for x in tensors)
    calls = []
    active = bool(foreign and gain > 0)
    width = layout.own + (foreign if active else 0)

    @contextmanager
    def sdpa_kernel(backend):
        assert backend == "efficient_only"
        calls.append("enter")
        yield
        calls.append("exit")

    def dispatch(q, k, v, *, attn_mask, dropout_p, is_causal):
        assert calls == ["enter"]
        assert q is tensors[0]
        assert q.dtype == k.dtype == v.dtype == attn_mask.dtype
        assert attn_mask.device == q.device
        assert attn_mask.shape == (1, 1, queries, width)
        mask = attn_mask.array[0, 0]
        assert mask.strides[-1] == mask.itemsize
        assert mask.strides[-2] // mask.itemsize % 8 == 0
        assert dropout_p == 0. and is_causal is False
        for query in range(queries):
            for position in range(width):
                value = mask[query, position]
                if position < layout.own:
                    assert value == (0. if position <= prefix + query else -math.inf)
                else:
                    assert value == pytest.approx(math.log(gain), rel=1e-7, abs=1e-7)
        for actual, own, incoming in ((k, tensors[1], tensors[3]), (v, tensors[2], tensors[4])):
            expected = np.concatenate((own.array, incoming.array), axis=2) if active else own.array
            np.testing.assert_array_equal(actual.array, np.repeat(expected, 2, axis=1))
        calls.append("dispatch")
        return "checked_boundary_only"

    def zeros(shape, *, device, dtype):
        assert device == tensors[0].device
        return ArrayTensor(np.zeros(shape, dtype=np.float32), dtype)

    def cat(values, dim):
        assert len({x.dtype for x in values}) == 1
        return ArrayTensor(np.concatenate([x.array for x in values], axis=dim), values[0].dtype)

    api = SimpleNamespace(bfloat16="bfloat16", float32="float32", zeros=zeros, cat=cat,
        arange=lambda n, **kwargs: np.arange(n),
        nn=SimpleNamespace(functional=SimpleNamespace(scaled_dot_product_attention=dispatch)))
    attention = SimpleNamespace(SDPBackend=SimpleNamespace(EFFICIENT_ATTENTION="efficient_only"),
                                sdpa_kernel=sdpa_kernel)
    monkeypatch.setitem(sys.modules, "torch", api)
    monkeypatch.setitem(sys.modules, "torch.nn.attention", attention)
    assert JointKernel("efficient_sdpa")(layout, tensors) == "checked_boundary_only"
    assert calls == ["enter", "dispatch", "exit"]
    for original, tensor in zip(originals, tensors):
        np.testing.assert_array_equal(original, tensor.array)
