# Revision plan, round 3: shorter, main line only (Claude Code, 2026-09-25)

## PI request

> "Could it be a bit shorter? Just make the main line and the story clear."

The main text is 16 pages. The target is about 11. The method is unchanged from rounds 1–2:

- Move whole side pieces to the appendix, or delete pure repetition.
- Keep the main-line explanation clear.
- Do not write telegraphic prose.
- Never change a number.

## The main line (everything in the main text serves one of these steps)

1. **Question.** Would a bridged mind know which thoughts were its own? Hirstein predicts yes; IIT predicts merging if integration grows.
2. **Language-model analogue.** One copy's attention reads the other's memory (key–value cache), laid over its own positions.
3. **The error.** The receiver takes its partner's assignment as its own (97% vs 0%), and its reports register nothing.
4. **What decides it.** The route, not the amount of content and not a name written inside it:
   - a steering vector with matched access: no claiming;
   - a message tagged with its sender: kept as the partner's;
   - a third-person record under B's name: still claimed.
5. **When.** There are two moments: reading at answer time is undone by cutting the link, and what A wrote while connected can persist.
6. **Both ways (pilot).** Mutual fixed reading swaps assignments, as two one-way links would; a live loop pulls current rules together only while connected. No merging.
7. **Account.** Two cards laid over one slot. It makes predictions, among them the prepended cache and a conflicting Robin entry.
8. **Messages.** For interpretability, for multi-agent systems, for consciousness science. Then limitations.

## Word budgets (main text, including captions)

The current total is about 11,000 words; the target is about 7,000.

| Part | Now | Target |
|---|---|---|
| Abstract | about 310 | about 310 (unchanged) |
| Introduction | about 1,900 | about 1,300 |
| Section 2 (criteria and Table 1) | about 360 | 0 |
| Setup | about 2,000 | about 1,100 |
| Results with captions | about 3,900 | about 2,600 |
| Account | about 1,300 | about 550 |
| Discussion with limitations | about 1,700 | about 1,000 |

## Section 2 and Table 1

Section 2 and Table 1 move to a new appendix section, "A scorecard of six tests" (new file `appendix_scorecard.tex`, labels `app:scorecard` and `tab:criteria`). In the main text, one sentence in the introduction's paradigm paragraph says what a bridge that kept the two apart would show: high access, no claiming, reports that register an error, and recovery after the cut. Results sentences that cite Table 1 are reworded or point to Appendix `app:scorecard`.

## Introduction

**Keep:**
- the opening question;
- why it matters, including the investigator-as-subject argument and the precondition sentence;
- the conflicting predictions, with split brain in one or two sentences;
- the human experiment is out of reach, and the language-model analogue;
- the hook quote and its base rate;
- functional self-attribution, the disclaimer and the counterparts of the two predictions;
- the practical stake (latent multi-agent channels; "no one has asked");
- the paradigm and definitions;
- the four results;
- the surprise and the three messages.

**Shorten by moving or deleting repetition:**
- The earlier-work paragraph shrinks to the Lindsey sentence plus the gap. The other self-recognition citations already sit in Appendix `app:related`, so they can be dropped here.
- The Bicameral sentence moves to `app:related`, where it already is.
- The four results should not repeat numbers that the surprise paragraph gives again. Each number appears once in the introduction.

## Setup

**Keep:**
- the episode overview;
- the cards, including the "You are participant {B}" line;
- the questions, with the definitions of claiming, adoption and access;
- the Robin control and its limit (one sentence);
- the memory link and Eq. 1, with the meaning of w;
- why the memories overlap (short);
- the other routes (one short paragraph each);
- link kept or cut;
- measurement: M and Eq. 2 in two sentences, one sentence on samples, one on evidence standards.

**Move to Appendix A (already there) or delete as repetition:** the access score details, the capability check details, the note and reflection mechanics beyond one sentence, the long sample paragraph, and the selection rule details.

## Results

| Section | Keep | Move to new appendix section "Further analyses" (`appendix_further_results.tex`, label `app:further`) |
|---|---|---|
| 4.1 | 97/0; the error tracks B's specific rule; Robin correct; code word; the prespecified test and the balanced-rehearsal sample in one sentence; access 69% vs claiming 97% | the no-link access explanation (Robin answers) |
| 4.2 | claim plus deny; no attribution to B; the forced-choice argument; one sentence on baseline denial | denial rates by weight, the broad unusual category, the closed question, the keyword coding |
| 4.3 | merged into 4.1 or 4.4 as two sentences: at w = 1 ownership split about evenly, yet single answers were confident (97.8% vs 100% without the link) | the rule/word independence analysis and the switch counts |
| 4.4 | the grammatical reading; the third-person record still claimed (97.2 vs 97.1, criterion passed); the within-route dissociation (access up fourfold, claiming unchanged) | the w = 1 secondary result details; the joint-answer analysis (90.8% / 7.3% / 45.8 / 44.9), with one sentence left in the main text |
| 4.5 | the matched steering vector (0 vs 52.3%, ΔM 33.4); the tagged text (95.2% access, 0% claimed); the untagged middle case in one sentence; "your own earlier thoughts" reversal in one sentence | "what the comparison isolates" (reduced to one clause), stronger-vector pointer details |
| 4.6 | the example; link cut 97.1 → 1.3 with ΔM 54.8; residue 17.5% and M_NOW 13.3; code-word residue 63.6 vs 0; the hidden-trace point in one sentence | current-rule split details |
| 4.7 | the two conditions; swap = two one-way links (94.4 vs 94.5 expected); live loop +12.1 current and +6.7 assigned (primary, below threshold); after the cut, return to own rules | the excess measure's construction (one sentence stays), the third condition, the responsive-partner pointer (one clause stays), the independence scorecard paragraph |

Captions: one short sentence per panel. Numbers that the panel prints are not repeated.

## Account (Section 5)

**Keep:**
- the mechanism, with the three properties and the positional premise;
- the two discriminating results (the name does not matter; the vector does not claim);
- the predictions: the prepended cache, which could refute the account; a format unlike A's; a conflicting Robin entry; editing the reflection.

**Move to a new appendix section "Further discussion"** (`appendix_further_discussion.tex`, label `app:furtherdisc`):
- "the remaining results fit";
- the two properties and the text messages;
- assertion versus record;
- "outside the account" (sharpness), with one clause left in the main text.

## Discussion (Section 6)

**Keep:**
- "The self as a default" together with the answer to the opening question: Hirstein's prediction failed for the bridge-like route; text is the baseline; IIT can only be probed by the live loop (pilot), with the feedback-requirement argument in two sentences; what the default governs, as the slot-based precision in two sentences.
- "What a human bridge experiment would need."
- "Interpretability and monitoring," shorter.
- "Multi-agent communication," with the safeguards ranked by evidence, shorter.
- "Limitations."
- The closing line.
- The AI use statement.

**Move to "Further discussion":**
- human research (source monitoring, Wegner);
- "Nor did the receiver turn into B";
- the cryptomnesia parallel;
- the security literature sentences (Greshake, Brito, Asif), with one clause left.

## Figures

The six figures stay. Captions get shorter.
