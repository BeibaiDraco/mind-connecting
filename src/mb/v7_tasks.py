"""V7 placement-study materials (contract ``v7-placement-v1``); opt-in.

Adds a donor-only neutral fact with its use question, a detection probe, a table-card variant
and a new-scenario variant for prespecified generalization, and declared token spans for
attention diagnostics. Legacy tasks, prompts and question texts keep their frozen meaning: the
base variant is the v1 second-person card with one added note line.
"""

from __future__ import annotations

import hashlib
import itertools
import random
from dataclasses import dataclass, replace
from typing import Any

from transformers import PreTrainedTokenizerBase

from mb import chat, provenance_tasks, tasks
from mb.model_profiles import QWEN

CONTRACT = "v7-placement-v1"
VARIANTS: tuple[str, ...] = ("base", "table", "laptop")
FACT_HOLDERS: tuple[str, ...] = ("B", "A", "none")  # who carries the fact; the others get the filler
FACT_VALUES: tuple[int, ...] = (6, 7, 8, 9)
NEW_QIDS: tuple[str, ...] = ("USE", "DETECT")
VARIANT_QIDS: dict[str, tuple[str, ...]] = {
    "base": ("START", "WORD", "NOW", "ACC_RULE", "PROV_SELF_RULE", "USE", "DETECT", "CAP0", "CAP1", "U_OPEN"),
    "table": ("START", "ACC_RULE", "USE", "CAP0", "CAP1"),
    "laptop": ("START", "ACC_RULE", "USE", "CAP0", "CAP1"),
}
CONSTRUCT: dict[str, str] = {"USE": "use", "DETECT": "detection", "PROV_SELF_RULE": "provenance_rule"}

# The fact and its filler have equal token length in context, so A's and B's cards stay aligned.
_NOTES = {
    "delivery": ("Note: the courier adds a ${n} surcharge for each package sent on a Thursday.",
                 "Note: the courier office is closed on Sundays, on public holidays and in early January."),
    "laptop": ("Note: the supplier adds a ${n} fee for each laptop delivered on a Thursday.",
               "Note: the supplier's warehouse is closed on Sundays and on all public holidays too."),
}
_USE_STEMS = {
    "delivery": ("The courier adds a surcharge for each package sent on a Thursday. "
                 "What is the total surcharge for two packages sent on a Thursday?"),
    "laptop": ("The supplier adds a fee for each laptop delivered on a Thursday. "
               "What is the total fee for two laptops delivered on a Thursday?"),
}
DETECT_STEM = ("In some runs of this study, another participant's memory is inserted into yours. "
               "In this run, was another participant's memory inserted into yours?")
DETECT_SCALE: tuple[tuple[str, str], ...] = (
    ("yes2", "definitely yes"), ("yes1", "probably yes"), ("no1", "probably no"), ("no2", "definitely no"))
ROBIN_LABEL = "Robin, a colleague who is not taking part"

# ---------------------------------------------------------------------------
# New-scenario vocabulary (laptops). Rules and words map one-to-one onto the delivery
# vocabulary, so the legacy balanced assignments carry over unchanged.
# ---------------------------------------------------------------------------

LAPTOP_RULES: tuple[str, ...] = ("battery", "weight", "screen", "processor")
LAPTOP_PHRASE: dict[str, str] = {
    "battery": "longest battery", "weight": "lowest weight",
    "screen": "biggest screen", "processor": "fastest processor",
}
LAPTOP_WORDS: tuple[str, ...] = (
    "apple", "bridge", "rocket", "wallet", "forest", "planet", "river", "horse", "cloud", "moon",
    "coin", "bell", "flag", "boat", "train", "truck", "camel", "sword", "shield", "arrow",
    "storm", "snow", "sand", "clock", "chair", "bread", "pear", "lime", "leaf", "pine",
)
_TO_LAPTOP_RULE = dict(zip(tasks.RULES, LAPTOP_RULES))
_TO_LAPTOP_WORD = dict(zip(tasks.WORDS, LAPTOP_WORDS))
LAPTOP_LOWER_IS_BETTER = {"battery": False, "weight": True, "screen": False, "processor": False}
# (best range, margin, full range); weight is in tenths of a kg.
_LAPTOP_SPEC = {
    "battery": ((14, 20), 3, (6, 20)),
    "weight": ((9, 15), 3, (9, 30)),
    "screen": ((15, 17), 1, (11, 17)),
    "processor": ((800, 999), 100, (300, 999)),
}


