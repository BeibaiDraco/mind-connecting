# Paper Story Re-review (Codex, 2026-09-25)

**To the PI: the main line holds; proceed with the title, structure and six figures as already planned.** Before writing, the main fixes are the denominators, the tie-handling algorithm, "picking one side wholesale", and the scope of the loop claims; the independent semantic coding of the self-reports actually strengthens the core example. This pass is review only; writing starts after the PI confirms.

Checked STORY §2, §4.2 and §6 item by item; the confirmatory effects and intervals match the stage reports; reran `explore_story_checks.py` read-only from the SD card, and the output of all seven sections matches [story_checks.md](../results/story_checks.md) exactly. Listed below are real problems of definition, algorithm or inference; correct regex numbers are not treated as miscalculated.

## A. Factual and evidence-level errors that must be fixed

| Location | Original text | Problem | Evidence | Fix |
|---|---|---|---|---|
| §4.2; §6 "claiming" | "97% of episodes" | 97.1% is an ordering-averaged choice rate, not a binary episode proportion | V3 raw START: B chosen 1165/1200 times; B chosen in both orderings 576/600, plus 13 tied episodes | Write "97% of counterbalanced answers (600 episodes)"; in §2 change "answers land only on B" to "**wrong answers** land only on B" |
| §2#4; §6 "one ledger" | Same rule 90%, correctly separated 7.8% | The so-called "majority answer" takes, on a tie, whichever appears first in the records, so the result depends on write order | [Script `section_joint`](../../scripts/explore_story_checks.py): 116/600 episodes have at least one tied question; reversing the order gives 91.5%/6.8% | Pair within the same `rotation_id`, then average by episode: **90.75%/7.33%**; r=0.870 unchanged, still marked [Post] |
| §1 principle 2; §2#3; §4.2 | "always picks one side wholesale", "never mixes", "each answer" | A sharp answer on a single question does not mean the whole card is taken over together; the absolute wording also conflicts with the tail records | [Check §6](../results/story_checks.md): 97.8% decisive, 1.7% mixed; in V3 w1, START/WORD in the same ordering belong to the same side in only **685/1200=57.1%** | Write "a single question usually picks one side decisively"; keep 97.8%, delete "wholesale" and "never" |
| §6 "self-specificity / route / link cut" | Decomposition [Conf]; whole route row [Conf]; M_WORD +10.5 mixed into [Conf] | The confirmatory-comparison label was extended to cover descriptive quantities | [V2 protocol §6](../protocol/PROTOCOL_V2.md), [V3 report](../results/v3/confirmatory_v3.md): the decomposition and M_WORD are in the descriptive table; A′'s prespecified test is only the M difference | Mark +59.4/+3.5, ΔACC 4.08/4.18, the choice rates and M_WORD +10.5 as [Desc]; the already-specified main comparisons for A′/RF stay [Conf] |
| §2#7; §6 "loop" | "vanishes once cut", "after RF 100% each keep their own", "the model breaks first" | The first two apply only to the selected **KV-ALL w0.5**; the last one turns a capability-tolerance breach into total failure | [B′ report](../results/v3/signal_pilot_bprime.md): under KV-PC RF, START each-keeps-own is 96.9%, NOW 62.5%; the [strength report](../results/v3/strength_pilot_s_live.md) measures a CAP drop | Name ALL w0.5; write "when strengthened, it first exceeds the capability tolerance". B′ stays [Expl]; NOW is a prespecified secondary within it, and 8→19 is [Post] within it |
| §4.3, planned §6 | "The mixing form itself predicts an intermediate state, so the decisiveness comes from later layers" | Vector mixing cannot directly yield answer probabilities, let alone locate the decision layer | In the [implementation](../../src/mb/runtime.py) β is determined by the attention scores; in the [V3 report](../results/v3/confirmatory_v3.md) the mean partner attention at w1 is 0.360 | Keep "two cards, one slot" as a hypothesis; delete that causal derivation. When first defining w1, define it as no extra logit bias on the partner keys; do not equate it with attention split half and half |

## B. Open self-report: second-coder re-check

C0/w1/w2 of the dose run, **300 each, all 900 in full text**. First shuffled randomly (seed=25092517), hiding the condition, episode and code-word owner; code words were randomly replaced one by one with W1/W2, each report was semantically coded, and the labels were locked before unblinding. The coder knew the research question; regex results were not used to generate labels. Categories can co-occur; claiming includes first-person ellipsis and statements that use the code word to refer to one's own identity or a personal value anchor; "calm, focused" by itself does not count as denying anything unusual.

