"""Runner wiring with a fake engine on CPU (review M2 B1/B2/I3/I8, test suggestions 1 and 9).

Needs torch but no GPU or model weights; runs in the ``not gpu`` suite on the GPU machine.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

from mb import chat, ledger, run, tasks  # noqa: E402

D = 16
TICKS = 48
PREFIX_LEN = 273


class FakeCal:
    layer = 18

    def hash(self):
        return "fakecal"


class FakeState:
    def __init__(self, sequences):
        self.seqs = sequences
        self.rows, self.phase, self.tick = len(sequences), "C", TICKS

    def consumed_matrix(self):
        return torch.full((self.rows, TICKS), 1000, dtype=torch.long)


class FakeEngine:
    """Records what it was asked to do; failure modes are switched by class attributes."""

    nan_target: tuple | None = None  # (recipient prefix head, suffix) whose readout returns NaN ...
    nan_budget = 0  # ... this many times, then succeeds
    fail_reflection = False
    prefixes: list[list[list[int]]] = []

    def __init__(self, model, tok, layer, cal):
        self.cal, self.layer = cal, layer
        self.device = torch.device("cpu")
        self.d = D

    def generate_notes(self, prefixes, max_new=48):
        return [[1001, 1002] for _ in prefixes]

    def prefill(self, sequences):
        FakeEngine.prefixes.append(sequences)
        return FakeState(sequences)

    def run_reflection(self, state, plan, ticks=TICKS, write=True):
        if FakeEngine.fail_reflection:
            raise RuntimeError("boom in C")
        rows = state.rows
        return {"tokens": torch.zeros(rows, ticks, dtype=torch.long), "inj_ratio": torch.zeros(rows, ticks),
                "msg_norm": torch.ones(rows, ticks), "unmatched": torch.zeros(rows, ticks, dtype=torch.bool),
                "energy_ratio": torch.full((rows, ticks), float("nan")), "cos_pair": torch.zeros(rows // 2, ticks)}

    def run_readout(self, snapshot, branches, suffixes, arm, static_rules, generate=0, mask_idx=None):
        n, length = suffixes.shape
        logits = torch.tensor([[3.0, 1.0, 0.0, -1.0]]).repeat(n, 1)
        for j, (p, role) in enumerate(branches):
            head = tuple(snapshot.seqs[2 * p + (0 if role == "A" else 1)][:PREFIX_LEN])
            if FakeEngine.nan_budget > 0 and (head, tuple(suffixes[j].tolist())) == FakeEngine.nan_target:
                logits[j, 0] = float("nan")
                FakeEngine.nan_budget -= 1
        out = {"label_logits": logits, "label_logprobs": torch.log_softmax(logits, -1),
               "label_mass": torch.full((n,), 0.99)}
        if arm.readout_mode in ("FULL", "RO") and arm.direction != "none":
            out.update(r_inj_ratio=torch.full((n, length), 0.1), r_unmatched=torch.zeros(n, length, dtype=torch.bool),
                       r_energy_ratio=torch.full((n, length), float("nan")),
                       r_donor_tokens=torch.zeros(n, length, dtype=torch.long),
                       r_inj_ratio_mean=torch.full((n,), 0.1), r_unmatched_ticks=torch.zeros(n, dtype=torch.long))
        if generate:
            out["generated"] = torch.full((n, generate), 1003, dtype=torch.long)
        return out

    def close(self):
        pass


@pytest.fixture(autouse=True)
def reset_fake():
    FakeEngine.nan_target, FakeEngine.nan_budget, FakeEngine.fail_reflection = None, 0, False
    FakeEngine.prefixes = []


def _nan_on(tok, ep, qid="START", budget=1):
    q = tasks.make_question(tok, ep, "A", qid, ep.rotations[0])
    FakeEngine.nan_target = (tuple(tasks.private_prefix_ids(tok, ep, "A")), tuple(q.suffix_ids))
    FakeEngine.nan_budget = budget


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer()


@pytest.fixture()
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("MB_DATA_ROOT", str(tmp_path))
    return tmp_path


def _make(data_root, tok, arms, qids=("START", "START_R", "U_OPEN"), n=3, limit=None, cal=False):
    cfg = run.StageConfig(stage="unit", tag="t", split="unit", n_episodes=n, arms=arms, qids=list(qids),
                          episodes_per_batch=2)
    run_dir = data_root / "results" / "r"
    run_dir.mkdir(parents=True, exist_ok=True)
    ident_path = run_dir / "identity.json"
    identity = run.build_identity(cfg, limit, "tmpl", {})
    if not ident_path.exists():
        ident_path.write_text(json.dumps(identity))
        (run_dir / "manifest.json").write_text(json.dumps({"smoke": limit is not None}))
    cal_map = {18: FakeCal()} if cal else {}
    runner = run.Runner(cfg, run_dir, limit, identity, cal_map, {}, lambda msg: None,
                        model=SimpleNamespace(config=SimpleNamespace(hidden_size=D)), tok=tok, engine_cls=FakeEngine)
    return cfg, runner


def _go(runner, cfg):
    arms = cfg.arm_configs()
    runner.register_arms(arms)
    runner.run_arms(arms)
    runner.close()
    return run.run_completeness(runner.run_dir)


def test_complete_run_then_resume_is_a_noop(data_root, tok):
    cfg, runner = _make(data_root, tok, [{"condition": "C0", "recipients": ["A", "B"]}])
    comp = _go(runner, cfg)
    assert comp["status"] == "complete" and comp["n_ok"] == 3 * 2 * (2 + 2 + 1)
    recs = ledger.load_records(runner.run_dir).records
    u_open = [r for r in recs if r["qid"] == "U_OPEN"]
    assert u_open and all(len(r["generated_ids"]) == 80 for r in u_open)
    assert all(r["attempt"] == "attempt-000" and r["pass"] == 0 for r in recs)
    n_prefill = len(FakeEngine.prefixes)
    cfg2, runner2 = _make(data_root, tok, [{"condition": "C0", "recipients": ["A", "B"]}])
    comp2 = _go(runner2, cfg2)
    assert comp2["status"] == "complete"
    assert len(ledger.load_records(runner.run_dir).records) == len(recs)  # nothing re-run
    assert len(FakeEngine.prefixes) == n_prefill  # no model work at all


def test_nan_readout_is_failed_then_retried(data_root, tok):
    cfg, runner = _make(data_root, tok, [{"condition": "C0"}])
    _nan_on(tok, runner.episodes[0], budget=1)
    comp = _go(runner, cfg)
    recs = ledger.load_records(runner.run_dir).records
    failed = [r for r in recs if r["status"] == "failed"]
    assert len(failed) == 1 and failed[0]["pass"] == 0 and failed[0]["label_logits"][0] is None
    retried = [r for r in recs if ledger.trial_key(r) == ledger.trial_key(failed[0]) and r["status"] == "ok"]
    assert len(retried) == 1 and retried[0]["pass"] == 1
    assert comp["status"] == "complete"


def test_persistent_nan_leaves_run_incomplete(data_root, tok):
    cfg, runner = _make(data_root, tok, [{"condition": "C0"}])
    _nan_on(tok, runner.episodes[0], budget=99)
    comp = _go(runner, cfg)
    assert comp["status"] == "incomplete" and comp["n_missing"] == 1


def test_reflection_failure_writes_failed_records(data_root, tok):
    cfg, runner = _make(data_root, tok, [{"condition": "C0"}])
    FakeEngine.fail_reflection = True
    comp = _go(runner, cfg)
    recs = ledger.load_records(runner.run_dir).records
    assert recs and all(r["status"] == "failed" and "boom in C" in r["failure_reason"] for r in recs)
    assert comp["status"] == "incomplete" and comp["n_ok"] == 0
    # Both passes tried; each expected trial has two failed audit records.
    assert len(recs) == 2 * comp["n_expected"]


def test_conflicting_hash_refuses_resume(data_root, tok):
    cfg, runner = _make(data_root, tok, [{"condition": "C0"}])
    _go(runner, cfg)
    shard = ledger.shard_paths(runner.run_dir)[0]
    lines = shard.read_text().splitlines()
    first = json.loads(lines[0])
    first["config_hash"] = "someone-else"
    shard.write_text("\n".join([json.dumps(first), *lines[1:]]) + "\n")
    _, runner2 = _make(data_root, tok, [{"condition": "C0"}])
    with pytest.raises(SystemExit, match="other config hashes"):
        runner2.register_arms(cfg.arm_configs())
    runner2.close()


def test_mismatch_donor_does_not_depend_on_limit(data_root, tok):
    arms = [{"condition": "MISMATCH", "gain": 0.3}]
    cfg, runner = _make(data_root, tok, arms, n=4, limit=1, cal=True)
    comp = _go(runner, cfg)
    assert comp["status"] == "complete"
    recs = ledger.load_records(runner.run_dir).records
    full_ids = [e.episode_id for e in tasks.make_episodes(4, "unit", 0)]
    assert {r["mismatch_scenario_from"] for r in recs} == {full_ids[1]}
    assert json.loads((runner.run_dir / "mismatch_donors.json").read_text())[full_ids[0]] == full_ids[1]
    # A's inputs are unchanged; only B's prefix carries the other episode's scenario.
    a_prefix, b_prefix = FakeEngine.prefixes[-1][0], FakeEngine.prefixes[-1][1]
    ep0 = runner.episodes[0]
    assert a_prefix[:273] == tasks.private_prefix_ids(tok, ep0, "A")
    donor = tasks.make_donor_variant(ep0, "MISMATCH", tasks.make_episodes(4, "unit", 0)[1]).donor_episode
    assert b_prefix[:273] == tasks.private_prefix_ids(tok, donor, "B")
    # R tick logs were saved for the bridged arm.
    assert list((runner.run_dir / "ticks").glob("R__*.npz"))


def test_cf_keeps_recipient_tokens_and_records_fixed_candidates(data_root, tok):
    cfg, runner = _make(data_root, tok, [{"condition": "CF", "gain": 0.3}], qids=("ACC_RULE",), n=2, cal=True)
    _go(runner, cfg)
    recs = ledger.load_records(runner.run_dir).records
    eps = {e.episode_id: e for e in runner.episodes}
    for r in recs:
        ep = eps[r["episode_id"]]
        plain = tasks.make_question(tok, ep, "A", "ACC_RULE", r["rotation_id"])
        assert r["text_hash"] == plain.text_hash  # recipient question unchanged
        assert (r["cf_r0_rule"], r["cf_r1_rule"]) == (ep.rule.B, ep.rule.spare)
        assert r["donor_rule"] == ep.rule.spare
        assert r["label_meaning"][r["options"].index(ep.rule.spare)] == "partner"


def test_lang_source_is_c0_reflection_of_b(data_root, tok):
    cfg, runner = _make(data_root, tok, [{"condition": "LANG_TAG"}, {"condition": "LANG_UNTAG"}],
                        qids=("START",), n=2)
    _go(runner, cfg)
    lang = [json.loads(line) for line in (runner.run_dir / "lang.jsonl").read_text().splitlines()]
    assert len(lang) == 2 and all(len(x["ids"]) == TICKS for x in lang)
    recs = ledger.load_records(runner.run_dir).records
    by_ep = {}
    for r in recs:
        by_ep.setdefault(r["episode_id"], set()).add(r["lang_source_sha"])
    assert all(len(v) == 1 for v in by_ep.values())  # tag/untag use the same source tokens


def test_calibration_file_validation(tmp_path):
    """Review I5: wrong layer, other prefix identity, smoke or non-finite files are rejected."""
    from mb.bridge import LayerCalibration
    from mb.conditions import MODEL_REVISION

    current = {"model_revision": MODEL_REVISION, "prefix_hash": "p"}

    def save(name, cal, **meta):
        blob = cal.state_dict()
        blob["meta"] = {"model_revision": MODEL_REVISION, "prefix_hash": "p", "smoke": False, **meta}
        torch.save(blob, tmp_path / name)
        return str(tmp_path / name)

    cal = LayerCalibration(18, torch.zeros(2560), torch.ones(2560), 1.0, {"raw:cost": torch.ones(2560)})
    good = save("good.pt", cal)
    loaded, meta = run.load_calibration(good, 18, current, allow_smoke=False)
    assert loaded.hash() == cal.hash() and meta["smoke"] is False
    with pytest.raises(SystemExit, match="layer"):
        run.load_calibration(good, 12, current, allow_smoke=False)
    with pytest.raises(SystemExit, match="prefix_hash"):
        run.load_calibration(good, 18, {**current, "prefix_hash": "q"}, allow_smoke=False)
    smoke = save("smoke.pt", cal, smoke=True)
    with pytest.raises(SystemExit, match="smoke"):
        run.load_calibration(smoke, 18, current, allow_smoke=False)
    run.load_calibration(smoke, 18, current, allow_smoke=True)
    nan = save("nan.pt", LayerCalibration(18, torch.full((2560,), float("nan")), torch.ones(2560), 1.0))
    with pytest.raises(SystemExit, match="non-finite"):
        run.load_calibration(nan, 18, current, allow_smoke=False)
    short = save("short.pt", LayerCalibration(18, torch.zeros(16), torch.ones(16), 1.0))
    with pytest.raises(SystemExit, match="shape"):
        run.load_calibration(short, 18, current, allow_smoke=False)


def test_third_person_frame_rewrites_only_the_donor(data_root, tok):
    arms = [{"condition": "ONE", "interface": "kv", "kv_scope": "P", "gain": 2.0, "partner_frame": "third"}]
    cfg, runner = _make(data_root, tok, arms, qids=("START",), n=2)
    _go(runner, cfg)
    a_prefix, b_prefix = FakeEngine.prefixes[-1][0], FakeEngine.prefixes[-1][1]
    ep0 = runner.episodes[0]
    assert a_prefix[:273] == tasks.private_prefix_ids(tok, ep0, "A")  # A unchanged (second person)
    third = tasks.private_prefix_ids(tok, ep0, "B", frame="third")
    assert b_prefix[:len(third)] == third
    assert "You were assigned" not in tok.decode(b_prefix[:len(third)])


def test_strict_third_person_frame_forces_the_note_opener(data_root, tok):
    """T3b: the donor's note starts with fixed third-person words; only the continuation is generated."""
    arms = [{"condition": "ONE", "interface": "kv", "kv_scope": "P", "gain": 1.0, "partner_frame": "third_strict"}]
    cfg, runner = _make(data_root, tok, arms, qids=("START",), n=2)
    _go(runner, cfg)
    b_prefix = FakeEngine.prefixes[-1][1]
    ep0 = runner.episodes[0]
    head = tasks.private_prefix_ids(tok, ep0, "B", frame="third_strict")
    opener = chat.encode(tok, f"Participant {ep0.codename['B']} chooses")
    assert head[-len(opener):] == opener
    assert b_prefix[:len(head) + 2] == head + [1001, 1002]  # the fake engine's note follows the opener
    logged = [json.loads(line) for line in (runner.run_dir / "notes.jsonl").read_text().splitlines()]
    strict = [r for r in logged if r["role"] == "B"]
    assert strict and all(r["opener"].startswith("Participant ") for r in strict)
    assert all("opener" not in r for r in logged if r["role"] == "A")
