"""CPU array doubles test data movement, not model inference or GPU performance."""

import json
import sys
from collections import Counter, OrderedDict
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from mb.v6_contract import Export
from mb.v6_native import NativeBackend, NativeKVPayload, _tensor_hash, _tensor_stamp
from mb.v6_performance import (PerformanceBackend, copy_payload_to_cpu,
                               profile_backend, workload_audit)
from mb.v6_run import SyntheticBackend


class ArrayTensor:
    def __init__(self, array, api, device="cuda", version=None):
        self.array, self.api, self.device = array, api, device
        self.version = [0] if version is None else version

    @property
    def _version(self):
        return self.version[0]

    @property
    def shape(self):
        return self.array.shape

    @property
    def dtype(self):
        return self.array.dtype

    def data_ptr(self):
        return self.array.ctypes.data

    def numel(self):
        return self.array.size

    def element_size(self):
        return self.array.itemsize

    def detach(self):
        return self

    def contiguous(self):
        return ArrayTensor(np.ascontiguousarray(self.array), self.api, self.device, self.version)

    def reshape(self, *shape):
        return ArrayTensor(self.array.reshape(*shape), self.api, self.device, self.version)

    def view(self, dtype):
        return ArrayTensor(self.array.view(dtype), self.api, self.device, self.version)

    def to(self, device):
        if device == self.device:
            return self
        self.api.counts["transfers"] += 1
        return ArrayTensor(self.array.copy(), self.api, device)

    def cpu(self):
        return self.to("cpu")

    def clone(self):
        return ArrayTensor(self.array.copy(), self.api, self.device)

    def split(self, size):
        return [self[i:i + size] for i in range(0, self.numel(), size)]

    def numpy(self):
        return self.array

    def __getitem__(self, index):
        return ArrayTensor(self.array[index], self.api, self.device, self.version)

    def add_(self, value):
        self.array += value
        self.version[0] += 1


@pytest.fixture
def tensor_api(monkeypatch):
    api = SimpleNamespace(uint8=np.uint8, counts=Counter())

    def cat(tensors, dim=0):
        api.counts["cat"] += 1
        assert len({t.device for t in tensors}) == 1
        return ArrayTensor(np.concatenate([t.array for t in tensors], axis=dim), api, tensors[0].device)

    api.cat = cat
    monkeypatch.setitem(sys.modules, "torch", api)
    return api


def tensors(api, n=4, dtype=np.float32, device="cuda"):
    return tuple(ArrayTensor((np.arange(4, dtype=dtype) + i).reshape(1, 1, 1, 4), api, device)
                 for i in range(n))


def backend(api):
    obj = PerformanceBackend.__new__(PerformanceBackend)
    obj.model_identity, obj._owner = "a" * 64, object()
    obj.tokens = SimpleNamespace(ordinary=lambda token: 100 <= token < 200)
    obj.modules = {1: 0, 2: 1}
    obj.device = "cuda"
    obj.model = SimpleNamespace(config=SimpleNamespace(hidden_size=8, num_attention_heads=2,
        num_key_value_heads=1, head_dim=4), parameters=lambda: iter(tensors(api, 1)))
    obj._window_cache, obj.performance_counts = OrderedDict(), Counter()
    return obj


def export(obj, api, position=0):
    ts = tensors(api)
    meta = {"token": 100, "position": position, "model_identity": obj.model_identity}
    digest = _tensor_hash(meta, ts)
    payload = NativeKVPayload(tuple(zip(ts[::2], ts[1::2])), 100, position,
        obj.model_identity, digest, tuple(_tensor_stamp(t) for t in ts), obj._owner)
    return Export(100, position, digest, payload)


def test_packed_copy_matches_reference_without_source_aliases(tensor_api):
    source = tensors(tensor_api, 8)
    copies = copy_payload_to_cpu(source, tensor_api=tensor_api, max_bytes=64)
    assert tensor_api.counts["transfers"] == 2
    for before, after in zip(source, copies):
        assert after.device == "cpu" and after.array.flags.c_contiguous
        assert after.shape == before.shape and after.dtype == before.dtype
        np.testing.assert_array_equal(after.array, before.array)
    source[0].add_(99)
    assert copies[0].array.flat[0] == 0
    copies[1].add_(88)
    assert copies[0].array.flat[0] == 0 and source[1].array.flat[0] == 1


def test_mixed_dtype_device_noncontiguous_oversize_and_empty(tensor_api):
    source = (*tensors(tensor_api, 1, np.uint8), *tensors(tensor_api, 1, np.float64),
              ArrayTensor(np.arange(24, dtype=np.float32).reshape(4, 6)[:, ::2], tensor_api),
              *tensors(tensor_api, 1, device="cpu"))
    copies = copy_payload_to_cpu(source, tensor_api=tensor_api, max_bytes=32)
    assert tensor_api.counts["transfers"] == 3
    for a, b in zip(source, copies):
        np.testing.assert_array_equal(a.array, b.array)
        assert b.dtype == a.dtype and b.array.flags.c_contiguous
    assert copy_payload_to_cpu((), tensor_api=tensor_api) == []
    with pytest.raises(ValueError):
        copy_payload_to_cpu(source, tensor_api=tensor_api, max_bytes=0)


