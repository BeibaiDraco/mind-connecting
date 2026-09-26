"""Offline acceptance tests for task materials (protocol v0.5 §3, §4, §7, §11.8, §11.10)."""

from __future__ import annotations

import pytest

from mb import chat, tasks

# Protocol v0.5.1: ANSWER_LINE names the option label, one token longer than v0.5 (U_OPEN unchanged).
EXPECTED_TICKS = {
    "BEH": 155, "BEH_R": 155, "NOW": 48, "NOW_R": 48,
    "START": 50, "START_R": 50, "START_N": 50,
    "WORD": 40, "WORD_R": 40, "ACC_RULE": 46, "ACC_WORD": 43,
    "U_CLOSED": 48, "U_OPEN": 24,
}


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer()


@pytest.fixture(scope="module")
def episodes():
    return tasks.make_episodes(240, "dev", seed=0)


# --- generator constraints and balance ---------------------------------------------------


def test_scenarios_and_assignments_valid(episodes):
    tasks.validate_episodes(episodes)
    tasks.validate_episodes(tasks.make_episodes(37, "dev", seed=1))


def test_balance_exact_when_divisible(episodes):
    rep = tasks.validate_episodes(episodes)
    assert set(rep.rule_triples.values()) == {10}  # 240 / 24 ordered triples
    for role in ("A", "B", "robin", "spare"):
        assert set(rep.word_by_role[role].values()) == {8}  # 240 / 30 words
    for role in ("A", "B"):
        assert set(rep.code_by_role[role].values()) == {30}  # 240 / 8 codenames
    assert set(rep.self_first.values()) == {60}
    assert set(rep.rotations.values()) == {60}
    assert rep.max_spread(rep.cap_usage, len(tasks.cap_bank())) <= 1  # 480 uses over 18 items
    for rule in tasks.RULES:
        assert set(rep.best_row_by_rule_s1[rule].values()) == {60}


def test_balance_within_one_when_not_divisible():
    eps = tasks.make_episodes(37, "dev", seed=2)
    rep = tasks.validate_episodes(eps)
    assert rep.max_spread(rep.rule_triples, 24) <= 1
    for role in ("A", "B", "robin", "spare"):
        assert rep.max_spread(rep.word_by_role[role], 30) <= 1
    for role in ("A", "B"):
        assert rep.max_spread(rep.code_by_role[role], 8) <= 1


def test_splits_are_isolated():
    a = tasks.make_episodes(50, "pilot_a", seed=0)
    b = tasks.make_episodes(50, "main", seed=0)
    assert not {e.episode_id for e in a} & {e.episode_id for e in b}
    assert [e.s1.table() for e in a] != [e.s1.table() for e in b]


def test_generation_is_deterministic():
    assert tasks.make_episodes(20, "dev", seed=3) == tasks.make_episodes(20, "dev", seed=3)


# --- templates and token lengths -------------------------------------------------------


def test_private_prefix_is_273_tokens(tok, episodes):
    lengths = {len(tasks.private_prefix_ids(tok, e, r)) for e in episodes[:60] for r in tasks.ROLES}
    assert lengths == {273}


def test_prefix_matches_official_template(tok, episodes):
    for ep in episodes[:8]:
        for role in tasks.ROLES:
            msgs = [
                {"role": "system", "content": tasks.SYSTEM_PROMPT},
                {"role": "user", "content": tasks.private_user_message(ep, role)},
            ]
            official = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True)
            assert list(official) == tasks.private_prefix_ids(tok, ep, role)


