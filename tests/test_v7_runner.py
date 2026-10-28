"""Real V7 orchestration with a deterministic NumPy engine double, never a model."""

import dataclasses
import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

from mb import chat, ledger, run, tasks, v7_run as v, v7_tasks as material
from mb.kv_geometry import bank_metadata, resolve_geometry
from mb.model_profiles import QWEN


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer(profile=QWEN.key)


def arm(name, variant="base"):
    return next(a for a in v.arms_for(variant) if a.arm_id == name)


def activate(runner, selected):
    runner.active_arm = selected
    runner._input_cache, runner._prefix_cache, runner._bank_cache = {}, {}, {}


def bare(tmp_path, tok, variant="base"):
    r = v.V7Runner.__new__(v.V7Runner)
    r.cfg = v.V7Config("v7_dev", variant, 2)
    r.run_dir, r.tok, r.notes = tmp_path, tok, {}
    r.all_episodes, r.episodes = r._stage_episodes(None)
    r.profile, r.template_hash = QWEN, "template"
    r.writer, r.pass_index = SimpleNamespace(path=tmp_path / "attempt-000"), 0
    activate(r, arm("orig_w2", variant))
    return r


def seed_notes(r):
    for selected in r.cfg.arm_configs():
        activate(r, selected)
        for ep in r.episodes:
            for role in tasks.ROLES:
                r.notes[r._note_key(ep, role)] = chat.encode(r.tok, f"Saved {role} note.")


@pytest.mark.parametrize("variant,arms,count", [("base", 14, 261), ("table", 5, 50), ("laptop", 5, 50)])
def test_exact_schedule_and_unique_identity(variant, arms, count):
    cfg = v.V7Config("v7_formal", variant, 12)
    selected = cfg.arm_configs()
    assert len(selected) == arms
    assert len({a.name for a in selected}) == len({a.config_hash("none", "none", "t") for a in selected}) == arms
    expected = v.expected_trials(cfg)
    assert len(expected) == len(set(expected)) == 12 * count
    assert all(k[2] == "A" for k in expected)
    assert {k[1].split("/")[-1] for k in expected if k[3] == "U_OPEN"} == (v.OPEN_ARMS if variant == "base" else set())
    if variant != "base":
        assert {a.arm_id for a in selected} == {"c0", "orig_w2", "trans_w2", "orig_w2_cf", "trans_w2_cf"}
    assert len(run.reflection_groups(selected)) == arms


@pytest.mark.parametrize("changes", [{"split": "old"}, {"variant": "unknown"}, {"n_episodes": 0},
    {"max_rows": True}, {"tag": "../bad"}, {"split": "v7_pilot", "n_episodes": 2},
    {"split": "v7_pilot", "n_episodes": 80, "variant": "table"}])
def test_invalid_config_rejected(changes):
    with pytest.raises(ValueError):
        v.V7Config(**(dict(split="v7_dev", variant="base", n_episodes=2) | changes))


def test_variants_paired_and_splits_disjoint():
    lists = [v.episodes_for(v.V7Config("v7_formal", name, 12)) for name in material.VARIANTS]
    assert [[(e.episode_id, e.base, e.fact_n, e.fact_n_cf) for e in eps] for eps in lists].count(
        [(e.episode_id, e.base, e.fact_n, e.fact_n_cf) for e in lists[0]]) == 3
    ids = [{e.episode_id for e in v.episodes_for(v.V7Config(split, "base", n))}
           for split, n in (("v7_dev", 12), ("v7_pilot", 80), ("v7_formal", 12))]
    assert not (ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2])


