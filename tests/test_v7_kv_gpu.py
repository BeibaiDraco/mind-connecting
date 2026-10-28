"""Deferred V7 checkpoint acceptance; run only after PI approves the V7 draft.

No experiment outcomes or prompt/geometry selection. These tests use fixed tokens
and the pinned Qwen model. Collection skips cleanly on a torch-free workstation.
"""
from __future__ import annotations

import copy
import json

import pytest

torch = pytest.importorskip('torch')
pytestmark = [pytest.mark.gpu,
              pytest.mark.skipif(not torch.cuda.is_available(), reason='requires approved GPU acceptance')]

from transformers import DynamicCache  # noqa: E402
from mb import chat  # noqa: E402
from mb.conditions import ArmConfig  # noqa: E402
from mb.kv_geometry import rephase_keys  # noqa: E402
from mb.runtime import Engine, KV_CONTEXT, cache_layers, load_model, make_plan, select_rows  # noqa: E402


@pytest.fixture(scope='module')
def engine():
    tok = chat.load_tokenizer()
    # FP32 isolates the translation identity from BF16 quantization of prefill keys.
    model = load_model(dtype=torch.float32, tokenizer=tok)
    obj = Engine(model, tok, 18, None)
    yield obj
    obj.close()


def _prefixes(engine):
    return [engine.tok.encode(text, add_special_tokens=False) for text in (
        'The green box holds seven copper keys. Count them carefully.',
        'A blue folder contains three pages and a red folder contains five pages.')]


def _spans(prefixes):
    return [[('P', 0, len(p)), ('tail', len(p) - 3, len(p)), ('empty', len(p), len(p))] for p in prefixes]


@torch.no_grad()
def test_real_offset_prefill_matches_rephased_keys_and_unchanged_values(engine, record_property):
    prefixes = _prefixes(engine)
    state = engine.prefill(prefixes, attention_spans=_spans(prefixes))
    rows, width = state.attn.shape
    ids = torch.full((rows, width), engine.pad_id, device=engine.device, dtype=torch.long)
    for row, tokens in enumerate(prefixes):
        ids[row, -len(tokens):] = torch.tensor(tokens, device=engine.device)
    positions = (state.attn.cumsum(-1) - 1).clamp(min=0)
    deltas = -state.attn.sum(-1)
    shifted_positions = positions + deltas[:, None]
    shifted_cache = DynamicCache(config=engine.model.config)
    engine.hook.mode = 'prefill'
    try:
        shifted = engine.model.model(input_ids=ids, attention_mask=state.attn,
            position_ids=shifted_positions, past_key_values=shifted_cache, use_cache=True)
    finally:
        engine.hook.mode = 'tick'
    freq, pairing, _ = engine._rotary_spec()
    worst = {'key_max_abs': 0., 'value_max_abs': 0.}
    for (key, value), (actual_key, actual_value) in zip(cache_layers(state.cache), cache_layers(shifted_cache)):
        expected = rephase_keys(key.float().unsqueeze(2), deltas, state.attn.bool(), freq, pairing).squeeze(2)
        valid = state.attn[:, None, :, None].bool().expand_as(key)
        torch.testing.assert_close(actual_key[valid], expected[valid], atol=2e-3, rtol=2e-3)
        torch.testing.assert_close(actual_value[valid], value[valid], atol=2e-3, rtol=2e-3)
        worst['key_max_abs'] = max(worst['key_max_abs'], float((actual_key[valid] - expected[valid]).abs().max()))
        worst['value_max_abs'] = max(worst['value_max_abs'], float((actual_value[valid] - value[valid]).abs().max()))
    torch.testing.assert_close(engine._lm_logits(shifted.last_hidden_state[:, -1]), state.logits,
                               atol=3e-3, rtol=2e-3)
    record_property('offset_prefill_fp32_errors', json.dumps(worst))


@torch.no_grad()
def test_runtime_zero_shift_logging_gqa_padding_and_snapshot_isolation(engine):
    prefixes = _prefixes(engine)
    state = engine.prefill(prefixes, attention_spans=_spans(prefixes))
    saved = [(k.clone(), v.clone()) for k, v in cache_layers(state.cache)]
    bank_meta = copy.deepcopy(state.kv_banks)
    common = dict(condition='ONE', interface='kv', kv_scope='P', gain=1.)

    def tick(snapshot, arm):
        branch = select_rows(snapshot, list(range(snapshot.rows)), engine.model.config)
        plan = make_plan(arm, ['A', 'B'] * (branch.rows // 2), [None] * branch.rows, None,
                         engine.device, d=engine.d)
        logits, _, _ = engine.step(branch, branch.pending, None, plan.kv)
        return logits, engine.last_kv_span_mass, engine.kv_condition_identity(branch, plan.kv)

    native, _, _ = tick(state, ArmConfig(**common))
    logged, masses, _ = tick(state, ArmConfig(**common, kv_log_spans=True))
    assert torch.equal(native, logged)
    assert masses.shape == (2, engine.model.config.num_hidden_layers,
                            engine.model.config.num_attention_heads, 6)
    assert torch.isnan(masses[1]).all() and torch.isfinite(masses[0]).all()
    shifted_arm = ArmConfig(**common, kv_position='before_own', kv_log_spans=True)
    shifted, _, geometry = tick(state, shifted_arm)
    assert geometry[0]['delta'] == -len(prefixes[1])
    assert geometry[0]['destination_range'][1] == 0
    assert torch.isfinite(shifted).all()
    for (key, value), (old_key, old_value) in zip(cache_layers(state.cache), saved):
        assert torch.equal(key, old_key) and torch.equal(value, old_value)
    assert state.kv_banks == bank_meta and not KV_CONTEXT.active
    longer = prefixes + [prefixes[0] * 2, prefixes[1] * 2]
    batched = engine.prefill(longer, attention_spans=_spans(longer))
    batch_logits, _, batch_geometry = tick(batched, shifted_arm)
    torch.testing.assert_close(batch_logits[:2], shifted, atol=3e-3, rtol=2e-3)
    assert batch_geometry[:2] == geometry
