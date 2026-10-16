"""Torch-free dispatch/bookkeeping tests; do not claim CUDA compatibility."""
from types import SimpleNamespace
import json
import subprocess
import sys

import pytest

from mb.v6_flex_compile import (FlexCompilation, MAX_GRAPHS, compile_policy,
                                mark_structure, owned_function)


def fake_torch(monkeypatch, *, failure=None, suppress=False, version="2.6.0"):
    seen = {"compile": [], "inductor": []}
    def inductor(graph, inputs):
        seen["inductor"].append((graph, inputs))
        if failure is not None:
            raise failure
        return lambda *args: (graph, args)
    def compile_fn(function, **kwargs):
        seen["compile"].append((function, kwargs))
        # Simulate a new graph per call so exhaustion is tested, not inferred.
        return lambda *args: kwargs["backend"]("graph", list(args))(*args)
    def lookup(name):
        assert name == "inductor"
        return inductor
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(__version__=version,
        compile=compile_fn, _dynamo=SimpleNamespace(config=SimpleNamespace(suppress_errors=suppress))))
    monkeypatch.setitem(sys.modules, "torch._dynamo.backends.registry", SimpleNamespace(lookup_backend=lookup))
    return seen


def test_import_is_inert():
    subprocess.run([sys.executable, "-c",
        "import mb.v6_flex_compile; import sys; assert 'torch' not in sys.modules"], check=True)


def test_owned_code_preserves_body_defaults_and_closure_without_shared_cache():
    offset = 7
    def original(x=3, *, y=2): return offset + x + y
    a, b = owned_function(original), owned_function(original)
    assert a() == b() == original() == 12
    assert a(4, y=5) == original(4, y=5)
    assert a.__code__ is not b.__code__ and a.__code__ is not original.__code__
    assert a.__code__.co_code == original.__code__.co_code
    assert a.__closure__ is original.__closure__ and a.__globals__ is original.__globals__


def test_only_structural_dimensions_are_specialized_inside_graph(monkeypatch):
    seen = []
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(
        _dynamo=SimpleNamespace(mark_static=lambda tensor, axis: seen.append((tensor, axis)))))
    q, k, v = object(), object(), object()
    mark_structure(q, k, v)
    assert seen == [(q, a) for a in (0, 1, 2, 3)] + [(x, a) for x in (k, v) for a in (0, 1, 3)]
    assert (k, 2) not in seen and (v, 2) not in seen


def test_compile_is_fullgraph_with_symbolic_kv_and_unmodified_global_limits(monkeypatch):
    seen = fake_torch(monkeypatch)
    def fused(x): return x
    c = FlexCompilation(fused)
    fn, options = seen["compile"][0]
    assert fn.__code__ is not fused.__code__
    assert options == {"backend": c._compile, "fullgraph": True, "dynamic": True}
    assert c("x") == ("graph", ("x",))
    report = c.report()
    assert report["graphs_attempted"] == 1 and report["compiler_seconds"] >= 0
    assert report["events"][0]["status"] == "compiled"
    report["events"][0]["status"] = "tampered"
    assert c.report()["events"][0]["status"] == "compiled"
    json.dumps(c.report(), allow_nan=False)


def test_compile_cap_is_checked_before_inductor_and_never_reset(monkeypatch):
    seen = fake_torch(monkeypatch)
    c = FlexCompilation(lambda x: x)
    for _ in range(MAX_GRAPHS): c("x")
    with pytest.raises(RuntimeError, match="budget exhausted"): c("x")
    assert len(seen["inductor"]) == MAX_GRAPHS
    with pytest.raises(RuntimeError, match="cannot retry"): c("x")
    assert c.report()["failed"] and len(seen["inductor"]) == MAX_GRAPHS


def test_compile_error_retains_elapsed_attempt_and_prevents_second_attempt(monkeypatch):
    seen = fake_torch(monkeypatch, failure=TypeError("symbolic shape"))
    c = FlexCompilation(lambda x: x)
    with pytest.raises(TypeError, match="symbolic shape"): c("x")
    with pytest.raises(RuntimeError, match="cannot retry"): c("x")
    report = c.report()
    assert len(seen["inductor"]) == report["graphs_attempted"] == 1
    assert report["events"][0]["error_type"] == "TypeError"
    assert report["events"][0]["compiler_seconds"] >= 0


@pytest.mark.parametrize("failure", [ValueError("trace failed"), KeyboardInterrupt()])
def test_trace_or_runtime_failure_without_compiler_callback_also_stays_terminal(monkeypatch, failure):
    fake_torch(monkeypatch)
    c = FlexCompilation(lambda x: x)
    def fail(*_): raise failure
    c._compiled = fail
    with pytest.raises(type(failure)): c("x")
    assert c.report()["failed"] and c.report()["graphs_attempted"] == 0
    with pytest.raises(RuntimeError, match="cannot retry"): c("x")


@pytest.mark.parametrize("kwargs", [{"suppress": True}, {"version": "2.7.0"}])
def test_wrong_environment_or_eager_fallback_refused(monkeypatch, kwargs):
    seen = fake_torch(monkeypatch, **kwargs)
    with pytest.raises(ValueError): FlexCompilation(lambda x: x)
    assert not seen["compile"] and not seen["inductor"]


def test_owner_reports_are_independent(monkeypatch):
    fake_torch(monkeypatch)
    a, b = FlexCompilation(lambda x: x), FlexCompilation(lambda x: x)
    a("x")
    assert a.report()["graphs_attempted"] == 1 and b.report()["graphs_attempted"] == 0
    assert a._function.__code__ is not b._function.__code__


def test_policy_is_explicit_detached_and_engineering_only():
    a = compile_policy(); a["key_value_static_axes"].append(2)
    b = compile_policy()
    assert b["key_value_static_axes"] == [0, 1, 3] and b["max_graphs_per_owner"] == 8
    assert b["scope"] == "unadopted_engineering_candidate"
