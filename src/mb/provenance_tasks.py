"""V5 source-qualified readouts; physical candidates never follow the donor swap.

This module is opt-in. The original task registry, default questions and prompts
retain their frozen meaning for v1-v4.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any

from mb import chat, tasks

CONTRACT = "v5-provenance-v1"
SELF_QIDS = ("PROV_SELF_RULE", "PROV_ROBIN_RULE", "PROV_SELF_WORD", "PROV_ROBIN_WORD")
DONOR_QIDS = ("PROV_DONOR_SELF_RULE", "PROV_DONOR_ROBIN_RULE",
              "PROV_DONOR_SELF_WORD", "PROV_DONOR_ROBIN_WORD")
QIDS = SELF_QIDS + DONOR_QIDS
BASELINE_QIDS = SELF_QIDS + ("START", "WORD", "CAP0", "CAP1")
VALIDITY_QIDS = DONOR_QIDS + ("CAP0", "CAP1")
ALL_QIDS = QIDS + ("START", "WORD", "CAP0", "CAP1")
STAGES = {f"v5_{model}_provenance_{phase}": (profile, phase)
          for model, profile in (("llama31", "llama31_8b_instruct"),
                                 ("qwen", "qwen3_4b_instruct_2507"))
          for phase in ("smoke", "base", "validity", "confirm")}
PHASE_QIDS = {"smoke": ALL_QIDS, "base": BASELINE_QIDS,
              "validity": VALIDITY_QIDS, "confirm": ALL_QIDS}


def donor_episode(ep: tasks.Episode) -> tasks.Episode:
    """Change only the B record's Robin assignment; all four values remain distinct."""
    return replace(ep, rule=tasks.Assign(ep.rule.A, ep.rule.B, ep.rule.spare, ep.rule.robin),
                   word=tasks.Assign(ep.word.A, ep.word.B, ep.word.spare, ep.word.robin))


def _records(ep: tasks.Episode, donor: tasks.Episode, recipient: str):
    if recipient not in tasks.ROLES:
        raise ValueError("provenance recipient must be A or B")
    return (ep, donor) if recipient == "A" else (donor, ep)


def candidates(ep: tasks.Episode) -> dict[str, dict[str, str]]:
    return {kind: {label: getattr(getattr(ep, kind), role)
                   for label, role in (("a", "A"), ("b", "B"), ("r", "robin"), ("d", "spare"))}
            for kind in ("rule", "word")}


def _truth(ep: tasks.Episode, role: str) -> dict[str, str]:
    return {"rule_self": ep.rule.of(role), "rule_robin": ep.rule.robin,
            "word_self": ep.word.of(role), "word_robin": ep.word.robin}


def question_body(ep: tasks.Episode, recipient: str, qid: str,
                  rotation: int) -> tuple[str, tuple[str, ...], tuple[str, ...], int | None]:
    """Pure canonical content for offline audits, without loading a tokenizer."""
    if recipient not in tasks.ROLES:
        raise ValueError("provenance recipient must be A or B")
    if qid not in QIDS:
        if qid not in ALL_QIDS:
            raise ValueError(f"not a provenance question: {qid}")
        return tasks._question_body(ep, recipient, qid, rotation)
    source_role = tasks.other(recipient) if qid in DONOR_QIDS else recipient
    source = ep.codename[source_role]
    subject = "Robin" if "ROBIN" in qid else source
    kind = "rule" if qid.endswith("RULE") else "word"
    noun = "priority" if kind == "rule" else "code word"
    options = tasks._rotate(tasks.RULES if kind == "rule" else ep.word_base_order, rotation)
    displayed = [tasks.RULE_PHRASE[value] if kind == "rule" else value for value in options]
    content = (f"According to participant {source}'s original private record, which {noun} "
               f"was {subject} assigned?\n{tasks._numbered(displayed)}\n{tasks.ANSWER_LINE}")
    meanings = tuple(ep.rule_meaning(recipient, value) if kind == "rule"
                     else ep.word_meaning(recipient, value) for value in options)
    return content, options, meanings, None


def make_question(tok, ep: tasks.Episode, donor: tasks.Episode, recipient: str,
                  qid: str, rotation: int) -> tasks.Question:
    """Question text/options depend on the original pair, never on the treatment."""
    _records(ep, donor, recipient)
    content, options, meanings, cap_id = question_body(ep, recipient, qid, rotation)
    if qid not in QIDS:
        return tasks.make_question(tok, ep, recipient, qid, rotation)
    kind = "rule" if qid.endswith("RULE") else "word"
    return tasks.Question(qid, "provenance_" + kind, recipient, rotation, content,
                          options, meanings, cap_id, False, tuple(chat.readout_suffix(tok, content)))


def record_metadata(ep: tasks.Episode, recipient: str, q: tasks.Question,
                    conflict: bool, materials: str = "v1") -> dict[str, Any]:
    donor = donor_episode(ep) if conflict else ep
    receiver_record, other_record = _records(ep, donor, recipient)
    partner = tasks.other(recipient)
    receiver_truth, donor_truth = _truth(receiver_record, recipient), _truth(other_record, partner)
    source_role = expected = None
    kind = None
    if q.qid in QIDS:
        kind = "rule" if q.qid.endswith("RULE") else "word"
        source_role = partner if q.qid in DONOR_QIDS else recipient
        truth = donor_truth if q.qid in DONOR_QIDS else receiver_truth
        expected = truth[kind + ("_robin" if "ROBIN" in q.qid else "_self")]
    elif q.qid in ("START", "WORD"):
        kind = "rule" if q.qid == "START" else "word"
        source_role, expected = recipient, receiver_truth[kind + "_self"]
    physical = candidates(ep)
    labels = ({key: str(q.options.index(value) + 1) for key, value in physical[kind].items()}
              if kind else {})
    def card_hash(record, role):
        return hashlib.sha256(tasks.private_user_message(record, role, materials).encode()).hexdigest()
    return {"version": CONTRACT, "donor_robin_conflict": conflict,
            "recipient_role": recipient, "donor_role": partner,
            "recipient_name": ep.codename[recipient], "donor_name": ep.codename[partner],
            "receiver_card_sha256": card_hash(receiver_record, recipient),
            "donor_card_sha256": card_hash(other_record, partner),
            "candidates": physical, "candidate_labels": labels,
            "receiver_truth": receiver_truth, "donor_truth": donor_truth,
            "source_role": source_role, "expected_truth": expected}


def render_question(tok, original_ep: tasks.Episode, recipient: str, qid: str,
                    rotation: int, conflict: bool = False) -> tasks.Question:
    """Public preflight helper using the same constructor as the runtime."""
    donor = donor_episode(original_ep) if conflict else original_ep
    return make_question(tok, original_ep, donor, recipient, qid, rotation)


def template_sequences(tok, materials: str = "v1") -> list[list[int]]:
    ep = tasks.make_episodes(1, "provenance-template-ref", seed=0)[0]
    donor = donor_episode(ep)
    seqs = [tasks.private_prefix_ids(tok, donor, "B", materials)]
    for recipient in tasks.ROLES:
        seqs += [list(make_question(tok, ep, donor, recipient, qid, rotation).suffix_ids)
                 for qid in QIDS for rotation in range(tasks.N_ROTATIONS)]
    return seqs
