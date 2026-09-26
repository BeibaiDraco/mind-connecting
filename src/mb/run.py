"""Experiment orchestration: stages, arms, records, manifests (protocol v0.5 §10).

Usage (on the GPU machine)::

    python -m mb.run configs/g1.yaml [--limit N] [--resume RUN_DIR [--allow-code-change]]

A new run creates ``<results>/<YYYYMMDD-HHMMSS>_<stage>_<tag>/`` with the input config,
the resolved run identity (``identity.json``), ``manifest.json`` (both written once, never
modified), immutable record shards ``records/attempt-NNN.jsonl``, tick logs, ``log.txt``
and stage outputs; ``run_status.json`` and ``completeness.json`` are derived status files.
``--resume`` recomputes the identity and refuses, before writing anything, unless it
matches; it then appends a new shard and runs only trials without an ``ok`` record.
Runs with ``--limit`` are smoke runs: their gate/selection outputs are non-consumable
and ``calibration: latest`` never picks them for a non-smoke run.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

from mb import chat, ledger, tasks
from mb.conditions import D_MODEL, MODEL_REVISION, ArmConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
CHAT_BUILD_VERSION = "chatml-v1"  # bump if chat.py token assembly changes
TICK_ARRAYS = (("r_inj_ratio", float("nan")), ("r_energy_ratio", float("nan")), ("r_unmatched", False),
               ("r_donor_tokens", -1))


# ---------------------------------------------------------------------------
# Paths, identity, logging
# ---------------------------------------------------------------------------


def results_dir() -> Path:
    env = os.environ.get("MB_DATA_ROOT")
    if env:
        root = Path(env)
        if not root.is_dir():
            raise SystemExit(f"MB_DATA_ROOT={root} is not a directory (is the SD card mounted?)")
        return root / "results"
    return REPO_ROOT / "results"


def new_run_dir(stage: str, tag: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = results_dir() / f"{stamp}_{stage}_{tag}"
    if path.exists():
        raise SystemExit(f"{path} already exists; refusing to overwrite")
    path.mkdir(parents=True)
    return path


def git_state() -> dict[str, Any]:
    def run(*cmd: str) -> str:
        try:
            return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return "unknown"

    return {"commit": run("git", "rev-parse", "HEAD"), "dirty": bool(run("git", "status", "--porcelain"))}


def source_hash() -> str:
    """Hash of the experiment code itself (src/mb/*.py), independent of git state."""
    h = hashlib.sha256()
    for path in sorted((REPO_ROOT / "src" / "mb").glob("*.py")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()[:16]


def _tokenizer_manifest() -> dict[str, Any]:
    return json.loads((REPO_ROOT / "materials" / "tokenizer_manifest.json").read_text())


def prefix_hash(tok, materials: str = "v1") -> str:
    """Hash of what calibration depends on: chat IDs, tokenizer, the P and C turns and the P/C
    phase lengths. Readout wording is deliberately excluded (calibration never sees R)."""
    h = hashlib.sha256()
    h.update(f"{CHAT_BUILD_VERSION}|{chat.IM_START}|{chat.IM_END}|{chat.ENDOFTEXT}".encode())
    h.update(f"materials={materials}|notes={tasks.NOTE_MAX_TOKENS_BY_MATERIALS[materials]}|"
             f"ticks={tasks.REFLECTION_TICKS}".encode())
    h.update(json.dumps(_tokenizer_manifest(), sort_keys=True).encode())
    ref = tasks.make_episodes(1, "template-ref", seed=0)[0]
    for s in [*(tasks.private_prefix_ids(tok, ref, r, materials) for r in tasks.ROLES), chat.close(tok),
              tasks.reflection_turn_ids(tok, materials)]:
        h.update(json.dumps(list(s)).encode())
    return h.hexdigest()[:16]


def template_hash(tok, materials: str = "v1") -> str:
    """Hash of every token sequence the protocol feeds the model, independent of episode draw.

    Covers the chat special IDs and assembly version, the tokenizer manifest, the P/C/LANG
    turns and every readout suffix of a reference episode (all rotations, both roles), and
    the question suffix of every CAP item.
    """
    h = hashlib.sha256()
    h.update(f"{CHAT_BUILD_VERSION}|{chat.IM_START}|{chat.IM_END}|{chat.ENDOFTEXT}|{chat.LABEL_IDS}".encode())
    h.update(json.dumps(_tokenizer_manifest(), sort_keys=True).encode())
    h.update(f"u_open={tasks.U_OPEN_TOKENS}|{prefix_hash(tok, materials)}".encode())
    ref = tasks.make_episodes(1, "template-ref", seed=0)[0]
    seqs: list[list[int]] = [tasks.private_prefix_ids(tok, ref, r, materials) for r in tasks.ROLES]
    seqs.append(tasks.reflection_turn_ids(tok, materials))
    seqs += [tasks.lang_turn_ids(tok, "Nova", "x", mode) for mode in tasks.LANG_FRAMES]
    seqs += [tasks.private_prefix_ids(tok, ref, r, materials, f) for f in ("third", "third_strict") for r in tasks.ROLES]
    seqs.append(chat.turn(tok, "user", tasks.third_person_reflection_prompt("Nova")))
    for r in tasks.ROLES:
        seqs += [list(q.suffix_ids) for q in tasks.readout_questions(tok, ref, r, rotations=range(tasks.N_ROTATIONS))]
    for item in tasks.cap_bank():
        probe = dataclasses.replace(ref, cap_items=(item.item_id, item.item_id))
        seqs.append(list(tasks.make_question(tok, probe, "A", "CAP0", 0).suffix_ids))
    for s in seqs:
        h.update(json.dumps(s).encode())
    return h.hexdigest()[:16]


def environment() -> dict[str, Any]:
    info: dict[str, Any] = {"python": platform.python_version(), "platform": platform.platform()}
    try:
        import tokenizers
        import torch
        import transformers

        info.update(torch=torch.__version__, transformers=transformers.__version__, tokenizers=tokenizers.__version__,
                    cuda=torch.version.cuda, gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
    except Exception as exc:  # the manifest must never block a run
        info["env_error"] = repr(exc)
    return info


def _jsonable(obj: Any) -> Any:
    """Counters/tuples/int keys -> plain JSON (keys become strings)."""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


def _read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text())


class RunLog:
    def __init__(self, run_dir: Path):
        self._fh = (run_dir / "log.txt").open("a")

    def __call__(self, msg: str) -> None:
        line = f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self._fh.write(line + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class StageConfig:
    stage: str
    tag: str
    split: str
    n_episodes: int
    seed: int = 0
    arms: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    qids: list[str] = dataclasses.field(default_factory=lambda: list(tasks.DEFAULT_QIDS))
    all_rotations_first: int = 0  # first k episodes get all 4 label rotations (diagnostic subset)
    episodes_per_batch: int = 32
    max_rows: int = 256
    calibration: dict[str, str] | str | None = None  # layer -> .pt path, or "latest"
    calibration_layers: list[int] = dataclasses.field(default_factory=list)  # for stage == calibrate
    post: list[str] = dataclasses.field(default_factory=list)  # post-processing steps
    frozen: dict[str, Any] | None = None  # frozen protocol-v1 parameters (formal stages; read by analysis)
    materials: str = "v1"  # task materials version (protocol v2 study E: "balanced")
    params: dict[str, Any] | None = None  # stage-specific post-processing parameters (protocol v2)

    def __post_init__(self) -> None:
        if self.materials not in tasks.MATERIALS:
            raise ValueError(f"unknown materials {self.materials!r}")
        unknown = set(self.qids) - set(tasks.QIDS)
        if unknown:
            raise ValueError(f"unknown qids {sorted(unknown)}")
        stopped = set(self.qids) & set(tasks.STOPPED_QIDS)
        if stopped:
            raise ValueError(f"qids {sorted(stopped)} belong to a stopped endpoint (decision_log 2026-09-24)")
        bad_post = set(self.post) - set(POST)
        if bad_post:
            raise ValueError(f"unknown post steps {sorted(bad_post)}")
        if "sample_size" in self.post and ("select_pilot_b" not in self.post
                                           or self.post.index("select_pilot_b") > self.post.index("sample_size")):
            raise ValueError("sample_size must follow select_pilot_b: parameters are frozen before N is computed")
        self.arm_configs()  # validate early

    @classmethod
    def load(cls, path: Path) -> "StageConfig":
        return cls(**yaml.safe_load(Path(path).read_text()))

    def arm_configs(self) -> list[ArmConfig]:
        arms = []
        for spec in self.arms:
            spec = dict(spec)
            if "recipients" in spec:
                spec["recipients"] = tuple(spec["recipients"])
            arms.append(ArmConfig(**spec))
        names = [a.name for a in arms]
        dup = sorted({n for n in names if names.count(n) > 1})
        if dup:
            raise ValueError(f"duplicate arm names {dup} (arms must differ in their named parameters)")
        return arms

    def resolved(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["arms"] = [dataclasses.asdict(a) for a in self.arm_configs()]
        return d


def stage_episodes(cfg: StageConfig, limit: int | None) -> tuple[list[tasks.Episode], list[tasks.Episode]]:
    """(full stage list, episodes actually run). Donor maps always use the full list."""
    full = tasks.make_episodes(cfg.n_episodes, cfg.split, cfg.seed)
    return full, (full if limit is None else full[: min(limit, cfg.n_episodes)])


def stage_expected(cfg: StageConfig, limit: int | None) -> list[ledger.TrialKey]:
    _, used = stage_episodes(cfg, limit)
    all_rot = {e.episode_id for e in used[: cfg.all_rotations_first]}
    return ledger.expected_trials([ledger.ArmSpec(a.name, a.recipients) for a in cfg.arm_configs()],
                                  [(e.episode_id, e.rotations) for e in used], cfg.qids, all_rot,
                                  n_rotations=tasks.N_ROTATIONS)


def run_completeness(run_dir: Path) -> dict[str, Any]:
    """Recompute completeness from the stored identity and all record shards."""
    identity = _read_json(run_dir / "identity.json")
    cfg = StageConfig(**identity["stage_config"])
    arm_hash_path = run_dir / "arm_hashes.json"
    arm_hash = _read_json(arm_hash_path) if arm_hash_path.exists() else {}
    report = ledger.load_records(run_dir)
    comp = ledger.completeness(report.records, stage_expected(cfg, identity["limit"]), arm_hash)
    comp["truncated_tails"] = report.truncated_tails
    return comp


# ---------------------------------------------------------------------------
# Run status and calibration files
# ---------------------------------------------------------------------------


def run_finished(run_dir: Path) -> bool:
    try:
        return _read_json(run_dir / "run_status.json").get("status") == "complete"
    except Exception:
        return False


def run_consumable(run_dir: Path) -> bool:
    """Finished and not a smoke run: the only runs later stages may consume."""
    try:
        smoke = _read_json(run_dir / "manifest.json").get("smoke", True)
    except Exception:
        return False
    return not smoke and run_finished(run_dir)


def resolve_calibration(spec: dict[str, str] | str | None, allow_smoke: bool = False) -> dict[int, str]:
    """``latest`` -> newest finished non-smoke calibrate run (smoke runs may fall back to a
    finished smoke calibration); a dict is taken as given (validated on load)."""
    if spec is None:
        return {}
    if spec == "latest":
        runs = sorted(p for p in results_dir().glob("*_calibrate_*") if (p / "calibration.json").exists())
        good = [p for p in runs if run_consumable(p)]
        if not good and allow_smoke:
            good = [p for p in runs if run_finished(p)]
        if not good:
            raise SystemExit("calibration: latest, but no finished non-smoke calibrate run was found")
        return {int(k): v for k, v in _read_json(good[-1] / "calibration.json").items()}
    return {int(k): v for k, v in dict(spec).items()}


def load_calibration(path: str, layer: int, current: dict[str, Any], allow_smoke: bool):
    """Load a calibration file and validate it against the running protocol identity."""
    import torch

    from mb.bridge import LayerCalibration

    blob = torch.load(path, map_location="cpu")
    cal = LayerCalibration.from_state_dict(blob)
    meta = blob.get("meta", {})
    problems = []
    if cal.layer != layer:
        problems.append(f"file is for layer {cal.layer}, configured under layer {layer}")
    for name, t in [("mu", cal.mu), ("sd", cal.sd), *[(k, v) for k, v in cal.static.items()]]:
        if tuple(t.shape) != (D_MODEL,) or not bool(torch.isfinite(t).all()):
            problems.append(f"{name}: shape {tuple(t.shape)} or non-finite values")
    for key in ("model_revision", "prefix_hash"):
        if meta.get(key) != current.get(key):
            problems.append(f"{key} {meta.get(key)} != current {current.get(key)}")
    if meta.get("smoke", True) and not allow_smoke:
        problems.append("smoke calibration cannot feed a non-smoke run")
    if problems:
        raise SystemExit(f"calibration {path} rejected: " + "; ".join(problems))
    return cal, meta


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _chunks(seq: list, size: int) -> Iterable[list]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


class Runner:
    """Model, caches and bookkeeping for one stage run.

    ``model``/``tok``/``engine_cls`` can be injected (tests use a fake engine on CPU).
    """

    def __init__(self, cfg: StageConfig, run_dir: Path, limit: int | None, identity: dict[str, Any],
                 cal_map: dict[int, Any], cal_meta: dict[int, dict[str, Any]], log: RunLog, *,
                 model=None, tok=None, engine_cls=None):
        import torch

        self.torch = torch
        self.cfg = cfg
        self.run_dir = run_dir
        self.log = log
        self.identity = identity
        self.template_hash = identity["template_hash"]
        self.tok = tok if tok is not None else chat.load_tokenizer()
        if model is None:
            from mb.runtime import load_model

            model = load_model()
        self.model = model
        if engine_cls is None:
            from mb.runtime import Engine

            engine_cls = Engine
        self.engine_cls = engine_cls
        self.d = int(model.config.hidden_size)
        self.cal = cal_map
        self.cal_meta = cal_meta
        self.all_episodes, self.episodes = stage_episodes(cfg, limit)
        self.by_id = {e.episode_id: e for e in self.all_episodes}
        self.mm_donor: dict[str, str] = {}
        self.notes: dict[str, list[int]] = {}
        self.c0_reflection: dict[str, list[int]] = {}
        prior = ledger.load_records(run_dir)
        if prior.truncated_tails:
            log(f"ignoring truncated final line in {prior.truncated_tails} (left untouched)")
        self.prior_records = prior.records
        self._load_notes()
        self._load_lang()
        self.writer = ledger.ShardWriter(run_dir)
        (run_dir / "ticks").mkdir(exist_ok=True)
        self.ticks_summary = (run_dir / "ticks.jsonl").open("a")
        self.notes_log = (run_dir / "notes.jsonl").open("a")
        self.lang_log = (run_dir / "lang.jsonl").open("a")
        self.arm_hash: dict[str, str] = {}
        self.new_records: list[dict[str, Any]] = []
        self.pass_index = 0

    # -- identity per arm ---------------------------------------------------------------

    def mask_indices(self, arm: ArmConfig):
        from mb.bridge import nested_mask_indices

        if arm.condition != "MASK":
            return None
        return nested_mask_indices(self.d, arm.mask_seed, (arm.k,))[arm.k]

    def arm_identity(self, arm: ArmConfig) -> tuple[dict[str, Any], str, str]:
        from mb.bridge import mask_hash

        cal = self.cal.get(arm.layer)
        cal_hash = cal.hash() if (cal is not None and arm.needs_calibration) else "none"
        mhash = mask_hash(self.mask_indices(arm))
        return (arm.identity(cal_hash, mhash, self.template_hash),
                arm.config_hash(cal_hash, mhash, self.template_hash), mhash)

    def register_arms(self, arms: list[ArmConfig]) -> None:
        if any(a.condition == "MISMATCH" for a in arms):
            if len(self.all_episodes) < 2:
                raise SystemExit("MISMATCH needs at least two episodes in the full stage list")
            self.mm_donor = ledger.mismatch_donor_map([e.episode_id for e in self.all_episodes])
        for arm in arms:
            _, chash, _ = self.arm_identity(arm)
            self.arm_hash[arm.name] = chash
        bad = ledger.conflicting_hashes(self.prior_records, self.arm_hash)
        if bad:
            raise SystemExit(f"resume refused: stored records carry other config hashes {bad}")
        self._write_once("arm_hashes.json", self.arm_hash)
        self._write_once("mask_audit.json", self._mask_audit(arms))
        if self.mm_donor:
            self._write_once("mismatch_donors.json", self.mm_donor)

    def _write_once(self, name: str, payload: Any) -> None:
        """Write a run-level file once; on resume its content must be identical."""
        path = self.run_dir / name
        payload = json.loads(json.dumps(payload))
        if path.exists():
            if _read_json(path) != payload:
                raise SystemExit(f"resume refused: {name} differs from the stored one")
        else:
            path.write_text(json.dumps(payload, indent=2))

    def _mask_audit(self, arms: list[ArmConfig]) -> dict[str, Any]:
        from mb.bridge import mask_hash

        audit = {}
        for arm in arms:
            idx = self.mask_indices(arm)
            if idx is None:
                continue
            meta = self.cal_meta.get(arm.layer, {})
            chosen = set(idx.tolist())
            audit[arm.name] = {
                "seed": arm.mask_seed, "k": arm.k, "hash": mask_hash(idx), "indices": sorted(chosen),
                "high_abs_mu_dims_in_mask": sorted(chosen & set(meta.get("high_abs_mu_dims", []))),
                "high_sd_dims_in_mask": sorted(chosen & set(meta.get("high_sd_dims", []))),
            }
        return audit

    # -- caches (restored on resume so shared inputs are never regenerated) -------------

    def _note_key(self, ep: tasks.Episode, role: str, frame: str = "second") -> str:
        return tasks.note_key(ep, role, self.cfg.materials, frame)

    def _jsonl(self, name: str) -> list[dict[str, Any]]:
        path = self.run_dir / name
        out = []
        if path.exists():
            for line in path.read_text().splitlines():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # a truncated tail from a crash; that entry is regenerated
        return out

    def _load_notes(self) -> None:
        for rec in self._jsonl("notes.jsonl"):
            self.notes.setdefault(rec["key"], rec["ids"])

    def _load_lang(self) -> None:
        for rec in self._jsonl("lang.jsonl"):
            self.c0_reflection.setdefault(rec["episode_id"], rec["ids"])

    def ensure_notes(self, engine, instances: list[tuple]) -> None:
        """instances: (episode, role) or (episode, role, frame)."""
        items = [(x[0], x[1], x[2] if len(x) > 2 else "second") for x in instances]
        todo = {self._note_key(ep, r, f): (ep, r, f) for ep, r, f in items if self._note_key(ep, r, f) not in self.notes}
        for batch in _chunks(list(todo.values()), self.cfg.max_rows):
            notes = engine.generate_notes([tasks.private_prefix_ids(self.tok, ep, r, self.cfg.materials, f)
                                           for ep, r, f in batch],
                                          max_new=tasks.NOTE_MAX_TOKENS_BY_MATERIALS[self.cfg.materials])
            for (ep, r, f), ids in zip(batch, notes):
                key = self._note_key(ep, r, f)
                self.notes[key] = ids
                rec = {"key": key, "episode_id": ep.episode_id, "role": r, "ids": ids, "note": self.tok.decode(ids),
                       "n_tokens": len(ids)}
                opener = tasks.note_opener(ep, r, f)
                if opener:  # ids hold only the continuation; the opener is part of the prefix
                    rec["opener"] = opener
                self.notes_log.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.notes_log.flush()

    def prefix(self, ep: tasks.Episode, role: str, lang: tuple[str, str] | None = None,
               frame: str = "second") -> list[int]:
        ids = [*tasks.private_prefix_ids(self.tok, ep, role, self.cfg.materials, frame),
               *self.notes[self._note_key(ep, role, frame)], *chat.close(self.tok)]
        if lang is not None:
            text, mode = lang
            ids += tasks.lang_turn_ids(self.tok, ep.codename[tasks.other(role)], text, mode)
        if tasks.is_third(frame):
            return ids + [*chat.turn(self.tok, "user", tasks.third_person_reflection_prompt(ep.codename[role])),
                          *chat.header(self.tok)]
        return ids + tasks.reflection_turn_ids(self.tok, self.cfg.materials)

    def ensure_c0_reflections(self, engine, chunk: list[tasks.Episode]) -> None:
        from mb.runtime import make_plan

        todo = [ep for ep in chunk if ep.episode_id not in self.c0_reflection]
        if not todo:
            return
        self.ensure_notes(engine, [(ep, r) for ep in todo for r in tasks.ROLES])
        state = engine.prefill([self.prefix(ep, r) for ep in todo for r in tasks.ROLES])
        plan = make_plan(ArmConfig("C0"), ["A", "B"] * len(todo), [None] * (2 * len(todo)), engine.cal,
                         engine.device, d=engine.d)
        engine.run_reflection(state, plan)
        consumed = state.consumed_matrix().cpu()
        for i, ep in enumerate(todo):
            ids = consumed[2 * i + 1].tolist()  # B's C1..C48, never the pending C49
            self.c0_reflection[ep.episode_id] = ids
            self.lang_log.write(json.dumps({"episode_id": ep.episode_id, "source": "C0 B reflection C1..C48",
                                            "ids": ids, "sha": ledger.canonical_hash(ids), "n_tokens": len(ids),
                                            "text": self.tok.decode(ids)}, ensure_ascii=False) + "\n")
        self.lang_log.flush()

    # -- records -------------------------------------------------------------------------

    def _base_record(self, arm: ArmConfig, ident: dict[str, Any], chash: str, mhash: str, ep: tasks.Episode,
                     recipient: str, q: tasks.Question) -> dict[str, Any]:
        return {
            "episode_id": ep.episode_id, "split": ep.split, "arm": arm.name, "recipient": recipient,
            "qid": q.qid, "construct": q.construct, "rotation_id": q.rotation_id, "n_ticks": q.n_ticks,
            "options": list(q.options), "label_meaning": list(q.label_meaning),
            "cap_item_id": q.cap_item_id, "text_hash": q.text_hash,
            "condition": arm.condition, "readout_mode": arm.readout_mode, "layer": arm.layer,
            "gain": arm.gain, "message_form": arm.form, "tau": arm.tau, "k": arm.k,
            "energy_mode": arm.energy_mode, "write_operator": arm.write_operator,
            "interface": arm.interface, "kv_scope": arm.kv_scope, "kv_w_live": arm.kv_w_live,
            "materials": self.cfg.materials,
            "calibration_hash": ident["calibration_hash"], "mask_hash": mhash,
            "template_hash": self.template_hash, "model_revision": MODEL_REVISION, "config_hash": chash,
            "attempt": self.writer.path.stem, "pass": self.pass_index,
        }

    def _emit(self, rec: dict[str, Any]) -> None:
        self.writer.write(rec)
        self.new_records.append(rec)

    def _tick_path(self, kind: str, arm: ArmConfig, chash: str, chunk_index: int) -> Path:
        path = (self.run_dir / "ticks" /
                f"{kind}__{_safe(arm.name)}__{chash}__chunk{chunk_index:03d}__{self.writer.path.stem}"
                f"__p{self.pass_index}.npz")
        if path.exists():
            raise FileExistsError(path)
        return path

    # -- one arm on one chunk ------------------------------------------------------------

    def _pending_questions(self, arm: ArmConfig, chunk: list[tasks.Episode], views: list[tasks.Episode],
                           all_rot_ids: set[str], done: set[ledger.TrialKey]
                           ) -> list[tuple[int, str, tasks.Question]]:
        specs = []
        for p, (ep, view) in enumerate(zip(chunk, views)):
            rots = range(tasks.N_ROTATIONS) if ep.episode_id in all_rot_ids else ep.rotations
            for recipient in arm.recipients:
                # A's label meanings follow the donor actually connected; its tokens do not change.
                q_ep = view if recipient == "A" else ep
                for q in tasks.readout_questions(self.tok, q_ep, recipient, rotations=rots, qids=self.cfg.qids):
                    if (ep.episode_id, arm.name, recipient, q.qid, q.rotation_id) not in done:
                        specs.append((p, recipient, q))
        return specs

    def _donors(self, arm: ArmConfig, chunk: list[tasks.Episode]) -> list[tasks.Episode]:
        donors = []
        for ep in chunk:
            if arm.donor_variant == "CF":
                donors.append(tasks.make_donor_variant(ep, "CF").donor_episode)
            elif arm.donor_variant == "MISMATCH":
                src = self.by_id[self.mm_donor[ep.episode_id]]
                donors.append(tasks.make_donor_variant(ep, "MISMATCH", src).donor_episode)
            else:
                donors.append(ep)
        return donors

    def run_arm_chunk(self, engine, arm: ArmConfig, chunk: list[tasks.Episode], all_rot_ids: set[str],
                      done: set[ledger.TrialKey], chunk_index: int) -> None:
        import numpy as np

        from mb.runtime import U_OPEN_TOKENS, make_plan

        torch = self.torch
        ident, chash, mhash = self.arm_identity(arm)
        donors = self._donors(arm, chunk)
        specs = self._pending_questions(arm, chunk, donors, all_rot_ids, done)
        if not specs:
            return
        lang_meta: list[dict[str, Any]] = [{} for _ in chunk]
        try:
            self.ensure_notes(engine, [(ep, "A") for ep in chunk] + [(d, "B", arm.partner_frame) for d in donors])
            if arm.lang:
                self.ensure_c0_reflections(engine, chunk)
            prefixes = []
            for p, (ep, donor) in enumerate(zip(chunk, donors)):
                lang = None
                if arm.lang:
                    ids = self.c0_reflection[ep.episode_id]
                    lang = (self.tok.decode(ids), arm.lang)
                    lang_meta[p] = {"lang_source_sha": ledger.canonical_hash(ids), "lang_n_tokens": len(ids)}
                prefixes += [self.prefix(ep, "A", lang), self.prefix(donor, "B", frame=arm.partner_frame)]
            state = engine.prefill(prefixes)
            idx = self.mask_indices(arm)
            if idx is not None:
                idx = idx.to(engine.device)
            static_rules = [d.rule.B for d in donors]
            plan = make_plan(arm, ["A", "B"] * len(chunk), [x for r in static_rules for x in (r, None)],
                             engine.cal, engine.device, idx, engine.d)
            ticklog = engine.run_reflection(state, plan, write=arm.readout_mode != "RO")
        except Exception as exc:
            reason = f"prefix/reflection: {exc!r}"
            self.log(f"[{arm.name}] chunk {chunk_index} failed before readouts: {reason}")
            for p, recipient, q in specs:
                rec = self._base_record(arm, ident, chash, mhash, chunk[p], recipient, q)
                rec.update(status="failed", failure_reason=reason)
                self._emit(rec)
            self.writer.flush()
            return

        c_path = self._tick_path("C", arm, chash, chunk_index)
        np.savez_compressed(c_path, episode_ids=np.array([e.episode_id for e in chunk]),
                            **{k: v.cpu().numpy() for k, v in ticklog.items()})
        consumed = state.consumed_matrix().cpu()
        for i, (ep, view) in enumerate(zip(chunk, donors)):
            text_a, text_b = self.tok.decode(consumed[2 * i].tolist()), self.tok.decode(consumed[2 * i + 1].tolist())
            self.ticks_summary.write(json.dumps({
                "episode_id": ep.episode_id, "arm": arm.name, "config_hash": chash, "phase": "C",
                "tick_file": c_path.name, "row_A": 2 * i, "row_B": 2 * i + 1,
                "inj_host_ratio_A": float(ticklog["inj_ratio"][2 * i].mean()),
                "inj_host_ratio_B": float(ticklog["inj_ratio"][2 * i + 1].mean()),
                "cos_AB": float(ticklog["cos_pair"][i].mean()) if "cos_pair" in ticklog else None,
                "unmatched_ticks_A": int(ticklog["unmatched"][2 * i].sum()),
                "kv_mass_A": (float(ticklog["kv_mass"][2 * i].nanmean())
                              if "kv_mass" in ticklog and bool(ticklog["kv_mass"][2 * i].isfinite().any()) else None),
                "reflection_A": text_a, "reflection_B": text_b,
                "mentions_A": tasks.mention_counts(view, text_a), "mentions_B": tasks.mention_counts(view, text_b),
            }, ensure_ascii=False) + "\n")
        self.ticks_summary.flush()

        groups: dict[tuple, list[tuple[int, str, tasks.Question]]] = defaultdict(list)
        for p, recipient, q in specs:  # one question type (and CAP item) per batch; equal lengths
            groups[(q.qid, q.cap_item_id, q.n_ticks, q.generative)].append((p, recipient, q))
        full = arm.readout_mode in ("FULL", "RO") and arm.direction != "none"
        per_chunk = max(1, self.cfg.max_rows // (2 if full else 1))
        rticks: list[tuple[list[str], dict[str, Any]]] = []
        for (qid, cap_id, length, generative), group in sorted(groups.items(), key=lambda kv: str(kv[0])):
            for part in _chunks(group, per_chunk):
                suffixes = torch.tensor([list(q.suffix_ids) for _, _, q in part], dtype=torch.long)
                rules = [static_rules[p] for p, _, _ in part]
                try:
                    out = engine.run_readout(state, [(p, r) for p, r, _ in part], suffixes, arm, rules,
                                             generate=U_OPEN_TOKENS if generative else 0, mask_idx=idx)
                    error = None
                except Exception as exc:  # failures stay as records, never dropped silently
                    out, error = None, f"readout: {exc!r}"
                    self.log(f"[{arm.name}] chunk {chunk_index} {qid}: {error}")
                if out is not None and "r_inj_ratio" in out:
                    keys = [json.dumps([chunk[p].episode_id, r, q.qid, q.rotation_id]) for p, r, q in part]
                    rticks.append((keys, {k: out[k].cpu().numpy() for k, _ in TICK_ARRAYS}))
                for j, (p, recipient, q) in enumerate(part):
                    ep = chunk[p]
                    rec = self._base_record(arm, ident, chash, mhash, ep, recipient, q)
                    rec.update(lang_meta[p])
                    if arm.donor_variant:
                        v = donors[p]
                        rec.update(donor_rule=v.rule.B, donor_word=v.word.B, cf_r0_rule=ep.rule.B,
                                   cf_r1_rule=ep.rule.spare, cf_r0_word=ep.word.B, cf_r1_word=ep.word.spare)
                        if arm.donor_variant == "MISMATCH":
                            rec["mismatch_scenario_from"] = self.mm_donor[ep.episode_id]
                    if out is None:
                        rec.update(status="failed", failure_reason=error)
                        self._emit(rec)
                        continue
                    vals = [out["label_logits"][j], out["label_logprobs"][j], out["label_mass"][j:j + 1]]
                    finite = all(bool(torch.isfinite(v).all()) for v in vals)
                    rec.update(label_logits=out["label_logits"][j].tolist(),
                               label_logprobs=out["label_logprobs"][j].tolist(),
                               label_mass=float(out["label_mass"][j]))
                    if "r_inj_ratio_mean" in out:
                        rec.update(r_inj_ratio_mean=float(out["r_inj_ratio_mean"][j]),
                                   r_unmatched_ticks=int(out["r_unmatched_ticks"][j]))
                    if "r_kv_mass_mean" in out:
                        rec["r_kv_mass_mean"] = float(out["r_kv_mass_mean"][j])
                    if "g_unmatched_ticks" in out:
                        rec["g_unmatched_ticks"] = int(out["g_unmatched_ticks"][j])
                    if generative:
                        ids = out["generated"][j].tolist()
                        rec.update(generated_ids=ids, generated_text=self.tok.decode(ids))
                        finite = finite and len(ids) == U_OPEN_TOKENS
                    rec.update(status="ok" if finite else "failed",
                               failure_reason=None if finite else "non-finite or malformed readout output")
                    self._emit(rec)
                self.writer.flush()
        if rticks:
            self._save_rticks(self._tick_path("R", arm, chash, chunk_index), rticks)
        del state
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @staticmethod
    def _save_rticks(path: Path, parts: list[tuple[list[str], dict[str, Any]]]) -> None:
        import numpy as np

        width = max(a["r_inj_ratio"].shape[1] for _, a in parts)
        arrays = {}
        for name, fill in TICK_ARRAYS:
            padded = []
            for _, a in parts:
                x = a[name]
                buf = np.full((x.shape[0], width), fill, dtype=x.dtype)
                buf[:, :x.shape[1]] = x
                padded.append(buf)
            arrays[name] = np.concatenate(padded)
        np.savez_compressed(path, trial_keys=np.array([k for ks, _ in parts for k in ks]),
                            lengths=np.concatenate([np.full(len(ks), a["r_inj_ratio"].shape[1]) for ks, a in parts]),
                            **arrays)

    def run_arms(self, arms: list[ArmConfig], passes: int = 2) -> None:
        """Run all pending trials; later passes retry trials that failed (same configuration)."""
        all_rot_ids = {ep.episode_id for ep in self.episodes[: self.cfg.all_rotations_first]}
        by_layer: dict[int, list[ArmConfig]] = defaultdict(list)
        for arm in arms:
            by_layer[arm.layer].append(arm)
        for attempt in range(passes):
            self.pass_index = attempt
            done = ledger.done_keys(self.prior_records + self.new_records, self.arm_hash)
            n_new_before = len(self.new_records)
            for layer, layer_arms in by_layer.items():
                needs_cal = any(a.needs_calibration for a in layer_arms)
                if needs_cal and layer not in self.cal:
                    raise SystemExit(f"arms at layer {layer} need a calibration file")
                engine = self.engine_cls(self.model, self.tok, layer, self.cal.get(layer) if needs_cal else None)
                try:
                    for ci, chunk in enumerate(_chunks(self.episodes, self.cfg.episodes_per_batch)):
                        for arm in layer_arms:
                            t0 = time.time()
                            self.run_arm_chunk(engine, arm, chunk, all_rot_ids, done, ci)
                            self.log(f"pass {attempt} [{arm.name}] chunk {ci}: {len(chunk)} episodes "
                                     f"in {time.time() - t0:.1f}s")
                finally:
                    engine.close()
            failed = [r for r in self.new_records[n_new_before:] if r.get("status") != "ok"]
            if not failed:
                break
            if attempt < passes - 1:
                self.log(f"retrying {len(failed)} failed trials once (same configuration)")
            else:
                self.log(f"{len(failed)} trials still failed after {passes} passes; left missing, not imputed")

    def close(self) -> None:
        self.writer.close()
        for fh in (self.ticks_summary, self.notes_log, self.lang_log):
            fh.close()


# ---------------------------------------------------------------------------
# Calibration stage
# ---------------------------------------------------------------------------


def run_calibration(runner: Runner, layers: list[int], smoke: bool) -> dict[int, str]:
    """C0 on calibration episodes; raw outputs of non-first C tokens per layer -> mu/sd/sigma, STATIC."""
    import torch

    from mb.bridge import BridgeHook, calibration_from_records, ema_update, message, static_vectors
    from mb.runtime import Engine, make_plan

    if not layers:
        raise SystemExit("calibrate stage needs calibration_layers")
    for l in layers:
        if (runner.run_dir / f"calibration_L{l}.pt").exists():
            raise SystemExit(f"calibration_L{l}.pt exists in {runner.run_dir}; outputs are never overwritten")
    engine = Engine(runner.model, runner.tok, layers[0], None)
    hooks = {l: BridgeHook(runner.model.model.layers[l - 1], l, record_all=True) for l in layers}
    for h in hooks.values():
        h.mode = "record"  # passive observers: any length, never write
    z_seqs: dict[int, list[torch.Tensor]] = {l: [] for l in layers}
    rms_seqs: dict[int, list[torch.Tensor]] = {l: [] for l in layers}
    rules: list[str] = []
    try:
        for chunk in _chunks(runner.episodes, runner.cfg.episodes_per_batch):
            runner.ensure_notes(engine, [(ep, r) for ep in chunk for r in tasks.ROLES])
            for h in hooks.values():
                h.records.clear()  # drop everything recorded while generating notes
            state = engine.prefill([runner.prefix(ep, r) for ep in chunk for r in tasks.ROLES])
            plan = make_plan(ArmConfig("C0"), ["A", "B"] * len(chunk), [None] * (2 * len(chunk)), None,
                             engine.device, d=engine.d)
            engine.run_reflection(state, plan)
            for l, h in hooks.items():
                if len(h.records) != 1 + state.tick:
                    raise RuntimeError(f"layer {l}: expected {1 + state.tick} records, got {len(h.records)}")
                z_seqs[l].append(torch.stack([z for _, z in h.records], dim=1).cpu())  # seed + T ticks
                rms_seqs[l].append(torch.stack([r for r, _ in h.records], dim=1).cpu())
            rules += [ep.own_rule(r) for ep in chunk for r in tasks.ROLES]
            runner.log(f"calibration chunk: {len(chunk)} episodes")
    finally:
        for h in hooks.values():
            h.remove()
        engine.close()
    paths: dict[int, str] = {}
    for l in layers:
        z = torch.cat(z_seqs[l], dim=0)  # [rows, 1 + T, d]
        r = torch.cat(rms_seqs[l], dim=0)
        body_z, body_rms = z[:, 2:, :], r[:, 2:]  # drop the prefill seed and the first C token
        cal = calibration_from_records(l, body_z.reshape(-1, body_z.shape[-1]), body_rms.reshape(-1))
        statics: dict[str, torch.Tensor] = {}
        unusable: list[str] = []
        for form, tau in (("raw", 1), ("ema", 8)):
            e = z[:, 0, :].clone()
            msgs = []
            for t in range(1, z.shape[1]):
                e = ema_update(e, z[:, t, :], tau)
                if t >= 2:
                    msgs.append(message(e, cal).float())  # the same BF16 messages the runtime sends
            m = torch.stack(msgs, dim=1)
            flat = m.reshape(-1, m.shape[-1])
            flat_rules = [rule for rule in rules for _ in range(m.shape[1])]
            vec, bad = static_vectors(flat, flat_rules, cal.sigma_in, form)
            statics.update(vec)
            unusable += bad
        cal.static, cal.static_unusable = statics, tuple(unusable)
        blob = cal.state_dict()
        blob["meta"] = {"model_revision": MODEL_REVISION, "prefix_hash": runner.identity["prefix_hash"],
                        "template_hash": runner.template_hash,
                        "split": runner.cfg.split, "n_episodes": len(runner.episodes), "smoke": smoke,
                        "run_dir": str(runner.run_dir),
                        "high_abs_mu_dims": torch.topk(cal.mu.abs(), 16).indices.tolist(),
                        "high_sd_dims": torch.topk(cal.sd, 16).indices.tolist()}
        path = runner.run_dir / f"calibration_L{l}.pt"
        with path.open("xb") as fh:  # never overwrite
            torch.save(blob, fh)
        paths[l] = str(path)
        runner.log(f"layer {l}: sigma_in={cal.sigma_in:.3f} hash={cal.hash()} unusable={unusable}")
    (runner.run_dir / "calibration.json").write_text(json.dumps(paths, indent=2))
    return paths


# ---------------------------------------------------------------------------
# Post-processing: reads records only; incomplete or smoke data never yields a decision
# ---------------------------------------------------------------------------


def _valid_ok(run_dir: Path) -> list[dict[str, Any]]:
    arm_hash = _read_json(run_dir / "arm_hashes.json")
    records = ledger.load_records(run_dir).records
    return [r for r in records if r.get("status") == "ok" and r.get("config_hash") == arm_hash.get(r["arm"])]


G1_CORRECT = {"START": "own", "NOW": "own", "BEH": "own", "WORD": "own",
              "START_R": "robin", "NOW_R": "robin", "BEH_R": "robin", "WORD_R": "robin",
              "START_N": "own", "CAP0": "correct", "CAP1": "correct"}
# BEH/BEH-R left the gate when their endpoint was stopped under the G1 rule (decision_log 2026-09-24).
G1_GATE = ("START", "NOW", "WORD", "START_R", "NOW_R", "WORD_R")
G1_MIN_ACC = 0.90
G1_MIN_MASS = 0.90


def rehearsal_rates(run_dir: Path) -> dict[str, dict[str, float]]:
    """How often notes and C0 reflections name each instance's own vs Robin's rule phrase and code word
    (protocol v2 study E manipulation check; descriptive for v1 materials)."""
    identity = _read_json(run_dir / "identity.json")
    cfg = StageConfig(**identity["stage_config"])
    full, _ = stage_episodes(cfg, identity["limit"])
    eps = {e.episode_id: e for e in full}
    hits: dict[str, list[float]] = defaultdict(list)

    def add(kind: str, ep: tasks.Episode, role: str, text: str) -> None:
        m = tasks.mention_counts(ep, text)
        hits[f"{kind}: own word"].append(float(m[f"word_{role}"] > 0))
        hits[f"{kind}: Robin word"].append(float(m["word_robin"] > 0))
        hits[f"{kind}: own rule phrase"].append(float(m[f"rule_{role}"] > 0))
        hits[f"{kind}: Robin rule phrase"].append(float(m["rule_robin"] > 0))

    notes_path, ticks_path = run_dir / "notes.jsonl", run_dir / "ticks.jsonl"
    if notes_path.exists():
        for line in notes_path.read_text().splitlines():
            rec = json.loads(line)
            if rec.get("episode_id") in eps:
                add("note", eps[rec["episode_id"]], rec["role"], rec.get("note", ""))
    if ticks_path.exists():
        for line in ticks_path.read_text().splitlines():
            rec = json.loads(line)
            if rec.get("episode_id") in eps and str(rec.get("arm", "")).startswith("C0"):
                for role in tasks.ROLES:
                    add("reflection", eps[rec["episode_id"]], role, rec.get(f"reflection_{role}", ""))
    return {k: sum(v) / len(v) for k, v in sorted(hits.items()) if v}


def post_g1(run_dir: Path) -> dict[str, Any]:
    """G1 (protocol §10): argmax accuracy of self/Robin items and label mass, per recipient."""
    from mb import readouts

    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    ok = [r for r in _valid_ok(run_dir) if r["qid"] != "U_OPEN"]
    acc: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    mass: dict[str, list[float]] = defaultdict(list)
    for r in ok:
        if r["qid"] in G1_CORRECT:
            hit = float(readouts.argmax_meaning(r) == G1_CORRECT[r["qid"]])
            acc[r["qid"]]["all"].append(hit)
            acc[r["qid"]][r["recipient"]].append(hit)
        mass[r["qid"]].append(float(r["label_mass"]))
    all_mass = [m for v in mass.values() for m in v]
    summary: dict[str, Any] = {
        "completeness": comp, "smoke": manifest.get("smoke", True),
        "accuracy": {q: {k: {"acc": sum(v) / len(v), "n": len(v)} for k, v in sorted(d.items())}
                     for q, d in sorted(acc.items())},
        "label_mass_mean": sum(all_mass) / len(all_mass) if all_mass else None,
        "label_mass_by_qid": {q: sum(v) / len(v) for q, v in sorted(mass.items())},
    }
    if comp["status"] != "complete":
        summary["G1"] = "incomplete"
    else:
        failing = [q for q in G1_GATE if summary["accuracy"].get(q, {}).get("all", {}).get("acc", 0.0) < G1_MIN_ACC]
        mass_ok = (summary["label_mass_mean"] or 0.0) >= G1_MIN_MASS
        summary["G1"] = "pass" if not failing and mass_ok else "fail"
        summary["failing_items"] = failing
        summary["mass_ok"] = mass_ok
    summary["rehearsal"] = rehearsal_rates(run_dir)
    summary["consumable"] = not summary["smoke"] and comp["status"] == "complete"
    (run_dir / "g1_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def post_select_pilot_a(run_dir: Path) -> dict[str, Any]:
    from mb import analyze, readouts

    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True)}
    if comp["status"] != "complete":
        out["selection"] = "incomplete"
    else:
        scores = readouts.score_records(_valid_ok(run_dir), readouts.ScoreOptions(rotations=None))
        meta = (scores[scores["condition"] == "ONE"][["arm", "message_form", "layer", "gain", "condition"]]
                .drop_duplicates().rename(columns={"message_form": "form"}))
        c0 = scores[scores["condition"] == "C0"]["arm"].unique()
        if len(c0) != 1:
            raise SystemExit("pilot A needs exactly one C0 arm")
        summary = analyze.selector_summary(scores, c0[0], meta)
        summary.to_csv(run_dir / "pilot_a_summary.csv", index=False)
        out["selection"] = dataclasses.asdict(analyze.select_pilot_a(summary))
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "pilot_a_selection.json").write_text(json.dumps(out, indent=2))
    return out


def post_select_pilot_b(run_dir: Path) -> dict[str, Any]:
    """Pilot B selector (protocol §10): g*, main gains and matched STATIC from ACC/CAP/format only."""
    from mb import analyze, readouts

    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True)}
    if comp["status"] != "complete":
        out["selection"] = "incomplete"
    else:
        scores = readouts.score_records(_valid_ok(run_dir), readouts.ScoreOptions(rotations=None))
        cand = scores[scores["condition"].isin(["ONE", "TWO", "STATIC"])]
        meta = (cand[["arm", "message_form", "layer", "gain", "condition"]].drop_duplicates()
                .rename(columns={"message_form": "form"}))
        if len(meta[["form", "layer"]].drop_duplicates()) != 1:
            raise SystemExit("pilot B runs at a single selected form and layer")
        c0 = scores[scores["condition"] == "C0"]["arm"].unique()
        if len(c0) != 1:
            raise SystemExit("pilot B needs exactly one C0 arm")
        summary = analyze.selector_summary(scores, c0[0], meta)
        summary.to_csv(run_dir / "pilot_b_summary.csv", index=False)
        out["selection"] = dataclasses.asdict(analyze.select_pilot_b(summary))
        out["form"], out["layer"] = str(meta["form"].iloc[0]), int(meta["layer"].iloc[0])
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "pilot_b_selection.json").write_text(json.dumps(out, indent=2))
    return out


def post_sample_size(run_dir: Path) -> dict[str, Any]:
    """Independent step after the Pilot B selection is written (protocol §9): N from the largest
    paired SD of M over the confirmatory contrasts at the selected points. Only SDs are reported;
    effect means are not computed here."""
    import numpy as np

    from mb import analyze, readouts

    sel = _read_json(run_dir / "pilot_b_selection.json")
    out: dict[str, Any] = {"smoke": sel["smoke"], "consumable": sel["consumable"]}
    s = sel["selection"]
    if s == "incomplete" or not s.get("ok"):
        out["N"] = None
        out["reason"] = "Pilot B selection incomplete or failed"
    else:
        scores = readouts.score_records(_valid_ok(run_dir), readouts.ScoreOptions(rotations=None))
        a = scores[scores["recipient"] == "A"]

        def arm(condition: str, gain: float | None = None) -> str:
            m = a[a["condition"] == condition]
            if gain is not None:
                m = m[np.isclose(m["gain"].astype(float), gain)]
            names = m["arm"].unique()
            if len(names) != 1:
                raise SystemExit(f"expected one {condition} arm at gain {gain}, found {list(names)}")
            return str(names[0])

        contrasts = [(arm("TWO", s["g_star"]), arm("ONE", s["g_star"]))]
        if s["static_executable"] and s["g_static"] is not None:
            contrasts.append((arm("ONE", s["g_star"]), arm("STATIC", s["g_static"])))
        contrasts.append((arm("ONE", s["g_star"]), arm("LANG_TAG")))
        sds = {f"{a1} - {a2}": float(np.std(analyze.paired_differences(scores, a1, a2, "M"), ddof=1))
               for a1, a2 in contrasts}
        n, mde = analyze.plan_sample_size(list(sds.values()))
        out.update(sd_of_paired_M=sds, N=n, mde_at_N=mde, delta=0.5)
    (run_dir / "sample_size.json").write_text(json.dumps(out, indent=2))
    return out


def post_pilot_c(run_dir: Path) -> dict[str, Any]:
    """Pilot C (protocol §10): engineering re-check of the frozen points and G2.

    G2 passes when the rule content-counterfactual score of ONE(g*) vs CF(g*) has a one-sided 95%
    bootstrap lower bound > 0 *and* ONE(g*) meets the engineering gates; the word score is
    reported separately. Every other bridged arm (STATIC, extension-A layers) is only re-checked.
    """
    import numpy as np

    from mb import analyze, readouts

    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True)}
    if comp["status"] != "complete":
        out["G2"] = "incomplete"
    else:
        ok = _valid_ok(run_dir)
        scores = readouts.score_records(ok, readouts.ScoreOptions(rotations=None))
        c0 = scores[scores["condition"] == "C0"]["arm"].unique()
        if len(c0) != 1:
            raise SystemExit("pilot C needs exactly one C0 arm")
        cand = scores[scores["condition"].isin(["ONE", "TWO", "STATIC", "CF"])]
        cols = ["arm", "message_form", "layer", "gain", "condition"] + [c for c in ("interface", "kv_scope")
                                                                          if c in cand.columns]
        meta = cand[cols].drop_duplicates().rename(columns={"message_form": "form"})
        summary = analyze.selector_summary(scores, c0[0], meta[["arm", "form", "layer", "gain", "condition"]])
        summary["arm"] = list(meta["arm"])
        summary["eligible"] = [bool(x) for x in analyze.eligible(summary)]
        summary.to_csv(run_dir / "pilot_c_summary.csv", index=False)
        out["engineering"] = summary.to_dict(orient="records")
        cf = meta[meta["condition"] == "CF"]
        if len(cf) != 1:
            raise SystemExit("pilot C needs exactly one CF arm (the G2 counterfactual)")
        form, layer, gain = cf["form"].iloc[0], int(cf["layer"].iloc[0]), float(cf["gain"].iloc[0])
        cf_row = cf.iloc[0]
        same_iface = ((meta["interface"] == cf_row["interface"]) & (meta["kv_scope"].astype(str) == str(cf_row["kv_scope"]))
                      if "interface" in meta.columns else True)
        one = meta[(meta["condition"] == "ONE") & (meta["form"] == form) & (meta["layer"] == layer)
                   & np.isclose(meta["gain"].astype(float), gain) & same_iface]
        if len(one) != 1:
            raise SystemExit("pilot C needs the ONE arm at the CF arm's form/layer/gain")
        one_arm, cf_arm = str(one["arm"].iloc[0]), str(cf["arm"].iloc[0])
        g2: dict[str, Any] = {"one_arm": one_arm, "cf_arm": cf_arm}
        for kind, qid in (("rule", "ACC_RULE"), ("word", "ACC_WORD")):
            df = readouts.content_cf_score([r for r in ok if r["arm"] == one_arm],
                                           [r for r in ok if r["arm"] == cf_arm], qid)
            vals = df["C_content"].to_numpy(dtype=float)
            finite = vals[np.isfinite(vals)]
            g2[f"C_content_{kind}"] = {"n": int(finite.size), "n_missing": int(vals.size - finite.size),
                                       "mean": float(finite.mean()) if finite.size else None,
                                       "lb95_one_sided": analyze.one_sided_lower_bound(finite)}
        one_row = summary[summary["arm"] == one_arm].iloc[0]
        g2["one_meets_engineering_gates"] = bool(one_row["eligible"])
        lb = g2["C_content_rule"]["lb95_one_sided"]
        out["G2"] = "pass" if (lb is not None and np.isfinite(lb) and lb > 0 and g2["one_meets_engineering_gates"]) \
            else "fail"
        out["g2_detail"] = g2
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "pilot_c.json").write_text(json.dumps(out, indent=2, default=float))
    return out


def _arm_at(scores, condition: str, gain: float | None = None, readout_mode: str = "FULL",
            recipient: str = "A") -> str:
    import numpy as np

    m = scores[(scores["recipient"] == recipient) & (scores["condition"] == condition)
               & (scores["readout_mode"] == readout_mode)]
    if gain is not None:
        m = m[np.isclose(m["gain"].astype(float), gain)]
    names = m["arm"].unique()
    if len(names) != 1:
        raise SystemExit(f"expected one {condition}/{readout_mode} arm at gain {gain} for {recipient}, found {list(names)}")
    return str(names[0])


SECONDARY_METRICS = ("M_NOW", "M_WORD")
DESCRIPTIVE_METRICS = ("M", "M_NOW", "M_WORD", "M_START_N", "ACC_RULE", "ACC_WORD", "CAP_ACC", "LABEL_MASS")


def post_confirmatory(run_dir: Path) -> dict[str, Any]:
    """Pre-registered analysis of the formal stage (protocol §9).

    Confirmatory: recipient A, FULL, metric M, contrasts TWO(g*)-ONE(g*), ONE(g*)-STATIC(g_s*) (if
    executable), ONE(g*)-LANG_TAG; two-sided paired t, Holm within the family, 10,000-resample
    episode-bootstrap 95% intervals, robustness summaries and the access (ACC) difference within
    each contrast. Secondary: the same contrasts on M_NOW and M_WORD, one Holm family. Descriptive:
    every arm minus C0 for each recipient. Missing trials stay missing (pairs are dropped, counts shown).
    """
    from mb import analyze, readouts

    manifest = _read_json(run_dir / "manifest.json")
    frozen = _read_json(run_dir / "identity.json")["stage_config"].get("frozen") or {}
    if "g_star" not in frozen:
        raise SystemExit("confirmatory analysis needs the frozen protocol-v1 parameters in the stage config")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True), "frozen": frozen}
    scores = readouts.score_records(_valid_ok(run_dir), readouts.ScoreOptions(rotations=None))
    one, two = _arm_at(scores, "ONE", frozen["g_star"]), _arm_at(scores, "TWO", frozen["g_star"])
    contrasts = [(two, one)]
    if frozen.get("static_executable") and frozen.get("g_static") is not None:
        contrasts.append((one, _arm_at(scores, "STATIC", frozen["g_static"])))
    contrasts.append((one, _arm_at(scores, "LANG_TAG")))

    def rows(results, p_holm=None):
        out_rows = []
        for i, r in enumerate(results):
            out_rows.append({"arm1": r.arm1, "arm2": r.arm2, "metric": r.metric, "n": r.test.n, "mean": r.test.mean,
                             "sd": r.test.sd, "se": r.test.se, "t": r.test.t, "p_two_sided": r.test.p_two_sided,
                             "p_holm": r.p_holm if p_holm is None else p_holm[i],
                             "ci95_lo": r.ci[0], "ci95_hi": r.ci[1]})
        return out_rows

    out["primary"] = rows(analyze.contrast_family(scores, contrasts, "M"))
    out["robustness"] = {f"{a1} - {a2}": analyze.robustness_report(analyze.paired_differences(scores, a1, a2, "M"))
                         for a1, a2 in contrasts}
    access = []
    for a1, a2 in contrasts:
        for metric in ("ACC_RULE", "ACC_WORD"):
            d = analyze.paired_differences(scores, a1, a2, metric)
            lo, hi = analyze.bootstrap_ci(d, n_boot=4000)
            access.append({"arm1": a1, "arm2": a2, "metric": metric, "n": int(len(d)),
                           "mean": float(d.mean()) if len(d) else None, "ci95_lo": lo, "ci95_hi": hi})
    out["access_in_contrasts"] = access
    sec = [r for metric in SECONDARY_METRICS for r in analyze.contrast_family(scores, contrasts, metric)]
    out["secondary"] = rows(sec, analyze.holm([r.test.p_two_sided for r in sec]))
    desc = []
    for recipient in ("A", "B"):
        sub = scores[scores["recipient"] == recipient]
        c0 = [a for a in sub[sub["condition"] == "C0"]["arm"].unique()]
        if len(c0) != 1:
            continue
        for arm in sorted(set(sub["arm"]) - set(c0)):
            for metric in DESCRIPTIVE_METRICS:
                d = analyze.paired_differences(scores, arm, c0[0], metric, recipient)
                if len(d) < 2:
                    continue
                lo, hi = analyze.bootstrap_ci(d, n_boot=4000)
                desc.append({"recipient": recipient, "arm": arm, "metric": metric, "n": int(len(d)),
                             "delta_vs_C0": float(d.mean()), "ci95_lo": lo, "ci95_hi": hi})
    out["descriptive"] = desc
    (run_dir / "confirmatory.json").write_text(json.dumps(out, indent=2, default=float))
    return out


# ---------------------------------------------------------------------------
# Protocol v2 post steps (PROTOCOL_V2.md §1–3). Parameters come from StageConfig.params.
# ---------------------------------------------------------------------------


def _stage_params(run_dir: Path) -> dict[str, Any]:
    return _read_json(run_dir / "identity.json")["stage_config"].get("params") or {}


def _partner_rates(records: list[dict[str, Any]], recipient: str = "A") -> dict[str, float]:
    """Share of ACC-rule answers (one recipient) whose argmax is the partner's actual rule."""
    from mb import readouts

    hits: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r["qid"] == "ACC_RULE" and r["recipient"] == recipient:
            hits[r["arm"]].append(float(readouts.argmax_meaning(r) == "partner"))
    return {arm: sum(v) / len(v) for arm, v in hits.items() if v}


def strength_table(run_dir: Path, recipient: str = "A") -> "pd.DataFrame":
    """Per arm vs C0 (one recipient): ACC increments, engineering gates and the partner-hit rate."""
    import pandas as pd

    from mb import analyze, readouts

    records = _valid_ok(run_dir)
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    a = scores[scores["recipient"] == recipient]
    c0 = a[a["condition"] == "C0"]
    if c0["arm"].nunique() != 1:
        raise SystemExit(f"a v2 pilot needs exactly one C0 arm for recipient {recipient}")
    base = c0.set_index("episode_id")
    rates = _partner_rates([r for r in records if r["recipient"] == recipient], recipient)
    meta = {r["arm"]: r for r in records}
    rows = []
    for arm, g in a[a["condition"] != "C0"].groupby("arm"):
        j = g.set_index("episode_id").join(base, rsuffix="_c0", how="inner").dropna(
            subset=["ACC_RULE", "ACC_RULE_c0", "CAP_ACC", "CAP_ACC_c0", "LABEL_MASS", "LABEL_MASS_c0"])
        m = meta[arm]
        rows.append({"arm": arm, "condition": m["condition"], "interface": m.get("interface", "residual"),
                     "kv_scope": m.get("kv_scope"), "kv_w_live": m.get("kv_w_live"), "layer": m["layer"],
                     "gain": float(m["gain"]), "n": len(j),
                     "acc_increment": float((j["ACC_RULE"] - j["ACC_RULE_c0"]).mean()),
                     "acc_word_increment": float((j["ACC_WORD"] - j["ACC_WORD_c0"]).mean()),
                     "cap_drop": float(j["CAP_ACC_c0"].mean() - j["CAP_ACC"].mean()),
                     "label_mass": float(j["LABEL_MASS"].mean()),
                     "mass_drop": float(j["LABEL_MASS_c0"].mean() - j["LABEL_MASS"].mean()),
                     "partner_rate": rates.get(arm, float("nan")),
                     "partner_rate_c0": rates.get(str(c0["arm"].iloc[0]), float("nan"))})
    table = pd.DataFrame(rows)
    if table.empty:
        raise SystemExit("no non-C0 arms to evaluate")
    table["eligible"] = [bool(x) for x in analyze.eligible(table)]
    return table


def post_select_strength(run_dir: Path) -> dict[str, Any]:
    """Strength pilot: per interface group the eligible point with the largest ACC-rule increment,
    and whether it passes the strength standard (ACC ≥ min_acc nat and partner hits ≥ min_partner)."""
    params = _stage_params(run_dir)
    min_acc, min_partner = float(params.get("min_acc", 5.0)), float(params.get("min_partner_rate", 0.30))
    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True),
                           "min_acc": min_acc, "min_partner_rate": min_partner}
    if comp["status"] != "complete":
        out["selection"] = "incomplete"
    else:
        table = strength_table(run_dir)
        table["strong"] = [bool(e and a >= min_acc and p >= min_partner)
                           for e, a, p in zip(table["eligible"], table["acc_increment"], table["partner_rate"])]
        table.to_csv(run_dir / "strength_table.csv", index=False)
        groups = {}
        for key, g in table.groupby(["condition", "interface", "kv_scope", "layer"], dropna=False):
            ok = g[g["eligible"]].sort_values(["acc_increment", "gain"], ascending=[False, True])
            groups["|".join(str(k) for k in key)] = None if ok.empty else ok.iloc[0].to_dict()
        # PROTOCOL_V2 §1: groups are tried in the pre-set order; in each, the top-ACC eligible point is
        # tested against the strength standard; the first group whose top point passes is selected.
        order = params.get("group_order") or sorted(groups)
        out["groups"], out["group_order"], out["selection"] = groups, order, None
        for key in order:
            top = groups.get(key)
            if top is not None and top["strong"]:
                out["selection"] = top
                break
        out["strength_gate"] = "pass" if out["selection"] is not None else "not met"
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "strength_selection.json").write_text(json.dumps(out, indent=2, default=str))
    return out


def post_match_static(run_dir: Path) -> dict[str, Any]:
    """STATIC gain whose ACC-rule increment is closest to each target arm (ties: smaller gain);
    unmatched when the gap exceeds 25% of the target's increment."""
    params = _stage_params(run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True)}
    if comp["status"] != "complete":
        out["matches"] = "incomplete"
    else:
        table = strength_table(run_dir)
        table.to_csv(run_dir / "strength_table.csv", index=False)
        static = table[(table["condition"] == "STATIC") & table["eligible"]]
        matches = {}
        for target in params.get("targets", []):
            m = _nearest_by_acc(table, static, target)
            matches[target] = None if m is None else {"static_arm": m["arm"], "gain": m["gain"],
                                                      "target_acc": m["target_acc"], "static_acc": m["arm_acc"],
                                                      "matched": m["matched"]}
        out["matches"] = matches
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "static_match.json").write_text(json.dumps(out, indent=2, default=str))
    return out


def _nearest_by_acc(table: "pd.DataFrame", candidates: "pd.DataFrame", target: str) -> dict[str, Any] | None:
    """Candidate whose ACC-rule increment is closest to the target arm's (ties: smaller gain); unmatched
    when the gap exceeds 25% of the target's increment."""
    row = table[table["arm"] == target]
    if row.empty:
        raise SystemExit(f"target arm {target} not in this run")
    t = float(row["acc_increment"].iloc[0])
    if candidates.empty:
        return None
    c = candidates.assign(dist=(candidates["acc_increment"] - t).abs())
    best = c.sort_values(["dist", "gain"]).iloc[0]
    return {"arm": best["arm"], "gain": float(best["gain"]), "target_acc": t, "arm_acc": float(best["acc_increment"]),
            "matched": bool(best["dist"] <= 0.25 * abs(t))}


def post_match_arms(run_dir: Path) -> dict[str, Any]:
    """S-T3b (PROTOCOL_V3 §5): among eligible candidate arms, the one whose ACC-rule increment matches the
    target arm's, by the same rule as the STATIC match (ACC, CAP and format only)."""
    params = _stage_params(run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True)}
    if comp["status"] != "complete":
        out["match"] = "incomplete"
    else:
        table = strength_table(run_dir)
        table.to_csv(run_dir / "strength_table.csv", index=False)
        cands = table[table["arm"].isin(params.get("candidates", [])) & table["eligible"]]
        out["match"] = _nearest_by_acc(table, cands, params["target"])
        out["target"] = params["target"]
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "arm_match.json").write_text(json.dumps(out, indent=2, default=str))
    return out


def _equivalence(scores, spec: dict[str, Any]) -> dict[str, Any]:
    """PROTOCOL_V3 §7 equivalence test: D = arm1 − arm2 on ``metric`` keeps at least (1 − margin) of the
    reference effect (effect_arm − base) when the 90% bootstrap interval of D lies above −margin × effect
    (two one-sided 5% tests' lower half; D may be positive)."""
    from mb import analyze

    d = _paired(scores, spec["arm1"], spec["arm2"], spec["metric"])
    e = _paired(scores, spec["effect_arm"], spec["base"], spec["metric"])
    lo, hi = analyze.bootstrap_ci(d, n_boot=10_000, level=0.90)
    effect = float(e.mean()) if e.size else math.nan
    bound = -float(spec["margin"]) * effect
    return {**spec, "n": int(d.size), "mean": float(d.mean()) if d.size else None, "ci90_lo": lo, "ci90_hi": hi,
            "effect": effect, "bound": bound, "equivalent": bool(d.size > 1 and math.isfinite(bound) and lo > bound)}


def _paired(scores, arm1: str, arm2: str, metric: str, recipient: str = "A"):
    from mb import analyze

    return analyze.paired_differences(scores, arm1, arm2, metric, recipient).to_numpy(dtype=float)


def post_signal(run_dir: Path) -> dict[str, Any]:
    """Signal gate (PROTOCOL_V2 §1): per study, go/no-go on its first primary comparison and N from
    the largest paired SD of its primary comparisons. Pilot data never enter a confirmatory sample."""
    import numpy as np

    from mb import analyze, readouts

    params = _stage_params(run_dir)
    min_effect = float(params.get("min_effect", 0.3))
    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True), "min_effect": min_effect}
    if comp["status"] != "complete":
        out["studies"] = "incomplete"
    else:
        scores = readouts.score_records(_valid_ok(run_dir), readouts.ScoreOptions(rotations=None))
        studies = {}
        for name, spec in params.get("studies", {}).items():
            comps = []
            for arm1, arm2, metric, direction in spec:
                d = _paired(scores, arm1, arm2, metric)
                lo, hi = analyze.bootstrap_ci(d, n_boot=10_000, level=0.90)
                comps.append({"arm1": arm1, "arm2": arm2, "metric": metric, "direction": direction, "n": int(d.size),
                              "mean": float(d.mean()) if d.size else None,
                              "sd": float(d.std(ddof=1)) if d.size > 1 else None, "ci90_lo": lo, "ci90_hi": hi})
            if not comps:
                raise SystemExit(f"study {name} has no comparisons")
            first = comps[0]
            if first["direction"] not in ("+", "-", "0"):
                raise SystemExit(f"study {name}: direction must be '+', '-' or '0'")
            if first["mean"] is None or not math.isfinite(first["mean"]):
                studies[name] = {"go": False, "comparisons": comps, "N": None, "mde_at_N": None,
                                 "reason": "no paired episodes"}
                continue
            sign_ok = {"+": first["mean"] > 0, "-": first["mean"] < 0, "0": True}[first["direction"]]
            excludes_zero = first["ci90_lo"] > 0 or first["ci90_hi"] < 0
            go = bool(sign_ok and abs(first["mean"]) >= min_effect and excludes_zero)
            sds = [c["sd"] for c in comps if c["sd"] is not None and math.isfinite(c["sd"])]
            n, mde = analyze.plan_sample_size(sds, delta=0.3) if sds else (None, None)
            studies[name] = {"go": go, "comparisons": comps, "N": n, "mde_at_N": mde,
                             "reason": ("" if go else "direction" if not sign_ok else
                                        "too small" if abs(first["mean"]) < min_effect else "interval includes 0")}
        out["studies"] = studies
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "signal.json").write_text(json.dumps(out, indent=2, default=float))
    return out


def post_contrasts(run_dir: Path) -> dict[str, Any]:
    """Confirmatory families (PROTOCOL_V2 §6, PROTOCOL_V3 §7): Holm within each study, 10,000-resample
    bootstrap intervals, robustness; v3 equivalence tests; descriptive arm − C0 deltas (recipient A)."""
    from mb import analyze, readouts

    params = _stage_params(run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True), "families": {},
                           "consumable": not manifest.get("smoke", True) and comp["status"] == "complete"}
    scores = readouts.score_records(_valid_ok(run_dir), readouts.ScoreOptions(rotations=None))
    for family, spec in params.get("families", {}).items():
        rows = []
        for arm1, arm2, metric in spec:
            d = _paired(scores, arm1, arm2, metric)
            t = analyze.paired_t(d)
            lo, hi = analyze.bootstrap_ci(d, n_boot=10_000)
            rows.append({"arm1": arm1, "arm2": arm2, "metric": metric, "n": t.n, "mean": t.mean, "sd": t.sd,
                         "se": t.se, "t": t.t, "p_two_sided": t.p_two_sided, "ci95_lo": lo, "ci95_hi": hi,
                         "robustness": analyze.robustness_report(d)})
        for row, p in zip(rows, analyze.holm([r["p_two_sided"] for r in rows])):
            row["p_holm"] = p
        out["families"][family] = rows
    out["equivalence"] = {name: _equivalence(scores, spec) for name, spec in params.get("equivalence", {}).items()}
    desc = []
    a = scores[scores["recipient"] == "A"]
    c0 = a[a["condition"] == "C0"]["arm"].unique()
    if len(c0) == 1:
        for arm in sorted(set(a["arm"]) - set(c0)):
            for metric in DESCRIPTIVE_METRICS:
                d = _paired(scores, arm, str(c0[0]), metric)
                if d.size < 2:
                    continue
                lo, hi = analyze.bootstrap_ci(d, n_boot=4000)
                desc.append({"arm": arm, "metric": metric, "n": int(d.size), "delta_vs_C0": float(d.mean()),
                             "ci95_lo": lo, "ci95_hi": hi})
    out["descriptive"] = desc
    (run_dir / "contrasts.json").write_text(json.dumps(out, indent=2, default=float))
    return out


# ---------------------------------------------------------------------------
# Protocol v3 post steps (PROTOCOL_V3.md): pair-level outcomes for two-way coupling
# ---------------------------------------------------------------------------

PAIR_OUTCOMES = ("one_wins", "a_adopts", "b_adopts", "swap", "intact", "both_third", "same_rule")
PAIR_MARGINALS = ("a_partner", "a_own", "b_partner", "b_own")
EXCESS_COLUMNS = ("one_wins", *PAIR_MARGINALS)


def pair_outcomes(run_dir: Path, qids: tuple[str, ...] = ("START", "NOW")) -> "pd.DataFrame":
    """Per (arm, qid, episode): share of rotations with each pair outcome (PROTOCOL_V3 §2).

    A's and B's answers come from separate branches of the same C48 snapshot, so an outcome is the
    agreement of two separately probed members, not a joint answer. The merge outcome ``one_wins``
    counts only one member's rule held by both (``a_adopts``: both hold B's rule; ``b_adopts``: both
    hold A's). A shared third rule (Robin's or the unused one) is ``both_third``, kept apart because it
    can signal damage rather than adoption. The per-side shares feed the independence baseline.
    """
    import pandas as pd

    from mb import readouts

    picks: dict[tuple, dict[str, tuple[str, str]]] = defaultdict(dict)
    for r in _valid_ok(run_dir):
        if r["qid"] in qids:
            meaning = readouts.argmax_meaning(r)
            option = r["options"][r["label_meaning"].index(meaning)] if meaning is not None else None
            picks[(r["arm"], r["qid"], r["episode_id"], r["rotation_id"])][r["recipient"]] = (meaning, option)
    per: dict[tuple, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (arm, qid, ep, _), who in picks.items():
        if "A" not in who or "B" not in who:
            continue
        (ma, oa), (mb_, ob) = who["A"], who["B"]
        same = oa is not None and oa == ob
        flags = {"a_adopts": ma == "partner" and mb_ == "own", "b_adopts": ma == "own" and mb_ == "partner",
                 "swap": ma == "partner" and mb_ == "partner", "intact": ma == "own" and mb_ == "own",
                 "both_third": same and ma not in ("own", "partner"), "same_rule": same,
                 "a_partner": ma == "partner", "a_own": ma == "own", "b_partner": mb_ == "partner",
                 "b_own": mb_ == "own"}
        flags["one_wins"] = flags["a_adopts"] or flags["b_adopts"]
        for k, v in flags.items():
            per[(arm, qid, ep)][k].append(float(v))
    rows = [{"arm": arm, "qid": qid, "episode_id": ep, **{k: sum(v) / len(v) for k, v in d.items()}}
            for (arm, qid, ep), d in per.items()]
    return pd.DataFrame(rows)


def one_wins_excess(x: "np.ndarray") -> "np.ndarray":
    """Observed one_wins minus its value if A's and B's picks were independent with the same marginals.

    ``x`` holds per-episode rows of EXCESS_COLUMNS along axis -2 (episodes weigh equally). Pooling over
    episodes also turns between-episode asymmetries into excess, which is why PROTOCOL_V3 §2 compares
    against a two-way arm without the live loop instead of against zero.
    """
    m = x.mean(axis=-2)
    return m[..., 0] - (m[..., 1] * m[..., 4] + m[..., 2] * m[..., 3])


def _no_pairs(arm1: str, arm2: str | None, qid: str, outcome: str, direction: str) -> dict[str, Any]:
    return {"arm1": arm1, "arm2": arm2, "qid": qid, "outcome": outcome, "direction": direction, "n": 0,
            "mean": None, "sd": None, "ci90_lo": math.nan, "ci90_hi": math.nan}


def _rate_comparison(pairs: "pd.DataFrame", arm1: str, arm2: str | None, qid: str, outcome: str,
                     direction: str) -> dict[str, Any]:
    """Paired per-episode difference of an outcome rate (arm2 None: the rate itself)."""
    from mb import analyze

    sub = pairs[pairs["qid"] == qid].pivot(index="episode_id", columns="arm", values=outcome)
    if arm1 not in sub.columns or (arm2 is not None and arm2 not in sub.columns):
        return _no_pairs(arm1, arm2, qid, outcome, direction)
    d = (sub[arm1] - (sub[arm2] if arm2 is not None else 0.0)).dropna().to_numpy(dtype=float)
    lo, hi = analyze.bootstrap_ci(d, n_boot=10_000, level=0.90)
    return {"arm1": arm1, "arm2": arm2, "qid": qid, "outcome": outcome, "direction": direction, "n": int(d.size),
            "mean": float(d.mean()) if d.size else None, "sd": float(d.std(ddof=1)) if d.size > 1 else None,
            "ci90_lo": lo, "ci90_hi": hi, "arm1_rate": float(sub[arm1].mean()),
            "arm2_rate": float(sub[arm2].mean()) if arm2 is not None else None}


def _excess_comparison(pairs: "pd.DataFrame", arm1: str, arm2: str | None, qid: str, direction: str,
                       n_boot: int = 10_000, seed: int = 0, level: float = 0.90) -> dict[str, Any]:
    """one_wins excess of arm1 minus that of arm2 (arm2 None: minus 0). The bootstrap resamples the same
    episodes in both arms; ``sd`` is its SE times √n, the per-episode SD that the N rule expects."""
    import numpy as np

    sub = pairs[pairs["qid"] == qid].set_index("episode_id")
    x1 = sub[sub["arm"] == arm1]
    x2 = sub[sub["arm"] == arm2] if arm2 is not None else None
    eps = sorted(x1.index if x2 is None else x1.index.intersection(x2.index))
    if len(eps) < 2:
        return _no_pairs(arm1, arm2, qid, "one_wins_excess", direction)
    cols = list(EXCESS_COLUMNS)
    a1 = x1.loc[eps, cols].to_numpy(dtype=float)
    a2 = x2.loc[eps, cols].to_numpy(dtype=float) if x2 is not None else None
    rng = np.random.default_rng(seed)
    boots = []
    for start in range(0, n_boot, 1000):  # chunks keep the index array small at N = 600
        idx = rng.integers(0, len(eps), size=(min(1000, n_boot - start), len(eps)))
        boots.append(one_wins_excess(a1[idx]) - (one_wins_excess(a2[idx]) if a2 is not None else 0.0))
    b = np.concatenate(boots)
    e1 = float(one_wins_excess(a1))
    e2 = float(one_wins_excess(a2)) if a2 is not None else None
    alpha = (1 - level) / 2
    return {"arm1": arm1, "arm2": arm2, "qid": qid, "outcome": "one_wins_excess", "direction": direction,
            "n": len(eps), "mean": e1 - (e2 if e2 is not None else 0.0),
            "sd": float(b.std(ddof=1)) * math.sqrt(len(eps)),
            "ci90_lo": float(np.quantile(b, alpha)), "ci90_hi": float(np.quantile(b, 1 - alpha)),
            "arm1_excess": e1, "arm2_excess": e2, "arm1_rate": float(a1[:, 0].mean()),
            "arm2_rate": float(a2[:, 0].mean()) if a2 is not None else None}


def pair_comparison(pairs: "pd.DataFrame", arm1: str, arm2: str | None, qid: str, outcome: str,
                    direction: str) -> dict[str, Any]:
    if pairs.empty:
        return _no_pairs(arm1, arm2, qid, outcome, direction)
    if outcome == "one_wins_excess":
        return _excess_comparison(pairs, arm1, arm2, qid, direction)
    return _rate_comparison(pairs, arm1, arm2, qid, outcome, direction)


def post_select_live(run_dir: Path) -> dict[str, Any]:
    """S-B′ (PROTOCOL_V3 §2): per KV family, the TWO arm with the largest live weight (PC: kv_w_live;
    ALL: w) that meets the engineering gates on both sides; reports A-side ACC and the ONE counterpart."""
    params = _stage_params(run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True)}
    if comp["status"] != "complete":
        out["selection"] = "incomplete"
    else:
        ta, tb = strength_table(run_dir, "A"), strength_table(run_dir, "B")
        both = ta.merge(tb[["arm", "eligible", "cap_drop"]], on="arm", suffixes=("", "_B"))
        both.to_csv(run_dir / "live_table.csv", index=False)
        selection = {}
        for family in params.get("family_order", ["PC", "ALL"]):
            fam = both[(both["condition"] == "TWO") & (both["kv_scope"] == family) & both["eligible"] & both["eligible_B"]]
            if fam.empty:
                selection[family] = None
                continue
            key = "kv_w_live" if family == "PC" else "gain"
            best = fam.sort_values(key, ascending=False).iloc[0].to_dict()
            best["one_arm"] = best["arm"].replace("TWO/", "ONE/", 1)
            selection[family] = best
        out["selection"] = selection
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "live_selection.json").write_text(json.dumps(out, indent=2, default=str))
    return out


def post_pair_signal(run_dir: Path) -> dict[str, Any]:
    """Signal gate on pair outcomes (PROTOCOL_V3 §2): go/no-go on the first comparison of each study and
    N from the largest paired SD of the study's comparisons, δ = min_effect (proportion scale).

    A comparison is [arm1, arm2 or null, qid, outcome, direction]; outcome ``one_wins_excess`` compares
    the excess of one_wins over independence, any other outcome compares per-episode rates. Lists under
    ``params.descriptive`` are reported but never enter the gate or N.
    """
    from mb import analyze

    params = _stage_params(run_dir)
    min_effect = float(params.get("min_effect", 0.10))
    manifest = _read_json(run_dir / "manifest.json")
    comp = run_completeness(run_dir)
    out: dict[str, Any] = {"completeness": comp, "smoke": manifest.get("smoke", True), "min_effect": min_effect}
    if comp["status"] != "complete":
        out["studies"] = "incomplete"
    else:
        pairs = pair_outcomes(run_dir)
        pairs.to_csv(run_dir / "pair_outcomes.csv", index=False)
        studies = {}
        for name, spec in params.get("studies", {}).items():
            comps = [pair_comparison(pairs, *c) for c in spec]
            if not comps:
                raise SystemExit(f"study {name} has no comparisons")
            first = comps[0]
            if first["direction"] not in ("+", "-", "0"):
                raise SystemExit(f"study {name}: direction must be '+', '-' or '0'")
            # A zero SD is a real (if extreme) pilot result; dropping it left go=true with no N.
            sds = [c["sd"] for c in comps if c["sd"] is not None and math.isfinite(c["sd"])]
            n, mde = analyze.plan_sample_size(sds, delta=min_effect) if sds else (None, None)
            if first["mean"] is None or not math.isfinite(first["mean"]):
                studies[name] = {"go": False, "comparisons": comps, "N": n, "mde_at_N": mde,
                                 "reason": "no paired episodes"}
                continue
            sign_ok = {"+": first["mean"] > 0, "-": first["mean"] < 0, "0": True}[first["direction"]]
            excludes_zero = first["ci90_lo"] > 0 or first["ci90_hi"] < 0
            go = bool(sign_ok and abs(first["mean"]) >= min_effect and excludes_zero)
            studies[name] = {"go": go, "comparisons": comps, "N": n, "mde_at_N": mde,
                             "reason": ("" if go else "direction" if not sign_ok else
                                        "too small" if abs(first["mean"]) < min_effect else "interval includes 0")}
        out["studies"] = studies
        out["descriptive"] = {name: [pair_comparison(pairs, *c) for c in spec]
                              for name, spec in params.get("descriptive", {}).items()}
    out["consumable"] = not out["smoke"] and comp["status"] == "complete"
    (run_dir / "pair_signal.json").write_text(json.dumps(out, indent=2, default=float))
    return out


POST = {"g1": post_g1, "select_pilot_a": post_select_pilot_a, "select_pilot_b": post_select_pilot_b,
        "sample_size": post_sample_size, "pilot_c": post_pilot_c, "confirmatory": post_confirmatory,
        "select_strength": post_select_strength, "match_static": post_match_static, "signal": post_signal,
        "contrasts": post_contrasts, "select_live": post_select_live, "pair_signal": post_pair_signal,
        "match_arms": post_match_arms}


# ---------------------------------------------------------------------------
# Run preparation (identity checks happen before any file is written)
# ---------------------------------------------------------------------------


def build_identity(cfg: StageConfig, limit: int | None, template: str, cal_info: dict[int, dict[str, Any]],
                   include_code: bool = True, prefix: str = "") -> dict[str, Any]:
    ident = {
        "stage_config": cfg.resolved(),
        "limit": limit,
        "calibration": {str(k): v for k, v in sorted(cal_info.items())},
        "template_hash": template,
        "prefix_hash": prefix,
        "cap_bank_hash": tasks.cap_bank_hash(),
        "tokenizer_manifest_sha": ledger.file_sha256(REPO_ROOT / "materials" / "tokenizer_manifest.json"),
        "chat_build": CHAT_BUILD_VERSION,
        "model_revision": MODEL_REVISION,
    }
    if include_code:
        ident["source_hash"] = source_hash()
    return json.loads(json.dumps(ident))  # canonical JSON types, so stored and fresh copies compare equal


@dataclasses.dataclass
class Prepared:
    run_dir: Path
    identity: dict[str, Any]
    cal_map: dict[int, Any]
    cal_meta: dict[int, dict[str, Any]]
    smoke: bool
    resumed: bool


def prepare_run(cfg: StageConfig, config_path: Path, limit: int | None, resume: Path | None,
                allow_code_change: bool = False, tok=None) -> Prepared:
    tok = tok if tok is not None else chat.load_tokenizer()
    smoke = limit is not None
    template, prefix = template_hash(tok, cfg.materials), prefix_hash(tok, cfg.materials)
    stored: dict[str, Any] | None = None
    if resume is not None:
        if cfg.stage == "calibrate":
            raise SystemExit("calibration runs cannot be resumed; start a new calibrate run")
        stored = _read_json(resume / "identity.json")
        cal_paths = {int(k): v["path"] for k, v in stored.get("calibration", {}).items()}  # pinned resolution
    else:
        cal_paths = resolve_calibration(cfg.calibration, allow_smoke=smoke)
    cal_map: dict[int, Any] = {}
    cal_meta: dict[int, dict[str, Any]] = {}
    cal_info: dict[int, dict[str, Any]] = {}
    for layer, path in sorted(cal_paths.items()):
        cal, meta = load_calibration(path, layer, {"model_revision": MODEL_REVISION, "prefix_hash": prefix},
                                     allow_smoke=smoke)
        cal_map[layer], cal_meta[layer] = cal, meta
        cal_info[layer] = {"path": str(path), "hash": cal.hash(), "smoke": bool(meta.get("smoke", True))}
    identity = build_identity(cfg, limit, template, cal_info, include_code=not (resume and allow_code_change),
                              prefix=prefix)

    if resume is not None:
        old = {k: v for k, v in stored.items() if not (allow_code_change and k == "source_hash")}
        diff = ledger.compare_identity(old, identity)
        if diff:
            raise SystemExit(f"resume refused: identity differs in {diff}")
        with (resume / "resume_log.jsonl").open("a") as fh:
            fh.write(json.dumps({"resumed": dt.datetime.now().isoformat(), "git": git_state(),
                                 "source_hash": source_hash(), "allow_code_change": allow_code_change,
                                 "argv": sys.argv}) + "\n")
        return Prepared(resume, stored, cal_map, cal_meta, smoke, True)

    run_dir = new_run_dir(cfg.stage, cfg.tag + (f"-smoke{limit}" if smoke else ""))
    (run_dir / "config.yaml").write_text(Path(config_path).read_text())
    (run_dir / "identity.json").write_text(json.dumps(identity, indent=2))
    manifest = {"stage": cfg.stage, "config_path": str(config_path), "started": dt.datetime.now().isoformat(),
                "git": git_state(), "env": environment(), "smoke": smoke, "argv": sys.argv}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return Prepared(run_dir, identity, cal_map, cal_meta, smoke, False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", type=Path)
    ap.add_argument("--limit", type=int, default=None, help="use only the first N episodes (smoke run)")
    ap.add_argument("--resume", type=Path, default=None, help="existing run directory to continue")
    ap.add_argument("--allow-code-change", action="store_true",
                    help="on resume, accept changed source files (recorded in resume_log.jsonl)")
    ap.add_argument("--post-only", action="store_true", help="only run post-processing on --resume dir")
    args = ap.parse_args(argv)

    cfg = StageConfig.load(args.config)
    if args.post_only:
        if not args.resume:
            raise SystemExit("--post-only needs --resume")
        for step in cfg.post:
            print(step, json.dumps(POST[step](args.resume), indent=2))
        return 0

    prep = prepare_run(cfg, args.config, args.limit, args.resume, args.allow_code_change)
    log = RunLog(prep.run_dir)
    log(f"{'resumed' if prep.resumed else 'new'} {cfg.stage} run {prep.run_dir} (smoke={prep.smoke})")
    runner = Runner(cfg, prep.run_dir, args.limit, prep.identity, prep.cal_map, prep.cal_meta, log)
    comp: dict[str, Any] | None = None
    try:
        if cfg.stage == "calibrate":
            run_calibration(runner, cfg.calibration_layers, prep.smoke)
            comp = {"status": "complete", "n_expected": 0, "n_ok": 0, "n_missing": 0}
        else:
            if not (prep.run_dir / "balance.json").exists():
                bal = tasks.validate_episodes(runner.episodes)
                (prep.run_dir / "balance.json").write_text(json.dumps(_jsonable(vars(bal)), indent=2))
            arms = cfg.arm_configs()
            runner.register_arms(arms)
            runner.run_arms(arms)
    finally:
        runner.close()
    if comp is None:
        comp = run_completeness(prep.run_dir)
    (prep.run_dir / "completeness.json").write_text(json.dumps(comp, indent=2))
    now = dt.datetime.now().isoformat()
    (prep.run_dir / "run_status.json").write_text(json.dumps(
        {"status": comp["status"], "updated": now, "finished": now if comp["status"] == "complete" else None},
        indent=2))
    log(f"completeness: {comp['status']} ({comp['n_ok']}/{comp['n_expected']})")
    for step in cfg.post:
        log(f"{step}: " + json.dumps(POST[step](prep.run_dir)))
    log(f"run dir: {prep.run_dir}")
    log.close()
    return exit_code(comp)


def exit_code(comp: dict[str, Any]) -> int:
    """Shell status of a finished stage: non-zero when it ended incomplete, so a driver stops there
    instead of logging the stage as done."""
    return 0 if comp["status"] == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
