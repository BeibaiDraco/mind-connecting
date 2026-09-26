# Paper Draft Review (Claude Code workflow, 2026-09-25)

One reviewer for each of five dimensions: numbers and evidence levels, story and structure, citations, typesetting, and a fresh reader. Each medium- or high-severity finding was then independently checked by a rebutter: 37 confirmed, 3 rejected; low-severity findings were not checked. This review is read-only and did not change the draft. Following the PI's preference, it does not ask for added boundary disclaimers and does not soften the wording.

**Paper draft review: merged revision list**

The five reviewers raised more than 70 items in total; after checking each one and merging duplicates, about 35 remain. The numbers themselves almost all match the source files; the problems are mainly in three places:

- **Some numbers lack their condition or their comparison, so readers will misread them.** The abstract's 97% does not say it is the w=2 result. The residue left after the link cut under KV-PC reads as if the loop caused it, but it did not. One prespecified test in v2 came out in the opposite direction, and the main text does not mention it.
- **The story line is broken.** The introduction and the tour contain not a single number. The count of the "seven findings" does not add up. The Hirstein vs. IIT debate set up at the start is never answered later. The study versions v1/v2/v3/B′ are never introduced in the main text.
- **Layout problems.** This is exactly the horizontal space you mentioned. The new figures are all 6.5 inches wide, but they are squeezed by the height cap in `\paperfigure`: Fig 1 prints at only about 80% of its width, Fig 4 at about 81%, and the text shrinks with them. Remove the height cap and every figure can fill the text block. The reviewer recompiled in a temporary copy: still 21 pages, with the main text ending on page 9. The horizontal space can also be used in three more places: merge the narrow tables in the appendix or put them side by side; add a full-width "study map" table to Setup; add a "tested in which section" column to Table 1.

Several of the reviewers' original suggestions conflict with the ledger or with your preferences; the list below **does not follow them**:

- Do not delete "only 7.3%"; it is the ledger's own wording.
- Do not rewrite the introduction as "three contributions".
- Do not add a Limitations sentence.
- Do not weaken the strong verb "establish" at the citation.
- Do not semantically recode §5.6.

Suggested order: first fix group 1, which is all pure text edits and can be done in half a day. Then fix the figure widths and the Fig 1 position in group 3. Once the figures are final, align the captions all at once.

## (1) Must fix (facts, numbers, evidence levels)

1. **Abstract, main.tex:65-67**
   - Problem: 97% is the result at w=2, and the abstract does not say so. Later it says "with no extra bias the two sides are roughly half and half", so readers will think any connection reaches 97%. The ledger explicitly forbids writing "any connection".
   - Fix: in the 97% sentence, state "when the partner's keys received a twofold attention weight (w=2)". Write the next sentence as "With no extra bias (w=1), 52% vs 48%". Do not write "attention doubled": at w=1 the partner already takes 0.360 of the attention.

2. **§5.7 KV-PC, results.tex:197-199**
   - Problem: the original text is "KV-PC behaved differently… 37.5%", which reads as if the loop caused the residue after the link cut. But the control with the same w=2 and no loop has a residue of 41.3% (appendix table 18.75+22.50), only 8.4 points above the independence expectation, versus 7.0 points for KV-PC. KV-ALL's full recovery likewise matches its w=0.5 no-loop control. The difference between the two comes from the prefill weight (2 vs 0.5), i.e. the residue described in §5.6.
   - Fix: replace it with "KV-PC's fixed part is w=2, and there is almost no extra convergence while linked; after the link cut, in 37.5% of Now pairs one side still uses the partner's rule, versus 41.3% in the control; this is the §5.6 residue, not a loop effect; KV-ALL's full recovery also matches the w=0.5 control". A post hoc data point can be added: the proportion of reflections mentioning the partner's rule is 53.8% for KV-PC and 1.2%/6.2% for KV-ALL. Do not write "caused by the reflection". Update the note on STORY #7 to match.

3. **§5.7, results.tex:182-184, and appendix.tex:190**
   - Problem: the main text gives only the post hoc result "once B can respond, A's use of the partner's rule rises from 8.1% to 19.4%". v2 ran a prespecified test of the same question (B_K, KV-ALL w=0.7), and the result was significantly reversed: M_NOW −4.8 nats, 90% CI [−8.3, −1.2]. The appendix only says "failed its directional gate", and lumps it into one sentence with B_R, whose result was null.
   - Fix: add a sentence in §5.7 stating that the B_K result was reversed and that both arms' capability exceeded the tolerance (drops of 9.4 and 14.4 points respectively). In the appendix, write the two separately: B_R had no effect (−0.24), B_K was reversed.

