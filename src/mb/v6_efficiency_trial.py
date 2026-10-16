"""Inert, bounded engineering trial preparation and explicitly guarded cases.

No renting, restart, credential access, scientific selector, automatic retry,
formal dispatch or model loading. A future approved controller supplies already
verified models and an independent live budget/shutdown check.
"""
from __future__ import annotations
from dataclasses import asdict,replace
from pathlib import Path
import hashlib
import json
import math
import os
import time
import traceback
from typing import Callable

from mb import v6_tasks as tasks
from mb import v6_neutral as neutral
from mb import v6_analysis as analysis
from mb.v6_batch import CohortRunner,CohortReceipt
from mb.v6_batch_neutral import NeutralCohortRunner
from mb.v6_contract import RuntimeSpec,canonical_digest
from mb.v6_run import NativeArchiveWriter,source_manifest
from mb.v6_benchmark import PROFILES

VERSION="v6-bounded-optimization-trial-1"
CASES=("short_repeat","full_cohort","baseline_fixture","calibration_fixture")


def _write(path,value):
    with Path(path).open("x") as f:
        json.dump(value,f,sort_keys=True,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())


def proposal() -> dict:
    sources=source_manifest()
    root=Path(__file__).resolve().parents[2]
    supporting=[*sorted((root/"tests").glob("test_v6_*py")),
        root/"docs/runbooks/V6_LOCAL_OPTIMIZATION_TRIAL_20261015.md",
        root/"docs/reviews/v6_local_optimization_review_20261015.md"]
    for p in supporting:
        sources[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    value={"version":VERSION,"source_sha256":sources,"profiles":list(PROFILES),
        "backend":{"chunk":16,"prefix_capacity":4096,"foreign_capacity":16,"cohort_width":2,"kernel":"compiled_flex"},
        "order":["operator_and_tiny_architecture_tests","teacher_forced_all_gains",*CASES],
        "gains":[0.,.25,.5,1.],"engineering_seed":208741,
        "runtime":asdict(RuntimeSpec(gain=1.)),"short_runtime":asdict(RuntimeSpec(work_tokens=2,preparation_tokens=1,gain=1.)),
        "proposed_incremental_cap_usd":8.,"proposed_lifecycle_seconds":14400,
        "proposed_worker_seconds":11700,"shutdown_and_backup_reserve_seconds":2700,
        "hourly_cap_usd":1.6,"noncompute_reserve_usd":1.6,"cumulative_cap_usd":100.,
        "retain_original_financial_anchor_and_all_prior_charges":True,
        "paid_launch_authorized":False,"formal_authorized":False,"automatic_scientific_continuation":False,
        "numerical_adoption":False,"whole_workload_forecast_requires_both_complete_models":True,
        "failure_rule":"retain evidence; no automatic retry or alternative kernel; actual stop and backup required",
        "micro_rule":"nonfinite, invariant failure, or any teacher-forced greedy disagreement stops before complete cases",
        "floating_error_rule":"retain all deviations; no full-model tolerance or scientific equivalence is asserted"}
    return json.loads(json.dumps(value,allow_nan=False))


def _publish_result(directory:Path,result:dict,check:Callable[[],None]) -> dict:
    """Last case operation: no deadline check after the terminal publication.

    This is a measurement receipt, never evidence of the caller's safe shutdown.
    A failure file always invalidates it (including a filesystem publication error).
    """
    _write(directory/"measurement.json",result)
    check()
    _write(directory/"result.json",result)
    return result


def read_result(directory:Path) -> dict:
    directory=Path(directory)
    if (directory/"failure.json").exists():raise ValueError("Failed case is not complete")
    measured=json.loads((directory/"measurement.json").read_text())
    terminal=json.loads((directory/"result.json").read_text())
    if canonical_digest(measured)!=canonical_digest(terminal):raise ValueError("Incomplete case publication")
    return terminal


def prepare(directory:Path) -> dict:
    package=proposal(); directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    _write(directory/"package.json",package)
    return package


def validate(package:dict) -> None:
    if canonical_digest(package)!=canonical_digest(proposal()):raise ValueError("Changed or stale engineering package")


def compare_position_traces(traces:dict,lengths:tuple[int,...]) -> tuple[bool,dict]:
    """Every real position is a gate input, including nonfinal positions."""
    import numpy as np
    arrays={};same=True
    if any(len(traces[name])!=len(lengths) for name in ("reference","candidate")):
        raise ValueError("Incomplete real-position lane trace")
    for lane,n in enumerate(lengths):
        rt,ct=traces["reference"][lane],traces["candidate"][lane]
        if len(rt)!=n or len(ct)!=n:raise ValueError("Incomplete real-position trace")
        for index,(r,c) in enumerate(zip(rt,ct,strict=True)):
            if len(r)!=2 or len(c)!=2:raise ValueError("Hidden state and logits required")
            for kind,(x,y) in enumerate(zip(r,c,strict=True)):
                if x.ndim!=1 or x.shape!=y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():
                    raise ValueError("Invalid intermediate real-position trace")
                arrays[f"position_reference_{lane}_{index}_{kind}"]=x
                arrays[f"position_candidate_{lane}_{index}_{kind}"]=y
            same &= int(r[1].argmax())==int(c[1].argmax())
    return same,arrays


def budget_envelope(*,prior_total_usd:float,hourly_usd:float,noncompute_usd:float,
                    elapsed_hours:float=4.) -> dict:
    values=(prior_total_usd,hourly_usd,noncompute_usd,elapsed_hours)
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in values):
        raise ValueError("Finite nonnegative financial inputs required")
    additional=hourly_usd*elapsed_hours+noncompute_usd
    return {"proposed_additional_usd":additional,"proposed_cumulative_usd":prior_total_usd+additional,
        "fits_proposal":bool(0<hourly_usd<=1.6 and elapsed_hours<=4. and additional<=8.
                            and prior_total_usd+additional<=100.),"approved":False}


