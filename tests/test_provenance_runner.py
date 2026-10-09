"""V5 opt-in, donor wiring, resume identity and sealed note-cache reuse (no torch)."""

import dataclasses
import io
import json
import sys
from types import SimpleNamespace

import pytest
import yaml

from mb import chat, ledger, provenance_tasks as p, run, tasks
from mb.conditions import ArmConfig
from mb.model_profiles import QWEN


def config(phase="confirm", **changes):
    stage = f"v5_qwen_provenance_{phase}"
    args = dict(stage=stage, split=stage, tag="unit", n_episodes=2, model_profile=QWEN.key,
                qids=list(p.PHASE_QIDS[phase]), params={"provenance_contract": p.CONTRACT},
                arms=[{"condition": "C0"},
                      {"condition": "ONE", "interface": "kv", "kv_scope": "P", "gain": 1.0},
                      {"condition": "ONE", "interface": "kv", "kv_scope": "P", "gain": 1.0,
                       "donor_robin_conflict": True}])
    args.update(changes)
    return run.StageConfig(**args)


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer(profile=QWEN.key)


def bare_runner(cfg, tok):
    r = run.Runner.__new__(run.Runner)
    r.cfg, r.tok, r.notes = cfg, tok, {}
    r.template_hash, r.profile = "template", QWEN
    r.writer, r.pass_index = SimpleNamespace(path=SimpleNamespace(stem="attempt-000")), 0
    return r


def test_conflict_identity_is_unique_and_legacy_hashes_are_unchanged():
    arms = [ArmConfig("C0"),
            ArmConfig("ONE", interface="kv", kv_scope="P", gain=1.0, layer=21,
                      model_profile="llama31_8b_instruct"),
            ArmConfig("STATIC", gain=.7, layer=21)]
    assert [a.config_hash("cal", "mask", "template") for a in arms] == [
        "9e719c9b82896d6b", "952b707c99520a8c", "01e43caea2637e21"]
    for a in arms:
        assert "donor_robin_conflict" not in a.identity("cal", "mask", "template")
    original = config().arm_configs()[1]
    changed = dataclasses.replace(original, donor_robin_conflict=True)
    assert original.name != changed.name
    assert original.config_hash("none", "none", "t") != changed.config_hash("none", "none", "t")
    assert len(run.reflection_groups([original, changed])) == 2
    assert "donor_robin_conflict" not in config().resolved()["arms"][0]


@pytest.mark.parametrize("changes", [
    {"stage": "v4_llama31_confirm"}, {"split": "different"}, {"params": {}},
    {"params": {"provenance_contract": "wrong"}}, {"materials": "balanced2"},
    {"model_profile": "llama31_8b_instruct"}, {"qids": ["START"]},
    {"arms": [{"condition": "STATIC", "gain": .1}]},
])
def test_provenance_contract_fails_closed(changes):
    with pytest.raises(ValueError):
        config(**changes)


def test_conflict_cannot_leak_into_an_old_stage():
    with pytest.raises(ValueError, match="restricted"):
        run.StageConfig(stage="old", split="old", tag="unit", n_episodes=2,
                        arms=[{"condition": "C0", "donor_robin_conflict": True}])
    with pytest.raises(ValueError, match="unknown qids"):
        run.StageConfig(stage="old", split="old", tag="unit", n_episodes=2,
                        qids=list(p.ALL_QIDS))
    for change in ({"condition": "STATIC", "gain": .1},
                   {"condition": "CF", "interface": "kv", "kv_scope": "P", "gain": 1.0},
                   {"condition": "ONE", "interface": "kv", "kv_scope": "ALL", "gain": 1.0}):
        with pytest.raises(ValueError, match="Robin conflict"):
            ArmConfig(**change, donor_robin_conflict=True)


