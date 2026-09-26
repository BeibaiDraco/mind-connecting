"""Hidden-state bridge between paired instances (protocol v0.5 §6).

Read/write position: the bridge adds its injection to the *input* of decoder block
``layer`` (1-indexed) and reads the *output* of the same block, so a message returned
through the partner has passed through at least one model block.

Order of operations is fixed: raw output z -> EMA e -> subtract mu -> clip ±5 sd ->
RMS-normalize to sigma_in -> mailbox (message m) -> condition transform -> gain -> write.
Only additive writes exist in v1; interpolation and KV sharing are v2 and raise.
"""

from __future__ import annotations

import functools
import hashlib
import math
from dataclasses import dataclass, field
from typing import Any

import torch

from mb.conditions import ContractIncomplete

CLIP_SD = 5.0
SD_FLOOR = 1e-6
RMS_FLOOR_FRAC = 1e-3
STATIC_MIN_FRAC = 0.01
ENERGY_EPS_FRAC = 1e-6


# ---------------------------------------------------------------------------
# Calibration and normalization
# ---------------------------------------------------------------------------


@dataclass
class LayerCalibration:
    layer: int  # 1-indexed block
    mu: torch.Tensor  # [d] fp32 mean raw block output
    sd: torch.Tensor  # [d] fp32 per-dim std of raw outputs (floored)
    sigma_in: float  # median RMS of block inputs
    static: dict[str, torch.Tensor] = field(default_factory=dict)  # "form:rule" -> [d], RMS == sigma_in
    static_unusable: tuple[str, ...] = ()

    def to(self, device: torch.device | str) -> "LayerCalibration":
        return LayerCalibration(self.layer, self.mu.to(device), self.sd.to(device), self.sigma_in,
                                {k: v.to(device) for k, v in self.static.items()}, self.static_unusable)

    def hash(self) -> str:
        h = hashlib.sha256()
        h.update(f"{self.layer}|{self.sigma_in:.9g}".encode())
        for t in (self.mu, self.sd):
            h.update(t.detach().float().cpu().numpy().tobytes())
        for key in sorted(self.static):
            h.update(key.encode())
            h.update(self.static[key].detach().float().cpu().numpy().tobytes())
        return h.hexdigest()[:16]

    def state_dict(self) -> dict[str, Any]:
        return {"layer": self.layer, "mu": self.mu.cpu(), "sd": self.sd.cpu(), "sigma_in": self.sigma_in,
                "static": {k: v.cpu() for k, v in self.static.items()},
                "static_unusable": list(self.static_unusable)}

    @classmethod
    def from_state_dict(cls, d: dict[str, Any]) -> "LayerCalibration":
        return cls(int(d["layer"]), d["mu"].float(), d["sd"].float(), float(d["sigma_in"]),
                   {k: v.float() for k, v in d["static"].items()}, tuple(d.get("static_unusable", ())))


def normalize(e: torch.Tensor, cal: LayerCalibration) -> torch.Tensor:
    """N_ℓ: center, clip at ±5 sd, rescale to RMS sigma_in. Input/outputs are fp32 [rows, d]."""
    c = torch.clamp(e.float() - cal.mu, min=-CLIP_SD * cal.sd, max=CLIP_SD * cal.sd)
    rms = c.pow(2).mean(dim=-1, keepdim=True).sqrt()
    return cal.sigma_in * c / torch.clamp(rms, min=RMS_FLOOR_FRAC * cal.sigma_in)


MESSAGE_DTYPE = torch.bfloat16


def message(e: torch.Tensor, cal: LayerCalibration) -> torch.Tensor:
    """Mailbox value m = BF16(N_ℓ(e)): normalization in fp32, quantized at the N output.

    Transforms and gains are applied later to ``m.float()``; e itself stays fp32.
    """
    return normalize(e, cal).to(MESSAGE_DTYPE)


