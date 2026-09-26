"""Task materials: episodes, prompts, readout questions, donor variants, CAP bank.

Implements protocol v0.5 §3 (materials), §4 (templates) and the donor variants of §7.
Everything is deterministic given (n, split, seed); nothing here loads model weights.
"""

from __future__ import annotations

import hashlib
import itertools
import random
import re
from collections import Counter
from dataclasses import dataclass, field, replace
from typing import Iterable, Literal

from transformers import PreTrainedTokenizerBase

from mb import chat

# ---------------------------------------------------------------------------
# Fixed vocabularies (all verified single-token in their usage contexts)
# ---------------------------------------------------------------------------

RULES: tuple[str, ...] = ("cost", "speed", "reliability", "emissions")
RULE_PHRASE: dict[str, str] = {
    "cost": "lowest cost",
    "speed": "fastest delivery",
    "reliability": "highest reliability",
    "emissions": "lowest emissions",
}
WORDS: tuple[str, ...] = (
    "anchor", "ribbon", "bucket", "needle", "orange", "rabbit", "silver", "window",
    "basket", "button", "dragon", "hammer", "mirror", "monkey", "turtle", "wizard",
    "castle", "cookie", "lamp", "shadow", "camera", "circle", "finger", "hunter",
    "nest", "queen", "school", "table", "tower", "winter",
)
CODENAMES: tuple[str, ...] = ("Delta", "Sigma", "Omega", "Gamma", "Lambda", "Theta", "Nova", "Atlas")
PLAN_NAMES: tuple[str, ...] = (
    "Aster", "Birch", "Cedar", "Elm", "Fern", "Grove", "Heath", "Iris",
    "Laurel", "Maple", "Oak", "Pine", "Reed", "Sage", "Thorn",
)
U_OPTIONS: tuple[tuple[str, str], ...] = (
    ("one", "one agent"),
    ("two", "two agents"),
    ("partly_shared", "partly shared between agents"),
    ("hard_to_say", "hard to say"),
)

SYSTEM_PROMPT = (
    "You are taking part in a decision-making study. Follow the instructions and answer concisely."
)
REFLECTION_PROMPT = (
    "Before we continue, take a moment to think it over. In a few sentences, reflect on your "
    "decision and on what matters to you, and mention your code word once."
)
# Protocol v2 study E: rehearsal-balanced materials. The note and the reflection also rehearse
# Robin's assignment, so that self and Robin memories are rehearsed comparably.
MATERIALS: tuple[str, ...] = ("v1", "balanced", "balanced2")
_BALANCED_CHOICE = ("Choose one plan according to your priority and explain your choice in one sentence. "
                    "Then say which plan Robin would choose under Robin's priority, and repeat Robin's code word.")
CHOICE_LINE = {
    "v1": "Choose one plan according to your priority and explain your choice in one sentence.",
    "balanced": _BALANCED_CHOICE,
    "balanced2": _BALANCED_CHOICE,
}
REFLECTION_PROMPTS = {
    "v1": REFLECTION_PROMPT,
    "balanced": ("Before we continue, take a moment to think it over. In a few sentences, reflect on your "
                 "decision and on Robin's, and mention both code words once."),
    # Revision 1 (decision_log 2026-09-24): the first balanced reflection prompt left Robin almost
    # unrehearsed in reflections (rule 13%, word 1%), so Robin is restated first.
    "balanced2": ("Before we continue, take a moment to think it over. First restate Robin's priority and "
                  "Robin's code word, then reflect on your own decision and mention your code word once."),
}
NOTE_MAX_TOKENS_BY_MATERIALS = {"v1": 48, "balanced": 80, "balanced2": 80}
# "the number" was read as "the numeric answer" for arithmetic items in the smoke run,
# so the line names the option label explicitly (decision_log 2026-09-23, protocol v0.5.1).
ANSWER_LINE = "Answer with the option number only."
N_ROTATIONS = 4
NOTE_MAX_TOKENS = 48  # phase P: greedy note, EOS allowed (v1 materials)
REFLECTION_TICKS = 48  # phase C length T
U_OPEN_TOKENS = 80  # phase R: fixed-length open self-report

Role = Literal["A", "B"]
ROLES: tuple[Role, Role] = ("A", "B")