4. **§5.6 results.tex:150-157, Fig 5 caption, appendix appendix_coding.tex:103-114**
   - Problem: the so-called "mentions B's rule 46.0%" is actually matched on exact phrases (e.g. "fastest delivery"), so a paraphrase counts as "not mentioned". The main text's example 00068 ("my priority is speed") happens to be coded as "rule not mentioned". The recomputed number is correct and the direction is unchanged; the main text just does not state this definition.
   - Fix: state "contains B's exact priority phrase 46.0%, contains B's code word 27.5% (keyword matching)", and call the two groups the "phrase group" and the "code-word group". At 00068 add a sentence: "It mentions the code word and only paraphrases the rule, so it is in the code-word group, not the phrase group." The abstract can stay as is.

5. **results.tex:64**
   - Problem: the denominator of "0.3% of the dose episodes" is wrong. It is only 1/300 in the w=1 arm, and it uses regex coding, whereas the rest of the main text uses semantic coding.
   - Fix: "At w=1, only 1 of 300 open reports (0.3%, regex coding) mentioned both code words."

6. **Fig 3 caption, results.tex:27**
   - Problem: "v2 replication" gets both the chronological order and the evidence level backwards. v2 ran first, and it was the prespecified confirmatory test.
   - Fix: "in v3 and in the earlier v2 sample (N=600 each; the v2 ΔM is the confirmatory test)".

7. **Fig 1 caption and the tour, tour_and_criteria.tex:16-27**
   - Problem 1: the caption says "rates are measured over the full samples", but the figure's 94.4% comes from the exploratory B′ pilot with only 80 episodes.
   - Problem 2: panel d of the new figure uses 00274 (code words tower/table), while the caption and main text say 00202 (dragon).
   - Fix: note in the caption "the two-way rate comes from an 80-episode exploratory pilot", and add "in an exploratory pilot" to the tour sentence. Make the episode number consistent: either change the figure, or change the caption, main text, appendix and STORY together to 00274.

8. **§5.4 results.tex:86-89, Fig 4 caption**
   - Problem: 90.8% answering both questions with the same rule, and r=.870, both lack a reference point.
   - Fix: keep "only 7.3%". Add the reference points: each question on its own picks the partner's rule about half the time (47.8% and 53.2%), so if the two questions were answered independently, agreement would be only about 50%; in the second-person condition r=.384. If the second-person 30.2% is cited, the same sentence must explain that in the second-person condition 57% of the partner answers landed on Robin, and only 3.8% were correctly separated. Otherwise readers will think the second person can separate the two ledgers. Delete "physical".

## (2) Should fix (story, clarity, citations)

1. **End of introduction, introduction.tex:73-79; tour, tour_and_criteria.tex:11-17**
   - Problem:
     - After the abstract there is not a single number until Section 5.
     - The list says "seven findings" but actually has only six. The split also differs from STORY §2: claiming and self-report were merged into one item, and two-way was split into two.
     - "verbal alarm" is not defined.
     - The tour says "seven tests", but Fig 1 has only three original-text panels and Table 1 has six criteria.
     - The same set of findings is told four times over.
   - Fix (recommended): write all seven items in the introduction in STORY §2's order, each with one number and an evidence label:
     - 97.1 vs 0, Robin 99.6
     - 83.3 (descriptive, post hoc coding)
     - 52.3/47.7, 97.8% of answers are sharp (post hoc)
     - 97.2
     - steering vector 0 vs 52; text access 95.2, claiming 0
     - 97.1→1.3, but residue 17.5 (post hoc grouping)
     - swap 94.4, +12.1 (exploratory)
   - The tour keeps the 00202 opening, changed to "Figure 1d–f shows three such moments", with one number per panel and no restating of the list. If pages are tight, merge the tour into the Fig 1 caption as in STORY §4.4.

2. **The Hirstein and IIT setup is never paid off**
   - Problem: after introduction.tex:27-33, the paper never mentions the two predictions again.
   - Fix:
     - Add to reason 1 (l.58-59) "and shows which of the competing predictions a functional analogue follows".
     - Add a sentence or two at the end of the introduction: contrary to Hirstein's expectation, the receiver does not know that the content is not its own (97% vs 0%); in the exploratory two-way pilot the result is a swap (94.4%), not a merger.
     - In the discussion, split "self as a default" out into its own paragraph that answers the opening. Keep IIT in conditional form; do not write "refutes" or "rules out merger".

