"""Engineering-only relocation oracle through the production joint KV read.

The reference uses a real negative-position donor prefill, never key rephasing.
Imports remain torch-free until a GPU operation is explicitly requested.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from mb.conditions import ArmConfig
from mb.kv_geometry import bank_metadata

LOGIT_ATOL, LOGIT_RTOL, MASS_ATOL = 3e-3, 2e-3, 2e-3
TICKS = 8


def read_saved_inputs(path: Path, expected_sha: str, *, expected_episodes: int = 12) -> dict:
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha:
        raise ValueError('saved input hash mismatch')
    data = json.loads(payload)
    expected_ids = [f'v7_dev-0-{i:05d}' for i in range(expected_episodes)]
    if data.get('episodes') != expected_ids:
        raise ValueError('saved inputs must be the original ordered dev episodes')
    prefixes, spans = data.get('prefix_ids', []), data.get('attention_spans', [])
    if len(prefixes) != 2 * expected_episodes or len(spans) != len(prefixes):
        raise ValueError('saved inputs require interleaved complete A/B pairs')
    for seq, declarations in zip(prefixes, spans):
        if not seq or any(type(t) is not int or t < 0 for t in seq):
            raise ValueError('invalid saved token IDs')
        bank_metadata(seq, declarations)
    return data


def reference_layout(prefixes: list[list[int]], pad_id: int) -> tuple[list, list, list, list[int]]:
    if not prefixes or len(prefixes) % 2 or any(not x for x in prefixes):
        raise ValueError('relocation needs nonempty complete A/B pairs')
    width = max(map(len, prefixes))
    offsets = [0 if row % 2 == 0 else -len(seq) for row, seq in enumerate(prefixes)]
    ids, masks, positions = [], [], []
    for seq, offset in zip(prefixes, offsets):
        pad = width - len(seq)
        ids.append([pad_id] * pad + list(seq))
        masks.append([0] * pad + [1] * len(seq))
        positions.append([max(col - pad, 0) + offset for col in range(width)])
    return ids, masks, positions, offsets


def prefill_relocated_reference(engine, prefixes: list[list[int]], native):
    import torch
    from transformers import DynamicCache
    from mb.runtime import cache_layers, select_rows

    ids, masks, positions, offsets = reference_layout(prefixes, engine.pad_id)
    tensor = lambda values: torch.tensor(values, dtype=torch.long, device=engine.device)
    if not torch.equal(tensor(masks), native.attn):
        raise ValueError('reference prefill padding differs from the native snapshot')
    cache = DynamicCache(config=engine.model.config)
    engine.hook.mode, engine.hook.write_enabled, engine.hook.injection = 'prefill', False, None
    try:
        out = engine.model.model(input_ids=tensor(ids), attention_mask=native.attn,
            position_ids=tensor(positions), past_key_values=cache, use_cache=True)
        seed = engine.hook.captured.clone()
    finally:
        engine.hook.mode = 'tick'
    logits = engine._lm_logits(out.last_hidden_state[:, -1])
    reference = select_rows(native, list(range(native.rows)), engine.model.config)
    for (key, value), (offset_key, offset_value) in zip(cache_layers(reference.cache), cache_layers(cache), strict=True):
        key[1::2], value[1::2] = offset_key[1::2], offset_value[1::2]
    reference.next_pos[1::2] += tensor(offsets)[1::2]
    reference.logits[1::2] = logits[1::2]
    reference.pending[1::2] = engine.no_eos_argmax(logits)[1::2]
    reference.ema[1::2] = seed[1::2]
    reference.mailbox[1::2] = engine._messages(seed)[1::2]
    # A must start from exactly the same state, not a separately rounded prefill.
    for name in ('attn', 'next_pos', 'logits', 'pending', 'ema', 'mailbox'):
        if not torch.equal(getattr(reference, name)[0::2], getattr(native, name)[0::2]):
            raise RuntimeError('receiver state changed while constructing the reference')
    for ref_layer, base_layer in zip(cache_layers(reference.cache), cache_layers(native.cache), strict=True):
        if any(not torch.equal(a[0::2], b[0::2]) for a, b in zip(ref_layer, base_layer)):
            raise RuntimeError('receiver cache changed while constructing the reference')
    return reference


def trace(engine, state, spans: list[list], token: int, *, translated: bool) -> list[dict[str, np.ndarray]]:
    import torch
    from mb.runtime import make_plan

    arm = ArmConfig('ONE', interface='kv', kv_scope='P', gain=2., kv_log_spans=True,
                    kv_position='before_own' if translated else 'native')
    plan = make_plan(arm, ['A', 'B'] * (state.rows // 2), [None] * state.rows, None,
                     engine.device, d=engine.d)
    rows = [dict(logits=[], own=[], donor=[]) for _ in range(state.rows // 2)]
    state.phase = 'C'
    for _ in range(TICKS):
        tokens = torch.full((state.rows,), token, dtype=torch.long, device=engine.device)
        logits, _, z = engine.step(state, tokens, None, plan.kv)
        engine.advance(state, logits, z, 1, update_messages=True)
        mass = engine.last_kv_span_mass
        cfg = engine.model.config
        if mass is None or tuple(mass.shape[:3]) != (state.rows, cfg.num_hidden_layers, cfg.num_attention_heads):
            raise RuntimeError('missing layer/head summaries in the production read')
        for pair, result in enumerate(rows):
            row = pair * 2
            own, donor = len(spans[row]), len(spans[row + 1])
            if mass.shape[-1] < own + donor:
                raise RuntimeError('missing declared span summaries')
            result['logits'].append(logits[row].float().detach().cpu().numpy().copy())
            result['own'].append(mass[row, :, :, :own].float().detach().cpu().numpy().copy())
            result['donor'].append(mass[row, :, :, own:own + donor].float().detach().cpu().numpy().copy())
    return [{name: np.stack(values) for name, values in row.items()} for row in rows]


def error_summary(actual, expected, *, atol: float, rtol: float = 0.) -> dict[str, Any]:
    a, b = np.asarray(actual, dtype=np.float64), np.asarray(expected, dtype=np.float64)
    if a.shape != b.shape or not a.size:
        raise ValueError('comparison arrays must be nonempty and identically shaped')
    finite = bool(np.isfinite(a).all() and np.isfinite(b).all())
    result = {'finite': finite, 'within': False, 'max_abs': None, 'rms': None,
              'violations': None, 'elements': int(a.size), 'atol': atol, 'rtol': rtol}
    if finite:
        difference = np.abs(a - b)
        violations = int(np.count_nonzero(difference > atol + rtol * np.abs(b)))
        result.update(within=violations == 0, max_abs=float(difference.max()),
                      rms=float(np.sqrt(np.mean(difference ** 2))), violations=violations)
    return result


def compare_traces(actual: list[dict], expected: list[dict], *, batch: int, row_start: int) -> list[dict]:
    result = []
    for index, (a, b) in enumerate(zip(actual, expected, strict=True)):
        if any(a[k].shape[0] != TICKS or b[k].shape[0] != TICKS for k in ('logits', 'own', 'donor')):
            raise ValueError('all eight teacher-forced ticks are required')
        for tick in range(TICKS):
            row = {'batch': batch, 'episode_index': row_start // 2 + index, 'tick': tick + 1}
            for name in ('logits', 'own', 'donor'):
                row[name] = error_summary(a[name][tick], b[name][tick],
                    atol=LOGIT_ATOL if name == 'logits' else MASS_ATOL,
                    rtol=LOGIT_RTOL if name == 'logits' else 0.)
            result.append(row)
    return result


def fp32_passed(rows: list[dict]) -> bool:
    return bool(rows) and all(row[name]['within'] for row in rows for name in ('logits', 'own', 'donor'))


def run_comparison(engine, prefixes: list[list[int]], spans: list[list], root: Path, *,
                   precision: str, token: int, batches: tuple[int, ...] = (1, 4, 8, 12)) -> dict:
    from mb.runtime import select_rows

    if precision not in ('fp32', 'bf16') or batches[0] != 1:
        raise ValueError('comparison requires a declared precision and batch-1 baseline first')
    compared, padding, provenance, baseline = [], [], [], []
    for batch in batches:
        for start in range(0, len(prefixes), 2 * batch):
            sequences, declared = prefixes[start:start + 2 * batch], spans[start:start + 2 * batch]
            native = engine.prefill(sequences, attention_spans=declared)
            translated = select_rows(native, list(range(native.rows)), engine.model.config)
            reference = prefill_relocated_reference(engine, sequences, native)
            provenance.append({'batch': batch, 'row_start': start, 'banks': native.kv_banks,
                'reference_prefill_offsets': [0 if i % 2 == 0 else -len(seq) for i, seq in enumerate(sequences)],
                'translated_read_offsets': [-len(sequences[i + 1]) for i in range(0, len(sequences), 2)],
                'reference_read_offset': 0, 'receiver_start_positions': native.next_pos[0::2].tolist()})
            engine.tag = f'relocation/{precision}/translated/batch{batch}'
            actual = trace(engine, translated, declared, token, translated=True)
            del translated
            engine.tag = f'relocation/{precision}/reference/batch{batch}'
            expected = trace(engine, reference, declared, token, translated=False)
            del reference
            compared.extend(compare_traces(actual, expected, batch=batch, row_start=start))
            del actual, expected
            if precision == 'bf16':
                engine.tag = f'padding/bf16/native/batch{batch}'
                current = trace(engine, native, declared, token, translated=False)
                if batch == 1:
                    baseline.extend(current)
                padding.extend(compare_traces(current, baseline[start // 2:start // 2 + len(current)],
                                              batch=batch, row_start=start))
            del native
    expected_keys = {(b, ep, tick) for b in batches for ep in range(len(prefixes) // 2)
                     for tick in range(1, TICKS + 1)}
    keys = [(x['batch'], x['episode_index'], x['tick']) for x in compared]
    if len(keys) != len(expected_keys) or set(keys) != expected_keys:
        raise RuntimeError('relocation coverage is incomplete or duplicated')
    result = {'precision': precision, 'is_gate': precision == 'fp32',
        'passed': fp32_passed(compared) if precision == 'fp32' else None,
        'comparison': compared, 'native_padding_variability': padding, 'provenance': provenance,
        'teacher_forced_token': token, 'ticks': TICKS, 'batches': list(batches),
        'cache_tensors_rephased_in_reference': False, 'receiver_initial_state_exact': True}
    with (root / f'relocation_{precision}.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    return result