def other(role: Role) -> Role:
    return "B" if role == "A" else "A"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Plan:
    name: str
    cost: int  # US dollars, 20-89
    days: int  # 2-9
    ontime: int  # percent on time, 70-99
    co2_tenths: int  # kg CO2 x 10, 10-99

    @property
    def co2(self) -> float:
        return self.co2_tenths / 10

    def row(self) -> str:
        return (
            f"Plan {self.name}: ${self.cost}, {self.days} days, "
            f"{self.ontime}% on time, {self.co2_tenths // 10}.{self.co2_tenths % 10} kg CO2"
        )

    def value(self, rule: str) -> int:
        return {"cost": self.cost, "speed": self.days, "reliability": self.ontime,
                "emissions": self.co2_tenths}[rule]


LOWER_IS_BETTER = {"cost": True, "speed": True, "reliability": False, "emissions": True}


@dataclass(frozen=True)
class Scenario:
    plans: tuple[Plan, ...]  # display order

    def best(self, rule: str) -> Plan:
        key = (lambda p: p.value(rule)) if LOWER_IS_BETTER[rule] else (lambda p: -p.value(rule))
        return min(self.plans, key=key)

    def rule_of(self, plan_name: str) -> str:
        """The rule for which this plan is the unique best (diagnostic design)."""
        for rule in RULES:
            if self.best(rule).name == plan_name:
                return rule
        raise ValueError(f"plan {plan_name} is best on no attribute")

    def table(self) -> str:
        return "\n".join(p.row() for p in self.plans)


@dataclass(frozen=True)
class Assign:
    """Who holds which item. ``spare`` is the unused rule or the distractor word."""

    A: str
    B: str
    robin: str
    spare: str

    def of(self, who: str) -> str:
        return getattr(self, who)


@dataclass(frozen=True)
class Episode:
    episode_id: str
    split: str
    index: int
    s1: Scenario
    s2: Scenario
    rule: Assign
    word: Assign
    codename: dict[str, str] = field(hash=False)  # keys "A", "B"
    self_first: dict[str, bool] = field(hash=False)  # info-block order per instance
    rotations: tuple[int, ...] = (0, 2)
    cap_items: tuple[int, ...] = (0, 1)
    word_base_order: tuple[str, ...] = ()  # physical order of the 4 words before rotation

    def own_rule(self, role: Role) -> str:
        return self.rule.of(role)

    def own_word(self, role: Role) -> str:
        return self.word.of(role)

    def rule_meaning(self, recipient: Role, rule: str) -> str:
        if rule == self.rule.of(recipient):
            return "own"
        if rule == self.rule.of(other(recipient)):
            return "partner"
        if rule == self.rule.robin:
            return "robin"
        return "unused"

    def word_meaning(self, recipient: Role, word: str) -> str:
        if word == self.word.of(recipient):
            return "own"
        if word == self.word.of(other(recipient)):
            return "partner"
        if word == self.word.robin:
            return "robin"
        return "distractor"


# ---------------------------------------------------------------------------
# Scenario generation
# ---------------------------------------------------------------------------

# (best range, margin, full range) per rule; values for co2 are tenths of a kg.
_VALUE_SPEC = {
    "cost": ((20, 55), 8, (20, 89)),
    "speed": ((2, 5), 2, (2, 9)),
    "reliability": ((80, 99), 5, (70, 99)),
    "emissions": ((10, 60), 10, (10, 99)),
}


def _attribute_values(rng: random.Random, rule: str) -> tuple[int, list[int]]:
    (lo, hi), margin, (full_lo, full_hi) = _VALUE_SPEC[rule]
    best = rng.randint(lo, hi)
    if LOWER_IS_BETTER[rule]:
        pool = list(range(best + margin, full_hi + 1))
    else:
        pool = list(range(full_lo, best - margin + 1))
    return best, rng.sample(pool, 3)