def test_foreign_cache_preserves_values_gain_and_bound(tensor_api):
    obj = backend(tensor_api)
    first, second = export(obj, tensor_api), export(obj, tensor_api, 1)
    expected = NativeBackend._foreign(obj, (first, second), .5)
    tensor_api.counts.clear()
    result = obj._foreign((first, second), .5)
    assert tensor_api.counts["cat"] == 4
    assert obj._foreign((first, second), 1.) is result
    assert tensor_api.counts["cat"] == 4
    assert obj._foreign((first, second), 0.) == ()
    for a, b in zip(expected, result):
        for x, y in zip(a, b):
            np.testing.assert_array_equal(x.array, y.array)
    obj._foreign((first,), .5)
    obj._foreign((second,), .5)
    assert len(obj._window_cache) == 2
    obj._foreign((first, second), .5)
    assert obj.performance_counts == {"window_hits": 1, "window_misses": 4}


@pytest.mark.parametrize("what", ("source", "cached", "metadata", "owner", "shape"))
def test_foreign_cache_does_not_bypass_validation(tensor_api, what):
    obj = backend(tensor_api)
    item = export(obj, tensor_api)
    cached = obj._foreign((item,), .5)
    if what == "source":
        item.payload.layers[0][0].add_(1)
    elif what == "cached":
        cached[0][0].add_(1)
    elif what == "metadata":
        item = replace(item, position=1)
    elif what == "owner":
        obj._owner = object()
    else:
        obj.model.config.num_key_value_heads = 2
    with pytest.raises(ValueError):
        obj._foreign((item,), .5)


@pytest.mark.parametrize("gain", (-1., float("nan"), float("inf")))
def test_invalid_gain_rejected_even_without_exports(tensor_api, gain):
    with pytest.raises(ValueError):
        backend(tensor_api)._foreign((), gain)


def test_archives_keep_logical_hashes_and_save_validated_copy(tensor_api):
    obj = backend(tensor_api)
    item = export(obj, tensor_api)
    reference = NativeBackend.__new__(NativeBackend)
    reference.__dict__.update(obj.__dict__)
    ref = reference.dump_export(item)
    tensor_api.counts.clear()
    fast = obj.dump_export(item)
    assert tensor_api.counts["transfers"] == 1
    assert {k: v for k, v in ref.items() if k != "tensors"} == {
        k: v for k, v in fast.items() if k != "tensors"}
    for a, b in zip(ref["tensors"], fast["tensors"]):
        np.testing.assert_array_equal(a.array, b.array)
    # A content mutation that evades a version counter must still fail the hash.
    item.payload.layers[0][0].array.flat[0] += 1
    with pytest.raises(ValueError, match="checksum"):
        obj.dump_export(item)


def test_profiler_counts_internal_calls_and_restores_after_failure():
    obj = SyntheticBackend()
    before = dict(obj.__dict__)
    with profile_backend(obj) as stats:
        state = obj.create("System", "User")
        obj.step(state, (), .5)
        with pytest.raises(ValueError, match="already"):
            with profile_backend(obj):
                pass
        with pytest.raises(ValueError):
            obj.begin_user(state, "still open")
    assert obj.__dict__ == before
    assert stats["calls"]["step"] == 1 and stats["calls"]["digest"] == 2
    assert stats["failures"] == {"begin_user": 1}
    assert set(stats) == {"version", "calls", "host_seconds_inclusive", "failures",
                          "linked_calls", "wall_seconds"}
    assert "System" not in json.dumps(stats)
    with pytest.raises(RuntimeError):
        with profile_backend(obj):
            raise RuntimeError("outer failure")
    assert obj.__dict__ == before


def test_profiler_restores_existing_flag_and_instance_method():
    obj = SyntheticBackend()
    obj._v6_profile_active = False
    custom = lambda state: "fixed-test-digest"
    obj.digest = custom
    before = dict(obj.__dict__)
    with profile_backend(obj) as stats:
        assert obj.digest({}) == "fixed-test-digest"
    assert obj.__dict__ == before and obj.digest is custom
    assert stats["calls"] == {"digest": 1}


@pytest.mark.parametrize("text", (False, True))
def test_actual_scheduler_workload(text):
    result = workload_audit(text_reference=text)
    assert result["scientific_data"] is False
    assert result["paired_work_periods"] == 80
    assert result["work_tokens_at_frozen_clock"] == 10240
    assert result["readouts"] == 328 + 24 * text
    assert result["archives"] == {"pair": 4, "tape": 12}
    assert result["readouts_by_kind"]["goal"] == 144
    assert result["preparation_tokens_at_frozen_clock"] == 160 + 32 * text
    assert result["text_tokens_at_frozen_clock"] == 768 * text
