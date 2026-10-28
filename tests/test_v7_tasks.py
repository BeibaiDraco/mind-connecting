"""Offline acceptance tests for the V7 placement-study materials (contract v7-placement-v1)."""

from __future__ import annotations

from collections import Counter

import pytest

from mb import chat, tasks
from mb import v7_tasks as v7

DIFF_SPANS = ("participant_line", "holder_line", "robin_line", "note_line")


@pytest.fixture(scope="module")
def tok():
    return chat.load_tokenizer()


@pytest.fixture(scope="module", params=v7.VARIANTS)
def variant_episodes(request):
    return v7.make_episodes(48, "v7_test", request.param)


def _strip_note(text: str) -> str:
    start = text.index("\n\nNote: ") + 2
    end = text.index("\n\n", start) + 2
    return text[:start] + text[end:]


def test_base_card_is_legacy_card_plus_note():
    for ep in v7.make_episodes(48, "v7_test", "base"):
        for role in tasks.ROLES:
            for holder in v7.FACT_HOLDERS:
                text = v7.private_user_message(ep, role, holder)
                assert _strip_note(text) == tasks.private_user_message(ep.base, role, "v1", "second")


@pytest.mark.parametrize("holder", v7.FACT_HOLDERS)
@pytest.mark.parametrize("counterfactual", (False, True))
def test_cards_align_and_differ_only_inside_declared_spans(tok, variant_episodes, holder, counterfactual):
    for ep in variant_episodes:
        a = v7.private_prefix_ids(tok, ep, "A", holder, counterfactual)
        b = v7.private_prefix_ids(tok, ep, "B", holder, counterfactual)
        assert len(a) == len(b)
        allowed = set()
        for role in tasks.ROLES:
            for name, s, e in v7.declared_spans(tok, ep, role, holder, counterfactual):
                if name in DIFF_SPANS:
                    allowed.update(range(s, e))
        assert {i for i, (x, y) in enumerate(zip(a, b)) if x != y} <= allowed


def test_spans_decode_to_declared_fields(tok, variant_episodes):
    for ep in variant_episodes[:12]:
        for role in tasks.ROLES:
            ids = v7.private_prefix_ids(tok, ep, role)
            text = {name: tok.decode(ids[s:e]).strip() for name, s, e in v7.declared_spans(tok, ep, role)}
            assert text["holder_rule"] == v7._phrase(ep, ep.view.rule.of(role))
            assert text["robin_rule"] == v7._phrase(ep, ep.view.rule.robin)
            assert text["holder_word"] == ep.view.word.of(role)
            assert text["robin_word"] == ep.view.word.robin
            assert text["note_line"].startswith("Note:")
            assert (f"${ep.fact_n} " in text["note_line"]) == (role == "B")


def test_span_order_follows_card_line_order(tok):
    for ep in v7.make_episodes(8, "v7_test", "base"):
        for role in tasks.ROLES:
            spans = {name: s for name, s, _ in v7.declared_spans(tok, ep, role)}
            assert (spans["holder_line"] < spans["robin_line"]) == ep.base.self_first[role]


def test_fact_pairs_balanced_and_distinct():
    eps = v7.make_episodes(120, "v7_test", "base")
    pairs = Counter((ep.fact_n, ep.fact_n_cf) for ep in eps)
    assert len(pairs) == 12 and set(pairs.values()) == {10}
    assert all(ep.fact_n != ep.fact_n_cf for ep in eps)


def test_base_and_table_views_are_the_legacy_episodes():
    legacy = tasks.make_episodes(24, "v7_test", 0)
    for variant in ("base", "table"):
        assert [ep.base for ep in v7.make_episodes(24, "v7_test", variant)] == legacy
        assert all(ep.view is ep.base for ep in v7.make_episodes(4, "v7_test", variant))


def test_variants_share_assignments_and_facts():
    base, laptop = (v7.make_episodes(48, "v7_test", v) for v in ("base", "laptop"))
    for b, l in zip(base, laptop):
        assert (b.fact_n, b.fact_n_cf) == (l.fact_n, l.fact_n_cf)
        assert l.view.rule.A == v7._TO_LAPTOP_RULE[b.view.rule.A]
        assert l.view.word.B == v7._TO_LAPTOP_WORD[b.view.word.B]
        assert l.view.self_first == b.view.self_first


def test_laptop_scenarios_valid_and_follow_legacy_row_layout():
    for ep in v7.make_episodes(96, "v7_test", "laptop"):
        for laptop_sc, legacy_sc in ((ep.view.s1, ep.base.s1), (ep.view.s2, ep.base.s2)):
            v7.validate_laptop_scenario(laptop_sc)
            for lp, dp in zip(laptop_sc.plans, legacy_sc.plans):
                assert lp.name == dp.name
                assert laptop_sc.rule_of(lp.name) == v7._TO_LAPTOP_RULE[legacy_sc.rule_of(dp.name)]


