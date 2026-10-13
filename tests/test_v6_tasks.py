"""Pure task, privacy and local tokenizer checks; no weights or model calls."""

from dataclasses import FrozenInstanceError, replace
from collections import Counter
from itertools import permutations, product
import json
import subprocess
import sys

import pytest

from mb import v6_tasks as t


@pytest.fixture
def episode():
    return t.make_episodes(1, "v6_unit", seed=17)[0]


def before(ep, round_id, actions=(None, None)):
    world = t.initial_world(ep)
    for r in range(1, round_id):
        world = t.transition(t.event_world(ep, world, r), actions)
    return world


def test_no_torch_or_transformers_import():
    script = "import sys; import mb.v6_tasks; assert 'torch' not in sys.modules; assert 'transformers' not in sys.modules"
    subprocess.run([sys.executable, "-c", script], check=True, capture_output=True)


def test_truth_table_and_actual_transition_exhaustive():
    for goal, partner_bit in product(range(4), range(2)):
        assert t.correct_action(goal, partner_bit) == ((0, 1, 2, 3), (2, 3, 0, 1))[partner_bit][goal]
    for beacons, actions in product(product(range(2), repeat=2), product((*range(4), None), repeat=2)):
        world = t.World(beacons, (0, 1), 1)
        result = t.transition(world, actions)
        assert result.beacons == tuple(beacons[k] if a is None else (0, 1, 1, 0)[a]
                                      for k, a in enumerate(actions))
        assert result.actions == (actions,)
        assert result.round_id == 1 and world.actions == ()


def test_generation_reproducibility_namespaces_and_balance():
    eps = t.make_episodes(240, "v6_confirm", 23)
    assert eps == t.make_episodes(240, "v6_confirm", 23)
    assert eps != t.make_episodes(240, "v6_confirm", 24)
    other = t.make_episodes(240, "v6_validity", 23)
    assert {e.episode_id for e in eps}.isdisjoint(e.episode_id for e in other)
    assert {e.seed for e in eps}.isdisjoint(e.seed for e in other)
    report = t.balance_report(eps)
    assert report["exact_N240_initial_marginals"]
    assert set(report["early_side"].values()) == {120}
    assert set(report["initial_goals_A"].values()) == {60}
    assert set(report["initial_goals_B"].values()) == {60}
    assert set(report["literal_initial_goals_A"].values()) == {60}
    assert set(report["literal_initial_goals_B"].values()) == {60}
    assert report["status"] == "proposed_not_frozen"
    assert not t.balance_report(eps[:60])["exact_N240_initial_marginals"]
    # Equality of all full joint cells is neither asserted nor fabricated.
    assert report["full_initial_joint"] and report["updated_goals"]


def test_six_round_event_goals_and_local_actions(episode):
    world = t.initial_world(episode)
    for r in range(1, 7):
        previous = world
        world = t.event_world(episode, world, r)
        if r in (2, 5):
            side = t.focal_side(episode, r)
            assert world.beacons[side] == previous.beacons[side] ^ 1
            assert world.beacons[1-side] == previous.beacons[1-side]
            assert world.goals[side] == previous.goals[side]
            assert world.goals[1-side] not in previous.goals
        else:
            assert world.beacons == previous.beacons and world.goals == previous.goals
        assert len(world.actions) == r-1
        world = t.transition(world, (r % 4, None))
        assert len(world.actions) == r
    assert t.focal_side(episode, 2) == t.focal_side(episode, 3)
    assert t.focal_side(episode, 5) == t.focal_side(episode, 6) == 1-t.focal_side(episode, 2)
    with pytest.raises(FrozenInstanceError):
        world.round_id = 1


def test_pulse_changes_only_focal_bit_and_keeps_new_responder_goal(episode):
    for checkpoint in (2, 5):
        pre = before(episode, checkpoint, (3, 2))
        zero = t.event_world(episode, pre, checkpoint, False)
        one = t.event_world(episode, pre, checkpoint, True)
        focal = t.focal_side(episode, checkpoint)
        assert zero.goals == one.goals
        assert zero.actions == one.actions == pre.actions
        assert zero.beacons[focal] ^ one.beacons[focal] == 1
        assert zero.beacons[1-focal] == one.beacons[1-focal]
        assert one == t.event_world(episode, pre, checkpoint)
        messages0 = t.round_prompts(episode, zero, checkpoint, t.updated_sides(episode, checkpoint))
        messages1 = t.round_prompts(episode, one, checkpoint, t.updated_sides(episode, checkpoint))
        assert messages0[1-focal] == messages1[1-focal]
        assert messages0[focal] != messages1[focal]