3. **No map of the study versions (setup.tex:72-77, results.tex:15-22 and 127, Fig 6 caption)**
   - Problem: v1, v2, BAL, G2, dose, v3 and B′ are never introduced in the main text. Readers will get stuck at §5.1, the most important section.
   - Fix: add a small full-width table "Study map" to Setup, with four columns: stage | new episodes | conditions | prespecified test. Also:
     - In results l.17 write "balanced-rehearsal sample (BAL)".
     - At l.127 write "the v1 residual-stream bridge".
     - In Fig 6 write "two-way pilot (B′, N=80)".

4. **The task description in Setup is too thin (setup.tex:5-35)**
   - Problem:
     - It does not say the private note is a plan written by the model itself (up to 48 tokens).
     - It does not say the prompt names the partner's codename.
     - It does not say the reflection prompt asks for the code word to be mentioned once.
     - It does not say what "balanced rehearsal" is.
     - The mechanistic premise "the partner's keys keep their own RoPE positions, which largely coincide with A's record" first appears only in Section 6.
   - Fix: add one sentence for each point above. State clearly that Start measures claiming and Now measures adoption, and point back to Section 3. Optional: move the appendix's question-stem table into Setup as a full-width table with a "what it measures" column.

5. **Terminology**
   - ΔM does not say which two arms are subtracted: at results:15 write "KV-P w=2 minus C0".
   - K* is used only once in the whole paper: delete it and write w=2 directly.
   - Spell out FULL/RF at first appearance (link open / link cut).
   - Define tick and donor.
   - Add a parenthetical gloss at the first appearance of w in the tour.
   - Explain w_P and w_C in the Fig 6 caption.

6. **Jargon in the abstract, main.tex:68-80**
   - Problem: static injection, mean rule-access, connected reflections, current plans, live loop and sharp are all unexplained.
   - Fix: switch back to the plain-language wording already settled at STORY.md:109, keeping the numbers and claims unchanged.

7. **§5.7, results.tex:182-188, Fig 6 caption (c)**
   - Problem: "making B responsive" does not make clear what exactly was changed. The excess convergence is described only in words, without the raw rates.
   - Fix:
     - Write "letting B also read A's live cache (two-way) instead of only A reading B".
     - Add the raw rates: with the loop, 43.1% of pairs have both members using the same member's rule, versus 6.9% in the control; the independence expectations are 36.2% and 6.7% respectively.
     - Add a `\label` to the formula in the appendix and reference it here. Update caption (c) to match.

8. **Section 6 and the discussion, account_and_discussion.tex:4-22 and 63-72**
   - Problem: principle 4 is missing (two-way reading of fixed memories amounts to a swap; only a live loop makes them pull on each other). "Assertion vs record" has no evidence attached. LatentMAS's prediction is not named.
   - Fix:
     - At l.20-22 cite the self-label −19.5 nats as evidence.
     - After l.14 add a sentence on principle 4 (94.4%, exploratory).
     - At l.19-20 write "prepended at separate positions, as in LatentMAS".
     - In the discussion, split out a separate "self as a default" paragraph, adding the source-monitoring prediction and the 52.3/47.7 at w=1 (post hoc description).

9. **Table 1, tour_and_criteria.tex:43-54**
   - Problem: the Specificity row has no verdict, and the Access row has no numbers.
   - Fix:
     - Specificity row: "Pass: Robin 99.6%; capability −2 points (tolerance 5)".
     - Access row: "Pass: B's rule read out 69.2% vs 3.9% (C0); 38.8-nat shift".
   - A "Tested in" column can be added, which also uses the horizontal space.

10. **Misplaced citations**
    - (a) intro:66-67: Zhang & Emu do not support the "private content" claim; only Cheng does. Attach the two separately, keeping the strong verb.
    - (b) intro:20-22: "bypassing translation into language" belongs only to Ramachandran; Hirstein is about "breaking the privacy of the mind". Split them as in OPENING.md:39.
    - (c) intro:70-72: cite koch2020bridging, only as the source of the name "brain bridging".
    - (d) intro:60-63 and related work l.41-42: add "and to the route by which content arrives".

11. **§5.2 results.tex:42-53**
    - Problem: the semantic coding was done by an AI (Codex), which the main text does not say here, so readers will assume it was human coding.
    - Fix: state "an AI coder blind to condition (Codex; Appendix C)".

