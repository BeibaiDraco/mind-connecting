"""CPU-only mathematical and contract checks, not GPU/native acceptance."""

import itertools
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import numpy as np
import pytest

from mb.v6_efficient import (JointKernel, Layout, TickSnapshot, diagnostic_error,
                             numpy_joint, scalar_oracle)
from mb.v6_efficient_native import EfficientPrototype, cohort_shape


def arrays(layout, seed=41):
    rng = np.random.default_rng(seed)
    return tuple(rng.normal(size=shape) for shape in layout.shapes)


@pytest.mark.parametrize("batch,queries,prefix,foreign,gain", tuple(itertools.product(
    (1, 2, 4, 8), (1, 2, 4), (0, 7), (0, 1, 16), (0., .25, .5, 1.))))
def test_independent_scalar_oracle(batch, queries, prefix, foreign, gain):
    layout = Layout(batch, 4, 2, queries, prefix, foreign, 4, gain)
    values = arrays(layout)
    before = tuple(x.copy() for x in values)
    expected, actual = scalar_oracle(layout, values), numpy_joint(layout, values)
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-12)
    for left, right in zip(before, values):
        np.testing.assert_array_equal(left, right)


def test_hand_computed_mask_and_gqa_cases_detect_wrong_semantics():
    layout = Layout(1, 4, 2, 2, 0, 1, 1, 1.)
    values = tuple(np.zeros(shape) for shape in layout.shapes)
    values[2][0, 0, :, 0] = (10, 20)
    values[2][0, 1, :, 0] = (30, 60)
    values[4][0, :, 0, 0] = (100, 300)
    expected = np.array([[[[55], [130/3]], [[55], [130/3]],
                          [[165], [390/3]], [[165], [390/3]]]])
    np.testing.assert_allclose(scalar_oracle(layout, values), expected)
    np.testing.assert_allclose(numpy_joint(layout, values), expected)
    # Missing the held foreign key or masking own future keys incorrectly must
    # disagree with these hand-computed targets.
    assert expected[0, 0, 0, 0] != 10
    assert expected[0, 0, 0, 0] != 130/3
    assert expected[0, 1, 0, 0] != expected[0, 2, 0, 0]


def test_lane_isolation_permutation_future_mask_and_fixed_window_chunking():
    layout = Layout(4, 4, 2, 4, 7, 16, 8, .5)
    values = arrays(layout)
    actual = numpy_joint(layout, values)
    changed = tuple(x.copy() for x in values)
    for tensor in changed:
        tensor[-1] += 100
    np.testing.assert_array_equal(actual[:-1], numpy_joint(layout, changed)[:-1])
    changed = tuple(x.copy() for x in values)
    changed[1][:, :, layout.prefix+1:] += 100
    changed[2][:, :, layout.prefix+1:] -= 100
    np.testing.assert_array_equal(actual[:, :, 0], numpy_joint(layout, changed)[:, :, 0])
    permutation = np.array([3, 1, 0, 2])
    np.testing.assert_array_equal(actual[permutation], numpy_joint(layout, tuple(x[permutation] for x in values)))
    pieces = []
    for token in range(layout.queries):
        one = replace(layout, queries=1, prefix=layout.prefix+token)
        q, k, v, fk, fv = values
        sliced = (q[:, :, token:token+1], k[:, :, :one.own], v[:, :, :one.own], fk, fv)
        pieces.append(scalar_oracle(one, sliced))
    np.testing.assert_allclose(actual, np.concatenate(pieces, axis=2), atol=1e-12, rtol=1e-12)


@pytest.mark.parametrize("field,value", [("batch", 0), ("batch", True), ("queries", 0),
    ("prefix", -1), ("foreign", 17), ("heads", 3), ("gain", float("nan")),
    ("gain", float("inf")), ("gain", -.5), ("gain", True)])
def test_layout_rejects_unsupported_inputs(field, value):
    with pytest.raises(ValueError):
        replace(Layout(2, 4, 2, 2, 7, 16, 4, .5), **{field: value})


def test_arrays_and_error_report_fail_closed():
    layout = Layout(2, 4, 2, 2, 7, 1, 4, .5)
    values = arrays(layout)
    with pytest.raises(ValueError):
        scalar_oracle(layout, (values[0][:1], *values[1:]))
    values[0].flat[0] = np.nan
    for function in (scalar_oracle, numpy_joint):
        with pytest.raises(ValueError):
            function(layout, values)
    report = diagnostic_error(np.zeros(2), np.ones(2), 2.)
    assert report["max_abs_over_value_scale"] == .5 and report["admitted"] is False
    with pytest.raises(ValueError):
        diagnostic_error(np.zeros(2), np.ones(3), 2.)


def test_paired_tick_freezes_all_inputs_and_publishes_atomically():
    state = TickSnapshot(0, ((("A0",), ("B0",)), (("C0",), ("D0",))))
    incoming = state.incoming()
    assert incoming == (("B0",), ("A0",), ("D0",), ("C0",))
    with pytest.raises(ValueError):
        state.publish(("A1",))
    after = state.publish(("A1", "B1", "C1", "D1"), window=1)
    assert state.incoming() == incoming
    assert after.incoming() == (("B1",), ("A1",), ("D1",), ("C1",))
    assert after.tick == 1
    with pytest.raises(FrozenInstanceError):
        state.tick = 3
    with pytest.raises(ValueError):
        TickSnapshot(0, [(("A",), ("B",))])


def test_cohort_refuses_ragged_or_aliased_histories_and_tokens():
    a = SimpleNamespace(consumed_tokens=(1, 2), cache=object())
    b = SimpleNamespace(consumed_tokens=(3, 4), cache=object())
    assert cohort_shape((a, b), ((1, 2), (3, 4)), 10) == (2, 2)
    for states, tokens in [((a, a), ((1,), (2,))), ((a, b), ((1,), (2, 3))),
                           ((a, b), ((1,), (True,))), ((a, b), ((1,), (10,))),
                           ((a, b), ((1,), [2])), ([a, b], ((1,), (2,)))]:
        with pytest.raises(ValueError):
            cohort_shape(states, tokens, 10)
    b.consumed_tokens = (1,)
    with pytest.raises(ValueError):
        cohort_shape((a, b), ((1,), (2,)), 10)


def test_imports_default_loading_and_kernel_selection_are_inert():
    output = subprocess.check_output([sys.executable, "-c",
        "import mb.v6_efficient_native; import sys; assert 'torch' not in sys.modules"], text=True)
    assert output == ""
    with pytest.raises(PermissionError):
        EfficientPrototype.from_local_cache(hardware_acceptance_authorized=True)
    with pytest.raises(ValueError):
        JointKernel("automatic")