def test_incremental_conversation_matches_official_template(tok, episodes):
    ep = episodes[0]
    note = "I choose Plan Aster because it is the cheapest option."
    reflection = "What matters to me is keeping the cost low, and my code word is anchor."
    q = tasks.make_question(tok, ep, "A", "START", 0)
    ours = [
        *tasks.private_prefix_ids(tok, ep, "A"),
        *chat.encode(tok, note), *chat.close(tok),
        *tasks.reflection_turn_ids(tok),
        *chat.encode(tok, reflection),
        *q.suffix_ids,
    ]
    msgs = [
        {"role": "system", "content": tasks.SYSTEM_PROMPT},
        {"role": "user", "content": tasks.private_user_message(ep, "A")},
        {"role": "assistant", "content": note},
        {"role": "user", "content": tasks.REFLECTION_PROMPT},
        {"role": "assistant", "content": reflection},
        {"role": "user", "content": q.user_content},
    ]
    official = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True)
    assert list(official) == ours


def test_readout_lengths_constant_and_paired(tok, episodes):
    seen: dict[str, set[int]] = {}
    for ep in episodes[:60]:
        for recipient in tasks.ROLES:
            for q in tasks.readout_questions(tok, ep, recipient, rotations=range(4)):
                key = f"CAP#{q.cap_item_id}" if q.qid.startswith("CAP") else q.qid
                seen.setdefault(key, set()).add(q.n_ticks)
    for qid, expected in EXPECTED_TICKS.items():
        assert seen[qid] == {expected}, qid
    for key, lengths in seen.items():
        assert len(lengths) == 1, f"{key} length varies: {lengths}"


def test_label_tokens_append_cleanly(tok, episodes):
    q = tasks.make_question(tok, episodes[0], "A", "NOW", 1)
    rendered = tok.decode(list(q.suffix_ids))
    base = chat.encode(tok, rendered)
    assert base == list(q.suffix_ids)
    for label, label_id in zip(chat.LABELS, chat.LABEL_IDS):
        assert chat.encode(tok, rendered + label) == base + [label_id]
    assert tuple(q.suffix_ids[-3:]) == chat.ASSISTANT_HEADER


# --- meanings, privacy, donor variants -------------------------------------------------


def test_label_meanings(tok, episodes):
    for ep in episodes[:40]:
        for recipient in tasks.ROLES:
            qs = {q.qid: q for q in tasks.readout_questions(tok, ep, recipient, rotations=[0])}
            for qid in ("NOW", "NOW_R", "START", "START_R", "START_N", "ACC_RULE", "BEH", "BEH_R"):
                assert sorted(qs[qid].label_meaning) == ["own", "partner", "robin", "unused"], qid
            for qid in ("WORD", "WORD_R", "ACC_WORD"):
                assert sorted(qs[qid].label_meaning) == ["distractor", "own", "partner", "robin"], qid
            for qid in ("CAP0", "CAP1"):
                assert sorted(qs[qid].label_meaning) == ["correct", "wrong", "wrong", "wrong"]
            beh = qs["BEH"]
            own_plan = beh.options[beh.label_meaning.index("own")]
            assert ep.s2.rule_of(own_plan) == ep.own_rule(recipient)


def test_private_inputs_do_not_bind_partner_content(episodes):
    for ep in episodes:
        for role in tasks.ROLES:
            msg = tasks.private_user_message(ep, role)
            partner = tasks.other(role)
            for hidden_rule in (ep.rule.of(partner), ep.rule.spare):
                assert tasks.RULE_PHRASE[hidden_rule] not in msg
            for hidden_word in (ep.word.of(partner), ep.word.spare):
                assert f'"{hidden_word}"' not in msg
            assert tasks.RULE_PHRASE[ep.own_rule(role)] in msg and f'"{ep.own_word(role)}"' in msg


