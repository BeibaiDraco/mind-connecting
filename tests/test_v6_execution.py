"""Offline orchestration fixtures explicitly replace native/model admission.

No fixture authorization, backend or result is production evidence. Real launch
proof checks are independently tested in test_v6_launch; CUDA is never imported.
"""
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from mb import v6_execution as execution
from mb import v6_native as native
from mb import v6_tasks as tasks
from mb.v6_contract import Export, RuntimeSpec, canonical_digest
from mb.v6_run import EpisodeLedger, KEY_FIELDS, SyntheticBackend

PROFILE = "qwen3_4b_instruct_2507"


def bytes_tree(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False))
    return {"path": str(path), "sha256": execution.file_sha256(path)}


@pytest.fixture
def native_fixture(tmp_path, monkeypatch):
    """Deliberately injected local stand-in; production has no such switch."""
    class MockNative(SyntheticBackend):
        kind = "unit_test_mock_only"
        model_identity = "e"*64
        device = "unit-test-no-device"
        tokens = SimpleNamespace(profile_key=PROFILE)
        def dump_state(self, state):
            return copy.deepcopy(state)
        def load_state(self, state):
            return copy.deepcopy(state)
        def dump_export(self, export):
            return {**export.identity(), "payload": copy.deepcopy(export.payload)}
        def load_export(self, payload):
            return Export(**payload)
    def dump(payload, handle):
        handle.write(json.dumps(payload, sort_keys=True).encode())
    def load(path, *, map_location, weights_only):
        assert map_location == "cpu" and weights_only is True
        return json.loads(path.read_bytes())
    monkeypatch.setattr(native, "NativeBackend", MockNative)
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(save=dump, load=load,
        cuda=SimpleNamespace(max_memory_allocated=lambda _: 0)))
    calls = []
    monkeypatch.setattr(execution, "_load_native", lambda p: calls.append(p) or MockNative())
    episodes = tasks.make_episodes(1, f"v6_{PROFILE}_smoke", 5)
    material = tmp_path/"material.json"
    tasks.write_materials(material, episodes)
    runtime = dict(work_tokens=64, preparation_tokens=16, window=16, gain=.5, choice_labels=["1","2","3","4"])
    plan = {"version":"v6-native-stage-1", "stage":"smoke", "model_profile":PROFILE,
            "n":1, "runtime":runtime, "material_pin":{"path":str(material),"sha256":execution.file_sha256(material)},
            "text_episode_ids":[], "output_dir":str(tmp_path/"run"), "source_manifest":{"mock-only":"a"*64},
            "prerequisites":{}, "admission_contract_pin":{"path":"mock-only","sha256":"b"*64}}
    accepted = {"version":"v6-native-acceptance-1","status":"passed","backend_kind":"native",
                "scientific_data":False,"model_profile":PROFILE,"native_model_identity":"e"*64,
                "source_manifest_sha256":canonical_digest(plan["source_manifest"]),
                "tokenizer_manifest_sha256":execution.file_sha256(execution.PROFILES[PROFILE].manifest_path),
                "checks":{name:True for name in execution.NATIVE_CHECKS}}
    plan["prerequisites"]["acceptance"] = save(tmp_path/"mock_acceptance.json", accepted)
    plan_path = tmp_path/"plan.json"; save(plan_path,plan)
    admission_path = tmp_path/"mock_admission.json"; save(admission_path,{"fixture":True})
    normalized = {**copy.deepcopy(plan),"plan_sha256":canonical_digest(plan),"_admission":{
        "authorization_sha256":"d"*64,"source_manifest_sha256":accepted["source_manifest_sha256"],
        "admission_contract_sha256":"b"*64,"historical_only":False,"validated_at_epoch":1000}}
    monkeypatch.setattr(execution,"_plan",lambda *_:copy.deepcopy(normalized))
    # Tiny clocks are only an injected execution-test optimization, never a CLI option.
    monkeypatch.setattr(execution,"_runtime",lambda _:RuntimeSpec(work_tokens=2,preparation_tokens=1,window=2,gain=.5))
    monkeypatch.setattr(execution,"_capture_admission",lambda *_:copy.deepcopy(normalized))
    monkeypatch.setattr(execution,"historical_plan",lambda _:copy.deepcopy(normalized))
    monkeypatch.setattr(execution,"_Bounds",lambda *_:SimpleNamespace(check=lambda **_:None))
    fake_acceptance_identity={"native_model_identity":"e"*64,"fixture":"offline-only"}
    accepted["identity_sha256"]=canonical_digest(fake_acceptance_identity)
    normalized["prerequisites"]["acceptance"]=save(tmp_path/"mock_acceptance.json",accepted)
    monkeypatch.setattr(execution,"_receipt_run",lambda *_:{"plan":{"stage":"acceptance"},
                                                         "native_identity":fake_acceptance_identity})
    return SimpleNamespace(plan=normalized, plan_path=plan_path, admission=admission_path,
        episodes=episodes, root=tmp_path, output=tmp_path/"run", calls=calls, backend=MockNative,
        accepted=accepted)