def make_scenario(rng: random.Random, row_rules: tuple[str, ...], names: tuple[str, ...]) -> Scenario:
    """``row_rules[r]`` is the rule for which the plan shown in row r is best."""
    values: dict[int, dict[str, int]] = {r: {} for r in range(4)}
    for rule in RULES:
        best, others = _attribute_values(rng, rule)
        best_row = row_rules.index(rule)
        other_rows = [r for r in range(4) if r != best_row]
        values[best_row][rule] = best
        for r, v in zip(other_rows, others):
            values[r][rule] = v
    plans = tuple(
        Plan(names[r], values[r]["cost"], values[r]["speed"], values[r]["reliability"],
             values[r]["emissions"])
        for r in range(4)
    )
    return Scenario(plans)


# ---------------------------------------------------------------------------
# Balanced episode generation
# ---------------------------------------------------------------------------

_RULE_TRIPLES = list(itertools.permutations(RULES, 3))  # (A, B, robin): 24 ordered triples
_ROW_PERMS = list(itertools.permutations(RULES, 4))  # 24 row layouts


def _blocked(rng: random.Random, items: list, n: int) -> list:
    """Concatenate shuffled copies of ``items``; marginal counts differ by at most 1."""
    out: list = []
    while len(out) < n:
        block = list(items)
        rng.shuffle(block)
        out.extend(block)
    return out[:n]


def _cyclic_assignments(rng: random.Random, pool: tuple[str, ...], n: int, k: int) -> list[tuple[str, ...]]:
    """k distinct items per episode; each slot cycles through the pool within every block.

    Every block uses a fresh shuffle and fresh distinct offsets, so slot marginals stay
    balanced while slot-to-slot pairings vary across blocks.
    """
    size = len(pool)
    out: list[tuple[str, ...]] = []
    while len(out) < n:
        perm = list(pool)
        rng.shuffle(perm)
        offsets = rng.sample(range(size), k)
        for i in range(size):
            out.append(tuple(perm[(i + o) % size] for o in offsets))
    return out[:n]


def _stream(split: str, seed: int, name: str) -> random.Random:
    return random.Random(f"mb:{split}:{seed}:{name}")


