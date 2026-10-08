"""Token-level conversation assembly with an unchanged legacy Qwen default.

Sequences are built from segments that meet at special tokens. The tokenizer splits on
special tokens before running BPE, so segment-wise encoding equals whole-text encoding;
tests check this against ``tokenizer.apply_chat_template``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Sequence

from transformers import AutoTokenizer, PreTrainedTokenizerBase

from mb.model_profiles import ModelProfile, QWEN, resolve_profile

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKENIZER_DIR = REPO_ROOT / "materials" / "tokenizer"

IM_START = 151644
IM_END = 151645
ENDOFTEXT = 151643
EOS_IDS: tuple[int, ...] = (IM_END, ENDOFTEXT)
LABELS: tuple[str, ...] = ("1", "2", "3", "4")
LABEL_IDS: tuple[int, ...] = (16, 17, 18, 19)
ASSISTANT_HEADER: tuple[int, ...] = (IM_START, 77091, 198)


@dataclass(frozen=True)
class TokenSpec:
    eos_ids: tuple[int, ...]
    pad_id: int
    label_ids: tuple[int, ...]
    bos_id: int | None = None


@lru_cache(maxsize=4)
def load_tokenizer(path: str | None = None, *, profile: str | ModelProfile | None = None,
                   manifest_path: str | Path | None = None) -> PreTrainedTokenizerBase:
    selected = resolve_profile(profile)
    root = Path(path) if path is not None else selected.tokenizer_dir
    if selected == QWEN:
        tok = AutoTokenizer.from_pretrained(str(root))
        if (tok.convert_tokens_to_ids("<|im_start|>") != IM_START
                or tok.convert_tokens_to_ids("<|im_end|>") != IM_END
                or tuple(tok.encode(s, add_special_tokens=False) for s in LABELS)
                != tuple([i] for i in LABEL_IDS)):
            raise ValueError("tokenizer does not match the frozen Qwen ChatML/label contract")
        tok._mb_profile = selected
        return tok
    manifest = selected.validate_manifest(manifest_path, root)
    tok = AutoTokenizer.from_pretrained(str(root), local_files_only=True, trust_remote_code=False)
    generation = json.loads((root / "generation_config.json").read_text())
    validate_tokenizer_profile(tok, selected, generation)
    tok._mb_asset_manifest = manifest
    tok._mb_assets_validated = True
    return tok


def profile_for_tokenizer(tok: PreTrainedTokenizerBase) -> ModelProfile:
    profile = getattr(tok, "_mb_profile", None)
    if profile is not None:
        return resolve_profile(profile)
    # Retain support for legacy Qwen tokenizers constructed directly by callers,
    # without silently treating an unknown tokenizer as Qwen.
    if (tok.convert_tokens_to_ids("<|im_start|>") == IM_START
            and tok.convert_tokens_to_ids("<|im_end|>") == IM_END):
        return QWEN
    raise ValueError("tokenizer has no validated model profile; use chat.load_tokenizer")


def runtime_tokens(tok: PreTrainedTokenizerBase) -> TokenSpec:
    if profile_for_tokenizer(tok) == QWEN:
        return TokenSpec(EOS_IDS, ENDOFTEXT, LABEL_IDS)
    spec = getattr(tok, "_mb_token_spec", None)
    if not isinstance(spec, TokenSpec):
        raise ValueError("new-model tokenizer has not passed token/serialization checks")
    return spec


def require_verified_tokenizer(tok: PreTrainedTokenizerBase, profile: str | ModelProfile | None) -> None:
    selected = resolve_profile(profile)
    if profile_for_tokenizer(tok) != selected:
        raise ValueError("tokenizer and model profiles differ")
    if selected != QWEN and not getattr(tok, "_mb_assets_validated", False):
        raise ValueError("new-model execution requires manifest-verified native tokenizer assets")


def native_conversation(tok: PreTrainedTokenizerBase, messages: Sequence[Mapping[str, str]],
                        *, add_generation_prompt: bool = False) -> list[int]:
    """Reference serialization using the actual tokenizer's native template.

    Native Llama strips the boundaries of completed text messages. Generated token
    streams are retained exactly in the runtime cache; they are never decoded,
    stripped and retokenized to construct a later turn.
    """
    selected = profile_for_tokenizer(tok)
    kwargs = {"date_string": selected.date_string} if selected.date_string is not None else {}
    return list(tok.apply_chat_template(list(messages), tokenize=True,
                                       add_generation_prompt=add_generation_prompt, **kwargs))


def _native_prefix(tok: PreTrainedTokenizerBase) -> list[int]:
    return native_conversation(tok, [{"role": "system", "content": ""}])


def _after_prefix(prefix: list[int], whole: list[int]) -> list[int]:
    if whole[:len(prefix)] != prefix:
        raise ValueError("native chat template is not incrementally prefix-stable")
    return whole[len(prefix):]


def validate_tokenizer_profile(tok: PreTrainedTokenizerBase, profile: str | ModelProfile,
                                generation: Mapping[str, object]) -> None:
    """Validate real token IDs and native serialization without loading a model.

    This alone is not an asset-integrity certificate; load_tokenizer additionally
    verifies all files before marking the tokenizer usable for model execution.
    """
    selected = resolve_profile(profile)
    if selected == QWEN:
        raise ValueError("legacy Qwen uses its frozen ChatML contract")
    tok._mb_assets_validated = False
    if not tok.get_chat_template():
        raise ValueError("the native tokenizer must supply a chat template")
    def special(text: str) -> int:
        ids = encode(tok, text)
        value = tok.convert_tokens_to_ids(text)
        if len(ids) != 1 or ids[0] != value or value not in tok.all_special_ids:
            raise ValueError(f"missing single special token {text}")
        return value

    bos = special("<|begin_of_text|>")
    expected_eos = {special(s) for s in ("<|end_of_text|>", "<|eot_id|>", "<|eom_id|>")}
    eos_value = generation.get("eos_token_id")
    eos = tuple(eos_value) if isinstance(eos_value, (list, tuple)) else (eos_value,)
    if set(eos) != expected_eos or len(eos) != len(expected_eos):
        raise ValueError("generation config must supply the complete native end-token set")
    if tok.bos_token_id != bos or generation.get("bos_token_id") != bos:
        raise ValueError("tokenizer and generation config disagree about BOS")
    if tok.eos_token_id not in expected_eos:
        raise ValueError("tokenizer EOS is absent from the generation stop set")
    label_tokens = [encode(tok, label) for label in LABELS]
    if any(len(ids) != 1 for ids in label_tokens):
        raise ValueError("each answer label must be a single token")
    labels = tuple(ids[0] for ids in label_tokens)
    if len(set(labels)) != 4 or set(labels) & (expected_eos | {bos}):
        raise ValueError("answer labels must be distinct non-control tokens")
    pad = generation.get("pad_token_id")
    if pad is None:
        pad = tok.pad_token_id
    if pad is None:
        pad = special("<|end_of_text|>")
    if not isinstance(pad, int) or not 0 <= pad < selected.vocab_size:
        raise ValueError("invalid native pad token")
    tok._mb_profile = selected
    tok._mb_token_spec = TokenSpec(tuple(int(i) for i in eos), pad, labels, bos)
    try:
        messages = [{"role": "system", "content": "Keep the records separate."},
                    {"role": "user", "content": "Record one."},
                    {"role": "assistant", "content": "The first record."},
                    {"role": "user", "content": "A shared message."},
                    {"role": "user", "content": "Reflect on the record."},
                    {"role": "assistant", "content": "My reflection."},
                    {"role": "user", "content": "Answer with the option number only."}]
        segmented = [t for msg in messages for t in turn(tok, msg["role"], msg["content"])]
        whole = native_conversation(tok, messages)
        if segmented != whole or whole.count(bos) != 1 or whole[0] != bos:
            raise ValueError("native complete turns do not match incremental assembly with one BOS")
        opened = native_conversation(tok, messages, add_generation_prompt=True)
        if [*whole, *header(tok)] != opened:
            raise ValueError("native assistant generation header is not prefix-stable")
        # Answer labels must also append cleanly after the actual native header.
        rendered = tok.decode(opened, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if encode(tok, rendered) != opened:
            raise ValueError("native reference conversation does not round-trip its token IDs")
        for label, label_id in zip(LABELS, labels):
            if encode(tok, rendered + label) != opened + [label_id]:
                raise ValueError("answer labels do not append as one token at the response position")
    except Exception:
        del tok._mb_profile
        del tok._mb_token_spec
        raise


def encode(tok: PreTrainedTokenizerBase, text: str) -> list[int]:
    return tok.encode(text, add_special_tokens=False)


def turn(tok: PreTrainedTokenizerBase, role: str, content: str) -> list[int]:
    """A complete message: ``<|im_start|>{role}\\n{content}<|im_end|>\\n``."""
    if profile_for_tokenizer(tok) != QWEN:
        if role == "system":
            return native_conversation(tok, [{"role": role, "content": content}])
        prefix = _native_prefix(tok)
        return _after_prefix(prefix, native_conversation(tok, [{"role": "system", "content": ""},
                                                              {"role": role, "content": content}]))
    return [IM_START, *encode(tok, f"{role}\n{content}"), IM_END, *encode(tok, "\n")]


def header(tok: PreTrainedTokenizerBase, role: str = "assistant") -> list[int]:
    """An opened message waiting for content: ``<|im_start|>{role}\\n``."""
    if profile_for_tokenizer(tok) != QWEN:
        if role != "assistant":
            raise ValueError("native incremental headers are defined only for assistant generation")
        return _after_prefix(_native_prefix(tok), native_conversation(
            tok, [{"role": "system", "content": ""}], add_generation_prompt=True))
    return [IM_START, *encode(tok, f"{role}\n")]


def close(tok: PreTrainedTokenizerBase) -> list[int]:
    """Closes the currently open message: ``<|im_end|>\\n``."""
    if profile_for_tokenizer(tok) != QWEN:
        return encode(tok, "<|eot_id|>")
    return [IM_END, *encode(tok, "\n")]


def readout_suffix(tok: PreTrainedTokenizerBase, question: str) -> list[int]:
    """Tokens the recipient consumes in phase R: close its turn, ask, open the answer."""
    return [*close(tok), *turn(tok, "user", question), *header(tok, "assistant")]
