from dataclasses import asdict, replace

from mb import v6_goal_stage_diagnostic as d
from mb.v6_contract import RuntimeSpec
from mb.v6_run import SyntheticBackend, record_key


def run(ep, reverse=False, side_order=(0,1)):
    r=d.GoalStageRunner(SyntheticBackend(),RuntimeSpec(work_tokens=3,preparation_tokens=1,window=2),
                      'synthetic',side_order=side_order)
    return r,r.run_diagnostic(ep,reverse_order=reverse)


def test_all_variants_and_stage_cells_preserve_order_invariance():
    for ep in d.materials():
        a,x=run(ep);b,y=run(ep,True,(1,0))
        assert len(x)==len({record_key(r) for r in x})==120
        assert {record_key(r):r for r in x}=={record_key(r):r for r in y}
        assert len(a.audit)==12*3 and len(a.stage_audit)==12
        assert {r['arm'] for r in x}==set(d.plan()['arms'])
        for r in x:
            assert r['side']==r['focal_side'] and r['world']['actions']==()
            assert r['world']['beacons']==ep.initial_beacons
            assert r['world']['goals'][r['side']]==ep.original_goals[r['side']]
            assert bool(r['readout_incoming'])==r['read_on']
            if r['read_on']:assert r['readout_incoming']==r['available_partner_exports']


def test_only_partner_assignment_changes_and_questions_do_not_reveal_it():
    for ep in d.materials():
        for side in (0,1):
            system,users=d.channel.clarity.initial_prompts(ep,'P2')
            texts={q:[] for q in d.QIDS}
            for goal in range(4):
                if goal==ep.original_goals[side]:continue
                world,vs,vu=d.donor_variant(ep,side,goal)
                before,after=asdict(d.tasks.initial_world(ep)),asdict(world)
                assert {k for k in before if before[k]!=after[k]} <= {'goals'}
                assert vs==system and vu[side]==users[side]
                w=replace(world,round_id=1)
                assert world.goals[side]==ep.original_goals[side]
                assert vu[1-side].splitlines()[:-1]==users[1-side].splitlines()[:-1]
                for q in d.QIDS:texts[q].append(d.question(ep,w,side,q).text)
            assert all(len(set(x))==1 for x in texts.values())


def test_disconnected_recipient_is_identical_and_readout_branch_has_same_parent():
    for ep in d.materials():
        _,rows=run(ep)
        for s in (0,1):
            own=[r for r in rows if r['side']==s]
            assert len({r['recipient_prepared_digest'] for r in own})==1
            assert len({r['recipient_postwork_digest'] for r in own if not r['work_on']})==1
            for g in range(4):
                for w in (False,True):
                    group=[r for r in own if r['donor_goal']==g and r['work_on']==w]
                    assert not group or len({r['postwork_pair_digest'] for r in group})==1
            for q in d.QIDS:
                off=[r for r in own if r['arm']=='W0R0' and r['qid']==q]
                assert len({tuple(r['legal_logits']) for r in off})==1


def test_no_action_or_diagnostic_answer_is_committed():
    class NoCommit(SyntheticBackend):
        def commit_answer(self,*args,**kwargs):raise AssertionError('No continuing action allowed')
    archive=[]
    r=d.GoalStageRunner(NoCommit(),RuntimeSpec(work_tokens=2,preparation_tokens=0,window=2),
                      'synthetic',artifact_sink=archive.append)
    r.run_diagnostic(d.materials()[0])
    assert len(archive)==1 and archive[0]['label']=='common_initial_pair'
