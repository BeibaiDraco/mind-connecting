"""Unadmitted fixed-lane V6 CUDA backend with private ragged packing.

Padding is scratch storage only: masked from attention, excluded from finite
checks for real inputs, removed before state publication. Never runner-selected.
"""
from __future__ import annotations

import contextvars
from dataclasses import dataclass, field, replace
import math
from typing import Any
import numpy as np

from mb.v6_contract import Export, Probe, canonical_digest
from mb.v6_native import NativeBackend, NativeState, NativeKVPayload, _tensor_hash, _tensor_stamp
from mb.v6_state_guard import DeviceStateGuard

VERSION = "v6-fixed-cohort-engineering-1"
NAME = "mb_v6_fixed_cohort_engineering"
CONTEXT = contextvars.ContextVar("v6_fixed_cohort", default=None)


@dataclass(frozen=True)
class PackedLayout:
    prefixes: tuple[int, ...]
    inputs: tuple[int, ...]
    windows: tuple[int, ...]
    offset: int
    count: int
    gain: float
    prefix_capacity: int | None = None
    window_capacity: int | None = None

    def __post_init__(self):
        if (not self.prefixes or not len(self.prefixes) == len(self.inputs) == len(self.windows)
                or any(type(xs) is not tuple for xs in (self.prefixes, self.inputs, self.windows))
                or any(type(x) is not int or x < 0 for xs in (self.prefixes, self.inputs, self.windows) for x in xs)
                or any(p+n == 0 for p, n in zip(self.prefixes, self.inputs))
                or any(w > 16 for w in self.windows)
                or type(self.offset) is not int or self.offset < 0
                or type(self.count) is not int or self.count <= 0
                or self.offset >= max(self.inputs)
                or (self.prefix_capacity is not None and (type(self.prefix_capacity) is not int
                    or self.prefix_capacity < max(self.prefixes)))
                or (self.window_capacity is not None and (type(self.window_capacity) is not int
                    or not max(self.windows) <= self.window_capacity <= 16))
                or type(self.gain) not in (float, int) or not math.isfinite(self.gain) or self.gain < 0):
            raise ValueError("Invalid fixed packed layout")

    @property
    def prefix(self): return self.prefix_capacity if self.prefix_capacity is not None else max(self.prefixes)

    @property
    def own(self): return self.prefix+self.offset+self.count

    @property
    def foreign(self):
        return self.window_capacity if self.window_capacity is not None else (max(self.windows) if self.gain else 0)

    def masks(self) -> tuple[np.ndarray, np.ndarray]:
        """Physical key visibility; padding never becomes a logical token."""
        key = np.arange(self.own)
        allowed = np.zeros((len(self.prefixes), self.count, self.own+self.foreign), dtype=bool)
        valid = np.zeros((len(self.prefixes), self.count), dtype=bool)
        for lane, (prefix, size, window) in enumerate(zip(self.prefixes, self.inputs, self.windows)):
            for q in range(self.count):
                logical = self.offset+q
                valid[lane, q] = logical < size
                allowed[lane, q, :self.own] = ((key < prefix) | ((key >= self.prefix)
                    & (key < self.prefix+size) & (key <= self.prefix+logical)))
                if self.foreign and self.gain:
                    allowed[lane, q, self.own:self.own+window] = True
                if not valid[lane, q]:
                    allowed[lane, q] = False
                    allowed[lane, q, 0 if prefix else self.prefix] = True
        return allowed, valid


