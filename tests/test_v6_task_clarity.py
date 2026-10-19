"""Semantic equivalence, allocation and contamination checks; no model execution."""

from collections import Counter
from copy import deepcopy
from dataclasses import replace
from itertools import permutations
import re

import pytest

from mb import v6_task_clarity as c, v6_tasks as t
from mb.v6_run import SyntheticBackend


def test_allocation_balance_identity_and_actual_answers():
    cases = c.make_short_cases()
    assert cases == c.make_short_cases() and len(cases) == 64
    assert len({x.episode.episode_id for x in cases}) == 64
    assert Counter(x.book for x in cases) == {b: 8 for b in range(8)}
    for goal in t.GOAL_NAMES:
        for partner in (0, 1):
            subset = [x for x in cases if x.episode.goal_names[x.world.goals[x.side]] == goal
                      and x.world.beacons[1-x.side] == partner]
            assert Counter((x.side, x.world.beacons[x.side] == partner) for x in subset) == {
                (s, same): 2 for s in (0, 1) for same in (False, True)}
    assert Counter(c.question(x.episode, x.world, x.side, "P0").correct_label for x in cases) == {
        label: 16 for label in t.LABELS}
    history = c.make_history_episodes()
    assert not {e.episode_id for e in history} & {x.episode.episode_id for x in cases}
    assert Counter((e.early_side, e.initial_beacons) for e in history) == {
        (s, (a, b)): 1 for s in (0, 1) for a in (0, 1) for b in (0, 1)}
    for side in (0, 1):
        assert Counter(e.goal_names[e.original_goals[side]] for e in history) == {g: 2 for g in t.GOAL_NAMES}


def test_original_prompt_and_answers_byte_identical():
    for case in c.make_short_cases():
        ep, w, side = case.episode, case.world, case.side
        assert c.initial_prompts(ep, "P0") == t.initial_prompts(ep)
        assert c.question(ep, w, side, "P0") == t.question(ep, w, side, "action")
        for variant in c.VARIANTS:
            assert c.initial_prompts(ep, variant)[1] == t.initial_prompts(ep)[1]
            for qid in c.QIDS:
                q = c.question(ep, w, side, variant, qid)
                original = t.question(ep, w, side, "latest_goal" if qid == "latest_goal" else "action")
                assert (q.correct, q.candidates) == (original.correct, original.candidates)
                assert q.text.endswith(original.text.split("\n", 1)[1])


def test_explicit_rules_match_parsed_table_under_every_name_permutation():
    base = c.make_short_cases()[0].episode
    for actions in permutations(t.ACTION_NAMES):
        for goals in permutations(t.GOAL_NAMES):
            ep = replace(base, action_names=actions, goal_names=goals)
            lines = c.action_table(ep, "P0").splitlines()
            header, dim, bright = [line.split(" | ")[1:] for line in lines]
            flat = dict((g, (d, b)) for g, d, b in re.findall(
                r"(G[0-3]): if the OTHER participant's current beacon is Dim, press (\w+); "
                r"if it is Bright, press (\w+)\.", c.action_table(ep, "P2")))
            assert flat == {g: (dim[i], bright[i]) for i, g in enumerate(header)}
            assert c.initial_prompts(ep, "P2")[0].split("Own-device transition table:\n")[1] == (
                t.initial_prompts(ep)[0].split("Own-device transition table:\n")[1])


def test_private_prompts_and_real_action_questions_do_not_disclose_partner():
    ep = c.make_history_episodes()[0]
    other = replace(ep, initial_beacons=(ep.initial_beacons[0], 1-ep.initial_beacons[1]))
    for v in c.VARIANTS:
        assert c.initial_prompts(ep, v)[1][0] == c.initial_prompts(other, v)[1][0]
        w = t.event_world(ep, t.initial_world(ep), 1)
        changed = replace(w, beacons=(w.beacons[0], 1-w.beacons[1]))
        assert c.question(ep, w, 0, v).text == c.question(ep, changed, 0, v).text
        assert c.question(ep, w, 0, v).correct != c.question(ep, changed, 0, v).correct
        assert c.question(ep, w, 0, v, "fullinfo_action").text != c.question(ep, changed, 0, v, "fullinfo_action").text


@pytest.mark.parametrize("variant", c.VARIANTS)
def test_short_collection_is_complete_fresh_and_not_scientific(variant):
    class NoWork(SyntheticBackend):
        def step(self, *args):
            raise AssertionError("Short cases must not generate work tokens")
        def commit_answer(self, *args):
            raise AssertionError("Short answers must not enter another case")
    rows = c.collect_short(NoWork(), variant, "reference")
    summary = c.validate_short(rows, variant, "reference")
    assert summary["complete"] and summary["synthetic"]
    assert summary["scientific_admission"] is False and summary["automatic_continuation"] is False
    broken = deepcopy(rows); broken[0]["choice"] = (broken[0]["choice"]+1) % 4
    with pytest.raises(ValueError, match="scoring"):
        c.validate_short(broken, variant, "reference")
    with pytest.raises(ValueError):
        c.validate_short(rows[:-1], variant, "reference")