def test_real_runner_wires_unchanged_A_changed_B_and_fixed_questions(tok):
    cfg = config()
    r = bare_runner(cfg, tok)
    episodes = tasks.make_episodes(2, cfg.split)
    original, conflict = cfg.arm_configs()[1:]
    views = r._donors(conflict, episodes)
    for ep, donor in zip(episodes, views):
        r.notes[r._note_key(ep, "A")] = chat.encode(tok, "A saved note")
        r.notes[r._note_key(ep, "B")] = chat.encode(tok, "B old saved note")
        r.notes[r._note_key(donor, "B")] = chat.encode(tok, "B conflicting saved note")
        assert r.prefix(ep, "B") != r.prefix(donor, "B")
    normal = r._pending_questions(original, episodes, episodes, set(), set())
    altered = r._pending_questions(conflict, episodes, views, set(), set())
    assert len(normal) == len(altered) == 2 * 12 * 2
    for (i, who, q0), (_, _, q1) in zip(normal, altered):
        assert q0 == q1
        ident = conflict.identity("none", "none", "template")
        rec = r._base_record(conflict, ident, "config", "none", episodes[i], who, q1)
        meta = rec["provenance"]
        assert meta["receiver_truth"]["rule_robin"] == episodes[i].rule.robin
        assert meta["donor_truth"]["rule_robin"] == episodes[i].rule.spare
    done = {(episodes[i].episode_id, conflict.name, who, q.qid, q.rotation_id) for i, who, q in altered}
    assert r._pending_questions(conflict, episodes, views, set(), done) == []


def test_actual_arm_path_passes_same_A_prefix_and_changed_B_to_engine(tok, monkeypatch):
    # Stop immediately after the real orchestration assembles the model inputs.
    # This exercises the donor wiring without importing torch or executing a model.
    import mb
    monkeypatch.setitem(sys.modules, "mb.runtime", SimpleNamespace(U_OPEN_TOKENS=80, make_plan=lambda *args: None))
    monkeypatch.delattr(mb, "runtime", raising=False)
    cfg = config()
    r = bare_runner(cfg, tok)
    ep = tasks.make_episodes(1, cfg.split)[0]
    donor = p.donor_episode(ep)
    for record, role, text in ((ep, "A", "A note"), (ep, "B", "original B note"),
                                (donor, "B", "conflicting B note")):
        r.notes[r._note_key(record, role)] = chat.encode(tok, text)
    r.torch, r.new_records = SimpleNamespace(), []
    r.ensure_notes = lambda *args: None
    r.arm_identity = lambda arm: (arm.identity("none", "none", "t"), "config", "none")
    r.writer.flush, r.writer.write, r.log = lambda: None, lambda record: None, lambda line: None
    seen = []
    def prefill(prefixes):
        seen.append(prefixes)
        raise RuntimeError("intentional model-free stop after input assembly")
    engine = SimpleNamespace(prefill=prefill)
    for arm in cfg.arm_configs()[1:]:
        assert r.run_arm_chunk(engine, arm, [ep], set(), set(), 0) is None
    assert seen[0][0] == seen[1][0] == r.prefix(ep, "A")
    assert seen[0][1] == r.prefix(ep, "B")
    assert seen[1][1] == r.prefix(donor, "B")
    assert seen[0][1] != seen[1][1]


def test_native_B_baseline_uses_conflicting_B_record(tok):
    cfg = config("base", arms=[{"condition": "C0", "recipients": ["A", "B"]},
        {"condition": "C0", "donor_robin_conflict": True, "recipients": ["A", "B"]}])
    r = bare_runner(cfg, tok)
    arm = cfg.arm_configs()[1]
    episodes = tasks.make_episodes(2, cfg.split)
    specs = r._pending_questions(arm, episodes, r._donors(arm, episodes), set(), set())
    assert len(specs) == 2 * 2 * 8 * 2
    for i, who, q in specs:
        if who == "B" and q.qid == "PROV_ROBIN_RULE":
            rec = r._base_record(arm, arm.identity("none", "none", "t"), "c", "none", episodes[i], who, q)
            assert rec["provenance"]["expected_truth"] == episodes[i].rule.spare
            assert rec["provenance"]["donor_truth"]["rule_robin"] == episodes[i].rule.robin


