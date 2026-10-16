"""Unrun CUDA engineering tests; tiny random models only, never acceptance."""
from types import SimpleNamespace
import numpy as np
import pytest
torch=pytest.importorskip("torch")
pytestmark=[pytest.mark.gpu,pytest.mark.skipif(not torch.cuda.is_available(),reason="CUDA host required")]
from mb import chat
from mb.model_profiles import QWEN,LLAMA31
from mb.v6_batch_native import PackedBackend,PackedLayout,packed_oracle,_Context,_attention,CONTEXT
from mb.v6_state_guard import DeviceStateGuard


@pytest.fixture(params=(QWEN,LLAMA31),ids=lambda p:p.model_type)
def backend(request):
    from transformers import Qwen3Config,Qwen3ForCausalLM,LlamaConfig,LlamaForCausalLM
    profile=request.param
    if not profile.tokenizer_dir.exists():pytest.skip("Pinned local tokenizer required; no downloads")
    cfg,cls=(Qwen3Config,Qwen3ForCausalLM) if profile==QWEN else (LlamaConfig,LlamaForCausalLM)
    config=cfg(vocab_size=profile.vocab_size,hidden_size=64,intermediate_size=128,num_hidden_layers=2,
        num_attention_heads=4,num_key_value_heads=2,head_dim=16,max_position_embeddings=4096,attention_dropout=0.)
    config._attn_implementation="sdpa";torch.manual_seed(945)
    torch.backends.cuda.matmul.allow_tf32=False
    model=cls(config).to(device="cuda",dtype=torch.bfloat16).eval()
    return PackedBackend(model,chat.load_tokenizer(profile=profile),chunk=4,prefix_capacity=256,
                         hardware_acceptance_authorized=True)


def states(backend):
    return (backend.create("Private state.","Beacon Dim."),backend.create("Private state.","Beacon Bright, goal two."))


def test_ragged_operator_oracle_repeat_and_padded_value_isolation(backend):
    l=PackedLayout((3,7),(4,1),(2,0),0,4,.5,16,16)
    torch.manual_seed(79)
    q,k,v,fk,fv=tuple(torch.randn(s,device="cuda",dtype=torch.bfloat16)
        for s in ((2,4,4,16),(2,2,l.own,16),(2,2,l.own,16),(2,2,16,16),(2,2,16,16)))
    masks,valid=l.masks();allowed=torch.tensor(masks,device="cuda")
    bias=torch.zeros(l.own+16,device="cuda");bias[l.own:]=np.log(.5)
    keys=torch.cat((k,fk),2);values=torch.cat((v,fv),2)
    actual=backend._fused(q,keys,values,allowed,bias)
    assert torch.equal(actual,backend._fused(q,keys,values,allowed,bias))
    cpu=tuple(x.float().cpu().numpy() for x in (q,k,v,fk,fv))
    reference=packed_oracle(l,cpu)
    error=np.abs(actual.float().cpu().numpy()-reference).transpose(0,2,1,3)[valid]
    scale=max(np.max(np.abs(cpu[2])),np.max(np.abs(cpu[4])))
    assert error.max()<=2**-7*scale
    values[0,:,3:16]=1000
    assert torch.equal(actual[0],backend._fused(q,keys,values,allowed,bias)[0])


def test_changed_other_lane_length_window_and_values_cannot_change_first_lane(backend):
    original=states(backend)
    token=backend.tokenizer.encode(" river",add_special_tokens=False)[0]
    donor=backend.step(backend.clone(original[1]),(),0.)
    first=tuple(backend.clone(s) for s in original)
    changed=tuple(backend.clone(s) for s in original)
    backend._consume(changed[1],(token,)*7)
    backend.consume_many(first,((token,)*2,(token,)*3),((donor,),()),.5)
    backend.consume_many(changed,((token,)*2,(token,)*9),((donor,),(donor,)),.5)
    assert backend.digest(first[0])==backend.digest(changed[0])
    assert len(first[0].consumed_tokens)==len(original[0].consumed_tokens)+2
    other=backend.digest(first[1]);first[0].cache.layers[0].keys.add_(1.)
    assert backend.digest(first[1])==other


