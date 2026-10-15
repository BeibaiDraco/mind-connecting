"""Opt-in V6 engineering candidates; no production wiring or execution authority.

The frozen backend remains the reference. These changes preserve its arithmetic,
readouts, checks and archives' logical payloads. Native equivalence and speed are
UNVERIFIED until a separately protected CUDA comparison passes.
"""

from __future__ import annotations

import math
import time
from collections import Counter, OrderedDict
from contextlib import contextmanager
from functools import wraps
from typing import Any, Iterator

from mb.v6_native import (ARCHIVE_VERSION, NativeBackend, _primitives,
                          _tensor_hash, _tensor_stamp)

VERSION = "v6-performance-candidate-1"
MAX_COPY_BYTES = 4 * 1024 * 1024


def copy_payload_to_cpu(tensors: tuple[Any, ...], *, tensor_api: Any,
                        max_bytes: int = MAX_COPY_BYTES) -> list[Any]:
    """Pack small tensors into bounded transfers; retain owned contiguous values.

    Oversized tensors use the reference path, avoiding a second large GPU buffer.
    CPU views can share a newly owned transfer buffer, never the source storage.
    This changes serialization layout, not tensor values or logical checksums.
    """
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("A positive copy buffer bound is required")
    result: list[Any] = []
    pending: list[Any] = []
    size = 0

    def flush() -> None:
        nonlocal size
        if not pending:
            return
        raw = tensor_api.cat([t.detach().contiguous().reshape(-1).view(tensor_api.uint8)
                              for t in pending])
        owned = raw.to("cpu")
        offset = 0
        for tensor in pending:
            length = tensor.numel() * tensor.element_size()
            result.append(owned[offset:offset + length].view(tensor.dtype).reshape(tensor.shape))
            offset += length
        pending.clear()
        size = 0

    for tensor in tensors:
        length = tensor.numel() * tensor.element_size()
        # Different element sizes can misalign a dtype view into the raw buffer.
        if pending and (size + length > max_bytes
                        or tensor.device != pending[0].device
                        or tensor.dtype != pending[0].dtype):
            flush()
        if length > max_bytes:
            flush()
            result.append(tensor.detach().to("cpu").contiguous().clone())
        else:
            pending.append(tensor)
            size += length
    flush()
    return result


class PerformanceBackend(NativeBackend):
    """Reference inference with bounded foreign-window reuse and packed archives.

    Construction still requires NativeBackend's explicit CUDA authorization.
    No tensor validation, checksum, sample, token or forward pass is omitted.
    Cache hits revalidate source tensors AND the cached concatenations. The two
    windows are retained strongly to prevent object-id reuse or dangling data.
    """

    performance_version = VERSION

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._window_cache: OrderedDict = OrderedDict()
        self.performance_counts: Counter = Counter()

    def _foreign(self, exports: tuple, gain: float) -> tuple:
        import torch

        if not math.isfinite(gain) or gain < 0:
            raise ValueError("Channel gain must be finite and nonnegative")
        # The reference zero-gain route performs ALL source validation without
        # materializing a concatenation. Actual gain is applied by attention.
        super()._foreign(exports, 0.0)
        if not exports or gain == 0:
            return ()
        key = tuple((id(e.payload), e.token, e.position, e.digest) for e in exports)
        if key in self._window_cache:
            _, layers, stamps = self._window_cache[key]
            if tuple(_tensor_stamp(t) for layer in layers for t in layer) != stamps:
                raise ValueError("Cached foreign K/V tensor was modified")
            self._window_cache.move_to_end(key)
            self.performance_counts["window_hits"] += 1
            return layers
        layers = tuple((torch.cat([e.payload.layers[i][0] for e in exports], dim=2),
                        torch.cat([e.payload.layers[i][1] for e in exports], dim=2))
                       for i in range(len(self.modules)))
        stamps = tuple(_tensor_stamp(t) for layer in layers for t in layer)
        self._window_cache[key] = (exports, layers, stamps)
        self.performance_counts["window_misses"] += 1
        if len(self._window_cache) > 2:
            self._window_cache.popitem(last=False)
        return layers

    def _archive_from_cpu(self, kind: str, metadata: dict, copies: list) -> dict:
        payload = {"version": ARCHIVE_VERSION, "kind": kind,
                   "model_identity": self.model_identity, "metadata": _primitives(metadata)}
        return {**payload, "tensors": copies, "sha256": _tensor_hash(payload, tuple(copies))}

    def _archive(self, kind: str, metadata: dict, tensors: tuple) -> dict:
        import torch

        copies = copy_payload_to_cpu(tensors, tensor_api=torch)
        self.performance_counts["archive_tensors"] += len(copies)
        return self._archive_from_cpu(kind, metadata, copies)

    def dump_export(self, export: Any) -> dict:
        import torch

        self._foreign((export,), 0.0)
        tensors = tuple(t for layer in export.payload.layers for t in layer)
        copies = copy_payload_to_cpu(tensors, tensor_api=torch)
        metadata = {"token": export.token, "position": export.position,
                    "model_identity": self.model_identity}
        # Validate the exact bytes that will be saved, with the reference hash.
        if _tensor_hash(metadata, tuple(copies)) != export.digest:
            raise ValueError("Export payload checksum differs before archive")
        self.performance_counts["archive_tensors"] += len(copies)
        return self._archive_from_cpu("export", {**metadata, "payload_digest": export.digest}, copies)