def test_new_readouts_are_in_template_hash_and_resume_identity(tok, tmp_path, monkeypatch):
    plain = run.template_hash(tok, profile=QWEN.key)
    prov = run.template_hash(tok, profile=QWEN.key, provenance=True)
    assert plain != prov
    original = p.template_sequences
    monkeypatch.setattr(p, "template_sequences", lambda *args: original(*args) + [[123]])
    assert run.template_hash(tok, profile=QWEN.key) == plain
    assert run.template_hash(tok, profile=QWEN.key, provenance=True) != prov
    monkeypatch.setattr(p, "template_sequences", original)
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    cfg = config()
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(dataclasses.asdict(cfg)))
    prep = run.prepare_run(cfg, path, None, None, tok=tok)
    assert prep.identity["template_hash"] == prov
    before = {str(f): f.read_bytes() for f in prep.run_dir.rglob("*") if f.is_file()}
    modified = dataclasses.replace(cfg, arms=cfg.arms[:-1])
    with pytest.raises(SystemExit, match="resume refused"):
        run.prepare_run(modified, path, None, prep.run_dir, tok=tok)
    assert {str(f): f.read_bytes() for f in prep.run_dir.rglob("*") if f.is_file()} == before


def reusable_fixture(tmp_path):
    cfg = run.StageConfig(stage="v5_llama_static_refine1", split="v5_llama_static_match", tag="refine",
        n_episodes=40, model_profile="llama31_8b_instruct",
        arms=[{"condition": "STATIC", "gain": .2, "layer": 21}], qids=["ACC_RULE"])
    records = [{"key": tasks.note_key(ep, role), "episode_id": ep.episode_id, "role": role,
                "ids": [11, 12], "n_tokens": 2, "note": "saved native tokens"}
               for ep in tasks.make_episodes(40, cfg.split) for role in tasks.ROLES]
    path = tmp_path / "source_notes.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records))
    cfg.params = {"phase": "refine1", "sources": {
        "reuse_notes": {"path": str(path), "sha256": ledger.file_sha256(path)}}}
    return cfg, records, path


def test_reused_note_cache_is_pinned_complete_and_append_only(tmp_path):
    cfg, records, path = reusable_fixture(tmp_path)
    run.validate_stage_sources(cfg)
    assert run.reusable_notes(cfg) == records
    r = run.Runner.__new__(run.Runner)
    r.notes, r.notes_log = {}, io.StringIO()
    r._seed_reused_notes(records)
    before = r.notes_log.getvalue()
    r._seed_reused_notes(records)
    assert r.notes_log.getvalue() == before
    assert r.notes == {record["key"]: record["ids"] for record in records}
    r.notes[records[0]["key"]] = [99]
    with pytest.raises(ValueError, match="stored notes differ"):
        r._seed_reused_notes(records)
    assert r.notes_log.getvalue() == before
    path.write_text(path.read_text() + "{")
    with pytest.raises(ValueError, match="integrity"):
        run.validate_stage_sources(cfg)
    cfg.params["sources"]["reuse_notes"]["sha256"] = ledger.file_sha256(path)
    with pytest.raises(ValueError, match="malformed or truncated"):
        run.reusable_notes(cfg)
    path.write_text(json.dumps(records[0]) + "\n")
    cfg.params["sources"]["reuse_notes"]["sha256"] = ledger.file_sha256(path)
    with pytest.raises(ValueError, match="incomplete"):
        run.reusable_notes(cfg)


@pytest.mark.parametrize("module,post", [("v5_static", "v5_static_match"),
                                        ("v5_provenance", "v5_provenance_contrasts")])
def test_new_post_dispatch_preserves_original_config(tmp_path, monkeypatch, module, post):
    cfg = config(post=[post])
    (tmp_path / "manifest.json").write_text('{"smoke": false}')
    monkeypatch.setattr(run, "run_completeness", lambda path: {"status": "complete"})
    calls = []
    monkeypatch.setitem(sys.modules, f"mb.{module}", SimpleNamespace(
        postprocess=lambda path, config, status: calls.append((path, config, status)) or {"ok": True}))
    import mb
    monkeypatch.delattr(mb, module, raising=False)
    assert run.run_post(post, tmp_path, cfg) == {"ok": True}
    assert calls[0][1] is cfg
    assert calls[0][2]["post_step"] == post and calls[0][2]["consumable"]
