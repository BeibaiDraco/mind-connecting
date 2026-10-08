"""Serializer contract tests with a synthetic tokenizer, plus actual Qwen regression.

The fixture exercises the adapter; it does not certify gated Llama assets. Those
must pass the same checks when they are obtained through official access.
"""

import pytest
from tokenizers import Tokenizer, decoders, models, pre_tokenizers
from transformers import PreTrainedTokenizerFast

from mb import chat, tasks
from mb.model_profiles import LLAMA31, QWEN


# Minimal test template with the native format's relevant properties: system date,
# one initial BOS, trimmed completed content, and consecutive user messages.
TEST_TEMPLATE = """{{ bos_token }}{% if messages[0]['role'] == 'system' %}
{% set system = messages[0]['content'] %}{% set rest = messages[1:] %}
{% else %}{% set system = '' %}{% set rest = messages %}{% endif %}
{{ '<|start_header_id|>system<|end_header_id|>\\n\\nToday Date: ' + date_string + '\\n\\n' + system|trim + '<|eot_id|>' }}
{% for message in rest %}{{ '<|start_header_id|>' + message['role'] + '<|end_header_id|>\\n\\n' + message['content']|trim + '<|eot_id|>' }}{% endfor %}
{% if add_generation_prompt %}{{ '<|start_header_id|>assistant<|end_header_id|>\\n\\n' }}{% endif %}"""
# Whitespace in the fixture source is not part of the rendered conversation.
TEST_TEMPLATE = TEST_TEMPLATE.replace("%}\n", "%}").replace("}}\n", "}}")


@pytest.fixture
def native_tok():
    special = ["<|begin_of_text|>", "<|end_of_text|>", "<|eot_id|>", "<|eom_id|>",
               "<|start_header_id|>", "<|end_header_id|>"]
    alphabet = sorted(pre_tokenizers.ByteLevel.alphabet())
    vocab = {s: i for i, s in enumerate(special + alphabet)}
    backend = Tokenizer(models.BPE(vocab, []))
    backend.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False)
    backend.decoder = decoders.ByteLevel()
    tok = PreTrainedTokenizerFast(tokenizer_object=backend, bos_token=special[0], eos_token=special[2],
                                 additional_special_tokens=special[1:])
    tok.chat_template = TEST_TEMPLATE
    generation = {"bos_token_id": tok.bos_token_id,
                  "eos_token_id": [tok.convert_tokens_to_ids(t) for t in special[1:4]]}
    chat.validate_tokenizer_profile(tok, LLAMA31, generation)
    return tok, generation


def test_legacy_qwen_tokens_and_native_prefix_stay_identical():
    tok = chat.load_tokenizer()
    assert chat.profile_for_tokenizer(tok) == QWEN
    assert chat.runtime_tokens(tok) == chat.TokenSpec(chat.EOS_IDS, chat.ENDOFTEXT, chat.LABEL_IDS)
    ep = tasks.make_episodes(1, "chat-profile-test")[0]
    messages = [{"role": "system", "content": tasks.SYSTEM_PROMPT},
                {"role": "user", "content": tasks.private_user_message(ep, "A")}]
    assert tasks.private_prefix_ids(tok, ep, "A") == chat.native_conversation(
        tok, messages, add_generation_prompt=True)


def test_native_incremental_tasks_match_full_reference(native_tok):
    tok, _ = native_tok
    ep = tasks.make_episodes(1, "native-contract-test")[0]
    note, reflection = "I keep my record.", "I remember the rule."
    question = tasks.make_question(tok, ep, "A", "START", 0)
    segmented = [*tasks.private_prefix_ids(tok, ep, "A"), *chat.encode(tok, note), *chat.close(tok),
                 *tasks.reflection_turn_ids(tok), *chat.encode(tok, reflection), *question.suffix_ids]
    messages = [{"role": "system", "content": tasks.SYSTEM_PROMPT},
                {"role": "user", "content": tasks.private_user_message(ep, "A")},
                {"role": "assistant", "content": note},
                {"role": "user", "content": tasks.REFLECTION_PROMPT},
                {"role": "assistant", "content": reflection},
                {"role": "user", "content": question.user_content}]
    assert segmented == chat.native_conversation(tok, messages, add_generation_prompt=True)
    assert segmented.count(tok.bos_token_id) == 1
    assert "26 Jul 2024" in tok.decode(segmented)
    assert chat.runtime_tokens(tok).label_ids != chat.LABEL_IDS


def test_native_lang_consecutive_users_and_prefix_stability(native_tok):
    tok, _ = native_tok
    messages = [{"role": "system", "content": "Separate sources."},
                {"role": "user", "content": "Private record."},
                {"role": "assistant", "content": "A note."}]
    prefix = chat.native_conversation(tok, messages)
    shared = tasks.lang_user_message("Nova", "B's text.", "tag")
    extra = [{"role": "user", "content": shared},
             {"role": "user", "content": tasks.REFLECTION_PROMPT}]
    whole = chat.native_conversation(tok, messages + extra, add_generation_prompt=True)
    assert whole == prefix + chat.turn(tok, "user", shared) + tasks.reflection_turn_ids(tok)


def test_native_label_ids_append_at_actual_task_response_positions(native_tok):
    tok, _ = native_tok
    ep = tasks.make_episodes(1, "native-label-test")[0]
    for q in tasks.readout_questions(tok, ep, "A", rotations=[0, 1]):
        rendered = tok.decode(q.suffix_ids, clean_up_tokenization_spaces=False)
        for label, value in zip(chat.LABELS, chat.runtime_tokens(tok).label_ids):
            assert chat.encode(tok, rendered + label) == list(q.suffix_ids) + [value]


def test_contract_validation_does_not_certify_assets(native_tok):
    tok, _ = native_tok
    with pytest.raises(ValueError, match="manifest-verified"):
        chat.require_verified_tokenizer(tok, LLAMA31)
    with pytest.raises(ValueError, match="profiles differ"):
        chat.require_verified_tokenizer(tok, QWEN)


def test_incomplete_stop_set_and_prefix_changing_template_fail(native_tok):
    tok, generation = native_tok
    with pytest.raises(ValueError, match="complete native end-token"):
        chat.validate_tokenizer_profile(tok, LLAMA31, generation | {"eos_token_id": [tok.eos_token_id]})
    tok.chat_template = "{{ messages|length }}" + TEST_TEMPLATE
    with pytest.raises(ValueError, match="prefix-stable|incremental assembly"):
        chat.validate_tokenizer_profile(tok, LLAMA31, generation)


def test_native_added_special_controls_need_not_be_in_special_token_map(native_tok):
    tok, generation = native_tok
    # Official Llama puts end_of_text/eom in the added-token metadata even when
    # neither appears among the named special_tokens_map entries.
    hidden = {"<|end_of_text|>", "<|eom_id|>"}
    tok.additional_special_tokens = [s for s in tok.additional_special_tokens if s not in hidden]
    for text in hidden:
        token = tok.convert_tokens_to_ids(text)
        assert token not in tok.all_special_ids
        assert tok.added_tokens_decoder[token].special
    chat.validate_tokenizer_profile(tok, LLAMA31, generation)
    assert set(chat.runtime_tokens(tok).eos_ids) == set(generation["eos_token_id"])


def test_loading_missing_new_assets_fails_before_tokenizer_download(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("must not call AutoTokenizer before asset validation")
    monkeypatch.setattr(chat.AutoTokenizer, "from_pretrained", forbidden)
    with pytest.raises(FileNotFoundError):
        chat.load_tokenizer(str(tmp_path), profile=LLAMA31, manifest_path=tmp_path / "absent.json")
