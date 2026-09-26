"""Offline tests for run preparation, resume identity and gate completeness (review M2 B1/B2).

No torch: these exercise ``mb.run`` up to (not including) the model, plus the post steps.
"""

from __future__ import annotations

import json

import pytest
import yaml

from mb import chat, ledger, run, tasks

G1_ARMS = [{"condition": "C0", "recipients": ["A", "B"]}]
G1_QIDS = ["START", "START_R", "NOW", "NOW_R", "WORD", "WORD_R", "CAP0", "CAP1"]


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer()


@pytest.fixture()
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    return tmp_path


def _cfg(**over):
    base = dict(stage="g1", tag="t", split="unit", n_episodes=3, arms=G1_ARMS, qids=G1_QIDS, post=["g1"])
    base.update(over)
    return run.StageConfig(**base)


def _config_file(tmp_path, cfg):
    path = tmp_path / f"{cfg.stage}_{cfg.tag}.yaml"
    path.write_text(yaml.safe_dump({k: v for k, v in vars(cfg).items()}))
    return path


def _snapshot(run_dir):
    return {p.relative_to(run_dir): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}


def _records(cfg, limit, arm_hash, tok, correct=True, keep=lambda key: True, status="ok"):
    """Synthetic records for every expected trial: the correct label gets the top logit."""
    full, used = run.stage_episodes(cfg, limit)
    by_id = {e.episode_id: e for e in used}
    out = []
    for key in run.stage_expected(cfg, limit):
        if not keep(key):
            continue
        ep_id, arm, recipient, qid, rot = key
        q = tasks.make_question(tok, by_id[ep_id], recipient, qid, rot)
        target = run.G1_CORRECT.get(qid)
        logits = [0.0, 0.0, 0.0, 0.0]
        if target in q.label_meaning:
            i = q.label_meaning.index(target) if correct else (q.label_meaning.index(target) + 1) % 4
            logits[i] = 5.0
        out.append({"episode_id": ep_id, "arm": arm, "recipient": recipient, "qid": qid, "rotation_id": rot,
                    "options": list(q.options), "label_meaning": list(q.label_meaning), "label_logits": logits,
                    "label_mass": 0.99, "status": status, "config_hash": arm_hash[arm], "condition": "C0"})
    return out


def _write_records(run_dir, recs):
    w = ledger.ShardWriter(run_dir)
    for r in recs:
        w.write(r)
    w.close()


# --- B1: identity is fixed at creation and checked before any write on resume -------------


def test_new_run_writes_identity_once(data_root, tok):
    cfg = _cfg()
    prep = run.prepare_run(cfg, _config_file(data_root, cfg), None, None, tok=tok)
    assert not prep.resumed and not prep.smoke
    ident = json.loads((prep.run_dir / "identity.json").read_text())
    assert ident == prep.identity
    assert ident["stage_config"]["arms"][0]["recipients"] == ["A", "B"]
    assert {"template_hash", "cap_bank_hash", "tokenizer_manifest_sha", "source_hash"} <= set(ident)
    assert json.loads((prep.run_dir / "manifest.json").read_text())["smoke"] is False


def test_resume_with_same_identity_only_appends_resume_log(data_root, tok):
    cfg = _cfg()
    prep = run.prepare_run(cfg, _config_file(data_root, cfg), None, None, tok=tok)
    before = _snapshot(prep.run_dir)
    again = run.prepare_run(cfg, _config_file(data_root, cfg), None, prep.run_dir, tok=tok)
    assert again.resumed and again.identity == prep.identity
    after = _snapshot(prep.run_dir)
    assert {k: v for k, v in after.items() if k.name != "resume_log.jsonl"} == before
    assert len((prep.run_dir / "resume_log.jsonl").read_text().splitlines()) == 1


