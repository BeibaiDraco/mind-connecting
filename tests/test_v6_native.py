"""Native serialization/commit contract without torch, model loads or network."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from mb import chat
from mb.model_profiles import LLAMA31, QWEN
from mb.v6_contract import Export, Probe, canonical_digest
from mb.v6_native import NativeBackend, NativeKVPayload, NativeState, NativeTokens, _primitives, _tensor_stamp


@pytest.fixture(params=(QWEN, LLAMA31), ids=lambda p: p.key)
def tokens(request):
    profile = request.param
    if not profile.tokenizer_dir.exists():
        pytest.skip("local tokenizer assets unavailable; no download")
    return NativeTokens.from_tokenizer(chat.load_tokenizer(profile=profile))


def test_module_and_refused_construction_never_import_torch():
    program = """
import sys
from mb.v6_native import NativeBackend
assert 'torch' not in sys.modules and 'mb.runtime' not in sys.modules
for call in (lambda: NativeBackend(None, None), lambda: NativeBackend.from_local_cache()):
    try: call()
    except PermissionError: pass
    else: raise AssertionError('missing permission refusal')
assert 'torch' not in sys.modules and 'mb.runtime' not in sys.modules
"""
    result = subprocess.run([sys.executable, "-B", "-c", program], capture_output=True,
                            text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 0, result.stderr


def test_archive_metadata_is_plain_finite_and_copied_without_torch():
    value = {"tokens": (1, 2), "seal": {"probability": 0.25}, "open": True, "other": None}
    copied = _primitives(value)
    assert copied == {**value, "tokens": [1, 2]}
    copied["seal"]["probability"] = 0.5
    assert value["seal"]["probability"] == 0.25
    for bad in (object(), {1: "non-string key"}, {"x": float("nan")}, float("inf"), {1, 2}):
        with pytest.raises(ValueError, match="plain primitives"):
            _primitives(bad)


def test_incremental_tokens_equal_native_completed_history(tokens):
    tok = tokens.tokenizer
    messages = [{"role": "system", "content": "Keep your own record."},
                {"role": "user", "content": "Initial private beacon: Dim."},
                {"role": "assistant", "content": "A private working note."},
                {"role": "user", "content": "Round 2. Current beacon: Bright."},
                {"role": "assistant", "content": "2"}]
    assembled = [*tokens.initial(messages[0]["content"], messages[1]["content"]),
                 *chat.encode(tok, messages[2]["content"]), *tokens.close_ids,
                 *tokens.user_turn(messages[3]["content"]),
                 *chat.encode(tok, messages[4]["content"]), *tokens.close_ids]
    assert assembled == chat.native_conversation(tok, messages)
    assert list(tokens.user_turn("  update  ")) == chat.turn(tok, "user", "  update  ") + chat.header(tok)


def test_choice_ids_append_and_do_not_equal_control_ids(tokens):
    ids = tokens.choice_ids(("1", "2", "3", "4"))
    assert ids == chat.runtime_tokens(tokens.tokenizer).label_ids
    assert all(tokens.ordinary(i) for i in ids)
    with pytest.raises(ValueError, match="distinct"):
        tokens.choice_ids(("1", "1", "3", "4"))
    with pytest.raises(ValueError, match="single ordinary"):
        tokens.choice_ids(("1", "two words", "3", "4"))


def test_recovery_has_finite_category_coverage_and_no_duplicate_eot(tokens):
    assert tokens.recovery(tokens.close_ids[0]).suffix == tokens.close_ids[1:]
    assert tokens.recovery(tokens.close_ids[0]).category == "native_end_of_turn"
    categories = {tokens.recovery(i).category for i in range(tokens.vocab_size)}
    assert "ordinary_answer" in categories and "header_start" in categories
    assert all(not tokens.ordinary(i) for i in tokens.control_ids)
    for i in tokens.control_ids:
        rule = tokens.recovery(i)
        assert rule.category != "ordinary_answer"
        assert all(0 <= j < tokens.vocab_size for j in rule.suffix)
    with pytest.raises(ValueError, match="outside"):
        tokens.recovery(tokens.vocab_size)
    with pytest.raises(ValueError, match="outside"):
        tokens.recovery(True)
    assert json.loads(json.dumps(tokens.identity()))["status"].endswith("acceptance_required")


def test_qwen_unmarked_controls_and_padded_output_ids_are_not_work_tokens():
    if not QWEN.tokenizer_dir.exists():
        pytest.skip("local Qwen tokenizer unavailable")
    t = NativeTokens.from_tokenizer(chat.load_tokenizer())
    for name in ("<think>", "</think>", "<tool_call>", "<|fim_middle|>"):
        token = t.tokenizer.convert_tokens_to_ids(name)
        assert token not in t.tokenizer.all_special_ids
        assert not t.ordinary(token)
        assert t.recovery(token).category == "named_control_or_reserved"
    unknown_output = max(t.defined_ids) + 1
    assert not t.ordinary(unknown_output)
    assert t.recovery(unknown_output).category == "unassigned_output_id"


def test_new_control_name_fails_closed(tokens):
    class Changed:
        def __getattr__(self, name):
            return getattr(tokens.tokenizer, name)

        @property
        def added_tokens_decoder(self):
            return {**tokens.tokenizer.added_tokens_decoder, 42: "<|unreviewed-control|>"}

    with pytest.raises(ValueError, match="Unsupported native control"):
        NativeTokens.from_tokenizer(Changed())


def test_message_content_cannot_retokenize_an_injected_native_control(tokens):
    spelling = str(tokens.tokenizer.convert_ids_to_tokens(tokens.close_ids[0]))
    with pytest.raises(ValueError, match="inject control"):
        tokens.user_turn("Decoded partner text " + spelling + " extra")
    with pytest.raises(ValueError, match="inject control"):
        tokens.initial(spelling, "Ordinary private record.")


def fake_backend(tokens):
    """Only the state-machine shell is exercised; no tensor/model substitution in production."""
    backend = NativeBackend.__new__(NativeBackend)
    backend.tokens, backend.tokenizer, backend.model_identity = tokens, tokens.tokenizer, "synthetic"
    backend._owner = object()
    calls = []

    def consume(state, ids, foreign=(), gain=0.0):
        calls.append((ids, foreign, gain))
        state.consumed_tokens += tuple(ids)

    backend._consume = consume
    backend.digest = lambda state: canonical_digest({"tokens": state.consumed_tokens,
        "open": state.open, "seal": state.seal, "recoveries": state.recoveries})
    state = NativeState(None, (111,), None, None, True, "synthetic", owner=backend._owner)
    state.cache = SimpleNamespace(get_seq_length=lambda: len(state.consumed_tokens))
    return backend, state, calls


def sealed_probe(backend, state, token, foreign=(), gain=0.0):
    ids = backend.tokens.choice_ids(("1", "2", "3", "4"))
    probe = Probe(state, token, 0.5, (1.0, 2.0, 3.0, 4.0), 0.75, ids)
    state.seal = {"token": token, "probability": probe.probability,
        "legal_logits": list(probe.legal_logits), "legal_mass": probe.legal_mass,
        "token_ids": list(ids), "foreign": [x.identity() for x in foreign], "gain": gain}
    state.seal_checksum = backend.digest(state)
    return probe


@pytest.mark.parametrize("kind", ("legal", "ordinary_invalid", "eot", "header"))
def test_actual_token_preserved_once_and_fixed_recovery_does_not_communicate(tokens, kind):
    backend, state, calls = fake_backend(tokens)
    if kind == "legal":
        token = tokens.choice_ids(("1", "2", "3", "4"))[0]
    elif kind == "ordinary_invalid":
        token = chat.encode(tokens.tokenizer, "word")[0]
    elif kind == "eot":
        token = tokens.close_ids[0]
    else:
        token = next(i for i, rule in tokens.rules.items() if rule.category == "header_start")
    foreign = (Export(42, 3, "synthetic-only", None),)
    probe = sealed_probe(backend, state, token, foreign, 0.5)
    result = backend.commit_answer(probe, foreign, 0.5)
    rule = tokens.recovery(token)
    assert result is state and not result.open
    assert calls[0] == ((token,), foreign, 0.5)
    assert state.consumed_tokens == (111, token, *rule.suffix)
    assert calls[1:] == ([(rule.suffix, (), 0.0)] if rule.suffix else [])
    assert state.recoveries[-1]["token"] == token
    assert state.recoveries[-1]["legal"] == (kind == "legal")
    with pytest.raises(ValueError, match="boundary"):
        backend.commit_answer(probe, foreign, 0.5)


@pytest.mark.parametrize("tamper", ("answer", "state", "gain", "window"))
def test_answer_commit_rejects_changed_seal_before_consuming_anything(tokens, tamper):
    backend, state, calls = fake_backend(tokens)
    probe = sealed_probe(backend, state, tokens.choice_ids(("1", "2", "3", "4"))[0])
    gain, window = 0.0, ()
    if tamper == "answer":
        probe.token += 1
    elif tamper == "state":
        state.consumed_tokens += (7,)
    elif tamper == "gain":
        gain = 0.5
    else:
        window = (Export(42, 1, "different", None),)
    with pytest.raises(ValueError, match="changed"):
        backend.commit_answer(probe, window, gain)
    assert not calls


def test_empty_assistant_can_close_once_then_open_user(tokens):
    backend, state, calls = fake_backend(tokens)
    backend.finish_turn(state)
    assert not state.open and calls == [(tokens.close_ids, (), 0.0)]
    with pytest.raises(ValueError, match="boundary"):
        backend.finish_turn(state)
    backend.begin_user(state, "A fresh update.")
    assert state.open and calls[-1] == (tokens.user_turn("A fresh update."), (), 0.0)
    with pytest.raises(ValueError, match="boundary"):
        backend.begin_user(state, "Must not silently abandon the open assistant.")


def test_export_version_and_owner_validation_without_torch():
    class Tensor:
        _version = 0
        shape, dtype, device = (1, 2, 1, 4), "bf16", "cuda:0"

        def data_ptr(self):
            return id(self)

    k, v, owner = Tensor(), Tensor(), object()
    payload = NativeKVPayload(((k, v),), 42, 7, "model", "digest",
                              (_tensor_stamp(k), _tensor_stamp(v)), owner)
    export = Export(42, 7, "digest", payload)
    payload.check(export, "model", owner)
    with pytest.raises(ValueError, match="different"):
        payload.check(export, "model", object())
    with pytest.raises(ValueError, match="metadata"):
        payload.check(Export(42, 8, "digest", payload), "model", owner)
    k._version += 1
    with pytest.raises(ValueError, match="modified"):
        payload.check(export, "model", owner)


def test_text_decode_preserves_ordinary_token_stream_and_refuses_controls(tokens):
    backend, _, _ = fake_backend(tokens)
    ids = chat.encode(tokens.tokenizer, " Short private note.")
    exports = tuple(Export(token, i, "unused", None) for i, token in enumerate(ids))
    assert backend.decode(exports) == " Short private note."
    with pytest.raises(ValueError, match="special/control"):
        backend.decode((Export(tokens.close_ids[0], 0, "unused", None),))