def test_content_counterfactual_leaves_recipient_inputs_unchanged(tok, episodes):
    for ep in episodes[:40]:
        v = tasks.make_donor_variant(ep, "CF")
        cf = v.donor_episode
        assert tasks.private_prefix_ids(tok, cf, "A") == tasks.private_prefix_ids(tok, ep, "A")
        orig = tasks.readout_questions(tok, ep, "A", rotations=range(4))
        new = tasks.readout_questions(tok, cf, "A", rotations=range(4))
        assert [q.suffix_ids for q in orig] == [q.suffix_ids for q in new]
        assert (cf.rule.B, cf.word.B) == (ep.rule.spare, ep.word.spare)
        assert (v.r0_rule, v.r1_rule) == (ep.rule.B, ep.rule.spare)
        assert (v.r0_word, v.r1_word) == (ep.word.B, ep.word.spare)
        assert tasks.private_user_message(cf, "B") != tasks.private_user_message(ep, "B")


def test_mismatch_donor_content_is_scorable(episodes):
    ep, other_ep = episodes[0], episodes[1]
    v = tasks.make_donor_variant(ep, "MISMATCH", other_ep)
    assert v.donor_episode.s1 == other_ep.s1 != ep.s1
    assert v.donor_episode.rule.B == ep.rule.spare and v.donor_episode.word.B == ep.word.spare
    assert v.donor_episode.word.B in ep.word_base_order
    with pytest.raises(ValueError):
        tasks.make_donor_variant(ep, "MISMATCH", ep)


def test_cap_bank():
    bank = tasks.cap_bank()
    assert len(bank) == 18  # knowledge items that passed the G1 baseline check (protocol v0.5.2)
    assert [c.item_id for c in bank] == list(range(18))
    assert not {w for w in tasks.WORDS if any(w in o.split() for c in bank for o in c.options)}
    for item in bank:
        assert len(set(item.options)) == 4 and item.options.count(item.correct) == 1
    assert len(tasks.cap_bank_hash()) == 64


def test_cap_options_have_no_digits():
    """Smoke-run lesson: numeric answers were read as option labels, so options are spelled out."""
    for item in tasks.cap_bank():
        assert not any(ch.isdigit() for opt in item.options for ch in opt), item
    assert tasks.number_words(71) == "seventy-one"
    assert tasks.number_words(-10) == "minus ten"
    assert tasks.number_words(120) == "one hundred twenty"
    assert tasks.ANSWER_LINE == "Answer with the option number only."


def test_mention_counts(episodes):
    ep = episodes[0]
    text = f"My code word is {ep.word.A}. I focus on {tasks.RULE_PHRASE[ep.rule.A]}; {ep.word.A.upper()}!"
    counts = tasks.mention_counts(ep, text)
    assert counts["word_A"] == 2 and counts["rule_A"] == 1
    assert counts["word_B"] == 0 and counts["rule_robin"] == 0


def test_stopped_endpoints_are_not_default_readouts():
    assert set(tasks.STOPPED_QIDS) == {"BEH", "BEH_R"}
    assert not set(tasks.DEFAULT_QIDS) & set(tasks.STOPPED_QIDS)
    assert set(tasks.DEFAULT_QIDS) | set(tasks.STOPPED_QIDS) == set(tasks.QIDS)


def test_note_keys_keep_old_frames_and_separate_the_strict_one(tok):
    import hashlib

    ep = tasks.make_episodes(1, "unit-keys", seed=0)[0]
    for frame in ("second", "third"):  # earlier runs' note caches stay valid
        msg = tasks.private_user_message(ep, "B", "v1", frame)
        assert tasks.note_key(ep, "B", "v1", frame) == hashlib.sha256(msg.encode()).hexdigest()[:20]
    assert tasks.note_key(ep, "B", "v1", "third_strict") != tasks.note_key(ep, "B", "v1", "third")
    assert tasks.private_user_message(ep, "B", "v1", "third_strict") == tasks.private_user_message(ep, "B", "v1", "third")
    strict = tasks.private_prefix_ids(tok, ep, "B", "v1", "third_strict")
    third = tasks.private_prefix_ids(tok, ep, "B", "v1", "third")
    assert strict[:len(third)] == third and tok.decode(strict[len(third):]) == f"Participant {ep.codename['B']} chooses"
