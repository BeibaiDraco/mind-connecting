"""Engineering fixtures for unchanged neutral workloads in fixed cohorts.

Collection only; no parameter selection, scientific gates, or continuation.
"""
from __future__ import annotations
from dataclasses import asdict, replace
import hashlib
from mb import v6_neutral as neutral
from mb import v6_tasks as tasks
from mb.v6_batch import CohortRunner
from mb.v6_contract import canonical_digest
from mb.v6_runtime import PairState


class NeutralCohortRunner:
    def __init__(self,backend,spec,profile,episodes,*,sinks=None):
        self.episodes=tuple(episodes)
        if not self.episodes or len({ep.stage for ep in self.episodes})!=1:
            raise ValueError("One declared neutral stage per fixed cohort")
        neutral._gain(self.episodes[0].stage,spec.gain)
        self.backend,self.spec,self.profile=backend,spec,profile
        self.engine=CohortRunner(backend,spec,profile,tuple(ep.task for ep in episodes))
        self.records=[[] for _ in episodes]
        self.sinks=sinks or (None,)*len(episodes)
        if len(self.sinks)!=len(episodes): raise ValueError("Neutral sink mismatch")
        self.started=False

    def read(self,pairs,held,stream,policy,qid):
        states=self.engine.states(pairs); windows=self.engine.windows(held)
        qs=tuple(neutral.question(ep,stream,pair.world,side,qid)
                 for ep,pair in zip(self.episodes,pairs) for side in (0,1))
        guard=self.backend.guard(states)
        probes=self.backend.probe_many(states,tuple(q.text for q in qs),self.spec.choice_labels,windows,self.spec.gain)
        if len(probes)!=len(qs): raise RuntimeError("Incomplete neutral probe batch")
        for p in probes: p.validate()
        guard.verify(); choices=[]
        for lane,(ep,pair) in enumerate(zip(self.episodes,pairs)):
            for side in (0,1):
                q,p=qs[2*lane+side],probes[2*lane+side]
                choice=q.candidates[p.token_ids.index(p.token)] if p.token in p.token_ids else None
                choices.append(choice)
                row={"contract":neutral.CONTRACT,"proposal_status":neutral.STATUS,"episode_id":ep.episode_id,
                    "model_profile":self.profile,"stage":ep.stage,"gain":self.spec.gain,
                    "stream":stream,"policy":policy,"round_id":pair.world.round_id,"side":side,"qid":qid,
                    "status":"ok","choice":choice,"correct_choice":q.correct,"correct":choice==q.correct,
                    "candidate_map":list(q.candidates),"cap_item_id":q.cap_item_id,
                    "material_sha256":canonical_digest(neutral.episode_to_dict(ep)),
                    "question_sha256":hashlib.sha256(q.text.encode()).hexdigest(),"world":asdict(pair.world),
                    "top_token":p.token,"top_probability":p.probability,"legal_logits":list(p.legal_logits),
                    "legal_mass":p.legal_mass,"token_ids":list(p.token_ids)}
                if getattr(self.backend,"kind",None)=="synthetic_fixture":
                    row.update(backend_kind="synthetic_fixture",scientific_data=False)
                self.records[lane].append(row)
                if self.sinks[lane]: self.sinks[lane](row)
        return probes,tuple(choices)

    def round_reads(self,pairs,held,stream,policy):
        continuation="continuation_action" if stream=="capability" else "continuation_fact"
        for qid in neutral.qids(self.episodes[0].stage,stream):
            if qid!=continuation: self.read(pairs,held,stream,policy,qid)
        probes,choices=self.read(pairs,held,stream,policy,continuation)
        states=self.backend.commit_many(probes,self.engine.windows(held),self.spec.gain)
        if len(states)!=2*len(pairs): raise RuntimeError("Incomplete neutral commitment")
        for lane,p in enumerate(pairs): p.models=tuple(states[2*lane:2*lane+2])
        return tuple(tuple(choices[2*i:2*i+2]) for i in range(len(pairs)))

    def run(self):
        if self.started: raise RuntimeError("Neutral cohort cannot restart")
        self.started=True
        for policy in neutral.policies(self.episodes[0].stage):
            pairs=self.engine.initialize()
            for r in range(1,7):
                self.engine.prepare(pairs,r)
                _,held=self.engine.work(pairs,policy)
                answers=self.round_reads(pairs,held,"capability",policy)
                for pair,choices in zip(pairs,answers): pair.world=tasks.transition(pair.world,choices)
            system,users=neutral.fact_initial_prompts()
            pairs=tuple(PairState(tuple(self.backend.create(system,u) for u in users),neutral.FactWorld())
                        for _ in self.episodes)
            for pair in pairs:
                for state in pair.models:
                    for _ in range(self.spec.preparation_tokens): self.backend.step(state,(),0.)
                    self.backend.finish_turn(state)
            for r in range(1,7):
                for ep,pair in zip(self.episodes,pairs):
                    pair.world=replace(pair.world,round_id=r);pair.windows=((),())
                    for state,text in zip(pair.models,neutral.fact_round_prompts(ep,r)):
                        self.backend.begin_user(state,text)
                _,held=self.engine.work(pairs,policy)
                answers=self.round_reads(pairs,held,"fact",policy)
                for pair,choices in zip(pairs,answers): pair.world=replace(pair.world,answers=(*pair.world.answers,choices))
        for ep,records in zip(self.episodes,self.records):
            neutral.validate_records(records,[ep],self.profile,self.spec.gain)
        return tuple(self.records)
