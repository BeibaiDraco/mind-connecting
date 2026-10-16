"""Unrun CUDA compilation gates: real shapes, no real weights or scientific data."""
from contextlib import contextmanager
import json
import time

import pytest

torch = pytest.importorskip("torch")
pytestmark = [pytest.mark.gpu,
              pytest.mark.skipif(not torch.cuda.is_available(), reason="authorized CUDA required")]

from mb.v6_batch_native import packed_flex
from mb.v6_efficient import JointKernel, Layout


def report(kernel):
    return kernel.compilation_report() if isinstance(kernel, JointKernel) else kernel.report()


@contextmanager
def evidence(record_property, kernels):
    start = time.monotonic()
    try:
        yield
    finally:
        record_property("compilation", json.dumps([report(k) for k in kernels]))
        record_property("test_wall_seconds_including_compile", time.monotonic() - start)


def make_kernel(kind):
    return JointKernel("compiled_flex") if kind == "joint" else packed_flex()


def inputs(batch, queries, prefix, *, real_shape=False):
    h, kh, d = (32, 8, 128) if real_shape else (4, 2, 16)
    l = Layout(batch, h, kh, queries, prefix, 16, d, .5)
    # Match native projected-query strides, rather than contiguous-only probes.
    q = torch.randn(batch, queries, h, d, device="cuda", dtype=torch.bfloat16).transpose(1, 2)
    rest = tuple(torch.randn(s, device="cuda", dtype=torch.bfloat16) for s in l.shapes[1:])
    return l, (q, *rest)


def call(kernel, layout, values):
    if isinstance(kernel, JointKernel): return kernel(layout, values)
    q, k, v, fk, fv = values
    k, v = torch.cat((k, fk), 2).contiguous(), torch.cat((v, fv), 2).contiguous()
    own = torch.arange(layout.own, device="cuda")[None] <= (
        layout.prefix + torch.arange(layout.queries, device="cuda")[:, None])
    allowed = torch.cat((own, torch.ones(layout.queries, 16, device="cuda", dtype=torch.bool)), 1)
    allowed = allowed[None].expand(layout.batch, -1, -1).contiguous()
    bias = torch.zeros(k.shape[2], device="cuda", dtype=torch.float32)
    bias[layout.own:] = torch.log(torch.tensor(.5, device="cuda"))
    return kernel(q.contiguous(), k, v, allowed, bias)


@pytest.mark.parametrize("kind", ("joint", "packed"))
@pytest.mark.parametrize("queries", (1, 4))
def test_many_kv_lengths_reuse_compilation(kind, queries, record_property):
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.manual_seed(940219)
    kernel = make_kernel(kind)
    with evidence(record_property, [kernel]), torch.no_grad():
        warm_graphs = None
        for i, prefix in enumerate((7, 9, 13, 17, 19, 23, 31, 37, 47, 61, 79, 97)):
            layout, values = inputs(2, queries, prefix)
            first = call(kernel, layout, values)
            assert torch.isfinite(first).all()
            assert torch.equal(first, call(kernel, layout, values))
            count = report(kernel)["graphs_attempted"]
            if i == 2:
                warm_graphs = count
                assert 1 <= warm_graphs <= 2
            elif i > 2:
                assert count == warm_graphs, "KV growth caused repeated compilation"


@pytest.mark.parametrize("kind", ("joint", "packed"))
def test_nine_independent_compiler_owners_do_not_share_cache_limit(kind, record_property):
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.manual_seed(940220)
    kernels = []
    layout, values = inputs(2, 2, 7)
    with evidence(record_property, kernels), torch.no_grad():
        expected = None
        for _ in range(9):
            kernel = make_kernel(kind); kernels.append(kernel)
            actual = call(kernel, layout, values)
            assert torch.isfinite(actual).all()
            if expected is None: expected = actual
            else: assert torch.equal(expected, actual)
            assert report(kernel)["graphs_attempted"] == 1


@pytest.mark.parametrize("kind", ("joint", "packed"))
def test_actual_checkpoint_attention_shapes_compile_and_repeat(kind, record_property):
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.manual_seed(940221)
    kernel = make_kernel(kind)
    with evidence(record_property, [kernel]), torch.no_grad():
        for batch, queries in ((1, 1), (1, 16), (2, 1), (2, 16), (4, 1), (4, 16)):
            prefixes = tuple(4096 + 16*i for i in range(12)) if batch == 4 else (4096,)
            warm_graphs = None
            for i, prefix in enumerate(prefixes):
                layout, values = inputs(batch, queries, prefix, real_shape=True)
                actual = call(kernel, layout, values)
                assert torch.isfinite(actual).all()
                assert torch.equal(actual, call(kernel, layout, values))
                count = report(kernel)["graphs_attempted"]
                if i == 2: warm_graphs = count
                elif i > 2:
                    assert count == warm_graphs, "Production-range KV growth recompiled"
        assert report(kernel)["graphs_attempted"] <= 8
