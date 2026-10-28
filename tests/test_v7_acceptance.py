"""Revised engineering admission: FP32 gates, BF16 describes, CAP0 precedes selection."""
import copy
import json
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from mb import v7_acceptance as a, v7_run


def timings():
    return [{"mode": "translated", "batch": b, "passed": True,
             "seconds_per_episode_token": 1 / b} for b in a.BATCHES]


def test_selection_uses_only_measured_throughput_and_requires_all_pass():
    original = timings()
    assert a.choose_batch(original) == 12
    tied = copy.deepcopy(original)
    for r in tied:
        r['seconds_per_episode_token'] = 1
    assert a.choose_batch(tied) == 1
    for index in range(len(original)):
        failed = copy.deepcopy(original); failed[index]['passed'] = False
        with pytest.raises(ValueError): a.choose_batch(failed)
    for partial in (original[:-1], original + original[:1]):
        with pytest.raises(ValueError): a.choose_batch(partial)


def test_receipts_cannot_be_replaced(tmp_path):
    path = tmp_path / 'recipe.json'; a.write_once(path, a.RECIPE)
    assert json.loads(path.read_text()) == a.RECIPE
    with pytest.raises(FileExistsError): a.write_once(path, {'passed': True})


def test_wrong_approval_cannot_create_output_or_load_model(tmp_path):
    output = tmp_path / 'acceptance'
    with pytest.raises(ValueError, match='approved'):
        a.main([str(output), '--saved-input-dir', str(tmp_path), '--approved-protocol-sha256', 'wrong'])
    assert not output.exists()


def test_new_approval_and_scope_preserve_historical_data():
    assert a.APPROVED_SHA == '608350de020b9392672142916484afc953e846344fe733f00e0b3c3f27479e09'
    assert a.RECIPE['split'] == 'v7_dev' and a.RECIPE['episodes'] == 12
    assert a.RECIPE['bf16_is_gate'] is False
    assert a.SAVED_HASHES['saved_inputs.json'] == 'a1526e1d9516d6427a5ed037aa14e62e77ce127c9ad4afa8c176427aa045d566'
    cfg = v7_run.V7Config('v7_dev', 'base', 12)
    expected = [key for key in v7_run.expected_trials(cfg) if key[3] == 'CAP0']
    assert len(expected) == 336
    assert len(v7_run.expected_trials(v7_run.V7Config('v7_pilot', 'base', 80))) == 20880


def test_stage_order_fp32_gate_and_descriptive_bf16_then_cap0_before_selection(tmp_path, monkeypatch):
    events = []
    class Model:
        def __init__(self, dtype): self.dtype = dtype
    class Engine:
        def __init__(self, model, *args): self.model = model
        def close(self): events.append('close-' + self.model.dtype)
    torch = SimpleNamespace(float32='fp32', bfloat16='bf16',
        inference_mode=nullcontext, set_num_threads=lambda n: None,
        cuda=SimpleNamespace(is_available=lambda: True, empty_cache=lambda: None))
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.setitem(sys.modules, 'mb.runtime', SimpleNamespace(
        load_model=lambda **kw: events.append('load-' + kw['dtype']) or Model(kw['dtype'])))
    monkeypatch.setattr(a, 'timed_engine_class', lambda path: Engine)
    monkeypatch.setattr(a.chat, 'load_tokenizer', lambda **kw: object())
    monkeypatch.setattr(a.chat, 'encode', lambda *args: [42])
    monkeypatch.setattr(a, 'validated_saved_inputs', lambda *args: (
        {'episodes': list(range(12)), 'prefix_ids': [[1, 2]] * 24, 'attention_spans': [[('P', 0, 2)]] * 24}, {}))
    def comparison(engine, *args, **kw):
        events.append('compare-' + engine.model.dtype)
        return {'passed': engine.model.dtype == 'fp32'}
    monkeypatch.setattr(a.relocation, 'run_comparison', comparison)
    monkeypatch.setattr(a, 'benchmark', lambda *args: events.append('timing') or timings())
    monkeypatch.setattr(a, 'engineering_run', lambda *args: events.append(('cap0', args[-1])) or {'passed': True})
    choose = a.choose_batch
    monkeypatch.setattr(a, 'choose_batch', lambda rows: events.append('select') or choose(rows))
    output = tmp_path / 'passed'
    arguments = [str(output), '--saved-input-dir', str(tmp_path), '--approved-protocol-sha256', a.APPROVED_SHA]
    assert a.main(arguments) == 0
    assert events.index('compare-fp32') < events.index('compare-bf16') < events.index('timing')
    assert events.index('timing') < events.index(('cap0', max(a.BATCHES))) < events.index('select')
    receipt = json.loads((output / 'acceptance.json').read_text())
    assert receipt['passed'] and receipt['selected_batch'] == 12
    assert receipt['bf16_is_gate'] is False and (output / 'pilot.yaml').exists()
    # BF16's returned false was deliberately not used for admission.
    events.clear()
    monkeypatch.setattr(a.relocation, 'run_comparison', lambda *args, **kw: {'passed': False})
    arguments[0] = str(tmp_path / 'failed')
    assert a.main(arguments) == 1
    assert 'load-bf16' not in events and 'timing' not in events and 'select' not in events
    assert not (tmp_path / 'failed/pilot.yaml').exists()
    events.clear()
    monkeypatch.setattr(a.relocation, 'run_comparison', comparison)
    monkeypatch.setattr(a, 'engineering_run', lambda *args: events.append('failed-cap0') or {'passed': False})
    arguments[0] = str(tmp_path / 'failed-cap0')
    assert a.main(arguments) == 1
    assert 'failed-cap0' in events and 'select' not in events
    assert not (tmp_path / 'failed-cap0/pilot.yaml').exists()


def test_saved_fixture_mismatch_fails_before_model_load_or_output_creation(tmp_path, monkeypatch):
    monkeypatch.setattr(a, 'validated_saved_inputs', lambda *args: (_ for _ in ()).throw(ValueError('hash mismatch')))
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='hash'):
        a.main([str(output), '--saved-input-dir', str(tmp_path), '--approved-protocol-sha256', a.APPROVED_SHA])
    assert not output.exists()
