from dataclasses import replace
import json
import numpy as np
import pytest

from mb.v6_batch import CohortRunner, SerialBatchAdapter, CohortReceipt
from mb.v6_batch_native import PackedLayout, packed_oracle
from mb.v6_contract import RuntimeSpec
from mb.v6_run import SyntheticBackend
from mb.v6_runtime import EpisodeRunner
from mb.v6_tasks import make_episodes
from mb.v6_state_guard import array_snapshot, verify_arrays
from mb.v6_batch_neutral import NeutralCohortRunner
from mb import v6_neutral as neutral


@pytest.mark.parametrize("n",[1,2,4])
@pytest.mark.parametrize("gain,invalid",[(0.,None),(.5,None),(1.,3)])
def test_complete_cohort_matches_independent_scalar_records_tapes_and_audits(n,gain,invalid):
    episodes=make_episodes(n,stage="engineering_batch",seed=8401)
    spec=RuntimeSpec(work_tokens=2,preparation_tokens=1,window=2,gain=gain)
    text_ids=(episodes[0].episode_id,)
    events=[[] for _ in episodes]
    def archive(target):
        return lambda e:target.append({k:v for k,v in e.items() if k!="value"})
    runner=CohortRunner(SerialBatchAdapter(SyntheticBackend(invalid_every=invalid)),spec,"synthetic",episodes,
        text_ids=text_ids,artifact_sinks=[archive(e) for e in events])
    actual=runner.run()
    for lane,ep in enumerate(episodes):
        expected_events=[]
        original=EpisodeRunner(SyntheticBackend(invalid_every=invalid),spec,"synthetic",artifact_sink=archive(expected_events))
        expected=original.run_episode(ep,text_reference=ep.episode_id in text_ids)
        assert actual[lane]==expected
        assert events[lane]==expected_events
        assert runner.runners[lane].audit==original.audit
    with pytest.raises(RuntimeError,match="restarted"): runner.run()


def test_cohort_detects_cross_lane_or_parent_contamination():
    class Bad(SerialBatchAdapter):
        def probe_many(self,states,*args):
            probes=super().probe_many(states,*args)
            states[0]["history"].append(("contamination",))
            return probes
    eps=make_episodes(2,stage="engineering_batch",seed=8401)
    with pytest.raises(RuntimeError,match="mutated"):
        CohortRunner(Bad(SyntheticBackend()),RuntimeSpec(work_tokens=2,preparation_tokens=1),"synthetic",eps).run()


@pytest.mark.parametrize("stage,gain",[("baseline",0.),("calibration",.25),("calibration",.5),("calibration",1.),("validation",.5)])
@pytest.mark.parametrize("invalid",[None,3])
def test_all_neutral_streams_match_unchanged_scalar(stage,gain,invalid):
    eps=neutral.make_episodes(2,stage,seed=944,namespace="engineering_cohort")
    spec=RuntimeSpec(work_tokens=2,preparation_tokens=1,gain=gain)
    run=NeutralCohortRunner(SerialBatchAdapter(SyntheticBackend(invalid_every=invalid)),spec,"synthetic",eps)
    actual=run.run()
    for ep,records in zip(eps,actual):
        expected=neutral.NeutralRunner(SyntheticBackend(invalid_every=invalid),spec,"synthetic").run_episode(ep)
        assert records==expected


def test_cohort_tick_does_not_publish_partial_outputs():
    class Bad(SerialBatchAdapter):
        def step_many(self,states,windows,gain):
            super().step_many(states[:1],windows[:1],gain)
            raise RuntimeError("lane failure")
    eps=make_episodes(2,stage="engineering_batch",seed=8401)
    runner=CohortRunner(Bad(SyntheticBackend()),RuntimeSpec(work_tokens=2,preparation_tokens=1),"synthetic",eps)
    pairs=runner.initialize(); runner.prepare(pairs,1)
    with pytest.raises(RuntimeError,match="lane failure"): runner.work(pairs,"LIVE")
    assert all(p.windows==((),()) for p in pairs)
    assert not any(r.audit for r in runner.runners)


def test_identity_bound_noop_resume_and_partial_rejection(tmp_path):
    identity={"cohort":["e1","e2"],"source":"abc","chunk":16,"is_engineering":True,
              "key_fields":["value"],"lane_keys":[[[3]],[[4]]]}
    rec=CohortReceipt(tmp_path/"run",identity)
    with pytest.raises(FileNotFoundError): CohortReceipt(tmp_path/"run",identity,resume=True)
    rec.complete([[{"value":3}],[{"value":4}]])
    before={p.name:p.read_bytes() for p in (tmp_path/"run").iterdir()}
    assert CohortReceipt(tmp_path/"run",identity,resume=True).result==rec.result
    assert before=={p.name:p.read_bytes() for p in (tmp_path/"run").iterdir()}
    (tmp_path/"run"/"identity.json").write_text(json.dumps({**identity,"is_engineering":1}))
    with pytest.raises(ValueError,match="identity"):
        CohortReceipt(tmp_path/"run",identity,resume=True)
    (tmp_path/"run"/"identity.json").write_text(json.dumps(identity))
    with pytest.raises(ValueError,match="identity"):
        CohortReceipt(tmp_path/"run",{**identity,"cohort":["e2","e1"]},resume=True)
    modified={**identity,"chunk":8}
    (tmp_path/"run"/"identity.json").write_text(json.dumps(modified))
    with pytest.raises(ValueError,match="Completion identity"):
        CohortReceipt(tmp_path/"run",modified,resume=True)
    (tmp_path/"run"/"identity.json").write_text(json.dumps(identity))
    (tmp_path/"run"/"records.json").write_text("[]")
    with pytest.raises(ValueError,match="bytes"): CohortReceipt(tmp_path/"run",identity,resume=True)


