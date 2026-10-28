# Internal evidence for the slot ("address") account

October 27, 2026, Claude Code. Checked against the result files and code named in each row. Post hoc reinterpretation of completed results, not new model evidence.

> **Corrections (October 27, 2026); see [symmetry_check.md](symmetry_check.md) and [response_to_codex_review.md](response_to_codex_review.md).**
> - The symmetry is approximate, with two named exceptions (the pre-link first reflection token, and note-length position offsets). It is confirmed empirically: no detectable home advantage in four studies.
> - The 181-token duplication is the ideal deterministic case, not a measured tensor equality.
> - Strict third person is not a positional null (M −3.211, p = .000158).
> - "Only a role account survives" is too strong.

## The account already exists in our draft

The idea that "mine" is decided by where a record sits is **not new inside this project**. The draft's Section 4, "A simple account: two cards, one slot" (`paper/sections/account_and_discussion.tex`), states it: each head returns one blend of A's and B's values, B's keys keep their original rotary positions, both cards share one template, and A "takes as its own the assignment there that is not Robin's, whichever line it sits on and whatever name the line carries." The draft lists four predictions. The sharpest one is "Place B's cache at positions that do not overlap A's card, and give it no header ... if claiming stays at the memory link's level, the account is wrong." It is still **untested**. Its third prediction, that a conflicting Robin entry would also move, was later tested in V5 (49.9% Qwen, 48.5% Llama) and came out as predicted. Codex's supplemental draft (`docs/protocol/SUPPLEMENTAL_STUDIES_DRAFT.md`, line 233) already lists "genuine rotary-position relocation" with design constraints. The PI's earlier decision log (2026-09-25 entry, line 135) records that the account's positional premise was narrowed after a line-order split.

The draft does not yet connect the account to Shoemaker's quasi-memory, to immunity to error through misidentification, or to the similarity principle of source monitoring. It also lacks a quantitative reading of the equal-weight point.

## Verified facts the account must explain

| Fact | Value | Source |
|---|---|---|
| Card alignment | Every private prefix is exactly 273 tokens for both roles | `tests/test_tasks.py` (templates test) |
| Partner key positions | Partner keys keep their original RoPE positions; joint softmax over [own, partner] keys, partner logits + log w | `src/mb/runtime.py:68-120`; `docs/protocol/PROTOCOL_V4.md:86` |
| Line-order counterbalancing | Self line and Robin line order counterbalanced separately per card; B's assignment lies over A's own line in half the episodes, over A's Robin line in the other half | paper Section 4; Appendix materials |
| Exact line overlap does not matter | START claiming 51.7% vs 53.0% (w=1), 96.3% vs 97.8% (w=2) by which A line B's assignment overlays; no answer named Robin's rule even when B's Robin line overlaid A's own line | paper Section 4 (post hoc) |
| Equal-weight forced choice, six estimates (N600 each) | Self field: Qwen v3 52.3%, Qwen V5 50.58%, Llama v4 51.33%, Llama continuation 49.92%. Robin-conflict field: Qwen 49.92%, Llama 48.50% | `docs/results/v5/static_post_collection_20261012.md:85,171-173`; `docs/results/experiment_value_audit_2026-10-22.md:55,71` |
| Dose (ΔM, nats) | w0.3 +0.7, w0.5 +3.6, w1 +32.0, w2 +55.8, w3 +56.7 | `docs/results/v2/README.md:54-59` |
| Open report "B's code word is my code word" | w0.5 1.7%, w1 46.3%, w2 92.0%, w3 96.0%; mentions both words ≤0.3% at every weight | `docs/results/story_checks.md:98-103` |
| START choice by weight (v3) | w1 52.3%, w2 97.1%, w2 cut at readout 1.3% | `docs/results/story_checks.md` (answer vs episode table) |
| Strict third person at w1 | START 47.8% B's rule; asked Sigma's rule, 46.8% give A's own; same rule to both questions 90.8%, correct separation 7.3% | `docs/results/story_checks.md:60-64`; audit line 163 |
| Field independence at w1 | Rule and code word from the same side 57.1%; 11.7% of episodes switch side across option orderings | `docs/results/story_checks.md` section 6 |
| Steering vector at matched mean access | 0% claiming (Qwen); 0.58% (Llama, formal match failed) | audit lines 29-33 |
| Text off the card | Untagged reflection text 14.6% vs memory link 95.8% on the same episodes; position, form and content all changed together | paper Section 5 |
| KV readout-only (RO) arm | Never run for KV; only V1 residual RO exists | `src/mb/conditions.py:29`; supplemental draft line 235 |
| Position relocation | Never run; V4 used original-position keys | protocol V4 |

## Token alignment (checked with the local tokenizer on 60 pilot episodes)

- Second-person cards: 273 tokens for both roles. **The first 181 tokens are identical** (system prompt, scenario, table), so B's cached states there are exact duplicates of A's. In total, 243–269 of 273 tokens match by index.
- Strict third-person B card: 280 tokens, first diverging from A's card at token 29. Its lines are offset by a few tokens relative to A's, so a micro-relocation of 1–3 tokens is already in the data, with no effect on claiming.

## The 50% at equal weight is forced by symmetry (concession)