@pytest.mark.parametrize("change", [
    dict(n_episodes=4),
    dict(qids=G1_QIDS[:4]),
    dict(arms=[{"condition": "C0", "recipients": ["A"]}]),
    dict(seed=1),
])
def test_resume_refused_before_any_write(data_root, tok, change):
    cfg = _cfg()
    prep = run.prepare_run(cfg, _config_file(data_root, cfg), None, None, tok=tok)
    before = _snapshot(prep.run_dir)
    changed = _cfg(**change)
    with pytest.raises(SystemExit, match="resume refused"):
        run.prepare_run(changed, _config_file(data_root, changed), None, prep.run_dir, tok=tok)
    assert _snapshot(prep.run_dir) == before


def test_resume_refused_on_changed_limit(data_root, tok):
    cfg = _cfg()
    prep = run.prepare_run(cfg, _config_file(data_root, cfg), 2, None, tok=tok)
    assert prep.smoke and "smoke2" in prep.run_dir.name
    with pytest.raises(SystemExit, match="resume refused"):
        run.prepare_run(cfg, _config_file(data_root, cfg), None, prep.run_dir, tok=tok)


def test_resume_refused_on_changed_source(data_root, tok, monkeypatch):
    cfg = _cfg()
    prep = run.prepare_run(cfg, _config_file(data_root, cfg), None, None, tok=tok)
    monkeypatch.setattr(run, "source_hash", lambda: "different")
    with pytest.raises(SystemExit, match="source_hash"):
        run.prepare_run(cfg, _config_file(data_root, cfg), None, prep.run_dir, tok=tok)
    ok = run.prepare_run(cfg, _config_file(data_root, cfg), None, prep.run_dir, allow_code_change=True, tok=tok)
    assert ok.resumed


def test_calibrate_runs_cannot_resume(data_root, tok):
    cfg = _cfg(stage="calibrate", arms=[], post=[], calibration_layers=[12])
    prep = run.prepare_run(cfg, _config_file(data_root, cfg), None, None, tok=tok)
    with pytest.raises(SystemExit, match="cannot be resumed"):
        run.prepare_run(cfg, _config_file(data_root, cfg), None, prep.run_dir, tok=tok)


def test_latest_calibration_skips_smoke_and_unfinished(data_root):
    base = data_root / "results"
    for name, smoke, finished in (("20260101-000000_calibrate_a", False, True),
                                  ("20260102-000000_calibrate_b-smoke2", True, True),
                                  ("20260103-000000_calibrate_c", False, False)):
        d = base / name
        d.mkdir(parents=True)
        (d / "calibration.json").write_text(json.dumps({"18": f"{name}/calibration_L18.pt"}))
        (d / "manifest.json").write_text(json.dumps({"smoke": smoke}))
        if finished:
            (d / "run_status.json").write_text(json.dumps({"status": "complete"}))
    assert run.resolve_calibration("latest") == {18: "20260101-000000_calibrate_a/calibration_L18.pt"}
    (base / "20260101-000000_calibrate_a" / "manifest.json").write_text(json.dumps({"smoke": True}))
    with pytest.raises(SystemExit):
        run.resolve_calibration("latest")
    assert run.resolve_calibration("latest", allow_smoke=True) == {
        18: "20260102-000000_calibrate_b-smoke2/calibration_L18.pt"}


def test_stage_config_validation():
    with pytest.raises(ValueError):
        _cfg(qids=["START", "NOPE"])
    with pytest.raises(ValueError):
        _cfg(post=["g2_magic"])
    with pytest.raises(ValueError, match="stopped endpoint"):
        _cfg(qids=["START", "BEH"])
    assert "BEH" not in run.StageConfig(stage="g1", tag="t", split="u", n_episodes=1).qids
    with pytest.raises(ValueError, match="duplicate arm names"):
        _cfg(arms=[{"condition": "SCRAM", "gain": 0.3, "scram_seed": 1},
                   {"condition": "SCRAM", "gain": 0.3, "scram_seed": 2}])


# --- B2: gates and selections refuse incomplete data; smoke output is never consumable -----


def _g1_run(data_root, tok, limit=None):
    cfg = _cfg()
    prep = run.prepare_run(cfg, _config_file(data_root, cfg), limit, None, tok=tok)
    arm_hash = {"C0/FULL": "h-c0"}
    (prep.run_dir / "arm_hashes.json").write_text(json.dumps(arm_hash))
    return cfg, prep, arm_hash


