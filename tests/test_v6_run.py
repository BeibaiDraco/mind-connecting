import json

import pytest

from mb.v6_contract import RuntimeSpec
from mb.v6_run import EpisodeLedger, run_synthetic
from mb.v6_tasks import make_episodes


def tree_bytes(path):
    return {str(p.relative_to(path)):p.read_bytes() for p in path.rglob("*") if p.is_file()}


def test_explicit_neutral_key_schema_is_preserved_on_resume(tmp_path):
    directory = tmp_path/"neutral"
    fields = ("episode_id", "policy", "round_id", "side", "qid")
    identity = {"key_fields": fields}
    identity = json.loads(json.dumps(identity))
    row = dict(zip(fields, ("e0", "OFF", 1, 0, "CAP0")))
    row["status"] = "ok"
    ledger = EpisodeLedger(directory, identity, key_fields=fields)
    ledger.write(row); ledger.close()
    before = tree_bytes(directory)
    ledger = EpisodeLedger(directory, identity, resume=True, key_fields=fields)
    ledger.write(row); ledger.close()
    assert tree_bytes(directory) == before
    with pytest.raises(ValueError, match="nonempty"):
        EpisodeLedger(tmp_path/"invalid", identity, key_fields=())
    assert not (tmp_path/"invalid").exists()


def test_synthetic_run_then_noop_resume(tmp_path):
    episodes = make_episodes(1, "development", 1)
    spec = RuntimeSpec(work_tokens=2, preparation_tokens=1, window=2)
    directory = tmp_path/"synthetic"
    first = run_synthetic(directory, episodes, spec, text_episodes={episodes[0].episode_id})
    before = tree_bytes(directory)
    second = run_synthetic(directory, episodes, spec, text_episodes={episodes[0].episode_id}, resume=True)
    assert first == second
    assert tree_bytes(directory) == before
    assert first["records"] == 352 and first["scientific_data"] is False


def test_resume_identity_rejects_before_any_write(tmp_path):
    directory = tmp_path/"run"
    EpisodeLedger(directory, {"source":"original"}).close()
    before = tree_bytes(directory)
    with pytest.raises(ValueError, match="no file was changed"):
        EpisodeLedger(directory, {"source":"changed"}, resume=True)
    assert tree_bytes(directory) == before


def test_successful_rows_immutable_and_corruption_rejected(tmp_path):
    directory = tmp_path/"run"
    identity = {"draft":True}
    ledger = EpisodeLedger(directory, identity)
    rec = {"model_profile":"synthetic","episode_id":"development-0","kind":"natural",
           "policy":"LIVE","checkpoint":0,"arm":"LIVE","version":1,"round_id":1,
           "side":0,"qid":"action","choice":1,"status":"ok"}
    ledger.write(rec)
    ledger.write(rec)
    with pytest.raises(ValueError, match="changed"):
        ledger.write({**rec,"choice":2})
    ledger.close()
    assert len((directory/"records/attempt-001.jsonl").read_text().splitlines()) == 1
    with (directory/"records/attempt-001.jsonl").open("a") as f:
        f.write('{"torn":')
    before = tree_bytes(directory)
    with pytest.raises(ValueError, match="Corrupt retained"):
        EpisodeLedger(directory, identity, resume=True)
    assert tree_bytes(directory) == before


def test_partial_episode_exact_retry_preserves_successes(tmp_path):
    episodes = make_episodes(1,"development",3)
    spec = RuntimeSpec(work_tokens=2,preparation_tokens=0,window=1)
    complete = tmp_path/"complete"
    run_synthetic(complete, episodes, spec)
    identity = json.loads((complete/"identity.json").read_text())
    rows = [json.loads(s) for s in (complete/"records/attempt-001.jsonl").read_text().splitlines()]
    partial = tmp_path/"partial"
    ledger = EpisodeLedger(partial, identity)
    ledger.note({"event":"episode_started","episode_id":episodes[0].episode_id})
    for row in rows[:13]:
        ledger.write(row)
    ledger.close()
    old_bytes = (partial/"records/attempt-001.jsonl").read_bytes()
    result = run_synthetic(partial, episodes, spec, resume=True)
    assert result["records"] == 328
    assert (partial/"records/attempt-001.jsonl").read_bytes() == old_bytes
    assert len((partial/"records/attempt-002.jsonl").read_text().splitlines()) == 315


