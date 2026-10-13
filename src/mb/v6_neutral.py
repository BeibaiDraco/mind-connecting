"""Proposed, torch-free neutral admission materials and six-round collection.

This module does not ratify thresholds, authorize hardware, or choose a gain.
Capability and factual-access streams are independent model histories. Only
designated diagnostic families may enter an admission statistic; the actual
continuation choices are retained to reconstruct their histories, not selected.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable

from mb import tasks as historical
from mb import v6_tasks as tasks
from mb.v6_contract import Backend, Probe, RuntimeSpec, canonical_digest
from mb.v6_runtime import EpisodeRunner, PairState

CONTRACT = "v6-neutral-proposed-v1"
STATUS = "proposed_unratified"
STAGES = ("baseline", "calibration", "validation")
FACT_NAMES = ("amber", "blue", "green", "red")
KEY_FIELDS = ("episode_id", "model_profile", "stage", "gain", "stream", "policy",
              "round_id", "side", "qid")
CAP_QIDS = ("CAP0", "CAP1", "CAP2")
BASE_ASSIGNMENT_QIDS = ("assignment_original", "assignment_latest")
CAPABILITY_QIDS = ("task_fullinfo", *CAP_QIDS, "continuation_action")
FACT_QIDS = ("access_fact", "continuation_fact")


def _int(value: Any, low: int, high: int) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Invalid neutral integer")


def _order(value: Any) -> None:
    if type(value) is not tuple or len(value) != 4 or set(value) != set(range(4)):
        raise ValueError("Neutral options require a four-way permutation")
    for x in value:
        _int(x, 0, 3)


def _seed(*values: Any) -> int:
    return int(canonical_digest([CONTRACT, *values])[:16], 16)


@dataclass(frozen=True)
class NeutralEpisode:
    task: tasks.Episode
    stage: str
    facts: tuple[tuple[int, int], ...]
    fact_orders: tuple[tuple[tasks.Four, tasks.Four], ...]
    cap_items: tuple[int, ...]
    cap_orders: tuple[tuple[tasks.Four, tasks.Four], ...]

    def __post_init__(self) -> None:
        if self.stage not in STAGES or not isinstance(self.task, tasks.Episode):
            raise ValueError("Invalid neutral stage/task")
        if type(self.facts) is not tuple or len(self.facts) != 6:
            raise ValueError("Six fresh private fact pairs required")
        for pair in self.facts:
            if type(pair) is not tuple or len(pair) != 2:
                raise ValueError("Private facts require physical A/B pairs")
            for value in pair:
                _int(value, 0, 3)
        if (type(self.cap_items) is not tuple or len(self.cap_items) != 18
                or set(self.cap_items) != set(range(18))):
            raise ValueError("Use every unchanged historical CAP item exactly once")
        for item in self.cap_items:
            _int(item, 0, 17)
        for orders, length in ((self.fact_orders, 6), (self.cap_orders, 18)):
            if type(orders) is not tuple or len(orders) != length:
                raise ValueError("Invalid neutral option schedule")
            for pair in orders:
                if type(pair) is not tuple or len(pair) != 2:
                    raise ValueError("Option schedule requires both physical sides")
                for value in pair:
                    _order(value)

    @property
    def episode_id(self) -> str:
        return self.task.episode_id


@dataclass(frozen=True)
class FactWorld:
    round_id: int = 0
    answers: tuple[tuple[int | None, int | None], ...] = ()

    def __post_init__(self) -> None:
        _int(self.round_id, 0, 6)
        if (type(self.answers) is not tuple or len(self.answers) not in
                ({0} if self.round_id == 0 else {self.round_id - 1, self.round_id})):
            raise ValueError("Fact history has inconsistent round count")
        for pair in self.answers:
            if type(pair) is not tuple or len(pair) != 2:
                raise ValueError("Fact history requires physical A/B answers")
            for value in pair:
                if value is not None:
                    _int(value, 0, 3)


@dataclass(frozen=True)
class NeutralQuestion:
    qid: str
    text: str
    candidates: tasks.Four
    correct: int
    cap_item_id: int | None = None

    def __post_init__(self) -> None:
        if self.qid not in (*CAPABILITY_QIDS, *FACT_QIDS, *BASE_ASSIGNMENT_QIDS):
            raise ValueError("Unknown neutral question")
        if type(self.text) is not str or not self.text:
            raise ValueError("Empty neutral question")
        _order(self.candidates)
        _int(self.correct, 0, 3)
        if self.cap_item_id is not None:
            _int(self.cap_item_id, 0, 17)


def make_episodes(n: int, stage: str, seed: int = 0, *, namespace: str | None = None) -> list[NeutralEpisode]:
    if stage not in STAGES:
        raise ValueError("Unknown neutral material stage")
    _int(n, 1, 1_000_000)
    _int(seed, 0, 2**64 - 1)
    namespace = namespace or stage
    if not re.fullmatch(r"[A-Za-z0-9_-]+", namespace):
        raise ValueError("Invalid neutral material namespace")
    base = tasks.make_episodes(n, f"v6-neutral-{stage}-{namespace}", seed)
    # Independent shuffles by round and side: no within-episode cycle makes a
    # future marker predictable from previous rounds or the other private card.
    columns = {}
    for r in range(6):
        for s in range(2):
            values = [i % 4 for i in range(n)]
            random.Random(_seed(seed, namespace, stage, "facts", r, s)).shuffle(values)
            columns[r, s] = values
    answer = []
    for i, ep in enumerate(base):
        rng = random.Random(_seed(ep.episode_id, "neutral-options"))
        def permutation() -> tasks.Four:
            values = list(range(4)); rng.shuffle(values)
            return tuple(values)
        items = list(range(18)); rng.shuffle(items)
        answer.append(NeutralEpisode(ep, stage,
            tuple(tuple(columns[r, s][i] for s in range(2)) for r in range(6)),
            tuple((permutation(), permutation()) for _ in range(6)), tuple(items),
            tuple((permutation(), permutation()) for _ in range(18))))
    return answer


def episode_to_dict(ep: NeutralEpisode) -> dict:
    return {"contract": CONTRACT, "status": STATUS, "cap_bank_sha256": historical.cap_bank_hash(),
            **asdict(ep)}


def episode_from_dict(value: dict) -> NeutralEpisode:
    if type(value) is not dict or set(value) != {
            "contract", "status", "cap_bank_sha256", "task", "stage", "facts",
            "fact_orders", "cap_items", "cap_orders"}:
        raise ValueError("Invalid neutral material schema")
    if (value["contract"] != CONTRACT or value["status"] != STATUS
            or value["cap_bank_sha256"] != historical.cap_bank_hash()):
        raise ValueError("Neutral material contract or CAP bank differs")
    def pairs(name: str) -> tuple:
        return tuple(tuple(tuple(order) for order in pair) for pair in value[name])
    return NeutralEpisode(tasks.episode_from_dict(value["task"]), value["stage"],
        tuple(tuple(pair) for pair in value["facts"]), pairs("fact_orders"),
        tuple(value["cap_items"]), pairs("cap_orders"))


def material_json(episodes: Iterable[NeutralEpisode]) -> str:
    return json.dumps([episode_to_dict(ep) for ep in episodes], sort_keys=True, indent=2,
                      allow_nan=False) + "\n"


def materials_sha256(episodes: Iterable[NeutralEpisode]) -> str:
    return hashlib.sha256(material_json(episodes).encode()).hexdigest()


def write_materials(path: str | Path, episodes: Iterable[NeutralEpisode]) -> None:
    target, raw = Path(path), material_json(episodes)
    if target.exists():
        if target.read_text() != raw:
            raise ValueError("Refusing to replace existing neutral materials")
        return
    with target.open("x") as handle:
        handle.write(raw)


def load_materials(path: str | Path) -> list[NeutralEpisode]:
    values = json.loads(Path(path).read_text())
    if type(values) is not list or not values:
        raise ValueError("Neutral material list must be nonempty")
    episodes = [episode_from_dict(value) for value in values]
    if len({ep.episode_id for ep in episodes}) != len(episodes):
        raise ValueError("Duplicate neutral episode identity")
    return episodes


def fact_initial_prompts() -> tuple[str, tuple[str, str]]:
    system = ("Participants A and B receive separate private parcel records. "
        "Each round supplies a new current marker, independently of previous markers. "
        "During the work period, keep a brief working note of the current round and "
        "your own marker. Keep participant names and round numbers explicit. "
        "When asked a question, answer with exactly one choice ID.")
    return system, tuple(f"You are participant {role}. Wait for your first private parcel record."
                         for role in tasks.ROLES)


def fact_round_prompts(ep: NeutralEpisode, round_id: int) -> tuple[str, str]:
    _int(round_id, 1, 6)
    return tuple(f"Round {round_id}. Participant {tasks.ROLES[side]}'s current private "
                 f"parcel marker is {FACT_NAMES[ep.facts[round_id-1][side]]}. "
                 "Work on this current record and keep a brief note."
                 for side in range(2))


def _render(qid: str, stem: str, values: tuple[str, ...], order: tasks.Four,
            correct: int, cap_id: int | None = None) -> NeutralQuestion:
    options = "\n".join(f"{label}. {values[value]}" for label, value in zip(tasks.LABELS, order))
    return NeutralQuestion(qid, f"{stem}\n{options}\n{tasks.ANSWER_LINE}", order, correct, cap_id)


def question(ep: NeutralEpisode, stream: str, world: tasks.World | FactWorld,
             side: int, qid: str) -> NeutralQuestion:
    _int(side, 0, 1)
    r = world.round_id
    _int(r, 1, 6)
    if stream == "fact":
        if not isinstance(world, FactWorld) or len(world.answers) != r-1 or qid not in FACT_QIDS:
            raise ValueError("Invalid factual readout boundary")
        target = side if qid == "continuation_fact" else 1-side
        marker, name = ep.facts[r-1][target], tasks.ROLES[target]
        prefix = (f"Supplied record for round {r}: participant {name}'s marker is {FACT_NAMES[marker]}.\n"
                  if ep.stage == "baseline" and qid == "access_fact" else "")
        return _render(qid, prefix + f"What is participant {name}'s current parcel marker in round {r}?",
                       FACT_NAMES, ep.fact_orders[r-1][side], marker)
    if stream != "capability" or not isinstance(world, tasks.World) or len(world.actions) != r-1:
        raise ValueError("Invalid capability readout boundary")
    if qid in CAP_QIDS:
        slot = 3*(r-1) + CAP_QIDS.index(qid)
        item = historical.cap_bank()[ep.cap_items[slot]]
        return _render(qid, item.question, item.options, ep.cap_orders[slot][side],
                       item.options.index(item.correct), item.item_id)
    if qid in ("task_fullinfo", "continuation_action"):
        q = tasks.question(ep.task, world, side, "action")
        prefix = (f"Current authorized record: participant {tasks.ROLES[side]}'s latest goal is "
                  f"{ep.task.goal_names[world.goals[side]]}; participant {tasks.ROLES[1-side]}'s "
                  f"current beacon is {tasks.BEACON_NAMES[world.beacons[1-side]]}.\n"
                  if qid == "task_fullinfo" else "")
        return NeutralQuestion(qid, prefix + q.text, q.candidates, q.correct)
    if ep.stage == "baseline" and qid in BASE_ASSIGNMENT_QIDS:
        which = "original_goal" if qid == "assignment_original" else "latest_goal"
        q = tasks.question(ep.task, world, side, which)
        prefix = (f"Supplied authorized records for participant {tasks.ROLES[side]}: "
                  f"original goal {ep.task.goal_names[ep.task.original_goals[side]]}; "
                  f"latest goal {ep.task.goal_names[world.goals[side]]}.\n")
        return NeutralQuestion(qid, prefix + q.text, q.candidates, q.correct)
    raise ValueError("Question is outside this stage's neutral contract")


def policies(stage: str) -> tuple[str, ...]:
    if stage not in STAGES:
        raise ValueError("Unknown neutral stage")
    return ("OFF",) if stage == "baseline" else ("OFF", "LIVE")


def qids(stage: str, stream: str) -> tuple[str, ...]:
    if stream == "fact":
        return FACT_QIDS
    if stream == "capability":
        return ("task_fullinfo", *CAP_QIDS,
                *(BASE_ASSIGNMENT_QIDS if stage == "baseline" else ()), "continuation_action")
    raise ValueError("Unknown neutral stream")


def _gain(stage: str, gain: float) -> None:
    if type(gain) not in (int, float) or not math.isfinite(gain):
        raise ValueError("Invalid neutral gain")
    allowed = (0.0,) if stage == "baseline" else (0.25, 0.5, 1.0)
    if gain not in allowed:
        raise ValueError("Neutral stage gain differs from the proposed finite grid")


def expected_keys(ep: NeutralEpisode, model_profile: str, gain: float) -> set[tuple]:
    _gain(ep.stage, gain)
    return {(ep.episode_id, model_profile, ep.stage, gain, stream, policy, r, side, qid)
            for policy in policies(ep.stage) for stream in ("capability", "fact")
            for r in range(1, 7) for side in range(2) for qid in qids(ep.stage, stream)}


def audit_tokenizer(tokenizer: Any, episodes: Iterable[NeutralEpisode]) -> dict:
    """Audit exact rendered native answer boundaries, without loading a model."""
    from mb import chat
    from mb.v6_native import NativeTokens

    eps = list(episodes)
    tokens = NativeTokens.from_tokenizer(tokenizer)
    checked, appends, errors = 0, 0, []
    label_ids = tokens.choice_ids(tasks.LABELS)
    for ep in eps:
        for stream in ("capability", "fact"):
            system, users = tasks.initial_prompts(ep.task) if stream == "capability" else fact_initial_prompts()
            histories = [[{"role":"system","content":system}, {"role":"user","content":user},
                          {"role":"assistant","content":"A brief private preparation note."}]
                         for user in users]
            world = tasks.initial_world(ep.task) if stream == "capability" else FactWorld()
            for r in range(1,7):
                world = tasks.event_world(ep.task,world,r) if stream == "capability" else replace(world,round_id=r)
                prompts = (tasks.round_prompts(ep.task,world,r,tasks.updated_sides(ep.task,r))
                           if stream == "capability" else fact_round_prompts(ep,r))
                for s in (0,1):
                    tokens.initial(system,users[s]); tokens.user_turn(prompts[s])
                    histories[s].extend([{"role":"user","content":prompts[s]},
                                         {"role":"assistant","content":"A brief current working note."}])
                    completed = tuple(chat.native_conversation(tokenizer,histories[s]))
                    for qid in qids(ep.stage,stream):
                        q = question(ep,stream,world,s,qid)
                        prefix = (*completed,*tokens.user_turn(q.text))
                        native = tuple(chat.native_conversation(tokenizer,
                            [*histories[s],{"role":"user","content":q.text}], add_generation_prompt=True))
                        checked += 1
                        if prefix != native:
                            errors.append(f"native_boundary:{ep.episode_id}:{stream}:{r}:{s}:{qid}")
                        rendered=tokenizer.decode(prefix,skip_special_tokens=False,clean_up_tokenization_spaces=False)
                        if tuple(chat.encode(tokenizer,rendered)) != prefix:
                            errors.append(f"decode_roundtrip:{ep.episode_id}:{stream}:{r}:{s}:{qid}")
                        for label,token in zip(tasks.LABELS,label_ids):
                            appends += 1
                            if tuple(chat.encode(tokenizer,rendered+label)) != (*prefix,token):
                                errors.append(f"label_append:{ep.episode_id}:{stream}:{r}:{s}:{qid}:{label}")
                continuation = "continuation_action" if stream == "capability" else "continuation_fact"
                answers=[]
                for s in (0,1):
                    q=question(ep,stream,world,s,continuation); answers.append(q.correct)
                    histories[s].extend([{"role":"user","content":q.text},
                        {"role":"assistant","content":tasks.LABELS[q.candidates.index(q.correct)]}])
                world = (tasks.transition(world,tuple(answers)) if stream == "capability"
                         else replace(world,answers=(*world.answers,tuple(answers))))
    return {"contract":CONTRACT,"status":"tokenizer_only_not_hardware_acceptance",
            "profile":tokens.profile_key,"episodes":len(eps),"materials_sha256":materials_sha256(eps),
            "cap_bank_sha256":historical.cap_bank_hash(),"native_answer_prefixes":checked,
            "label_append_checks":appends,"passed":not errors,"errors":errors,
            "limits":"Rendered histories use oracle answers only for boundary enumeration; no model performance, generated-cache continuation or equal-length fact claim."}


class NeutralRunner:
    """Collect draft diagnostics; the caller owns identity, persistence and approval."""

    def __init__(self, backend: Backend, spec: RuntimeSpec, model_profile: str, *,
                 sink: Any = None, side_order: tuple[int, int] = (0, 1)):
        self.engine = EpisodeRunner(backend, spec, model_profile, side_order=side_order)
        self.backend, self.spec, self.model_profile, self.sink = backend, spec, model_profile, sink
        self.records: list[dict] = []

    def _read(self, ep: NeutralEpisode, pair: PairState, stream: str, policy: str,
              side: int, qid: str, held: tuple) -> tuple[Probe, int | None]:
        q = question(ep, stream, pair.world, side, qid)
        before = self.engine.digest(pair)
        p = self.backend.probe(pair.models[side], q.text, self.spec.choice_labels,
                               held[side], self.spec.gain)
        p.validate()
        if self.engine.digest(pair) != before:
            raise RuntimeError("Neutral probe contaminated the continuing pair")
        choice = q.candidates[p.token_ids.index(p.token)] if p.token in p.token_ids else None
        row = {"contract": CONTRACT, "proposal_status": STATUS, "episode_id": ep.episode_id,
            "model_profile": self.model_profile, "stage": ep.stage, "gain": self.spec.gain,
            "stream": stream, "policy": policy, "round_id": pair.world.round_id,
            "side": side, "qid": qid, "status": "ok", "choice": choice,
            "correct_choice": q.correct, "correct": choice == q.correct,
            "candidate_map": list(q.candidates), "cap_item_id": q.cap_item_id,
            "material_sha256": canonical_digest(episode_to_dict(ep)),
            "question_sha256": hashlib.sha256(q.text.encode()).hexdigest(),
            "world": asdict(pair.world), "top_token": p.token, "top_probability": p.probability,
            "legal_logits": list(p.legal_logits), "legal_mass": p.legal_mass,
            "token_ids": list(p.token_ids)}
        if getattr(self.backend, "kind", None) == "synthetic_fixture":
            row.update(backend_kind="synthetic_fixture", scientific_data=False)
        self.records.append(row)
        if self.sink is not None:
            self.sink(row)
        return p, choice

    def _round_reads(self, ep: NeutralEpisode, pair: PairState, stream: str,
                     policy: str, held: tuple) -> tuple:
        # Diagnostic states never enter a continuing stream. Both actual answers
        # are sealed before either side commits, exactly as in the main task.
        continuation = "continuation_action" if stream == "capability" else "continuation_fact"
        for qid in qids(ep.stage, stream):
            if qid != continuation:
                for side in (0, 1):
                    self._read(ep, pair, stream, policy, side, qid, held)
        actual = [self._read(ep, pair, stream, policy, side, continuation, held) for side in (0, 1)]
        pair.models = tuple(self.backend.commit_answer(actual[s][0], held[s], self.spec.gain)
                            for s in (0, 1))
        return tuple(value[1] for value in actual)

    def _capability(self, ep: NeutralEpisode, policy: str) -> None:
        pair = self.engine.initialize(ep.task)
        for r in range(1, 7):
            self.engine.prepare(ep.task, pair, r)
            _, held = self.engine.work(pair, policy)
            choices = self._round_reads(ep, pair, "capability", policy, held)
            pair.world = tasks.transition(pair.world, choices)

    def _fact(self, ep: NeutralEpisode, policy: str) -> None:
        system, users = fact_initial_prompts()
        pair = PairState(tuple(self.backend.create(system, user) for user in users), FactWorld())
        for state in pair.models:
            for _ in range(self.spec.preparation_tokens):
                self.backend.step(state, (), 0.0)
            self.backend.finish_turn(state)
        for r in range(1, 7):
            pair.world = replace(pair.world, round_id=r)
            pair.windows = ((), ())
            for side, text in enumerate(fact_round_prompts(ep, r)):
                self.backend.begin_user(pair.models[side], text)
            _, held = self.engine.work(pair, policy)
            choices = self._round_reads(ep, pair, "fact", policy, held)
            pair.world = replace(pair.world, answers=(*pair.world.answers, choices))

    def run_episode(self, ep: NeutralEpisode) -> list[dict]:
        _gain(ep.stage, self.spec.gain)
        self.records = []
        for policy in policies(ep.stage):
            self._capability(ep, policy)
            self._fact(ep, policy)
        validate_records(self.records, [ep], self.model_profile, self.spec.gain)
        return self.records


def _native(row: dict) -> None:
    ids, candidates = row["token_ids"], row["candidate_map"]
    if (type(ids) is not list or len(ids) != 4 or len(set(ids)) != 4
            or any(type(i) is not int or i < 0 for i in ids)
            or type(row["top_token"]) is not int or row["top_token"] < 0):
        raise ValueError("Invalid neutral native choice IDs")
    _order(tuple(candidates))
    logits = row["legal_logits"]
    if type(logits) is not list or len(logits) != 4:
        raise ValueError("Invalid neutral logits")
    for value in (*logits, row["top_probability"], row["legal_mass"]):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("Non-finite neutral native readout")
    if not 0 <= row["top_probability"] <= 1 or not 0 <= row["legal_mass"] <= 1.000001:
        raise ValueError("Invalid neutral probability")
    choice = candidates[ids.index(row["top_token"])] if row["top_token"] in ids else None
    if (row["choice"] is not None and type(row["choice"]) is not int) or row["choice"] != choice:
        raise ValueError("Neutral choice differs from actual native token")


def validate_records(records: Iterable[dict], episodes: Iterable[NeutralEpisode], model_profile: str,
                     gain: float, *, require_complete: bool = True) -> dict:
    """Reconstruct questions/worlds from materials and actual preceding choices.

    This validates raw truth and technical completeness only. It never admits a
    scientific stage or fills missing data; source/approval admission is external.
    """
    eps = list(episodes)
    if not eps or len({ep.episode_id for ep in eps}) != len(eps):
        raise ValueError("Declare nonempty unique neutral materials")
    expected = set().union(*(expected_keys(ep, model_profile, gain) for ep in eps))
    ledger, failed, seen = {}, set(), set()
    synthetic = False
    for row in records:
        if type(row) is not dict:
            raise ValueError("Neutral raw record must be a mapping")
        try:
            key = tuple(row[k] for k in KEY_FIELDS)
            if key not in expected or key in seen:
                raise ValueError("Unexpected or duplicate neutral readout key")
            if (row["contract"] != CONTRACT or row["proposal_status"] != STATUS
                    or row["status"] not in ("ok", "technical_failure")
                    or type(row["round_id"]) is not int or type(row["side"]) is not int
                    or type(row["gain"]) not in (int, float) or not math.isfinite(row["gain"])):
                raise ValueError("Invalid neutral record status/contract")
            seen.add(key)
            if row["status"] == "technical_failure":
                failed.add(key)
                continue
            if type(row["correct"]) is not bool or type(row["correct_choice"]) is not int:
                raise ValueError("Invalid neutral correctness metadata")
            _native(row)
        except (KeyError, TypeError) as exc:
            raise ValueError("Malformed neutral raw record") from exc
        synthetic |= row.get("scientific_data") is False or str(row.get("backend_kind", "")).startswith("synthetic")
        ledger[key] = row
    for ep in eps:
        digest = canonical_digest(episode_to_dict(ep))
        for policy in policies(ep.stage):
            for stream in ("capability", "fact"):
                world: tasks.World | FactWorld = tasks.initial_world(ep.task) if stream == "capability" else FactWorld()
                known = True
                for r in range(1, 7):
                    rows = { (side, qid): ledger.get((ep.episode_id, model_profile, ep.stage, gain,
                             stream, policy, r, side, qid))
                             for side in range(2) for qid in qids(ep.stage, stream)}
                    if not known:
                        if any(row is not None for row in rows.values()):
                            raise ValueError("Neutral rows follow an incomplete action history")
                        continue
                    world = tasks.event_world(ep.task, world, r) if stream == "capability" else replace(world, round_id=r)
                    for (side, qid), row in rows.items():
                        if row is None:
                            continue
                        q = question(ep, stream, world, side, qid)
                        expected_fields = {"material_sha256": digest,
                            "question_sha256": hashlib.sha256(q.text.encode()).hexdigest(),
                            "candidate_map": list(q.candidates), "correct_choice": q.correct,
                            "correct": row["choice"] == q.correct, "cap_item_id": q.cap_item_id,
                            "world": json.loads(json.dumps(asdict(world)))}
                        for name, value in expected_fields.items():
                            if canonical_digest(row.get(name)) != canonical_digest(value):
                                raise ValueError(f"Neutral material/question/world mismatch: {name}")
                    qid = "continuation_action" if stream == "capability" else "continuation_fact"
                    actual = [rows[s, qid] for s in range(2)]
                    known = all(row is not None for row in actual)
                    if known:
                        choices = tuple(row["choice"] for row in actual)
                        world = (tasks.transition(world, choices) if stream == "capability"
                                 else replace(world, answers=(*world.answers, choices)))
    missing = len(expected-ledger.keys())
    if require_complete and missing:
        raise ValueError("Incomplete neutral ledger; no gate may consume it")
    return {"contract": CONTRACT, "status": STATUS, "complete": missing == 0,
            "expected_records": len(expected), "ok_records": len(ledger), "missing_records": missing,
            "technical_failures": len(failed), "synthetic": synthetic,
            "source_verified": False, "scientific_admission": False}