@pytest.mark.parametrize("variant", material.VARIANTS)
def test_counterfactual_is_only_B_and_question_labels_are_fixed(tmp_path, tok, variant):
    r = bare(tmp_path, tok, variant)
    seed_notes(r)
    ep = r.episodes[0]
    activate(r, arm("trans_w2", variant))
    a, b = r.prefix(ep, "A"), r.prefix(ep, "B")
    ka, kb = r._note_key(ep, "A"), r._note_key(ep, "B")
    original = r._pending_questions(r.active_arm, [ep], [ep], set(), set())
    activate(r, arm("trans_w2_cf", variant))
    assert r.prefix(ep, "A") == a and r.prefix(ep, "B") != b
    assert r._note_key(ep, "A") == ka and r._note_key(ep, "B") != kb
    assert r._pending_questions(r.active_arm, [ep], [ep], set(), set()) == [x for x in original if x[2].qid != "U_OPEN"]
    q = next(q for _, _, q in original if q.qid == "USE")
    ident, chash, mhash = r.arm_identity(r.active_arm)
    record = r._base_record(r.active_arm, ident, chash, mhash, ep, "A", q)
    assert record["v7"]["use_expected_meaning"] == "cf"
    assert record["v7"]["fact_shown"] == r.v7_episodes[ep.episode_id].fact_n_cf
    assert record["v7"]["card_sha256"]["A"] == hashlib.sha256(material.private_user_message(
        r.v7_episodes[ep.episode_id], "A").encode()).hexdigest()


def test_copy_A_is_exact_including_notes_spans_hashes_and_no_fact(tmp_path, tok):
    r = bare(tmp_path, tok)
    seed_notes(r)
    ep = r.episodes[0]
    activate(r, arm("same_trans_w2"))
    a, sa = r._prefix_parts(ep, "A")
    b, sb = r._prefix_parts(ep, "B")
    assert a == b and a is not b and sa == sb
    assert r._note_key(ep, "A") == r._note_key(ep, "B")
    q = material.make_question(tok, r.v7_episodes[ep.episode_id], "A", "USE", 0)
    record = r._base_record(r.active_arm, *r.arm_identity(r.active_arm), ep, "A", q)
    meta = record["v7"]
    assert meta["card_sha256"]["A"] == meta["card_sha256"]["B"]
    assert meta["banks"]["A"] == meta["banks"]["B"]
    assert meta["fact_holder"] == "none" and meta["fact_shown"] is None and meta["use_expected_meaning"] is None
    assert meta["input_sources"] == {"A": "A", "B": "A"}
    assert resolve_geometry(meta["banks"]["A"], meta["banks"]["B"], "before_own")["delta"] == -len(b)


def test_fullinfo_third_person_and_all_prefix_regions(tmp_path, tok):
    r = bare(tmp_path, tok)
    seed_notes(r)
    ep = r.episodes[0]
    v7 = r.v7_episodes[ep.episode_id]
    activate(r, arm("orig_w2"))
    original_a, original_b = r.prefix(ep, "A"), r.prefix(ep, "B")
    activate(r, arm("c0_fullinfo"))
    assert f"${v7.fact_n} surcharge" in tok.decode(r.prefix(ep, "A"))
    assert f"${v7.fact_n} surcharge" not in tok.decode(r.prefix(ep, "B"))
    activate(r, arm("third_trans_w2"))
    assert r.prefix(ep, "A") == original_a and r.prefix(ep, "B") != original_b
    ids, spans = r._prefix_parts(ep, "B")
    byname = {name: (lo, hi) for name, lo, hi in spans}
    assert {"first_token", "system_turn", "note", "closure", "prompt"} <= byname.keys()
    note = tok.decode(ids[slice(*byname["note"])])
    assert note == tasks.note_opener(ep, "B", "third_strict") + tok.decode(r.notes[r._note_key(ep, "B")])
    assert ids[slice(*byname["closure"])] == chat.close(tok)
    assert ids[slice(*byname["prompt"])] == v.reflection_ids(tok, v7, "B", "third_strict")
    assert byname["note"][1] == byname["closure"][0] and byname["closure"][1] == byname["prompt"][0]
    assert byname["prompt"][1] == len(ids)
    q = material.make_question(tok, v7, "A", "START", 0)
    meta = r._base_record(r.active_arm, *r.arm_identity(r.active_arm), ep, "A", q)["v7"]
    assert meta["card_sha256"]["B"] == hashlib.sha256(material.private_user_message(
        v7, "B", frame="third_strict").encode()).hexdigest()
    assert meta["card_sha256"]["B"] != material.record_metadata(v7, "A", q)["card_sha256"]["B"]
    activate(r, arm("orig_w2"))
    r.notes[r._note_key(ep, "A")] = []
    _, spans = r._prefix_parts(ep, "A")
    assert next(hi - lo for name, lo, hi in spans if name == "note") == 0