12. **account_and_discussion.tex:8-10**
    - Problem: "preservation of Robin's shared row" is close to wording the ledger forbids. Robin's logit actually changed by +3.5 nats, versus +59.4 for the self question.
    - Fix: change it to "Robin answers stayed correct (99.6%)".

## (3) Typesetting and layout

1. **Figure width (`\paperfigure` at main.tex:38-43)**
   - Problem: the height cap squeezes the figure width:
     - Fig 1 is 3.95in tall with a 3.15in cap, so it can print only 5.2in wide.
     - Fig 4 is 4.45in tall with a 3.60in cap, printing 5.3in wide.
     - Fig 6 is also slightly narrower.
     - The current main.pdf is older than the new figures, so this is not yet visible in the PDF.
   - Fix: keep only `width=\linewidth` in `\includegraphics`. Or change the caps to fig1 4.0in, fig4 4.5in, fig6 3.55in. After the change it is still 21 pages. If Fig 4 is too cramped, draw it shorter, e.g. a 2×2 layout, rather than squeezing it with the cap.

2. **Fig 1 position**
   - Problem: it currently lands on page 3, after Table 1, while the tour text introducing it is on the previous page.
   - Fix: move the whole fig1_hook block to after introduction.tex l.44 (the nam2021direct sentence). It will land at the top of page 2, and Table 1 moves to page 3. This has been verified by compiling.

3. **Captions do not match the new figures (align them all at once after the figures are final)**
   - Problem:
     - The new Fig 4 has five panels a–e, but the caption still has a–d, so all letters are off by one.
     - The new Fig 2 has only two blocks left, the task and the timeline, but the caption still describes STATIC, text, two-way and KV-ALL/KV-PC.
     - The Fig 1 caption does not use a–f labels.
     - §5.5 never references Fig 4 from start to finish.
     - The (e) capability panels of Fig 3 and Fig 6 are not described in the captions.
   - Fix: rewrite the caption letters to match the new figures, then sync the appendix's figure/table provenance table, story_numbers and STORY §5.

4. **Narrow tables in the appendix**
   - Problem: most take up only 50–60% of the text-block width, and are stacked on top of each other.
   - Fix: merge Tables 12 and 13 into one (two column groups START | NOW, using `\cmidrule`). Put 17+19, 10+11 and 6+7 side by side with minipage, or stretch them to full width with tabularx. This can save half a page to a page.

5. **Closing sentence (account_and_discussion.tex:94)**
   - Problem: the paper's final sentence has been typeset inside the AI use statement.
   - Fix: move it before that heading. Change the heading to `\section*{AI use statement}`.

6. **Citation format (main.tex:9)**
   - Problem: multiple citations are separated by commas, so it is hard to tell which is which.
   - Fix: change to `\usepackage[round,semicolon]{natbib}`.

7. **Appendix pointers (setup.tex:77-78)**
   - Problem: the main text says the comparison ledger is in Appendix A, but it is actually Table 5 in Appendix B, and v1's is Table 15.
   - Fix: point to `\ref{tab:contrasts}` and `\ref{tab:v1contrasts}` instead. Remove "evidence ledger" from Appendix A's title.

8. **Small fixes**
   - Change B$\prime$ to B$'$; use `\qname` for readout names in the appendix tables.
   - Add `\widowpenalty` and `\clubpenalty` to prevent orphan lines at the top of pages.
   - Break the title manually so "Their Own" does not sit alone on a line.
   - Change the hand-written Figure~1 and Figure~6 to `\ref`.
   - The red TODO on page 21: either fill in the URL or delete it.
   - Do not let the verification notes in the refs.bib note fields print in the references.
   - Add `arXiv:xxxx` numbers to the preprint entries.

## (4) Could fix

1. In §5.1 change "13 switched" to "576 in both orderings, 13 in only one, 11 in neither".
2. Open §5.3 with the dose curve first: 0 at w≤0.3, 1.3% at 0.5, 51% at 1, 96–100% at 2–3.
3. After 57.1% add "about 50% if answered independently"; change Fig 3d's 2.2% to 2.3% (27/1200).
4. Small citation fixes:
   - At the Chalmers citation, change "argue against" to "judge it unlikely".
   - For self-recognition, add "against human-written text".
   - Change Pearson-Vogel to "a preprint reports it in one 32B Qwen model".
   - Give the page number at easy problems.
   - State that Bicameral is the structurally closest precedent.
   - Attach Stark to the "write residue" point.
   - Add a citation of yang2025qwen3 in Setup.
   - Note that the six criteria follow Lindsey's approach.