def test_native_mock_smoke_noop_and_certificate_are_byte_identical(native_fixture):
    p=native_fixture
    result=execution.execute(p.plan_path,p.admission)
    assert result["validation"]["ok_records"]==328
    assert result["scientific_data"] is False
    assert len(list((p.output/"archives").glob("*.pt")))==16
    before=bytes_tree(p.root)
    assert execution.execute(p.plan_path,p.admission,resume=True)==result
    certificate=execution.audit_noop_resume(p.plan_path,p.admission)
    assert certificate["byte_identical"] is True
    assert certificate["completion_pin"]["sha256"]==execution.file_sha256(p.output/"completion.json")
    assert bytes_tree(p.root)==before and len(p.calls)==1


@pytest.mark.parametrize("case",["source", "identity", "records", "archive"])
def test_resume_tampering_fails_before_load_or_write(native_fixture,case):
    p=native_fixture
    execution.execute(p.plan_path,p.admission)
    if case=="source":
        p.plan["source_manifest"]["mock-only"]="f"*64
    elif case=="identity":
        item=execution.read_json(p.output/"identity.json");item["native_model_identity"]="f"*64
        save(p.output/"identity.json",item)
    elif case=="records":
        path=next((p.output/"records").glob("*.jsonl"));path.write_text(path.read_text()+'{"torn":')
    else:
        path=next((p.output/"archives").glob("*.pt"));path.write_bytes(b"tampered")
    before=bytes_tree(p.root)
    with pytest.raises(ValueError):
        execution.execute(p.plan_path,p.admission,resume=True)
    assert bytes_tree(p.root)==before and len(p.calls)==1


def test_real_synthetic_backend_rejected_without_output(native_fixture,monkeypatch):
    p=native_fixture
    monkeypatch.setattr(execution,"_load_native",lambda _:SyntheticBackend())
    with pytest.raises(ValueError,match="real admitted"):
        execution.execute(p.plan_path,p.admission)
    assert not p.output.exists()


def test_model_bytes_must_match_accepted_identity(native_fixture,monkeypatch):
    p=native_fixture
    backend=p.backend();backend.model_identity="f"*64
    monkeypatch.setattr(execution,"_load_native",lambda _:backend)
    with pytest.raises(ValueError,match="parameter identity"):
        execution.execute(p.plan_path,p.admission)
    assert not p.output.exists()


@pytest.mark.parametrize("case", ["missing_check","synthetic","different_source"])
def test_acceptance_prerequisite_never_accepts_placeholder(native_fixture,case):
    p=native_fixture
    if case=="missing_check": p.accepted["checks"].pop("foreign_attention_reference")
    elif case=="synthetic": p.accepted["backend_kind"]="synthetic_fixture"
    else: p.accepted["source_manifest_sha256"]="f"*64
    p.plan["prerequisites"]["acceptance"]=save(p.root/"changed.json",p.accepted)
    with pytest.raises(ValueError,match="Acceptance"):
        execution.execute(p.plan_path,p.admission)
    assert not p.output.exists() and not p.calls


def test_refused_live_admission_precedes_any_model_or_write(native_fixture,monkeypatch):
    p=native_fixture
    before=bytes_tree(p.root)
    def denied(*_):raise PermissionError("test-only missing grant")
    monkeypatch.setattr(execution,"_plan",denied)
    with pytest.raises(PermissionError):execution.execute(p.plan_path,p.admission)
    assert not p.calls and bytes_tree(p.root)==before


def test_historical_envelope_never_authorizes_execution(tmp_path,monkeypatch):
    import mb.v6_launch as launch
    monkeypatch.setattr(launch,"validate_execution",lambda *_:{"_admission":{"historical_only":True}})
    with pytest.raises(ValueError,match="Historical"):
        execution._plan(tmp_path/"plan",tmp_path/"admission")
    assert not list(tmp_path.iterdir())


