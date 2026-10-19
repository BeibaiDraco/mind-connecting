from dataclasses import replace

from mb import v6_interaction_pilot as p, v6_tasks as tasks
from mb.v6_contract import RuntimeSpec
from mb.v6_run import SyntheticBackend, record_key


def runner(**kw):
    return p.PilotRunner(SyntheticBackend(), RuntimeSpec(work_tokens=4,
        preparation_tokens=2, window=2, gain=p.GAIN), "synthetic", **kw)


def test_finite_coverage_and_exact_replay_with_both_side_orders():
    for ep in p.materials():
        a, b = runner(), runner(side_order=(1, 0))
        rows = a.run_pilot(ep)
        assert rows == b.run_pilot(ep)
        assert len(rows) == len({record_key(r) for r in rows}) == 150
        assert {r['qid'] for r in rows} == {'action', 'partner_beacon', 'latest_goal'}
        assert {r['arm'] for r in rows if r['kind'] == 'pulse'} == {'L','Fcut','Rcut','Replay'}
        assert len(a.audit) == 28*4


def test_channel_inputs_do_not_leak_other_private_world_fields():
    for ep in p.materials():
        w = tasks.event_world(ep, tasks.initial_world(ep), 1)
        for side in (0, 1):
            b = list(w.beacons); b[1-side] ^= 1
            g = list(w.goals); g[1-side] = (g[1-side]+1) % 4
            changed = replace(w, beacons=tuple(b), goals=tuple(g))
            assert p.round_messages(ep, w, (False,False))[side] == p.round_messages(ep, changed, (False,False))[side]
            assert p.clarity.question(ep,w,side,'P2').text == p.clarity.question(ep,changed,side,'P2').text


def test_fresh_identity_and_no_fullinfo_question_or_formal_dispatch():
    old = {e.episode.episode_id for e in p.clarity.make_short_cases()}
    assert not old.intersection(e.episode_id for e in p.materials())
    assert {e.early_side for e in p.materials()} == {0,1}
    assert p.plan()['records'] == 300 and p.plan()['formal_authorized'] is False


def test_measurement_probes_never_commit_goal_or_partner_answer():
    class Tracking(SyntheticBackend):
        def __init__(self): super().__init__(); self.committed=[]
        def commit_answer(self, probe, foreign, gain):
            self.committed.append(probe.state['history'][-1][1])
            return super().commit_answer(probe, foreign, gain)
    backend=Tracking()
    r=p.PilotRunner(backend,RuntimeSpec(work_tokens=2,preparation_tokens=0,window=2),"synthetic")
    r.run_pilot(p.materials()[0])
    assert len(backend.committed)==50
    assert all('which button' in q for q in backend.committed)