def test_device_guard_signed_zero_and_owned_reference(backend):
    parents=states(backend)
    parents[0].native_logits[0,0]=0.
    g=DeviceStateGuard(backend,parents);g.verify()
    parents[0].native_logits[0,0]=-0.
    with pytest.raises(RuntimeError,match="bytes"):g.verify()


def test_intermediate_real_nonfinite_blocks_all_cohort_publication(backend,monkeypatch):
    parents=states(backend);histories=tuple(s.consumed_tokens for s in parents)
    caches=tuple(id(s.cache) for s in parents);real=backend.model.lm_head.forward
    def bad(hidden):
        result=real(hidden)
        if result.ndim==3:result[1,0,0]=torch.nan
        return result
    monkeypatch.setattr(backend.model.lm_head,"forward",bad)
    token=backend.tokenizer.encode(" river",add_special_tokens=False)[0]
    with pytest.raises(ValueError,match="Nonfinite"):
        backend.consume_many(parents,((token,)*2,(token,)),((),()),0.)
    assert all(s.failed for s in parents)
    assert tuple(s.consumed_tokens for s in parents)==histories
    assert tuple(id(s.cache) for s in parents)==caches


def test_scalar_preparation_and_text_commit_use_single_real_decode(backend,monkeypatch):
    state=states(backend)[0];seen=[];original=backend.consume_many
    def observe(states,inputs,windows,gain,**kwargs):
        seen.append((inputs,kwargs.get("decode",False)))
        return original(states,inputs,windows,gain,**kwargs)
    monkeypatch.setattr(backend,"consume_many",observe)
    export=backend.step(state,(),0.)
    assert seen==[(((export.token,),),True)]
    p=backend.probe(state,"Choose 1, 2, 3, or 4.",("1","2","3","4"),(),0.)
    seen.clear();before=p.state.consumed_tokens
    result=backend.commit_answer(p,(),0.)
    assert seen[0]==(((p.token,),),True)
    assert result.consumed_tokens==before+(p.token,)+backend.tokens.recovery(p.token).suffix
    assert result.recoveries[-1]["token"]==p.token and not result.open


def test_final_state_validation_failure_does_not_publish_any_lane(backend,monkeypatch):
    parents=states(backend);original=backend._check_state
    histories=tuple(s.consumed_tokens for s in parents);caches=tuple(id(s.cache) for s in parents)
    # Native tensor dataclass equality is not an identity check.
    def checked(state,*args,**kwargs):
        if all(state is not p for p in parents) and state.consumed_tokens[:-1]==histories[1]:
            raise ValueError("injected final-state failure")
        return original(state,*args,**kwargs)
    monkeypatch.setattr(backend,"_check_state",checked)
    token=backend.tokenizer.encode(" river",add_special_tokens=False)[0]
    with pytest.raises(ValueError,match="injected"):
        backend.consume_many(parents,((token,),(token,)),((),()),0.,decode=True)
    assert tuple(s.consumed_tokens for s in parents)==histories
    assert tuple(id(s.cache) for s in parents)==caches and all(s.failed for s in parents)


@pytest.mark.parametrize("bad",[1.,-1.,float("nan")])
def test_malformed_additive_mask_is_not_silently_ignored(bad):
    module=object();layout=PackedLayout((1,),(2,),(0,),0,2,0.)
    allowed,valid=layout.masks()
    b=SimpleNamespace(modules={id(module):0},_fused=lambda q,*args:q)
    c=_Context(b,layout,(),torch.tensor(allowed,device="cuda"),torch.tensor(valid,device="cuda"))
    q=torch.zeros(1,2,2,4,device="cuda"); k=v=torch.zeros(1,1,3,4,device="cuda")
    mask=torch.where(c.allowed[:,None],0.,-torch.inf);mask[0,0,0,2]=bad
    handle=CONTEXT.set(c)
    try:_attention(module,q,k,v,mask,scaling=.5)
    finally:CONTEXT.reset(handle)
    assert not bool(torch.stack(c.mask_checks).all())
