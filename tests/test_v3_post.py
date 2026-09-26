"""Offline tests for protocol-v3 pair-level outcomes, live-loop selection and the pair signal gate."""

from __future__ import annotations

import json
import random

import numpy as np
import pandas as pd
import pytest

from mb import chat, ledger, run, tasks


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer()


def _make_run(tmp_path, tok, arms, qids, picks, params, n=16, name="r", cap_fail=None):
    """picks: (arm, recipient, qid) -> function(episode_index) -> meaning to make the argmax."""
    cfg = run.StageConfig(stage="v3", tag="t", split=f"unit3-{name}", n_episodes=n, arms=arms, qids=qids, params=params)
    run_dir = tmp_path / name
    run_dir.mkdir()
    (run_dir / "identity.json").write_text(json.dumps(run.build_identity(cfg, None, "tmpl", {})))
    (run_dir / "manifest.json").write_text(json.dumps({"smoke": False}))
    arm_cfgs = {a.name: a for a in cfg.arm_configs()}
    arm_hash = {k: f"h{i}" for i, k in enumerate(arm_cfgs)}
    (run_dir / "arm_hashes.json").write_text(json.dumps(arm_hash))
    _, used = run.stage_episodes(cfg, None)
    eps = {e.episode_id: e for e in used}
    rng = random.Random(0)
    default = {"START": "own", "NOW": "own", "START_R": "robin", "NOW_R": "robin", "ACC_RULE": "robin",
               "ACC_WORD": "robin", "CAP0": "correct", "CAP1": "correct"}
    w = ledger.ShardWriter(run_dir)
    for ep_id, arm, recipient, qid, rot in run.stage_expected(cfg, None):
        a = arm_cfgs[arm]
        q = tasks.make_question(tok, eps[ep_id], recipient, qid, rot)
        idx = eps[ep_id].index
        want = picks.get((arm, recipient, qid), lambda i: default[qid])(idx)
        if cap_fail and (arm, recipient) in cap_fail and qid.startswith("CAP") and idx % 2 == 0:
            want = "wrong"
        logits = [rng.gauss(0, 0.2) for _ in range(4)]
        logits[q.label_meaning.index(want)] += 8.0
        w.write({"episode_id": ep_id, "arm": arm, "recipient": recipient, "qid": qid, "rotation_id": rot,
                 "options": list(q.options), "label_meaning": list(q.label_meaning), "label_logits": logits,
                 "label_mass": 0.99, "status": "ok", "config_hash": arm_hash[arm], "condition": a.condition,
                 "layer": a.layer, "gain": a.gain, "message_form": a.form, "readout_mode": a.readout_mode,
                 "interface": a.interface, "kv_scope": a.kv_scope, "kv_w_live": a.kv_w_live})
    w.close()
    return run_dir


KV = {"interface": "kv", "kv_scope": "ALL", "gain": 0.6, "recipients": ["A", "B"]}
QIDS = ["START", "NOW", "ACC_RULE", "CAP0", "CAP1"]


def test_pair_outcomes_classify_merge_and_swap(tmp_path, tok):
    arms = [{"condition": "C0", "recipients": ["A", "B"]}, {"condition": "ONE", **KV}, {"condition": "TWO", **KV}]
    picks = {("ONE/KV-ALL/w0.6/FULL", "A", "START"): lambda i: "partner" if i % 4 == 0 else "own",
             ("TWO/KV-ALL/w0.6/FULL", "A", "START"): lambda i: "partner" if i % 2 == 0 else "own",
             ("TWO/KV-ALL/w0.6/FULL", "B", "START"): lambda i: "partner" if i % 4 in (0, 1) else "own"}
    d = _make_run(tmp_path, tok, arms, QIDS, picks, {})
    pairs = run.pair_outcomes(d)
    g = pairs[pairs["qid"] == "START"].groupby("arm")[list(run.PAIR_OUTCOMES)].mean()
    assert g.loc["C0/FULL", "intact"] == 1.0 and g.loc["C0/FULL", "one_wins"] == 0.0
    assert g.loc["ONE/KV-ALL/w0.6/FULL", "a_adopts"] == pytest.approx(0.25)
    two = g.loc["TWO/KV-ALL/w0.6/FULL"]
    # i%4: 0 -> swap, 1 -> B adopts A, 2 -> A adopts B, 3 -> intact
    assert (two["swap"], two["b_adopts"], two["a_adopts"], two["intact"]) == pytest.approx((0.25, 0.25, 0.25, 0.25))
    assert two["one_wins"] == pytest.approx(0.5) and two["same_rule"] == pytest.approx(0.5)
    assert two["both_third"] == 0.0


