# Offline logic checks for the continuous v6 proposal

These checks accompany [the unfrozen design](../PROTOCOL_V6_CONTINUOUS_DRAFT.md). They use only the Python standard library. They neither load an LLM nor implement the proposed native runtime, channel, shadows or statistical tests.

Reproduce the saved result from the repository root:

```sh
python3 docs/protocol/v6_continuous_checks/check_design.py
```

The output is saved in `design_check_results.json`. Assertions check:

- All 48 initial beacon/distinct-goal worlds have distinct old/new oracle answers at both ends of the two-round pulse chain. The responsive reference policy passes the three path contrasts and the specific-response quality score.
- In all 48 worlds, replaying the unchanged reference in the unchanged branch reproduces that reference. Changed-branch second-round replay carries a beacon from a different actual world in all 48 cases. This establishes a limitation of the replay contrast, not equal-information isolation.
- All 384 enumerated six-round reference schedules preserve actual action consequences. Holding one's own fields fixed gives 64 partner-field variations with identical private controller messages. Invalid actions hold only their own beacon.
- A fresh once-per-round beacon broadcast is informationally sufficient for an ideal controller and can equal LIVE. Both names intentionally use the same oracle information; this is not a test of the unimplemented FRESH shadow-generation code.
- Randomly changing away from an old answer has signed Delta 2/3 despite zero component Q. Two independent random switches have mean chain Q -1/3. A balanced goal-blind beacon echo has mean component Q zero.
- Twelve directly pulse-aware synthetic policies respond perfectly even with the return path cut; scoring both arms gives zero return contrast. This checks that response alone is insufficient, using the same signed/Delta calculation as other policies.
- Ordinary action labels can collide across participants' different beacon rows. A common fresh goal-to-action row avoids that ambiguity in all 576 permutations of a row and three distinct goals.
- The illustrative N240 allocation balances initial physical roles, beacon cells and goal labels. Full updated-goal, probe-alternative, codebook and text-subset balancing remains a material-generator requirement.
- Workload arithmetic gives 80 paired work periods per base episode, 19,560 per model including the N60 text subset, and 39,120 across both models. N remains 240 per model, not the number of branches, tokens or readouts.

The precision calculation is a normal approximation under assumed episode-score SD 0.5: pointwise 95% half-width 0.0633 and conservative 80% power reference 0.1257 for the strictest Holm22 threshold. It is not measured power or a joint-power guarantee for the eight-part sustained-chain criterion. Exact analysis-code simulations, native source isolation, answer-token recovery, hardware acceptance, runtime/cost measurement and model competence are pending. No scientific setting or spending authorization is created by passing this checker.