def test_goal_probe_fixed_world_and_shared_fresh_row(episode):
    for checkpoint in (3, 6):
        pre = before(episode, checkpoint)
        zero = t.goal_probe_world(episode, pre, checkpoint, False)
        one = t.goal_probe_world(episode, pre, checkpoint, True)
        focal = t.focal_side(episode, checkpoint)
        assert zero.beacons == one.beacons == pre.beacons
        assert zero.actions == one.actions == pre.actions
        assert zero.round_id == one.round_id == checkpoint
        assert zero.goals[1-focal] == one.goals[1-focal]
        assert len({zero.goals[focal], one.goals[focal], one.goals[1-focal]}) == 3
        row = episode.transfer_rows[0 if checkpoint == 3 else 1]
        for side in range(2):
            q0 = t.question(episode, zero, side, "transfer_action", checkpoint)
            q1 = t.question(episode, one, side, "transfer_action", checkpoint)
            assert q0.text == q1.text and q0.candidates == q1.candidates
            assert q1.correct == row[one.goals[side]]
            assert t.BEACON_NAMES[one.beacons[1-side]] in q1.text
            for goal in range(4):
                assert f"{episode.goal_names[goal]} -> {episode.transfer_names[row[goal]]}" in q1.text
        assert all(name not in episode.action_names for name in episode.transfer_names)


def test_pulse_candidates_use_oracle_not_real_branch_outputs():
    for ep in t.make_episodes(96, "v6_pulse_test", 7):
        for checkpoint in (2, 5):
            pre = before(ep, checkpoint, (None, None))
            result = t.pulse_candidates(ep, pre, checkpoint)
            focal = t.focal_side(ep, checkpoint)
            for index, changed in enumerate((False, True)):
                current = t.event_world(ep, pre, checkpoint, changed)
                action_j = t.correct_action(current.goals[1-focal], current.beacons[focal])
                # Do not use transition() to independently check the fixed candidates.
                j_next = 0 if action_j in (0, 3) else 1
                action_i = current.goals[focal] if j_next == 0 else (current.goals[focal] + 2) % 4
                assert result["responder"][index] == action_j
                assert result["initiator"][index] == action_i
            assert len(set(result["responder"])) == len(set(result["initiator"])) == 2


def test_messages_and_device_transition_have_no_partner_side_channel(episode):
    world = t.event_world(episode, t.initial_world(episode), 1)
    for side, own_update in product(range(2), (False, True)):
        flags = tuple(k == side and own_update for k in range(2))
        original = t.round_prompts(episode, world, 1, flags)[side]
        for partner_bit, partner_goal in product(range(2), range(4)):
            beacons, goals = list(world.beacons), list(world.goals)
            beacons[1-side], goals[1-side] = partner_bit, partner_goal
            other = replace(world, beacons=tuple(beacons), goals=tuple(goals))
            assert t.round_prompts(episode, other, 1, flags)[side] == original
            for own_action, partner_action in product((*range(4), None), repeat=2):
                actions = (own_action, partner_action) if side == 0 else (partner_action, own_action)
                assert t.transition(other, actions).beacons[side] == (
                    world.beacons[side] if own_action is None else t.NEXT_BEACON[own_action])
    system, private = t.initial_prompts(episode)
    assert "correct" not in system.lower() and "reward" not in system.lower()
    for side in range(2):
        assert f"You are participant {t.ROLES[side]}." in private[side]
        assert episode.goal_names[episode.original_goals[1-side]] not in private[side]
        assert "initial beacon" in private[side]


def test_question_semantics_not_option_index_and_no_answer_leak(episode):
    world = t.event_world(episode, t.initial_world(episode), 1)
    for side, goal, otherbit in product(range(2), range(4), range(2)):
        goals, beacons = list(world.goals), list(world.beacons)
        goals[side], beacons[1-side] = goal, otherbit
        changed = replace(world, goals=tuple(goals), beacons=tuple(beacons))
        q = t.question(episode, changed, side, "action")
        assert q.correct == t.correct_action(goal, otherbit)
        assert q.text == t.question(episode, world, side, "action").text
        assert q.correct_label == str(q.candidates.index(q.correct)+1)
        assert "Dim" not in q.text and "Bright" not in q.text
        for label, meaning in zip(t.LABELS, q.candidates):
            assert f"{label}. {episode.action_names[meaning]}" in q.text
        partner_q = t.question(episode, changed, side, "partner_beacon")
        assert partner_q.correct == otherbit
        assert set(partner_q.candidates) == {0, 1, 2, 3}
        assert "Unknown" in partner_q.text and "Another beacon" in partner_q.text


def test_original_latest_and_partner_records_remain_distinct(episode):
    world = t.event_world(episode, before(episode, 6), 6)
    for side in range(2):
        assert t.question(episode, world, side, "original_goal").correct == episode.original_goals[side]
        assert t.question(episode, world, side, "latest_goal").correct == world.goals[side]
        assert t.question(episode, world, side, "partner_goal").correct == world.goals[1-side]
        assert "before any updates" in t.question(episode, world, side, "original_goal").text
        assert "most recent authorized" in t.question(episode, world, side, "latest_goal").text