def test_pair_signal_gate(tmp_path, tok):
    arms = [{"condition": "C0", "recipients": ["A", "B"]}, {"condition": "ONE", **KV}, {"condition": "TWO", **KV}]
    picks = {("ONE/KV-ALL/w0.6/FULL", "A", "START"): lambda i: "partner" if i % 4 == 0 else "own",
             ("TWO/KV-ALL/w0.6/FULL", "A", "START"): lambda i: "partner" if i % 4 in (0, 1) else "own",
             ("TWO/KV-ALL/w0.6/FULL", "B", "START"): lambda i: "partner" if i % 4 == 2 else "own"}
    params = {"studies": {"B'": [["TWO/KV-ALL/w0.6/FULL", "ONE/KV-ALL/w0.6/FULL", "START", "one_wins", "+"]]},
              "min_effect": 0.10}
    out = run.post_pair_signal(_make_run(tmp_path, tok, arms, QIDS, picks, params))
    st = out["studies"]["B'"]
    assert st["comparisons"][0]["mean"] == pytest.approx(0.5) and st["go"] and 300 <= st["N"] <= 600


def test_select_live_requires_both_sides_eligible(tmp_path, tok):
    arms = [{"condition": "C0", "recipients": ["A", "B"]}]
    for w in (0.5, 0.6):
        arms += [{"condition": c, **{**KV, "gain": w}} for c in ("ONE", "TWO")]
    cap_fail = {("TWO/KV-ALL/w0.6/FULL", "B")}  # B side breaks at w = 0.6
    d = _make_run(tmp_path, tok, arms, QIDS, {}, {"family_order": ["ALL"]}, cap_fail=cap_fail)
    sel = run.post_select_live(d)["selection"]["ALL"]
    assert sel["arm"] == "TWO/KV-ALL/w0.5/FULL" and sel["one_arm"] == "ONE/KV-ALL/w0.5/FULL"


KVP = {**KV, "kv_scope": "P"}
COUPLED = {("TWO/KV-ALL/w0.6/FULL", "A", "START"): lambda i: "partner" if i % 2 == 0 else "own",
           ("TWO/KV-ALL/w0.6/FULL", "B", "START"): lambda i: "partner" if i % 2 == 1 else "own"}
INDEPENDENT = {("TWO/KV-P/w0.6/FULL", "A", "START"): lambda i: "partner" if i % 4 in (0, 1) else "own",
               ("TWO/KV-P/w0.6/FULL", "B", "START"): lambda i: "partner" if i % 4 in (0, 2) else "own"}


def test_shared_third_rule_is_not_a_merge(tmp_path, tok):
    arms = [{"condition": "C0", "recipients": ["A", "B"]}, {"condition": "TWO", **KV}]
    both_robin = lambda i: "robin" if i % 2 == 0 else "own"
    picks = {("TWO/KV-ALL/w0.6/FULL", "A", "START"): both_robin, ("TWO/KV-ALL/w0.6/FULL", "B", "START"): both_robin}
    pairs = run.pair_outcomes(_make_run(tmp_path, tok, arms, QIDS, picks, {}))
    two = pairs[(pairs["qid"] == "START") & (pairs["arm"] == "TWO/KV-ALL/w0.6/FULL")][list(run.PAIR_OUTCOMES)].mean()
    assert (two["both_third"], two["same_rule"], two["one_wins"], two["intact"]) == pytest.approx((0.5, 0.5, 0.0, 0.5))


def test_one_wins_excess_is_zero_under_independence():
    # rows: one_wins, a_partner, a_own, b_partner, b_own
    coupled = np.array([[1, 1, 0, 0, 1], [1, 0, 1, 1, 0]], dtype=float)  # one side wins, never both move
    independent = np.array([[0, 1, 0, 1, 0], [1, 1, 0, 0, 1], [1, 0, 1, 1, 0], [0, 0, 1, 0, 1]], dtype=float)
    assert run.one_wins_excess(coupled) == pytest.approx(0.5)
    assert run.one_wins_excess(independent) == pytest.approx(0.0)