def test_material_namespace_and_count_are_not_caller_assertions(native_fixture):
    p=native_fixture
    assert execution._materials(p.plan)[0]==p.episodes
    p.plan["n"]=2
    with pytest.raises(ValueError,match="count/profile/stage"):
        execution._materials(p.plan)
    p.plan["n"]=1;p.plan["stage"]="acceptance"
    with pytest.raises(ValueError,match="count/profile/stage"):
        execution._materials(p.plan)


@pytest.mark.parametrize("stage,gain,n",[("baseline",0.,60),("calibration",.25,40),("calibration",.5,40),("calibration",1.,40),("validation",.5,80)])
def test_actual_neutral_material_namespace(stage,gain,n,tmp_path):
    from mb import v6_neutral as neutral
    suffix=f"_g{int(gain*100):03d}" if stage=="calibration" else ""
    eps=neutral.make_episodes(n,stage,0,namespace=f"{PROFILE}_{stage}{suffix}")
    file=tmp_path/"materials.json";neutral.write_materials(file,eps)
    plan={"stage":stage,"model_profile":PROFILE,"n":n,"runtime":{"gain":gain},
          "material_pin":{"path":str(file),"sha256":execution.file_sha256(file)},"text_episode_ids":[]}
    loaded,digest,fields=execution._materials(plan)
    assert loaded==eps and digest==neutral.materials_sha256(eps) and fields==neutral.KEY_FIELDS


def test_exact_one_retry_preserves_successful_rows(native_fixture,monkeypatch):
    p=native_fixture
    original=execution.EpisodeRunner
    attempts=[]
    class FailsOnce(original):
        def emit(self,*args,**kwargs):
            super().emit(*args,**kwargs)
            if len(attempts)==1 and len(self.records)==13:
                raise RuntimeError("simulated transient decoder failure")
        def run_episode(self,*args,**kwargs):
            attempts.append(1)
            return super().run_episode(*args,**kwargs)
    monkeypatch.setattr(execution,"EpisodeRunner",FailsOnce)
    result=execution.execute(p.plan_path,p.admission)
    assert result["validation"]["ok_records"]==328 and len(attempts)==2
    notes=[json.loads(line) for line in (p.output/"notes.jsonl").read_text().splitlines()]
    assert sum(r["event"]=="episode_started" for r in notes)==2
    rows=[json.loads(line) for f in (p.output/"records").glob("*.jsonl") for line in f.read_text().splitlines()]
    assert len(rows)==328 and len({tuple(r[k] for k in KEY_FIELDS) for r in rows})==328


def test_exhausted_retry_refused_without_model_or_new_notes(native_fixture):
    p=native_fixture
    _,digest,fields=execution._materials(p.plan)
    identity=execution._identity(p.plan,digest,fields,"e"*64)
    ledger=EpisodeLedger(p.output,identity)
    for _ in range(2):ledger.note({"event":"episode_started","episode_id":p.episodes[0].episode_id})
    ledger.close()
    before=bytes_tree(p.output)
    with pytest.raises(RuntimeError,match="retry are exhausted"):
        execution.execute(p.plan_path,p.admission,resume=True)
    assert bytes_tree(p.output)==before and not p.calls


def test_orphan_archive_is_preserved_and_blocks_resume(native_fixture):
    p=native_fixture
    _,digest,fields=execution._materials(p.plan)
    ledger=EpisodeLedger(p.output,execution._identity(p.plan,digest,fields,"e"*64));ledger.close()
    (p.output/"archives").mkdir();(p.output/"archives/orphan.pt").write_bytes(b"partial")
    before=bytes_tree(p.output)
    with pytest.raises(ValueError,match="Unindexed"):
        execution.execute(p.plan_path,p.admission,resume=True)
    assert bytes_tree(p.output)==before and not p.calls


def test_retry_cannot_change_retained_success(native_fixture,monkeypatch):
    p=native_fixture
    original=execution.EpisodeRunner;attempts=[]
    class ChangedRetry(original):
        def emit(self,*args,**kwargs):
            super().emit(*args,**kwargs)
            if len(attempts)==1 and len(self.records)==1:raise RuntimeError("transient")
        def run_episode(self,*args,**kwargs):
            attempts.append(1)
            if len(attempts)>1:
                old=self.sink
                self.sink=lambda row:old({**row,"top_probability":.123})
            return super().run_episode(*args,**kwargs)
    monkeypatch.setattr(execution,"EpisodeRunner",ChangedRetry)
    with pytest.raises(ValueError,match="changed"):
        execution.execute(p.plan_path,p.admission)
    assert not (p.output/"completion.json").exists()


