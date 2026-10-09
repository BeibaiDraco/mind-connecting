"""Physical answers, source truths and tokenizer-level treatment invariance."""

import dataclasses
import hashlib

import pytest

from mb import chat, provenance_tasks as p, tasks
from mb.model_profiles import LLAMA31, QWEN


@pytest.fixture(scope="module", params=[QWEN, LLAMA31], ids=["qwen", "llama"])
def tok(request):
    return chat.load_tokenizer(profile=request.param.key)


def test_conflict_changes_only_donor_robin_and_preserves_candidate_set(tok):
    for ep in tasks.make_episodes(4, "provenance-materials"):
        donor = p.donor_episode(ep)
        assert donor.rule == tasks.Assign(ep.rule.A, ep.rule.B, ep.rule.spare, ep.rule.robin)
        assert donor.word == tasks.Assign(ep.word.A, ep.word.B, ep.word.spare, ep.word.robin)
        for f in dataclasses.fields(ep):
            if f.name not in ("rule", "word"):
                assert getattr(donor, f.name) == getattr(ep, f.name)
        assert tasks.private_prefix_ids(tok, ep, "A") != tasks.private_prefix_ids(tok, donor, "A")
        # The mutation is a DONOR view: the runner must keep A on ep, not donor.
        assert tasks.note_key(ep, "B") != tasks.note_key(donor, "B")
        assert sorted(donor.word_base_order) == sorted(dataclasses.astuple(donor.word))


def test_all_source_questions_keep_exact_tokens_and_physical_labels_across_treatment(tok):
    ep = tasks.make_episodes(1, "provenance-question-tokens")[0]
    donor = p.donor_episode(ep)
    for recipient in tasks.ROLES:
        for qid in p.ALL_QIDS:
            for k in range(4):
                before = p.make_question(tok, ep, ep, recipient, qid, k)
                after = p.make_question(tok, ep, donor, recipient, qid, k)
                assert before == after
                assert after.suffix_ids == tuple(chat.readout_suffix(tok, after.user_content))
                if qid in p.QIDS:
                    source = tasks.other(recipient) if qid in p.DONOR_QIDS else recipient
                    assert f"participant {ep.codename[source]}'s original private record" in after.user_content


def test_source_truths_use_actual_card_and_keep_global_a_b_r_d(tok):
    ep = tasks.make_episodes(1, "provenance-truths")[0]
    donor = p.donor_episode(ep)
    for recipient in tasks.ROLES:
        for qid in p.ALL_QIDS:
            q = p.make_question(tok, ep, donor, recipient, qid, 2)
            meta = p.record_metadata(ep, recipient, q, True)
            assert meta["candidates"]["rule"] == dict(a=ep.rule.A, b=ep.rule.B, r=ep.rule.robin, d=ep.rule.spare)
            expected_receiver = ep if recipient == "A" else donor
            expected_other = donor if recipient == "A" else ep
            assert meta["receiver_truth"]["rule_robin"] == expected_receiver.rule.robin
            assert meta["donor_truth"]["word_robin"] == expected_other.word.robin
            card = tasks.private_user_message(expected_receiver, recipient)
            assert meta["receiver_card_sha256"] == hashlib.sha256(card.encode()).hexdigest()
            if qid in ("CAP0", "CAP1"):
                assert meta["expected_truth"] is None and meta["candidate_labels"] == {}
                continue
            kind = "word" if "WORD" in qid else "rule"
            source = tasks.other(recipient) if qid in p.DONOR_QIDS else recipient
            record = donor if source == "B" else ep
            item = "robin" if "ROBIN" in qid else source
            assert meta["source_role"] == source
            assert meta["expected_truth"] == getattr(getattr(record, kind), item)
            for label, physical in meta["candidates"][kind].items():
                assert q.options[int(meta["candidate_labels"][label]) - 1] == physical


def test_legacy_registry_does_not_silently_add_provenance():
    assert not set(tasks.QIDS) & set(p.QIDS)
    assert not set(tasks.DEFAULT_QIDS) & set(p.QIDS)
    assert tasks.registered_qids() == tasks.QIDS
    assert set(tasks.registered_qids(provenance=True)) == set(tasks.QIDS) | set(p.QIDS)
    assert len(p.ALL_QIDS) == 12 and len(p.BASELINE_QIDS) == 8 and len(p.VALIDITY_QIDS) == 6
