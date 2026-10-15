"""Prepared CUDA equivalence tests; importing never downloads a model."""

from collections import Counter, OrderedDict
from io import BytesIO

import pytest

torch = pytest.importorskip("torch")
pytestmark = [pytest.mark.gpu,
              pytest.mark.skipif(not torch.cuda.is_available(), reason="authorized CUDA host required")]

from test_v6_native_gpu import backend  # noqa: E402, F401
from mb.v6_performance import (PerformanceBackend, copy_payload_to_cpu,
                               profile_backend)  # noqa: E402


def candidate(reference):
    # Compare the exact same model/owner sequentially; construction authority
    # comes from the authorized reference fixture, never this test helper.
    obj = PerformanceBackend.__new__(PerformanceBackend)
    obj.__dict__.update(reference.__dict__)
    obj._window_cache, obj.performance_counts = OrderedDict(), Counter()
    return obj


def assert_archive_equal(a, b):
    assert {k: v for k, v in a.items() if k != "tensors"} == {
        k: v for k, v in b.items() if k != "tensors"}
    assert len(a["tensors"]) == len(b["tensors"])
    assert all(torch.equal(x, y) for x, y in zip(a["tensors"], b["tensors"]))


@pytest.mark.parametrize("gain", (0., .25, .5, 1.))
def test_reference_and_candidate_exact_states_readouts_archives(backend, gain):
    fast = candidate(backend)
    root = backend.create("Keep your own record.", "Your beacon is Dim. Your goal is G0.")
    donor = backend.create("Keep your own record.", "Your beacon is Bright. Your goal is G1.")
    foreign = tuple(backend.step(donor, (), 0.) for _ in range(16))
    parent_hash = backend.digest(root)
    left, right = backend.clone(root), fast.clone(root)
    for _ in range(3):
        a, b = backend.step(left, foreign, gain), fast.step(right, foreign, gain)
        assert a.identity() == b.identity()
        assert backend.digest(left) == fast.digest(right)
        assert_archive_equal(backend.dump_export(a), fast.dump_export(b))
    for question in ("Choose one ID.\n1. Left\n2. Right\n3. Up\n4. Down",
                     "What is your recorded goal?\n1. G0\n2. G1\n3. G2\n4. G3"):
        a = backend.probe(left, question, ("1", "2", "3", "4"), foreign, gain)
        with profile_backend(fast):
            b = fast.probe(right, question, ("1", "2", "3", "4"), foreign, gain)
        assert (
            a.token, a.probability, a.legal_logits, a.legal_mass, a.token_ids) == (
            b.token, b.probability, b.legal_logits, b.legal_mass, b.token_ids)
        assert backend.digest(a.state) == fast.digest(b.state)
        old, new = backend.dump_state(a.state), fast.dump_state(b.state)
        assert_archive_equal(old, new)
        buf = BytesIO()
        torch.save(new, buf)
        buf.seek(0)
        restored = backend.load_state(torch.load(buf, weights_only=True, map_location="cpu"))
        assert backend.digest(restored) == backend.digest(a.state)
        a = backend.commit_answer(a, foreign, gain)
        b = fast.commit_answer(b, foreign, gain)
        assert backend.digest(a) == fast.digest(b)
    assert backend.digest(root) == parent_hash
    if gain:
        assert fast.performance_counts["window_hits"] > 0


def test_real_tensor_packing_bf16_alignment_ownership_and_serialization():
    tensors = (
        torch.arange(3, device="cuda", dtype=torch.uint8),
        torch.arange(10, device="cuda", dtype=torch.bfloat16).reshape(2, 5),
        torch.arange(10, device="cuda", dtype=torch.bfloat16).reshape(2, 5) + 1,
        torch.arange(21, device="cuda", dtype=torch.float32).reshape(3, 7)[:, ::2],
        torch.arange(80, device="cuda", dtype=torch.bfloat16),  # Oversized fallback.
        torch.arange(4, device="cpu", dtype=torch.bfloat16),
        torch.zeros((0, 2), device="cuda", dtype=torch.bfloat16),
    )
    reference = [t.detach().to("cpu").contiguous().clone() for t in tensors]
    copies = copy_payload_to_cpu(tensors, tensor_api=torch, max_bytes=64)
    for a, b in zip(reference, copies):
        assert torch.equal(a, b) and a.dtype == b.dtype and b.is_contiguous()
        assert b.device.type == "cpu" and not b.requires_grad
    buf = BytesIO()
    torch.save(copies, buf)
    buf.seek(0)
    restored = torch.load(buf, weights_only=True, map_location="cpu")
    assert all(torch.equal(a, b) for a, b in zip(reference, restored))
    tensors[1].add_(20)
    copies[2].add_(30)
    assert torch.equal(reference[1], copies[1])
    assert torch.equal(reference[5], copies[5])
    copies[5].add_(1)
    assert torch.equal(reference[5], tensors[5])