def test_codebook_permutations_preserve_visible_physics(episode):
    for names in permutations(t.ACTION_NAMES):
        ep = replace(episode, action_names=names)
        system, _ = t.initial_prompts(ep)
        for action in range(4):
            assert f"{names[action]} -> {t.BEACON_NAMES[t.NEXT_BEACON[action]]}" in system
        for beacon in range(2):
            expected = t.BEACON_NAMES[beacon] + " | " + " | ".join(
                names[t.correct_action(goal, beacon)] for goal in range(4))
            assert expected in system


@pytest.mark.parametrize("value", [-1, 4, 1.5, True, "1"])
def test_bad_action_rejected_not_coerced(episode, value):
    world = t.event_world(episode, t.initial_world(episode), 1)
    with pytest.raises(ValueError):
        t.transition(world, (value, 0))


def test_invalid_sequencing_and_materials_refused(episode):
    world = t.initial_world(episode)
    with pytest.raises(ValueError):
        t.transition(world, (0, 0))
    with pytest.raises(ValueError):
        t.event_world(episode, world, 2)
    current = t.event_world(episode, world, 1)
    with pytest.raises(ValueError):
        t.event_world(episode, current, 2)
    completed = t.transition(current, (None, 0))
    with pytest.raises(ValueError):
        t.transition(completed, (0, 0))
    with pytest.raises(ValueError):
        t.question(episode, completed, 0, "action")
    with pytest.raises(ValueError):
        t.question(episode, current, 0, "transfer_action", 3)
    with pytest.raises(ValueError):
        t.event_world(episode, world, 1, False)
    with pytest.raises(ValueError):
        t.round_prompts(episode, current, 1, (0, 1))
    with pytest.raises(ValueError):
        replace(episode, updated_goals=episode.original_goals)
    with pytest.raises(ValueError):
        replace(episode, initial_beacons=(0, 2))
    with pytest.raises(ValueError):
        replace(episode, option_orders=((0, 0, 1, 2),)*4)


def test_serialization_identity_and_write_once(tmp_path):
    episodes = t.make_episodes(8, "v6_files", 100)
    path = tmp_path / "materials.json"
    digest = t.write_materials(path, episodes)
    assert digest == t.materials_sha256(episodes)
    assert t.write_materials(path, episodes) == digest
    assert t.load_materials(path) == episodes
    assert json.loads(t.material_json(episodes))["status"] == "proposed_not_frozen"
    with pytest.raises(ValueError):
        t.write_materials(path, episodes[::-1])
    with pytest.raises(ValueError):
        t.material_json(episodes + episodes[:1])
    data = t.episode_to_dict(episodes[0])
    assert t.episode_from_dict(data) == episodes[0]
    data["new_field"] = True
    with pytest.raises(ValueError):
        t.episode_from_dict(data)


def test_text_subset_exact_material_only_balance_and_order_invariance():
    episodes = t.make_episodes(240, "v6_text_selection", 0)
    selected = t.select_text_subset(episodes)
    assert selected is not None and len(selected) == 60
    assert selected == t.select_text_subset(reversed(episodes))
    assert set(Counter(ep.original_goals for ep in selected).values()) == {5}
    assert set(Counter(ep.early_side for ep in selected).values()) == {30}
    assert set(Counter(ep.initial_beacons for ep in selected).values()) == {15}
    cells = Counter((ep.early_side, ep.initial_beacons) for ep in selected)
    assert len(cells) == 8 and set(cells.values()) <= {7, 8}
    for side in range(2):
        assert set(Counter(ep.goal_names[ep.original_goals[side]] for ep in selected).values()) == {15}
    assert {ep.episode_id for ep in selected} <= {ep.episode_id for ep in episodes}


def test_text_subset_refuses_infeasible_or_undeclared_relaxation():
    episodes = t.make_episodes(240, "v6_text_failure", 0)
    assert t.select_text_subset(episodes[:4]) is None
    assert t.select_text_subset([ep for ep in episodes if ep.early_side == 0]) is None
    with pytest.raises(ValueError, match="multiple of 12"):
        t.select_text_subset(episodes, n=61)


@pytest.mark.parametrize("profile_key", ["qwen3_4b_instruct_2507", "llama31_8b_instruct"])
def test_real_local_tokenizers_only(profile_key):
    pytest.importorskip("transformers")
    from mb.chat import load_tokenizer
    from mb.model_profiles import resolve_profile
    profile = resolve_profile(profile_key)
    if not (profile.tokenizer_dir / "tokenizer.json").is_file():
        pytest.skip("local pinned tokenizer assets unavailable; no download")
    report = t.audit_tokenizer(load_tokenizer(profile=profile), t.make_episodes(1, "v6_tokens", 0))
    assert report["passed"], report["errors"]
    assert report["native_answer_prefixes"] == 64
    assert report["label_append_checks"] == 256
    assert report["status"] == "local_tokenizer_audit_not_model_acceptance"
