"""Offline tests for the protocol v2 post steps (strength gate, STATIC matching, signal gate, contrasts)."""

from __future__ import annotations

import json
import random

import pytest

from mb import chat, ledger, run, tasks


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer()


def _make_run(tmp_path, tok, arms, qids, boosts, params, n=12, name="r", seed=0):
    """boosts: arm name -> {qid: (meaning, logit added)}; baseline answers are correct."""
    cfg = run.StageConfig(stage="v2", tag="t", split=f"unit-{name}", n_episodes=n, arms=arms, qids=qids,
                          params=params)
    run_dir = tmp_path / name
    run_dir.mkdir()
    (run_dir / "identity.json").write_text(json.dumps(run.build_identity(cfg, None, "tmpl", {})))
    (run_dir / "manifest.json").write_text(json.dumps({"smoke": False}))
    arm_cfgs = {a.name: a for a in cfg.arm_configs()}
    arm_hash = {name_: f"h{i}" for i, name_ in enumerate(arm_cfgs)}
    (run_dir / "arm_hashes.json").write_text(json.dumps(arm_hash))
    _, used = run.stage_episodes(cfg, None)
    eps = {e.episode_id: e for e in used}
    rng = random.Random(seed)
    correct = {**run.G1_CORRECT, "ACC_RULE": "robin", "ACC_WORD": "robin", "U_CLOSED": "one"}
    w = ledger.ShardWriter(run_dir)
    for ep_id, arm, recipient, qid, rot in run.stage_expected(cfg, None):
        a = arm_cfgs[arm]
        q = tasks.make_question(tok, eps[ep_id], recipient, qid, rot)
        logits = [rng.gauss(0, 0.3) for _ in range(4)]
        if correct.get(qid) in q.label_meaning:
            logits[q.label_meaning.index(correct[qid])] += 10.0
        for (bq, meaning, amount) in boosts.get(arm, []):
            if bq == qid and meaning in q.label_meaning:
                logits[q.label_meaning.index(meaning)] += amount + rng.gauss(0, 0.3)
        w.write({"episode_id": ep_id, "arm": arm, "recipient": recipient, "qid": qid, "rotation_id": rot,
                 "options": list(q.options), "label_meaning": list(q.label_meaning), "label_logits": logits,
                 "label_mass": 0.99, "status": "ok", "config_hash": arm_hash[arm], "condition": a.condition,
                 "layer": a.layer, "gain": a.gain, "message_form": a.form, "readout_mode": a.readout_mode,
                 "interface": a.interface, "kv_scope": a.kv_scope})
    w.close()
    return run_dir


ACC_QIDS = ["ACC_RULE", "ACC_WORD", "CAP0", "CAP1"]
KV_ONE = {"condition": "ONE", "interface": "kv", "kv_scope": "ALL"}


def test_strength_gate_selects_strongest_eligible_point(tmp_path, tok):
    arms = [{"condition": "C0"}, {**KV_ONE, "gain": 0.1}, {**KV_ONE, "gain": 1.0}]
    boosts = {"ONE/KV-ALL/w0.1/FULL": [("ACC_RULE", "partner", 3.0)],
              "ONE/KV-ALL/w1/FULL": [("ACC_RULE", "partner", 12.0)]}
    out = run.post_select_strength(_make_run(tmp_path, tok, arms, ACC_QIDS, boosts, {"min_acc": 5.0}))
    assert out["strength_gate"] == "pass" and out["selection"]["arm"] == "ONE/KV-ALL/w1/FULL"
    assert out["selection"]["partner_rate"] > 0.9 and out["selection"]["acc_increment"] > 5


def test_strength_gate_not_met_when_too_weak(tmp_path, tok):
    arms = [{"condition": "C0"}, {**KV_ONE, "gain": 1.0}]
    boosts = {"ONE/KV-ALL/w1/FULL": [("ACC_RULE", "partner", 2.0)]}  # partner never becomes the argmax
    out = run.post_select_strength(_make_run(tmp_path, tok, arms, ACC_QIDS, boosts, {"min_acc": 5.0}))
    assert out["strength_gate"] == "not met" and out["selection"] is None
    assert out["groups"]["ONE|kv|ALL|18"]["arm"] == "ONE/KV-ALL/w1/FULL"  # still reported