class Array(np.ndarray):
    def __new__(cls, value, dtype=None):
        return np.asarray(value, dtype=dtype).view(cls)

    def cpu(self):
        return self

    def numpy(self):
        return np.asarray(self)


@dataclasses.dataclass
class FakeState:
    prefixes: list
    banks: list

    def consumed_matrix(self):
        return Array([[100, 101]] * len(self.prefixes))


class FakeEngine:
    calls = []
    fail_once = False
    fail_always = False
    note_calls = 0

    def __init__(self, model, tok, layer, cal):
        self.tok, self.cal, self.device, self.d = tok, None, "cpu", QWEN.hidden_size

    def generate_notes(self, prefixes, max_new):
        type(self).note_calls += len(prefixes)
        return [chat.encode(self.tok, f"Saved note {sum(ids) % 9}.") for ids in prefixes]

    def prefill(self, prefixes, attention_spans=None):
        spans = attention_spans or [[("P", 0, len(ids))] for ids in prefixes]
        self.calls.append((prefixes, spans))
        return FakeState(prefixes, [bank_metadata(ids, s) for ids, s in zip(prefixes, spans)])

    def run_reflection(self, state, plan, write=True):
        self.calls.append((plan.arm.arm_id, write))
        n = len(state.prefixes)
        values = {"inj_ratio": Array(np.zeros((n, 2))), "unmatched": Array(np.zeros((n, 2), dtype=bool))}
        if plan.arm.kv_log_spans:
            values["kv_geometry"] = [resolve_geometry(state.banks[i], state.banks[i ^ 1], plan.arm.kv_position)
                                     if i % 2 == 0 else None for i in range(n)]
        return values

    def run_readout(self, state, rows, suffixes, selected, rules, generate=0, mask_idx=None):
        if type(self).fail_always or type(self).fail_once:
            type(self).fail_once = False
            raise RuntimeError("synthetic readout failure")
        n, ticks = len(rows), suffixes.shape[1]
        out = {"label_logits": Array(np.zeros((n, 4))), "label_logprobs": Array(np.full((n, 4), -1.4)),
               "label_mass": Array(np.full(n, .98)),
               "generated": Array(np.full((n, generate), 100, dtype=int))}
        out.update({key: Array(np.full((n, ticks), fill)) for key, fill in run.TICK_ARRAYS})
        if selected.kv_log_spans:
            geometry = [resolve_geometry(state.banks[p * 2], state.banks[p * 2 + 1], selected.kv_position) for p, _ in rows]
            out["kv_geometry"] = geometry
            out["r_kv_span_mass"] = Array(np.zeros((n, ticks, 2, 2, len(geometry[0]["spans"]))))
            out["r_kv_bank_mass"] = Array(np.zeros((n, ticks, 2, 2, 2)))
            out["r_kv_query_pos"] = Array(np.tile(np.arange(ticks), (n, 1)))
        return out

    def close(self):
        pass


@pytest.fixture
def fake_model(monkeypatch):
    FakeEngine.calls, FakeEngine.fail_once, FakeEngine.fail_always, FakeEngine.note_calls = [], False, False, 0
    torch = SimpleNamespace(tensor=lambda x, dtype=None: Array(x, dtype), long=np.int64, isfinite=np.isfinite,
                            cuda=SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "mb.runtime", SimpleNamespace(U_OPEN_TOKENS=80,
        make_plan=lambda selected, *args, **kwargs: SimpleNamespace(arm=selected)))
    return SimpleNamespace(config=SimpleNamespace(hidden_size=QWEN.hidden_size))


def prepared(tmp_path, tok, monkeypatch, variant="base"):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    cfg = v.V7Config("v7_dev", variant, 1, episodes_per_batch=1, max_rows=4)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg.resolved()))
    return cfg, path, v.prepare_run(cfg, path, tok=tok)