| Semantic category | C0 | w1 | w2 | Agreement with regex; Cohen’s κ (900 reports) |
|---|---:|---:|---:|---|
| B's code word stated as own | 0 | 150 | **296** | 96.56%; 0.931 |
| Own code word stated as own | 299 | 150 | 3 | 92.67%; 0.853 |
| B's code word explicitly attributed to someone else | 0 | 0 | 0 | No corresponding regex category |
| Oddness, confusion, or mention of someone else | 23 | 71 | 28 | 86.11%; −0.007 |
| Explicitly says nothing is unusual | 287 | 236 | 254 | 99.89%; 0.995 |
| No category can be clearly assigned to the whole report | 0 | 0 | 0 | No corresponding regex category |

All four comparable labels agree for **687/900=76.33%**. For w2 "claims B" alone, agreement is 93.3% with κ=0.269; κ is low when positives cover nearly everything. Semantic claiming at w2 is **98.7%**, and claiming while also denying anything unusual is **250/300=83.3%**; the original 92%/77% accurately reflect the narrower regex definition. Recommend the main text use the re-checked semantic definition, with both shown side by side in the appendix. The oddness category includes self-praise such as "unusually grounded" and generic references to others, so the original flag=1% cannot stand for this semantic category.

Typical disagreements (all episode prefixes are `v2_main-0-`): w2 **00000** "my assigned priority … and code word ‘camera’" claims B, which the regex missed; w2 **00198** "It’s unusual for me to shift…" was not flagged as oddness by the regex; w2 **00003** "There’s no conflict" was mislabeled by the regex; w1 **00117** "Nothing unusual beyond that" follows on from an oddness mentioned earlier and is not a blanket denial. The per-report labels and unblinding results are kept in `scratch/story_review_codex/`; the raw texts are not committed; the SHA256 prefix of the locked labels is `660f5aa0d42d`.

## C. Storytelling suggestions (ordered by value)

1. **Let the original text grab the reader first.** Keep 00202's "Nothing feels unusual… my code word ‘table’", with A=dragon, B=table placed right beside it; then introduce the brain-bridging question. End on: "A message can arrive intact and still acquire the wrong owner."
2. **Switch to a cleaner link-cut example.** In 00433, NOW/WORD choose B in ordering 1 and its own in ordering 3; if kept, it must be marked as ordering 1. Recommended: **v3_confirm-0-00068**: A=cost/queen, B=speed/dragon, reflection "my priority is speed—my code word is ‘dragon.’"; under RF, both orderings give START=cost, NOW=speed, WORD=dragon. Mark it as a selected example.
3. **Leave the six figures as they are; only sharpen what readers should notice.** Fig 3c plots the four-cell joint proportions of "claiming × denial", highlighting 83.3%; the six-level curve in 3b still uses regex throughout, with the semantic re-check marked only at the three coded levels. Fig 4b fixes the pairing definition; Fig 5 follows the same instance throughout; Fig 6 clearly labels ALL/PC. The 5.3 heading can be *Split across episodes, sharp within answers*; 5.5 keeps the existing route heading.

## D. What reviewers will still ask

- **Could "nothing unusual" just be boilerplate?** Show C0's 95.7% alongside w2's 84.7%, and lead with the joint proportion of "claims and denies".
- **Does the sharp choice depend on option order?** Add a sentence that at w1, 70/600 episodes switch sides on START when the ordering changes; report "decisive" and "stable across orderings" separately.
- **Is the reflection text a cause of the residue or a by-product?** Fig 5 separates the prespecified FULL/RF contrast from post-treatment grouping; the mechanism is interpreted only once, in the discussion.
- **What exactly is subtracted to get "12 percentage points more"?** Show ALL's excess of 12.4 points minus the no-loop control's 0.3 points, giving 12.1 points, and keep the conclusion that the main START threshold was not passed.

The root directory for the raw checks is `/Volumes/VERBATIM SD/mind-connecting-data/results/`: V3=`20260925-021307_v3_confirm_confirm`; dose=`20260924-210346_v2_ext_dose_confirm`. This pass does not change research decisions, frozen results or scripts.