def test_runtime_contract_rejects_silent_clock_change():
    plan={"stage":"smoke","runtime":{"work_tokens":64,"preparation_tokens":16,"window":16,
                                       "gain":.5,"choice_labels":["1","2","3","4"]}}
    assert execution._runtime(plan).work_tokens==64
    plan["runtime"]["work_tokens"]=32
    with pytest.raises(ValueError,match="clocks"):
        execution._runtime(plan)


def test_standalone_pass_json_is_not_native_run_evidence(tmp_path):
    pin=save(tmp_path/"acceptance.json",{"status":"passed"})
    with pytest.raises(FileNotFoundError):
        execution._receipt_run(pin,{})


def test_archived_material_resolves_original_deleted_path(native_fixture):
    p=native_fixture
    evidence=p.root/"evidence";evidence.mkdir()
    pin=p.plan["material_pin"]
    (evidence/(pin["sha256"]+".json")).write_bytes(Path(pin["path"]).read_bytes())
    Path(pin["path"]).unlink()
    p.plan["_admission"]["evidence_dir"]=str(evidence)
    assert execution._materials(p.plan)[0]==p.episodes


# Reuse the independently maintained real launch-envelope fixture, not a bypass.
from test_v6_launch import package  # noqa: E402,F401


def test_original_admission_archive_survives_live_proof_refresh(package):
    p=package
    out=p.root/"archive-test";out.mkdir()
    original_plan=p.plan_path.read_bytes();original_proof=p.proof_path.read_bytes()
    first=execution._capture_admission(out,p.plan_path,p.proof_path)
    assert first["_admission"]["historical_only"] is True
    evidence=Path(first["_admission"]["evidence_dir"])
    assert (evidence/(execution.file_sha256(p.plan_path)+".json")).read_bytes()==original_plan
    assert (evidence/(execution.file_sha256(p.proof_path)+".json")).read_bytes()==original_proof
    Path(p.proof["local_guard_pin"]["path"]).write_text("{}")
    p.proof_path.write_text("{}")
    later=execution.historical_plan(out)
    assert later==first
    archived=evidence/(first["_admission"]["authorization_sha256"]+".json")
    archived.write_text("{}")
    with pytest.raises(ValueError):execution.historical_plan(out)


def test_neutral_native_mock_keeps_its_own_keys_and_material_metadata(native_fixture,monkeypatch):
    from mb import v6_neutral as neutral
    from mb import v6_admission as admission
    p=native_fixture
    episodes=neutral.make_episodes(1,"baseline",0,namespace="unit-test-only")
    p.plan["stage"]="baseline";p.plan["runtime"]["gain"]=0
    fields=neutral.KEY_FIELDS
    monkeypatch.setattr(execution,"_runtime",lambda _:RuntimeSpec(work_tokens=2,preparation_tokens=1,window=2,gain=0.))
    monkeypatch.setattr(execution,"_materials",lambda _:(episodes,neutral.materials_sha256(episodes),fields))
    monkeypatch.setattr(execution,"_prerequisites",lambda _:p.accepted)
    monkeypatch.setattr(admission,"validate_stage_prerequisites",lambda _: {"fixture":True})
    observed=[]
    def gate(records,eps,plan,*,native_identity):
        assert len(records)==108 and eps==episodes
        assert neutral.validate_records(records,eps,PROFILE,0.)["complete"]
        assert len({r["material_sha256"] for r in records})==1
        assert all(r["execution_identity_sha256"]==canonical_digest(native_identity) for r in records)
        observed.append(1)
        return {"gate":"fail","consumable":True,"fixture_only":True}
    monkeypatch.setattr(admission,"evaluate_stage",gate)
    report=execution.execute(p.plan_path,p.admission)
    assert report["validation"]["gate"]=="fail" and report["status"]=="complete"
    assert len(observed)==1 and not (p.output/"archives").exists()
    before=bytes_tree(p.root)
    assert execution.execute(p.plan_path,p.admission,resume=True)==report
    assert len(observed)==1 and bytes_tree(p.root)==before