def ema_update(e_prev: torch.Tensor, z: torch.Tensor, tau: int) -> torch.Tensor:
    """e_t = (1 - 1/tau) e_{t-1} + z_t / tau, in fp32; tau == 1 is the raw message."""
    if tau == 1:
        return z.float()
    return (1.0 - 1.0 / tau) * e_prev + z.float() / tau


def rms(x: torch.Tensor) -> torch.Tensor:
    return x.float().pow(2).mean(dim=-1).sqrt()


def static_vectors(messages: torch.Tensor, rules: list[str], sigma_in: float, form: str
                   ) -> tuple[dict[str, torch.Tensor], list[str]]:
    """Rule-conditional mean directions from calibration messages (protocol v0.5 §6).

    ``messages``: [n, d] normalized messages of one form; ``rules``: the emitting
    instance's rule per row. Returns m_STATIC = sigma_in * v / RMS(v) per rule.
    """
    grand = messages.mean(dim=0)
    out: dict[str, torch.Tensor] = {}
    unusable: list[str] = []
    for rule in sorted(set(rules)):
        idx = torch.tensor([i for i, r in enumerate(rules) if r == rule], device=messages.device)
        v = messages.index_select(0, idx).mean(dim=0) - grand
        v_rms = float(rms(v.unsqueeze(0)))
        key = f"{form}:{rule}"
        if v_rms < STATIC_MIN_FRAC * sigma_in:
            unusable.append(key)
            continue
        out[key] = sigma_in * v / v_rms
    return out, unusable


# ---------------------------------------------------------------------------
# Condition transforms (applied to mailbox messages at write time)
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=4)
def _scram_cpu(d: int, seed: int) -> torch.Tensor:
    g = torch.Generator(device="cpu").manual_seed(seed)
    q, r = torch.linalg.qr(torch.randn(d, d, generator=g, dtype=torch.float64))
    return (q * torch.sign(torch.diagonal(r)).unsqueeze(0)).float()


def scram_matrix(d: int, seed: int, device: torch.device | str = "cpu") -> torch.Tensor:
    """Fixed random orthogonal matrix (norm-preserving, destroys the shared coordinate code)."""
    return _scram_cpu(d, seed).to(device)


def nested_mask_indices(d: int, seed: int, ks: tuple[int, ...]) -> dict[int, torch.Tensor]:
    """First-k coordinates of one fixed permutation: masks are nested across k."""
    g = torch.Generator(device="cpu").manual_seed(seed)
    perm = torch.randperm(d, generator=g)
    return {k: torch.sort(perm[:k]).values for k in ks}


def mask_hash(indices: torch.Tensor | None) -> str:
    if indices is None:
        return "none"
    return hashlib.sha256(indices.cpu().numpy().astype("int64").tobytes()).hexdigest()[:16]


@dataclass
class TransformResult:
    message: torch.Tensor
    unmatched: torch.Tensor | None = None  # bool [rows], energy-matching failures
    energy_ratio: torch.Tensor | None = None


def apply_transform(m: torch.Tensor, kind: str, *, q: torch.Tensor | None = None,
                    idx: torch.Tensor | None = None) -> TransformResult:
    if kind == "none":
        return TransformResult(m)
    if kind == "scram":
        assert q is not None
        return TransformResult(m @ q.T)
    if kind in ("mask_fixed", "mask_matched"):
        assert idx is not None
        masked = torch.zeros_like(m)
        masked[:, idx] = m[:, idx]
        full = m.norm(dim=-1)
        part = masked.norm(dim=-1)
        if kind == "mask_fixed":
            return TransformResult(masked, energy_ratio=part.pow(2) / torch.clamp(full.pow(2), min=1e-30))
        unmatched = (full > 0) & (part < ENERGY_EPS_FRAC * full)
        scale = torch.where((full > 0) & ~unmatched, full / torch.clamp(part, min=1e-30), torch.ones_like(full))
        out = masked * scale.unsqueeze(-1)
        out[full == 0] = 0.0
        return TransformResult(out, unmatched=unmatched, energy_ratio=part.pow(2) / torch.clamp(full.pow(2), min=1e-30))
    if kind in ("interpolate", "kv_share"):
        raise ContractIncomplete(f"{kind} is a v2 interface; its contract is not defined in protocol v1")
    raise ValueError(kind)


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------


