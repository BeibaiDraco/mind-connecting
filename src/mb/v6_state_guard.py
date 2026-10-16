"""Temporary byte-equality guard; public SHA256/archive checks remain unchanged."""
from __future__ import annotations

import json
from typing import Any
import numpy as np


def _metadata_bytes(metadata: dict) -> bytes:
    return json.dumps(metadata,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def array_snapshot(metadata: dict, arrays: tuple[np.ndarray, ...]) -> tuple:
    """CPU oracle for byte semantics, including signed zero and all NaN bits."""
    return _metadata_bytes(metadata), tuple((a.shape, a.dtype.str, a.tobytes(order="C")) for a in arrays)


def verify_arrays(snapshot: tuple, metadata: dict, arrays: tuple[np.ndarray, ...]) -> None:
    if snapshot != array_snapshot(metadata, arrays):
        raise RuntimeError("Protected state bytes or metadata changed")


class DeviceStateGuard:
    """Own full GPU reference bytes; one final device flag, never approximate."""

    def __init__(self, backend: Any, states: tuple[Any, ...]):
        import torch
        if not states or len({id(s) for s in states}) != len(states):
            raise ValueError("Distinct protected states required")
        self._backend, self._states = backend, states
        self._metadata, self._bytes, self._shapes = [], [], []
        with backend._lock, torch.no_grad():
            for state in states:
                backend._check_state(state)
                tensors = self._tensors(state)
                if any(t.device.type != "cuda" for t in tensors):
                    raise ValueError("Device guard requires CUDA tensors")
                self._metadata.append(self._meta(state))
                self._shapes.append(tuple((tuple(t.shape), t.dtype, t.device) for t in tensors))
                self._bytes.append(tuple(t.detach().contiguous().reshape(-1).view(torch.uint8).clone()
                                         for t in tensors))

    def _meta(self, state: Any) -> bytes:
        return _metadata_bytes({"state": self._backend._state_metadata(state),
                                "seal_checksum": state.seal_checksum})

    @staticmethod
    def _tensors(state: Any) -> tuple:
        return (state.native_logits, state.last_hidden,
                *tuple(t for layer in state.cache.layers for t in (layer.keys, layer.values)))

    def verify(self) -> None:
        import torch
        flags = []
        with self._backend._lock, torch.no_grad():
            for state, metadata, shapes, snapshots in zip(
                    self._states, self._metadata, self._shapes, self._bytes, strict=True):
                self._backend._check_state(state)
                tensors = self._tensors(state)
                if (self._meta(state) != metadata
                        or tuple((tuple(t.shape), t.dtype, t.device) for t in tensors) != shapes):
                    raise RuntimeError("Protected state metadata/layout changed")
                flags.extend((t.detach().contiguous().reshape(-1).view(torch.uint8) == saved).all()
                             for t, saved in zip(tensors, snapshots, strict=True))
            if not bool(torch.stack(flags).all()):
                raise RuntimeError("Protected state bytes changed")
