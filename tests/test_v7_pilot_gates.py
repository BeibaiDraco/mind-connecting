"""V7 pilot gates (protocol V7 §7 step 2) on synthetic records."""

from __future__ import annotations

import json

import pytest

from mb import v7_run, v7_tasks as material
from v7_synthetic import default_choice, load_script, records, run_dir

gates = load_script("v7_pilot_gates")
EPISODES = material.make_episodes(10, "v7_dev", "base")
GATE_QIDS = ("USE", "CAP0", "CAP1")


def policy(fullinfo=10, c0_fact=2, c0_cf=1, orig_fact=8, orig_cf=7, cap_wrong=()):
    """Episode counts choosing each USE meaning; ``cap_wrong`` lists (arm, qid, episode, rotation slot)."""
    def choose(arm, qid, i, rotation):
        if qid == "USE":
            if arm == "c0_fullinfo":
                return "fact" if i < fullinfo else "other"
            if arm == "c0":
                return "fact" if i < c0_fact else "cf" if i < c0_fact + c0_cf else "other"
            if arm == "orig_w2":
                return "fact" if i < orig_fact else "other"
            if arm == "orig_w2_cf":
                return "cf" if i < orig_cf else "other"
        if qid in ("CAP0", "CAP1"):
            slot = EPISODES[i].base.rotations.index(rotation)
            return "wrong" if (arm, qid, i, slot) in cap_wrong else "correct"
        return default_choice(qid)
    return choose


def build(choose, mass=lambda arm: 0.99):
    return records(EPISODES, choose, GATE_QIDS, mass)


def test_values_are_exact_and_all_gates_pass():
    out = gates.evaluate(build(policy(cap_wrong={("trans_w1", "CAP0", 0, 0)})))
    g = out["gates"]
    assert g["U1"]["value"] == 1.0 and g["U2"]["value"] == pytest.approx(0.2)
    assert g["U3_fact"]["value"] == pytest.approx(0.6) and g["U3_cf"]["value"] == pytest.approx(0.6)
    assert out["cap_drop_by_arm"]["trans_w1"] == pytest.approx(0.025)
    assert out["cap_drop_by_arm"]["orig_w2"] == 0.0 and set(out["cap_drop_by_arm"]) == set(gates.LINKED_ARMS)
    assert out["all_pass"] and out["n_episodes"] == 10


def test_thresholds_are_inclusive_without_rounding_error():
    wrong = {("same_trans_w2", "CAP0", 0, 0), ("same_trans_w2", "CAP1", 3, 1)}  # 2 of 40 items: exactly 5 points
    out = gates.evaluate(build(policy(fullinfo=9, c0_fact=4, c0_cf=0, orig_fact=10, orig_cf=4, cap_wrong=wrong)))
    g = out["gates"]
    assert g["U1"]["value"] == pytest.approx(0.9) and g["U1"]["pass"]
    assert g["U2"]["value"] == pytest.approx(0.4) and g["U2"]["pass"]
    assert g["U3_cf"]["value"] == pytest.approx(0.4) and g["U3_cf"]["pass"]
    assert out["cap_drop_by_arm"]["same_trans_w2"] == pytest.approx(0.05) and g["Q1_cap"]["pass"]


@pytest.mark.parametrize("change, failing", [
    (dict(fullinfo=8), "U1"), (dict(c0_fact=5), "U2"), (dict(orig_fact=4), "U3_fact"), (dict(orig_cf=3), "U3_cf"),
    (dict(cap_wrong={("orig_w1", "CAP0", 0, 0), ("orig_w1", "CAP0", 1, 0), ("orig_w1", "CAP1", 2, 1)}), "Q1_cap"),
])
def test_each_gate_can_fail(change, failing):
    out = gates.evaluate(build(policy(**change)))
    assert [name for name, g in out["gates"].items() if not g["pass"]] == [failing]
    assert not out["all_pass"]


def test_label_mass_gate_is_per_arm():
    out = gates.evaluate(build(policy(), mass=lambda arm: 0.94 if arm == "third_trans_w2" else 0.99))
    assert not out["gates"]["Q1_mass"]["pass"] and out["gates"]["Q1_mass"]["min_mass"] == pytest.approx(0.94)
    assert out["use_assay_valid"] and not out["quality_ok"]


class Guarded(dict):
    """A record whose outcome fields must not be read by the gates."""

    def __getitem__(self, key):
        if key not in ("arm_id", "qid", "label_mass"):
            raise AssertionError(f"gate read {key} of {dict.__getitem__(self, 'arm_id')}/{dict.__getitem__(self, 'qid')}")
        return dict.__getitem__(self, key)

    get = __getitem__


def test_no_ownership_outcome_or_translated_use_is_read():
    choose = policy()
    rows = records(EPISODES, choose)
    protected = [Guarded(r) if r["qid"] not in GATE_QIDS or (r["qid"] == "USE" and r["arm_id"] not in gates.USE_ARMS)
                 else r for r in rows]
    assert any(isinstance(r, Guarded) and r["qid"] == "START" for r in protected)
    assert any(isinstance(r, Guarded) and r["qid"] == "USE" for r in protected)
    out = gates.evaluate(protected)
    assert out["all_pass"]
    assert set(out["use_rates"]["fact"]) == set(gates.USE_ARMS)


def test_duplicate_and_unpaired_records_are_rejected():
    rows = build(policy())
    with pytest.raises(ValueError, match="duplicate"):
        gates.evaluate(rows + [rows[0]])
    first = rows[0]["episode_id"]
    with pytest.raises(ValueError):
        gates.evaluate([r for r in rows if not (r["arm_id"] == "orig_w2" and r["episode_id"] == first)])


def test_cli_writes_gates_but_dev_runs_are_never_consumable(tmp_path):
    cfg = v7_run.V7Config("v7_dev", "base", 12)
    root = run_dir(tmp_path, cfg, lambda arm, qid, i, rot: (
        "fact" if qid == "USE" and arm in ("c0_fullinfo", "orig_w2") else
        "cf" if qid == "USE" and arm == "orig_w2_cf" else default_choice(qid)))
    assert gates.main([str(root)]) == 0
    out = json.loads((root / "v7_pilot_gates.json").read_text())
    assert out["result"] == "evaluated" and out["completeness"]["status"] == "complete"
    assert out["all_pass"] and out["consumable"] is False and out["smoke"] is True


def test_cli_does_not_evaluate_an_incomplete_run(tmp_path):
    cfg = v7_run.V7Config("v7_dev", "base", 12)
    root = run_dir(tmp_path, cfg, lambda arm, qid, i, rot: default_choice(qid))
    shard = root / "records" / "attempt-001.jsonl"
    shard.write_text("".join(shard.read_text().splitlines(keepends=True)[:-5]))
    assert gates.main([str(root)]) == 0
    out = json.loads((root / "v7_pilot_gates.json").read_text())
    assert out["result"] == "incomplete" and out["consumable"] is False and "gates" not in out