class CheckedBackend:
    def __init__(self,backend,check:Callable[[],None]):self.backend,self.check=backend,check
    def __getattr__(self,name):
        value=getattr(self.backend,name)
        if not callable(value):return value
        def call(*a,**kw):
            self.check();out=value(*a,**kw);self.check();return out
        return call


def _material(profile):
    return tasks.make_episodes(2,stage=f"performance_only_20261014_{profile}",seed=208741)


def _identity(package,backend,profile,case,episodes,spec,text_ids):
    neutral_case=case in ("baseline_fixture","calibration_fixture")
    fields=neutral.KEY_FIELDS if neutral_case else analysis.KEY_FIELDS
    keys=[sorted(neutral.expected_keys(ep,profile,spec.gain) if neutral_case else
                 analysis.expected_keys(ep.episode_id,profile,text=ep.episode_id in text_ids)) for ep in episodes]
    return {"package_sha256":canonical_digest(package),"model_identity":backend.model_identity,
        "case":case,"profile":profile,"cohort":[ep.episode_id for ep in episodes],"runtime":asdict(spec),
        "text_ids":list(text_ids),"material_sha256":canonical_digest([
            neutral.episode_to_dict(ep) if neutral_case else tasks.episode_to_dict(ep) for ep in episodes]),
        "key_fields":list(fields),"lane_keys":[[list(k) for k in lane] for lane in keys],
        "scientific_data":False,"scientific_admission":False}