def test_pair_signal_on_excess_against_the_no_loop_arm(tmp_path, tok):
    arms = [{"condition": "C0", "recipients": ["A", "B"]}, {"condition": "TWO", **KV}, {"condition": "TWO", **KVP}]
    loop, no_loop = "TWO/KV-ALL/w0.6/FULL", "TWO/KV-P/w0.6/FULL"
    params = {"studies": {"B'": [[loop, no_loop, "START", "one_wins_excess", "+"],
                                 [loop, None, "START", "one_wins_excess", "+"]]},
              "descriptive": {"rates": [[loop, no_loop, "START", "one_wins", "+"]]}, "min_effect": 0.10}
    out = run.post_pair_signal(_make_run(tmp_path, tok, arms, QIDS, {**COUPLED, **INDEPENDENT}, params))
    st = out["studies"]["B'"]
    first = st["comparisons"][0]
    assert first["arm1_excess"] == pytest.approx(0.5) and first["arm2_excess"] == pytest.approx(0.0)
    assert first["mean"] == pytest.approx(0.5) and first["ci90_lo"] > 0 and st["go"]
    assert 300 <= st["N"] <= 600
    assert st["comparisons"][1]["mean"] == pytest.approx(0.5)
    assert out["descriptive"]["rates"][0]["mean"] == pytest.approx(0.5)


def test_pair_signal_keeps_zero_sd(tmp_path, tok):
    # Every episode merges under TWO and none under ONE: the paired SD is 0, which must still give N.
    arms = [{"condition": "C0", "recipients": ["A", "B"]}, {"condition": "ONE", **KV}, {"condition": "TWO", **KV}]
    params = {"studies": {"B'": [["TWO/KV-ALL/w0.6/FULL", "ONE/KV-ALL/w0.6/FULL", "START", "one_wins", "+"]]},
              "min_effect": 0.10}
    st = run.post_pair_signal(_make_run(tmp_path, tok, arms, QIDS, COUPLED, params))["studies"]["B'"]
    assert st["comparisons"][0]["sd"] == 0.0 and st["go"] and st["N"] == 300


def test_pair_signal_without_pairs_is_no_go(tmp_path, tok):
    arms = [{"condition": "C0", "recipients": ["A", "B"]}, {"condition": "TWO", **KV}]
    params = {"studies": {"B'": [["TWO/KV-ALL/w0.6/FULL", "TWO/KV-P/w0.6/FULL", "START", "one_wins_excess", "+"]]}}
    st = run.post_pair_signal(_make_run(tmp_path, tok, arms, QIDS, COUPLED, params))["studies"]["B'"]
    assert not st["go"] and st["reason"] == "no paired episodes"


def test_exit_code_flags_incomplete_stages():
    assert run.exit_code({"status": "complete"}) == 0
    assert run.exit_code({"status": "incomplete"}) != 0


def _script(name):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, run.REPO_ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_bprime_signal_config_pairs_each_loop_arm_with_its_no_loop_control(tmp_path):
    gen = _script("make_v3_bprime_signal")
    d = tmp_path / "s_live"
    d.mkdir()
    sel = {"PC": {"arm": "TWO/KV-PC/w2+0.3/FULL", "condition": "TWO", "kv_scope": "PC", "gain": 2.0, "kv_w_live": 0.3},
           "ALL": {"arm": "TWO/KV-ALL/w0.55/FULL", "condition": "TWO", "kv_scope": "ALL", "gain": 0.55,
                   "kv_w_live": None}}
    (d / "live_selection.json").write_text(json.dumps({"consumable": True, "selection": sel}))
    cfg, _ = gen.build(gen.selection(d))
    out = tmp_path / "sig.yaml"
    out.write_text(__import__("yaml").safe_dump(cfg))
    names = {a.name for a in run.StageConfig.load(out).arm_configs()}
    assert names == {"C0/FULL", "ONE/KV-PC/w2+0.3/FULL", "TWO/KV-PC/w2+0.3/FULL", "TWO/KV-PC/w2+0.3/RF",
                     "TWO/KV-P/w2/FULL", "TWO/KV-P/w2/RF", "ONE/KV-ALL/w0.55/FULL", "TWO/KV-ALL/w0.55/FULL",
                     "TWO/KV-ALL/w0.55/RF", "TWO/KV-P/w0.55/FULL", "TWO/KV-P/w0.55/RF"}
    studies = cfg["params"]["studies"]
    assert studies["B'-PC"][0] == ["TWO/KV-PC/w2+0.3/FULL", "TWO/KV-P/w2/FULL", "START", "one_wins_excess", "+"]
    assert studies["B'-ALL"][1] == ["TWO/KV-ALL/w0.55/RF", "TWO/KV-P/w0.55/RF", "START", "one_wins_excess", "+"]
    used = {x for spec in [*studies.values(), *cfg["params"]["descriptive"].values()] for c in spec for x in c[:2]}
    assert used - {None} <= names