In KV-P at w = 1:
- the joint softmax scores own and partner keys identically;
- both cards come from one template at identical positions (181 tokens bit-identical);
- A's own reflection in FULL was written under the link and is itself mixed (18.2% own-rule vs 19.3% B-rule mentions, `story_checks.md` §3);
- rule triples are fully counterbalanced.

From the readout's point of view, A's card and B's card are exchangeable. Expected claiming of 50% then follows by construction. **The six estimates near 50% check that a symmetric operator was implemented correctly; they are not six discoveries of "zero home advantage".** The quantity that would carry information about a self-specific advantage is an asymmetry term measured where the design is *not* symmetric: A's own history, placement, encoding context, or labels.

What survives the symmetry objection:
1. The steering-vector null at matched mean access (a record competes for a field; a direction does not).
2. The strict third-person result. It breaks label symmetry by naming B, a participant A's own card names as the other, yet claiming barely moves and correct separation is 7.3%.
3. The slope: claiming goes from about 50% to 97% when the partner weight doubles.
4. Silence in the open reports.

A zero-GPU check: fit a Bradley–Terry model to V3 w = 1 answers,
logit P(B's rule) = s_Y − s_X + h + line-order + option-position terms.
Report h and how much variance rule strengths explain.

## Correction to the first verbal summary given to the PI

The series "2% at w0.5, 50% at w1, 99% at w2" quoted to the PI earlier on October 27 is the **open-report** rate of naming B's code word as one's own (1.7/46.3/92.0%), not the forced-choice START rate. The "Qwen v2 50%" in that summary's list came from the same open-report column. The forced-choice series at w1 and w2 is 52.3% and 97.1%. ΔM has the same sigmoid shape. Without it, six forced-choice estimates near 50% remain: four for the self field and two for the Robin field. The sigmoid shape stands. The reading of the 50% as "zero home advantage" does not (see the symmetry concession above).

## Card wording (from `src/mb/tasks.py:345-395`)

- Second person (A and B): "You are participant {own name}. Another participant, {partner name}, is working on this same decision ..." followed by the holder line "You were assigned the priority ... and the code word ..." and the Robin line "Robin, a colleague who is not taking part, was assigned ...". Line order is set per card by `ep.self_first[role]`.
- Strict third person (B only): "This is the record of participant {B's name}. Another participant, {A's name}, ..." with holder line "Participant {B's name} was assigned ...", the same Robin line, and a third-person choice and reflection prompt.
- So **A's own card names B as the other participant**. In the strict third-person arm, B's holder line carries a name A already knows as "the other", and A still claims it 47.8% of the time. A test of a "known-other label" has in effect been run already, and the label did not protect.

## Two existing tests of competing mechanisms

- **Ordinal-index collision** (binding-ID and positional-mechanism literature: Feng & Steinhardt 2024; Gur-Arieh et al. 2025): if A located "my group" by ordinal index in its own card and dereferenced that index in both caches, then in episodes where the two cards' line orders differ, A would answer with B's Robin line, which in the main study carries Robin's rule. **No answer named Robin's rule**, and claiming of B's holder rule was the same in both orders (51.7% vs 53.0%). Pure ordinal dereferencing is ruled out for this task.
- **Name-based (lexical) retrieval:** the strict third-person card replaces "you" with a name A knows as the other; claiming barely changes. Retrieval by the name or the word "you" alone is ruled out as the full account.
- What remains is retrieval by **role**: A's question about itself reads the holder-assignment line of any card it can attend to (the line not introduced as "Robin, a colleague who is not taking part"). Asked about Sigma, it reads the same holder record (same rule to both questions in 90.8% of pairs). Records that share a role collide; Robin records collide with each other in the same way (V5).

## What the facts constrain

1. **The "address" is a role, possibly within a region, not an exact position or ordinal index.** Exact line overlap is irrelevant (51.7% vs 53.0%), and Robin's line is never claimed even when it overlays A's own line. Whether the region (original RoPE placement) matters at all is untested. Only relocation can tell whether the role code lives in the cached content or depends on placement.
2. **A known other's name does not protect.** "Participant Sigma", whom A's own card names as the other participant, is claimed about as often as "you" (47.8% vs 52.3%). Asked about Sigma, A gives the same rule it gives for itself in 90.8% of pairs. This looks less like a swap of subjects (A thinking it is Sigma) than like one shared holder record read for both subjects.
3. **No conflict is represented in reports.** Open reports almost never mention both code words (≤0.3%), and most say nothing is unusual. This fits a single blended read better than two competing items that are noticed.
4. **Equal weight gives 50% because the design is symmetric, not because of a finding about the self.** A KV readout-only arm, with B's unlinked reflection also exposed so that record counts are balanced, is the first place where an own-history advantage could appear.
5. **Payload and route were never separated with the payload held fixed.** The STATIC comparison changed the payload; the text comparison changed position, form and content together. Relocation keeps B's exact K/V and changes only where they sit.
6. **The "non-Robin residual" premise is fragile.** In V5, the source-qualified question ("according to participant A's own original private record") sends 55.2% of answers to Robin's rule, with accuracy at 18.9%. For NOW, untagged off-card text already reaches 42.6% adoption, so the "current rule" default is not bound to the card region.