def run_case(directory:Path,package:dict,backend,profile:str,case:str,*,
             hardware_authorized:bool=False,check:Callable[[],None]|None=None) -> dict:
    """One explicitly selected case. Caller must inspect prior stage receipts.

    This callable has no automatic next-case or formal-run path. The caller owns
    operator/micro admission, fresh finance/lease protection and actual shutdown.
    """
    validate(package)
    if hardware_authorized is not True or not callable(check):raise PermissionError("Fresh external hardware authority/check required")
    from mb.v6_batch_native import PackedBackend
    if (type(backend) is not PackedBackend or profile not in PROFILES or backend.tokens.profile_key!=profile
            or backend.chunk!=16 or backend.prefix_capacity!=4096 or case not in CASES):
        raise ValueError("Unbound backend/profile/case")
    directory=Path(directory)
    if directory.exists():raise FileExistsError(directory)
    check();directory.mkdir(parents=False,exist_ok=False)
    def event(value):
        with (directory/"journal.jsonl").open("a") as f:
            f.write(json.dumps({"monotonic":time.monotonic(),**value},sort_keys=True,allow_nan=False)+"\n")
            f.flush();os.fsync(f.fileno())
    try:
        import torch
        guarded=CheckedBackend(backend,check)
        spec=RuntimeSpec(**package["short_runtime" if case=="short_repeat" else "runtime"])
        episodes=_material(profile);texts=(episodes[0].episode_id,)
        neutral_case=case in ("baseline_fixture","calibration_fixture")
        if neutral_case:
            stage="baseline" if case=="baseline_fixture" else "calibration"
            spec=replace(spec,gain=0. if stage=="baseline" else 1.)
            episodes=neutral.make_episodes(2,stage,seed=208742 if stage=="baseline" else 208743,
                namespace=f"performance_only_20261014_{profile}");texts=()
        identity=_identity(package,backend,profile,case,episodes,spec,texts)
        receipt=CohortReceipt(directory/"cohort",identity)
        def sink(row):
            # Preserve each completed row if a later operation or deadline fails.
            with (directory/"partial_records.jsonl").open("a") as f:
                f.write(json.dumps({**row,"engineering_only":True},sort_keys=True,allow_nan=False)+"\n")
                f.flush();os.fsync(f.fileno())
        writers=[]
        if not neutral_case:
            for lane in range(len(episodes)):
                writers.append(NativeArchiveWriter(directory/f"archives-{lane}",backend,identity))
        if neutral_case:
            runner=NeutralCohortRunner(guarded,spec,profile,episodes,sinks=(sink,)*2)
        else:
            runner=CohortRunner(guarded,spec,profile,episodes,text_ids=texts,sinks=(sink,)*2,artifact_sinks=writers)
        event({"phase":"compute_start","case":case});check();torch.cuda.synchronize()
        start=time.monotonic();records=runner.run();torch.cuda.synchronize();seconds=time.monotonic()-start
        event({"phase":"compute_complete","seconds":seconds});check()
        receipt.complete(records)
        for lane,writer in enumerate(writers):
            for name in writer.index:
                check()
                writer.load(name)
                event({"phase":"archive_restored","lane":lane,"name":name})
                check()
            check()
            NativeArchiveWriter(writer.directory,backend,identity,resume=True)
            event({"phase":"archive_inventory_reopened","lane":lane})
            check()
        reopened=CohortReceipt(directory/"cohort",identity,resume=True)
        if reopened.result!=json.loads(json.dumps(records)):raise ValueError("No-op reopened records differ")
        if case=="short_repeat":
            repeated=CohortRunner(guarded,spec,profile,episodes,text_ids=texts).run()
            if repeated!=records:raise ValueError("Same-cohort repeated full schedule differs")
        elapsed=time.monotonic()-start
        result={"version":VERSION,"status":"engineering_case_complete_not_admitted","profile":profile,"case":case,
            "package_sha256":canonical_digest(package),"model_identity":backend.model_identity,
            "episodes":len(episodes),"compute_seconds_including_archive_writes":seconds,
            "case_seconds_including_restore_checks":elapsed,"records":sum(map(len,records)),
            "exact_same_backend_replay":not neutral_case,"native_archive_restore_verified":not neutral_case,
            "record_noop_resume_verified":True,"scientific_admission":False,
            "bytes_before_result":sum(p.stat().st_size for p in directory.rglob('*') if p.is_file())}
        event({"phase":"measurement_ready"})
        return _publish_result(directory,result,check)
    except BaseException as exc:
        event({"phase":"failed","error_type":type(exc).__name__,"message":str(exc)})
        _write(directory/"failure.json",{"error_type":type(exc).__name__,"message":str(exc),
            "traceback":traceback.format_exc(),"scientific_admission":False,"retry_authorized":False})
        raise