def packed_oracle(layout: PackedLayout, arrays: tuple[np.ndarray, ...]) -> np.ndarray:
    """Independent scalar oracle using logical indices, not masks()."""
    q, k, v, fk, fv = (np.asarray(x, dtype=np.float64) for x in arrays)
    b, h, t, d = q.shape
    if (b != len(layout.prefixes) or t != layout.count or k.shape != v.shape
            or k.shape[0] != b or k.shape[2:] != (layout.own, d)
            or fk.shape != fv.shape or fk.shape != (b, k.shape[1], layout.foreign, d)
            or h % k.shape[1]):
        raise ValueError("Oracle shape mismatch")
    out = np.zeros_like(q)
    for lane in range(b):
        for head in range(h):
            kh = head // (h//k.shape[1])
            for qi in range(t):
                n = layout.offset+qi
                if n >= layout.inputs[lane]: continue
                indexes = list(range(layout.prefixes[lane])) + list(range(layout.prefix, layout.prefix+n+1))
                scores, values = [], []
                for index in indexes:
                    scores.append(sum(q[lane,head,qi,j]*k[lane,kh,index,j] for j in range(d))/math.sqrt(d))
                    values.append(v[lane,kh,index])
                if layout.gain:
                    for index in range(layout.windows[lane]):
                        scores.append(sum(q[lane,head,qi,j]*fk[lane,kh,index,j] for j in range(d))/math.sqrt(d)+math.log(layout.gain))
                        values.append(fv[lane,kh,index])
                weights = np.exp(np.array(scores)-max(scores)); weights /= weights.sum()
                for j in range(d):
                    out[lane,head,qi,j] = sum(w*x[j] for w,x in zip(weights,values))
    return out


@dataclass
class _Context:
    backend: Any
    layout: PackedLayout
    foreign: tuple
    allowed: Any
    valid: Any
    seen: set[int] = field(default_factory=set)
    mask_checks: list = field(default_factory=list)


def _attention(module, query, key, value, attention_mask, dropout=0., scaling=None, **kwargs):
    import torch
    c = CONTEXT.get()
    if c is None: raise RuntimeError("Packed attention outside owned context")
    index = c.backend.modules.get(id(module))
    if index is None or index in c.seen or dropout or (scaling is not None and scaling != query.shape[-1]**-.5):
        raise ValueError("Unsupported/repeated packed attention")
    c.seen.add(index)
    if key.shape[-2] != c.layout.own:
        raise ValueError("Packed own cache length differs")
    if attention_mask is not None:
        if attention_mask.ndim != 4 or tuple(attention_mask.shape[-2:]) != (c.layout.count,c.layout.own):
            raise ValueError("Unexpected native own-mask layout")
        expected = c.allowed[:,None,:,:c.layout.own]
        if attention_mask.dtype == torch.bool:
            correct=attention_mask==expected
        elif attention_mask.is_floating_point():
            excluded=torch.isneginf(attention_mask) | (attention_mask==torch.finfo(attention_mask.dtype).min)
            correct=torch.where(expected,attention_mask==0,excluded)
        else:
            raise ValueError("Unsupported own-mask precision")
        c.mask_checks.append((correct | ~c.valid[:,None,:,None]).all())
    if c.foreign:
        fk, fv = c.foreign[index]
        key, value = torch.cat((key,fk),dim=2), torch.cat((value,fv),dim=2)
    bias = torch.zeros(key.shape[2], device=query.device, dtype=torch.float32)
    if c.layout.foreign and c.layout.gain: bias[c.layout.own:] = math.log(c.layout.gain)
    output = c.backend._fused(query.contiguous(),key.contiguous(),value.contiguous(),c.allowed,bias)
    return output.transpose(1,2).contiguous(), None


