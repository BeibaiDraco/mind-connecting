from dataclasses import replace

import pytest

from mb.v6_contract import RuntimeSpec
from mb.v6_runtime import EpisodeRunner, PairState
from mb.v6_run import SyntheticBackend
from mb.v6_tasks import make_episodes


@pytest.fixture
def ep():
    return make_episodes(1, stage="development", seed=731)[0]


def runner(**kwargs):
    return EpisodeRunner(SyntheticBackend(), RuntimeSpec(work_tokens=4,
                         preparation_tokens=2, window=2), "synthetic", **kwargs)


def test_complete_episode_and_role_order_invariance(ep):
    first, second = runner(), runner(side_order=(1, 0))
    left = first.run_episode(ep, text_reference=True)
    right = second.run_episode(ep, text_reference=True)
    assert left == right
    assert len(left) == 352
    assert sum(r["kind"] == "natural" for r in left) == 120
    assert sum(r["kind"] == "pulse" for r in left) == 64
    assert sum(r["kind"] == "goal" for r in left) == 144
    # Four shortened ticks per 80 work periods, including FRESH shadows.
    assert len(first.audit) == 320


def test_only_committed_current_round_exports_are_visible(ep):
    run = runner()
    pair = run.initialize(ep)
    run.prepare(ep, pair, 1)
    tape, held = run.work(pair, "LIVE")
    for tick, audit in enumerate(run.audit):
        assert [len(x) for x in audit["incoming"]] == [min(tick, 2)]*2
        for side in (0, 1):
            assert audit["incoming"][side] == [x.identity() for x in tape.entries[1-side][max(0,tick-2):tick]]
    assert held == (tape.entries[1][-2:], tape.entries[0][-2:])
    run.actions(ep, pair, held, {"kind": "natural", "policy": "LIVE", "checkpoint": 0,
                                "arm": "LIVE", "version": 1})
    previous = {x.digest for side in tape.entries for x in side}
    run.prepare(ep, pair, 2)
    assert pair.windows == ((), ())
    next_tape, _ = run.work(pair, "LIVE")
    assert not previous.intersection(x.digest for side in next_tape.entries for x in side)


def test_fresh_shadow_does_not_enter_actual_history(ep):
    run = runner()
    pair = run.initialize(ep)
    run.prepare(ep, pair, 1)
    before = [len(s["history"]) for s in pair.models]
    _, held = run.work(pair, "FRESH")
    assert [len(s["history"])-n for s,n in zip(pair.models,before)] == [4,4]
    assert [len(w) for w in held] == [2,2]
    assert len(run.audit) == 8  # Four shadow and four actual ticks.


def test_wrong_round_replay_refused(ep):
    run = runner()
    pair = run.initialize(ep)
    run.prepare(ep, pair, 1)
    tape, _ = run.work(run.clone(pair), "LIVE")
    with pytest.raises(ValueError, match="exact round"):
        run.work(pair, "Replay", tape=replace(tape, round_id=2), focal=0)


def test_invalid_outputs_remain_failures_and_actual_history(ep):
    run = EpisodeRunner(SyntheticBackend(invalid_every=1), runner().spec, "synthetic")
    checkpoints = run.natural(ep, "LIVE")
    actions = [r for r in run.records if r["qid"] == "action"]
    assert all(r["choice"] is None and r["correct"] is False for r in actions)
    assert checkpoints[3].world.actions == ((None,None), (None,None))
    for state in checkpoints[3].models:
        answers = [x for x in state["history"] if x[0] == "actual_answer"]
        assert [x[1] for x in answers] == [999,999]


def test_zero_gain_policy_actions_agree(ep):
    run = EpisodeRunner(SyntheticBackend(), replace(runner().spec, gain=0), "synthetic")
    run.natural(ep, "LIVE")
    first = [(r["round_id"],r["side"],r["qid"],r["choice"]) for r in run.records]
    run.records = []
    run.natural(ep, "OFF")
    assert first == [(r["round_id"],r["side"],r["qid"],r["choice"]) for r in run.records]


def test_mutating_measurement_backend_rejected(ep):
    class BadBackend(SyntheticBackend):
        def probe(self, state, *args, **kwargs):
            state["history"].append(("leak",))
            return super().probe(state, *args, **kwargs)
    run = EpisodeRunner(BadBackend(), runner().spec, "synthetic")
    with pytest.raises(RuntimeError, match="Readout mutated"):
        run.natural(ep, "LIVE")


def test_all_diagnostic_branches_preserve_parent(ep):
    run = runner()
    checkpoints = run.natural(ep, "LIVE")
    before = {k:run.digest(v) for k,v in checkpoints.items()}
    for k in (2,5):
        run.pulses(ep, checkpoints[k], k)
    for k in (3,6):
        run.goals(ep, checkpoints[k], k)
    assert before == {k:run.digest(v) for k,v in checkpoints.items()}


def test_no_formal_status_can_be_constructed():
    with pytest.raises(ValueError, match="no authorized formal"):
        RuntimeSpec(status="formal")


def test_changed_live_pulse_reproduces_natural_continuation(ep):
    run = runner()
    records = run.run_episode(ep)
    natural = {(r["round_id"],r["side"]):r for r in records
               if r["kind"] == "natural" and r["policy"] == "LIVE" and r["qid"] == "action"}
    fields = ("choice","correct_choice","top_token","top_probability","legal_logits","legal_mass")
    for row in records:
        if row["kind"] == "pulse" and row["arm"] == "L" and row["version"] == 1:
            original = natural[row["round_id"],row["side"]]
            assert all(row[k] == original[k] for k in fields)


def test_checkpoint_and_replay_artifact_hooks_are_complete(ep):
    saved = []
    run = runner(artifact_sink=lambda event: saved.append({k:v for k,v in event.items() if k != "value"}))
    run.run_episode(ep)
    assert len(saved) == 16
    assert sum(x["kind"] == "pair" for x in saved) == 4
    assert sum(x["label"].startswith("fresh_") for x in saved) == 6
    assert sum(x["label"].startswith("pulse") for x in saved) == 4
    assert sum(x["label"].startswith("goal") for x in saved) == 2
    assert [x["sequence"] for x in saved] == list(range(16))