def test_history_clock_actual_commits_and_discarded_fact_queries():
    class Tracking(SyntheticBackend):
        def __init__(self):
            super().__init__(invalid_every=5); self.steps = 0; self.committed = []
        def step(self, state, foreign, gain):
            assert foreign == () and gain == 0
            self.steps += 1
            return super().step(state, foreign, gain)
        def commit_answer(self, probe, foreign, gain):
            self.committed.append(deepcopy(probe.state))
            return super().commit_answer(probe, foreign, gain)
    backend = Tracking(); snapshots = []
    ep = c.make_history_episodes()[0]
    rows = c.collect_history(backend, ep, "P1", "optimized", history_sink=snapshots.append)
    assert backend.steps == 2*16 + 6*2*64 and len(backend.committed) == 12
    assert len(snapshots) == 7
    assert c.validate_history(rows, ep, "P1", "optimized")["complete"]
    for state in backend.committed:
        user_text = "\n".join(x[1] for x in state["history"] if x[0] == "user")
        assert "Current authorized record" not in user_text
        assert "According to the most recent" not in user_text
        assert "Action table (unchanged rules)" not in user_text
    assert any(r["choice"] is None for r in rows)
    broken = deepcopy(rows)
    old = broken[-1]["world"]["beacons"]
    broken[-1]["world"]["beacons"] = (1-old[0], old[1])
    with pytest.raises(ValueError, match="world"):
        c.validate_history(broken, ep, "P1", "optimized")


def test_parent_mutation_is_rejected_before_recording():
    class Mutating(SyntheticBackend):
        def probe(self, state, *args):
            p = super().probe(state, *args)
            state["history"].append(("unexpected",))
            return p
    rows = []
    with pytest.raises(RuntimeError, match="parent"):
        c.collect_short(Mutating(), "P1", "reference", sink=rows.append)
    assert rows == []


def test_wrong_variants_materials_and_missing_real_sinks_fail_before_use():
    with pytest.raises(ValueError):
        c.collect_short(SyntheticBackend(), "P9", "reference")
    with pytest.raises(ValueError):
        c.collect_history(SyntheticBackend(), c.make_short_cases()[0].episode, "P0", "reference")
    class Unbound:
        kind = "native"
    with pytest.raises(ValueError, match="Qwen"):
        c.collect_short(Unbound(), "P0", "reference")


def test_preparation_bundle_is_inert_bound_and_write_once(tmp_path):
    import hashlib
    import json
    from pathlib import Path
    import runpy
    prepare = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/prepare_v6_task_clarity.py"))["prepare"]
    target = tmp_path/"prepared"
    manifest = prepare(target)
    assert manifest["gpu_launch_authorized"] is False
    assert manifest["history_variant"] is None and manifest["thresholds_ratified"] is False
    assert manifest["short_scored_answers"] == manifest["history_readouts"] == 384
    for name, pin in manifest["files"].items():
        assert hashlib.sha256((target/name).read_bytes()).hexdigest() == pin["sha256"]
    assert len(json.loads((target/"short_inputs.json").read_text())) == 192
    before = (target/"manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        prepare(target)
    assert (target/"manifest.json").read_bytes() == before


def test_actual_local_tokenizer_renders_all_short_prefixes_and_answer_ids():
    from mb import chat
    from mb.model_profiles import QWEN
    from mb.v6_native import NativeTokens
    if not QWEN.tokenizer_dir.exists():
        pytest.skip("Local tokenizer absent; no download")
    tok = chat.load_tokenizer(profile=QWEN)
    native = NativeTokens.from_tokenizer(tok)
    labels = native.choice_ids(t.LABELS)
    for case in c.make_short_cases():
        for variant in c.VARIANTS:
            system, users = c.initial_prompts(case.episode, variant)
            q = c.question(case.episode, case.world, case.side, variant, "fullinfo_action")
            prefix = (*native.initial(system, users[case.side]), *native.close_ids, *native.user_turn(q.text))
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": users[case.side]},
                        {"role": "assistant", "content": ""},
                        {"role": "user", "content": q.text}]
            assert prefix == tuple(chat.native_conversation(tok, messages, add_generation_prompt=True))
            rendered = tok.decode(prefix, skip_special_tokens=False, clean_up_tokenization_spaces=False)
            for label, token in zip(t.LABELS, labels):
                assert chat.encode(tok, rendered+label) == [*prefix, token]
