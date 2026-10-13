"""Unrun hardware tests using tiny random CUDA models, never downloaded weights.

Passing these does not certify the real pinned checkpoints, control-token recovery
or the scientific scheduler. Real-model acceptance remains a separate prerequisite.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
pytestmark = [pytest.mark.gpu,
              pytest.mark.skipif(not torch.cuda.is_available(), reason="authorized CUDA host required")]

from mb import chat  # noqa: E402
from mb.model_profiles import LLAMA31, QWEN  # noqa: E402
from mb.v6_contract import Probe  # noqa: E402
from mb.v6_native import NativeBackend, _AttentionContext, _FORWARD, _attention  # noqa: E402


@pytest.fixture(params=(QWEN, LLAMA31), ids=lambda p: p.model_type)
def backend(request):
    from transformers import LlamaConfig, LlamaForCausalLM, Qwen3Config, Qwen3ForCausalLM

    profile = request.param
    if not profile.tokenizer_dir.exists():
        pytest.skip("local tokenizer assets absent; this test never downloads")
    tok = chat.load_tokenizer(profile=profile)
    config_cls, model_cls = ((Qwen3Config, Qwen3ForCausalLM) if profile == QWEN
                             else (LlamaConfig, LlamaForCausalLM))
    cfg = config_cls(vocab_size=profile.vocab_size, hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2, head_dim=8,
        max_position_embeddings=4096, attention_dropout=0.0)
    cfg._attn_implementation = "sdpa"
    torch.manual_seed(719)
    model = model_cls(cfg).to(device="cuda", dtype=torch.float32).eval()
    yield NativeBackend(model, tok, hardware_acceptance_authorized=True)
    del model


def assert_cache_equal(left, right):
    assert left.get_seq_length() == right.get_seq_length()
    for a, b in zip(left.layers, right.layers):
        assert torch.equal(a.keys, b.keys)
        assert torch.equal(a.values, b.values)


def test_no_link_and_zero_gain_match_native_same_shape(backend):
    from transformers import DynamicCache

    state = backend.create("Follow your private record.", "My beacon is Dim.")
    ids = torch.tensor([state.consumed_tokens], device=backend.device)
    cache = DynamicCache(config=backend.model.config)
    with torch.no_grad():
        ref = backend.model.model(input_ids=ids, attention_mask=torch.ones_like(ids),
            position_ids=torch.arange(ids.shape[1], device=backend.device)[None],
            cache_position=torch.arange(ids.shape[1], device=backend.device),
            past_key_values=cache, use_cache=True)
        ref_logits = backend.model.lm_head(ref.last_hidden_state[:, -1]).float()
    assert torch.equal(state.native_logits, ref_logits)
    assert_cache_equal(state.cache, cache)
    sender = backend.create("A different record.", "My beacon is Bright.")
    foreign = (backend.step(sender, (), 0.0),)
    for _ in range(3):
        token = backend.step(state, foreign, 0.0).token
        pos = cache.get_seq_length()
        with torch.no_grad():
            ref = backend.model.model(input_ids=torch.tensor([[token]], device=backend.device),
                attention_mask=torch.ones(1, pos + 1, device=backend.device, dtype=torch.long),
                position_ids=torch.tensor([[pos]], device=backend.device),
                cache_position=torch.tensor([pos], device=backend.device), past_key_values=cache, use_cache=True)
            ref_logits = backend.model.lm_head(ref.last_hidden_state[:, -1]).float()
        assert torch.equal(state.native_logits, ref_logits)
        assert_cache_equal(state.cache, cache)
    assert _FORWARD.get() is None and backend.model.config._attn_implementation == "sdpa"


@pytest.mark.parametrize("mask_type", ("none", "bool", "float"))
def test_foreign_attention_equals_independent_joint_softmax(mask_type):
    torch.manual_seed(91)
    module = SimpleNamespace(num_key_value_groups=2, is_causal=True)
    q = torch.randn(1, 4, 1, 8, device="cuda")
    own_k, own_v = [torch.randn(1, 2, 5, 8, device="cuda") for _ in range(2)]
    foreign_k, foreign_v = [torch.randn(1, 2, 3, 8, device="cuda") for _ in range(2)]
    mask = None
    if mask_type != "none":
        mask = torch.tensor([[[[True, False, True, True, True]]]], device="cuda")
        if mask_type == "float":
            mask = torch.where(mask, 0.0, -torch.inf)
    ctx = _AttentionContext({id(module): 0}, ((foreign_k, foreign_v),), 0.7)
    handle = _FORWARD.set(ctx)
    try:
        result, _ = _attention(module, q, own_k, own_v, mask)
    finally:
        _FORWARD.reset(handle)
    k = torch.cat([own_k, foreign_k], 2).repeat_interleave(2, dim=1)
    v = torch.cat([own_v, foreign_v], 2).repeat_interleave(2, dim=1)
    logits = torch.matmul(q, k.transpose(-1, -2)) * (8 ** -0.5)
    logits[..., 5:] += __import__("math").log(0.7)
    if mask is not None:
        if mask.dtype == torch.bool:
            logits[..., :5] = logits[..., :5].masked_fill(~mask, -torch.inf)
        else:
            logits[..., :5] += mask
    expected = (torch.softmax(logits, -1) @ v).transpose(1, 2)
    assert torch.allclose(result, expected, atol=2e-6, rtol=2e-6)
    assert ctx.seen == {0}


def test_snapshot_exports_delay_and_zero_change_replay(backend):
    initial = [backend.create("Act privately.", text) for text in ("Beacon Dim.", "Beacon Bright.")]
    live = [backend.clone(x) for x in initial]
    windows = [(), ()]
    archived_windows, traces = [], []
    for _ in range(4):
        # The two source windows are fixed before either history advances.
        old = tuple(windows)
        archived_windows.append(old)
        exports = [backend.step(live[i], old[1-i], 0.5) for i in range(2)]
        windows = [(*old[i], exports[i])[-16:] for i in range(2)]
        traces.append([backend.digest(s) for s in live])
    replay = [backend.clone(x) for x in initial]
    replay_a = ()
    for tick in range(4):
        # J stays active; only its outgoing stream is replaced by recorded J.
        next_a = backend.step(replay[0], archived_windows[tick][1], 0.5)
        backend.step(replay[1], replay_a, 0.5)
        replay_a = (*replay_a, next_a)[-16:]
        assert [backend.digest(s) for s in replay] == traces[tick]
    assert all(backend.digest(a) != backend.digest(b) for a, b in zip(initial, live))
    original = backend.digest(live[0])
    clone = backend.clone(live[0])
    clone.cache.layers[0].keys.add_(1)
    assert backend.digest(live[0]) == original
    # Old exports are independent copies even after continued sender generation.
    window = windows[0]
    backend.step(live[0], (), 0)
    backend._foreign(window, 0.5)
    window[0].payload.layers[0][0].add_(1)
    with pytest.raises(ValueError, match="modified"):
        backend._foreign(window, 0.5)


def test_sealed_held_window_questions_and_actual_answer_continuation(backend):
    receiver = backend.create("Keep your own record.", "Beacon Dim.")
    sender = backend.create("Keep your own record.", "Beacon Bright.")
    foreign = tuple(backend.step(sender, (), 0) for _ in range(2))
    root_digest = backend.digest(receiver)
    sender_digest = backend.digest(sender)
    question = "Choose one ID.\n1. Left\n2. Right\n3. Up\n4. Down"
    one = backend.probe(receiver, question, ("1", "2", "3", "4"), foreign, 0.5)
    two = backend.probe(receiver, question, ("1", "2", "3", "4"), foreign, 0.5)
    assert one.token == two.token and one.legal_logits == two.legal_logits
    assert backend.digest(one.state) == backend.digest(two.state)
    assert backend.digest(receiver) == root_digest and backend.digest(sender) == sender_digest
    before_tokens = one.state.consumed_tokens
    action = one.token
    continued = backend.commit_answer(one, foreign, 0.5)
    assert continued.consumed_tokens == (*before_tokens, action, *backend.tokens.recovery(action).suffix)
    assert not continued.open
    backend.begin_user(continued, "Round 2. Your current beacon is Dim. Goal unchanged.")
    assert continued.open
    backend.step(continued, (), 0)
    assert backend.digest(receiver) == root_digest


def test_forward_failure_clears_context_and_invalidates_partial_state(backend):
    state = backend.create("Record.", "Beacon Dim.")

    def fail(*_):
        raise RuntimeError("synthetic decoder failure")

    hook = backend.model.model.layers[0].register_forward_hook(fail)
    try:
        with pytest.raises(RuntimeError, match="synthetic decoder"):
            backend.step(state, (), 0)
    finally:
        hook.remove()
    assert _FORWARD.get() is None
    assert backend.model.config._attn_implementation == "sdpa" and state.failed
    with pytest.raises(ValueError, match="failed forward"):
        backend.clone(state)
    with pytest.raises(ValueError, match="failed forward"):
        backend.dump_state(state)


def weights_only_roundtrip(value):
    from io import BytesIO

    stream = BytesIO()
    torch.save(value, stream)
    stream.seek(0)
    return torch.load(stream, weights_only=True, map_location="cpu")


def test_state_and_incremental_tape_archive_roundtrip_rebinds_owner(backend):
    state = backend.create("Private record.", "Beacon Dim.")
    sender = backend.create("Private record.", "Beacon Bright.")
    window = tuple(backend.step(sender, (), 0) for _ in range(3))
    backend.step(state, window, 0.5)
    saved = weights_only_roundtrip({"state": backend.dump_state(state),
        "tape": [backend.dump_export(e) for e in window]})
    restored_backend = NativeBackend(backend.model, backend.tokenizer,
                                     hardware_acceptance_authorized=True)
    assert restored_backend.model_identity == backend.model_identity
    assert restored_backend._owner is not backend._owner
    with pytest.raises(ValueError, match="different model"):
        restored_backend._foreign(window, 0.5)
    restored = restored_backend.load_state(saved["state"])
    tape = tuple(restored_backend.load_export(x) for x in saved["tape"])
    assert restored_backend.digest(restored) == backend.digest(state)
    assert [e.identity() for e in tape] == [e.identity() for e in window]
    for _ in range(3):
        left = backend.step(state, window, 0.5)
        right = restored_backend.step(restored, tape, 0.5)
        assert left.identity() == right.identity()
        assert backend.digest(state) == restored_backend.digest(restored)
    # Archive buffers and returned native tensors never alias.
    original = tape[0].payload.layers[0][0].clone()
    saved["tape"][0]["tensors"][0].add_(1)
    assert torch.equal(tape[0].payload.layers[0][0], original)
    tape[0].payload.layers[0][0].add_(1)
    with pytest.raises(ValueError, match="modified"):
        restored_backend._foreign(tape, 0.5)


def test_sealed_probe_and_closed_recovery_survive_archive(backend):
    state = backend.create("Keep the record.", "Beacon Dim.")
    sender = backend.create("Keep the record.", "Beacon Bright.")
    foreign = (backend.step(sender, (), 0),)
    probe = backend.probe(state, "Choose: 1 left, 2 right, 3 up, 4 down.",
                          ("1", "2", "3", "4"), foreign, 0.5)
    archived = weights_only_roundtrip(backend.dump_state(probe.state))
    restored = backend.load_state(archived)
    replay_probe = Probe(restored, probe.token, probe.probability, probe.legal_logits,
                         probe.legal_mass, probe.token_ids)
    direct = backend.commit_answer(probe, foreign, 0.5)
    replay = backend.commit_answer(replay_probe, foreign, 0.5)
    assert backend.digest(direct) == backend.digest(replay)
    closed = backend.load_state(weights_only_roundtrip(backend.dump_state(replay)))
    assert not closed.open and closed.recoveries == replay.recoveries
    assert backend.digest(closed) == backend.digest(replay)
    backend.begin_user(closed, "Next round. Beacon Bright.")
    backend.begin_user(replay, "Next round. Beacon Bright.")
    assert backend.digest(closed) == backend.digest(replay)


@pytest.mark.parametrize("kind,tamper", [(k, t) for k in ("state", "export")
                                       for t in ("tensor", "metadata", "model", "checksum")])
def test_archive_tamper_rejected_before_device_restore(backend, monkeypatch, kind, tamper):
    state = backend.create("Private record.", "Beacon Dim.")
    export = backend.step(state, (), 0)
    archive = backend.dump_state(state) if kind == "state" else backend.dump_export(export)
    if tamper == "tensor":
        archive["tensors"][0].view(-1)[0] += 1
    elif tamper == "metadata":
        if kind == "state":
            archive["metadata"]["state"]["tokens"][0] += 1
        else:
            archive["metadata"]["position"] += 1
    elif tamper == "model":
        archive["model_identity"] = "0" * 64
    else:
        archive["sha256"] = "0" * 64
    # Any successful parse would next validate shapes and allocate native tensors.
    monkeypatch.setattr(backend, "_check_archived_tensors", lambda *_a, **_k:
                        pytest.fail("corruption passed the CPU archive checksum"))
    with pytest.raises(ValueError, match="identity|checksum"):
        (backend.load_state if kind == "state" else backend.load_export)(archive)


def test_same_config_different_weights_cannot_restore_state(backend):
    state = backend.create("Private record.", "Beacon Dim.")
    archive = backend.dump_state(state)
    with torch.no_grad():
        next(backend.model.parameters()).view(-1)[0].add_(1)
    changed = NativeBackend(backend.model, backend.tokenizer, hardware_acceptance_authorized=True)
    assert changed.weights_digest != backend.weights_digest
    assert changed.model_identity != backend.model_identity
    with pytest.raises(ValueError, match="model identity"):
        changed.load_state(archive)


def test_valid_outer_hash_does_not_admit_failed_or_wrong_inner_identity(backend):
    from copy import deepcopy

    state = backend.create("Private record.", "Beacon Dim.")
    export = backend.step(state, (), 0)
    saved = backend.dump_state(state)
    failed = deepcopy(saved["metadata"])
    failed["state"]["failed"] = True
    with pytest.raises(ValueError, match="failed native state"):
        backend.load_state(backend._archive("state", failed, tuple(saved["tensors"])))
    bad_seal = deepcopy(saved["metadata"])
    bad_seal["seal_checksum"] = saved["metadata"]["state_digest"]
    with pytest.raises(ValueError, match="Unsealed"):
        backend.load_state(backend._archive("state", bad_seal, tuple(saved["tensors"])))
    tape = backend.dump_export(export)
    wrong = deepcopy(tape["metadata"])
    wrong["position"] += 1
    with pytest.raises(ValueError, match="payload checksum"):
        backend.load_export(backend._archive("export", wrong, tuple(tape["tensors"])))