class PackedBackend(NativeBackend):
    status = "fixed_cohort_engineering_not_admitted"

    def __init__(self, model, tokenizer, *, chunk: int = 16, prefix_capacity: int = 4096,
                 hardware_acceptance_authorized=False):
        if type(chunk) is not int or chunk not in (1,2,4,8,16,32):
            raise ValueError("Invalid fixed chunk")
        if type(prefix_capacity) is not int or not 64 <= prefix_capacity <= 8192:
            raise ValueError("Explicit bounded fixed prefix capacity required")
        super().__init__(model, tokenizer, hardware_acceptance_authorized=hardware_acceptance_authorized)
        import torch
        from torch.nn.attention.flex_attention import flex_attention
        from transformers import AttentionInterface
        from transformers.masking_utils import AttentionMaskInterface, sdpa_mask
        if torch.__version__.split('+')[0] != '2.6.0' or torch.backends.cuda.matmul.allow_tf32:
            raise ValueError("Pinned Torch2.6.0 and disabled matmul TF32 required")
        self.chunk = chunk
        self.prefix_capacity=prefix_capacity
        self.model_identity = canonical_digest({"native":self.model_identity,"version":VERSION,
            "chunk":chunk,"prefix_capacity":prefix_capacity,"foreign_capacity":16,
            "kernel":"compiled_flex","science":False})
        def fused(q,k,v,allowed,bias):
            def score_mod(score,b,h,qi,ki):
                good = (qi < allowed.shape[1]) & (ki < allowed.shape[2])
                visible = allowed[b,qi.clamp(max=allowed.shape[1]-1),ki.clamp(max=allowed.shape[2]-1)]
                return torch.where(good & visible, score+bias[ki.clamp(max=bias.shape[0]-1)], -torch.inf)
            return flex_attention(q,k,v,score_mod=score_mod,enable_gqa=True)
        self._fused = torch.compile(fused, fullgraph=True, dynamic=True)
        AttentionInterface.register(NAME,_attention)
        AttentionMaskInterface.register(NAME,sdpa_mask)

    @classmethod
    def from_local_cache(cls, **kwargs):
        raise PermissionError("Engineering harness with separate authority required")

    def _consume(self, state, ids, foreign=(), gain=0.):
        # Empty initial histories use the unchanged native initialization path.
        if not state.consumed_tokens:
            return super()._consume(state,ids,foreign,gain)
        self.consume_many((state,),(ids,),(foreign,),gain)

    def guard(self, states): return DeviceStateGuard(self,states)

    def step(self, state, foreign, gain):
        return self.step_many((state,),(foreign,),gain)[0]

    def commit_answer(self, probe, foreign, gain):
        return self.commit_many((probe,),(foreign,),gain)[0]

    def consume_many(self, states, inputs, windows, gain, *, decode=False, trace=None):
        import torch
        from transformers import DynamicCache
        if (any(type(x) is not tuple for x in (states,inputs,windows)) or not states
                or not len(states)==len(inputs)==len(windows)
                or len({id(s) for s in states}) != len(states)
                or any(type(x) is not tuple for x in (*inputs,*windows))
                or any(type(i) is not int or not 0 <= i < self.tokens.vocab_size for row in inputs for i in row)):
            raise ValueError("Fixed distinct lanes and immutable valid inputs required")
        for state in states:
            self._check_state(state)
            if type(state) is not NativeState or state.seal is not None or not state.consumed_tokens:
                raise ValueError("Initialized unsealed native states required")
        donor = tuple(self._foreign(w,gain) for w in windows)
        lengths = tuple(len(s.consumed_tokens) for s in states)
        sizes = tuple(map(len,inputs)); count=max(sizes)
        if count == 0: return
        if max(lengths)>self.prefix_capacity or (decode and any(n!=1 for n in sizes)):
            raise ValueError("Frozen prefix capacity or single decode contract exceeded")
        prefix=self.prefix_capacity; foreign=16
        chunk=1 if decode else self.chunk
        copied, merged = [], []
        for layer in range(len(self.modules)):
            kv=[]; fv=[]
            for part,name in enumerate(("keys","values")):
                exemplar=getattr(states[0].cache.layers[layer],name)
                shape=(len(states),exemplar.shape[1],prefix,exemplar.shape[-1])
                buffer=exemplar.new_zeros(shape)
                fbuffer=exemplar.new_zeros((len(states),shape[1],foreign,shape[-1]))
                for lane,state in enumerate(states):
                    buffer[lane:lane+1,:,:lengths[lane]]=getattr(state.cache.layers[layer],name)
                    if donor[lane]: fbuffer[lane:lane+1,:,:len(windows[lane])]=donor[lane][layer][part]
                kv.append(buffer); fv.append(fbuffer)
            copied.append(tuple(kv)); merged.append(tuple(fv))
        cache=DynamicCache(ddp_cache_data=tuple(copied),config=self.model.config)
        last_hidden=[s.last_hidden for s in states]; last_logits=[s.native_logits for s in states]
        with self._lock, torch.no_grad():
            try:
                for offset in range(0,count,chunk):
                    size=chunk
                    layout=PackedLayout(lengths,sizes,tuple(map(len,windows)),offset,size,gain,prefix,foreign)
                    allowed,valid=layout.masks()
                    c=_Context(self,layout,tuple(merged) if foreign else (),
                        torch.as_tensor(allowed,device=self.device),torch.as_tensor(valid,device=self.device))
                    tokens=tuple(tuple((row[offset+i] if offset+i<len(row) else 0) for i in range(size)) for row in inputs)
                    positions=torch.tensor(lengths,device=self.device)[:,None]+offset+torch.arange(size,device=self.device)[None]
                    key_valid=torch.zeros(len(states),layout.own,dtype=torch.long,device=self.device)
                    for lane in range(len(states)):
                        key_valid[lane,:lengths[lane]]=1
                        key_valid[lane,prefix:prefix+min(sizes[lane],offset+size)]=1
                    previous=[cfg._attn_implementation for cfg in self._configs]
                    handle=CONTEXT.set(c)
                    try:
                        for cfg in self._configs: cfg._attn_implementation=NAME
                        result=self.model.model(input_ids=torch.tensor(tokens,device=self.device),
                            attention_mask=key_valid,position_ids=positions,
                            cache_position=torch.arange(prefix+offset,layout.own,device=self.device),
                            past_key_values=cache,use_cache=True)
                        if c.seen != set(range(len(self.modules))): raise RuntimeError("Attention layer bypass")
                        hidden=result.last_hidden_state; logits=self.model.lm_head(hidden).float()
                        finite=(torch.isfinite(hidden).all(-1)&torch.isfinite(logits).all(-1)) | ~c.valid
                        flags=[finite.all(),*c.mask_checks]
                        if not bool(torch.stack(flags).all()): raise ValueError("Nonfinite real input or incorrect own mask")
                        if trace is not None:
                            trace(offset,c.valid,hidden,logits)
                        for lane,n in enumerate(sizes):
                            if offset < n:
                                last=min(n-offset,size)-1
                                last_hidden[lane]=hidden[lane:lane+1,last].detach().clone()
                                last_logits[lane]=logits[lane:lane+1,last].detach().clone()
                    finally:
                        CONTEXT.reset(handle)
                        for cfg,impl in zip(self._configs,previous): cfg._attn_implementation=impl
                updates=[]
                for lane,state in enumerate(states):
                    data=tuple(tuple(torch.cat((getattr(layer,name)[lane:lane+1,:,:lengths[lane]],
                        getattr(layer,name)[lane:lane+1,:,prefix:prefix+sizes[lane]]),dim=2).detach().clone()
                        for name in ("keys","values")) for layer in cache.layers)
                    new=replace(state,cache=DynamicCache(ddp_cache_data=data,config=self.model.config),
                        consumed_tokens=state.consumed_tokens+inputs[lane],last_hidden=last_hidden[lane],native_logits=last_logits[lane])
                    self._check_state(new); updates.append(new)
                for state,new in zip(states,updates):
                    state.cache,state.consumed_tokens,state.last_hidden,state.native_logits=(
                        new.cache,new.consumed_tokens,new.last_hidden,new.native_logits)
            except BaseException:
                for state in states: state.failed=True
                raise

    def step_many(self, states, windows, gain):
        import torch
        for s in states: self._check_state(s,open_required=True)
        logits=torch.cat([s.native_logits for s in states]).clone(); logits[:,self._forbidden]=-math.inf
        tokens=tuple(logits.argmax(-1).tolist())
        if any(not self.tokens.ordinary(t) for t in tokens): raise ValueError("Invalid work token")
        positions=tuple(len(s.consumed_tokens) for s in states)
        try:
            self.consume_many(states,tuple((t,) for t in tokens),windows,gain,decode=True)
            exports=[]
            for state,token,position in zip(states,tokens,positions):
                layers=tuple((layer.keys[:,:,-1:].detach().clone(),layer.values[:,:,-1:].detach().clone()) for layer in state.cache.layers)
                tensors=tuple(t for layer in layers for t in layer)
                digest=_tensor_hash({"token":token,"position":position,"model_identity":self.model_identity},tensors)
                payload=NativeKVPayload(layers,token,position,self.model_identity,digest,
                    tuple(_tensor_stamp(t) for t in tensors),self._owner)
                exports.append(Export(token,position,digest,payload))
            return tuple(exports)
        except BaseException:
            for state in states: state.failed=True
            raise

    def probe_many(self, states, questions, labels, windows, gain):
        import torch
        if not len(states)==len(questions)==len(windows): raise ValueError("Probe lane mismatch")
        for s in states: self._check_state(s,open_required=True)
        ids=self.tokens.choice_ids(labels)
        branches=tuple(self.clone(s) for s in states)
        self.consume_many(branches,tuple(self.tokens.close_ids for _ in states),windows,gain)
        self.consume_many(branches,tuple(self.tokens.user_turn(q) for q in questions),windows,gain)
        if self._w32 is None: self._w32=self.model.lm_head.weight.detach().float()
        with torch.no_grad():
            scores=torch.nn.functional.linear(torch.cat([b.last_hidden for b in branches]).float(),self._w32,
                self.model.lm_head.bias.detach().float() if self.model.lm_head.bias is not None else None)
            probs=torch.softmax(scores,-1)
        tokens=torch.cat([b.native_logits for b in branches]).argmax(-1).tolist()
        out=[]
        for lane,(branch,token) in enumerate(zip(branches,tokens)):
            p=Probe(branch,token,float(probs[lane,token]),tuple(float(scores[lane,i]) for i in ids),
                float(probs[lane,list(ids)].sum()),ids); p.validate()
            branch.seal={"token":p.token,"probability":p.probability,"legal_logits":list(p.legal_logits),
                "legal_mass":p.legal_mass,"token_ids":list(ids),"foreign":[e.identity() for e in windows[lane]],"gain":gain}
            branch.seal_checksum=self.digest(branch); out.append(p)
        return tuple(out)

    def commit_many(self, probes, windows, gain):
        if len(probes)!=len(windows): raise ValueError("Commit lane mismatch")
        states=tuple(p.state for p in probes)
        for p,w in zip(probes,windows):
            p.validate(); self._check_state(p.state,open_required=True)
            seal={"token":p.token,"probability":p.probability,"legal_logits":list(p.legal_logits),
                "legal_mass":p.legal_mass,"token_ids":list(p.token_ids),"foreign":[e.identity() for e in w],"gain":gain}
            if p.state.seal != seal or p.state.seal_checksum != self.digest(p.state):
                raise ValueError("Sealed answer changed before cohort commitment")
        rules=tuple(self.tokens.recovery(p.token) for p in probes)
        try:
            for s in states: s.seal=None; s.seal_checksum=None
            self.consume_many(states,tuple((p.token,) for p in probes),windows,gain,decode=True)
            self.consume_many(states,tuple(rule.suffix for rule in rules),tuple(() for _ in states),0.)
            for s,p,rule in zip(states,probes,rules):
                s.recoveries+=({"token":p.token,"legal":p.token in p.token_ids,"category":rule.category,"suffix":list(rule.suffix)},)
                s.open=False
            return states
        except BaseException:
            for s in states: s.failed=True
            raise
