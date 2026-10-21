"""Read bounded exposed-data structure and check proposed diagnostic identifiability.

No model execution or new empirical effect/selection analysis. Output is stdout.
"""
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('/Volumes/VERBATIM SD/mind-connecting-data/v6/replacement-clarity-20261019-goal-stage-diagnostic1/restored/output')

def main() -> None:
    source = ROOT / 'records.jsonl'
    if not source.exists():
        raise SystemExit('Required exposed SD evidence is unavailable; no fallback')
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    keys = [(r['episode_id'], r['focal_side'], r['donor_goal'], r['arm'], r['qid']) for r in rows]
    prepared = defaultdict(set)
    postwork = defaultdict(set)
    coverage = Counter()
    for r in rows:
        prepared[(r['episode_id'], r['focal_side'])].add(r['recipient_prepared_digest'])
        postwork[(r['episode_id'], r['focal_side'], r['donor_goal'], r['work_on'])].add(r['recipient_postwork_digest'])
        coverage[(r['episode_id'], r['focal_side'], r['donor_goal'], r['arm'])] += 1
    worlds = list(itertools.product((0, 1), repeat=4))  # xA, xB, gA, gB
    policies = {
        'use_partner_fact_own_goal': [xb ^ ga for xa, xb, ga, gb in worlds],
        'use_partner_fact_partner_goal': [xb ^ gb for xa, xb, ga, gb in worlds],
        'copy_ideal_partner_action': [xa ^ gb for xa, xb, ga, gb in worlds],
        'use_own_fact_own_goal': [xa ^ ga for xa, xb, ga, gb in worlds],
        'constant_zero': [0] * len(worlds),
        'constant_one': [1] * len(worlds),
    }
    target = policies['use_partner_fact_own_goal']
    accuracies = {k: sum(x == y for x, y in zip(target, v))/len(worlds) for k, v in policies.items()}
    assert len({tuple(v) for v in policies.values()}) == len(policies)
    distorted_fact_with_own_goal = [(xb ^ ga ^ gb) ^ ga for xa, xb, ga, gb in worlds]
    assert distorted_fact_with_own_goal == policies['use_partner_fact_partner_goal']
    assert set(v for k, v in accuracies.items() if k != 'use_partner_fact_own_goal') == {0.5}
    assert all(len(s) == 1 for s in prepared.values())
    assert all(len(s) == 1 for s in postwork.values())
    result = {
        'scope': 'Exposed developmental evidence: coverage only; synthetic policies are not model results',
        'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'rows': len(rows), 'unique_keys': len(set(keys)),
        'layouts': len({r['episode_id'] for r in rows}),
        'arms': sorted({r['arm'] for r in rows}), 'qids': sorted({r['qid'] for r in rows}),
        'unique_cells': len(coverage), 'questions_per_cell': sorted(set(coverage.values())),
        'world_action_lengths': sorted({len(r['world']['actions']) for r in rows}),
        'prepared_state_groups_invariant': len(prepared),
        'postwork_state_groups_shared_across_readout_conditions': len(postwork),
        'sample_schema': sorted(rows[0]),
        'policy_check': {
            'worlds': len(worlds), 'variables': ['xA', 'xB', 'gA', 'gB'],
            'distinct_full_response_patterns': len(policies),
            'accuracies_against_target': accuracies,
            'consequence': 'All five alternatives have identical accuracy but distinct intervention patterns; accuracy alone cannot identify goal capture, action copying or missing input.',
            'limitation': 'Ideal deterministic alternatives only. Distorting the perceived partner fact to xB XOR gA XOR gB while retaining gA gives exactly the same actions as adopting gB. Behavioral patterns alone do not identify a goal-representation change.',
            'fact_distortion_and_goal_adoption_observationally_identical': True
        },
        'capability_counterexample': {
            'foreign_fact_retained_after_receipt': 'Connected and disconnected actions can both remain correct; no current dependency is established.',
            'fresh_partner_private_fact_after_branch': 'Dependency is possible, but actual linked/cut performance must establish it; a forecast failure cannot be assumed.',
            'inference': 'Source origin, present dependency and ability forecast require separate measurements.'
        }
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
