"""Offline tests for pure scoring (protocol v0.5 §8)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from mb import chat, readouts, tasks

BASE = {"own": 5.0, "partner": 1.0, "robin": 0.0, "unused": 0.0, "distractor": 0.0,
        "correct": 4.0, "wrong": 0.0, "one": 3.0, "two": 0.0, "partly_shared": 0.0, "hard_to_say": 0.0}


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer()


@pytest.fixture(scope="module")
def ep():
    return tasks.make_episodes(4, "dev", seed=7)[0]


def make_records(tok, ep, arm="C0", recipient="A", rotations=(0, 2), logit_fn=None):
    """Synthetic runtime records whose logits depend on label meaning (and optionally qid/rotation)."""
    logit_fn = logit_fn or (lambda qid, rot, meaning: BASE[meaning])
    recs = []
    for q in tasks.readout_questions(tok, ep, recipient, rotations=rotations):
        if q.generative:
            continue
        logits = [logit_fn(q.qid, q.rotation_id, m) for m in q.label_meaning]
        recs.append({
            "episode_id": ep.episode_id, "recipient": recipient, "arm": arm, "qid": q.qid,
            "rotation_id": q.rotation_id, "label_logits": logits, "label_meaning": list(q.label_meaning),
            "options": list(q.options), "label_mass": 0.97, "status": "ok", "text_hash": q.text_hash,
        })
    return recs


def test_M_sign_and_common_partner_bias_cancels(tok, ep):
    def fn(qid, rot, meaning):
        if qid == "START_R":
            return {"robin": 5.0, "partner": 0.0}.get(meaning, 0.0)
        return BASE[meaning]

    row = readouts.score_records(make_records(tok, ep, logit_fn=fn)).iloc[0]
    assert row["L_START"] == pytest.approx(1.0 - 5.0)
    assert row["L_START_R"] == pytest.approx(0.0 - 5.0)
    assert row["M"] == pytest.approx(1.0)

    def biased(qid, rot, meaning):
        return fn(qid, rot, meaning) + (2.5 if meaning == "partner" else 0.0)

    row_b = readouts.score_records(make_records(tok, ep, logit_fn=biased)).iloc[0]
    assert row_b["M"] == pytest.approx(row["M"])
    assert row_b["L_START"] == pytest.approx(row["L_START"] + 2.5)


def test_metrics_computed_per_rotation_then_averaged(tok, ep):
    def fn(qid, rot, meaning):
        bump = 1.0 if (qid == "START" and meaning == "partner" and rot == 2) else 0.0
        return BASE[meaning] + bump

    row = readouts.score_records(make_records(tok, ep, logit_fn=fn)).iloc[0]
    base = readouts.score_records(make_records(tok, ep)).iloc[0]
    assert row["M"] == pytest.approx(base["M"] + 0.5)
    assert row["n_rotations"] == 2


def test_missing_rotation_and_nonfinite_become_nan(tok, ep):
    recs = [r for r in make_records(tok, ep) if not (r["qid"] == "START" and r["rotation_id"] == 2)]
    row = readouts.score_records(recs).iloc[0]
    assert math.isnan(row["M"])
    assert math.isnan(row["L_START"])
    assert not math.isnan(row["M_NOW"])  # unaffected metrics still computed

    lenient = readouts.score_records(recs, readouts.ScoreOptions(require_all_rotations=False)).iloc[0]
    assert math.isnan(lenient["M"])  # rotation 2 incomplete for START -> that rotation is NaN

    bad = make_records(tok, ep)
    for r in bad:
        if r["qid"] == "START_R" and r["rotation_id"] == 0:
            r["label_logits"] = [0.0, float("nan"), 1.0, 2.0]
    assert math.isnan(readouts.score_records(bad).iloc[0]["M"])

    failed = make_records(tok, ep)
    failed[0]["status"] = "failed"
    row_f = readouts.score_records(failed).iloc[0]
    assert math.isnan(row_f[{"BEH": "M_BEH"}.get(failed[0]["qid"], "M_BEH")])


def test_capability_argmax_and_profile(tok, ep):
    row = readouts.score_records(make_records(tok, ep)).iloc[0]
    assert row["CAP_ACC"] == 1.0
    assert row["LABEL_MASS"] == pytest.approx(0.97)
    assert row["argmax_START"] == "own" and row["argmax_U_CLOSED"] == "one"


def test_duplicate_records_rejected(tok, ep):
    recs = make_records(tok, ep)
    with pytest.raises(ValueError):
        readouts.score_records(recs + recs[:1])


def test_content_cf_uses_fixed_physical_candidates(tok, ep):
    v = tasks.make_donor_variant(ep, "CF")
    r0, r1 = v.r0_rule, v.r1_rule

    def orig_fn(qid, rot, meaning):
        return {"partner": 1.0}.get(meaning, 0.0)

    orig = make_records(tok, ep, arm="ONE", logit_fn=orig_fn)
    cf_ep = v.donor_episode
    cf = make_records(tok, cf_ep, arm="ONE_CF", logit_fn=orig_fn)  # partner is now r1
    out = readouts.content_cf_score(orig, cf, "ACC_RULE", r0, r1).iloc[0]
    # orig: z(r1)=0 (unused), z(r0)=1 (partner) -> Q=-1; cf: z(r1)=1, z(r0)=0 -> Q=+1
    assert out["C_content"] == pytest.approx(2.0)

    tampered = [dict(r, text_hash="x") if r["qid"] == "ACC_RULE" else r for r in cf]
    with pytest.raises(ValueError):
        readouts.content_cf_score(orig, tampered, "ACC_RULE", r0, r1)


def test_content_cf_reads_per_episode_candidates(tok):
    """G2 wiring: each episode has its own (B rule, spare rule); read them from the CF records."""
    eps = tasks.make_episodes(2, "dev", seed=5)

    def fn(qid, rot, meaning):
        return {"partner": 1.0}.get(meaning, 0.0)

    orig, cf = [], []
    for ep in eps:
        v = tasks.make_donor_variant(ep, "CF")
        orig += make_records(tok, ep, arm="ONE", logit_fn=fn)
        cf += [dict(r, cf_r0_rule=v.r0_rule, cf_r1_rule=v.r1_rule)
               for r in make_records(tok, v.donor_episode, arm="ONE_CF", logit_fn=fn)]
    assert eps[0].rule.B != eps[1].rule.B or eps[0].rule.spare != eps[1].rule.spare
    out = readouts.content_cf_score(orig, cf, "ACC_RULE")
    assert list(out["C_content"]) == pytest.approx([2.0, 2.0])
    # Missing CF data for an episode is reported as missing, never as zero.
    part = readouts.content_cf_score(orig, [r for r in cf if r["episode_id"] == eps[0].episode_id], "ACC_RULE")
    assert math.isnan(part.set_index("episode_id").loc[eps[1].episode_id, "C_content"])
    with pytest.raises(ValueError, match="lacks"):
        readouts.content_cf_score(orig, [{k: v for k, v in r.items() if not k.startswith("cf_")} for r in cf],
                                  "ACC_RULE")


def test_label_probs_are_descriptive_softmax(tok, ep):
    rec = make_records(tok, ep)[0]
    p = readouts.label_probs(rec)
    assert p.sum() == pytest.approx(1.0) and np.all(p >= 0)
