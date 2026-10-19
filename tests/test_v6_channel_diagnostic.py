from dataclasses import replace
import re

from mb import v6_channel_diagnostic as d, v6_tasks as tasks
from mb.v6_contract import RuntimeSpec
from mb.v6_run import SyntheticBackend, record_key


def runner(**kw):
    return d.ChannelRunner(SyntheticBackend(),RuntimeSpec(work_tokens=3,preparation_tokens=1,window=2),"synthetic",**kw)


def test_finite_readout_coverage_and_order_invariance():
    for ep in d.materials():
        a,b=runner(),runner(side_order=(1,0))
        xs=a.run_diagnostic(ep);ys=b.run_diagnostic(ep,reverse_order=True)
        assert {record_key(x):x for x in xs} == {record_key(x):x for x in ys}
        assert len(xs)==len({record_key(x) for x in xs})==150
        assert {x['qid'] for x in xs}==set(d.QIDS)
        assert len(a.audit)==15*3


def test_only_explicit_text_control_reveals_partner_beacon():
    for ep in d.materials():
        w=tasks.event_world(ep,tasks.initial_world(ep),1)
        for side in (0,1):
            b=list(w.beacons);b[1-side]^=1;changed=replace(w,beacons=tuple(b))
            for condition in d.CONDITIONS:
                x=d.round_messages(ep,w,(False,False),condition)[side]
                y=d.round_messages(ep,changed,(False,False),condition)[side]
                assert (x!=y)==(condition=='TEXT_FACTS')
            for qid in d.QIDS:assert d.question(ep,w,side,qid).text==d.question(ep,changed,side,qid).text


def test_readout_truth_matches_displayed_rule_and_pair():
    for ep in d.materials():
        system,_=d.clarity.initial_prompts(ep,'P2')
        rules={g:(dim,bright) for g,dim,bright in re.findall(r"(G\d): if the OTHER participant's current beacon is Dim, press (\w+); if it is Bright, press (\w+)\.",system)}
        w=tasks.event_world(ep,tasks.initial_world(ep),1)
        for side in (0,1):
            q=d.question(ep,w,side,'own_rule');i=q.candidates.index(q.correct)
            line=q.text.splitlines()[i+1]
            pair=rules[ep.goal_names[w.goals[side]]]
            assert f'Dim: {pair[0]}; Bright: {pair[1]}' in line
            q=d.question(ep,w,side,'beacon_pair');assert (q.correct//2,q.correct%2)==w.beacons


def test_initial_state_archived_once_and_only_actions_committed():
    class Tracking(SyntheticBackend):
        def __init__(self):super().__init__();self.questions=[]
        def commit_answer(self,probe,foreign,gain):
            self.questions.append(probe.state['history'][-1][1])
            return super().commit_answer(probe,foreign,gain)
    backend=Tracking();events=[]
    run=d.ChannelRunner(backend,RuntimeSpec(work_tokens=2,preparation_tokens=0,window=2),'synthetic',artifact_sink=events.append)
    run.run_diagnostic(d.materials()[0])
    assert len(events)==1 and events[0]['label']=='common_initial_pair'
    assert len(backend.questions)==30 and all('which button' in q for q in backend.questions)
    assert not set(e.episode_id for e in d.materials()) & set(e.episode_id for e in d.pilot.materials())