def teacher_forced_micro(directory:Path,package:dict,native,candidate,*,
                         hardware_authorized=False,check=None) -> dict:
    """Common native K/V bytes are rebound only for this labeled engineering test."""
    validate(package)
    if hardware_authorized is not True or not callable(check):raise PermissionError("Fresh external hardware authority required")
    from mb.v6_batch_native import PackedBackend
    from mb.v6_native import NativeBackend,NativeKVPayload,_tensor_hash,_tensor_stamp
    from mb.v6_contract import Export
    if (type(native) is not NativeBackend or type(candidate) is not PackedBackend
            or native.model is not candidate.model or native.weights_digest!=candidate.weights_digest
            or native.tokens.profile_key not in PROFILES or candidate.tokens.profile_key!=native.tokens.profile_key
            or candidate.chunk!=16 or candidate.prefix_capacity!=4096):
        raise ValueError("Same verified fixed weights and declared candidate required")
    directory=Path(directory)
    if directory.exists():raise FileExistsError(directory)
    check();directory.mkdir(exist_ok=False)
    try:
        import torch
        import numpy as np
        texts=("My private beacon is Dim.","My private beacon is Bright. Keep this separate from other records.")
        first=tuple(native.create("Follow your own private record.",t) for t in texts)
        second=tuple(candidate.create("Follow your own private record.",t) for t in texts)
        donor=native.create("Donor fixture.","Another independent beacon is Bright.")
        native_exports=[];candidate_exports=[]
        for _ in range(16):
            check();e=native.step(donor,(),0.);native_exports.append(e)
            layers=tuple(tuple(t.detach().clone() for t in layer) for layer in e.payload.layers)
            tensors=tuple(t for layer in layers for t in layer)
            digest=_tensor_hash({"token":e.token,"position":e.position,"model_identity":candidate.model_identity},tensors)
            payload=NativeKVPayload(layers,e.token,e.position,candidate.model_identity,digest,
                tuple(_tensor_stamp(t) for t in tensors),candidate._owner)
            candidate_exports.append(Export(e.token,e.position,digest,payload))
        token=native.tokenizer.encode(" river",add_special_tokens=False)[0]
        inputs=((token,)*17,(token,)*3);reports=[]
        for gain in package["gains"]:
            check();left=tuple(native.clone(s) for s in first);right=tuple(candidate.clone(s) for s in second)
            nw=(tuple(native_exports),());cw=(tuple(candidate_exports),())
            arrays={};timing={};position_traces={"reference":[[],[]],"candidate":[[],[]]}
            def capture(offset,valid,hidden,logits):
                flags=valid.cpu().tolist()
                for lane,row in enumerate(flags):
                    for index,keep in enumerate(row):
                        if keep:
                            position_traces["candidate"][lane].append((
                                hidden[lane,index].float().cpu().numpy().copy(),
                                logits[lane,index].float().cpu().numpy().copy()))
            for name in (("reference","candidate") if gain in (0.,.5) else ("candidate","reference")):
                torch.cuda.synchronize();start=time.monotonic()
                if name=="reference":
                    for lane,(s,ids,w) in enumerate(zip(left,inputs,nw)):
                        def capture_native(module,args,result):
                            for hidden in result.last_hidden_state[0]:
                                scores=native.model.lm_head(hidden[None]).float()[0]
                                position_traces["reference"][lane].append((
                                    hidden.float().cpu().numpy().copy(),scores.cpu().numpy().copy()))
                        hook=native.model.model.register_forward_hook(capture_native)
                        try:native._consume(s,ids,w,gain)
                        finally:hook.remove()
                else:candidate.consume_many(right,inputs,cw,gain,trace=capture)
                torch.cuda.synchronize();timing[name]=time.monotonic()-start
                # A lease expiring after a measured phase must not erase its evidence.
                label=str(gain).replace('.','_')
                phase_arrays={f"lane_{lane}_position_{pos}_{kind}":a
                    for lane,trace in enumerate(position_traces[name])
                    for pos,pair in enumerate(trace) for kind,a in enumerate(pair)}
                with (directory/f"gain-{label}-{name}-positions.npz").open("xb") as f:
                    np.savez(f,**phase_arrays);f.flush();os.fsync(f.fileno())
                _write(directory/f"gain-{label}-{name}-phase.json",{
                    "phase":name,"seconds_including_trace_capture":timing[name],
                    "positions_by_lane":[len(t) for t in position_traces[name]],"scientific_admission":False})
                check()
            differences=[]
            same_tokens,position_arrays=compare_position_traces(position_traces,tuple(map(len,inputs)))
            arrays.update(position_arrays)
            for lane,(a,b) in enumerate(zip(left,right)):
                aa=(a.last_hidden,a.native_logits,*tuple(t for layer in a.cache.layers for t in (layer.keys,layer.values)))
                bb=(b.last_hidden,b.native_logits,*tuple(t for layer in b.cache.layers for t in (layer.keys,layer.values)))
                if a.consumed_tokens!=b.consumed_tokens:raise ValueError("Teacher-forced history differs")
                for index,(x,y) in enumerate(zip(aa,bb,strict=True)):
                    if x.shape!=y.shape or x.dtype!=y.dtype:raise ValueError("Teacher-forced layout/precision differs")
                    rx=x.float().cpu().numpy();cy=y.float().cpu().numpy()
                    if not np.isfinite(rx).all() or not np.isfinite(cy).all():raise ValueError("Nonfinite teacher-forced trace")
                    arrays[f"reference_{lane}_{index}"]=rx;arrays[f"candidate_{lane}_{index}"]=cy
                    differences.append({"lane":lane,"tensor":index,"max_abs":float(np.abs(rx-cy).max()),
                        "exact_bytes":bool(torch.equal(x.view(torch.uint8),y.view(torch.uint8)))})
                same_tokens &= int(a.native_logits.argmax())==int(b.native_logits.argmax())
            label=str(gain).replace('.','_')
            with (directory/f"gain-{label}.npz").open("xb") as f:
                np.savez(f,**arrays);f.flush();os.fsync(f.fileno())
            report={"gain":gain,"same_greedy_tokens_at_every_real_position":same_tokens,
                "real_positions_compared":sum(map(len,inputs)),"tensor_differences":differences,
                "timing_seconds_including_first_compile_if_any":timing,"common_donor_bytes":True,
                "scientific_equivalence":False}
            _write(directory/f"gain-{label}.json",report);reports.append(report);check()
            if not same_tokens:raise ValueError("Teacher-forced greedy disagreement: retain and review; do not proceed")
        result={"status":"micro_engineering_complete_not_admitted","reports":reports,
            "package_sha256":canonical_digest(package),"weights_sha256":native.weights_digest,
            "scientific_admission":False,"full_model_tolerance_adopted":False}
        return _publish_result(directory,result,check)
    except BaseException as exc:
        _write(directory/"failure.json",{"error_type":type(exc).__name__,"message":str(exc),
            "traceback":traceback.format_exc(),"retry_authorized":False})
        raise