def test_bprime_signal_config_needs_a_selection(tmp_path):
    gen = _script("make_v3_bprime_signal")
    (tmp_path / "live_selection.json").write_text(json.dumps({"consumable": True, "selection": {"PC": None}}))
    with pytest.raises(SystemExit):
        gen.selection(tmp_path)


def test_t3_person_words():
    t3 = _script("report_t3_checks")
    assert t3.person_words("I choose Plan Pine because it fits my priority.")["first"]
    assert t3.person_words("You should pick Plan Oak.") == {"first": False, "second": True, "any": True}
    assert not t3.person_words("Participant Nova chooses Plan Pine, in line with Nova's priority.")["any"]


def test_t3_verdict_follows_the_preregistered_order():
    t3 = _script("report_t3_checks")
    go = {"go": True, "mean": 20.0}
    lost = {"ci90_lo": -30.0, "ci90_hi": -10.0}
    assert t3.verdict(0.25, 1.0, 1.0, go, lost)[0] == "leaky"  # leaks decide first, whatever M does
    assert t3.verdict(0.05, 0.6, 1.0, go, lost)[0] == "unmatched"
    code, text = t3.verdict(0.05, 0.9, 1.1, go, lost)
    assert code == "persists" and "excludes 0" in text
    assert t3.verdict(0.05, 0.9, None, {"go": False, "mean": 0.1}, lost)[0] == "gone"


def test_t3_notes_are_found_by_frame(tmp_path, tok):
    t3 = _script("report_t3_checks")
    cfg = run.StageConfig(stage="v3", tag="t", split="unit3-t3", n_episodes=4,
                          arms=[{"condition": "C0"}], qids=["START"], params={})
    _, eps = run.stage_episodes(cfg, None)
    lines = []
    for ep in eps:
        for frame, text in (("second", "I choose Plan X for my priority."), ("third", "Plan X suits the priority.")):
            key = tasks.note_key(ep, "B", "v1", frame)
            ids = tok.encode(text, add_special_tokens=False)
            lines.append(json.dumps({"key": key, "episode_id": ep.episode_id, "role": "B", "ids": ids, "note": text,
                                     "n_tokens": len(ids)}))
    (tmp_path / "notes.jsonl").write_text("\n".join(lines) + "\n")
    df = t3.notes_by_frame(tmp_path, cfg).groupby("frame").mean(numeric_only=True)
    assert df.loc["second", "any"] == 1.0 and df.loc["third", "any"] == 0.0
    assert df.loc["third", "name_mentions"] > df.loc["second", "name_mentions"]


def test_aprime_signal_config_uses_the_matched_static_and_its_calibration(tmp_path):
    gen = _script("make_v3_aprime_signal")
    d = tmp_path / "s_static_a"
    d.mkdir()
    m = {"static_arm": "STATIC/L24/raw/g0.1/FULL", "gain": 0.1, "target_acc": 4.2, "static_acc": 3.6, "matched": True}
    (d / "static_match.json").write_text(json.dumps({"consumable": True, "matches": {"ONE/KV-P/w1/FULL": m}}))
    (d / "config.yaml").write_text("calibration: {24: /gpu/cal/calibration_L24.pt}\n")
    cfg = gen.build(*gen.match(d))
    out = tmp_path / "sig.yaml"
    out.write_text(__import__("yaml").safe_dump(cfg))
    loaded = run.StageConfig.load(out)
    assert {a.name for a in loaded.arm_configs()} == {"C0/FULL", "ONE/KV-P/w1/FULL", "STATIC/L24/raw/g0.1/FULL"}
    assert cfg["calibration"] == {24: "/gpu/cal/calibration_L24.pt"}
    assert cfg["params"]["studies"]["A'"] == [["ONE/KV-P/w1/FULL", "STATIC/L24/raw/g0.1/FULL", "M", "0"]]