class BridgeHook:
    """Pre/post hooks on one decoder block.

    - post hook: records the block output at the last position (raw, fp32) on every forward;
      in prefill this is the read-only seed capture.
    - pre hook: records the host input RMS at the last position; adds ``injection`` only if
      ``write_enabled`` and the forward processes exactly one token per row.
    """

    MODES = ("tick", "prefill", "record")

    def __init__(self, block: torch.nn.Module, layer: int, record_all: bool = False):
        self.layer = layer
        # "tick": exactly one token per row, writes allowed; "prefill": read-only, any length;
        # "record": passive observer (calibration), any length, never writes.
        self.mode = "tick"
        self.write_enabled = False
        self.injection: torch.Tensor | None = None  # [rows, d] fp32
        self.captured: torch.Tensor | None = None  # [rows, d] fp32, last position output
        self.host_rms: torch.Tensor | None = None  # [rows]
        self.record_all = record_all
        self.records: list[tuple[torch.Tensor, torch.Tensor]] = []  # (input rms, output) per forward
        self._rows = 0
        self._handles = [
            block.register_forward_pre_hook(self._pre, with_kwargs=True),
            block.register_forward_hook(self._post, with_kwargs=True),
        ]

    def _pre(self, module, args, kwargs):
        hidden = args[0] if args else kwargs["hidden_states"]
        if not isinstance(hidden, torch.Tensor) or hidden.dim() != 3:
            raise TypeError(f"layer {self.layer}: unexpected hidden_states {type(hidden)}")
        if self.mode not in self.MODES:
            raise ValueError(f"layer {self.layer}: unknown hook mode {self.mode!r}")
        if self.mode == "tick" and hidden.shape[1] != 1:
            raise RuntimeError(f"layer {self.layer}: a tick must consume exactly one token per row")
        if self.mode != "tick" and self.write_enabled:
            raise RuntimeError(f"bridge writes are disabled in {self.mode} mode")
        self._rows = hidden.shape[0]
        self.host_rms = rms(hidden[:, -1, :])
        if self.write_enabled and self.injection is not None:
            if self.injection.shape != (hidden.shape[0], hidden.shape[2]):
                raise RuntimeError(f"injection shape {tuple(self.injection.shape)} vs hidden {tuple(hidden.shape)}")
            hidden = hidden + self.injection.to(hidden.dtype).unsqueeze(1)
            if args:
                args = (hidden, *args[1:])
            else:
                kwargs = {**kwargs, "hidden_states": hidden}
        return args, kwargs

    def _post(self, module, args, kwargs, output):
        if not isinstance(output, torch.Tensor):
            raise TypeError(f"layer {self.layer}: expected Tensor output (transformers 4.57.1), got {type(output)}")
        if output.dim() != 3 or output.shape[0] != self._rows or (self.mode == "tick" and output.shape[1] != 1):
            raise RuntimeError(f"layer {self.layer}: unexpected block output shape {tuple(output.shape)}")
        self.captured = output[:, -1, :].float()
        if self.record_all:
            self.records.append((self.host_rms.clone(), self.captured.clone()))
        return None

    def reset(self) -> None:
        self.write_enabled = False
        self.injection = None
        self.captured = None
        self.host_rms = None
        self.records.clear()

    def remove(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []


def calibration_from_records(layer: int, outputs: torch.Tensor, input_rms: torch.Tensor) -> LayerCalibration:
    """mu/sd/sigma_in from raw C0 block outputs [n, d] and input RMS [n] (non-first C tokens)."""
    mu = outputs.mean(dim=0)
    sd = torch.clamp(outputs.std(dim=0), min=SD_FLOOR)
    sigma_in = float(input_rms.median())
    if not math.isfinite(sigma_in) or sigma_in <= 0:
        raise ValueError(f"layer {layer}: bad sigma_in {sigma_in}")
    return LayerCalibration(layer, mu, sd, sigma_in)