def test_g1_passes_only_when_complete(data_root, tok):
    cfg, prep, arm_hash = _g1_run(data_root, tok)
    recs = _records(cfg, None, arm_hash, tok)
    # Review repro: only the first episode succeeds, all others failed -> must not pass.
    first = recs[0]["episode_id"]
    _write_records(prep.run_dir, [r if r["episode_id"] == first else dict(r, status="failed") for r in recs])
    s = run.post_g1(prep.run_dir)
    assert s["G1"] == "incomplete" and not s["consumable"]
    assert s["completeness"]["n_missing"] > 0
    # Retrying the failed trials (new shard) completes the run; the audit keeps both records.
    _write_records(prep.run_dir, [r for r in recs if r["episode_id"] != first])
    s = run.post_g1(prep.run_dir)
    assert s["G1"] == "pass" and s["consumable"]
    # 3 episodes x 2 rotations, reported per recipient as well as pooled (failed rows excluded).
    assert s["accuracy"]["START"]["A"]["n"] == s["accuracy"]["START"]["B"]["n"] == 6
    assert s["accuracy"]["START"]["all"]["n"] == 12


def test_g1_fails_on_wrong_answers_and_lists_items(data_root, tok):
    cfg, prep, arm_hash = _g1_run(data_root, tok)
    recs = _records(cfg, None, arm_hash, tok)
    bad = _records(cfg, None, arm_hash, tok, correct=False)
    mixed = [b if r["qid"] == "NOW_R" else r for r, b in zip(recs, bad)]
    _write_records(prep.run_dir, mixed)
    s = run.post_g1(prep.run_dir)
    assert s["G1"] == "fail" and s["failing_items"] == ["NOW_R"]


def test_g1_ignores_records_under_another_config_hash(data_root, tok):
    cfg, prep, arm_hash = _g1_run(data_root, tok)
    _write_records(prep.run_dir, _records(cfg, None, {"C0/FULL": "stale"}, tok))
    assert run.post_g1(prep.run_dir)["G1"] == "incomplete"


def test_smoke_g1_is_never_consumable(data_root, tok):
    cfg, prep, arm_hash = _g1_run(data_root, tok, limit=2)
    _write_records(prep.run_dir, _records(cfg, 2, arm_hash, tok))
    s = run.post_g1(prep.run_dir)
    assert s["G1"] == "pass" and s["smoke"] and not s["consumable"]


def test_pilot_a_selection_refuses_incomplete(data_root, tok):
    arms = [{"condition": "C0"}, {"condition": "ONE", "gain": 0.3, "layer": 18}]
    cfg = run.StageConfig(stage="pilot_a", tag="t", split="unit-a", n_episodes=4, arms=arms,
                          qids=["ACC_RULE", "ACC_WORD", "CAP0", "CAP1"], post=["select_pilot_a"])
    run_dir = data_root / "results" / "pa"
    run_dir.mkdir(parents=True)
    (run_dir / "identity.json").write_text(json.dumps(run.build_identity(cfg, None, "tmpl", {})))
    (run_dir / "manifest.json").write_text(json.dumps({"smoke": False}))
    arm_hash = {"C0/FULL": "h0", "ONE/L18/raw/g0.3/FULL": "h1"}
    (run_dir / "arm_hashes.json").write_text(json.dumps(arm_hash))
    recs = _records(cfg, None, arm_hash, tok)
    for r in recs:
        r.update(condition=r["arm"].split("/")[0], layer=18, gain=0.3 if r["arm"].startswith("ONE") else 0.0,
                 message_form="raw")
    # Review repro: C0 complete, ONE has a single rotation of a single episode.
    one = [r for r in recs if r["arm"].startswith("ONE")]
    _write_records(run_dir, [r for r in recs if r["arm"] == "C0/FULL"] + one[:1])
    out = run.post_select_pilot_a(run_dir)
    assert out["selection"] == "incomplete" and not out["consumable"]
    _write_records(run_dir, one[1:])
    out = run.post_select_pilot_a(run_dir)
    assert out["selection"] != "incomplete" and out["consumable"]