def test_pair_signal_report_renders(tmp_path, tok):
    rep = _script("report_v3_pair_signal")
    arms = [{"condition": "C0", "recipients": ["A", "B"]}, {"condition": "TWO", **KV}, {"condition": "TWO", **KVP},
            {"condition": "TWO", **KV, "readout_mode": "RF"}]
    loop, no_loop = "TWO/KV-ALL/w0.6/FULL", "TWO/KV-P/w0.6/FULL"
    params = {"studies": {"B'": [[loop, no_loop, "START", "one_wins_excess", "+"]]},
              "descriptive": {"B'": [[loop, None, "START", "one_wins_excess", "0"]]}, "min_effect": 0.10}
    d = _make_run(tmp_path, tok, arms, QIDS, {**COUPLED, **INDEPENDENT}, params)
    run.post_pair_signal(d)
    out = tmp_path / "report.md"
    import sys
    argv, sys.argv = sys.argv, ["report", str(d), "--out", str(out)]
    try:
        assert rep.main() == 0
    finally:
        sys.argv = argv
    text = out.read_text()
    assert "Go / no-go" in text and "TWO/KV-ALL/w0.6/RF" in text and "Member B" in text
    table = rep.outcome_table(pd.read_csv(d / "pair_outcomes.csv"), "START").set_index("arm")
    assert table.loc[loop, "excess"] == pytest.approx(0.5) and table.loc[no_loop, "excess"] == pytest.approx(0.0)


def test_match_arms_picks_the_strict_frame_weight_with_the_target_acc(tmp_path, tok):
    kvp = {"interface": "kv", "kv_scope": "P"}
    arms = [{"condition": "C0"}, {"condition": "ONE", **kvp, "gain": 1.0}]
    arms += [{"condition": "ONE", **kvp, "gain": w, "partner_frame": "third_strict"} for w in (0.6, 0.8, 1.0)]
    # ACC_RULE picks: the target and w0.8 name the partner's rule on every episode, w1 on half, w0.6 never
    picks = {(a, "A", "ACC_RULE"): (lambda i: "partner") for a in ("ONE/KV-P/w1/FULL", "ONE/KV-P/w0.8/3ps/FULL")}
    picks[("ONE/KV-P/w1/3ps/FULL", "A", "ACC_RULE")] = lambda i: "partner" if i % 2 == 0 else "robin"
    cands = ["ONE/KV-P/w0.6/3ps/FULL", "ONE/KV-P/w0.8/3ps/FULL", "ONE/KV-P/w1/3ps/FULL"]
    d = _make_run(tmp_path, tok, arms, QIDS, picks, {"target": "ONE/KV-P/w1/FULL", "candidates": cands})
    m = run.post_match_arms(d)["match"]
    assert m["arm"] == "ONE/KV-P/w0.8/3ps/FULL" and m["matched"]


def test_t3b_verdict_uses_the_equivalence_margin():
    t3 = _script("report_t3_checks")
    inside = {"mean": -1.0, "ci90_lo": -4.0, "ci90_hi": 2.0}
    assert t3.verdict_t3b(0.0, 1.05, 1.0, inside, effect=30.0)[0] == "retained"  # −4 > −6
    below = {"mean": -12.0, "ci90_lo": -16.0, "ci90_hi": -8.0}
    assert t3.verdict_t3b(0.0, 1.05, 1.0, below, effect=30.0)[0] == "reduced"
    wide = {"mean": -3.0, "ci90_lo": -9.0, "ci90_hi": 3.0}
    assert t3.verdict_t3b(0.0, 1.05, 1.0, wide, effect=30.0)[0] == "inconclusive"
    assert t3.verdict_t3b(0.0, 1.40, 1.0, inside, effect=30.0)[0] == "unmatched"
    assert t3.verdict_t3b(0.2, 1.00, 1.0, inside, effect=30.0)[0] == "leaky"


