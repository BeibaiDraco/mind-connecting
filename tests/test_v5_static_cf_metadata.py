"""CF metadata follows the real runner's donor view without changing physical options."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from mb import chat, model_profiles, tasks, v5_static as study
from mb.run import Runner, StageConfig


@pytest.fixture
def produced_run(tmp_path, monkeypatch):
    # Token serialization is outside this metadata test; all question/record assembly is real.
    monkeypatch.setattr(chat, "readout_suffix", lambda tok, content: [1])
    cfg = StageConfig(stage=study.PREFIX + "validity", tag="metadata-test",
                      split=study.PREFIX + "validity", n_episodes=2,
                      model_profile=study.PROFILE, qids=list(study.FORMAL_QIDS),
                      arms=[study.arm("C0"), study.arm("ONE"), study.arm("CF"),
                            study.arm("STATIC", 16, 0.5)])
    runner = Runner.__new__(Runner)
    runner.cfg, runner.tok = cfg, object()
    runner.template_hash = "synthetic-template"
    runner.profile = model_profiles.resolve_profile(cfg.model_profile)
    runner.writer = SimpleNamespace(path=tmp_path / "records" / "attempt-000.jsonl")
    runner.pass_index = 0
    identity = {"stage_config": json.loads(json.dumps(cfg.resolved())), "limit": None,
                "template_hash": runner.template_hash, "model_revision": runner.profile.revision,
                "calibration": {"16": {"hash": "synthetic-calibration"}}}
    episodes = tasks.make_episodes(cfg.n_episodes, cfg.split, cfg.seed)
    records, hashes = [], {}
    for arm in cfg.arm_configs():
        cal_hash = "synthetic-calibration" if arm.needs_calibration else "none"
        hashes[arm.name] = arm.config_hash(cal_hash, "none", runner.template_hash)
        views = runner._donors(arm, episodes)
        for index, recipient, question in runner._pending_questions(arm, episodes, views, set(), set()):
            ep = episodes[index]
            row = runner._base_record(arm, {"calibration_hash": cal_hash}, hashes[arm.name],
                                      "none", ep, recipient, question)
            if arm.donor_variant:
                row.update(donor_rule=views[index].rule.B, donor_word=views[index].word.B,
                           cf_r0_rule=ep.rule.B, cf_r1_rule=ep.rule.spare,
                           cf_r0_word=ep.word.B, cf_r1_word=ep.word.spare)
            row.update(status="ok", label_logits=[0.0] * 4,
                       label_logprobs=[-2.0] * 4, label_mass=0.9)
            records.append(row)
    for name, value in (("identity.json", identity), ("arm_hashes.json", hashes),
                        ("manifest.json", {"smoke": False})):
        (tmp_path / name).write_text(json.dumps(value))
    runner.writer.path.parent.mkdir()

    def write():
        runner.writer.path.write_text("".join(json.dumps(r) + "\n" for r in records))

    write()
    return tmp_path, cfg, episodes, records, write


def test_runner_cf_records_pass_with_unchanged_physical_questions(produced_run):
    path, cfg, _, records, _ = produced_run
    checked, report = study._checked_records(path, cfg, {"status": "complete"})
    assert report["consumable"] and len(checked) == 2 * 4 * len(cfg.qids) * 2
    ordinary = {(r["episode_id"], r["qid"], r["rotation_id"]): r
                for r in records if r["condition"] == "ONE"}
    for row in (r for r in records if r["condition"] == "CF"):
        base = ordinary[row["episode_id"], row["qid"], row["rotation_id"]]
        assert (row["text_hash"], row["options"]) == (base["text_hash"], base["options"])
        if row["qid"] in ("CAP0", "CAP1"):
            assert row["label_meaning"] == base["label_meaning"]
        else:
            assert row["label_meaning"] != base["label_meaning"]
            for physical, meaning in zip(row["options"], row["label_meaning"]):
                kind = "word" if row["qid"] in ("WORD", "WORD_R", "ACC_WORD") else "rule"
                if physical == row[f"cf_r1_{kind}"]:
                    assert meaning == "partner"
                if physical == row[f"cf_r0_{kind}"]:
                    assert meaning == ("distractor" if kind == "word" else "unused")


@pytest.mark.parametrize("qid", ["ACC_RULE", "ACC_WORD"])
@pytest.mark.parametrize("condition", ["CF", "ONE"])
def test_original_and_cf_meanings_are_not_interchangeable(produced_run, qid, condition):
    path, cfg, episodes, records, write = produced_run
    row = next(r for r in records if r["condition"] == condition and r["qid"] == qid)
    ep = next(ep for ep in episodes if ep.episode_id == row["episode_id"])
    wrong_ep = ep if condition == "CF" else tasks.make_donor_variant(ep, "CF").donor_episode
    row["label_meaning"] = list(tasks._question_body(wrong_ep, "A", qid, row["rotation_id"])[2])
    write()
    with pytest.raises(ValueError, match="raw question, physical content or identity"):
        study._checked_records(path, cfg, {"status": "complete"})


@pytest.mark.parametrize("field", ["options", "text_hash", "cf_r0_rule", "cf_r1_rule",
                                    "cf_r0_word", "cf_r1_word"])
def test_cf_repair_still_rejects_physical_metadata_corruption(produced_run, field):
    path, cfg, _, records, write = produced_run
    row = next(r for r in records if r["condition"] == "CF" and r["qid"] == "ACC_RULE")
    if field == "options":
        row[field] = row[field][1:] + row[field][:1]
    else:
        row[field] = "tampered"
    write()
    with pytest.raises(ValueError, match="raw question, physical content or identity"):
        study._checked_records(path, cfg, {"status": "complete"})