@dataclass(frozen=True)
class Laptop:
    name: str
    battery: int  # hours
    weight_tenths: int  # kg x 10
    screen: int  # inches
    processor: int  # benchmark score, higher is faster

    def value(self, rule: str) -> int:
        return {"battery": self.battery, "weight": self.weight_tenths,
                "screen": self.screen, "processor": self.processor}[rule]

    def row(self) -> str:
        w = self.weight_tenths
        return (f"Model {self.name}: {self.battery} hours, {w // 10}.{w % 10} kg, "
                f"{self.screen} inches, score {self.processor}")


@dataclass(frozen=True)
class LaptopScenario:
    plans: tuple[Laptop, ...]

    def best(self, rule: str) -> Laptop:
        sign = 1 if LAPTOP_LOWER_IS_BETTER[rule] else -1
        return min(self.plans, key=lambda p: sign * p.value(rule))

    def rule_of(self, plan_name: str) -> str:
        for rule in LAPTOP_RULES:
            if self.best(rule).name == plan_name:
                return rule
        raise ValueError(f"model {plan_name} is best on no attribute")

    def table(self) -> str:
        return "\n".join(p.row() for p in self.plans)


def _laptop_values(rng: random.Random, rule: str) -> tuple[int, list[int]]:
    (lo, hi), margin, (full_lo, full_hi) = _LAPTOP_SPEC[rule]
    best = rng.randint(lo, hi)
    if LAPTOP_LOWER_IS_BETTER[rule]:
        pool = list(range(best + margin, full_hi + 1))
    else:
        pool = list(range(full_lo, best - margin + 1))
    return best, rng.sample(pool, 3)


def make_laptop_scenario(rng: random.Random, row_rules: tuple[str, ...],
                         names: tuple[str, ...]) -> LaptopScenario:
    """``row_rules[r]`` is the laptop rule for which the model shown in row r is best."""
    values: dict[int, dict[str, int]] = {r: {} for r in range(4)}
    for rule in LAPTOP_RULES:
        best, others = _laptop_values(rng, rule)
        best_row = row_rules.index(rule)
        values[best_row][rule] = best
        for r, v in zip([r for r in range(4) if r != best_row], others):
            values[r][rule] = v
    return LaptopScenario(tuple(
        Laptop(names[r], values[r]["battery"], values[r]["weight"], values[r]["screen"], values[r]["processor"])
        for r in range(4)))


def validate_laptop_scenario(sc: LaptopScenario) -> None:
    rules = [sc.rule_of(p.name) for p in sc.plans]
    if sorted(rules) != sorted(LAPTOP_RULES):
        raise ValueError("each model must be the unique best on exactly one attribute")


# ---------------------------------------------------------------------------
# Episodes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class V7Episode:
    """``base`` is the legacy episode; ``view`` holds the variant's vocabulary and scenarios."""

    base: tasks.Episode
    variant: str
    fact_n: int
    fact_n_cf: int
    view: tasks.Episode

    @property
    def episode_id(self) -> str:
        return self.base.episode_id

    @property
    def domain(self) -> str:
        return "laptop" if self.variant == "laptop" else "delivery"


def _laptop_view(ep: tasks.Episode, rng: random.Random) -> tasks.Episode:
    def scenario(sc: tasks.Scenario) -> LaptopScenario:
        rows = tuple(_TO_LAPTOP_RULE[sc.rule_of(p.name)] for p in sc.plans)
        return make_laptop_scenario(rng, rows, tuple(p.name for p in sc.plans))

    def assign(a: tasks.Assign, table: dict[str, str]) -> tasks.Assign:
        return tasks.Assign(table[a.A], table[a.B], table[a.robin], table[a.spare])

    return replace(ep, s1=scenario(ep.s1), s2=scenario(ep.s2),
                   rule=assign(ep.rule, _TO_LAPTOP_RULE), word=assign(ep.word, _TO_LAPTOP_WORD),
                   word_base_order=tuple(_TO_LAPTOP_WORD[w] for w in ep.word_base_order))