def test_static_matching(tmp_path, tok):
    arms = [{"condition": "C0", "layer": 24}, {"condition": "ONE", "layer": 24, "gain": 0.2}]
    arms += [{"condition": "STATIC", "layer": 24, "gain": g} for g in (0.01, 0.02, 0.05)]
    boosts = {"ONE/L24/raw/g0.2/FULL": [("ACC_RULE", "partner", 1.0)],
              "STATIC/L24/raw/g0.01/FULL": [("ACC_RULE", "partner", 0.4)],
              "STATIC/L24/raw/g0.02/FULL": [("ACC_RULE", "partner", 1.05)],
              "STATIC/L24/raw/g0.05/FULL": [("ACC_RULE", "partner", 3.0)]}
    out = run.post_match_static(_make_run(tmp_path, tok, arms, ACC_QIDS, boosts,
                                          {"targets": ["ONE/L24/raw/g0.2/FULL"]}))
    m = out["matches"]["ONE/L24/raw/g0.2/FULL"]
    assert m["static_arm"] == "STATIC/L24/raw/g0.02/FULL" and m["matched"]


M_QIDS = ["START", "START_R", "NOW", "NOW_R", "ACC_RULE", "CAP0", "CAP1"]


@pytest.mark.parametrize("direction,go", [("+", True), ("-", False), ("0", True)])
def test_signal_gate(tmp_path, tok, direction, go):
    arms = [{"condition": "C0"}, {"condition": "LANG_UNTAG"}]
    boosts = {"LANG_UNTAG/FULL": [("NOW", "partner", 3.0)]}  # M_NOW up by about 3 nat
    params = {"studies": {"C": [["LANG_UNTAG/FULL", "C0/FULL", "M_NOW", direction]]}, "min_effect": 0.3}
    out = run.post_signal(_make_run(tmp_path, tok, arms, M_QIDS, boosts, params, n=16))
    study = out["studies"]["C"]
    assert study["go"] is go and 300 <= study["N"] <= 600
    assert study["comparisons"][0]["mean"] == pytest.approx(3.0, abs=0.5)


def test_signal_gate_rejects_small_effects(tmp_path, tok):
    arms = [{"condition": "C0"}, {"condition": "LANG_UNTAG"}]
    boosts = {"LANG_UNTAG/FULL": [("NOW", "partner", 0.1)]}
    params = {"studies": {"C": [["LANG_UNTAG/FULL", "C0/FULL", "M_NOW", "+"]]}}
    out = run.post_signal(_make_run(tmp_path, tok, arms, M_QIDS, boosts, params, n=16))
    assert out["studies"]["C"]["go"] is False


def test_contrast_families_are_holm_adjusted_within_study(tmp_path, tok):
    arms = [{"condition": "C0"}, {"condition": "LANG_UNTAG"}, {"condition": "LANG_TAG"}]
    boosts = {"LANG_UNTAG/FULL": [("NOW", "partner", 3.0)]}
    params = {"families": {"C": [["LANG_UNTAG/FULL", "LANG_TAG/FULL", "M_NOW"], ["LANG_TAG/FULL", "C0/FULL", "M_NOW"]],
                           "X": [["LANG_TAG/FULL", "C0/FULL", "M"]]}}
    out = run.post_contrasts(_make_run(tmp_path, tok, arms, M_QIDS, boosts, params, n=16))
    fam = out["families"]["C"]
    assert fam[0]["mean"] == pytest.approx(3.0, abs=0.5) and fam[0]["p_holm"] < 0.01
    assert all(r["p_holm"] >= r["p_two_sided"] for r in fam) and len(out["families"]["X"]) == 1
    assert {d["arm"] for d in out["descriptive"]} == {"LANG_UNTAG/FULL", "LANG_TAG/FULL"}


def test_strength_selection_follows_group_order(tmp_path, tok):
    """PROTOCOL_V2 §1: groups in pre-set order; the top-ACC eligible point per group is tested."""
    arms = [{"condition": "C0"}, {"condition": "ONE", "interface": "kv", "kv_scope": "C", "gain": 1.0},
            {**KV_ONE, "gain": 0.5}, {**KV_ONE, "gain": 1.0}]
    boosts = {"ONE/KV-C/w1/FULL": [("ACC_RULE", "partner", 11.0)],
              # ALL: the stronger point misses the partner-hit rate is impossible to fake here, so make the
              # top-ACC ALL point strong as well; order decides between C and ALL.
              "ONE/KV-ALL/w0.5/FULL": [("ACC_RULE", "partner", 6.0)],
              "ONE/KV-ALL/w1/FULL": [("ACC_RULE", "partner", 14.0)]}
    params = {"min_acc": 5.0, "group_order": ["ONE|kv|C|18", "ONE|kv|ALL|18"]}
    out = run.post_select_strength(_make_run(tmp_path, tok, arms, ACC_QIDS, boosts, params))
    assert out["selection"]["arm"] == "ONE/KV-C/w1/FULL"  # C comes first even though ALL is stronger
    params["group_order"] = ["ONE|kv|ALL|18", "ONE|kv|C|18"]
    out = run.post_select_strength(_make_run(tmp_path, tok, arms, ACC_QIDS, boosts, params, name="r2"))
    assert out["selection"]["arm"] == "ONE/KV-ALL/w1/FULL"