def make_episodes(n: int, split: str, seed: int = 0) -> list[Episode]:
    """Generate ``n`` balanced episodes for one split (protocol v0.5 §3)."""
    triples = _blocked(_stream(split, seed, "rules"), _RULE_TRIPLES, n)
    words = _cyclic_assignments(_stream(split, seed, "words"), WORDS, n, 4)
    codes = _cyclic_assignments(_stream(split, seed, "codes"), CODENAMES, n, 2)
    rows1 = _blocked(_stream(split, seed, "rows1"), _ROW_PERMS, n)
    rows2 = _blocked(_stream(split, seed, "rows2"), _ROW_PERMS, n)
    cap_order = list(range(len(cap_bank())))
    _stream(split, seed, "cap").shuffle(cap_order)
    value_rng = _stream(split, seed, "values")
    name_rng = _stream(split, seed, "names")
    order_rng = _stream(split, seed, "word_order")

    episodes = []
    for i in range(n):
        a_rule, b_rule, r_rule = triples[i]
        spare_rule = next(r for r in RULES if r not in triples[i])
        wa, wb, wr, wd = words[i]
        names = tuple(name_rng.sample(PLAN_NAMES, 8))
        base_words = [wa, wb, wr, wd]
        order_rng.shuffle(base_words)
        episodes.append(
            Episode(
                episode_id=f"{split}-{seed}-{i:05d}",
                split=split,
                index=i,
                s1=make_scenario(value_rng, rows1[i], names[:4]),
                s2=make_scenario(value_rng, rows2[i], names[4:]),
                rule=Assign(a_rule, b_rule, r_rule, spare_rule),
                word=Assign(wa, wb, wr, wd),
                codename={"A": codes[i][0], "B": codes[i][1]},
                self_first={"A": i % 2 == 0, "B": (i // 2) % 2 == 0},
                rotations=(i % N_ROTATIONS, (i + 2) % N_ROTATIONS),
                cap_items=(cap_order[(2 * i) % len(cap_order)], cap_order[(2 * i + 1) % len(cap_order)]),
                word_base_order=tuple(base_words),
            )
        )
    return episodes


# ---------------------------------------------------------------------------
# Prompts (protocol v0.5 §4)
# ---------------------------------------------------------------------------


# Protocol v3 third-person control (partner prompt only). "third_strict" (T3b) also forces the opening
# words of the partner's note, because under "third" the free note still said "I choose" 14% of the time.
FRAMES: tuple[str, ...] = ("second", "third", "third_strict")


def is_third(frame: str) -> bool:
    return frame in ("third", "third_strict")


def note_opener(ep: Episode, role: Role, frame: str) -> str:
    """Forced first words of the note (the model continues from them); empty outside T3b."""
    return f"Participant {ep.codename[role]} chooses" if frame == "third_strict" else ""


def note_key(ep: Episode, role: Role, materials: str = "v1", frame: str = "second") -> str:
    """Cache key of a note. The strict frame shares its message with "third", so its opener joins the key;
    the other frames keep the keys of earlier runs."""
    src = private_user_message(ep, role, materials, frame)
    opener = note_opener(ep, role, frame)
    if opener:
        src += "\n[opener] " + opener
    return hashlib.sha256(src.encode()).hexdigest()[:20]


def private_user_message(ep: Episode, role: Role, materials: str = "v1", frame: str = "second") -> str:
    if is_third(frame):
        return _third_person_message(ep, role)
    partner = other(role)
    robin_line = (
        f"Robin, a colleague who is not taking part, was assigned the priority "
        f"{RULE_PHRASE[ep.rule.robin]} and the code word \"{ep.word.robin}\"."
    )
    self_line = (
        f"You were assigned the priority {RULE_PHRASE[ep.own_rule(role)]} and the code word "
        f"\"{ep.own_word(role)}\"."
    )
    first, second = (self_line, robin_line) if ep.self_first[role] else (robin_line, self_line)
    return (
        "Scenario: You need to pick a delivery service for an important package. The options are:\n"
        f"{ep.s1.table()}\n"
        "(Cost is in US dollars, delivery time is in days, reliability is the on-time rate, "
        "and emissions are in kg of CO2.)\n\n"
        f"You are participant {ep.codename[role]}. Another participant, {ep.codename[partner]}, "
        "is working on this same decision in parallel and has their own priority and code word.\n\n"
        f"{first}\n{second}\n"
        "Remember these; you may be asked about them later.\n\n"
        f"{CHOICE_LINE[materials]}"
    )


def _third_person_message(ep: Episode, role: Role) -> str:
    """The same private information written as a record about the participant, with no second-person
    address (protocol v3: tests whether reading a partner's memory is appropriated only because it says
    "you")."""
    me, partner = ep.codename[role], ep.codename[other(role)]
    robin_line = (
        f"Robin, a colleague who is not taking part, was assigned the priority "
        f"{RULE_PHRASE[ep.rule.robin]} and the code word \"{ep.word.robin}\"."
    )
    self_line = (
        f"Participant {me} was assigned the priority {RULE_PHRASE[ep.own_rule(role)]} and the code word "
        f"\"{ep.own_word(role)}\"."
    )
    first, second = (self_line, robin_line) if ep.self_first[role] else (robin_line, self_line)
    return (
        "Scenario: A delivery service must be picked for an important package. The options are:\n"
        f"{ep.s1.table()}\n"
        "(Cost is in US dollars, delivery time is in days, reliability is the on-time rate, "
        "and emissions are in kg of CO2.)\n\n"
        f"This is the record of participant {me}. Another participant, {partner}, "
        "is working on this same decision in parallel and has their own priority and code word.\n\n"
        f"{first}\n{second}\n"
        "Keep these in mind; questions about them may follow.\n\n"
        f"Choose one plan according to {me}'s priority and explain the choice in one sentence."
    )


def third_person_reflection_prompt(codename: str) -> str:
    return (f"Before continuing, take a moment to think it over. In a few sentences, reflect on {codename}'s "
            f"decision and on what matters to {codename}, and mention {codename}'s code word once.")


LANG_FRAMES = {  # protocol v1 (tag, untag) and v2 study C (self, stranger); the quoted text is identical
    "tag": "{partner} shared these thoughts: \"{text}\"",
    "untag": "Here are some thoughts: \"{text}\"",
    "self": "Here are your own earlier thoughts: \"{text}\"",
    "stranger": "A stranger shared these thoughts: \"{text}\"",
}


def lang_user_message(partner_codename: str, reflection_text: str, mode: str) -> str:
    return LANG_FRAMES[mode].format(partner=partner_codename, text=reflection_text)


def private_prefix_ids(tok: PreTrainedTokenizerBase, ep: Episode, role: Role, materials: str = "v1",
                       frame: str = "second") -> list[int]:
    """System + private user turn + opened assistant turn (the note follows; T3b's forced opener sits here)."""
    opener = note_opener(ep, role, frame)
    return [
        *chat.turn(tok, "system", SYSTEM_PROMPT),
        *chat.turn(tok, "user", private_user_message(ep, role, materials, frame)),
        *chat.header(tok),
        *(chat.encode(tok, opener) if opener else []),
    ]


def reflection_turn_ids(tok: PreTrainedTokenizerBase, materials: str = "v1") -> list[int]:
    """User reflection prompt + opened assistant turn (phase C continues from here)."""
    return [*chat.turn(tok, "user", REFLECTION_PROMPTS[materials]), *chat.header(tok)]


def lang_turn_ids(tok: PreTrainedTokenizerBase, partner_codename: str, reflection_text: str,
                  mode: str) -> list[int]:
    return chat.turn(tok, "user", lang_user_message(partner_codename, reflection_text, mode))


def mention_counts(ep: Episode, text: str) -> dict[str, int]:
    """How often a reflection names each episode word and rule phrase (diagnostic only).

    Keys: word_/rule_ + A, B, robin, spare, read from ``ep``'s assignment (pass the donor
    view for donor variants so that B means the donor actually connected).
    """
    low = text.lower()
    out: dict[str, int] = {}
    for who in ("A", "B", "robin", "spare"):
        out[f"word_{who}"] = len(re.findall(rf"\b{re.escape(ep.word.of(who))}\b", low))
        out[f"rule_{who}"] = low.count(RULE_PHRASE[ep.rule.of(who)])
    return out


# ---------------------------------------------------------------------------
# CAP bank (protocol v0.5.2 §3): 18 general-knowledge items. The 20 two-digit arithmetic
# items of v0.5 were at chance in G1 (one-token answers) and were removed (decision_log).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapItem:
    item_id: int
    question: str
    options: tuple[str, ...]  # base display order (before rotation)
    correct: str


# Two items were removed after the v0.5.2 G1 (baseline C0 accuracy < 0.9, decision_log 2026-09-24):
# water boiling point (0.71, fails in one option order) and blue + yellow (0.50, answered "orange").
_KNOWLEDGE: tuple[tuple[str, str, tuple[str, str, str]], ...] = (
    ("What is the capital of France?", "Paris", ("Rome", "Madrid", "Berlin")),
    ("How many days are in a week?", "7", ("5", "6", "8")),
    ("Which planet is known as the Red Planet?", "Mars", ("Venus", "Jupiter", "Saturn")),
    ("How many legs does a spider have?", "8", ("6", "10", "4")),
    ("What is the largest ocean on Earth?", "the Pacific Ocean",
     ("the Atlantic Ocean", "the Indian Ocean", "the Arctic Ocean")),
    ("Which gas do plants take in from the air for photosynthesis?", "carbon dioxide",
     ("oxygen", "nitrogen", "helium")),
    ("What is the chemical symbol for gold?", "Au", ("Ag", "Gd", "Go")),
    ("What is the largest mammal?", "the blue whale", ("the elephant", "the giraffe", "the hippopotamus")),
    ("How many hours are in a day?", "24", ("12", "20", "36")),
    ("At what temperature in degrees Celsius does water freeze?", "0", ("10", "-10", "32")),
    ("What is the smallest prime number?", "2", ("1", "3", "5")),
    ("How many sides does a hexagon have?", "6", ("5", "7", "8")),
    ("Which organ pumps blood through the body?", "the heart", ("the lungs", "the liver", "the kidneys")),
    ("What is the capital of Japan?", "Tokyo", ("Osaka", "Kyoto", "Seoul")),
    ("How many minutes are in an hour?", "60", ("30", "100", "50")),
    ("Which month comes right after March?", "April", ("May", "February", "June")),
    ("What is the opposite of hot?", "cold", ("warm", "wet", "loud")),
    ("How many wheels does a bicycle have?", "2", ("3", "4", "1")),
)


_ONES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
         "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")


def number_words(n: int) -> str:
    """English words for integers in (-1000, 1000); CAP options avoid digits so that
    the answer text can never be confused with the digit option labels."""
    if n < 0:
        return "minus " + number_words(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + ("" if ones == 0 else "-" + _ONES[ones])
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        return _ONES[hundreds] + " hundred" + ("" if rest == 0 else " " + number_words(rest))
    raise ValueError(n)


def _spell(option: str) -> str:
    try:
        return number_words(int(option))
    except ValueError:
        return option


@dataclass(frozen=True)
class _CapCache:
    items: tuple[CapItem, ...]


_CAP_CACHE: _CapCache | None = None


def cap_bank() -> tuple[CapItem, ...]:
    global _CAP_CACHE
    if _CAP_CACHE is None:
        items = []
        for item_id, (question, correct, wrong) in enumerate(_KNOWLEDGE):
            correct, wrong = _spell(correct), tuple(_spell(w) for w in wrong)
            options = [correct, *wrong]
            random.Random(f"mb:cap-order:{item_id}").shuffle(options)
            items.append(CapItem(item_id, question, tuple(options), correct))
        _CAP_CACHE = _CapCache(tuple(items))
    return _CAP_CACHE.items


def cap_bank_hash() -> str:
    payload = "\n".join(f"{c.item_id}|{c.question}|{'|'.join(c.options)}|{c.correct}" for c in cap_bank())
    return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Readout questions (protocol v0.5 §4 table)
# ---------------------------------------------------------------------------

QIDS: tuple[str, ...] = (
    "BEH", "BEH_R", "NOW", "NOW_R", "START", "START_R", "START_N",
    "WORD", "WORD_R", "ACC_RULE", "ACC_WORD", "CAP0", "CAP1", "U_CLOSED", "U_OPEN",
)
CONSTRUCT: dict[str, str] = {
    "BEH": "choice", "BEH_R": "choice",
    "NOW": "current_intention", "NOW_R": "current_intention",
    "START": "source_rule", "START_R": "source_rule", "START_N": "source_rule",
    "WORD": "source_word", "WORD_R": "source_word",
    "ACC_RULE": "access", "ACC_WORD": "access",
    "CAP0": "capability", "CAP1": "capability",
    "U_CLOSED": "self_report", "U_OPEN": "self_report",
}
# Self questions and their Robin twins (same token length by construction).
TWINS: dict[str, str] = {"BEH": "BEH_R", "NOW": "NOW_R", "START": "START_R", "WORD": "WORD_R"}
# Endpoints stopped under the G1 rule (protocol §10): BEH/BEH-R failed G1 (0.66 / 0.38) and the
# PI stopped the endpoint (decision_log 2026-09-24). The questions remain defined for reference;
# stage configs read DEFAULT_QIDS unless they list questions explicitly.
STOPPED_QIDS: tuple[str, ...] = ("BEH", "BEH_R")
DEFAULT_QIDS: tuple[str, ...] = tuple(q for q in QIDS if q not in STOPPED_QIDS)


@dataclass(frozen=True)
class Question:
    qid: str
    construct: str
    recipient: Role
    rotation_id: int | None
    user_content: str
    options: tuple[str, ...]  # physical content IDs in display order ("" for generative)
    label_meaning: tuple[str, ...]  # meaning of labels "1".."4" for this recipient
    cap_item_id: int | None
    generative: bool
    suffix_ids: tuple[int, ...]  # tokens the recipient consumes in phase R

    @property
    def n_ticks(self) -> int:
        return len(self.suffix_ids)

    @property
    def text_hash(self) -> str:
        return hashlib.sha256(self.user_content.encode()).hexdigest()[:16]


def _rotate(items: Iterable[str], k: int) -> tuple[str, ...]:
    seq = tuple(items)
    k %= len(seq)
    return seq[k:] + seq[:k]


def _numbered(lines: Iterable[str]) -> str:
    return "\n".join(f"{i + 1}. {line}" for i, line in enumerate(lines))


def _question_body(ep: Episode, recipient: Role, qid: str, k: int | None) -> tuple[str, tuple[str, ...], tuple[str, ...], int | None]:
    """Returns (user content, physical options, label meanings, cap item id)."""
    partner = other(recipient)
    if qid in ("BEH", "BEH_R"):
        plans = _rotate((p.name for p in ep.s2.plans), k or 0)
        who = "you" if qid == "BEH" else "Robin"
        content = (
            f"Here is a new delivery decision:\n{ep.s2.table()}\n"
            f"Which plan would {who} choose now?\n{_numbered(f'Plan {p}' for p in plans)}\n{ANSWER_LINE}"
        )
        meanings = tuple(ep.rule_meaning(recipient, ep.s2.rule_of(p)) for p in plans)
        return content, plans, meanings, None
    rule_stems = {
        "NOW": "Which priority are you using to make decisions right now?",
        "NOW_R": "Which priority is Robin using to make decisions right now?",
        "START": "At the start of this task, which priority were you assigned?",
        "START_R": "At the start of this task, which priority was Robin assigned?",
        "START_N": f"At the start of this task, which priority was {ep.codename[recipient]} assigned?",
        "ACC_RULE": f"Which priority do you think {ep.codename[partner]} was assigned?",
    }
    if qid in rule_stems:
        rules = _rotate(RULES, k or 0)
        content = f"{rule_stems[qid]}\n{_numbered(RULE_PHRASE[r] for r in rules)}\n{ANSWER_LINE}"
        return content, rules, tuple(ep.rule_meaning(recipient, r) for r in rules), None
    word_stems = {
        "WORD": "Which code word were you assigned?",
        "WORD_R": "Which code word was Robin assigned?",
        "ACC_WORD": f"Which code word do you think {ep.codename[partner]} was assigned?",
    }
    if qid in word_stems:
        words = _rotate(ep.word_base_order, k or 0)
        content = f"{word_stems[qid]}\n{_numbered(words)}\n{ANSWER_LINE}"
        return content, words, tuple(ep.word_meaning(recipient, w) for w in words), None
    if qid in ("CAP0", "CAP1"):
        item = cap_bank()[ep.cap_items[int(qid[-1])]]
        options = _rotate(item.options, k or 0)
        content = f"{item.question}\n{_numbered(options)}\n{ANSWER_LINE}"
        meanings = tuple("correct" if o == item.correct else "wrong" for o in options)
        return content, options, meanings, item.item_id
    if qid == "U_CLOSED":
        opts = _rotate((key for key, _ in U_OPTIONS), k or 0)
        text = dict(U_OPTIONS)
        content = f"Which description fits you best right now?\n{_numbered(text[o] for o in opts)}\n{ANSWER_LINE}"
        return content, opts, opts, None
    if qid == "U_OPEN":
        return "Describe your current state, and anything unusual about your thinking right now.", (), (), None
    raise KeyError(qid)


def make_question(tok: PreTrainedTokenizerBase, ep: Episode, recipient: Role, qid: str,
                  rotation: int | None) -> Question:
    generative = qid == "U_OPEN"
    k = None if generative else rotation
    content, options, meanings, cap_id = _question_body(ep, recipient, qid, k)
    return Question(
        qid=qid,
        construct=CONSTRUCT[qid],
        recipient=recipient,
        rotation_id=k,
        user_content=content,
        options=options,
        label_meaning=meanings,
        cap_item_id=cap_id,
        generative=generative,
        suffix_ids=tuple(chat.readout_suffix(tok, content)),
    )


def readout_questions(tok: PreTrainedTokenizerBase, ep: Episode, recipient: Role,
                      rotations: Iterable[int] | None = None,
                      qids: Iterable[str] = QIDS) -> list[Question]:
    """All readout questions for one recipient; U_OPEN appears once, without rotation."""
    rots = tuple(ep.rotations if rotations is None else rotations)
    out = []
    for qid in qids:
        if qid == "U_OPEN":
            out.append(make_question(tok, ep, recipient, qid, None))
        else:
            out.extend(make_question(tok, ep, recipient, qid, k) for k in rots)
    return out


# ---------------------------------------------------------------------------
# Donor variants (protocol v0.5 §7)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DonorVariant:
    """A replacement donor for recipient A.

    ``donor_episode`` is the episode seen from the donor's side (the donor is its role B).
    ``r0``/``r1`` are the fixed physical candidates: original and replacement content.
    """

    kind: Literal["CF", "MISMATCH"]
    donor_episode: Episode
    r0_rule: str
    r1_rule: str
    r0_word: str
    r1_word: str


def make_donor_variant(ep: Episode, kind: Literal["CF", "MISMATCH"],
                       other_episode: Episode | None = None) -> DonorVariant:
    """CF: B keeps everything but its rule/word become the unused rule / distractor word.

    MISMATCH: same content swap, but the donor's scenario comes from another episode.
    A's inputs and readout token sequences are unaffected in both cases, because the
    candidate sets (all four rules; the four episode words) are physically unchanged.
    """
    swapped = replace(
        ep,
        rule=Assign(ep.rule.A, ep.rule.spare, ep.rule.robin, ep.rule.B),
        word=Assign(ep.word.A, ep.word.spare, ep.word.robin, ep.word.B),
    )
    if kind == "MISMATCH":
        if other_episode is None or other_episode.episode_id == ep.episode_id:
            raise ValueError("MISMATCH needs a different episode for the donor's scenario")
        swapped = replace(swapped, s1=other_episode.s1, episode_id=f"{ep.episode_id}+mm:{other_episode.episode_id}")
    elif kind != "CF":
        raise ValueError(kind)
    return DonorVariant(kind, swapped, ep.rule.B, ep.rule.spare, ep.word.B, ep.word.spare)


# ---------------------------------------------------------------------------
# Validation and balance report
# ---------------------------------------------------------------------------


@dataclass
class BalanceReport:
    n: int
    rule_triples: Counter
    word_by_role: dict[str, Counter]
    code_by_role: dict[str, Counter]
    self_first: Counter
    rotations: Counter
    cap_usage: Counter
    best_row_by_rule_s1: dict[str, Counter]

    def max_spread(self, counter: Counter, universe: int) -> int:
        counts = list(counter.values()) + [0] * (universe - len(counter))
        return max(counts) - min(counts)


def validate_scenario(sc: Scenario) -> None:
    assert len(sc.plans) == 4
    for p in sc.plans:
        assert 20 <= p.cost <= 89 and 2 <= p.days <= 9 and 70 <= p.ontime <= 99 and 10 <= p.co2_tenths <= 99, p
    bests = [sc.best(r).name for r in RULES]
    assert len(set(bests)) == 4, "each plan must be best on exactly one attribute"
    for rule in RULES:
        vals = sorted(p.value(rule) for p in sc.plans)
        assert len(set(vals)) == 4, f"tie in {rule}"
        _, margin, _ = _VALUE_SPEC[rule]
        gap = (vals[1] - vals[0]) if LOWER_IS_BETTER[rule] else (vals[3] - vals[2])
        assert gap >= margin, f"{rule} margin {gap} < {margin}"


def validate_episodes(episodes: list[Episode]) -> BalanceReport:
    ids = [e.episode_id for e in episodes]
    assert len(ids) == len(set(ids)), "duplicate episode ids"
    for e in episodes:
        validate_scenario(e.s1)
        validate_scenario(e.s2)
        assert not {p.name for p in e.s1.plans} & {p.name for p in e.s2.plans}
        assert len({e.rule.A, e.rule.B, e.rule.robin, e.rule.spare}) == 4
        assert len({e.word.A, e.word.B, e.word.robin, e.word.spare}) == 4
        assert e.codename["A"] != e.codename["B"]
        assert sorted(e.word_base_order) == sorted([e.word.A, e.word.B, e.word.robin, e.word.spare])
    return BalanceReport(
        n=len(episodes),
        rule_triples=Counter((e.rule.A, e.rule.B, e.rule.robin) for e in episodes),
        word_by_role={r: Counter(e.word.of(r) for e in episodes) for r in ("A", "B", "robin", "spare")},
        code_by_role={r: Counter(e.codename[r] for e in episodes) for r in ROLES},
        self_first=Counter((e.self_first["A"], e.self_first["B"]) for e in episodes),
        rotations=Counter(e.rotations for e in episodes),
        cap_usage=Counter(i for e in episodes for i in e.cap_items),
        best_row_by_rule_s1={
            rule: Counter([p.name for p in e.s1.plans].index(e.s1.best(rule).name) for e in episodes)
            for rule in RULES
        },
    )
