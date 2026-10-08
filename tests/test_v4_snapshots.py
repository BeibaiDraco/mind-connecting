"""Bounded C48 reuse, byte-level identity, and resume refusal without torch."""

from __future__ import annotations

import copy
import dataclasses
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from mb import run, tasks
from mb.conditions import ArmConfig
from mb.model_profiles import LLAMA31


@dataclasses.dataclass
class SyntheticState:
    cache: object
    attn: np.ndarray
    next_pos: np.ndarray
    pending: np.ndarray
    logits: np.ndarray
    mailbox: np.ndarray
    ema: np.ndarray
    consumed: list[np.ndarray]
    tick: int = 48
    phase: str = "C"
    c_start: int = 7


def state():
    return SyntheticState(
        cache=SimpleNamespace(layers=[SimpleNamespace(keys=np.ones((2, 2, 7, 4), dtype=np.float32),
                                                       values=np.zeros((2, 2, 7, 4), dtype=np.float32),
                                                       is_initialized=True)], offloading=False),
        attn=np.ones((2, 55), dtype=np.int64), next_pos=np.array([55, 55]), pending=np.array([12, 13]),
        logits=np.zeros((2, 8), dtype=np.float32), mailbox=np.zeros((2, 4), dtype=np.float32),
        ema=np.ones((2, 4), dtype=np.float32), consumed=[np.array([i, i + 1]) for i in range(48)])


def arm(mode="FULL", **changes):
    return ArmConfig("ONE", readout_mode=mode, interface="kv", kv_scope="P", gain=2,
                     model_profile=LLAMA31.key, **changes)


def test_full_and_rf_group_by_reflection_contract_only():
    full, rf = arm(), arm("RF")
    cf = ArmConfig("CF", interface="kv", kv_scope="P", gain=2, model_profile=LLAMA31.key)
    weak = ArmConfig("ONE", interface="kv", kv_scope="P", gain=1, model_profile=LLAMA31.key)
    ro = arm("RO")
    assert run.reflection_groups([full, cf, rf, weak, ro]) == [[full, rf], [cf], [weak], [ro]]
    assert run.reflection_groups([full, arm("RF", recipients=("A", "B"))]) == [[full, arm("RF", recipients=("A", "B"))]]


@pytest.mark.parametrize("field", [field.name for field in dataclasses.fields(SyntheticState)])
def test_snapshot_fingerprint_covers_every_relevant_field(field):
    original = state()
    changed = copy.deepcopy(original)
    if field == "cache":
        changed.cache.layers[0].values[0, 0, 0, 0] = 3
    elif field == "consumed":
        changed.consumed[-1][0] += 1
    elif field == "phase":
        changed.phase = "R"
    elif field in ("tick", "c_start"):
        setattr(changed, field, getattr(changed, field) + 1)
    else:
        getattr(changed, field).flat[0] += 1
    assert run.snapshot_hash(original) == run.snapshot_hash(copy.deepcopy(original))
    assert run.snapshot_hash(original) != run.snapshot_hash(changed)


def test_snapshot_includes_cache_metadata_dtype_shape_and_added_fields():
    baseline = state()
    for mutate in (lambda s: setattr(s.cache.layers[0], "is_initialized", False),
                   lambda s: setattr(s, "ema", s.ema.astype(np.float64)),
                   lambda s: setattr(s, "ema", s.ema.reshape(4, 2)),
                   lambda s: setattr(s, "done", True)):
        altered = copy.deepcopy(baseline)
        mutate(altered)
        assert run.snapshot_hash(altered) != run.snapshot_hash(baseline)
    baseline.unknown = object()
    with pytest.raises(TypeError, match="unsupported snapshot"):
        run.snapshot_hash(baseline)


def test_snapshot_registration_is_append_only_and_rejects_changed_retry(tmp_path):
    runner = run.Runner.__new__(run.Runner)
    runner.run_dir, runner.snapshot_hashes = tmp_path, {}
    episodes = tasks.make_episodes(2, "snapshot-test")
    runner._register_snapshot("key", "original", episodes)
    path = tmp_path / "snapshots.jsonl"
    original = path.read_bytes()
    runner._register_snapshot("key", "original", episodes)
    assert path.read_bytes() == original
    with pytest.raises(RuntimeError, match="retry/resume"):
        runner._register_snapshot("key", "changed", episodes)
    assert path.read_bytes() == original
    with path.open("a") as fh:
        fh.write('{"interrupted":')
    runner._register_snapshot("new-key", "next", episodes)
    assert json.loads(path.read_text().splitlines()[-1])["sha256"] == "next"
    assert path.read_bytes().startswith(original)