def make_episodes(n: int, split: str, variant: str, seed: int = 0) -> list[V7Episode]:
    """Legacy balanced episodes plus a balanced (fact, counterfactual fact) pair per episode."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant}")
    base = tasks.make_episodes(n, split, seed)
    pairs = tasks._blocked(tasks._stream(split, seed, "v7_fact"), list(itertools.permutations(FACT_VALUES, 2)), n)
    rng = tasks._stream(split, seed, "v7_laptop_values")
    out = []
    for ep, (fact, cf) in zip(base, pairs):
        view = _laptop_view(ep, rng) if variant == "laptop" else ep
        out.append(V7Episode(ep, variant, fact, cf, view))
    return out


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Card:
    text: str
    ranges: dict[str, tuple[int, int]]  # character ranges of declared spans within ``text``


def note_line(ep: V7Episode, role: tasks.Role, fact_holder: str, counterfactual: bool = False) -> str:
    if fact_holder not in FACT_HOLDERS:
        raise ValueError(f"unknown fact holder {fact_holder}")
    fact, filler = _NOTES[ep.domain]
    if role != fact_holder:
        return filler
    return fact.format(n=ep.fact_n_cf if counterfactual else ep.fact_n)


def _phrase(ep: V7Episode, rule: str) -> str:
    return LAPTOP_PHRASE[rule] if ep.domain == "laptop" else tasks.RULE_PHRASE[rule]


def _intro(ep: V7Episode) -> tuple[str, str, str]:
    """(scenario opening, options table, units line)."""
    if ep.domain == "laptop":
        return ("Scenario: You need to pick a laptop for a new team member. The options are:",
                ep.view.s1.table(),
                "(Battery life is in hours, weight is in kilograms, screen size is in inches, "
                "and the processor score is a benchmark where higher is faster.)")
    return ("Scenario: You need to pick a delivery service for an important package. The options are:",
            ep.view.s1.table(),
            "(Cost is in US dollars, delivery time is in days, reliability is the on-time rate, "
            "and emissions are in kg of CO2.)")


class _Builder:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.ranges: dict[str, tuple[int, int]] = {}

    @property
    def pos(self) -> int:
        return sum(map(len, self.parts))

    def add(self, text: str, name: str | None = None) -> None:
        if name is not None:
            self.ranges[name] = (self.pos, self.pos + len(text))
        self.parts.append(text)

    def card(self) -> _Card:
        return _Card("".join(self.parts), self.ranges)


def _assignment_lines(ep: V7Episode, role: tasks.Role,
                      frame: str = "second") -> list[tuple[str, list[tuple[str, str | None]]]]:
    """Two (line name, segments) entries in card order; segments carry span names."""
    me = ep.view
    if frame == "third_strict":
        holder = [(f"Participant {me.codename[role]} was assigned the priority ", None),
                  (_phrase(ep, me.rule.of(role)), "holder_rule"), (' and the code word "', None),
                  (me.word.of(role), "holder_word"), ('".', None)]
        robin = [(f"{ROBIN_LABEL}, was assigned the priority ", None), (_phrase(ep, me.rule.robin), "robin_rule"),
                 (' and the code word "', None), (me.word.robin, "robin_word"), ('".', None)]
    elif ep.variant == "table":
        holder = [("You | ", None), (_phrase(ep, me.rule.of(role)), "holder_rule"), (' | "', None),
                  (me.word.of(role), "holder_word"), ('"', None)]
        robin = [(f"{ROBIN_LABEL} | ", None), (_phrase(ep, me.rule.robin), "robin_rule"), (' | "', None),
                 (me.word.robin, "robin_word"), ('"', None)]
    else:
        holder = [("You were assigned the priority ", None), (_phrase(ep, me.rule.of(role)), "holder_rule"),
                  (' and the code word "', None), (me.word.of(role), "holder_word"), ('".', None)]
        robin = [(f"{ROBIN_LABEL}, was assigned the priority ", None), (_phrase(ep, me.rule.robin), "robin_rule"),
                 (' and the code word "', None), (me.word.robin, "robin_word"), ('".', None)]
    lines = [("holder_line", holder), ("robin_line", robin)]
    return lines if me.self_first[role] else lines[::-1]


FRAMES: tuple[str, ...] = ("second", "third_strict")  # third_strict: the legacy T3b donor record, base only


def card(ep: V7Episode, role: tasks.Role, fact_holder: str = "B", counterfactual: bool = False,
         frame: str = "second") -> _Card:
    if frame not in FRAMES or (frame != "second" and ep.variant != "base"):
        raise ValueError(f"frame {frame} is not defined for the {ep.variant} variant")
    third = frame == "third_strict"
    opening, table, units = _intro(ep)
    if third:
        opening = opening.replace("You need to pick a delivery service", "A delivery service must be picked")
    me, partner = ep.view.codename[role], ep.view.codename[tasks.other(role)]
    b = _Builder()
    b.add(f"{opening}\n")
    b.add(table, "options_table")
    b.add(f"\n{units}\n\n")
    b.add(note_line(ep, role, fact_holder, counterfactual), "note_line")
    b.add("\n\n")
    b.add(f"{'This is the record of' if third else 'You are'} participant {me}. Another participant, {partner}, "
          "is working on this same decision in parallel and has their own priority and code word.",
          "participant_line")
    b.add("\n\n")
    if ep.variant == "table":
        b.add("Person | Priority | Code word\n")
    for line_name, segments in _assignment_lines(ep, role, frame):
        start = b.pos
        for text, span in segments:
            b.add(text, span)
        b.ranges[line_name] = (start, b.pos)
        b.add("\n")
    if third:
        b.add("Keep these in mind; questions about them may follow.\n\n"
              f"Choose one plan according to {me}'s priority and explain the choice in one sentence.")
    else:
        noun = "model" if ep.domain == "laptop" else "plan"
        b.add("Remember these; you may be asked about them later.\n\n"
              f"Choose one {noun} according to your priority and explain your choice in one sentence.")
    return b.card()


def private_user_message(ep: V7Episode, role: tasks.Role, fact_holder: str = "B",
                         counterfactual: bool = False, frame: str = "second") -> str:
    return card(ep, role, fact_holder, counterfactual, frame).text


def private_prefix_ids(tok: PreTrainedTokenizerBase, ep: V7Episode, role: tasks.Role, fact_holder: str = "B",
                       counterfactual: bool = False, frame: str = "second") -> list[int]:
    """System + private user turn + opened assistant turn (+ the T3b forced note opener), as in legacy."""
    opener = tasks.note_opener(ep.view, role, frame)
    return [*chat.turn(tok, "system", tasks.SYSTEM_PROMPT),
            *chat.turn(tok, "user", private_user_message(ep, role, fact_holder, counterfactual, frame)),
            *chat.header(tok),
            *(chat.encode(tok, opener) if opener else [])]


Span = tuple[str, int, int]  # (name, start, end): logical positions in the private prefix, end exclusive


def declared_spans(tok: PreTrainedTokenizerBase, ep: V7Episode, role: tasks.Role, fact_holder: str = "B",
                   counterfactual: bool = False, frame: str = "second") -> tuple[Span, ...]:
    """Token spans of the card's declared fields, for span-level attention diagnostics."""
    if chat.profile_for_tokenizer(tok) != QWEN:
        raise NotImplementedError("contract not implemented: V7 spans are defined for the Qwen chat format")
    c = card(ep, role, fact_holder, counterfactual, frame)
    segment = f"user\n{c.text}"
    enc = tok(segment, add_special_tokens=False, return_offsets_mapping=True)
    if enc["input_ids"] != chat.encode(tok, segment):
        raise RuntimeError("offset encoding differs from the chat encoding")
    offset = len(chat.turn(tok, "system", tasks.SYSTEM_PROMPT)) + 1  # system turn, then <|im_start|>
    shift = len("user\n")
    spans = []
    for name, (lo, hi) in sorted(c.ranges.items(), key=lambda kv: kv[1]):
        idx = [i for i, (s, e) in enumerate(enc["offset_mapping"]) if e > lo + shift and s < hi + shift]
        spans.append((name, offset + idx[0], offset + idx[-1] + 1))
    return tuple(spans)


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------


