"""Run production attention/geometry code with a NumPy API double, without torch.

This validates arithmetic and state plumbing, not CUDA/BF16 kernels or a checkpoint.
The actual offset-prefill acceptance test is separately GPU-marked and deferred.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from mb.conditions import ArmConfig
from mb.kv_geometry import bank_metadata, digest, rephase_keys, resolve_geometry
from mb.run import Runner, TICK_ARRAYS
from mb.model_profiles import QWEN, resolve_profile


class Tensor(np.ndarray):
    def __new__(cls, x, dtype=None):
        return np.asarray(x, dtype=dtype).view(cls)

    @property
    def device(self):
        return 'cpu'

    def float(self):
        return Tensor(self, np.float32)

    def bool(self):
        return Tensor(self, bool)

    def clone(self):
        return Tensor(self.copy())

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return np.asarray(self)

    def to(self, dtype=None):
        return self if dtype is None or isinstance(dtype, str) else Tensor(self, dtype)

    def numel(self):
        return self.size

    def view(self, *shape):
        return Tensor(np.asarray(self).reshape(*shape))

    def unsqueeze(self, dim):
        return Tensor(np.expand_dims(self, dim))

    def index_select(self, dim, idx):
        return Tensor(np.take(self, idx, axis=dim))

    def transpose(self, a, b):
        return Tensor(np.swapaxes(self, a, b))

    def masked_fill(self, mask, value):
        return Tensor(np.where(mask, value, self))

    def mean(self, dim=None, **kw):
        return Tensor(np.asarray(self).mean(axis=dim, **kw))

    def sum(self, dim=None, keepdim=False, **kw):
        return Tensor(np.asarray(self).sum(axis=dim, keepdims=keepdim, **kw))

    def cumsum(self, dim):
        return Tensor(np.asarray(self).cumsum(axis=dim))

    def nonzero(self, as_tuple=False):
        assert as_tuple
        return tuple(Tensor(x) for x in np.asarray(self).nonzero())

    def cos(self):
        return Tensor(np.cos(self))

    def sin(self):
        return Tensor(np.sin(self))

    def exp(self):
        return Tensor(np.exp(self))

    def norm(self, dim):
        return Tensor(np.linalg.norm(self, axis=dim))


def _api():
    return SimpleNamespace(
        Tensor=Tensor, float32=np.float32, bool=np.bool_, long=np.int64,
        no_grad=lambda: lambda fn: fn,
        tensor=lambda x, dtype=None, **kw: Tensor(x, dtype),
        as_tensor=lambda x, dtype=None, **kw: Tensor(x, dtype),
        arange=lambda *args, **kw: Tensor(np.arange(*args)),
        full=lambda shape, value, dtype=np.float32, **kw: Tensor(np.full(shape, value, dtype)),
        ones=lambda *shape, dtype=np.float32, **kw: Tensor(np.ones(shape, dtype)),
        zeros=lambda shape, dtype=np.float32, **kw: Tensor(np.zeros(shape, dtype)),
        empty=lambda *shape, dtype=np.float32, **kw: Tensor(np.empty(shape, dtype)),
        zeros_like=lambda x: Tensor(np.zeros_like(x)),
        full_like=lambda x, value: Tensor(np.full_like(x, value)),
        stack=lambda x, dim=0: Tensor(np.stack(x, axis=dim)),
        cat=lambda x, dim=0: Tensor(np.concatenate(x, axis=dim)),
        matmul=lambda x, y: Tensor(np.matmul(x, y)),
        einsum=lambda eq, *x: Tensor(np.einsum(eq, *x)),
        where=lambda m, x, y: Tensor(np.where(m, x, y)),
        isfinite=lambda x: Tensor(np.isfinite(x)),
        exp=lambda x: Tensor(np.exp(x)),
        sigmoid=lambda x: Tensor(1 / (1 + np.exp(-x))),
        logsumexp=lambda x, dim, keepdim: Tensor(np.logaddexp.reduce(x, axis=dim, keepdims=keepdim)),
        equal=np.array_equal,
        log_softmax=lambda x, dim: Tensor(np.log(_softmax(x))),
        nn=SimpleNamespace(functional=SimpleNamespace(cosine_similarity=lambda a, b, dim:
            Tensor(np.zeros(a.shape[0])))),
    )


def _load_runtime(api):
    source = Path('src/mb/runtime.py').read_text()
    wanted = {'KVPlan', '_KVContext', 'kv_attention', 'State', 'cache_layers', 'select_rows',
              'Plan', 'make_plan', 'TickLog', 'Engine'}
    tree = ast.parse(source)
    nodes = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)]
    nodes += [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in wanted]
    ns = dict(torch=api, math=math, copy=copy, dataclass=dataclass, field=field,
              rephase_keys=rephase_keys, bank_metadata=bank_metadata, digest=digest,
              resolve_geometry=resolve_geometry, REFLECTION_TICKS=48, NOTE_MAX_TOKENS=64,
              resolve_profile=resolve_profile, ema_update=lambda e, z, tau: z)
    exec(compile(ast.fix_missing_locations(ast.Module(nodes, type_ignores=[])), 'runtime.py', 'exec'), ns)
    ns['KV_CONTEXT'] = ns['_KVContext']()
    ns['sdpa_attention_forward'] = _sdpa
    ns['DynamicCache'] = lambda ddp_cache_data, config: SimpleNamespace(
        layers=[SimpleNamespace(keys=k, values=v) for k, v in ddp_cache_data])
    return ns


def _rotate(api):
    # Execute the installed pinned Qwen implementation, not a guessed pairing convention.
    root = Path(importlib.util.find_spec('transformers').origin).parent
    source = root / 'models/qwen3/modeling_qwen3.py'
    node = next(n for n in ast.parse(source.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == 'rotate_half')
    ns = {'torch': api}
    exec(compile(ast.Module([node], type_ignores=[]), str(source), 'exec'), ns)
    return ns['rotate_half']


def _softmax(logits):
    x = np.asarray(logits, dtype=np.float64)
    largest = x.max(axis=-1, keepdims=True)
    finite = np.isfinite(largest)
    shifted = np.subtract(x, largest, out=np.full_like(x, -np.inf), where=finite)
    exp = np.exp(shifted)
    return np.divide(exp, exp.sum(axis=-1, keepdims=True), out=np.zeros_like(exp),
                     where=exp.sum(axis=-1, keepdims=True) != 0)


def _sdpa(module, query, key, value, attention_mask, scaling=None, **kw):
    groups = query.shape[1] // key.shape[1]
    k, v = (np.repeat(np.asarray(x), groups, axis=1) for x in (key, value))
    logits = np.asarray(query) @ k.swapaxes(-1, -2) * (scaling or query.shape[-1] ** -.5)
    if attention_mask is not None:
        logits = np.where(attention_mask, logits, -np.inf)
    return Tensor((_softmax(logits) @ v).transpose(0, 2, 1, 3), np.float32), None


@pytest.fixture
def runtime(monkeypatch):
    api = _api()
    monkeypatch.setitem(sys.modules, 'torch', api)
    ns = _load_runtime(api)
    ns['rotate'] = _rotate(api)
    return ns


def fixture_state(rt, lengths=(3, 5, 2, 6), extra_pad=0, ticks=2):
    n, prefill = len(lengths), max(lengths) + extra_pad
    width = prefill + ticks
    attn = np.zeros((n, width), dtype=np.int64)
    banks = []
    for i, length in enumerate(lengths):
        attn[i, prefill-length:] = 1
        banks.append(bank_metadata(list(range(10+i, 10+i+length)),
            [('P', 0, length), ('rule', 1, min(3, length)), ('empty_note', length, length)]))
    state = rt['State'](cache=None, attn=Tensor(attn), next_pos=Tensor(np.array(lengths) + ticks - 1),
        pending=Tensor(np.ones(n, dtype=np.int64)), logits=Tensor(np.zeros((n, 4))),
        mailbox=Tensor(np.zeros((n, 6))), ema=Tensor(np.zeros((n, 6))), c_start=prefill, kv_banks=banks)
    engine = rt['Engine'].__new__(rt['Engine'])
    engine.device = 'cpu'
    engine.last_kv_bank_mass = None
    engine.model = SimpleNamespace(config=SimpleNamespace(num_hidden_layers=2))
    inv = Tensor([1.0, .07, .003], np.float32)
    engine._rotary_spec = lambda: (inv, rt['rotate'], {'fixture': 'actual_Qwen_pairing'})
    return engine, state


def attention_inputs(state, heads=6):
    rng = np.random.default_rng(781)
    n, width = state.attn.shape
    q = Tensor(rng.normal(size=(n, heads, 1, 6)), np.float32)
    k, v = (Tensor(rng.normal(size=(n, 2, width, 6)), np.float32) for _ in range(2))
    return q, k, v, state.attn[:, None, None, :].bool()


@pytest.mark.parametrize('scope,position', [('P', 'before_own'), ('P', 'native'), ('C', 'native'),
                                          ('ALL', 'native'), ('PC', 'native')])
def test_joint_mass_masks_and_gqa_match_independent_dense_softmax(runtime, scope, position):
    rt = runtime
    engine, state = fixture_state(rt)
    kv = rt['KVPlan'](Tensor([True, False, True, False]), math.log(1.4), scope,
                      -math.inf if scope == 'PC' else None, position, True)
    q, key, value, mask = attention_inputs(state)
    before = key.copy(), value.copy()
    engine._kv_begin(state, kv)
    ctx = rt['KV_CONTEXT']
    geometry = engine.kv_condition_identity(state, kv)
    for layer in range(2):
        out, _ = rt['kv_attention'](SimpleNamespace(layer_idx=layer), q, key, value, mask)
        for row in (0, 2):
            donor = row ^ 1
            kpar = np.array(key[donor], dtype=np.float64)
            delta = geometry[row]['delta']
            phase = delta * np.array([1., .07, .003])
            # Independent complex representation of the model's first-half/second-half pairs.
            z = kpar[..., :3] + 1j * kpar[..., 3:]
            z = z * np.exp(1j * phase)
            kpar = np.concatenate([z.real, z.imag], axis=-1)
            for head in range(q.shape[1]):
                kh = head // 3
                own = np.asarray(key[row, kh], np.float64) @ q[row, head, 0] / np.sqrt(6)
                par = kpar[kh] @ q[row, head, 0] / np.sqrt(6) + ctx.pos_bias
                logits = np.r_[np.where(mask[row, 0, 0], own, -np.inf),
                               np.where(ctx.readable[row], par, -np.inf)]
                joint = _softmax(logits)
                expected = joint @ np.concatenate([value[row, kh], value[donor, kh]])
                np.testing.assert_allclose(out[row, 0, head], expected, atol=4e-7, rtol=2e-6)
                for slot, span in enumerate(geometry[row]['spans']):
                    source = row if span['bank'] == 'own' else donor
                    logical = np.asarray(state.attn[source]).cumsum() - 1
                    chosen = (logical >= span['start']) & (logical < span['end']) & state.attn[source].bool()
                    probs = joint[:key.shape[2]] if span['bank'] == 'own' else joint[key.shape[2]:]
                    np.testing.assert_allclose(ctx.span_mass[layer][row//2, head, slot],
                                               probs[chosen].sum(), atol=2e-7, rtol=2e-6)
    np.testing.assert_array_equal(key, before[0])
    np.testing.assert_array_equal(value, before[1])
    engine._kv_end(state.rows, kv)
    assert engine.last_kv_span_mass.shape == (4, 2, 6, 6)
    assert np.isnan(engine.last_kv_span_mass[[1, 3]]).all()
    np.testing.assert_allclose(np.asarray(engine.last_kv_bank_mass[[0, 2]]).sum(-1), 1., atol=1e-7)
    assert np.isnan(engine.last_kv_bank_mass[[1, 3]]).all()
    if scope == 'C':
        np.testing.assert_array_equal(engine.last_kv_span_mass[[0, 2], :, :, 3:], 0.)
    assert not ctx.active and ctx.delta is None and ctx.span_mass == {}


def test_zero_delta_and_logging_are_bit_identical_to_legacy_path(runtime):
    rt = runtime
    engine, state = fixture_state(rt)
    q, key, value, mask = attention_inputs(state)
    plain = rt['KVPlan'](Tensor([True, False, True, False]), 0., 'P')
    engine._kv_begin(state, plain)
    legacy = rt['kv_attention'](SimpleNamespace(layer_idx=0), q, key, value, mask)[0]
    engine._kv_begin(state, plain)
    ctx = rt['KV_CONTEXT']
    ctx.delta = Tensor([0, 0])
    ctx.rephase_mask = ctx.readable[[0, 2]]
    ctx.inv_freq, ctx.rotate_half, _ = engine._rotary_spec()
    zero = rt['kv_attention'](SimpleNamespace(layer_idx=0), q, key, value, mask)[0]
    np.testing.assert_array_equal(legacy, zero)
    logged = rt['KVPlan'](plain.receivers, 0., 'P', position='native', log_spans=True)
    engine._kv_begin(state, logged)
    actual = rt['kv_attention'](SimpleNamespace(layer_idx=0), q, key, value, mask)[0]
    np.testing.assert_array_equal(legacy, actual)


def test_sign_norm_inverse_and_nonselected_keys(runtime):
    rng = np.random.default_rng(5)
    keys = Tensor(rng.normal(size=(2, 2, 1, 7, 6)), np.float32)
    saved = keys.copy()
    freq = Tensor([1., .07, .003], np.float32)
    delta = Tensor([-5, 0])
    selected = Tensor([[False, False, True, True, True, True, True], [True] * 7])
    shifted = rephase_keys(keys, delta, selected, freq, runtime['rotate'])
    restored = rephase_keys(shifted, -delta, selected, freq, runtime['rotate'])
    np.testing.assert_allclose(np.linalg.norm(shifted, axis=-1), np.linalg.norm(keys, axis=-1),
                               atol=5e-7, rtol=2e-7)
    np.testing.assert_allclose(restored, keys, atol=5e-7, rtol=2e-7)
    np.testing.assert_array_equal(keys, saved)
    np.testing.assert_array_equal(shifted[1], keys[1])
    np.testing.assert_array_equal(shifted[0, :, :, :2], keys[0, :, :, :2])
    assert rephase_keys(keys, Tensor([0, 0]), selected, freq, runtime['rotate']) is keys
    unit = Tensor([[[[[1., 0., 0., 0., 0., 0.]]]]], np.float32)
    got = rephase_keys(unit, Tensor([-1]), Tensor([[True]]), freq, runtime['rotate'])
    assert got[0, 0, 0, 0, 3] == pytest.approx(-math.sin(1), abs=1e-7)


def test_padding_batch_invariance_and_branch_metadata_isolation(runtime):
    rt = runtime
    engine, state = fixture_state(rt)
    q, key, value, mask = attention_inputs(state)
    kv = rt['KVPlan'](Tensor([True, False, True, False]), 0., 'P', position='before_own', log_spans=True)
    engine._kv_begin(state, kv)
    original = rt['kv_attention'](SimpleNamespace(layer_idx=0), q, key, value, mask)[0]
    metadata = engine.kv_condition_identity(state, kv)
    for chosen in ((0, 1), (2, 3), (2, 3, 0, 1)):
        rows = list(chosen)
        st = copy.deepcopy(state)
        st.attn = Tensor(np.pad(state.attn[rows], ((0, 0), (4, 0))))
        st.c_start += 4
        st.pending = state.pending[rows]
        st.kv_banks = [copy.deepcopy(state.kv_banks[r]) for r in rows]
        plan = rt['KVPlan'](Tensor([True, False] * (len(rows)//2)), 0., 'P',
                            position='before_own', log_spans=True)
        engine._kv_begin(st, plan)
        kp = Tensor(np.pad(key[rows], ((0, 0), (0, 0), (4, 0), (0, 0)), constant_values=1e6))
        vp = Tensor(np.pad(value[rows], ((0, 0), (0, 0), (4, 0), (0, 0)), constant_values=-1e6))
        out = rt['kv_attention'](SimpleNamespace(layer_idx=0), q[rows], kp, vp,
                                 st.attn[:, None, None, :].bool())[0]
        np.testing.assert_allclose(out, original[rows], atol=3e-7, rtol=1e-6)
        assert engine.kv_condition_identity(st, plan) == [metadata[r] for r in rows]
    state.cache = SimpleNamespace(layers=[SimpleNamespace(keys=key, values=value)])
    saved_key = key.copy()
    branch = rt['select_rows'](state, [2, 3, 0, 1], None)
    branch.kv_banks[0]['spans'][0]['start'] = 999
    branch.cache.layers[0].keys[0] = 999
    branch.attn[0] = 0
    assert state.kv_banks[2]['spans'][0]['start'] == 0
    np.testing.assert_array_equal(state.cache.layers[0].keys, saved_key)
    assert state.attn[2].any()


def test_missing_geometry_bad_gqa_and_missing_layer_fail_closed(runtime):
    rt = runtime
    engine, state = fixture_state(rt)
    kv = rt['KVPlan'](Tensor([True, False, True, False]), 0., 'P', position='before_own', log_spans=True)
    state.kv_banks = None
    with pytest.raises(ValueError, match='prefill'):
        engine._kv_begin(state, kv)
    engine, state = fixture_state(rt)
    engine._kv_begin(state, kv)
    q, k, v, m = attention_inputs(state, heads=5)
    with pytest.raises(RuntimeError, match='divisible'):
        rt['kv_attention'](SimpleNamespace(layer_idx=0), q, k, v, m)
    engine._kv_end(state.rows, kv, completed=False)
    assert not rt['KV_CONTEXT'].active
    assert engine.last_kv_span_mass is None
    engine._kv_begin(state, kv)
    q, k, v, m = attention_inputs(state)
    rt['kv_attention'](SimpleNamespace(layer_idx=0), q, k, v, m)
    with pytest.raises(RuntimeError, match='ran in 1 layers'):
        engine._kv_end(state.rows, kv)
    assert not rt['KV_CONTEXT'].active and rt['KV_CONTEXT'].span_mass == {}


def test_no_readable_partner_has_zero_joint_mass_and_finite_output(runtime):
    rt = runtime
    engine, state = fixture_state(rt, ticks=1)
    kv = rt['KVPlan'](Tensor([True, False, True, False]), 0., 'C', log_spans=True)
    engine._kv_begin(state, kv)
    q, k, v, m = attention_inputs(state)
    with np.errstate(invalid='ignore'):
        out, _ = rt['kv_attention'](SimpleNamespace(layer_idx=0), q, k, v, m)
    assert np.isfinite(out).all()
    np.testing.assert_array_equal(rt['KV_CONTEXT'].mass_sum, 0.)
    np.testing.assert_array_equal(rt['KV_CONTEXT'].span_mass[0][:, :, 3:], 0.)
    reference, _ = _sdpa(None, q, k, v, m)
    np.testing.assert_array_equal(out, reference)


def test_rotary_shape_and_dtype_fail_closed(runtime):
    keys = Tensor(np.ones((1, 2, 1, 3, 6)), np.float32)
    args = (Tensor([-3]), Tensor([[True] * 3]), Tensor([1., .1, .01]), runtime['rotate'])
    with pytest.raises(ValueError, match='fp32'):
        rephase_keys(Tensor(keys, np.float64), *args)
    with pytest.raises(ValueError, match='head dimension'):
        rephase_keys(keys, args[0], args[1], Tensor([1., .1]), args[-1])


def test_span_metadata_hashes_empty_spans_and_validation():
    own = bank_metadata([1, 2, 3], [('all', 0, 3), ('note', 3, 3)])
    donor = bank_metadata([5, 6, 7, 8], [('fact', 1, 3)])
    meta = resolve_geometry(own, donor, 'before_own')
    assert meta['delta'] == -4 and meta['destination_range'] == [-4, 0]
    assert meta['source_position_map'] == {'start': 0, 'stop': 4, 'step': 1}
    assert meta['spans'][-1]['apparent_start'] == -3
    changed = bank_metadata([5, 9, 7, 8], [('fact', 1, 3)])
    assert changed['spans'][0]['sha256'] != donor['spans'][0]['sha256']
    for spans in ([('x', -1, 2)], [('x', 0, 4)], [('x', 0, 1), ('x', 1, 2)], [('x', True, 2)]):
        with pytest.raises(ValueError):
            bank_metadata([1, 2, 3], spans)


def test_npz_summaries_preserve_variable_span_slots_and_missing_values(tmp_path):
    parts = []
    for n, ticks, spans in ((2, 4, 5), (1, 2, 3)):
        arrays = {k: np.full((n, ticks), fill) for k, fill in TICK_ARRAYS}
        arrays.update(Runner._tick_payload({'kv_geometry': [{'delta': -5, 'spans': []}] * n,
            'r_kv_span_mass': Tensor(np.full((n, ticks, 2, 6, spans), .25)),
            'r_kv_query_pos': Tensor(np.tile(np.arange(10, 10+ticks), (n, 1)))}))
        if n == 2:
            arrays['g_kv_span_mass'] = np.full((n, 3, 2, 6, spans), .5)
        parts.append(([str(i) for i in range(n)], arrays))
    target = tmp_path / 'summary.npz'
    Runner._save_rticks(target, parts)
    with np.load(target, allow_pickle=False) as data:
        assert data['r_kv_span_mass'].shape == (3, 4, 2, 6, 5)
        assert np.isnan(data['r_kv_span_mass'][2, 2:]).all()
        assert np.isnan(data['r_kv_span_mass'][2, :2, :, :, 3:]).all()
        assert np.isnan(data['g_kv_span_mass'][2]).all()
        assert (data['r_kv_query_pos'][2, 2:] == -1).all()
        assert data['g_kv_span_mass_lengths'].tolist() == [3, 3, 0]
        assert json.loads(data['kv_geometry_json'][0])['delta'] == -5


@pytest.mark.parametrize('mode', ['FULL', 'RF', 'RO'])
@pytest.mark.parametrize('recipient', ['A', 'B'])
def test_readout_branch_preserves_geometry_and_exports_tick_axes(runtime, mode, recipient):
    rt = runtime
    engine, snapshot = fixture_state(rt, lengths=(3, 5))
    snapshot.phase, snapshot.tick = 'C', 48
    snapshot.cache = SimpleNamespace(layers=[SimpleNamespace(
        keys=Tensor(np.zeros((2, 2, 7, 6))), values=Tensor(np.zeros((2, 2, 7, 6))))])
    original_banks = copy.deepcopy(snapshot.kv_banks)
    engine.profile = QWEN
    engine.cal, engine.d = None, 6
    engine.label_ids = Tensor(np.arange(4))
    engine.no_eos_argmax = lambda logits: Tensor(np.asarray(logits).argmax(-1))
    engine.fp32_logits = lambda hidden: hidden
    engine._messages = lambda ema: Tensor(np.zeros_like(ema))
    engine.last_kv_mass = engine.last_kv_mass_cr = engine.last_kv_span_mass = None
    engine.hook = SimpleNamespace(host_rms=None)
    seen_banks = []

    def step(state, tokens, injection, kv=None):
        seen_banks.append(copy.deepcopy(state.kv_banks))
        state.attn = Tensor(np.concatenate([state.attn, np.ones((state.rows, 1))], axis=1))
        state.next_pos = state.next_pos + 1
        state.tick += 1
        state.consumed.append(tokens.clone())
        engine.last_kv_span_mass = None
        if kv is not None:
            geometry = engine.kv_condition_identity(state, kv)
            engine.last_kv_span_mass = Tensor(np.stack([
                np.full((2, 6, 6), .125 if g is not None else np.nan) for g in geometry]))
        logits = Tensor(np.tile([0., 1., 2., 3.], (state.rows, 1)))
        return logits, logits, Tensor(np.zeros((state.rows, 6)))

    engine.step = step
    arm = ArmConfig('ONE', interface='kv', kv_scope='P', gain=1., readout_mode=mode,
                    kv_position='before_own', kv_log_spans=True, recipients=('A', 'B'))
    out = engine.run_readout(snapshot, [(0, recipient)], Tensor([[11, 12, 13]]), arm,
                             [None], generate=3)
    assert out['generated'].shape == (1, 3)
    assert snapshot.kv_banks == original_banks
    assert snapshot.tick == 48
    assert not snapshot.consumed
    if mode == 'RF':
        assert 'kv_geometry' not in out and 'r_kv_span_mass' not in out
        assert len(seen_banks[0]) == 1
    else:
        assert out['r_kv_span_mass'].shape == (1, 3, 2, 6, 6)
        assert out['g_kv_span_mass'].shape == (1, 2, 2, 6, 6)
        assert out['g_kv_query_pos'][0, 0] == out['r_kv_query_pos'][0, -1] + 1
        if recipient == 'A':
            assert out['kv_geometry'][0]['delta'] == -5
            assert np.isfinite(out['r_kv_span_mass']).all()
        else:
            assert out['kv_geometry'] == [None]
            assert np.isnan(out['r_kv_span_mass']).all()
            assert seen_banks[0] == [original_banks[1], original_banks[0]]


def test_loaded_rotary_frequencies_and_pairing_are_used_and_changes_refused(runtime, monkeypatch):
    rt = runtime
    rotary = SimpleNamespace(rope_type='default', inv_freq=Tensor([1., .051, .0017], np.float32),
                             attention_scaling=2.5)
    pairing = rt['rotate']
    pairing.__module__ = 'transformers.models.qwen3.modeling_qwen3'
    monkeypatch.setitem(sys.modules, pairing.__module__, SimpleNamespace(rotate_half=pairing))
    engine = rt['Engine'].__new__(rt['Engine'])
    engine.model = SimpleNamespace(model=SimpleNamespace(rotary_emb=rotary),
                                   config=SimpleNamespace(model_type='qwen3'))
    engine._kv_rotary = None
    freq, rotate, identity = engine._rotary_spec()
    assert rotate is pairing
    np.testing.assert_array_equal(freq, rotary.inv_freq)
    assert identity['cached_attention_scaling'] == 2.5
    assert identity['rephase_attention_scaling'] == 1.
    rotary.inv_freq[1] *= 2
    with pytest.raises(ValueError, match='changed'):
        engine._rotary_spec()
    rotary.rope_type = 'dynamic'
    with pytest.raises(ValueError, match='stationary'):
        engine._rotary_spec()


def test_step_cleans_context_and_hooks_when_geometry_validation_fails(runtime):
    rt = runtime
    engine, state = fixture_state(rt)
    engine.hook = SimpleNamespace(mode=None, injection=None, write_enabled=False)
    engine.model.model = lambda **kwargs: pytest.fail('invalid geometry reached model execution')
    state.kv_banks[0]['length'] += 1
    kv = rt['KVPlan'](Tensor([True, False, True, False]), 0., 'P', position='before_own')
    with pytest.raises(ValueError, match='logical lengths'):
        engine.step(state, state.pending, Tensor(np.zeros((4, 6))), kv)
    assert not rt['KV_CONTEXT'].active
    assert rt['KV_CONTEXT'].receivers is None and rt['KV_CONTEXT'].span_mass == {}
    assert not engine.hook.write_enabled and engine.hook.injection is None
    assert engine.last_kv_span_mass is None


@pytest.mark.parametrize('position,logging', [('native', False), ('native', True), ('before_own', True)])
def test_runner_passes_material_span_declarations_to_prefill(monkeypatch, position, logging):
    import mb
    monkeypatch.setitem(sys.modules, 'mb.runtime', SimpleNamespace(U_OPEN_TOKENS=80, make_plan=None))
    monkeypatch.delattr(mb, 'runtime', raising=False)
    runner = Runner.__new__(Runner)
    runner.torch = SimpleNamespace()
    runner.cfg = SimpleNamespace(model_profile=None)
    runner.arm_identity = lambda a: ({}, 'config', 'mask')
    own, donor = SimpleNamespace(episode_id='own'), SimpleNamespace(episode_id='donor')
    runner._donors = lambda *args: [donor]
    runner._pending_questions = lambda *args: [(0, 'A', None)]
    runner.ensure_notes = lambda *args: None
    runner.prefix = lambda ep, role, *args, **kw: [1, 2, 3] if role == 'A' else [4, 5, 6, 7]
    declarations = []
    def spans(ep, role, frame, ids):
        declarations.append((ep.episode_id, role, frame))
        return [('fact', len(ids) - 2, len(ids))]
    runner.prefix_spans = spans
    runner._base_record = lambda *args: {}
    runner._emit = lambda rec: None
    runner.writer = SimpleNamespace(flush=lambda: None)
    runner.log = lambda line: None
    received = []
    def prefill(sequences, **kwargs):
        received.append((sequences, kwargs))
        raise RuntimeError('intentional stop before any model operation')
    arm = ArmConfig('ONE', interface='kv', kv_scope='P', gain=1., kv_position=position,
                    kv_log_spans=logging, partner_frame='third_strict')
    runner.run_arm_chunk(SimpleNamespace(prefill=prefill), arm, [own], set(), set(), 0)
    assert len(received) == 1
    if position != 'native' or logging:
        assert received[0][1]['attention_spans'] == [[('fact', 1, 3)], [('fact', 2, 4)]]
        assert declarations == [('own', 'A', 'second'), ('donor', 'B', 'third_strict')]
    else:
        assert received[0][1] == {} and declarations == []


def test_legacy_run_and_snapshot_identity_omit_unused_v7_fields(runtime):
    from dataclasses import replace
    from mb import run

    cfg = run.StageConfig(stage='unit', tag='unit', split='unit', n_episodes=1,
                          arms=[dict(condition='ONE', interface='kv', kv_scope='P', gain=1.)])
    resolved = cfg.resolved()
    assert 'kv_position' not in resolved['arms'][0] and 'kv_log_spans' not in resolved['arms'][0]
    explicit = replace(cfg, arms=[{**cfg.arms[0], 'kv_position': 'native', 'kv_log_spans': False}])
    assert explicit.resolved() == resolved
    shifted = replace(cfg, arms=[{**cfg.arms[0], 'kv_position': 'before_own', 'kv_log_spans': True}])
    assert shifted.resolved() != resolved
    a, b = cfg.arm_configs()[0], shifted.arm_configs()[0]
    assert run.reflection_groups([a, b, replace(b, readout_mode='RF')]) == [[a], [b, replace(b, readout_mode='RF')]]
    _, state = fixture_state(runtime)
    type(state).__module__ = 'mb.runtime'
    state.kv_banks = None
    with_default = run.snapshot_hash(state)
    del state.kv_banks
    assert run.snapshot_hash(state) == with_default
    state.kv_banks = [bank_metadata([1, 2], [('P', 0, 2)])]
    assert run.snapshot_hash(state) != with_default
