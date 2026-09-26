"""Offline tests for run bookkeeping (review M2 B1/B2/I3/I7/I8); no torch needed."""

from __future__ import annotations

import json

import pytest

from mb import ledger


def _rec(ep="e0", arm="C0/FULL", recipient="A", qid="START", rot=0, status="ok", h="h1"):
    return {"episode_id": ep, "arm": arm, "recipient": recipient, "qid": qid, "rotation_id": rot,
            "status": status, "config_hash": h}


def test_shards_are_new_files_and_never_reopened(tmp_path):
    w1 = ledger.ShardWriter(tmp_path)
    w1.write(_rec())
    w1.close()
    w2 = ledger.ShardWriter(tmp_path)
    w2.write(_rec(ep="e1"))
    w2.close()
    names = [p.name for p in ledger.shard_paths(tmp_path)]
    assert names == ["attempt-000.jsonl", "attempt-001.jsonl"]
    assert [r["episode_id"] for r in ledger.load_records(tmp_path).records] == ["e0", "e1"]


def test_truncated_tail_is_tolerated_and_reported(tmp_path):
    w = ledger.ShardWriter(tmp_path)
    w.write(_rec())
    w.close()
    with w.path.open("a") as fh:
        fh.write('{"episode_id":')  # crash mid-write
    before = w.path.read_bytes()
    rep = ledger.load_records(tmp_path)
    assert len(rep.records) == 1 and rep.truncated_tails == ["attempt-000.jsonl"]
    assert w.path.read_bytes() == before  # evidence left untouched
    # A complete final line without newline still counts.
    w2 = ledger.ShardWriter(tmp_path)
    w2.close()
    w2.path.write_text(json.dumps(_rec(ep="e9")))
    assert "e9" in [r["episode_id"] for r in ledger.load_records(tmp_path).records]


def test_corrupt_middle_line_stops_the_load(tmp_path):
    (tmp_path / "records").mkdir()
    (tmp_path / "records" / "attempt-000.jsonl").write_text(
        json.dumps(_rec()) + "\n" + "{broken\n" + json.dumps(_rec(ep="e1")) + "\n")
    with pytest.raises(ValueError, match="corrupt line 2"):
        ledger.load_records(tmp_path)


def test_nonfinite_values_become_null(tmp_path):
    w = ledger.ShardWriter(tmp_path)
    w.write({**_rec(), "label_logits": [float("nan"), 1.0, float("inf"), 0.0]})
    w.close()
    rec = ledger.load_records(tmp_path).records[0]
    assert rec["label_logits"] == [None, 1.0, None, 0.0]


def test_done_keys_need_ok_status_and_matching_hash():
    recs = [_rec(status="failed"), _rec(qid="NOW"), _rec(qid="WORD", h="old")]
    done = ledger.done_keys(recs, {"C0/FULL": "h1"})
    assert done == {("e0", "C0/FULL", "A", "NOW", 0)}
    assert ledger.conflicting_hashes(recs, {"C0/FULL": "h1"}) == {"C0/FULL": {"old"}}


def test_expected_trials_and_completeness():
    arms = [ledger.ArmSpec("C0/FULL", ("A", "B"))]
    eps = [("e0", (0, 2)), ("e1", (1, 3))]
    exp = ledger.expected_trials(arms, eps, ["START", "U_OPEN"], all_rotation_ids={"e1"})
    # e0: 2 rotations, e1: all 4; U_OPEN once; x2 recipients
    assert len(exp) == 2 * (2 + 1) + 2 * (4 + 1)
    recs = [_rec(ep=e, recipient=r, qid=q, rot=rot) for (e, _, r, q, rot) in exp]
    assert ledger.completeness(recs, exp, {"C0/FULL": "h1"})["status"] == "complete"
    # Missing one rotation, one recipient's U_OPEN, and a whole episode are all caught.
    for drop in (lambda k: k[0] == "e1" and k[4] == 3,
                 lambda k: k[2] == "B" and k[3] == "U_OPEN",
                 lambda k: k[0] == "e0"):
        part = [r for r, k in zip(recs, exp) if not drop(k)]
        comp = ledger.completeness(part, exp, {"C0/FULL": "h1"})
        assert comp["status"] == "incomplete" and comp["n_missing"] > 0
    # A failed record never counts, a later ok retry does.
    failed = [dict(r, status="failed") if i == 0 else r for i, r in enumerate(recs)]
    assert ledger.completeness(failed, exp, {"C0/FULL": "h1"})["status"] == "incomplete"
    assert ledger.completeness(failed + [recs[0]], exp, {"C0/FULL": "h1"})["status"] == "complete"


def test_mismatch_donor_map_is_fixed_on_the_full_list():
    ids = [f"e{i}" for i in range(4)]
    full = ledger.mismatch_donor_map(ids)
    assert full["e1"] == "e2" and full["e3"] == "e0"
    assert all(k != v for k, v in full.items())
    with pytest.raises(ValueError):
        ledger.mismatch_donor_map(["e0"])


def test_compare_identity():
    assert ledger.compare_identity({"a": 1, "b": [1, 2]}, {"a": 1, "b": [1, 2]}) == []
    assert ledger.compare_identity({"a": 1}, {"a": 2, "c": 0}) == ["a", "c"]