def test_second_failed_retry_not_automatically_repeated(tmp_path):
    from mb.v6_run import synthetic_identity
    ep = make_episodes(1,"development",2)
    spec = RuntimeSpec(work_tokens=2)
    directory = tmp_path/"failed"
    identity = json.loads(json.dumps(synthetic_identity(ep,spec,"qwen3_4b_instruct_2507",set())))
    ledger = EpisodeLedger(directory,identity)
    for _ in range(2):
        ledger.note({"event":"episode_started","episode_id":ep[0].episode_id})
    ledger.close()
    before = tree_bytes(directory)
    with pytest.raises(RuntimeError,match="retry are exhausted"):
        run_synthetic(directory,ep,spec,resume=True)
    assert tree_bytes(directory) == before


@pytest.mark.parametrize("corruption", ["unexpected", "nonfinite"])
def test_partial_ledger_rejected_before_any_append(tmp_path, corruption):
    episodes = make_episodes(1,"development",10)
    spec = RuntimeSpec(work_tokens=2,preparation_tokens=0,window=1)
    path = tmp_path/"synthetic"
    run_synthetic(path,episodes,spec)
    shard = path/"records/attempt-001.jsonl"
    row = json.loads(shard.read_text().splitlines()[0])
    if corruption == "unexpected":
        row["qid"] = "not_planned"
    else:
        row["legal_mass"] = float("nan")
    shard.write_text(json.dumps(row)+"\n")
    before = tree_bytes(path)
    with pytest.raises(ValueError):
        run_synthetic(path,episodes,spec,resume=True)
    assert tree_bytes(path) == before


def test_native_archive_io_contract_with_primitive_fixture(tmp_path, monkeypatch):
    """Exercise files/identities without torch or any native inference."""
    import copy
    import sys
    from types import SimpleNamespace
    import mb.v6_native as native
    from mb.v6_contract import Export
    from mb.v6_runtime import EpisodeRunner
    from mb.v6_run import NativeArchiveWriter, SyntheticBackend

    class ArchiveFixture(SyntheticBackend):
        def dump_state(self, state):
            return copy.deepcopy(state)
        def load_state(self, state):
            return copy.deepcopy(state)
        def dump_export(self, export):
            return {**export.identity(),"payload":copy.deepcopy(export.payload)}
        def load_export(self, payload):
            return Export(**payload)

    def save(payload, handle):
        handle.write(json.dumps(payload,sort_keys=True).encode())
    def load(path, *, map_location, weights_only):
        assert map_location == "cpu" and weights_only is True
        return json.loads(path.read_bytes())
    monkeypatch.setattr(native,"NativeBackend",ArchiveFixture)
    monkeypatch.setitem(sys.modules,"torch",SimpleNamespace(save=save,load=load))
    backend = ArchiveFixture()
    archive = NativeArchiveWriter(tmp_path/"archives",backend,{"frozen":False})
    spec = RuntimeSpec(work_tokens=2,preparation_tokens=0,window=1)
    runner = EpisodeRunner(backend,spec,"qwen3_4b_instruct_2507",artifact_sink=archive)
    ep = make_episodes(1,"development",2)[0]
    runner.run_episode(ep)
    assert len(archive.index) == 16
    for filename in archive.index:
        archive.load(filename)
    before = tree_bytes(tmp_path/"archives")
    resumed = NativeArchiveWriter(tmp_path/"archives",backend,{"frozen":False},resume=True)
    runner.artifact_sink = resumed
    runner.run_episode(ep)
    assert tree_bytes(tmp_path/"archives") == before
    filename = next(iter(archive.index))
    (tmp_path/"archives"/filename).write_bytes(b"tampered")
    with pytest.raises(ValueError,match="file hash differs"):
        archive.load(filename)
    before = tree_bytes(tmp_path/"archives")
    with pytest.raises(ValueError,match="integrity failed before append"):
        NativeArchiveWriter(tmp_path/"archives",backend,{"frozen":False},resume=True)
    assert tree_bytes(tmp_path/"archives") == before
