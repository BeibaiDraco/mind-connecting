"""Experimental arms: condition name -> donor mapping, gain, transform, readout mode, identity.

Implements the arm vocabulary of protocol v0.5 §5-7. An arm fixes everything that is
constant across the episodes of one batch; per-episode content (donor variants, LANG
text) is resolved by the runtime.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass


class ContractIncomplete(NotImplementedError):
    """Raised for v2 branches (interpolation writes, KV sharing) that v1 must not run."""


CONDITIONS = ("C0", "ONE", "TWO", "STATIC", "LANG_TAG", "LANG_UNTAG", "CF", "MISMATCH", "SCRAM", "MASK",
              "LANG_SELF", "LANG_STRANGER")
LANG_MODES = {"LANG_TAG": "tag", "LANG_UNTAG": "untag", "LANG_SELF": "self", "LANG_STRANGER": "stranger"}
INTERFACES = ("residual", "kv")  # v1 residual addition; v2 KV reading (protocol v2 §4)
KV_SCOPES = ("C", "ALL", "P", "PC")  # C: partner's C/R tokens; ALL: whole valid cache; P: prefill only;
# PC: whole valid cache with separate weights for the prefill (gain) and the C/R segment (kv_w_live) (protocol v3)
KV_CONDITIONS = ("ONE", "TWO", "CF", "MISMATCH")  # live-donor conditions that have a KV version
READOUT_MODES = ("FULL", "RF", "RO")
PARTNER_FRAMES = ("second", "third", "third_strict")  # mirrors tasks.FRAMES; conditions stays tokenizer-free
FORMS = {"raw": 1, "ema": 8}  # message form -> tau
MODEL_REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
N_LAYERS = 36  # Qwen3-4B-Instruct-2507; the engine re-checks against the loaded model
D_MODEL = 2560
MAX_GAIN = 10.0


@dataclass(frozen=True)
class ArmConfig:
    condition: str
    readout_mode: str = "FULL"
    layer: int = 18  # 1-indexed block
    gain: float = 0.0
    form: str = "raw"
    k: int | None = None  # MASK: injection support size
    energy_mode: str | None = None  # MASK: "fixed" | "matched"
    mask_direction: str = "one"  # MASK: "one" | "two"
    scram_seed: int = 20260923
    mask_seed: int = 20260924
    recipients: tuple[str, ...] = ("A",)
    write_operator: str = "add"
    interface: str = "residual"  # "kv": the receiver's attention also reads the partner's KV cache; gain = weight w
    kv_scope: str | None = None  # kv only: "C" (partner's C/R tokens) or "ALL" (partner's whole valid cache)
    kv_w_live: float | None = None  # kv scope PC only: weight on the partner's C/R tokens (gain weighs its prefill)
    partner_frame: str = "second"  # protocol v3: "third" / "third_strict" write the donor's memory as a record

    def __post_init__(self) -> None:
        if self.condition not in CONDITIONS:
            raise ValueError(f"unknown condition {self.condition}")
        if not isinstance(self.gain, (int, float)) or not math.isfinite(self.gain):
            raise ValueError(f"gain must be a finite number, got {self.gain!r}")
        if not isinstance(self.layer, int) or not 1 <= self.layer <= N_LAYERS:
            raise ValueError(f"layer must be an integer in 1..{N_LAYERS}, got {self.layer!r}")
        if self.gain > MAX_GAIN:
            raise ValueError(f"gain {self.gain} above the sanity bound {MAX_GAIN}")
        if self.mask_direction not in ("one", "two"):
            raise ValueError(f"mask_direction must be 'one' or 'two', got {self.mask_direction!r}")
        if self.condition != "MASK" and (self.k is not None or self.energy_mode is not None
                                         or self.mask_direction != "one"):
            raise ValueError("k / energy_mode / mask_direction are only valid for MASK arms")
        if (not self.recipients or len(set(self.recipients)) != len(self.recipients)
                or not set(self.recipients) <= {"A", "B"}):
            raise ValueError(f"recipients must be a non-empty subset of A/B without repeats, got {self.recipients!r}")
        if self.readout_mode not in READOUT_MODES:
            raise ValueError(f"unknown readout mode {self.readout_mode}")
        if self.form not in FORMS:
            raise ValueError(f"unknown message form {self.form}")
        if self.write_operator != "add":
            raise ContractIncomplete(f"write operator {self.write_operator!r} is a v2 interface")
        if self.interface not in INTERFACES:
            raise ValueError(f"unknown interface {self.interface!r}")
        if self.interface == "kv":
            if self.condition not in KV_CONDITIONS:
                raise ValueError(f"{self.condition} has no KV-reading version")
            if self.kv_scope not in KV_SCOPES:
                raise ValueError(f"kv arms need kv_scope in {KV_SCOPES}, got {self.kv_scope!r}")
            if self.form != "raw":
                raise ValueError("message form does not apply to KV reading; leave it at the default")
        elif self.kv_scope is not None:
            raise ValueError("kv_scope is only valid for kv arms")
        if self.partner_frame not in PARTNER_FRAMES:
            raise ValueError(f"partner_frame must be one of {PARTNER_FRAMES}, got {self.partner_frame!r}")
        if self.partner_frame != "second" and not (self.interface == "kv" and self.direction == "one"):
            raise ValueError("the third-person partner frame is defined for one-way KV arms only")
        if self.kv_scope == "PC":
            if not isinstance(self.kv_w_live, (int, float)) or not math.isfinite(self.kv_w_live) or self.kv_w_live < 0:
                raise ValueError(f"KV-PC needs a finite kv_w_live >= 0, got {self.kv_w_live!r}")
        elif self.kv_w_live is not None:
            raise ValueError("kv_w_live is only valid for kv_scope PC")
        if self.bridged and self.gain <= 0:
            raise ValueError(f"{self.condition} needs a positive gain")
        if not self.bridged and self.gain != 0:
            raise ValueError(f"{self.condition} must have gain 0")
        if self.condition == "MASK":
            if self.k is None or self.energy_mode not in ("fixed", "matched"):
                raise ValueError("MASK needs k and energy_mode in {fixed, matched}")
            if not isinstance(self.k, int) or not 1 <= self.k <= D_MODEL:
                raise ValueError(f"MASK k must be an integer in 1..{D_MODEL}, got {self.k!r}")
            if self.energy_mode == "matched" and self.mask_direction != "one":
                raise ValueError("energy-matched masks are run one-way only (protocol v0.5 §7)")
        if "B" in self.recipients and not self.bridged and self.condition != "C0":
            # v3 measures B in one-way bridged arms too (as a non-receiving pair member); LANG arms give B nothing.
            raise ValueError("B is a measured recipient only in C0 or bridged arms")
        if self.readout_mode != "FULL" and not self.bridged:
            raise ValueError("RF/RO only make sense for bridged arms")

    @property
    def tau(self) -> int:
        return FORMS[self.form]

    @property
    def bridged(self) -> bool:
        return self.condition != "C0" and self.condition not in LANG_MODES

    @property
    def needs_calibration(self) -> bool:
        """Residual writes are normalized by the layer calibration; KV reading uses raw caches."""
        return self.bridged and self.interface == "residual"

    @property
    def direction(self) -> str:
        """none: no hidden channel; one: A receives from B; two: both receive."""
        if not self.bridged:
            return "none"
        if self.condition == "TWO" or (self.condition == "MASK" and self.mask_direction == "two"):
            return "two"
        return "one"

    @property
    def transform(self) -> str:
        if self.condition == "SCRAM":
            return "scram"
        if self.condition == "MASK":
            return f"mask_{self.energy_mode}"
        return "none"

    @property
    def lang(self) -> str | None:
        return LANG_MODES.get(self.condition)

    @property
    def donor_variant(self) -> str | None:
        return self.condition if self.condition in ("CF", "MISMATCH") else None

    @property
    def name(self) -> str:
        parts = [self.condition]
        if self.interface == "kv":
            w = f"w{self.gain:g}" + (f"+{self.kv_w_live:g}" if self.kv_scope == "PC" else "")
            parts += [f"KV-{self.kv_scope}", w]
            if self.partner_frame != "second":
                parts.append({"third": "3p", "third_strict": "3ps"}[self.partner_frame])
        elif self.bridged:
            parts.append(f"L{self.layer}")
            parts.append(self.form)
            parts.append(f"g{self.gain:g}")
        if self.condition == "MASK":
            parts.append(f"k{self.k}-{self.energy_mode}-{self.mask_direction}")
        parts.append(self.readout_mode)
        return "/".join(parts)

    def identity(self, calibration_hash: str, mask_hash: str, template_hash: str) -> dict:
        ident = asdict(self)
        ident.update(tau=self.tau, calibration_hash=calibration_hash if self.needs_calibration else "none",
                     mask_hash=mask_hash, template_hash=template_hash, model_revision=MODEL_REVISION)
        return ident

    def config_hash(self, calibration_hash: str, mask_hash: str, template_hash: str) -> str:
        payload = json.dumps(self.identity(calibration_hash, mask_hash, template_hash), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
