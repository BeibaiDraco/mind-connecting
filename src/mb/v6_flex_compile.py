"""Bounded engineering compilation; imports do not load torch or models."""
from __future__ import annotations

import copy
import time
from types import FunctionType
from typing import Any, Callable

VERSION = "v6-flex-structural-specialization-1"
MAX_GRAPHS = 8


def compile_policy() -> dict:
    return {"version": VERSION, "fullgraph": True, "dynamic": True,
            "query_static_axes": [0, 1, 2, 3], "key_value_static_axes": [0, 1, 3],
            "packed_mask_static_axes": [0, 1], "key_length": "dynamic",
            "max_graphs_per_owner": MAX_GRAPHS, "cache_scope": "owned_code_object",
            "failure": "terminal_no_retry_or_eager_fallback",
            "scope": "unadopted_engineering_candidate"}


def mark_structure(query: Any, key: Any, value: Any) -> None:
    """Run inside the graph: specialize metadata without marking input objects.

    Torch 2.6 flex decoding requires concrete B/H in its split heuristic. The
    growing KV length stays symbolic; freezing every length would recompile
    each prefix. Query width has only the declared decode/prefill variants.
    """
    import torch
    for axis in (0, 1, 2, 3):
        torch._dynamo.mark_static(query, axis)
    for tensor in (key, value):
        for axis in (0, 1, 3):
            torch._dynamo.mark_static(tensor, axis)


def owned_function(function: Callable) -> Callable:
    """Isolate Dynamo's code-object cache across separate backend owners.

    The bytecode, globals, defaults and closure are unchanged. This avoids a
    tiny fixture consuming another model owner's recompile cache allowance.
    """
    owned = FunctionType(function.__code__.replace(), function.__globals__,
                         function.__name__, function.__defaults__, function.__closure__)
    owned.__kwdefaults__ = function.__kwdefaults__
    return owned


class FlexCompilation:
    """Count actual compiler callbacks, retain failure, never reset or retry."""

    def __init__(self, function: Callable):
        import torch
        from torch._dynamo.backends.registry import lookup_backend
        if torch.__version__.split("+")[0] != "2.6.0":
            raise ValueError("Flex compilation requires pinned Torch 2.6.0")
        if torch._dynamo.config.suppress_errors:
            raise ValueError("Eager fallback must not suppress compilation failures")
        self._events: list[dict] = []
        self._failed = False
        self._inductor = lookup_backend("inductor")
        self._function = owned_function(function)
        self._compiled = torch.compile(self._function, backend=self._compile,
                                       fullgraph=True, dynamic=True)

    def _compile(self, graph: Any, inputs: list[Any]) -> Callable:
        if self._failed or len(self._events) >= MAX_GRAPHS:
            self._failed = True
            raise RuntimeError("Flex compilation budget exhausted; no retry")
        event = {"index": len(self._events) + 1, "status": "started",
                 "input_shapes": [list(map(str, x.shape)) for x in inputs if hasattr(x, "shape")]}
        self._events.append(event)
        start = time.monotonic()
        try:
            result = self._inductor(graph, inputs)
            event["status"] = "compiled"
            return result
        except BaseException as exc:
            self._failed = True
            event.update(status="failed", error_type=type(exc).__name__)
            raise
        finally:
            event["compiler_seconds"] = time.monotonic() - start

    def __call__(self, *args: Any) -> Any:
        if self._failed:
            raise RuntimeError("Failed flex compiler cannot retry")
        try:
            return self._compiled(*args)
        except BaseException:
            self._failed = True
            raise

    def report(self) -> dict:
        return {"policy": compile_policy(), "failed": self._failed,
                "graphs_attempted": len(self._events),
                "compiler_seconds": sum(x.get("compiler_seconds", 0.) for x in self._events),
                "events": copy.deepcopy(self._events),
                "timing_scope": "inductor_callback_only_not_total_first_call_or_cuda_time"}
