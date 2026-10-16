"""CPU-only engineering authority, identity and failure-evidence boundaries."""
import json
import numpy as np
import pytest
from mb import v6_efficiency_trial as trial
from mb.v6_batch_native import PackedBackend


def test_inert_package_roundtrip_source_binding_and_no_overwrite(tmp_path,monkeypatch):
    root=tmp_path/"plan"
    created=trial.prepare(root)
    loaded=json.loads((root/"package.json").read_text())
    assert created==loaded
    trial.validate(loaded)
    for key in ("paid_launch_authorized","formal_authorized","automatic_scientific_continuation","numerical_adoption"):
        assert loaded[key] is False
    assert "tests/test_v6_batch_gpu.py" in loaded["source_sha256"]
    with pytest.raises(FileExistsError):trial.prepare(root)
    manifest=trial.source_manifest()
    monkeypatch.setattr(trial,"source_manifest",lambda:{**manifest,"changed":"a"*64})
    with pytest.raises(ValueError,match="stale"):trial.validate(loaded)


@pytest.mark.parametrize("field,value",[("formal_authorized",True),("proposed_incremental_cap_usd",9.),
    ("gains",[0.,.5]),("backend",{"cohort_width":4})])
def test_package_cannot_expand_trial(tmp_path,field,value):
    p=trial.proposal();p[field]=value
    with pytest.raises(ValueError):trial.validate(p)


def test_boolean_cannot_alias_frozen_numeric_gain():
    p=trial.proposal();p["gains"][-1]=True
    with pytest.raises(ValueError):trial.validate(p)


def test_engineering_precision_note_and_policy_are_bound():
    p=trial.proposal()
    assert "docs/runbooks/V6_SDPA_DTYPE_REPAIR_20261016.md" in p["source_sha256"]
    assert p["operator_bias_policy"]["efficient_sdpa"]=="query_dtype_before_aligned_slice"
    assert p["operator_bias_policy"]["scope"]=="unadopted_engineering_candidate"
    p["operator_bias_policy"]["efficient_sdpa"]="float32"
    with pytest.raises(ValueError,match="stale"):trial.validate(p)


def test_compile_policy_and_new_check_are_source_bound(tmp_path):
    p=trial.prepare_compiler_check(tmp_path/"compiler")
    trial.validate_compiler_check(p)
    assert p["stages"][0]["expected_tests"]==10 and p["stages"][1]["expected_tests"]==55
    assert "src/mb/v6_flex_compile.py" in p["source_sha256"]
    assert "tests/test_v6_flex_compile_gpu.py" in p["source_sha256"]
    assert "docs/runbooks/V6_FLEX_COMPILE_REPAIR_20261016.md" in p["source_sha256"]
    for key in ("paid_launch_authorized","formal_authorized","real_checkpoint_loading",
                "automatic_retry","whole_workload_forecast_allowed"):
        assert p[key] is False
    assert p["proposed_lifecycle_seconds"]==1800 and p["proposed_incremental_cap_usd"]==2.
    p["flex_compile_policy"]["max_graphs_per_owner"]=32
    with pytest.raises(ValueError,match="stale"):trial.validate_compiler_check(p)


def test_main_package_cannot_silently_replace_compile_policy():
    p=trial.proposal();p["flex_compile_policy"]["key_length"]="static"
    with pytest.raises(ValueError,match="stale"):trial.validate(p)


def test_intermediate_disagreement_blocks_even_when_final_token_matches():
    hidden=np.ones(2)
    a=[(hidden,np.array([1.,0.])),(hidden,np.array([0.,1.]))]
    b=[(hidden,np.array([0.,1.])),(hidden,np.array([0.,1.]))]
    ok,arrays=trial.compare_position_traces({"reference":[a],"candidate":[b]},(2,))
    assert not ok and len(arrays)==8
    with pytest.raises(ValueError,match="Incomplete"):
        trial.compare_position_traces({"reference":[a],"candidate":[b[-1:]]},(2,))
    b[0]=(hidden,np.array([float("nan"),1.]))
    with pytest.raises(ValueError,match="Invalid"):
        trial.compare_position_traces({"reference":[a],"candidate":[b]},(2,))


def test_execution_refuses_before_gpu_import_or_output_without_fresh_authority(tmp_path):
    p=trial.proposal()
    with pytest.raises(PermissionError):trial.run_case(tmp_path/"x",p,None,"qwen","full_cohort")
    with pytest.raises(PermissionError):trial.teacher_forced_micro(tmp_path/"y",p,None,None)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("prior,rate,extra,hours,expected",[
    (20.,1.6,1.6,4.,True),(93.,1.6,1.6,4.,False),(0.,1.61,0.,1.,False),
    (0.,1.,0.,4.01,False),(0.,1.6,2.,4.,False),(0.,0.,0.,4.,False)])
def test_envelope_keeps_all_prior_charges_without_granting_authority(prior,rate,extra,hours,expected):
    r=trial.budget_envelope(prior_total_usd=prior,hourly_usd=rate,noncompute_usd=extra,elapsed_hours=hours)
    assert r["fits_proposal"] is expected and r["approved"] is False
    assert r["proposed_cumulative_usd"]==prior+rate*hours+extra


@pytest.mark.parametrize("bad",[-1.,float("nan"),float("inf"),True,"1"])
def test_envelope_rejects_unusable_accounting(bad):
    with pytest.raises(ValueError):trial.budget_envelope(prior_total_usd=bad,hourly_usd=1.,noncompute_usd=1.)


def test_late_check_failure_retains_measurement_without_success(tmp_path):
    def expired():raise TimeoutError("deadline")
    with pytest.raises(TimeoutError):trial._publish_result(tmp_path,{"measured":12},expired)
    assert json.loads((tmp_path/"measurement.json").read_text())=={"measured":12}
    assert not (tmp_path/"result.json").exists()
    with pytest.raises(FileNotFoundError):trial.read_result(tmp_path)


def test_terminal_is_last_operation_and_failure_takes_precedence(tmp_path):
    calls=[]
    def check():
        assert not (tmp_path/"result.json").exists()
        calls.append(True)
    trial._publish_result(tmp_path,{"science":False},check)
    assert calls==[True] and trial.read_result(tmp_path)=={"science":False}
    (tmp_path/"failure.json").write_text('{}')
    with pytest.raises(ValueError,match="Failed"):trial.read_result(tmp_path)


def test_scalar_generation_and_commit_use_same_bulk_boundary_without_torch():
    b=PackedBackend.__new__(PackedBackend);seen=[]
    def step_many(s,w,g):seen.append(("step",s,w,g));return ("export",)
    def commit_many(s,w,g):seen.append(("commit",s,w,g));return ("state",)
    b.step_many=step_many;b.commit_many=commit_many
    assert b.step("parent",("signal",),.5)=="export"
    assert b.commit_answer("probe",(),0.)=="state"
    assert seen==[("step",("parent",),(("signal",),),.5),("commit",("probe",),((),),0.)]
