"""Offline tests for arm configuration (protocol v0.5 §5-7); no torch needed."""

from __future__ import annotations

import pytest

from mb.conditions import ArmConfig, ContractIncomplete


def test_names_and_derived_properties():
    one = ArmConfig("ONE", layer=18, gain=0.3, form="ema")
    assert one.name == "ONE/L18/ema/g0.3/FULL" and one.tau == 8 and one.direction == "one"
    assert ArmConfig("TWO", gain=0.3).direction == "two"
    assert ArmConfig("C0").direction == "none" and ArmConfig("C0").name == "C0/FULL"
    assert ArmConfig("LANG_TAG").lang == "tag" and ArmConfig("LANG_UNTAG").lang == "untag"
    assert ArmConfig("CF", gain=0.3).donor_variant == "CF"
    assert ArmConfig("SCRAM", gain=0.3).transform == "scram"
    m = ArmConfig("MASK", gain=0.3, k=128, energy_mode="fixed", mask_direction="two")
    assert m.transform == "mask_fixed" and m.direction == "two"


@pytest.mark.parametrize("kwargs", [
    dict(condition="ONE"),                               # bridged arm without gain
    dict(condition="C0", gain=0.1),                      # unbridged arm with gain
    dict(condition="MASK", gain=0.3),                    # MASK without k/energy mode
    dict(condition="MASK", gain=0.3, k=16, energy_mode="matched", mask_direction="two"),
    dict(condition="LANG_TAG", recipients=("A", "B")),   # B is measured only in C0 or bridged arms (v3)
    dict(condition="LANG_TAG", readout_mode="RF"),       # RF/RO need a bridge
    dict(condition="NOPE"),
    dict(condition="ONE", gain=0.3, form="spiky"),
])
def test_invalid_arms_rejected(kwargs):
    with pytest.raises(ValueError):
        ArmConfig(**kwargs)


def test_v2_write_operators_raise_contract_incomplete():
    with pytest.raises(ContractIncomplete):
        ArmConfig("ONE", gain=0.3, write_operator="interpolate")


def test_config_hash_tracks_identity():
    arm = ArmConfig("ONE", gain=0.3)
    h = arm.config_hash("cal1", "none", "tmpl")
    assert h == arm.config_hash("cal1", "none", "tmpl")
    assert h != arm.config_hash("cal2", "none", "tmpl")
    assert h != ArmConfig("ONE", gain=0.5).config_hash("cal1", "none", "tmpl")
    assert ArmConfig("C0").identity("cal1", "none", "tmpl")["calibration_hash"] == "none"


@pytest.mark.parametrize("kwargs", [
    dict(condition="ONE", gain=float("nan")),
    dict(condition="ONE", gain=float("inf")),
    dict(condition="ONE", gain=-0.3),
    dict(condition="ONE", gain=50.0),                    # above the sanity bound
    dict(condition="ONE", gain=0.3, layer=0),
    dict(condition="ONE", gain=0.3, layer=37),
    dict(condition="ONE", gain=0.3, layer=18.0),
    dict(condition="MASK", gain=0.3, k=0, energy_mode="fixed"),
    dict(condition="MASK", gain=0.3, k=-4, energy_mode="fixed"),
    dict(condition="MASK", gain=0.3, k=4096, energy_mode="fixed"),
    dict(condition="MASK", gain=0.3, k=16, energy_mode="fixed", mask_direction="tow"),
    dict(condition="ONE", gain=0.3, k=16),               # MASK-only field on another arm
    dict(condition="C0", recipients=()),
    dict(condition="C0", recipients=("A", "A")),
    dict(condition="C0", recipients=("A", "C")),
])
def test_malformed_arm_parameters_rejected(kwargs):
    """Review M2 I6: parameters that would silently run no bridge or the wrong one."""
    with pytest.raises(ValueError):
        ArmConfig(**kwargs)



def test_kv_pc_arms():
    """Protocol v3: split weights for the partner's prefill (gain) and C/R segment (kv_w_live)."""
    a = ArmConfig("TWO", gain=2.0, interface="kv", kv_scope="PC", kv_w_live=0.3, recipients=("A", "B"))
    assert a.name == "TWO/KV-PC/w2+0.3/FULL" and not a.needs_calibration
    assert ArmConfig("ONE", gain=0.6, interface="kv", kv_scope="ALL", recipients=("A", "B")).recipients == ("A", "B")
    for bad in (dict(condition="ONE", gain=2.0, interface="kv", kv_scope="PC"),
                dict(condition="ONE", gain=2.0, interface="kv", kv_scope="PC", kv_w_live=-1.0),
                dict(condition="ONE", gain=2.0, interface="kv", kv_scope="P", kv_w_live=0.3)):
        with pytest.raises(ValueError):
            ArmConfig(**bad)


def test_third_person_partner_frame():
    """Protocol v3 control: only one-way KV arms may present the donor's memory in the third person."""
    a = ArmConfig("ONE", gain=2.0, interface="kv", kv_scope="P", partner_frame="third")
    assert a.name == "ONE/KV-P/w2/3p/FULL"
    for bad in (dict(condition="TWO", gain=2.0, interface="kv", kv_scope="P", partner_frame="third"),
                dict(condition="ONE", gain=0.2, partner_frame="third"),
                dict(condition="ONE", gain=2.0, interface="kv", kv_scope="P", partner_frame="first")):
        with pytest.raises(ValueError):
            ArmConfig(**bad)


def test_strict_third_person_frame_is_named_apart():
    a = ArmConfig("ONE", gain=0.8, interface="kv", kv_scope="P", partner_frame="third_strict")
    assert a.name == "ONE/KV-P/w0.8/3ps/FULL"
    with pytest.raises(ValueError):
        ArmConfig("TWO", gain=0.8, interface="kv", kv_scope="P", partner_frame="third_strict")
