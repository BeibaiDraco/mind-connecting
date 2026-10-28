"""V7 variance-only step (protocol V7 §7 step 4) on synthetic records."""

from __future__ import annotations

import json
import math
import shutil
import statistics
import subprocess

import pytest

from mb import run, v7_tasks as material
from v7_synthetic import default_choice, load_script, records

variance = load_script("v7_variance")
EPISODES = material.make_episodes(8, "v7_dev", "base")
QIDS = ("START", "USE")


def choose(arm, qid, i, rotation):
    if qid not in QIDS:
        return default_choice(qid)
    slot = EPISODES[i].base.rotations.index(rotation)
    if qid == "START":
        if arm == "orig_w2":
            return "partner"
        if arm == "trans_w2":  # episode partner rates 1, ½, 0, 1, ½, 0, 1, ½
            return "partner" if i % 3 == 0 or (i % 3 == 1 and slot == 0) else "own"
    if qid == "USE":
        if arm in ("orig_w2", "orig_w2_cf"):
            return "fact" if arm == "orig_w2" else "cf"
        if arm == "trans_w2":
            return "fact" if i < 6 else "other"
        if arm == "trans_w2_cf":
            return "cf" if i % 2 == 0 and slot == 0 else "other"
    return default_choice(qid)


def expected():
    p1 = [[0, -0.5, -1][i % 3] for i in range(8)]
    t_trans = [((1 if i < 6 else 0) + (0.5 if i % 2 == 0 else 0)) / 2 for i in range(8)]
    d_use = [t - 1 for t in t_trans]
    return statistics.stdev(p1), statistics.stdev(d_use)


def test_paired_sds_and_implied_precision():
    out = variance.summarize(records(EPISODES, choose, QIDS))
    sd_p1, sd_use = expected()
    assert out["n_episodes"] == 8 and out["planned_n"] == 600
    for name, sd in (("P1", sd_p1), ("D_use", sd_use)):
        assert out[name]["paired_sd"] == pytest.approx(sd)
        assert out[name]["half_width_points_at_planned_n"] == pytest.approx(100 * 1.96 * sd / math.sqrt(600), rel=1e-4)
        assert out[name]["n_for_5_point_half_width"] == math.ceil((variance.Z95 * sd / 0.05) ** 2)


def test_output_holds_no_means_differences_or_intervals():
    out = variance.summarize(records(EPISODES, choose, QIDS))
    assert set(out) == {"n_episodes", "planned_n", "P1", "D_use"}
    for name in ("P1", "D_use"):
        assert set(out[name]) == {"paired_sd", "half_width_points_at_planned_n", "n_for_5_point_half_width"}


class Guarded(dict):
    def __getitem__(self, key):
        if key not in ("arm_id", "qid"):
            raise AssertionError(f"variance step read {key}")
        return dict.__getitem__(self, key)


def test_only_the_co_primary_arms_and_questions_are_read():
    wanted = {("START", "orig_w2"), ("START", "trans_w2"), ("USE", "orig_w2"), ("USE", "orig_w2_cf"),
              ("USE", "trans_w2"), ("USE", "trans_w2_cf")}
    rows = [r if (r["qid"], r["arm_id"]) in wanted else Guarded(r) for r in records(EPISODES, choose)]
    assert variance.summarize(rows)["P1"]["paired_sd"] == pytest.approx(expected()[0])


def test_missing_counterfactual_episode_is_rejected():
    rows = records(EPISODES, choose, QIDS)
    first = EPISODES[0].episode_id
    with pytest.raises(ValueError):
        variance.summarize([r for r in rows if not (r["arm_id"] == "trans_w2_cf" and r["episode_id"] == first)])


def test_refuses_to_run_before_the_parameter_seal(tmp_path):
    assert not subprocess.run(["git", "tag", "-l", variance.SEAL_TAG], cwd=run.REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
    with pytest.raises(SystemExit, match="parameter seal"):
        variance.main([str(tmp_path), str(tmp_path / "out.json")])
    assert not (tmp_path / "out.json").exists()


def test_seal_check_requires_byte_identical_sealed_files(tmp_path):
    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=tmp_path, check=True,
                       capture_output=True)

    for name in variance.SEALED_FILES:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(run.REPO_ROOT / name, tmp_path / name)
    git("init", "-q")
    git("add", ".")
    git("commit", "-q", "-m", "seal")
    git("tag", variance.SEAL_TAG)
    assert len(variance.require_seal(tmp_path)) == 40
    (tmp_path / variance.SEALED_FILES[1]).write_text("# changed\n")
    with pytest.raises(SystemExit, match="differs from its sealed version"):
        variance.require_seal(tmp_path)


def test_main_requires_passed_consumable_gates(tmp_path, monkeypatch):
    monkeypatch.setattr(variance, "require_seal", lambda: "0" * 40)
    (tmp_path / "v7_pilot_gates.json").write_text(json.dumps({"consumable": True, "all_pass": False}))
    with pytest.raises(SystemExit, match="gates all passed"):
        variance.main([str(tmp_path), str(tmp_path / "out.json")])
    assert not (tmp_path / "out.json").exists()