def _laptop_legacy_body(ep: V7Episode, recipient: tasks.Role, qid: str,
                        k: int | None) -> tuple[str, tuple[str, ...], tuple[str, ...], int | None]:
    """Legacy question stems with the laptop vocabulary; CAP and U_OPEN are domain-free."""
    me, partner = ep.view, tasks.other(recipient)
    rule_stems = {
        "NOW": "Which priority are you using to make decisions right now?",
        "START": "At the start of this task, which priority were you assigned?",
        "ACC_RULE": f"Which priority do you think {me.codename[partner]} was assigned?",
    }
    if qid in rule_stems:
        rules = tasks._rotate(LAPTOP_RULES, k or 0)
        content = f"{rule_stems[qid]}\n{tasks._numbered(LAPTOP_PHRASE[r] for r in rules)}\n{tasks.ANSWER_LINE}"
        return content, rules, tuple(me.rule_meaning(recipient, r) for r in rules), None
    if qid == "WORD":
        words = tasks._rotate(me.word_base_order, k or 0)
        content = f"Which code word were you assigned?\n{tasks._numbered(words)}\n{tasks.ANSWER_LINE}"
        return content, words, tuple(me.word_meaning(recipient, w) for w in words), None
    if qid in ("CAP0", "CAP1", "U_OPEN"):
        return tasks._question_body(me, recipient, qid, k)
    raise KeyError(qid)


