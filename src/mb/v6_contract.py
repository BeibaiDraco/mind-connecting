"""Torch-free interfaces for the unfrozen continuous-interaction implementation."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Protocol


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Export:
    token: int
    position: int
    digest: str
    payload: Any = field(repr=False, compare=False)

    def identity(self) -> dict[str, Any]:
        return {"token": self.token, "position": self.position, "digest": self.digest}


@dataclass
class Probe:
    state: Any
    token: int
    probability: float
    legal_logits: tuple[float, float, float, float]
    legal_mass: float
    token_ids: tuple[int, int, int, int]

    def validate(self) -> None:
        values = (*self.legal_logits, self.probability, self.legal_mass)
        if not all(math.isfinite(x) for x in values):
            raise ValueError("Non-finite native readout")
        if len(set(self.token_ids)) != 4 or len(self.legal_logits) != 4:
            raise ValueError("Four distinct native answer tokens required")
        if not 0 <= self.probability <= 1 or not 0 <= self.legal_mass <= 1.000001:
            raise ValueError("Invalid native probability")


class Backend(Protocol):
    """Each state is one model history; exported payloads must be immutable copies."""

    def create(self, system: str, user: str) -> Any: ...
    def clone(self, state: Any) -> Any: ...
    def digest(self, state: Any) -> str: ...
    def decode(self, exports: tuple[Export, ...]) -> str: ...
    def begin_user(self, state: Any, text: str) -> None: ...
    def finish_turn(self, state: Any, foreign: tuple[Export, ...] = (),
                    gain: float = 0.0) -> None: ...
    def step(self, state: Any, foreign: tuple[Export, ...], gain: float) -> Export: ...
    def probe(self, state: Any, question: str, choice_labels: tuple[str, str, str, str],
              foreign: tuple[Export, ...], gain: float) -> Probe: ...
    def commit_answer(self, probe: Probe, foreign: tuple[Export, ...], gain: float) -> Any: ...


@dataclass(frozen=True)
class RuntimeSpec:
    work_tokens: int = 64
    preparation_tokens: int = 16
    window: int = 16
    gain: float = 0.5
    choice_labels: tuple[str, str, str, str] = ("1", "2", "3", "4")
    status: str = "draft_local_only"

    def __post_init__(self) -> None:
        if min(self.work_tokens, self.window) < 1 or self.preparation_tokens < 0:
            raise ValueError("Invalid work/window/preparation length")
        if not math.isfinite(self.gain) or self.gain < 0:
            raise ValueError("Invalid channel gain")
        if self.status != "draft_local_only":
            raise ValueError("This implementation has no authorized formal mode")
        if len(set(self.choice_labels)) != 4:
            raise ValueError("Four distinct choice labels required")