def collector(cfg, prep, tok, fake_model):
    r = v.V7Runner(cfg, prep.run_dir, None, prep.identity, {}, {}, lambda line: None,
                   model=fake_model, tok=tok, engine_cls=FakeEngine)
    r.register_arms(cfg.arm_configs())
    return r


@pytest.mark.parametrize("variant", material.VARIANTS)
def test_full_dispatch_serialization_retry_and_completed_resume(tmp_path, tok, monkeypatch, fake_model, variant):
    cfg, path, prep = prepared(tmp_path, tok, monkeypatch, variant)
    FakeEngine.fail_once = True
    r = collector(cfg, prep, tok, fake_model)
    try:
        r.run_arms(cfg.arm_configs())
    finally:
        r.close()
    records = ledger.load_records(prep.run_dir).records
    assert any(rec["status"] == "failed" for rec in records)
    assert ledger.done_keys(records) == set(v.expected_trials(cfg))
    assert len({rec["c48_snapshot_key"] for rec in records if "c48_snapshot_key" in rec}) == len(cfg.arm_configs())
    comp = v.run_completeness(prep.run_dir)
    assert comp["status"] == "complete" and comp["smoke"] and not comp["consumable"]
    for rec in records:
        if rec["status"] == "ok" and rec["arm_id"].startswith("trans"):
            assert rec["kv_condition_identity"]["delta"] == -rec["v7"]["banks"]["B"]["length"]
            assert rec["r_kv_condition_identity"] == rec["kv_condition_identity"]
    for archive in (prep.run_dir / "ticks").glob("R*.npz"):
        with np.load(archive, allow_pickle=False) as arrays:
            if "kv_geometry_json" in arrays:
                assert len(arrays["kv_geometry_json"]) == len(arrays["trial_keys"])
                assert json.loads(arrays["kv_geometry_json"][0])["spans"]
    if variant == "base":
        modes = [x for x in FakeEngine.calls if isinstance(x[0], str)]
        assert ("orig_w2_ro", False) in modes and ("trans_w2_ro", False) in modes
        assert ("orig_w2", True) in modes
    old = {p: p.read_bytes() for p in prep.run_dir.rglob("*") if p.is_file()}
    calls = len(FakeEngine.calls)
    resumed = v.prepare_run(cfg, path, resume=prep.run_dir, tok=tok)
    r = collector(cfg, resumed, tok, fake_model)
    try:
        r.run_arms(cfg.arm_configs())
    finally:
        r.close()
    assert len(FakeEngine.calls) == calls
    assert all(p.read_bytes() == contents for p, contents in old.items())
    assert len(list((prep.run_dir / "records").glob("attempt-*.jsonl"))) == 2


def test_persistent_failures_retry_once_and_remain_missing(tmp_path, tok, monkeypatch, fake_model):
    cfg, _, prep = prepared(tmp_path, tok, monkeypatch, "table")
    FakeEngine.fail_always = True
    r = collector(cfg, prep, tok, fake_model)
    try:
        r.run_arms(cfg.arm_configs())
    finally:
        r.close()
    records = ledger.load_records(prep.run_dir).records
    assert len(records) == 2 * len(v.expected_trials(cfg))
    assert {rec["pass"] for rec in records} == {0, 1}
    assert all(rec["status"] == "failed" and "label_logits" not in rec for rec in records)
    assert v.run_completeness(prep.run_dir)["n_ok"] == 0


@pytest.mark.parametrize("field,value", [("seed", 1), ("variant", "table"), ("n_episodes", 2), ("max_rows", 8)])
def test_resume_refuses_changes_before_any_write(tmp_path, tok, monkeypatch, field, value):
    cfg, path, prep = prepared(tmp_path, tok, monkeypatch)
    before = {p: p.read_bytes() for p in prep.run_dir.rglob("*") if p.is_file()}
    cfg = dataclasses.replace(cfg, **{field: value})
    path.write_text(yaml.safe_dump(cfg.resolved()))
    with pytest.raises(SystemExit, match="resume refused"):
        v.prepare_run(cfg, path, resume=prep.run_dir, tok=tok)
    assert {p: p.read_bytes() for p in prep.run_dir.rglob("*") if p.is_file()} == before


