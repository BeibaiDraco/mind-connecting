"""Fixed-cohort engineering scheduler; the original scalar runner is the oracle.

Every operation has fixed episode/side lane order. No grouping by answers,
runtime length, effect, significance or completion speed. No launch authority.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path

from mb.v6_contract import canonical_digest
from mb.v6_runtime import EpisodeRunner, PairState, RoundTape, POLICIES, GOAL_QIDS
from mb import v6_tasks as tasks

VERSION = "v6-fixed-cohort-scheduler-1"


class _HashGuard:
    def __init__(self,backend,states):
        self.backend,self.states=backend,states
        self.before=tuple(backend.digest(s) for s in states)
    def verify(self):
        if tuple(self.backend.digest(s) for s in self.states)!=self.before:
            raise RuntimeError("Protected readout mutated continuing state")


class SerialBatchAdapter:
    """Offline semantic oracle; not a performance claim or model loader."""
    def __init__(self,backend): self.backend=backend
    def __getattr__(self,name): return getattr(self.backend,name)
    def guard(self,states): return _HashGuard(self.backend,states)
    def step_many(self,states,windows,gain):
        return tuple(self.backend.step(s,w,gain) for s,w in zip(states,windows,strict=True))
    def probe_many(self,states,questions,labels,windows,gain):
        return tuple(self.backend.probe(s,q,labels,w,gain) for s,q,w in zip(states,questions,windows,strict=True))
    def commit_many(self,probes,windows,gain):
        return tuple(self.backend.commit_answer(p,w,gain) for p,w in zip(probes,windows,strict=True))


class CohortRunner:
    def __init__(self,backend,spec,profile,episodes,*,text_ids=(),sinks=None,artifact_sinks=None):
        self.episodes=tuple(episodes); self.text_ids=tuple(text_ids)
        ids=tuple(ep.episode_id for ep in self.episodes)
        if (not ids or len(ids)>4 or len(set(ids))!=len(ids) or len(set(text_ids))!=len(text_ids)
                or not set(text_ids)<=set(ids)):
            raise ValueError("One to four fixed distinct episodes and declared TEXT subset required")
        self.backend,self.spec,self.profile=backend,spec,profile
        self.identity={"version":VERSION,"episodes":ids,"text_ids":self.text_ids,
            "runtime":asdict(spec),"profile":profile,"lane_order":"episode_then_A_B",
            "question_order":GOAL_QIDS,"shape_rule":"fixed_lanes_right_packed_prefix_and_query",
            "scientific_admission":False}
        sinks=sinks or (None,)*len(ids); artifact_sinks=artifact_sinks or (None,)*len(ids)
        if len(sinks)!=len(ids) or len(artifact_sinks)!=len(ids): raise ValueError("Sink lane mismatch")
        self.runners=tuple(EpisodeRunner(backend,spec,profile,sink=s,artifact_sink=a)
            for s,a in zip(sinks,artifact_sinks))
        for runner,ep in zip(self.runners,self.episodes): runner._episode_id=ep.episode_id
        self.started=False

    @staticmethod
    def states(pairs): return tuple(s for pair in pairs for s in pair.models)
    @staticmethod
    def windows(held): return tuple(w for pair in held for w in pair)

    def initialize(self):
        return tuple(r.initialize(ep) for r,ep in zip(self.runners,self.episodes))

    def prepare(self,pairs,round_id,**kwargs):
        for r,ep,pair in zip(self.runners,self.episodes,pairs): r.prepare(ep,pair,round_id,**kwargs)

    def work(self,pairs,policy,*,tapes=None,focals=None):
        if policy not in (*POLICIES,"L","Fcut","Rcut","Replay"): raise ValueError("Unknown policy")
        n=len(pairs)
        tapes=tapes or (None,)*n; focals=focals or (None,)*n
        if n!=len(self.runners) or len(tapes)!=n or len(focals)!=n: raise ValueError("Work lane mismatch")
        parents=tuple(r.digest(p) for r,p in zip(self.runners,pairs))
        if policy=="FRESH":
            shadows=tuple(r.clone(p) for r,p in zip(self.runners,pairs))
            tapes,_=self.work(shadows,"OFF")
            if tuple(r.digest(p) for r,p in zip(self.runners,pairs))!=parents:
                raise RuntimeError("Shadow contaminated actual cohort")
            for r,t,p in zip(self.runners,tapes,pairs): r.archive("tape",t,f"fresh_round{p.world.round_id}")
        entries=[[[],[]] for _ in pairs]
        for tick in range(self.spec.work_tokens):
            incoming=tuple(tuple(r._incoming(p,policy,s,tick,t,f) for s in (0,1))
                for r,p,t,f in zip(self.runners,pairs,tapes,focals))
            outgoing=self.backend.step_many(self.states(pairs),self.windows(incoming),self.spec.gain)
            if len(outgoing)!=2*n: raise RuntimeError("Incomplete cohort publication")
            for lane in range(n):
                for side in (0,1):
                    export=outgoing[2*lane+side]
                    if entries[lane][side] and export.position<=entries[lane][side][-1].position:
                        raise RuntimeError("Export position did not advance")
                    entries[lane][side].append(export)
            # No new window is visible until every lane's output has validated.
            for lane,(r,pair) in enumerate(zip(self.runners,pairs)):
                pair.windows=tuple(tuple(row[-self.spec.window:]) for row in entries[lane])
                r.audit.append({"round_id":pair.world.round_id,"policy":policy,"tick":tick,
                    "incoming":[[e.identity() for e in w] for w in incoming[lane]]})
        held=tuple(tuple(r._incoming(p,policy,s,self.spec.work_tokens,t,f) for s in (0,1))
            for r,p,t,f in zip(self.runners,pairs,tapes,focals))
        result=tuple(RoundTape(p.world.round_id,tuple(tuple(row) for row in e),parent)
            for p,e,parent in zip(pairs,entries,parents))
        return result,held

    def reads(self,pairs,held,qid,checkpoint):
        states=self.states(pairs)
        questions=tuple(tasks.question(ep,p.world,s,qid,checkpoint=checkpoint or None)
            for ep,p in zip(self.episodes,pairs) for s in (0,1))
        guard=self.backend.guard(states)
        probes=self.backend.probe_many(states,tuple(q.text for q in questions),self.spec.choice_labels,
                                       self.windows(held),self.spec.gain)
        if len(probes)!=len(states): raise RuntimeError("Incomplete readout cohort")
        for probe in probes: probe.validate()
        guard.verify()
        return tuple((q,p,q.candidates[p.token_ids.index(p.token)] if p.token in p.token_ids else None)
                     for q,p in zip(questions,probes))

    def actions(self,pairs,held,metas,*,candidates=None,access=False):
        reads=self.reads(pairs,held,"action",metas[0]["checkpoint"])
        if access:
            diagnostics=self.reads(pairs,held,"partner_beacon",0)
            for lane,(r,ep,pair,meta) in enumerate(zip(self.runners,self.episodes,pairs,metas)):
                for side in (0,1): r.emit(ep,pair,side,*diagnostics[2*lane+side],meta)
        for lane,(r,ep,pair,meta) in enumerate(zip(self.runners,self.episodes,pairs,metas)):
            for side in (0,1):
                r.emit(ep,pair,side,*reads[2*lane+side],meta,
                       candidates[lane].get(side) if candidates else None)
        committed=self.backend.commit_many(tuple(row[1] for row in reads),self.windows(held),self.spec.gain)
        if len(committed)!=2*len(pairs): raise RuntimeError("Incomplete answer commitment")
        for lane,pair in enumerate(pairs):
            pair.models=tuple(committed[2*lane:2*lane+2])
            pair.world=tasks.transition(pair.world,tuple(reads[2*lane+s][2] for s in (0,1)))

    def natural(self,policy):
        pairs=self.initialize(); checkpoints={}
        for round_id in range(1,7):
            if policy=="LIVE" and round_id in (2,3,5,6):
                saved=tuple(r.clone(p) for r,p in zip(self.runners,pairs)); checkpoints[round_id]=saved
                for r,p in zip(self.runners,saved): r.archive("pair",p,f"live_before_round{round_id}")
            self.prepare(pairs,round_id); _,held=self.work(pairs,policy)
            meta={"kind":"natural","policy":policy,"checkpoint":0,"arm":policy,"version":1}
            self.actions(pairs,held,tuple(meta.copy() for _ in pairs),access=True)
        return checkpoints

    def pulses(self,parents,checkpoint):
        focals=tuple(tasks.focal_side(ep,checkpoint) for ep in self.episodes)
        fixed=tuple(tasks.pulse_candidates(ep,p.world,checkpoint) for ep,p in zip(self.episodes,parents))
        original=tuple(r.digest(p) for r,p in zip(self.runners,parents)); reference={}; reference_end=None
        for arm in ("L","Fcut","Rcut","Replay"):
            for version in (0,1):
                pairs=tuple(r.clone(p) for r,p in zip(self.runners,parents))
                for round_id in (checkpoint,checkpoint+1):
                    self.prepare(pairs,round_id,pulse=bool(version) if round_id==checkpoint else None)
                    tapes,held=self.work(pairs,arm,tapes=reference.get(round_id),focals=focals)
                    if arm=="L" and version==0:
                        reference[round_id]=tapes
                        for r,t in zip(self.runners,tapes): r.archive("tape",t,f"pulse{checkpoint}_q0_round{round_id}")
                    metas=tuple({"kind":"pulse","policy":"LIVE","checkpoint":checkpoint,
                        "arm":arm,"version":version,"focal_side":f} for f in focals)
                    candidates=tuple({1-f if round_id==checkpoint else f:
                        data["responder" if round_id==checkpoint else "initiator"]} for f,data in zip(focals,fixed))
                    self.actions(pairs,held,metas,candidates=candidates)
                end=tuple(r.digest(p) for r,p in zip(self.runners,pairs))
                if arm=="L" and version==0: reference_end=end
                if arm=="Replay" and version==0 and end!=reference_end:
                    raise RuntimeError("Unchanged cohort two-round Replay differs")
        if tuple(r.digest(p) for r,p in zip(self.runners,parents))!=original:
            raise RuntimeError("Pulse branch contaminated parent")

    def goals(self,parents,checkpoint):
        focals=tuple(tasks.focal_side(ep,checkpoint) for ep in self.episodes)
        candidates=[]
        for ep,p,f in zip(self.episodes,parents,focals):
            row=ep.transfer_rows[0 if checkpoint==3 else 1]
            candidates.append((row[p.world.goals[f]],row[ep.probe_goals[0 if checkpoint==3 else 1]]))
        original=tuple(r.digest(p) for r,p in zip(self.runners,parents)); reference=None; saved=None
        for arm in ("L","Fcut","Replay"):
            for version in (0,1):
                pairs=tuple(r.clone(p) for r,p in zip(self.runners,parents))
                self.prepare(pairs,checkpoint,goal_changed=bool(version))
                tapes,held=self.work(pairs,arm,tapes=reference,focals=focals)
                if arm=="L" and version==0:
                    reference=tapes
                    for r,t in zip(self.runners,tapes): r.archive("tape",t,f"goal{checkpoint}_q0")
                reads={qid:self.reads(pairs,held,qid,checkpoint) for qid in GOAL_QIDS}
                observed=[]
                for lane,(r,ep,pair,f) in enumerate(zip(self.runners,self.episodes,pairs,focals)):
                    meta={"kind":"goal","policy":"LIVE","checkpoint":checkpoint,
                          "arm":arm,"version":version,"focal_side":f}
                    for side in (0,1):
                        for qid in GOAL_QIDS:
                            q,p,choice=reads[qid][2*lane+side]
                            r.emit(ep,pair,side,q,p,choice,meta,candidates[lane] if qid=="transfer_action" else None)
                            observed.append((p.token,p.legal_logits,p.legal_mass))
                if arm=="L" and version==0: saved=observed
                if arm=="Replay" and version==0 and observed!=saved:
                    raise RuntimeError("Unchanged cohort goal Replay differs")
        if tuple(r.digest(p) for r,p in zip(self.runners,parents))!=original:
            raise RuntimeError("Goal branch contaminated parent")

    def run(self):
        if self.started: raise RuntimeError("A cohort object cannot be restarted")
        self.started=True
        checkpoints=self.natural("LIVE")
        for policy in POLICIES[1:]: self.natural(policy)
        for cp in (2,5): self.pulses(checkpoints[cp],cp)
        for cp in (3,6): self.goals(checkpoints[cp],cp)
        # TEXT membership and order are predeclared; its scheduler stays scalar.
        for r,ep in zip(self.runners,self.episodes):
            if ep.episode_id in self.text_ids: r.natural(ep,"TEXT")
            if len(r.records)!=328+(24 if ep.episode_id in self.text_ids else 0):
                raise RuntimeError("Cohort record coverage differs")
        return tuple(r.records for r in self.runners)


class CohortReceipt:
    """Record-only receipt; native artifact verification is a separate prerequisite."""
    def __init__(self,directory:Path,identity:dict,*,resume=False):
        self.directory=Path(directory); self.identity=json.loads(json.dumps(identity))
        fields=self.identity.get("key_fields")
        expected=self.identity.get("lane_keys")
        if (type(fields) is not list or not fields or len(set(fields))!=len(fields)
                or not all(type(f) is str for f in fields) or type(expected) is not list or not expected
                or any(type(lane) is not list or not lane for lane in expected)
                or any(type(key) is not list or len(key)!=len(fields) for lane in expected for key in lane)
                or any(len({canonical_digest(key) for key in lane})!=len(lane) for lane in expected)):
            raise ValueError("Expected unique per-lane record keys must be bound before execution")
        if resume:
            if canonical_digest(json.loads((self.directory/"identity.json").read_text()))!=canonical_digest(self.identity):
                raise ValueError("Cohort identity changed before resume")
            result=json.loads((self.directory/"complete.json").read_text())
            if (set(result)!={"records_sha256","identity_sha256","scientific_admission"}
                    or result["identity_sha256"]!=canonical_digest(self.identity)
                    or result["scientific_admission"] is not False):
                raise ValueError("Completion identity/schema changed")
            raw=(self.directory/"records.json").read_bytes()
            import hashlib
            if hashlib.sha256(raw).hexdigest()!=result["records_sha256"]:
                raise ValueError("Completed cohort bytes changed")
            self.result=json.loads(raw); self._coverage(self.result); self.closed=True
        else:
            self.directory.mkdir(exist_ok=False,parents=False)
            self._new("identity.json",self.identity); self.closed=False; self.result=None

    def _new(self,name,value):
        with (self.directory/name).open("x") as f:
            json.dump(value,f,sort_keys=True,allow_nan=False); f.flush(); os.fsync(f.fileno())

    def complete(self,records):
        if self.closed: raise RuntimeError("Completed cohort is immutable")
        import hashlib
        self._coverage(records)
        self._new("records.json",records)
        self._new("complete.json",{"records_sha256":hashlib.sha256((self.directory/"records.json").read_bytes()).hexdigest(),
                                   "identity_sha256":canonical_digest(self.identity),"scientific_admission":False})
        self.closed=True; self.result=records

    def _coverage(self,records):
        if type(records) not in (tuple,list) or len(records)!=len(self.identity["lane_keys"]):
            raise ValueError("Cohort record lane coverage differs")
        for rows,expected in zip(records,self.identity["lane_keys"]):
            keys=[]
            for row in rows:
                if type(row) is not dict or any(k not in row for k in self.identity["key_fields"]):
                    raise ValueError("Missing record key field")
                keys.append(canonical_digest([row[k] for k in self.identity["key_fields"]]))
            if len(keys)!=len(set(keys)) or set(keys)!={canonical_digest(k) for k in expected}:
                raise ValueError("Cohort record key coverage differs")