def test_run_arms_reuses_one_state_for_full_rf_and_releases_each_family():
    runner = run.Runner.__new__(run.Runner)
    runner.cfg = run.StageConfig(stage="unit", tag="unit", split="snapshots", n_episodes=3,
                                 model_profile=LLAMA31.key, episodes_per_batch=2)
    runner.episodes = tasks.make_episodes(3, "snapshots")
    runner.prior_records, runner.new_records, runner.arm_hash, runner.cal = [], [], {}, {}
    runner.model, runner.tok = None, None
    runner.engine_cls = lambda *args: SimpleNamespace(close=lambda: None)
    runner.log = lambda message: None
    calls = []

    def branch(engine, selected, chunk, all_rot_ids, done, chunk_index, snapshot=None):
        if snapshot is None:
            snapshot = object()
        calls.append((selected.name, chunk_index, snapshot))
        return snapshot

    runner.run_arm_chunk = branch
    full, rf = arm(), arm("RF")
    cf = ArmConfig("CF", interface="kv", kv_scope="P", gain=2, model_profile=LLAMA31.key)
    runner.run_arms([full, cf, rf])
    assert len(calls) == 6
    assert calls[0][2] is calls[1][2]  # same C48 object for FULL and RF
    assert calls[2][2] is not calls[0][2]  # CF independently rebuilt
    assert calls[3][2] is calls[4][2]
    assert calls[3][2] is not calls[0][2]  # next episode chunk is independent


def test_mutated_shared_snapshot_fails_before_any_readout(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "mb.runtime", SimpleNamespace(U_OPEN_TOKENS=80, make_plan=None))
    runner = run.Runner.__new__(run.Runner)
    runner.torch = None
    runner.arm_identity = lambda selected: ({}, "config", "mask")
    episodes = tasks.make_episodes(1, "mutation")
    runner._donors = lambda selected, chunk: chunk
    runner._pending_questions = lambda *args: [(0, "A", SimpleNamespace())]
    runner._base_record = lambda *args: {}
    emitted = []
    runner._emit = emitted.append
    runner.log = lambda message: None
    runner.writer = SimpleNamespace(flush=lambda: None)
    frozen = state()
    snapshot = run.ReflectionSnapshot(frozen, {}, [{}], ["cost"], None, "key", run.snapshot_hash(frozen))
    frozen.pending[0] += 1
    engine = SimpleNamespace(run_readout=lambda *args, **kwargs: pytest.fail("mutated state reached a readout"))
    runner.run_arm_chunk(engine, arm("RF"), episodes, set(), set(), 0, snapshot)
    assert len(emitted) == 1 and emitted[0]["status"] == "failed"
    assert "snapshot was mutated" in emitted[0]["failure_reason"]


def test_torch_bf16_snapshot_hash_and_cloned_cache_isolation():
    """Runs on the GPU host's offline suite; torch is deliberately absent on the Mac."""
    torch = pytest.importorskip("torch")
    from transformers import DynamicCache
    from mb.runtime import State, select_rows

    kv = [(torch.ones(2, 2, 7, 4, dtype=torch.bfloat16),
           torch.zeros(2, 2, 7, 4, dtype=torch.bfloat16))]
    original = State(
        cache=DynamicCache(ddp_cache_data=kv), attn=torch.ones(2, 7, dtype=torch.long),
        next_pos=torch.tensor([7, 7]), pending=torch.tensor([12, 13]),
        logits=torch.zeros(2, 8), mailbox=torch.zeros(2, 4, dtype=torch.bfloat16),
        ema=torch.ones(2, 4), consumed=[torch.tensor([i, i + 1]) for i in range(48)],
        tick=48, phase="C", c_start=7)
    before = run.snapshot_hash(original)
    branch = select_rows(original, [0, 1], None)
    assert run.snapshot_hash(branch) == before
    branch.cache.layers[0].keys[0, 0, 0, 0] = 9
    branch.pending[0] += 1
    branch.mailbox[0, 0] += 1
    branch.consumed[0][0] += 1
    assert run.snapshot_hash(original) == before
    assert run.snapshot_hash(branch) != before
