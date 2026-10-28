"""Synthetic V7 records for offline tests of the pilot gates and the variance step."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Callable

from mb import run, v7_run, v7_tasks as material

Policy = Callable[[str, str, int, int | None], str]


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, run.REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(ep: material.V7Episode, arm_id: str, qid: str, rotation: int | None, meaning: str,
           mass: float = 0.99) -> dict:
    _, options, meanings, _ = material.question_body(ep, "A", qid, rotation)
    logits = [0.0] * 4
    if qid != "U_OPEN":
        logits[list(meanings).index(meaning)] = 5.0
    return {"episode_id": ep.episode_id, "arm": f"V7/base/{arm_id}", "arm_id": arm_id, "recipient": "A",
            "qid": qid, "rotation_id": rotation, "options": list(options), "label_meaning": list(meanings),
            "label_logits": logits, "label_mass": mass, "status": "ok"}


def default_choice(qid: str) -> str:
    return {"USE": "other", "CAP0": "correct", "CAP1": "correct", "DETECT": "no2",
            "PROV_SELF_RULE": "own"}.get(qid, "own")


def records(episodes: list[material.V7Episode], policy: Policy, qids: tuple[str, ...] | None = None,
            mass: Callable[[str], float] = lambda arm: 0.99) -> list[dict]:
    out = []
    for i, ep in enumerate(episodes):
        for arm in v7_run.arms_for("base"):
            for qid in v7_run.qids_for(arm):
                if qids is not None and qid not in qids:
                    continue
                for rotation in ((None,) if qid == "U_OPEN" else ep.base.rotations):
                    out.append(record(ep, arm.arm_id, qid, rotation, policy(arm.arm_id, qid, i, rotation),
                                      mass(arm.arm_id)))
    return out


def run_dir(tmp_path: Path, cfg: v7_run.V7Config, policy: Policy) -> Path:
    """A minimal run directory that satisfies ``v7_run.run_completeness``."""
    root = tmp_path / "run"
    (root / "records").mkdir(parents=True)
    template = "synthetic-template"
    hashes = {a.name: a.config_hash("none", "none", template) for a in cfg.arm_configs()}
    identity = {"stage_config": cfg.resolved(), "template_hash": template, "limit": None}
    (root / "identity.json").write_text(json.dumps(identity))
    (root / "arm_hashes.json").write_text(json.dumps(hashes))
    (root / "manifest.json").write_text(json.dumps({"smoke": cfg.split == "v7_dev"}))
    rows = records(v7_run.episodes_for(cfg), policy)
    with (root / "records" / "attempt-001.jsonl").open("w") as stream:
        for row in rows:
            stream.write(json.dumps({**row, "config_hash": hashes[row["arm"]]}) + "\n")
    return root
