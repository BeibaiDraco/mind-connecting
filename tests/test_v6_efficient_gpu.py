"""Unrun CUDA engineering checks; no scientific/native acceptance certificate.

Only tiny random models are constructed. Real checkpoint acceptance, complete
Replay and measured episode throughput remain separate prerequisites.
"""

from dataclasses import replace

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytestmark = [pytest.mark.gpu,
              pytest.mark.skipif(not torch.cuda.is_available(), reason="authorized CUDA host required")]

from mb import chat  # noqa: E402
from mb.model_profiles import LLAMA31, QWEN  # noqa: E402
from mb.v6_efficient import JointKernel, Layout, scalar_oracle  # noqa: E402
from mb.v6_efficient_native import EfficientPrototype  # noqa: E402
from mb.v6_efficient_probe import ENGINEERING_LIMIT  # noqa: E402


@pytest.mark.parametrize("kind", ("efficient_sdpa", "compiled_flex"))
def test_fused_operator_independent_oracle_and_exact_repetition(kind):
    layout = Layout(2, 4, 2, 4, 7, 16, 16, .5)
    torch.manual_seed(940215)
    values = tuple(torch.randn(shape, device="cuda", dtype=torch.bfloat16) for shape in layout.shapes)
    originals = tuple(x.clone() for x in values)
    cpu = tuple(x.float().cpu().numpy().astype(np.float64) for x in values)
    expected = scalar_oracle(layout, cpu)
    kernel = JointKernel(kind)
    with torch.no_grad():
        actual = kernel(layout, values)
        repeated = kernel(layout, values)
    assert torch.equal(actual, repeated)
    scale = max(np.abs(cpu[2]).max(), np.abs(cpu[4]).max())
    assert np.max(np.abs(actual.float().cpu().numpy() - expected)) <= ENGINEERING_LIMIT * scale
    assert all(torch.equal(a, b) for a, b in zip(originals, values))
    one = replace(layout, batch=1)
    with torch.no_grad():
        singleton = kernel(one, tuple(x[:1] for x in values))
    assert torch.isfinite(singleton).all()


@pytest.fixture(params=(QWEN, LLAMA31), ids=lambda p: p.model_type)
def backend(request):
    from transformers import LlamaConfig, LlamaForCausalLM, Qwen3Config, Qwen3ForCausalLM
    profile = request.param
    if not profile.tokenizer_dir.exists():
        pytest.skip("Local tokenizer required; tests never download")
    cfg_cls, cls = ((Qwen3Config, Qwen3ForCausalLM) if profile == QWEN
                    else (LlamaConfig, LlamaForCausalLM))
    config = cfg_cls(vocab_size=profile.vocab_size, hidden_size=64, intermediate_size=128,
        num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2, head_dim=16,
        max_position_embeddings=4096, attention_dropout=0.)
    config._attn_implementation = "sdpa"
    torch.manual_seed(941)
    model = cls(config).to(device="cuda", dtype=torch.bfloat16).eval()
    yield EfficientPrototype(model, chat.load_tokenizer(profile=profile), kernel="compiled_flex",
                             chunk=2, hardware_acceptance_authorized=True)


def parents(backend):
    state = backend.create("Follow your private record.", "My beacon is Dim.")
    donor = backend.create("A different private record.", "My beacon is Bright.")
    export = backend.step(donor, (), 0.)
    token = backend.tokenizer.encode(" river", add_special_tokens=False)[0]
    return state, export, (token,) * 4


def test_linked_prefill_and_cohort_repeat_isolation_and_owned_outputs(backend):
    original, donor, ids = parents(backend)
    digest = backend.digest(original)
    first = (backend.clone(original), backend.clone(original))
    second = (backend.clone(original), backend.clone(original))
    backend.consume_cohort(first, (ids, ids), ((donor,), (donor,)), .5)
    backend.consume_cohort(second, (ids, ids), ((donor,), (donor,)), .5)
    assert [backend.digest(s) for s in first] == [backend.digest(s) for s in second]
    assert backend.digest(original) == digest
    assert all(s.consumed_tokens == original.consumed_tokens + ids for s in first)
    unchanged = backend.digest(first[1])
    first[0].cache.layers[0].keys.add_(1.)
    assert backend.digest(first[1]) == unchanged


def test_intermediate_full_vocab_nonfinite_prevents_all_publication(backend, monkeypatch):
    original, _, ids = parents(backend)
    states = (backend.clone(original), backend.clone(original))
    histories = tuple(s.consumed_tokens for s in states)
    cache_ids = tuple(id(s.cache) for s in states)
    real = backend.model.lm_head.forward
    def corrupt_middle(hidden):
        output = real(hidden)
        if output.ndim == 3:
            output[1, 0, 0] = torch.nan
        return output
    monkeypatch.setattr(backend.model.lm_head, "forward", corrupt_middle)
    with pytest.raises(ValueError, match="non-finite"):
        backend.consume_cohort(states, (ids, ids), ((), ()), 0.)
    assert all(s.failed for s in states)
    assert tuple(s.consumed_tokens for s in states) == histories
    assert tuple(id(s.cache) for s in states) == cache_ids


def test_second_final_validation_failure_cannot_publish_first_lane(backend, monkeypatch):
    original, _, ids = parents(backend)
    states = (backend.clone(original), backend.clone(original))
    histories = tuple(s.consumed_tokens for s in states)
    cache_ids = tuple(id(s.cache) for s in states)
    real, candidates = backend._check_state, []
    def reject_second(state, **kwargs):
        real(state, **kwargs)
        if all(state is not parent for parent in states):
            candidates.append(state)
            if len(candidates) == 2:
                raise ValueError("injected second-lane validation failure")
    monkeypatch.setattr(backend, "_check_state", reject_second)
    with pytest.raises(ValueError, match="second-lane"):
        backend.consume_cohort(states, (ids, ids), ((), ()), 0.)
    assert tuple(s.consumed_tokens for s in states) == histories
    assert tuple(id(s.cache) for s in states) == cache_ids
    assert all(s.failed for s in states)
