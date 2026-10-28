"""V7 logical bank geometry and declared-span provenance (no torch dependency).

Positions are zero-based and intervals are half-open. Padding never enters these
identities. Spans describe the fixed P bank, including its note and closing prompt.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    import torch

Span = tuple[str, int, int]
PLACEMENTS = ("native", "before_own")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def placement_contract(position: str) -> dict:
    if position not in PLACEMENTS:
        raise ValueError(f"unknown KV placement: {position!r}")
    return {"version": 1, "position": position, "bank": "complete_valid_P",
            "coordinates": "logical_unpadded_half_open", "key_operation": "read_time_R(delta)_fp32",
            "delta_rule": "own_start-donor_end" if position == "before_own" else "zero",
            "values": "unchanged", "cache": "unchanged"}


def bank_metadata(tokens: list[int], spans: list[Span]) -> dict:
    if not tokens:
        raise ValueError("a P bank must contain at least one token")
    names: set[str] = set()
    declared = []
    for name, start, end in spans:
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("span names must be nonempty and unique within each row")
        if (type(start) is not int or type(end) is not int
                or not 0 <= start <= end <= len(tokens)):
            raise ValueError(f"span {name!r} must be a half-open logical interval within P")
        names.add(name)
        entry = {"name": name, "start": start, "end": end,
                 "token_sha256": digest(tokens[start:end])}
        entry["sha256"] = digest(entry)
        declared.append(entry)
    return {"length": len(tokens), "token_sha256": digest(tokens), "spans": declared}


def resolve_geometry(own: dict, donor: dict, position: str, *, log_spans: bool = True) -> dict:
    """Resolve an arm rule for one receiving row, independent of batch padding."""
    contract = placement_contract(position)
    delta = -donor["length"] if position == "before_own" else 0
    spans = []
    if log_spans:
        for bank, meta, shift in (("own", own, 0), ("donor", donor, delta)):
            for span in meta["spans"]:
                spans.append({**span, "bank": bank, "delta": shift,
                              "apparent_start": span["start"] + shift,
                              "apparent_end": span["end"] + shift})
    result = {**contract, "delta": delta, "own_range": [0, own["length"]],
              "source_range": [0, donor["length"]],
              "destination_range": [delta, donor["length"] + delta],
              "source_position_map": {"start": 0, "stop": donor["length"], "step": 1},
              "own_prefix_sha256": own["token_sha256"],
              "donor_prefix_sha256": donor["token_sha256"], "spans": spans}
    result["sha256"] = digest(result)
    return result


def rephase_keys(keys: torch.Tensor, delta: torch.Tensor, selected: torch.Tensor,
                 inv_freq: torch.Tensor, rotate_half: Callable[[torch.Tensor], torch.Tensor]) -> torch.Tensor:
    """Rotate a copied fp32 partner-key view; never write through to cached K/V.

    keys: [rows, KV heads, 1, length, dim]; delta: [rows]; selected: [rows,length].
    Frequencies and pairing come from the loaded model. Existing rotary amplitude
    scaling is already present in cached keys and must not be applied again.
    """
    import torch

    if keys.dtype != torch.float32:
        raise ValueError("read-time rephasing requires fp32 keys")
    if keys.shape[-1] != 2 * inv_freq.numel():
        raise ValueError("rotary frequencies do not cover the key head dimension")
    if not bool((delta != 0).any()):
        return keys  # Preserve the original arithmetic exactly for delta = 0.
    phase = delta.float()[:, None] * inv_freq.float()[None, :]
    phase = torch.cat((phase, phase), dim=-1)[:, None, None, None, :]
    rotated = keys * phase.cos() + rotate_half(keys) * phase.sin()
    use = selected & (delta[:, None] != 0)
    return torch.where(use[:, None, None, :, None], rotated, keys)