# --- I5: identity hashes cover what they claim to cover -----------------------------------


def test_template_and_prefix_hash_scope(tok, monkeypatch):
    p0, t0 = run.prefix_hash(tok), run.template_hash(tok)
    assert (p0, t0) == (run.prefix_hash(tok), run.template_hash(tok))  # stable
    monkeypatch.setattr(tasks, "ANSWER_LINE", "Answer with a digit.")
    assert run.prefix_hash(tok) == p0, "calibration must not depend on readout wording"
    assert run.template_hash(tok) != t0
    monkeypatch.undo()
    monkeypatch.setitem(tasks.REFLECTION_PROMPTS, "v1", "Think it over.")
    assert run.prefix_hash(tok) != p0 and run.template_hash(tok) != t0
    monkeypatch.undo()
    monkeypatch.setattr(chat, "IM_END", chat.ENDOFTEXT)  # ChatML assembly change
    assert run.template_hash(tok) != t0
    monkeypatch.undo()
    ref = tasks.make_episodes(1, "template-ref", seed=0)[0]
    item = next(c for c in tasks.cap_bank() if c.item_id not in ref.cap_items)  # not drawn by the reference
    monkeypatch.setattr(tasks, "_CAP_CACHE", tasks._CapCache(tuple(
        tasks.CapItem(c.item_id, c.question + (" Think." if c is item else ""), c.options, c.correct)
        for c in tasks.cap_bank())))
    assert run.template_hash(tok) != t0


# --- Pilot B selection and the separate sample-size step ----------------------------------


def _pilot_b_run(data_root, tok, drop_last=False):
    import random

    arms = [{"condition": "C0", "layer": 24}, {"condition": "LANG_TAG", "layer": 24}]
    for cond, grid in (("ONE", (0.1, 0.3)), ("TWO", (0.1, 0.3)), ("STATIC", (0.1, 0.3))):
        arms += [{"condition": cond, "form": "raw", "layer": 24, "gain": g} for g in grid]
    cfg = run.StageConfig(stage="pilot_b", tag="t", split="unit-b", n_episodes=4, arms=arms,
                          qids=["START", "START_R", "ACC_RULE", "CAP0", "CAP1"], post=["select_pilot_b", "sample_size"])
    run_dir = data_root / "results" / "pb"
    run_dir.mkdir(parents=True)
    (run_dir / "identity.json").write_text(json.dumps(run.build_identity(cfg, None, "tmpl", {})))
    (run_dir / "manifest.json").write_text(json.dumps({"smoke": False}))
    arm_hash = {a.name: f"h{i}" for i, a in enumerate(cfg.arm_configs())}
    (run_dir / "arm_hashes.json").write_text(json.dumps(arm_hash))
    by_name = {a.name: a for a in cfg.arm_configs()}
    rng = random.Random(0)
    recs = _records(cfg, None, arm_hash, tok)
    for r in recs:
        a = by_name[r["arm"]]
        r.update(condition=a.condition, layer=a.layer, gain=a.gain, message_form=a.form)
        r["label_logits"] = [z + rng.gauss(0, 0.3) for z in r["label_logits"]]
        if r["qid"] == "ACC_RULE" and a.condition == "ONE" and a.gain == 0.3:
            r["label_logits"][r["label_meaning"].index("partner")] += 1.0  # the transmitting point
    if drop_last:
        recs = recs[:-1]
    _write_records(run_dir, recs)
    return run_dir