def test_t3b_signal_config_compares_matched_strict_frame_with_second_person_w1(tmp_path):
    gen = _script("make_v3_t3b_signal")
    d = tmp_path / "s_t3b"
    d.mkdir()
    m = {"arm": "ONE/KV-P/w0.8/3ps/FULL", "gain": 0.8, "target_acc": 4.2, "arm_acc": 4.4, "matched": True}
    (d / "arm_match.json").write_text(json.dumps({"consumable": True, "match": m, "target": "ONE/KV-P/w1/FULL"}))
    cfg = gen.build(gen.match(d))
    out = tmp_path / "sig.yaml"
    out.write_text(__import__("yaml").safe_dump(cfg))
    names = {a.name for a in run.StageConfig.load(out).arm_configs()}
    assert names == {"C0/FULL", "ONE/KV-P/w1/FULL", "ONE/KV-P/w0.8/3ps/FULL", "ONE/KV-P/w2/FULL", "ONE/KV-P/w2/3ps/FULL"}
    assert cfg["params"]["studies"]["T3b"] == [["ONE/KV-P/w0.8/3ps/FULL", "ONE/KV-P/w1/FULL", "M", "0"],
                                               ["ONE/KV-P/w1/FULL", "C0/FULL", "M", "+"]]


def test_equivalence_keeps_or_fails_the_margin():
    eps = [f"e{i}" for i in range(40)]
    rng = np.random.default_rng(0)

    def scores(third_mean):
        rows = []
        for e in eps:
            rows += [{"episode_id": e, "recipient": "A", "arm": "C0/FULL", "M": rng.normal(0, 1)},
                     {"episode_id": e, "recipient": "A", "arm": "K", "M": rng.normal(50, 3)},
                     {"episode_id": e, "recipient": "A", "arm": "K3", "M": rng.normal(third_mean, 3)}]
        return pd.DataFrame(rows)

    spec = {"arm1": "K3", "arm2": "K", "effect_arm": "K", "base": "C0/FULL", "metric": "M", "margin": 0.2}
    kept = run._equivalence(scores(49.0), spec)
    assert kept["equivalent"] and kept["bound"] == pytest.approx(-0.2 * kept["effect"])
    assert not run._equivalence(scores(30.0), spec)["equivalent"]


def test_v3_confirm_config_carries_the_four_approved_comparisons(tmp_path):
    gen = _script("make_v3_confirm")
    d = tmp_path / "s_static_a"
    d.mkdir()
    m = {"static_arm": "STATIC/L24/raw/g0.1/FULL", "gain": 0.1, "target_acc": 4.2, "static_acc": 3.6, "matched": True}
    (d / "static_match.json").write_text(json.dumps({"consumable": True, "matches": {"ONE/KV-P/w1/FULL": m}}))
    (d / "config.yaml").write_text("calibration: {24: /gpu/cal/calibration_L24.pt}\n")
    cfg = gen.build(*gen.static_match(d))
    out = tmp_path / "confirm.yaml"
    out.write_text(__import__("yaml").safe_dump(cfg))
    names = {a.name for a in run.StageConfig.load(out).arm_configs()}
    assert names == {"C0/FULL", "ONE/KV-P/w1/FULL", "STATIC/L24/raw/g0.1/FULL", "ONE/KV-P/w2/FULL", "ONE/KV-P/w2/RF",
                     "ONE/KV-P/w2/3ps/FULL", "ONE/KV-P/w1/3ps/FULL"}
    fam = cfg["params"]["families"]
    assert fam["A'"] == [["ONE/KV-P/w1/FULL", "STATIC/L24/raw/g0.1/FULL", "M"]]
    assert fam["RF"] == [["ONE/KV-P/w2/FULL", "ONE/KV-P/w2/RF", "M"], ["ONE/KV-P/w2/RF", "C0/FULL", "M_NOW"]]
    eq = cfg["params"]["equivalence"]["T3_K*"]
    assert (eq["arm1"], eq["arm2"], eq["margin"]) == ("ONE/KV-P/w2/3ps/FULL", "ONE/KV-P/w2/FULL", 0.2)
    used = {x for spec in fam.values() for c in spec for x in c[:2]} | {eq["arm1"], eq["arm2"], eq["base"]}
    assert used <= names and cfg["n_episodes"] == 600