PROFILE_METHODS = ("create", "clone", "digest", "begin_user", "finish_turn", "step",
                   "probe", "commit_answer", "decode", "_consume", "_foreign",
                   "_archive", "dump_state", "dump_export")


@contextmanager
def profile_backend(backend: Any) -> Iterator[dict]:
    """Count nested native operations and inclusive host wall time, without sync.

    Timing is diagnostic: nested times overlap and GPU work can be asynchronous.
    Whole-episode wall time remains the speed/cost measurement. No prompts,
    answers, model outputs, credentials or connection information are recorded.
    """
    missing = object()
    previous_flag = backend.__dict__.get("_v6_profile_active", missing)
    if getattr(backend, "_v6_profile_active", False):
        raise ValueError("Backend already has an active profiler")
    backend._v6_profile_active = True
    stats: dict[str, Any] = {"version": VERSION, "calls": {}, "host_seconds_inclusive": {},
                             "failures": {}, "linked_calls": {}}
    previous: dict[str, Any] = {}

    def wrapper(name: str, method: Any) -> Any:
        @wraps(method)
        def measured(*args: Any, **kwargs: Any) -> Any:
            stats["calls"][name] = stats["calls"].get(name, 0) + 1
            if name in ("step", "probe"):
                index = 1 if name == "step" else 3
                foreign = kwargs.get("foreign", args[index] if len(args) > index else ())
                if foreign:
                    stats["linked_calls"][name] = stats["linked_calls"].get(name, 0) + 1
            start = time.perf_counter()
            try:
                return method(*args, **kwargs)
            except BaseException:
                stats["failures"][name] = stats["failures"].get(name, 0) + 1
                raise
            finally:
                times = stats["host_seconds_inclusive"]
                times[name] = times.get(name, 0.0) + time.perf_counter() - start
        return measured

    start = time.perf_counter()
    try:
        for name in PROFILE_METHODS:
            if hasattr(backend, name):
                previous[name] = backend.__dict__.get(name, missing)
                setattr(backend, name, wrapper(name, getattr(backend, name)))
        yield stats
    finally:
        for name, value in previous.items():
            if value is missing:
                delattr(backend, name)
            else:
                setattr(backend, name, value)
        stats["wall_seconds"] = time.perf_counter() - start
        if previous_flag is missing:
            del backend._v6_profile_active
        else:
            backend._v6_profile_active = previous_flag


def workload_audit(*, text_reference: bool = False) -> dict:
    """Execute the real scheduler with a fixture, never load or score a model."""
    from mb.v6_contract import RuntimeSpec
    from mb.v6_run import SyntheticBackend
    from mb.v6_runtime import EpisodeRunner
    from mb.v6_tasks import make_episodes

    # Shorten only the fixture clock. Report the adopted 64/16-token workload
    # algebra separately; this fixture is not an experiment or a speed estimate.
    spec = RuntimeSpec(work_tokens=4, preparation_tokens=2, window=2)
    backend = SyntheticBackend()
    archives: Counter = Counter()
    runner = EpisodeRunner(backend, spec, "synthetic",
                           artifact_sink=lambda event: archives.update([event["kind"]]))
    with profile_backend(backend) as profile:
        rows = runner.run_episode(make_episodes(1, stage="development", seed=731)[0],
                                  text_reference=text_reference)
    periods = len(runner.audit) // spec.work_tokens
    natural_initializations = profile["calls"]["create"] // 2
    return {"version": VERSION, "scientific_data": False,
            "purpose": "scheduler operation count, not a GPU timing or outcome",
            "fixture_work_tokens": spec.work_tokens,
            "text_reference": text_reference, "paired_work_periods": periods,
            "work_tokens_at_frozen_clock": periods * 2 * 64,
            "preparation_tokens_at_frozen_clock": natural_initializations * 2 * 16,
            "text_tokens_at_frozen_clock": 6 * 2 * 64 if text_reference else 0,
            "readouts": len(rows), "archives": dict(archives),
            "readouts_by_kind": dict(Counter(row["kind"] for row in rows)),
            "fixture_backend_calls": profile["calls"]}
