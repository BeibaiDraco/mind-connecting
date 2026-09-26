"""Token-level ChatML assembly for Qwen3-4B-Instruct-2507 (protocol v0.5 §2, §4–5).

Sequences are built from segments that meet at special tokens. The tokenizer splits on
special tokens before running BPE, so segment-wise encoding equals whole-text encoding;
tests check this against ``tokenizer.apply_chat_template``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from transformers import AutoTokenizer, PreTrainedTokenizerBase

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKENIZER_DIR = REPO_ROOT / "materials" / "tokenizer"

IM_START = 151644
IM_END = 151645
ENDOFTEXT = 151643
EOS_IDS: tuple[int, ...] = (IM_END, ENDOFTEXT)
LABELS: tuple[str, ...] = ("1", "2", "3", "4")
LABEL_IDS: tuple[int, ...] = (16, 17, 18, 19)
ASSISTANT_HEADER: tuple[int, ...] = (IM_START, 77091, 198)


@lru_cache(maxsize=4)
def load_tokenizer(path: str | None = None) -> PreTrainedTokenizerBase:
    return AutoTokenizer.from_pretrained(str(path or TOKENIZER_DIR))


def encode(tok: PreTrainedTokenizerBase, text: str) -> list[int]:
    return tok.encode(text, add_special_tokens=False)


def turn(tok: PreTrainedTokenizerBase, role: str, content: str) -> list[int]:
    """A complete message: ``<|im_start|>{role}\\n{content}<|im_end|>\\n``."""
    return [IM_START, *encode(tok, f"{role}\n{content}"), IM_END, *encode(tok, "\n")]


def header(tok: PreTrainedTokenizerBase, role: str = "assistant") -> list[int]:
    """An opened message waiting for content: ``<|im_start|>{role}\\n``."""
    return [IM_START, *encode(tok, f"{role}\n")]


def close(tok: PreTrainedTokenizerBase) -> list[int]:
    """Closes the currently open message: ``<|im_end|>\\n``."""
    return [IM_END, *encode(tok, "\n")]


def readout_suffix(tok: PreTrainedTokenizerBase, question: str) -> list[int]:
    """Tokens the recipient consumes in phase R: close its turn, ask, open the answer."""
    return [*close(tok), *turn(tok, "user", question), *header(tok, "assistant")]
