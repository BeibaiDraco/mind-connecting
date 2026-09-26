"""Bridge math: normalization, EMA, transforms, STATIC vectors (protocol v0.5 §6, §11.12-13).

Needs torch but not a GPU; skipped on machines without torch (the local Mac).
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from mb import bridge  # noqa: E402
from mb.conditions import ContractIncomplete  # noqa: E402

D = 64


def _cal(sigma: float = 3.0) -> bridge.LayerCalibration:
    g = torch.Generator().manual_seed(0)
    return bridge.LayerCalibration(18, torch.randn(D, generator=g), torch.rand(D, generator=g) + 0.5, sigma)


def test_normalize_hits_sigma_and_clips():
    cal = _cal()
    e = torch.randn(5, D) * 4 + cal.mu
    m = bridge.normalize(e, cal)
    assert torch.allclose(bridge.rms(m), torch.full((5,), cal.sigma_in), atol=1e-4)
    spike = cal.mu.clone().unsqueeze(0)
    spike[0, 0] += 1e6  # one huge coordinate is clipped to 5 sd before rescaling
    m2 = bridge.normalize(spike, cal)
    assert torch.isfinite(m2).all() and m2[0, 0] > 0
    zero = bridge.normalize(cal.mu.unsqueeze(0), cal)  # all-zero centered vector stays zero
    assert torch.count_nonzero(zero) == 0


def test_ema_tau1_is_raw_and_impulse_decays_by_7_over_8():
    z = torch.randn(3, D)
    assert torch.equal(bridge.ema_update(torch.zeros(3, D), z, 1), z)
    e = torch.zeros(1, D)
    impulse = torch.ones(1, D)
    e = bridge.ema_update(e, impulse, 8)
    assert torch.allclose(e, impulse / 8)
    e2 = bridge.ema_update(e, torch.zeros(1, D), 8)
    assert torch.allclose(e2, e * 7 / 8)


def test_scram_preserves_norm_and_masks_are_nested():
    q = bridge.scram_matrix(D, seed=1)
    x = torch.randn(4, D)
    assert torch.allclose((x @ q.T).norm(dim=-1), x.norm(dim=-1), atol=1e-4)
    assert torch.equal(q, bridge.scram_matrix(D, seed=1))
    masks = bridge.nested_mask_indices(D, seed=2, ks=(4, 16, 32))
    assert set(masks[4].tolist()) <= set(masks[16].tolist()) <= set(masks[32].tolist())
    assert bridge.mask_hash(masks[4]) == bridge.mask_hash(bridge.nested_mask_indices(D, 2, (4,))[4])


def test_mask_fixed_and_energy_matched():
    idx = torch.tensor([0, 1, 2, 3])
    m = torch.randn(3, D)
    fixed = bridge.apply_transform(m, "mask_fixed", idx=idx).message
    assert torch.count_nonzero(fixed[:, 4:]) == 0 and torch.equal(fixed[:, :4], m[:, :4])
    res = bridge.apply_transform(m, "mask_matched", idx=idx)
    assert torch.allclose(res.message.norm(dim=-1), m.norm(dim=-1), atol=1e-4)
    assert torch.count_nonzero(res.message[:, 4:]) == 0 and not res.unmatched.any()
    edge = torch.zeros(2, D)
    edge[1, 10] = 1.0  # support has no energy -> flagged, not silently rescaled
    res2 = bridge.apply_transform(edge, "mask_matched", idx=idx)
    assert res2.unmatched.tolist() == [False, True]
    assert torch.count_nonzero(res2.message) == 0


def test_static_vectors_rms_and_unusable():
    msgs = torch.randn(400, D)
    rules = ["cost"] * 200 + ["speed"] * 200
    msgs[:200] += 2.0  # strong rule-dependent shift
    vec, bad = bridge.static_vectors(msgs, rules, sigma_in=3.0, form="raw")
    assert set(vec) == {"raw:cost", "raw:speed"} and not bad
    assert torch.allclose(bridge.rms(vec["raw:cost"].unsqueeze(0)), torch.tensor([3.0]), atol=1e-4)
    same = torch.randn(1, D).repeat(10, 1)
    vec2, bad2 = bridge.static_vectors(same, ["cost"] * 5 + ["speed"] * 5, sigma_in=3.0, form="ema")
    assert not vec2 and sorted(bad2) == ["ema:cost", "ema:speed"]


def test_v2_transforms_raise():
    with pytest.raises(ContractIncomplete):
        bridge.apply_transform(torch.zeros(1, D), "interpolate")


def test_calibration_roundtrip_and_hash():
    cal = _cal()
    cal.static = {"raw:cost": torch.ones(D)}
    back = bridge.LayerCalibration.from_state_dict(cal.state_dict())
    assert back.hash() == cal.hash()