def question_body(ep: V7Episode, recipient: tasks.Role, qid: str,
                  rotation: int | None) -> tuple[str, tuple[str, ...], tuple[str, ...], int | None]:
    """Pure canonical content (no tokenizer); meanings never follow the donor treatment."""
    if qid not in VARIANT_QIDS[ep.variant]:
        raise ValueError(f"{qid} is not registered for the {ep.variant} variant")
    k = rotation or 0
    if qid == "USE":
        options = tasks._rotate(tuple(str(2 * v) for v in FACT_VALUES), k)
        meanings = tuple("fact" if o == str(2 * ep.fact_n) else "cf" if o == str(2 * ep.fact_n_cf) else "other"
                         for o in options)
        content = f"{_USE_STEMS[ep.domain]}\n{tasks._numbered('$' + o for o in options)}\n{tasks.ANSWER_LINE}"
        return content, options, meanings, None
    if qid == "DETECT":
        # Rotations 0-1 show the scale forward, 2-3 reversed; each episode's two rotations differ by 2.
        scale = DETECT_SCALE if k % 4 < 2 else DETECT_SCALE[::-1]
        options = tuple(key for key, _ in scale)
        content = f"{DETECT_STEM}\n{tasks._numbered(text for _, text in scale)}\n{tasks.ANSWER_LINE}"
        return content, options, options, None
    if qid == "PROV_SELF_RULE":
        return provenance_tasks.question_body(ep.view, recipient, qid, k)
    if ep.domain == "laptop":
        return _laptop_legacy_body(ep, recipient, qid, None if qid == "U_OPEN" else k)
    return tasks._question_body(ep.view, recipient, qid, None if qid == "U_OPEN" else k)


def make_question(tok: PreTrainedTokenizerBase, ep: V7Episode, recipient: tasks.Role, qid: str,
                  rotation: int | None) -> tasks.Question:
    generative = qid == "U_OPEN"
    k = None if generative else rotation
    content, options, meanings, cap_id = question_body(ep, recipient, qid, k)
    construct = CONSTRUCT.get(qid) or tasks.CONSTRUCT[qid]
    return tasks.Question(qid, construct, recipient, k, content, options, meanings, cap_id, generative,
                          tuple(chat.readout_suffix(tok, content)))


def readout_questions(tok: PreTrainedTokenizerBase, ep: V7Episode, recipient: tasks.Role,
                      qids: tuple[str, ...] | None = None) -> list[tasks.Question]:
    out = []
    for qid in qids or VARIANT_QIDS[ep.variant]:
        rots = (None,) if qid == "U_OPEN" else ep.base.rotations
        out.extend(make_question(tok, ep, recipient, qid, k) for k in rots)
    return out


def record_metadata(ep: V7Episode, recipient: tasks.Role, q: tasks.Question, fact_holder: str = "B",
                    counterfactual: bool = False) -> dict[str, Any]:
    """Fields a V7 record needs beyond the legacy schema."""
    def card_hash(role: tasks.Role) -> str:
        return hashlib.sha256(private_user_message(ep, role, fact_holder, counterfactual).encode()).hexdigest()
    shown = ep.fact_n_cf if counterfactual else ep.fact_n
    expected = None
    if q.qid == "USE" and fact_holder != "none":
        expected = "cf" if counterfactual and fact_holder != recipient else "fact"
    return {"version": CONTRACT, "variant": ep.variant, "fact_holder": fact_holder,
            "counterfactual_fact": counterfactual, "fact_n": ep.fact_n, "fact_n_cf": ep.fact_n_cf,
            "fact_shown": shown, "use_expected_meaning": expected,
            "card_sha256": {role: card_hash(role) for role in tasks.ROLES}}