def test_strength_top_point_must_itself_pass(tmp_path, tok):
    """A weaker point that passes does not rescue a group whose top-ACC point fails the hit rate."""
    arms = [{"condition": "C0"}, {**KV_ONE, "gain": 0.5}, {**KV_ONE, "gain": 1.0}]
    boosts = {"ONE/KV-ALL/w0.5/FULL": [("ACC_RULE", "partner", 11.0)],
              "ONE/KV-ALL/w1/FULL": [("ACC_RULE", "partner", 9.0), ("ACC_RULE", "unused", 12.0)]}
    out = run.post_select_strength(_make_run(tmp_path, tok, arms, ACC_QIDS, boosts, {"min_acc": 5.0}))
    table = {r["arm"]: r for r in out["groups"].values() if r}
    top = out["groups"]["ONE|kv|ALL|18"]
    assert top["arm"] in ("ONE/KV-ALL/w0.5/FULL", "ONE/KV-ALL/w1/FULL")
    assert (out["strength_gate"] == "pass") == bool(top["strong"])


def _script(name):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, run.REPO_ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("name", ["C0/FULL", "ONE/L24/raw/g0.2/FULL", "TWO/KV-ALL/w0.7/FULL", "STATIC/L24/raw/g0.03/FULL",
                                  "LANG_SELF/FULL", "ONE/KV-P/w2/RO", "CF/KV-P/w2/FULL"])
def test_v2_arm_names_round_trip(name):
    from mb.conditions import ArmConfig

    assert ArmConfig(**_script("make_v2_main")._arm_spec(name)).name == name


def test_make_v2_main_includes_only_go_studies(tmp_path):
    from types import SimpleNamespace

    mod = _script("make_v2_main")

    def sig(d, studies):
        d.mkdir()
        (d / "signal.json").write_text(json.dumps({"consumable": True, "studies": studies}))
        return d

    comp = lambda a1, a2, m: {"arm1": a1, "arm2": a2, "metric": m}  # noqa: E731
    s1 = sig(tmp_path / "s1", {
        "B_R": {"go": False, "N": 400, "comparisons": [comp("TWO/L24/raw/g0.3/FULL", "ONE/L24/raw/g0.3/FULL", "M_NOW")]},
        "C": {"go": True, "N": 300, "comparisons": [comp("LANG_UNTAG/FULL", "LANG_TAG/FULL", "M_NOW"),
                                                    comp("LANG_SELF/FULL", "LANG_UNTAG/FULL", "M_NOW")]}})
    s2 = sig(tmp_path / "s2", {
        "D": {"go": True, "N": 452, "comparisons": [comp("ONE/KV-P/w2/FULL", "C0/FULL", "M"),
                                                    comp("ONE/KV-P/w2/FULL", "C0/FULL", "M_NOW")]}})
    cfgs = mod.build(SimpleNamespace(sig1=s1, sig2=s2, sigE=None, cal="/x/cal.pt", cal_bal=None, only=None,
                                     materials="balanced2"))
    main = run.StageConfig(**cfgs["v2_main"])
    names = {a.name for a in main.arm_configs()}
    assert main.n_episodes == 452 and set(main.params["families"]) == {"C", "D"}
    assert "TWO/L24/raw/g0.3/FULL" not in names and {"LANG_SELF/FULL", "ONE/KV-P/w2/FULL", "C0/FULL"} <= names
    diag = run.StageConfig(**cfgs["v2_main_diag"])
    assert {a.name for a in diag.arm_configs()} == {"C0/FULL", "ONE/KV-P/w2/FULL", "CF/KV-P/w2/FULL"}
    only = mod.build(SimpleNamespace(sig1=s1, sig2=s2, sigE=None, cal="/x/cal.pt", cal_bal=None, only="C",
                                     materials="balanced2"))
    assert set(only) == {"v2_main"} and set(only["v2_main"]["params"]["families"]) == {"C"}