def test_pilot_b_selection_and_sample_size(data_root, tok):
    run_dir = _pilot_b_run(data_root, tok)
    sel = run.post_select_pilot_b(run_dir)
    assert sel["consumable"] and sel["selection"]["ok"]
    assert sel["selection"]["g_star"] == 0.3 and (sel["form"], sel["layer"]) == ("raw", 24)
    size = run.post_sample_size(run_dir)
    assert 300 <= size["N"] <= 600 and size["N"] % 4 == 0
    assert set(size["sd_of_paired_M"]) == {"TWO/L24/raw/g0.3/FULL - ONE/L24/raw/g0.3/FULL",
                                           f"ONE/L24/raw/g0.3/FULL - STATIC/L24/raw/g{sel['selection']['g_static']:g}/FULL",
                                           "ONE/L24/raw/g0.3/FULL - LANG_TAG/FULL"}
    assert not any("mean" in k for k in size)  # only variances feed N


def test_pilot_b_incomplete_gives_no_selection_and_no_n(data_root, tok):
    run_dir = _pilot_b_run(data_root, tok, drop_last=True)
    assert run.post_select_pilot_b(run_dir)["selection"] == "incomplete"
    size = run.post_sample_size(run_dir)
    assert size["N"] is None and not size["consumable"]


