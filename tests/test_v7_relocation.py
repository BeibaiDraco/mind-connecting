"""Offline contracts for the production-read relocation acceptance harness."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from mb import v7_relocation as r
from test_v7_kv_engine import Tensor, _api


def test_per_row_offset_uses_unpadded_donor_lengths_only():
    prefixes = [[11, 12], [20, 21, 22, 23, 24], [30, 31, 32, 33], [40, 41, 42]]
    ids, mask, positions, offsets = r.reference_layout(prefixes, 0)
    assert offsets == [0, -5, 0, -3]
    assert positions[0][-2:] == [0, 1]
    assert positions[1] == [-5, -4, -3, -2, -1]
    assert positions[2][-4:] == [0, 1, 2, 3]
    assert positions[3][-3:] == [-3, -2, -1]
    assert ids[0] == [0, 0, 0, 11, 12]
    assert mask[0] == [0, 0, 0, 1, 1]
    with pytest.raises(ValueError):
        r.reference_layout(prefixes[:3], 0)


def test_logit_relative_tolerance_and_absolute_only_mass_tolerance():
    assert r.error_summary([1.004], [1.0], atol=r.LOGIT_ATOL, rtol=r.LOGIT_RTOL)['within']
    assert not r.error_summary([1.006], [1.0], atol=r.LOGIT_ATOL, rtol=r.LOGIT_RTOL)['within']
    assert r.error_summary([.0019], [0.], atol=r.MASS_ATOL)['within']
    assert not r.error_summary([.0021], [0.], atol=r.MASS_ATOL)['within']
    assert not r.error_summary([100.003], [100.], atol=r.MASS_ATOL)['within']
    assert (r.LOGIT_ATOL, r.LOGIT_RTOL, r.MASS_ATOL) == (.003, .002, .002)


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_comparisons_are_explicit_json_safe_failures(bad):
    result = r.error_summary([bad], [0], atol=r.MASS_ATOL)
    assert not result['finite'] and not result['within']
    assert result['max_abs'] is None
    json.dumps(result, allow_nan=False)


def test_empty_or_mismatched_comparisons_do_not_silently_pass():
    for x, y in (([], []), ([1], [1, 2])):
        with pytest.raises(ValueError):
            r.error_summary(x, y, atol=r.MASS_ATOL)


def test_saved_inputs_are_hashed_before_they_can_be_used(tmp_path):
    payload = {'episodes': ['v7_dev-0-00000'], 'prefix_ids': [[2, 3], [4, 5, 6]],
               'attention_spans': [[['P', 0, 2]], [['P', 0, 3]]]}
    path = tmp_path / 'inputs.json'
    path.write_text(json.dumps(payload))
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    assert r.read_saved_inputs(path, sha, expected_episodes=1) == payload
    path.write_text(json.dumps({**payload, 'prefix_ids': [[7, 3], [4, 5, 6]]}))
    with pytest.raises(ValueError, match='hash'):
        r.read_saved_inputs(path, sha, expected_episodes=1)


@pytest.mark.parametrize('mutation', ['episode', 'rows', 'span', 'token'])
def test_invalid_fixture_layout_fails_even_with_a_matching_file_hash(tmp_path, mutation):
    payload = {'episodes': ['v7_dev-0-00000'], 'prefix_ids': [[2, 3], [4, 5, 6]],
               'attention_spans': [[['P', 0, 2]], [['P', 0, 3]]]}
    if mutation == 'episode': payload['episodes'] = ['v7_pilot-0-00000']
    if mutation == 'rows': payload['prefix_ids'].pop()
    if mutation == 'span': payload['attention_spans'][1][0][2] = 4
    if mutation == 'token': payload['prefix_ids'][0][0] = -1
    path = tmp_path / 'inputs.json'; path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        r.read_saved_inputs(path, hashlib.sha256(path.read_bytes()).hexdigest(), expected_episodes=1)


def fake_runtime(monkeypatch):
    api = _api()
    monkeypatch.setitem(sys.modules, 'torch', api)
    cache_layers = lambda cache: [(x.keys, x.values) for x in cache.layers]
    monkeypatch.setitem(sys.modules, 'mb.runtime', SimpleNamespace(
        cache_layers=cache_layers, select_rows=lambda state, idx, config: copy.deepcopy(state)))
    monkeypatch.setitem(sys.modules, 'transformers', SimpleNamespace(
        DynamicCache=lambda **kw: SimpleNamespace(layers=[])))
    return api


def test_true_prefill_reference_replaces_only_donor_state_and_keeps_source_isolated(monkeypatch):
    fake_runtime(monkeypatch)
    prefixes = [[11, 12], [20, 21, 22, 23, 24], [30, 31, 32, 33], [40, 41, 42]]
    ids, mask, positions, offsets = r.reference_layout(prefixes, 0)
    native = SimpleNamespace(rows=4, attn=Tensor(mask), next_pos=Tensor([2, 5, 4, 3]),
        pending=Tensor([1, 2, 3, 4]), logits=Tensor(np.ones((4, 6))), mailbox=Tensor(np.ones((4, 2))),
        ema=Tensor(np.ones((4, 2))), c_start=5,
        kv_banks=[{'row': x} for x in range(4)],
        cache=SimpleNamespace(layers=[SimpleNamespace(keys=Tensor(np.ones((4, 1, 5, 2))),
                                                     values=Tensor(np.full((4, 1, 5, 2), 7.)))]))
    original = copy.deepcopy(native)
    hook = SimpleNamespace(mode='tick', write_enabled=False, injection=None)
    calls = []
    def forward(**kw):
        calls.append(kw)
        assert hook.mode == 'prefill' and not hook.write_enabled and hook.injection is None
        assert np.array_equal(kw['position_ids'], positions)
        assert np.array_equal(kw['input_ids'], ids)
        keys = np.broadcast_to(np.array(positions)[:, None, :, None], (4, 1, 5, 2)).copy()
        kw['past_key_values'].layers = [SimpleNamespace(keys=Tensor(keys), values=Tensor(keys + 100))]
        hook.captured = Tensor(np.full((4, 2), 5.))
        return SimpleNamespace(last_hidden_state=Tensor(np.full((4, 5, 2), 6.)))
    engine = SimpleNamespace(device='cpu', pad_id=0, hook=hook,
        model=SimpleNamespace(config=object(), model=forward),
        _lm_logits=lambda h: Tensor(np.full((4, 6), 9.)),
        no_eos_argmax=lambda logits: Tensor(np.full(4, 5)),
        _messages=lambda ema: Tensor(ema * 2))
    reference = r.prefill_relocated_reference(engine, prefixes, native)
    assert len(calls) == 1 and hook.mode == 'tick'
    assert reference.next_pos.tolist() == [2, 0, 4, 0]
    for name in ('next_pos', 'pending', 'logits', 'mailbox', 'ema', 'attn'):
        assert np.array_equal(getattr(reference, name)[0::2], getattr(original, name)[0::2])
        assert np.array_equal(getattr(native, name), getattr(original, name))
    assert reference.kv_banks == native.kv_banks
    assert np.array_equal(reference.cache.layers[0].keys[0::2], original.cache.layers[0].keys[0::2])
    assert reference.cache.layers[0].keys[1, 0, :, 0].tolist() == [-5, -4, -3, -2, -1]
    assert reference.cache.layers[0].values[1, 0, :, 0].tolist() == [95, 96, 97, 98, 99]
    reference.cache.layers[0].keys[0, 0, 0, 0] = 999
    assert np.array_equal(native.cache.layers[0].keys, original.cache.layers[0].keys)


def test_trace_invokes_real_engine_step_eight_times_and_slices_receiver_slots(monkeypatch):
    api = fake_runtime(monkeypatch)
    plans = []
    sys.modules['mb.runtime'].make_plan = lambda arm, *args, **kw: plans.append(arm) or SimpleNamespace(kv=arm)
    calls = []
    state = SimpleNamespace(rows=4, phase='P', next_pos=Tensor([3, 5, 4, 6]))
    def step(st, tokens, injection, kv):
        calls.append((np.asarray(tokens).copy(), injection, kv))
        st.next_pos += 1
        engine.last_kv_span_mass = Tensor(np.full((4, 2, 6, 4), .1))
        engine.last_kv_span_mass[1::2] = np.nan
        return Tensor(np.ones((4, 9))), None, Tensor(np.ones((4, 3)))
    engine = SimpleNamespace(device='cpu', d=3, model=SimpleNamespace(config=SimpleNamespace(
        num_hidden_layers=2, num_attention_heads=6)), step=step, advance=lambda *args, **kw: None)
    spans = [[('a', 0, 1), ('b', 1, 2)]] * 4
    result = r.trace(engine, state, spans, token=42, translated=True)
    assert len(calls) == 8 and len(plans) == 1
    arm = plans[0]
    assert (arm.condition, arm.interface, arm.kv_scope, arm.gain, arm.kv_position, arm.kv_log_spans) == (
        'ONE', 'kv', 'P', 2., 'before_own', True)
    assert len(result) == 2 and result[0]['logits'].shape == (8, 9)
    assert result[0]['own'].shape == result[0]['donor'].shape == (8, 2, 6, 2)
    assert np.isfinite(result[0]['own']).all()
    assert all((tokens == 42).all() and injection is None for tokens, injection, _ in calls)
    r.trace(engine, state, spans, token=42, translated=False)
    assert plans[-1].kv_position == 'native'


def test_mass_error_in_one_head_or_donor_cannot_be_hidden_by_averaging():
    base = {'logits': np.zeros((8, 3)), 'own': np.zeros((8, 2, 4, 2)), 'donor': np.zeros((8, 2, 4, 2))}
    compared = copy.deepcopy(base)
    compared['donor'][7, 1, 3, 1] = .0021
    rows = r.compare_traces([compared], [base], batch=1, row_start=0)
    assert len(rows) == 8 and not rows[-1]['donor']['within']
    assert all(x['logits']['within'] and x['own']['within'] for x in rows)
    assert not r.fp32_passed(rows)
    assert not r.fp32_passed([])


def test_precision_receipt_checks_model_and_cache_not_only_label(monkeypatch):
    api = fake_runtime(monkeypatch)
    api.float32 = np.dtype(np.float32)
    api.bfloat16 = 'bf16'
    api.backends = SimpleNamespace(cuda=SimpleNamespace(matmul=SimpleNamespace(allow_tf32=False),
        flash_sdp_enabled=lambda: True, math_sdp_enabled=lambda: True))
    api.get_float32_matmul_precision = lambda: 'highest'
    engine = SimpleNamespace(model=SimpleNamespace(parameters=lambda: [Tensor([1.], np.float32)],
        config=SimpleNamespace(_attn_implementation='mb_kv')))
    receipt = r.precision_metadata(engine, 'fp32')
    assert receipt['parameter_dtypes'] == ['float32'] and receipt['matmul_allow_tf32'] is False
    state = SimpleNamespace(cache=SimpleNamespace(layers=[SimpleNamespace(
        keys=Tensor([1.], np.float32), values=Tensor([2.], np.float32))]))
    r.check_cache_precision(state, 'fp32')
    state.cache.layers[0].values = Tensor([2.], np.float64)
    with pytest.raises(RuntimeError, match='cache precision'): r.check_cache_precision(state, 'fp32')
    engine.model.parameters = lambda: [Tensor([1.], np.float64)]
    with pytest.raises(RuntimeError, match='model precision'): r.precision_metadata(engine, 'fp32')