def test_laptop_vocabulary_is_single_token_and_disjoint(tok):
    assert len(v7.LAPTOP_WORDS) == len(set(v7.LAPTOP_WORDS)) == len(tasks.WORDS)
    cap_words = {w for item in tasks.cap_bank() for o in item.options for w in o.split()}
    assert not set(v7.LAPTOP_WORDS) & (set(tasks.WORDS) | cap_words)
    for w in v7.LAPTOP_WORDS:
        quoted, listed = tok.tokenize(f'the code word "{w}".'), tok.tokenize(f"1. {w}\n")
        assert len(quoted) == 6 and quoted[-2] == w
        assert len(listed) == 4 and listed[2] == "Ġ" + w
    legacy = {len(chat.encode(tok, " " + p)) for p in tasks.RULE_PHRASE.values()}
    assert {len(chat.encode(tok, " " + p)) for p in v7.LAPTOP_PHRASE.values()} == legacy


def test_use_question_options_and_meanings(tok):
    for variant in v7.VARIANTS:
        for ep in v7.make_episodes(24, "v7_test", variant):
            for k in range(tasks.N_ROTATIONS):
                content, options, meanings, _ = v7.question_body(ep, "A", "USE", k)
                assert sorted(options, key=int) == [str(2 * v) for v in v7.FACT_VALUES]
                assert meanings.count("fact") == 1 and meanings.count("cf") == 1
                assert options[meanings.index("fact")] == str(2 * ep.fact_n)
                assert options[meanings.index("cf")] == str(2 * ep.fact_n_cf)
                assert "Thursday" in content and content.endswith(tasks.ANSWER_LINE)


def test_detect_shows_both_scale_directions_per_episode():
    for ep in v7.make_episodes(8, "v7_test", "base"):
        orders = [v7.question_body(ep, "A", "DETECT", k)[1] for k in ep.base.rotations]
        assert orders[0] == tuple(reversed(orders[1]))
        assert set(orders[0]) == {key for key, _ in v7.DETECT_SCALE}


def test_registered_questions_build_and_keep_legacy_text(tok):
    for variant in v7.VARIANTS:
        ep = v7.make_episodes(4, "v7_test", variant)[1]
        for q in v7.readout_questions(tok, ep, "A"):
            assert q.generative or len(q.options) == len(q.label_meaning) == 4
            assert q.n_ticks > 0
        with pytest.raises(ValueError):
            v7.question_body(ep, "A", "BEH", 0)
    base = v7.make_episodes(4, "v7_test", "base")[1]
    for qid in ("START", "WORD", "NOW", "ACC_RULE", "CAP0"):
        assert v7.question_body(base, "A", qid, 2) == tasks._question_body(base.base, "A", qid, 2)


def test_laptop_questions_use_laptop_vocabulary():
    ep = v7.make_episodes(4, "v7_test", "laptop")[2]
    content, options, meanings, _ = v7.question_body(ep, "A", "START", 1)
    assert set(options) == set(v7.LAPTOP_RULES)
    assert meanings[options.index(ep.view.rule.A)] == "own"
    assert meanings[options.index(ep.view.rule.B)] == "partner"
    assert all(v7.LAPTOP_PHRASE[r] in content for r in options)


def test_record_metadata_expected_use_meaning(tok):
    ep = v7.make_episodes(2, "v7_test", "base")[0]
    q = v7.make_question(tok, ep, "A", "USE", 0)
    assert v7.record_metadata(ep, "A", q)["use_expected_meaning"] == "fact"
    assert v7.record_metadata(ep, "A", q, counterfactual=True)["use_expected_meaning"] == "cf"
    assert v7.record_metadata(ep, "A", q, fact_holder="none")["use_expected_meaning"] is None
    meta = v7.record_metadata(ep, "A", q, counterfactual=True)
    assert meta["fact_shown"] == ep.fact_n_cf and meta["version"] == v7.CONTRACT


def test_spans_refuse_non_qwen_formats(tok, monkeypatch):
    monkeypatch.setattr(chat, "profile_for_tokenizer", lambda _tok: object())
    with pytest.raises(NotImplementedError):
        v7.declared_spans(tok, v7.make_episodes(1, "v7_test", "base")[0], "A")


def test_third_person_donor_card_is_legacy_t3b_plus_note(tok):
    for ep in v7.make_episodes(24, "v7_test", "base"):
        text = v7.private_user_message(ep, "B", frame="third_strict")
        assert _strip_note(text) == tasks.private_user_message(ep.base, "B", "v1", "third_strict")
        ids = v7.private_prefix_ids(tok, ep, "B", frame="third_strict")
        assert ids[-len(chat.encode(tok, tasks.note_opener(ep.base, "B", "third_strict"))):] == \
            chat.encode(tok, tasks.note_opener(ep.base, "B", "third_strict"))
        spans = {n: tok.decode(ids[s:e]).strip() for n, s, e in v7.declared_spans(tok, ep, "B", frame="third_strict")}
        assert spans["holder_rule"] == tasks.RULE_PHRASE[ep.base.rule.B]
        assert spans["participant_line"].startswith("This is the record of participant")


def test_third_person_frame_only_on_base():
    for variant in ("table", "laptop"):
        with pytest.raises(ValueError):
            v7.private_user_message(v7.make_episodes(1, "v7_test", variant)[0], "B", frame="third_strict")
