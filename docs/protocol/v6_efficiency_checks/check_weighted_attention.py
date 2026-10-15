"""CPU-only algebra checks for an unapproved V6 implementation proposal.

No model, torch, empirical measurements or scientific admission. FP64 agreement
does not imply equality to the frozen BF16 execution or a fused CUDA kernel.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import numpy as np


def softmax(scores: np.ndarray) -> np.ndarray:
    shifted = scores - scores.max(axis=-1, keepdims=True)
    weights = np.exp(shifted)
    return weights / weights.sum(axis=-1, keepdims=True)


def lse(scores: np.ndarray) -> np.ndarray:
    peak = scores.max(axis=-1, keepdims=True)
    return peak + np.log(np.exp(scores - peak).sum(axis=-1, keepdims=True))


def scores_and_values(q: np.ndarray, k: np.ndarray, v: np.ndarray,
                      fk: np.ndarray, fv: np.ndarray, prefix: int
                      ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    groups = q.shape[1] // k.shape[1]
    own_k, own_v = (np.repeat(x, groups, axis=1) for x in (k, v))
    foreign_k, foreign_v = (np.repeat(x, groups, axis=1) for x in (fk, fv))
    own = np.einsum('bhtd,bhsd->bhts', q, own_k) / math.sqrt(q.shape[-1])
    causal = np.arange(k.shape[2])[None, :] <= prefix + np.arange(q.shape[2])[:, None]
    own = np.where(causal[None, None, :, :], own, -np.inf)
    foreign = np.einsum('bhtd,bhfd->bhtf', q, foreign_k) / math.sqrt(q.shape[-1])
    return own, own_v, foreign, foreign_v


def mixture(q: np.ndarray, k: np.ndarray, v: np.ndarray, fk: np.ndarray,
            fv: np.ndarray, prefix: int, gain: float) -> np.ndarray:
    own, own_v, foreign, foreign_v = scores_and_values(q, k, v, fk, fv, prefix)
    own_out = np.einsum('bhts,bhsd->bhtd', softmax(own), own_v)
    if gain == 0 or fk.shape[2] == 0:
        return own_out
    foreign = foreign + math.log(gain)
    foreign_out = np.einsum('bhtf,bhfd->bhtd', softmax(foreign), foreign_v)
    own_lse, foreign_lse = lse(own), lse(foreign)
    # Stable partition weight without exponential overflow in stress cases.
    beta = np.exp(foreign_lse - np.logaddexp(own_lse, foreign_lse))
    return own_out + beta * (foreign_out - own_out)


def joint(q: np.ndarray, k: np.ndarray, v: np.ndarray, fk: np.ndarray,
          fv: np.ndarray, prefix: int, gain: float) -> np.ndarray:
    own, own_v, foreign, foreign_v = scores_and_values(q, k, v, fk, fv, prefix)
    if gain == 0 or fk.shape[2] == 0:
        logits, values = own, own_v
    else:
        logits = np.concatenate((own, foreign + math.log(gain)), axis=-1)
        values = np.concatenate((own_v, foreign_v), axis=2)
    return np.einsum('bhts,bhsd->bhtd', softmax(logits), values)


def check() -> dict:
    rng = np.random.default_rng(731040)
    count, max_error, isolation_checks, causal_checks = 0, 0.0, 0, 0
    for batch, queries, prefix, window, gain, groups, scale in itertools.product(
            (1, 2, 4), (1, 2, 5), (0, 7), (0, 1, 16), (0.0, .25, .5, 1.0), (1, 2), (1., 20.)):
        kv_heads, dim = 2, 8
        q = rng.normal(size=(batch, kv_heads * groups, queries, dim)) * scale
        k = rng.normal(size=(batch, kv_heads, prefix + queries, dim)) * scale
        v = rng.normal(size=k.shape)
        fk = rng.normal(size=(batch, kv_heads, window, dim)) * scale
        fv = rng.normal(size=fk.shape)
        left, right = mixture(q, k, v, fk, fv, prefix, gain), joint(q, k, v, fk, fv, prefix, gain)
        error = float(np.max(np.abs(left - right)))
        max_error = max(max_error, error)
        assert np.allclose(left, right, atol=1e-11, rtol=1e-11)
        separate = np.concatenate([joint(q[i:i+1], k[i:i+1], v[i:i+1], fk[i:i+1],
                                         fv[i:i+1], prefix, gain) for i in range(batch)])
        assert np.allclose(right, separate, atol=1e-11, rtol=1e-11)
        if batch > 1:
            changed_k = k.copy(); changed_k[-1] += 123
            changed_v = v.copy(); changed_v[-1] -= 45
            changed = joint(q, changed_k, changed_v, fk, fv, prefix, gain)
            assert np.array_equal(right[:-1], changed[:-1])
            isolation_checks += 1
        if queries > 1:
            changed_k = k.copy(); changed_k[:, :, prefix+1:, :] += 89
            changed_v = v.copy(); changed_v[:, :, prefix+1:, :] -= 57
            changed = joint(q, changed_k, changed_v, fk, fv, prefix, gain)
            assert np.array_equal(right[:, :, 0, :], changed[:, :, 0, :])
            causal_checks += 1
        count += 1
    # A generic triangular mask over own+foreign incorrectly removes a held
    # foreign key. This simple negative control must distinguish that error.
    q = np.ones((1, 2, 1, 8)); k = np.zeros((1, 2, 1, 8)); v = k.copy()
    fk = k.copy(); fv = np.ones_like(fk)
    correct = joint(q, k, v, fk, fv, 0, 1.)
    wrongly_masked = joint(q, k, v, fk, fv, 0, 0.)
    assert np.all(correct == .5) and np.all(wrongly_masked == 0.)
    return {'scientific_data': False, 'model_executed': False, 'gpu_executed': False,
            'purpose': 'FP64 algebra and mask/lane checks only', 'cases': count,
            'max_absolute_difference': max_error, 'lane_isolation_checks': isolation_checks,
            'own_future_mask_checks': causal_checks, 'bad_foreign_mask_detected': True,
            'native_bf16_equivalence_established': False, 'speedup_established': False}


if __name__ == '__main__':
    result = check()
    destination = Path(__file__).with_name('results.json')
    with destination.open('x') as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps(result, sort_keys=True))
