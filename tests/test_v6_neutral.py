"""Neutral material/privacy and collector invariants; no model or torch."""

import json
from collections import Counter
from copy import deepcopy
from dataclasses import replace

import pytest

from mb import tasks as historical
from mb import v6_neutral as n
from mb import v6_tasks as t
from mb.v6_contract import RuntimeSpec
from mb.v6_run import SyntheticBackend


def collect(stage="validation", backend=None, **kwargs):
    ep = n.make_episodes(1, stage, seed=913, namespace="unit-test")[0]
    spec = RuntimeSpec(work_tokens=3, preparation_tokens=1, window=2,
                       gain=0.0 if stage == "baseline" else 0.5)
    runner = n.NeutralRunner(backend or SyntheticBackend(), spec, "synthetic", **kwargs)
    return ep, runner, runner.run_episode(ep)


def test_material_roundtrip_write_once_and_disjoint_namespaces(tmp_path):
    eps = n.make_episodes(4, "calibration", seed=9, namespace="qwen-cal025")
    assert eps == n.make_episodes(4, "calibration", seed=9, namespace="qwen-cal025")
    other = n.make_episodes(4, "calibration", seed=9, namespace="qwen-cal050")
    assert not {ep.episode_id for ep in eps} & {ep.episode_id for ep in other}
    path = tmp_path/"materials.json"
    n.write_materials(path, eps)
    before = path.read_bytes()
    n.write_materials(path, eps)
    assert path.read_bytes() == before and n.load_materials(path) == eps
    with pytest.raises(ValueError, match="replace"):
        n.write_materials(path, other)
    forged = json.loads(before)
    forged[0]["cap_bank_sha256"] = "0"*64
    with pytest.raises(ValueError, match="CAP bank"):
        n.episode_from_dict(forged[0])


