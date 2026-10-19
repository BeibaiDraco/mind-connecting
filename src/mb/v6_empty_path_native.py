"""Unadmitted repair for the packed backend's single-history readout path.

Preserves native execution when there is no effective incoming state. This does
not certify or change consume_many/step_many, linked inference or a formal run.
"""
from typing import Any

from mb.v6_batch_native import PackedBackend
from mb.v6_native import NativeBackend, NativeState
from mb.v6_contract import Export, canonical_digest


class EmptyPathNativeBackend(PackedBackend):
    status = "single_history_empty_path_repair_not_admitted"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.model_identity = canonical_digest({"packed": self.model_identity,
            "repair": "single-history-native-empty-path-v1", "science": False})

    def _consume(self, state: NativeState, ids: tuple[int, ...],
                 foreign: tuple[Export, ...] = (), gain: float = 0.) -> None:
        if not foreign or gain == 0:
            return NativeBackend._consume(self, state, ids, foreign, gain)
        return super()._consume(state, ids, foreign, gain)
