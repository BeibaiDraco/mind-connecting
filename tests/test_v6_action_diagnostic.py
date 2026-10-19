"""Independent rendered-rule checks for the finite diagnostic interventions."""
from collections import Counter
import re
import pytest
from mb import v6_action_diagnostic as d, v6_task_clarity as c, v6_tasks as t


def test_exposed_fixed_scope_and_original_anchor():
    items = d.materials()
    assert len(items) == 320 and Counter(x.arm for x in items) == {a: 64 for a in d.ARMS}
    for case in c.make_short_cases():
        x = d.make_item(case, "joint_p2")
        assert x.system == c.initial_prompts(case.episode, "P2")[0]
        assert x.question == c.question(case.episode, case.world, case.side, "P2", "fullinfo_action").text
        assert {z.case_id for z in items} == {v.episode.episode_id for v in c.make_short_cases()}


def test_rule_and_button_oracles_against_rendered_original_table():
    for case in c.make_short_cases():
        ep, w, s = case.episode, case.world, case.side
        lines = c.action_table(ep, "P0").splitlines()
        names = lines[0].split(" | ")[1:]
        rules = {name: tuple(lines[b+1].split(" | ")[i+1] for b in (0, 1))
                 for i, name in enumerate(names)}
        pair = rules[ep.goal_names[w.goals[s]]]
        action = pair[w.beacons[1-s]]
        for arm in d.ARMS:
            x = d.make_item(case, arm)
            assert x.private == c.initial_prompts(ep, "P2")[1][s]
            label = t.LABELS[x.candidates.index(x.correct)]
            line = next(line for line in x.question.splitlines() if line.startswith(label+'. '))
            if arm == 'rule_pair':
                assert line == f'{label}. Dim: {pair[0]}; Bright: {pair[1]}'
                assert len(re.findall(r'^[1-4]\. ', x.question, re.M)) == 4
            else:
                assert line == f'{label}. {action}'
            if arm == 'oracle_pair':
                assert f'beacon is Dim, press {pair[0]}; if it is Bright, press {pair[1]}' in x.question
            if arm == 'oracle_button':
                assert f'already been computed: {action}.' in x.question
            if arm == 'compact_joint':
                assert 'Own-device transition' not in x.system
                assert c.action_table(ep, 'P2') in x.system


def test_invalid_output_is_preserved():
    item = d.materials()[0]
    assert d.score(item, 999, (10, 11, 12, 13)) == {'choice': None, 'correct': False, 'invalid': True}
    token = (10, 11, 12, 13)[item.candidates.index(item.correct)]
    assert d.score(item, token, (10, 11, 12, 13))['correct']
    with pytest.raises(ValueError): d.make_item(c.make_short_cases()[0], 'unbounded')
    with pytest.raises(ValueError): d.score(item, token, (10, 10, 12, 13))


def test_followup_is_fixed_and_work_inputs_are_paired():
    assert len(d.work_materials()) == 192
    for case in c.make_short_cases():
        a, na = d.work_item(case, 'facts_first_nowork')
        b, nb = d.work_item(case, 'facts_first_work64')
        assert (na, nb) == (0, 64)
        assert (a.system, a.private, a.question, a.correct, a.candidates) == (
            b.system, b.private, b.question, b.correct, b.candidates)
        x, n = d.work_item(case, 'minimal_oracle_pair')
        assert n == 0 and 'Own-device' not in x.system
        ep, w, side = case.episode, case.world, case.side
        rules = dict(re.findall(r'If the signal is (Dim|Bright), press (\w+)\.', x.private))
        button = rules[t.BEACON_NAMES[w.beacons[1-side]]]
        label = t.LABELS[x.candidates.index(x.correct)]
        assert f'{label}. {button}\n' in x.question


def test_empty_path_repair_preserves_live_route_and_state_identity(monkeypatch):
    from mb.v6_empty_path_native import EmptyPathNativeBackend as E
    from mb.v6_native import NativeBackend as N
    from mb.v6_batch_native import PackedBackend as P
    calls = []
    monkeypatch.setattr(N, '_consume', lambda self, *args: calls.append(('native', args)))
    monkeypatch.setattr(P, '_consume', lambda self, *args: calls.append(('packed', args)))
    obj = object.__new__(E); state = object(); donor = object()
    for window, gain, expected in [((), 0., 'native'), ((), 1., 'native'),
                                   ((donor,), 0., 'native'), ((donor,), 1., 'packed')]:
        obj._consume(state, (1, 2), window, gain)
        assert calls[-1] == (expected, (state, (1, 2), window, gain))