@pytest.mark.parametrize("size,stage", [(60,"baseline"),(40,"calibration"),(80,"validation")])
def test_fresh_fact_margins_and_all_historical_cap_items(size, stage):
    episodes = n.make_episodes(size, stage, namespace="material-check")
    for r in range(6):
        for side in (0,1):
            assert Counter(ep.facts[r][side] for ep in episodes) == {v:size//4 for v in range(4)}
    for ep in episodes:
        assert sorted(ep.cap_items) == list(range(18))
    # Fresh draws are not a forced alternating/cyclic within-episode code.
    assert any(ep.facts[r][s] == ep.facts[r-1][s]
               for ep in episodes for r in range(1,6) for s in (0,1))
    assert len(historical.cap_bank()) == 18


def test_private_fact_prompts_do_not_change_with_other_record():
    ep = n.make_episodes(1,"validation")[0]
    facts = list(ep.facts); facts[0] = (facts[0][0], (facts[0][1]+1)%4)
    changed = replace(ep, facts=tuple(facts))
    assert n.fact_round_prompts(ep,1)[0] == n.fact_round_prompts(changed,1)[0]
    assert n.fact_round_prompts(ep,1)[1] != n.fact_round_prompts(changed,1)[1]
    own = n.question(ep,"fact",n.FactWorld(1),0,"continuation_fact")
    assert own == n.question(changed,"fact",n.FactWorld(1),0,"continuation_fact")
    other = n.question(ep,"fact",n.FactWorld(1),0,"access_fact")
    other_changed = n.question(changed,"fact",n.FactWorld(1),0,"access_fact")
    assert other.text == other_changed.text and other.correct != other_changed.correct


def test_baseline_record_supply_only_and_fullinfo_task_truth():
    ep = n.make_episodes(1,"baseline")[0]
    q = n.question(ep,"fact",n.FactWorld(1),0,"access_fact")
    assert "Supplied record" in q.text and n.FACT_NAMES[ep.facts[0][1]] in q.text
    validation = replace(ep,stage="validation")
    assert "Supplied record" not in n.question(validation,"fact",n.FactWorld(1),0,"access_fact").text
    world = t.event_world(ep.task,t.initial_world(ep.task),1)
    q = n.question(ep,"capability",world,0,"task_fullinfo")
    assert ep.task.goal_names[world.goals[0]] in q.text
    assert t.BEACON_NAMES[world.beacons[1]] in q.text
    assert q.correct == t.correct_action(world.goals[0],world.beacons[1])
    assert "Current authorized record" not in n.question(ep,"capability",world,0,"continuation_action").text
    for qid in n.BASE_ASSIGNMENT_QIDS:
        assert "Supplied authorized records" in n.question(ep,"capability",world,0,qid).text
        with pytest.raises(ValueError, match="outside"):
            n.question(validation,"capability",world,0,qid)


def test_cap_question_bank_bytes_and_scoring_unchanged():
    ep = n.make_episodes(1,"baseline")[0]
    world = t.initial_world(ep.task)
    seen=[]
    for r in range(1,7):
        world=t.event_world(ep.task,world,r)
        for qid in n.CAP_QIDS:
            q=n.question(ep,"capability",world,1,qid)
            item=historical.cap_bank()[q.cap_item_id]
            assert q.text.startswith(item.question+"\n")
            assert all(option in q.text for option in item.options)
            assert item.options[q.correct] == item.correct
            seen.append(q.cap_item_id)
        world=t.transition(world,(None,None))
    assert sorted(seen)==list(range(18))


@pytest.mark.parametrize("stage,count", [("baseline",108),("calibration",168),("validation",168)])
def test_complete_declared_collection_and_side_order_invariance(stage,count):
    ep,runner,rows=collect(stage)
    _,_,reverse=collect(stage,side_order=(1,0))
    assert rows==reverse and len(rows)==count
    assert n.validate_records(rows,[ep],"synthetic",runner.spec.gain)["complete"]
    assert {tuple(row[k] for k in n.KEY_FIELDS) for row in rows} == n.expected_keys(ep,"synthetic",runner.spec.gain)
    assert all(row["proposal_status"]=="proposed_unratified" for row in rows)
    assert all(row["scientific_data"] is False for row in rows)
    assert not any(row["qid"] in n.BASE_ASSIGNMENT_QIDS for row in rows) if stage!="baseline" else True


def test_probe_answers_and_supplied_records_never_feed_continuing_history():
    class TrackingBackend(SyntheticBackend):
        def __init__(self):
            super().__init__(); self.created=[]; self.commits=[]
        def create(self,*args):
            state=super().create(*args); self.created.append(state); return state
        def commit_answer(self,probe,*args):
            self.commits.append(deepcopy(probe.state))
            return super().commit_answer(probe,*args)
    backend=TrackingBackend()
    collect(backend=backend)
    assert len(backend.created)==8  # Fresh A/B pair for each policy and stream.
    assert len(backend.commits)==48
    raw=json.dumps(backend.commits)
    assert "Current authorized record:" not in raw
    assert "Supplied authorized records" not in raw
    assert all(item.question not in raw for item in historical.cap_bank())


def test_off_has_no_foreign_window_and_rounds_reset():
    _,runner,_=collect()
    for tick in runner.engine.audit:
        if tick["policy"]=="OFF" or tick["tick"]==0:
            assert tick["incoming"]==[[],[]]
    assert any(any(tick["incoming"]) for tick in runner.engine.audit if tick["policy"]=="LIVE")


def test_invalid_continuations_are_preserved_and_hold_device_state():
    ep,runner,rows=collect(backend=SyntheticBackend(invalid_every=1))
    assert all(row["choice"] is None and row["correct"] is False for row in rows)
    r2=[row for row in rows if row["stream"]=="capability" and row["round_id"]==2]
    assert all(row["world"]["actions"]==((None,None),) for row in r2)
    result=n.validate_records(rows,[ep],"synthetic",runner.spec.gain)
    assert result["complete"] and result["synthetic"] and not result["scientific_admission"]


def test_mutating_diagnostic_backend_rejected():
    class BadBackend(SyntheticBackend):
        def probe(self,state,*args):
            state["history"].append(("leak",)); return super().probe(state,*args)
    with pytest.raises(RuntimeError,match="contaminated"):
        collect(backend=BadBackend())


@pytest.mark.parametrize("mutation",["duplicate","nan","question","truth","world","choice","status"])
def test_corrupt_raw_ledger_refused(mutation):
    ep,runner,original=collect()
    rows=deepcopy(original)
    if mutation=="duplicate": rows.append(rows[0])
    elif mutation=="nan": rows[0]["legal_logits"][0]=float("nan")
    elif mutation=="question": rows[0]["question_sha256"]="0"*64
    elif mutation=="truth": rows[0]["correct_choice"]=(rows[0]["correct_choice"]+1)%4
    elif mutation=="world": rows[0]["world"]["round_id"]=2
    elif mutation=="choice": rows[0]["choice"]=(rows[0]["choice"]+1)%4
    elif mutation=="status": rows[0]["status"]="failed"
    with pytest.raises(ValueError):
        n.validate_records(rows,[ep],"synthetic",runner.spec.gain)


def test_missing_tail_unavailable_and_missing_prior_actions_not_invented():
    ep,runner,rows=collect()
    result=n.validate_records(rows[:-1],[ep],"synthetic",runner.spec.gain,require_complete=False)
    assert not result["complete"] and result["missing_records"]==1
    with pytest.raises(ValueError,match="Incomplete"):
        n.validate_records(rows[:-1],[ep],"synthetic",runner.spec.gain)
    missing=[row for row in rows if not (row["policy"]=="OFF" and row["stream"]=="capability"
             and row["round_id"]==1 and row["qid"]=="continuation_action")]
    with pytest.raises(ValueError,match="incomplete action history"):
        n.validate_records(missing,[ep],"synthetic",runner.spec.gain,require_complete=False)


def test_explicit_technical_failure_is_unavailable_not_a_wrong_answer():
    ep,runner,rows=collect()
    failed=rows[-1]
    rows[-1]={k:failed[k] for k in (*n.KEY_FIELDS,"contract","proposal_status")}
    rows[-1].update(status="technical_failure",error_type="RuntimeError")
    result=n.validate_records(rows,[ep],"synthetic",runner.spec.gain,require_complete=False)
    assert result["technical_failures"]==1 and result["missing_records"]==1
    assert result["ok_records"]==167 and not result["complete"]
    with pytest.raises(ValueError,match="Incomplete"):
        n.validate_records(rows,[ep],"synthetic",runner.spec.gain)


def test_stage_gain_and_material_schema_fail_closed():
    with pytest.raises(ValueError): n.make_episodes(1,"validity")
    ep=n.make_episodes(1,"baseline")[0]
    with pytest.raises(ValueError): n.expected_keys(ep,"synthetic",.5)
    with pytest.raises(ValueError): n.expected_keys(replace(ep,stage="validation"),"synthetic",.75)
    with pytest.raises(ValueError): replace(ep,cap_items=tuple([0]*18))
    with pytest.raises(ValueError): replace(ep,facts=tuple([(False,1)]*6))


def test_raw_choice_uses_native_token_not_fp32_diagnostic_argmax():
    ep,runner,rows=collect()
    for row in rows:
        row["legal_logits"]=[-999.,999.,0.,1.]
    assert n.validate_records(rows,[ep],"synthetic",runner.spec.gain)["complete"]


@pytest.mark.parametrize("profile_key",["qwen3_4b_instruct_2507","llama31_8b_instruct"])
def test_local_native_answer_boundaries_only(profile_key):
    from mb import chat
    from mb.model_profiles import resolve_profile
    profile=resolve_profile(profile_key)
    if not profile.tokenizer_dir.exists():
        pytest.skip("Pinned local tokenizer assets absent; never download")
    eps=[n.make_episodes(1,stage,namespace="tokenizer-test")[0]
         for stage in ("baseline","validation")]
    result=n.audit_tokenizer(chat.load_tokenizer(profile=profile),eps)
    assert result["passed"] and result["errors"]==[]
    assert result["native_answer_prefixes"]==108+84
    assert result["label_append_checks"]==4*(108+84)
