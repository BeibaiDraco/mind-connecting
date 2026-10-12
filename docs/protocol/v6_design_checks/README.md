# Local checks for the reciprocal-interaction draft

These checks validate task algebra, counterexamples, planned balance and workload. They do not instantiate an LLM, inspect formal experiment outcomes, test the new runtime, or freeze the design.

Run from the repository root:

```sh
.venv/bin/python docs/protocol/v6_design_checks/check_design.py
```

The saved output is `design_check_results.json`. It verifies:

- All 6,912 combinations of two four-way permutations and an ordered request change have distinct old/new correct actions.
- Correct private lookup has mapping-specific score 1; repeating the old answer and randomly switching among non-old answers have expected score 0.
- A full-table one-way broadcast can solve the composition while failing the forward-necessity criterion.
- Averaging changed and unchanged requests can falsely suggest path necessity on the changed request; the primary estimand therefore uses changed requests only.
- All 2,304 combinations of goal triple, fact pair and fresh action mapping preserve distinct old/new/partner actions and the partner's unchanged correct goal.
- A proposed 600-episode schedule has 25 episodes per ordered goal triple and 75 per physical-initiator-by-fact-pair cell overall.
- Feedback sensitivity alone can be produced by a synthetic echo; mapping-specific response is a separate requirement.
- The planned paired-trajectory and readout counts match the draft.

The precision grid is a normal approximation using the most conservative entry threshold in a twelve-test Holm family. Synthetic null, small and large effects are planning illustrations. No empirical variance or observed LLM effect is assumed. Before protocol freeze, the implemented analysis needs its own exact-code simulation, and native hardware acceptance remains necessary.