def test_source_override_is_explicit_and_material_change_still_refused(tmp_path, tok, monkeypatch):
    cfg, path, prep = prepared(tmp_path, tok, monkeypatch)
    monkeypatch.setattr(run, "source_hash", lambda: "changed-source")
    with pytest.raises(SystemExit, match="source_hash"):
        v.prepare_run(cfg, path, resume=prep.run_dir, tok=tok)
    v.prepare_run(cfg, path, resume=prep.run_dir, allow_code_change=True, tok=tok)
    assert json.loads((prep.run_dir / "resume_log.jsonl").read_text())["allow_code_change"]
    original = material.private_prefix_ids
    monkeypatch.setattr(material, "private_prefix_ids", lambda *args, **kw: [*original(*args, **kw), 123])
    with pytest.raises(SystemExit, match="template_hash"):
        v.prepare_run(cfg, path, resume=prep.run_dir, allow_code_change=True, tok=tok)


def test_append_only_note_recovery_and_conflict_detection(tmp_path, tok):
    r = bare(tmp_path, tok)
    fake = FakeEngine(None, tok, 18, None)
    ep = r.episodes[0]
    r.ensure_notes(fake, [(ep, "A"), (ep, "B")])
    path = tmp_path / "notes.jsonl"
    valid = path.read_bytes()
    with path.open("a") as stream:
        stream.write('{"interrupted":')
    activate(r, arm("trans_w2_cf"))
    r.ensure_notes(fake, [(ep, "A"), (ep, "B")])
    assert path.read_bytes().startswith(valid + b'{"interrupted":')
    assert len(v._check_notes(path)) == 3
    r.notes.clear()
    r._load_notes()
    before = path.read_bytes()
    r.ensure_notes(fake, [(ep, "A"), (ep, "B")])
    assert path.read_bytes() == before
    record = v._check_notes(path)[0]
    record["ids"] = [999]
    record["n_tokens"] = 1
    record["ids_sha256"] = ledger.canonical_hash(record["ids"], 64)
    v._append(path, record)
    with pytest.raises(ValueError, match="conflicting"):
        v._check_notes(path)


