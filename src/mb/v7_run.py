"""V7 material adapter and raw collector; no selection or scientific analysis.

``python -m mb.v7_run CONFIG`` prints an offline schedule. Execution additionally
requires ``--execute --approved-protocol-sha256 SHA`` after PI approval. Formal
execution requires the config, protocol and package sources at ``protocol-v7``.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from mb import chat, ledger, run, tasks, v7_tasks as material
from mb.conditions import ArmConfig
from mb.kv_geometry import bank_metadata
from mb.model_profiles import QWEN

CONTRACT = "v7-runner-v1"
ATTENTION_LOGGING = {"schema": "v7-answer-position-v1", "readout": "last_suffix_query",
                     "open_answer": "all_tokens", "reflection": False, "generated_continuation": True}
PROTOCOL = run.REPO_ROOT / "docs/protocol/PROTOCOL_V7_DRAFT.md"
OPEN_ARMS = frozenset({"c0", "orig_w2", "trans_w2", "orig_w1", "trans_w1",
                       "same_orig_w2", "same_trans_w2", "third_orig_w2", "third_trans_w2"})


@dataclasses.dataclass(frozen=True)
class V7Arm(ArmConfig):
    arm_id: str = ""
    variant: str = "base"
    fact_holder: str = "B"
    counterfactual_fact: bool = False
    copy_A: bool = False

    @property
    def name(self) -> str:
        return f"V7/{self.variant}/{self.arm_id}"


def arms_for(variant: str) -> list[V7Arm]:
    if variant not in material.VARIANTS:
        raise ValueError(f"unknown V7 variant {variant}")

    def arm(name: str, **changes) -> V7Arm:
        args = dict(condition="ONE", interface="kv", kv_scope="P", gain=2.0,
                    kv_log_spans=True, model_profile=QWEN.key, variant=variant, arm_id=name)
        if name.startswith("c0"):
            args.update(condition="C0", interface="residual", kv_scope=None, gain=0.0, kv_log_spans=False)
        if "trans" in name:
            args["kv_position"] = "before_own"
        args.update(changes)
        return V7Arm(**args)

    base = [arm("c0"), arm("c0_fullinfo", fact_holder="A"), arm("orig_w2"), arm("trans_w2"),
            arm("orig_w2_cf", counterfactual_fact=True), arm("trans_w2_cf", counterfactual_fact=True),
            arm("orig_w1", gain=1.0), arm("trans_w1", gain=1.0),
            arm("orig_w2_ro", readout_mode="RO"), arm("trans_w2_ro", readout_mode="RO"),
            arm("same_orig_w2", copy_A=True), arm("same_trans_w2", copy_A=True),
            arm("third_orig_w2", partner_frame="third_strict"),
            arm("third_trans_w2", partner_frame="third_strict")]
    names = {"c0", "orig_w2", "trans_w2", "orig_w2_cf", "trans_w2_cf"}
    return base if variant == "base" else [a for a in base if a.arm_id in names]


def qids_for(arm: V7Arm) -> tuple[str, ...]:
    return tuple(q for q in material.VARIANT_QIDS[arm.variant] if q != "U_OPEN" or arm.arm_id in OPEN_ARMS)


@dataclasses.dataclass(frozen=True)
class V7Config:
    split: str
    variant: str
    n_episodes: int
    tag: str = "v7"
    seed: int = 0
    episodes_per_batch: int = 8
    max_rows: int = 32

    def __post_init__(self) -> None:
        if self.split not in ("v7_dev", "v7_pilot", "v7_formal") or self.variant not in material.VARIANTS:
            raise ValueError("V7 requires a registered split and variant")
        for name in ("n_episodes", "episodes_per_batch", "max_rows"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.max_rows < 2:
            raise ValueError("max_rows must accommodate an A/B pair")
        if type(self.seed) is not int or not re.fullmatch(r"[A-Za-z0-9_-]+", self.tag):
            raise ValueError("invalid seed or run tag")
        if self.split == "v7_pilot" and (self.variant != "base" or self.n_episodes != 80):
            raise ValueError("the declared V7 pilot is 80 base episodes")

    @property
    def stage(self) -> str:
        return f"{self.split}_{self.variant}"

    model_profile = QWEN.key
    materials = "v1"  # legacy note length and reflection clock
    provenance = False
    params = None
    all_rotations_first = 0

    def arm_configs(self) -> list[V7Arm]:
        return arms_for(self.variant)

    def resolved(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def episodes_for(cfg: V7Config, limit: int | None = None) -> list[material.V7Episode]:
    if limit is not None and (type(limit) is not int or not 1 <= limit <= cfg.n_episodes):
        raise ValueError("limit must be in 1..n_episodes")
    return material.make_episodes(cfg.n_episodes, cfg.split, cfg.variant, cfg.seed)[:limit]


def expected_trials(cfg: V7Config, limit: int | None = None) -> list[ledger.TrialKey]:
    return [(ep.episode_id, arm.name, "A", qid, rotation)
            for ep in episodes_for(cfg, limit) for arm in cfg.arm_configs() for qid in qids_for(arm)
            for rotation in ((None,) if qid == "U_OPEN" else ep.base.rotations)]


def input_context(arm: V7Arm, role: str) -> tuple[str, str, bool, str]:
    source = "A" if arm.copy_A else role
    return (source, arm.fact_holder, arm.counterfactual_fact and source == "B",
            arm.partner_frame if source == "B" else "second")


def reflection_ids(tok, ep: material.V7Episode, role: str, frame: str) -> list[int]:
    if frame == "third_strict":
        return [*chat.turn(tok, "user", tasks.third_person_reflection_prompt(ep.view.codename[role])),
                *chat.header(tok)]
    return tasks.reflection_turn_ids(tok)


def material_digest(cfg: V7Config, tok) -> str:
    """Bind every scheduled token input and declared span, including all CAP items drawn."""
    digest = hashlib.sha256()

    def add(value) -> None:
        digest.update(json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n")

    add((CONTRACT, material.CONTRACT, tasks.NOTE_MAX_TOKENS, tasks.REFLECTION_TICKS, tasks.U_OPEN_TOKENS))
    add(chat.close(tok))
    contexts = sorted({input_context(a, r) for a in cfg.arm_configs() for r in tasks.ROLES})
    for ep in episodes_for(cfg):
        add(ep.episode_id)
        for role, holder, cf, frame in contexts:
            add((role, holder, cf, frame, material.private_prefix_ids(tok, ep, role, holder, cf, frame),
                 material.declared_spans(tok, ep, role, holder, cf, frame), reflection_ids(tok, ep, role, frame)))
        for q in material.readout_questions(tok, ep, "A"):
            add((q.qid, q.rotation_id, q.suffix_ids, q.label_meaning, q.cap_item_id))
    return digest.hexdigest()


def build_identity(cfg: V7Config, tok, limit: int | None = None) -> dict[str, Any]:
    episodes_for(cfg, limit)
    template = material_digest(cfg, tok)
    identity = {"contract": CONTRACT, "stage_config": cfg.resolved(), "limit": limit,
            "attention_logging": ATTENTION_LOGGING,
            "model_profile": QWEN.identity(), "template_hash": template,
            "tokenizer_manifest_sha": ledger.file_sha256(Path(QWEN.manifest_path)),
            "protocol_sha256": ledger.file_sha256(PROTOCOL),
            "material_source_sha256": ledger.file_sha256(Path(material.__file__)),
            "source_hash": run.source_hash(),
            "arms": [a.identity("none", "none", template) for a in cfg.arm_configs()],
            "expected_trials_sha256": ledger.canonical_hash(expected_trials(cfg, limit), 64)}
    return json.loads(json.dumps(identity))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_bytes().splitlines()
    records = []
    for index, line in enumerate(lines):
        try:
            record = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            marker = {"truncated_tail_sha256": hashlib.sha256(line).hexdigest()}
            if index != len(lines) - 1 and lines[index + 1] != json.dumps(marker).encode():
                raise ValueError(f"corrupt JSONL body: {path}:{index + 1}") from None
            continue
        if not isinstance(record, dict):
            raise ValueError(f"non-object JSONL record: {path}:{index + 1}")
        if "truncated_tail_sha256" not in record:
            records.append(record)
    return records


def _append(path: Path, record: dict[str, Any]) -> None:
    separator = ""
    if path.exists() and path.stat().st_size:
        with path.open("rb") as fh:
            pos = fh.seek(0, 2)
            data = b""
            while pos and len(data.splitlines()) < 2:
                width = min(pos, 4096)
                pos -= width
                fh.seek(pos)
                data = fh.read(width) + data
            separator = "" if data.endswith(b"\n") else "\n"
        tail = data.splitlines()[-1]
        try:
            json.loads(tail)
        except (json.JSONDecodeError, UnicodeDecodeError):
            separator += json.dumps({"truncated_tail_sha256": hashlib.sha256(tail).hexdigest()}) + "\n"
    with path.open("a") as fh:
        fh.write(separator + json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")


def _check_notes(path: Path) -> list[dict[str, Any]]:
    records = _read_jsonl(path)
    seen = {}
    for record in records:
        ids = record.get("ids")
        if (record.get("contract") != CONTRACT or not isinstance(ids, list)
                or len(ids) > tasks.NOTE_MAX_TOKENS or any(type(i) is not int or i < 0 for i in ids)
                or record.get("n_tokens") != len(ids)
                or record.get("ids_sha256") != ledger.canonical_hash(ids, 64)
                or record.get("key") != ledger.canonical_hash(record.get("context"), 64)):
            raise ValueError("invalid V7 note cache record")
        if seen.setdefault(record["key"], record) != record:
            raise ValueError("conflicting V7 note cache records")
    return records


def prepare_run(cfg: V7Config, config_path: Path, limit: int | None = None, resume: Path | None = None,
                allow_code_change: bool = False, tok=None) -> run.Prepared:
    """Offline preparation; reject identity or ledger corruption before any resume write."""
    raw = config_path.read_text()
    if V7Config(**yaml.safe_load(raw)) != cfg:
        raise ValueError("input config differs from the resolved configuration")
    tok = tok if tok is not None else chat.load_tokenizer(profile=QWEN.key)
    chat.require_verified_tokenizer(tok, QWEN.key)
    identity = build_identity(cfg, tok, limit)
    smoke = cfg.split == "v7_dev" or limit is not None
    hashes = {a.name: a.config_hash("none", "none", identity["template_hash"]) for a in cfg.arm_configs()}
    if resume is not None:
        stored = run._read_json(resume / "identity.json")
        omit = {"source_hash"} if allow_code_change else set()
        diff = ledger.compare_identity({k: v for k, v in stored.items() if k not in omit},
                                       {k: v for k, v in identity.items() if k not in omit})
        if diff:
            raise SystemExit(f"resume refused: identity differs in {diff}")
        records = ledger.load_records(resume).records
        expected = set(expected_trials(cfg, limit))
        if any(ledger.trial_key(r) not in expected or r.get("config_hash") != hashes.get(r.get("arm"))
               for r in records):
            raise SystemExit("resume refused: records outside the declared trial/identity contract")
        if (resume / "arm_hashes.json").exists() and run._read_json(resume / "arm_hashes.json") != hashes:
            raise SystemExit("resume refused: arm_hashes differ")
        _check_notes(resume / "notes.jsonl")
        snapshots = _read_jsonl(resume / "snapshots.jsonl")
        snapshots += [{"key": r["c48_snapshot_key"], "sha256": r["c48_snapshot_sha256"]}
                      for r in records if "c48_snapshot_key" in r]
        seen = {}
        for snap in snapshots:
            if seen.setdefault(snap["key"], snap["sha256"]) != snap["sha256"]:
                raise SystemExit("resume refused: conflicting C48 snapshot hashes")
        _append(resume / "resume_log.jsonl", {"resumed": dt.datetime.now().isoformat(),
                "git": run.git_state(), "source_hash": identity["source_hash"],
                "allow_code_change": allow_code_change})
        return run.Prepared(resume, stored, {}, {}, smoke, True)
    root = run.new_run_dir(cfg.stage, cfg.tag + (f"-smoke{limit or cfg.n_episodes}" if smoke else ""))
    for name, value in (("identity.json", identity), ("arm_hashes.json", hashes),
                        ("manifest.json", {"stage": cfg.stage, "git": run.git_state(), "env": run.environment(),
                         "started": dt.datetime.now().isoformat(), "smoke": smoke, "contract": CONTRACT})):
        (root / name).write_text(json.dumps(value, indent=2))
    (root / "config.yaml").write_text(raw)
    return run.Prepared(root, identity, {}, {}, smoke, False)


class V7Runner(run.Runner):
    """Reuse the reviewed C/R engine, branching, retry and tick serialization paths."""

    @staticmethod
    def _tick_payload(values: dict[str, Any]) -> dict[str, Any]:
        """Keep the answer-producing query before branches with different lengths are padded."""
        diagnostics = ("kv_span_mass", "kv_bank_mass", "kv_query_pos")
        readout = tuple("r_" + field for field in diagnostics)
        selected = {}
        for name, value in values.items():
            if name in diagnostics:
                continue
            selected[name] = value[:, -1:] if name in readout else value
        return run.Runner._tick_payload(selected)

    def _stage_episodes(self, limit: int | None) -> tuple[list[tasks.Episode], list[tasks.Episode]]:
        full = episodes_for(self.cfg)
        self.v7_episodes = {ep.episode_id: ep for ep in full}
        return [ep.view for ep in full], [ep.view for ep in episodes_for(self.cfg, limit)]

    def arm_identity(self, arm: V7Arm) -> tuple[dict[str, Any], str, str]:
        return (arm.identity("none", "none", self.template_hash),
                arm.config_hash("none", "none", self.template_hash), "none")

    def mask_indices(self, arm: V7Arm) -> None:
        return None

    def _mask_audit(self, arms: list[V7Arm]) -> dict:
        return {}

    def _jsonl(self, name: str) -> list[dict[str, Any]]:
        return _read_jsonl(self.run_dir / name)

    def _load_notes(self) -> None:
        for rec in _check_notes(self.run_dir / "notes.jsonl"):
            self.notes[rec["key"]] = rec["ids"]

    def _context(self, ep: tasks.Episode, role: str) -> tuple:
        source, holder, cf, frame = input_context(self.active_arm, role)
        key = (ep.episode_id, source, holder, cf, frame)
        if key in self._input_cache:
            return self._input_cache[key]
        v7 = self.v7_episodes[ep.episode_id]
        ids = material.private_prefix_ids(self.tok, v7, source, holder, cf, frame)
        context = {"contract": CONTRACT, "episode_id": ep.episode_id, "variant": v7.variant,
                   "role": source, "fact_holder": holder, "counterfactual_fact": cf, "frame": frame,
                   "private_prefix_sha256": ledger.canonical_hash(ids, 64)}
        result = v7, source, holder, cf, frame, ids, context
        self._input_cache[key] = result
        return result

    def _note_key(self, ep: tasks.Episode, role: str, frame: str = "second") -> str:
        return ledger.canonical_hash(self._context(ep, role)[-1], 64)

    def ensure_notes(self, engine, instances: list[tuple]) -> None:
        todo = {}
        for item in instances:
            ctx = self._context(item[0], item[1])
            key = ledger.canonical_hash(ctx[-1], 64)
            if key not in self.notes:
                todo[key] = ctx
        for batch in run._chunks(list(todo.items()), self.cfg.max_rows):
            notes = engine.generate_notes([ctx[-2] for _, ctx in batch], max_new=tasks.NOTE_MAX_TOKENS)
            if len(notes) != len(batch):
                raise ValueError("note generator returned the wrong number of rows")
            for (key, ctx), ids in zip(batch, notes):
                if (len(ids) > tasks.NOTE_MAX_TOKENS or any(type(i) is not int or i < 0 for i in ids)):
                    raise ValueError("invalid generated note IDs")
                record = {"contract": CONTRACT, "key": key, "context": ctx[-1],
                          "episode_id": ctx[0].episode_id, "role": ctx[1], "ids": ids,
                          "ids_sha256": ledger.canonical_hash(ids, 64), "n_tokens": len(ids),
                          "note": self.tok.decode(ids), "opener": tasks.note_opener(ctx[0].view, ctx[1], ctx[4])}
                _append(self.run_dir / "notes.jsonl", record)
                self.notes[key] = list(ids)

    def _prefix_parts(self, ep: tasks.Episode, role: str) -> tuple[list[int], list[material.Span]]:
        v7, source, holder, cf, frame, private, context = self._context(ep, role)
        key = ledger.canonical_hash(context, 64)
        if key in self._prefix_cache:
            ids, spans = self._prefix_cache[key]
            return list(ids), list(spans)
        generated = self.notes[key]
        close = chat.close(self.tok)
        prompt = reflection_ids(self.tok, v7, source, frame)
        opener = chat.encode(self.tok, tasks.note_opener(v7.view, source, frame))
        start, stop = len(private) - len(opener), len(private) + len(generated)
        ids = [*private, *generated, *close, *prompt]
        spans = [*material.declared_spans(self.tok, v7, source, holder, cf, frame),
                 ("note", start, stop), ("closure", stop, stop + len(close)),
                 ("prompt", stop + len(close), len(ids))]
        self._prefix_cache[key] = ids, spans
        return list(ids), list(spans)

    def prefix(self, ep: tasks.Episode, role: str, lang=None, frame: str = "second") -> list[int]:
        if lang is not None:
            raise ValueError("V7 does not register a language arm")
        return self._prefix_parts(ep, role)[0]

    def prefix_spans(self, ep: tasks.Episode, role: str, frame: str, prefix_ids: list[int]) -> list[material.Span]:
        ids, spans = self._prefix_parts(ep, role)
        if ids != prefix_ids:
            raise ValueError("span declaration does not match the actual prefix")
        return spans

    def _pending_questions(self, arm: V7Arm, chunk: list[tasks.Episode], views: list[tasks.Episode],
                           all_rot_ids: set[str], done: set[ledger.TrialKey]) -> list[tuple[int, str, tasks.Question]]:
        return [(i, "A", q) for i, ep in enumerate(chunk)
                for q in material.readout_questions(self.tok, self.v7_episodes[ep.episode_id], "A", qids_for(arm))
                if (ep.episode_id, arm.name, "A", q.qid, q.rotation_id) not in done]

    def _base_record(self, arm: V7Arm, ident: dict, chash: str, mhash: str, ep: tasks.Episode,
                     recipient: str, q: tasks.Question) -> dict[str, Any]:
        record = super()._base_record(arm, ident, chash, mhash, ep, recipient, q)
        v7 = self.v7_episodes[ep.episode_id]
        meta = material.record_metadata(v7, recipient, q, arm.fact_holder, arm.counterfactual_fact)
        meta.update(arm_id=arm.arm_id, copy_A=arm.copy_A, partner_frame=arm.partner_frame,
                    input_sources={r: input_context(arm, r)[0] for r in tasks.ROLES})
        if arm.copy_A:
            meta.update(fact_holder="none", fact_shown=None, use_expected_meaning=None)
        meta["card_sha256"], meta["banks"], meta["note_keys"] = {}, {}, {}
        for role in tasks.ROLES:
            _, source, holder, cf, frame, _, context = self._context(ep, role)
            card = material.private_user_message(v7, source, holder, cf, frame)
            meta["card_sha256"][role] = hashlib.sha256(card.encode()).hexdigest()
            key = ledger.canonical_hash(context, 64)
            meta["note_keys"][role] = key
            # Note-generation failures still need a valid failed record.
            if key in self.notes and key not in self._bank_cache:
                self._bank_cache[key] = bank_metadata(*self._prefix_parts(ep, role))
            meta["banks"][role] = self._bank_cache.get(key)
        record.update(v7=meta, materials=material.CONTRACT, variant=v7.variant, arm_id=arm.arm_id)
        return record

    def _mention_counts(self, ep: tasks.Episode, text: str) -> dict[str, int]:
        if self.cfg.variant != "laptop":
            return super()._mention_counts(ep, text)
        low = text.lower()
        return {f"{kind}_{who}": count for who in ("A", "B", "robin", "spare") for kind, count in (
            ("word", len(re.findall(rf"\b{re.escape(ep.word.of(who))}\b", low))),
            ("rule", low.count(material.LAPTOP_PHRASE[ep.rule.of(who)])))}

    def run_arm_chunk(self, engine, arm: V7Arm, chunk: list[tasks.Episode], all_rot_ids: set[str],
                      done: set[ledger.TrialKey], chunk_index: int,
                      snapshot: run.ReflectionSnapshot | None = None) -> run.ReflectionSnapshot | None:
        if arm not in self.cfg.arm_configs():
            raise ValueError("unregistered V7 arm")
        self.active_arm = arm
        self._input_cache, self._prefix_cache, self._bank_cache = {}, {}, {}
        try:
            return super().run_arm_chunk(engine, arm, chunk, all_rot_ids, done, chunk_index, snapshot)
        finally:
            del self.active_arm
            self._input_cache.clear()
            self._prefix_cache.clear()
            self._bank_cache.clear()

    def _register_snapshot(self, key: str, sha: str, chunk: list[tasks.Episode]) -> None:
        previous = self.snapshot_hashes.get(key)
        if previous is not None and previous != sha:
            raise RuntimeError(f"C48 snapshot differs on retry/resume for {key}")
        if previous is None:
            _append(self.run_dir / "snapshots.jsonl", {"key": key, "sha256": sha,
                    "episodes": [ep.episode_id for ep in chunk]})
            self.snapshot_hashes[key] = sha


def run_completeness(root: Path) -> dict[str, Any]:
    identity = run._read_json(root / "identity.json")
    cfg = V7Config(**identity["stage_config"])
    records = ledger.load_records(root).records
    hashes = {a.name: a.config_hash("none", "none", identity["template_hash"]) for a in cfg.arm_configs()}
    expected = expected_trials(cfg, identity["limit"])
    expected_set = set(expected)
    if any(ledger.trial_key(r) not in expected_set or r.get("config_hash") != hashes.get(r.get("arm"))
           for r in records):
        raise ValueError("records outside the V7 trial/identity contract")
    result = ledger.completeness(records, expected, hashes)
    result.update(smoke=run._read_json(root / "manifest.json")["smoke"], consumable=False)
    return result


def validate_launch(cfg: V7Config, config_path: Path, approved_protocol_sha256: str | None,
                    limit: int | None) -> None:
    if approved_protocol_sha256 != ledger.file_sha256(PROTOCOL):
        raise ValueError("execution requires the SHA256 of the V7 draft approved by the PI")
    if cfg.split == "v7_dev" and not 12 <= len(episodes_for(cfg, limit)) <= 24:
        raise ValueError("the approved engineering smoke must contain 12..24 dev episodes")
    if cfg.split != "v7_formal":
        return
    paths = [PROTOCOL, config_path.resolve(), *sorted((run.REPO_ROOT / "src/mb").glob("*.py"))]
    for path in paths:
        try:
            relative = path.relative_to(run.REPO_ROOT)
            frozen = subprocess.check_output(["git", "show", f"protocol-v7:{relative}"],
                                              cwd=run.REPO_ROOT, stderr=subprocess.DEVNULL)
        except (ValueError, subprocess.CalledProcessError) as exc:
            raise ValueError("formal execution requires the protocol-v7 frozen config, protocol and code") from exc
        if frozen != path.read_bytes():
            raise ValueError(f"formal input differs from protocol-v7: {relative}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--allow-code-change", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-protocol-sha256")
    args = parser.parse_args(argv)
    cfg = V7Config(**yaml.safe_load(args.config.read_text()))
    if not args.execute:
        print(json.dumps({"stage": cfg.stage, "episodes": len(episodes_for(cfg, args.limit)),
                          "arms": [a.arm_id for a in cfg.arm_configs()],
                          "n_expected": len(expected_trials(cfg, args.limit)), "execution": False}, indent=2))
        return 0
    validate_launch(cfg, args.config, args.approved_protocol_sha256, args.limit)
    prep = prepare_run(cfg, args.config, args.limit, args.resume, args.allow_code_change)
    log = run.RunLog(prep.run_dir)
    collector = None
    try:
        collector = V7Runner(cfg, prep.run_dir, args.limit, prep.identity, {}, {}, log)
        collector.register_arms(cfg.arm_configs())
        collector.run_arms(cfg.arm_configs())
        collector.writer.flush()
        comp = run_completeness(prep.run_dir)
        (prep.run_dir / "completeness.json").write_text(json.dumps(comp, indent=2))
        (prep.run_dir / "run_status.json").write_text(json.dumps({"status": comp["status"],
                "updated": dt.datetime.now().isoformat()}, indent=2))
        log(f"V7 raw collection: {comp['n_ok']}/{comp['n_expected']} trials; no analysis dispatched")
        return run.exit_code(comp)
    finally:
        if collector is not None:
            collector.close()
        log.close()


if __name__ == "__main__":
    raise SystemExit(main())