@pytest.mark.parametrize("gain",[0.,.25,.5,1.])
@pytest.mark.parametrize("prefixes,inputs,windows",[((1,5),(4,1),(0,3)),((3,2),(0,5),(2,0)),((0,2),(4,3),(3,1))])
@pytest.mark.parametrize("offset,count",[(0,2),(2,2)])
def test_packed_mask_against_independent_scalar_oracle(gain,prefixes,inputs,windows,offset,count):
    if offset+count>max(inputs): return
    layout=PackedLayout(prefixes,inputs,windows,offset,count,gain)
    rng=np.random.default_rng(42); b=2; h=4; kh=2; d=3
    q=rng.normal(size=(b,h,count,d)); k=rng.normal(size=(b,kh,layout.own,d)); v=rng.normal(size=k.shape)
    fk=rng.normal(size=(b,kh,layout.foreign,d)); fv=rng.normal(size=fk.shape)
    expected=packed_oracle(layout,(q,k,v,fk,fv))
    allowed,valid=layout.masks()
    keys=np.repeat(np.concatenate((k,fk),axis=2),2,axis=1)
    values=np.repeat(np.concatenate((v,fv),axis=2),2,axis=1)
    scores=q@keys.swapaxes(-1,-2)/np.sqrt(d)
    if layout.foreign: scores[:,:,:,layout.own:]+=np.log(gain)
    scores=np.where(allowed[:,None],scores,-np.inf)
    weights=np.exp(scores-np.max(scores,axis=-1,keepdims=True)); weights/=weights.sum(axis=-1,keepdims=True)
    actual=weights@values
    np.testing.assert_allclose(actual.transpose(0,2,1,3)[valid],expected.transpose(0,2,1,3)[valid],rtol=1e-12,atol=1e-12)
    # Poison every padding entry; no valid query may use its value.
    changed=v.copy()
    for lane,p in enumerate(prefixes): changed[lane,:,p:layout.prefix]=1e15
    np.testing.assert_array_equal(packed_oracle(layout,(q,k,changed,fk,fv)),expected)


def test_mask_future_and_foreign_boundaries_are_explicit():
    layout=PackedLayout((2,4),(3,1),(1,0),0,3,.5)
    mask,valid=layout.masks()
    assert np.flatnonzero(mask[0,0]).tolist()==[0,1,4,7]
    assert np.flatnonzero(mask[0,2]).tolist()==[0,1,4,5,6,7]
    assert np.flatnonzero(mask[1,0]).tolist()==[0,1,2,3,4]
    assert valid.tolist()==[[True,True,True],[True,False,False]]


def test_fixed_physical_shapes_do_not_follow_other_lane_lengths():
    a=PackedLayout((3,5),(2,3),(2,1),0,4,.5,16,16)
    b=PackedLayout((3,12),(2,13),(2,16),0,4,.5,16,16)
    am,av=a.masks();bm,bv=b.masks()
    assert am.shape==bm.shape
    np.testing.assert_array_equal(am[0],bm[0]);np.testing.assert_array_equal(av[0],bv[0])
    rng=np.random.default_rng(5)
    arrays=tuple(rng.normal(size=s) for s in ((2,4,4,3),(2,2,a.own,3),(2,2,a.own,3),(2,2,16,3),(2,2,16,3)))
    np.testing.assert_array_equal(packed_oracle(a,arrays)[0],packed_oracle(b,arrays)[0])


@pytest.mark.parametrize("change",["signed_zero","bit","shape","dtype","metadata","count"])
def test_byte_guard_catches_changes_float_equality_misses(change):
    a=np.array([0.,1.],dtype=np.float32); metadata={"history":[1,2]}
    snapshot=array_snapshot(metadata,(a,)); arrays=(a.copy(),)
    if change=="signed_zero": arrays[0][0]=-0.
    if change=="bit": arrays[0].view(np.uint8)[-1]^=1
    if change=="shape": arrays=(arrays[0].reshape(1,2),)
    if change=="dtype": arrays=(arrays[0].astype(np.float64),)
    if change=="metadata": metadata["history"].append(3)
    if change=="count": arrays=()
    with pytest.raises(RuntimeError): verify_arrays(snapshot,metadata,arrays)
    assert json.loads(snapshot[0])=={"history":[1,2]}


@pytest.mark.parametrize("before,after",[(1,True),(0.0,-0.0)])
def test_metadata_byte_guard_is_stricter_than_python_equality(before,after):
    assert before==after
    snap=array_snapshot({"value":before},())
    with pytest.raises(RuntimeError): verify_arrays(snap,{"value":after},())