def test_cli_is_offline_by_default_and_execution_requires_approval(tmp_path, monkeypatch, capsys):
    cfg = v.V7Config("v7_dev", "base", 12)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg.resolved()))
    monkeypatch.setattr(v, "prepare_run", lambda *a, **kw: pytest.fail("offline CLI must not create a run"))
    assert v.main([str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["execution"] is False
    with pytest.raises(ValueError, match="approved"):
        v.main([str(path), "--execute"])
    with pytest.raises(ValueError, match="12..24"):
        v.validate_launch(cfg, path, ledger.file_sha256(v.PROTOCOL), 1)
    with pytest.raises(ValueError, match="protocol-v7"):
        v.validate_launch(dataclasses.replace(cfg, split="v7_formal"), path, ledger.file_sha256(v.PROTOCOL), None)
    v.validate_launch(cfg, path, ledger.file_sha256(v.PROTOCOL), None)


def test_note_identity_contains_effective_material_factors(tmp_path, tok):
    r = bare(tmp_path, tok)
    ep = r.episodes[0]
    keys = []
    for name in ("orig_w2", "orig_w2_cf", "third_orig_w2", "c0_fullinfo"):
        activate(r, arm(name))
        context = r._context(ep, "B")[-1]
        assert {"variant", "fact_holder", "counterfactual_fact", "frame", "private_prefix_sha256"} <= context.keys()
        keys.append(r._note_key(ep, "B"))
    assert len(set(keys)) == 4
    other = bare(tmp_path, tok, "table")
    assert other._note_key(other.episodes[0], "B") not in keys


@pytest.mark.parametrize("damage", ["unknown_trial", "missing_hash", "snapshot", "note"])
def test_corrupt_resume_is_rejected_before_any_write(tmp_path, tok, monkeypatch, damage):
    cfg, path, prep = prepared(tmp_path, tok, monkeypatch)
    if damage in ("unknown_trial", "missing_hash"):
        key = v.expected_trials(cfg)[0]
        record = dict(zip(("episode_id", "arm", "recipient", "qid", "rotation_id"), key))
        record["status"] = "ok"
        if damage == "unknown_trial":
            record["qid"] = "UNREGISTERED"
        writer = ledger.ShardWriter(prep.run_dir)
        writer.write(record)
        writer.close()
    elif damage == "snapshot":
        v._append(prep.run_dir / "snapshots.jsonl", {"key": "same", "sha256": "a"})
        v._append(prep.run_dir / "snapshots.jsonl", {"key": "same", "sha256": "b"})
    else:
        (prep.run_dir / "notes.jsonl").write_text('{}\n')
    before = {p: p.read_bytes() for p in prep.run_dir.rglob("*") if p.is_file()}
    with pytest.raises((SystemExit, ValueError)):
        v.prepare_run(cfg, path, resume=prep.run_dir, tok=tok)
    assert {p: p.read_bytes() for p in prep.run_dir.rglob("*") if p.is_file()} == before


def test_unicode_crash_tail_recovery_preserves_bytes_and_rejects_body_corruption(tmp_path):
    path = tmp_path / "notes.jsonl"
    original = b'{"valid": true}\n{"text": "\xe4\xb8'
    path.write_bytes(original)
    assert v._read_jsonl(path) == [{"valid": True}]
    v._append(path, {"next": True})
    assert path.read_bytes().startswith(original)
    assert v._read_jsonl(path) == [{"valid": True}, {"next": True}]
    path.write_bytes(b'{bad}\n{"valid": true}\n')
    with pytest.raises(ValueError, match="corrupt JSONL body"):
        v._read_jsonl(path)


def test_partial_resume_reuses_notes_and_runs_only_missing_trials(tmp_path, tok, monkeypatch, fake_model):
    cfg, path, prep = prepared(tmp_path, tok, monkeypatch, "table")
    r = collector(cfg, prep, tok, fake_model)
    try:
        r.run_arms(cfg.arm_configs()[:1])
    finally:
        r.close()
    prior_keys = ledger.done_keys(ledger.load_records(prep.run_dir).records)
    prior_notes = FakeEngine.note_calls
    shard = prep.run_dir / "records/attempt-000.jsonl"
    original = shard.read_bytes()
    resumed = v.prepare_run(cfg, path, resume=prep.run_dir, tok=tok)
    r = collector(cfg, resumed, tok, fake_model)
    try:
        r.run_arms(cfg.arm_configs())
        assert not (prior_keys & {ledger.trial_key(rec) for rec in r.new_records})
    finally:
        r.close()
    assert shard.read_bytes() == original and v.run_completeness(prep.run_dir)["status"] == "complete"
    # C0 generated both original notes; only the counterfactual B note is new.
    assert FakeEngine.note_calls == prior_notes + 1


def test_note_failure_is_recorded_and_retryable(tmp_path, tok, monkeypatch, fake_model):
    cfg, _, prep = prepared(tmp_path, tok, monkeypatch, "table")
    original = FakeEngine.generate_notes
    count = 0

    def failing_once(self, prefixes, max_new):
        nonlocal count
        count += 1
        if count == 1:
            raise RuntimeError("synthetic note failure")
        return original(self, prefixes, max_new)

    monkeypatch.setattr(FakeEngine, "generate_notes", failing_once)
    r = collector(cfg, prep, tok, fake_model)
    try:
        r.run_arms(cfg.arm_configs())
    finally:
        r.close()
    records = ledger.load_records(prep.run_dir).records
    failed = [rec for rec in records if rec["status"] == "failed"]
    assert failed and all(rec["v7"]["banks"] == {"A": None, "B": None} for rec in failed)
    assert v.run_completeness(prep.run_dir)["status"] == "complete"