def test_make_pilot_b_config_requires_consumable_selection(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("make_pilot_b", run.REPO_ROOT / "scripts" / "make_pilot_b.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    (tmp_path / "identity.json").write_text(json.dumps({"calibration": {"24": {"path": "/x/calibration_L24.pt"}}}))
    good = {"consumable": True, "selection": {"ok": True, "form": "raw", "layer": 24, "gain": 0.3, "score": 1.8}}
    (tmp_path / "pilot_a_selection.json").write_text(json.dumps(good))
    cfg, _ = mod.build(tmp_path / "pilot_a_selection.json")
    parsed = run.StageConfig(**cfg)
    assert len(parsed.arm_configs()) == 2 + 8 + 8 + 8 and parsed.calibration == {24: "/x/calibration_L24.pt"}
    for bad in (dict(good, consumable=False), dict(good, selection="incomplete"),
                dict(good, selection=dict(good["selection"], ok=False))):
        (tmp_path / "pilot_a_selection.json").write_text(json.dumps(bad))
        with pytest.raises(SystemExit):
            mod.build(tmp_path / "pilot_a_selection.json")


# --- Pilot C / G2 ---------------------------------------------------------------------------


def _pilot_c_run(data_root, tok, effect: float, name="pc"):
    import random

    arms = [{"condition": "C0", "layer": 24},
            {"condition": "ONE", "form": "raw", "layer": 24, "gain": 0.3},
            {"condition": "CF", "form": "raw", "layer": 24, "gain": 0.3}]
    cfg = run.StageConfig(stage="pilot_c", tag="t", split="unit-c", n_episodes=12, arms=arms,
                          qids=["ACC_RULE", "ACC_WORD", "CAP0", "CAP1"], post=["pilot_c"])
    run_dir = data_root / "results" / name
    run_dir.mkdir(parents=True)
    (run_dir / "identity.json").write_text(json.dumps(run.build_identity(cfg, None, "tmpl", {})))
    (run_dir / "manifest.json").write_text(json.dumps({"smoke": False}))
    arm_hash = {a.name: f"h{i}" for i, a in enumerate(cfg.arm_configs())}
    (run_dir / "arm_hashes.json").write_text(json.dumps(arm_hash))
    _, used = run.stage_episodes(cfg, None)
    rng = random.Random(1)
    recs = []
    for key in run.stage_expected(cfg, None):
        ep_id, arm, recipient, qid, rot = key
        ep = next(e for e in used if e.episode_id == ep_id)
        cond = arm.split("/")[0]
        view = tasks.make_donor_variant(ep, "CF").donor_episode if cond == "CF" else ep
        q = tasks.make_question(tok, view, recipient, qid, rot)
        logits = [rng.gauss(0, 0.5) for _ in range(4)]
        if qid.startswith("CAP"):
            logits[q.label_meaning.index("correct")] += 5.0
        elif cond in ("ONE", "CF"):
            actual = view.rule.B if qid == "ACC_RULE" else view.word.B  # the donor actually connected
            logits[list(q.options).index(actual)] += effect
        rec = {"episode_id": ep_id, "arm": arm, "recipient": recipient, "qid": qid, "rotation_id": rot,
               "options": list(q.options), "label_meaning": list(q.label_meaning), "label_logits": logits,
               "label_mass": 0.99, "status": "ok", "config_hash": arm_hash[arm], "condition": cond,
               "layer": 24, "gain": 0.0 if cond == "C0" else 0.3, "message_form": "raw", "text_hash": q.text_hash}
        if cond == "CF":
            rec.update(cf_r0_rule=ep.rule.B, cf_r1_rule=ep.rule.spare, cf_r0_word=ep.word.B, cf_r1_word=ep.word.spare)
        recs.append(rec)
    _write_records(run_dir, recs)
    return run_dir


def test_g2_passes_when_content_follows_the_donor(data_root, tok):
    out = run.post_pilot_c(_pilot_c_run(data_root, tok, effect=2.0))
    g2 = out["g2_detail"]
    assert out["G2"] == "pass" and out["consumable"]
    assert g2["C_content_rule"]["mean"] == pytest.approx(4.0, abs=0.6)  # (+2) - (-2)
    assert g2["C_content_rule"]["lb95_one_sided"] > 0 and g2["one_meets_engineering_gates"]


def test_g2_fails_without_content_transfer(data_root, tok):
    out = run.post_pilot_c(_pilot_c_run(data_root, tok, effect=0.0, name="pc0"))
    assert out["G2"] == "fail"
    assert out["g2_detail"]["C_content_rule"]["lb95_one_sided"] <= 0


def test_make_pilot_c_config(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("make_pilot_c", run.REPO_ROOT / "scripts" / "make_pilot_c.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pa, pb = tmp_path / "pa", tmp_path / "pb"
    pa.mkdir()
    pb.mkdir()
    cal = {str(l): {"path": f"/x/calibration_L{l}.pt"} for l in (12, 18, 24)}
    (pa / "identity.json").write_text(json.dumps({"calibration": cal}))
    (pa / "pilot_a_selection.json").write_text(json.dumps({"consumable": True, "selection": {
        "ok": True, "form": "raw", "layer": 24, "gain": 0.3, "score": 1.8,
        "per_layer_gain": {"12": 0.3, "18": None, "24": 0.3}}}))
    (pb / "pilot_b_selection.json").write_text(json.dumps({"consumable": True, "form": "raw", "layer": 24, "selection": {
        "ok": True, "g_star": 0.2, "main_gains": [0.05, 0.1, 0.2, 0.3], "g_static": 0.5, "static_matched": True,
        "static_neighbors": [0.3, 0.7], "static_executable": True}}))
    cfg, _ = mod.build(pa, pb)
    parsed = run.StageConfig(**cfg)
    names = [a.name for a in parsed.arm_configs()]
    assert "CF/L24/raw/g0.2/FULL" in names and "STATIC/L24/raw/g0.5/FULL" in names
    assert "ONE/L12/raw/g0.3/FULL" in names and not any("/L18/" in n for n in names)  # L18 unusable
    assert "ONE/L24/raw/g0.3/FULL" in names and "ONE/L24/raw/g0.2/FULL" in names  # g*_24 differs from g*
    assert parsed.calibration == {12: "/x/calibration_L12.pt", 24: "/x/calibration_L24.pt"}


# --- formal stage generation and the pre-registered analysis --------------------------------


def test_episode_generation_is_prefix_stable():
    """Formal stages share the main split: the first k episodes must not depend on N."""
    long = tasks.make_episodes(600, "main", 0)
    assert tasks.make_episodes(60, "main", 0) == long[:60]
    assert tasks.make_episodes(300, "main", 0) == long[:300]


def _fake_pilots(tmp_path, g2="pass", n=400):
    pa, pb, pc = (tmp_path / x for x in ("pa", "pb", "pc"))
    for d in (pa, pb, pc):
        d.mkdir()
    cal = {str(l): {"path": f"/x/calibration_L{l}.pt"} for l in (12, 18, 24)}
    (pa / "identity.json").write_text(json.dumps({"calibration": cal}))
    (pa / "pilot_a_selection.json").write_text(json.dumps({"consumable": True, "selection": {
        "ok": True, "form": "raw", "layer": 24, "gain": 0.3, "score": 1.8,
        "per_layer_gain": {"12": 0.3, "18": 0.1, "24": 0.3}}}))
    (pb / "pilot_b_selection.json").write_text(json.dumps({"consumable": True, "form": "raw", "layer": 24, "selection": {
        "ok": True, "g_star": 0.3, "main_gains": [0.05, 0.1, 0.2, 0.3, 0.5], "g_static": 0.5, "static_matched": True,
        "static_neighbors": [0.3, 0.7], "static_executable": True}}))
    (pb / "sample_size.json").write_text(json.dumps({"consumable": True, "N": n, "mde_at_N": 0.5,
                                                     "sd_of_paired_M": {"x": 3.0}}))
    (pc / "pilot_c.json").write_text(json.dumps({"consumable": True, "G2": g2, "g2_detail": {"C_content_rule": {}}}))
    return pa, pb, pc


def _load_script(name):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, run.REPO_ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_make_main_builds_protocol_condition_set(tmp_path):
    mod = _load_script("make_main")
    configs = mod.build_all(*_fake_pilots(tmp_path))
    main = run.StageConfig(**configs["main"])
    names = [a.name for a in main.arm_configs()]
    assert main.n_episodes == 400 and main.all_rotations_first == 60 and main.post == ["confirmatory"]
    assert sum(n.startswith("ONE/L24/raw/") and n.endswith("/FULL") for n in names) == 5
    assert sum(n.startswith("TWO/L24/raw/") and n.endswith("/FULL") for n in names) == 5
    assert {"STATIC/L24/raw/g0.3/FULL", "STATIC/L24/raw/g0.5/FULL", "STATIC/L24/raw/g0.7/FULL"} <= set(names)
    assert {"LANG_TAG/FULL", "LANG_UNTAG/FULL", "MISMATCH/L24/raw/g0.3/FULL", "SCRAM/L24/raw/g0.3/FULL",
            "ONE/L24/raw/g0.3/RF", "ONE/L24/raw/g0.3/RO", "TWO/L24/raw/g0.3/RF", "TWO/L24/raw/g0.3/RO"} <= set(names)
    assert not any(n.startswith("CF/") for n in names)  # CF only in the diagnostic subset
    diag = run.StageConfig(**configs["main_diag"])
    assert diag.n_episodes == 60 and [a.condition for a in diag.arm_configs()] == ["C0", "ONE", "CF"]
    ext_l = run.StageConfig(**configs["ext_layers"])
    assert ext_l.n_episodes == 300 and {a.layer for a in ext_l.arm_configs() if a.bridged} == {12, 18, 24}
    ext_m = run.StageConfig(**configs["ext_masks"])
    assert sum(a.condition == "MASK" for a in ext_m.arm_configs()) == 9
    for cfg in configs.values():
        assert cfg["frozen"]["g_star"] == 0.3 and cfg["split"] == "main"


@pytest.mark.parametrize("g2", ["fail", "incomplete"])
def test_make_main_refuses_without_g2(tmp_path, g2):
    mod = _load_script("make_main")
    with pytest.raises(SystemExit, match="G2"):
        mod.build_all(*_fake_pilots(tmp_path, g2=g2))


def test_confirmatory_analysis_reports_three_contrasts(data_root, tok):
    import random

    frozen = {"g_star": 0.3, "g_static": 0.5, "static_executable": True}
    arms = [{"condition": "C0", "layer": 24, "recipients": ["A", "B"]},
            {"condition": "ONE", "form": "raw", "layer": 24, "gain": 0.3},
            {"condition": "TWO", "form": "raw", "layer": 24, "gain": 0.3, "recipients": ["A", "B"]},
            {"condition": "STATIC", "form": "raw", "layer": 24, "gain": 0.5},
            {"condition": "LANG_TAG", "layer": 24}]
    cfg = run.StageConfig(stage="main", tag="t", split="unit-m", n_episodes=8, arms=arms, frozen=frozen,
                          qids=["START", "START_R", "NOW", "NOW_R", "WORD", "WORD_R", "ACC_RULE", "ACC_WORD",
                                "CAP0", "CAP1"], post=["confirmatory"])
    run_dir = data_root / "results" / "main"
    run_dir.mkdir(parents=True)
    (run_dir / "identity.json").write_text(json.dumps(run.build_identity(cfg, None, "tmpl", {})))
    (run_dir / "manifest.json").write_text(json.dumps({"smoke": False}))
    arm_hash = {a.name: f"h{i}" for i, a in enumerate(cfg.arm_configs())}
    (run_dir / "arm_hashes.json").write_text(json.dumps(arm_hash))
    by_name = {a.name: a for a in cfg.arm_configs()}
    rng = random.Random(3)
    recs = _records(cfg, None, arm_hash, tok)
    for r in recs:
        a = by_name[r["arm"]]
        r.update(condition=a.condition, layer=a.layer, gain=a.gain, message_form=a.form, readout_mode=a.readout_mode)
        r["label_logits"] = [z + rng.gauss(0, 0.5) for z in r["label_logits"]]
    _write_records(run_dir, recs)
    out = run.post_confirmatory(run_dir)
    assert [(c["arm1"].split("/")[0], c["arm2"].split("/")[0]) for c in out["primary"]] == [
        ("TWO", "ONE"), ("ONE", "STATIC"), ("ONE", "LANG_TAG")]
    assert all(c["n"] == 8 and c["p_holm"] >= c["p_two_sided"] for c in out["primary"])
    assert len(out["secondary"]) == 6 and len(out["robustness"]) == 3
    assert {d["recipient"] for d in out["descriptive"]} == {"A", "B"}


def test_freeze_manifest_verification(tmp_path, monkeypatch):
    mod = _load_script("freeze_protocol")
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "FREEZE", tmp_path / "FREEZE.txt")
    for p in mod.frozen_files() + [tmp_path / "src" / "mb" / "x.py"]:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"content of {p.name}")
    files = mod.frozen_files()
    (tmp_path / "FREEZE.txt").write_text("# header\n" + "\n".join(
        f"{mod.digest(p)}  {p.relative_to(tmp_path)}" for p in files) + "\n")
    assert mod.verify() == 0
    (tmp_path / "configs" / "main.yaml").write_text("edited after the freeze")
    assert mod.verify() == 1
    (tmp_path / "configs" / "main.yaml").write_text("content of main.yaml")
    (tmp_path / "src" / "mb" / "new_module.py").write_text("unlisted code")
    assert mod.verify() == 1


def test_materials_versions_have_their_own_identity(tok):
    """Protocol v2 study E: balanced materials must never share a calibration with v1 materials."""
    assert run.prefix_hash(tok, "balanced") != run.prefix_hash(tok, "v1")
    assert run.template_hash(tok, "balanced") != run.template_hash(tok, "v1")
    with pytest.raises(ValueError):
        _cfg(materials="nope")


def test_v3_freeze_lists_the_confirm_config_and_chain_driver(tmp_path, monkeypatch):
    mod = _load_script("freeze_protocol")
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    (tmp_path / "configs" / "v3").mkdir(parents=True)
    for name in ("v3_confirm.yaml", "s_live.yaml", "sig_t3b.yaml"):
        (tmp_path / "configs" / "v3" / name).write_text("x")
    mod.configure("v3")
    rel = {str(p.relative_to(tmp_path)) for p in mod.frozen_files()}
    assert {"docs/protocol/PROTOCOL_V3.md", "scripts/make_v3_confirm.py", "scripts/run_chain.sh",
            "configs/v3/v3_confirm.yaml"} <= rel
    assert "configs/v3/s_live.yaml" not in rel  # pilots are not part of the frozen formal stage
    assert mod.FREEZE.name == "FREEZE_protocol_v3.txt"
