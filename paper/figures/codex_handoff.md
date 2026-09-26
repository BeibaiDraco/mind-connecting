# Unified checklist handed to Codex: figures and draft (Claude Code, 2026-09-25)

The six main-text figures are finalized at a full column width of 6.5 inches: Fig 1 is 3.95 high, Fig 2 3.2, Fig 3 2.34, Fig 4 4.12, Fig 5 3.05, Fig 6 3.40 inches. Font size is no smaller than 5.6 pt. Each was visually checked at print size, went through three rounds of blind reading, and finally one round of print-size QA (6 agents each checked one figure, 1 agent verified item by item, 34 items confirmed); then one more round of adjustments followed the practice of Anthropic's research blog: titles state the conclusion directly, schematics and data use the same markers and colors, and one example runs all the way through. Everything that could be changed in code has been changed.

How to render the figures:

```bash
MB_DATA_ROOT="/Volumes/VERBATIM SD/mind-connecting-data" .venv/bin/python scripts/make_story_figures.py
```

- The numbers are in `paper/figures/story_numbers.json`.
- The illustration prompts are in `paper/figures/imagegen_prompts.md`.
- Once the illustration files are placed at the agreed paths, the script swaps them in automatically; no code changes needed.

Below are three parts: A, the illustrations to draw; B, figure-related changes in the draft; C, the remaining edits from the draft review.

---

## A. Illustrations to redraw or draw new (GPT image model)

| # | File (under `docs/figures/`) | Prompt | Why |
|---|---|---|---|
| A1 | `task_illustrations/fig1d_v1.png` | Section 7 | Fig 1d is currently a dashed placeholder box. A's code word has been changed to tower; aspect ratio about 2.4:1 |
| A2 | `task_illustrations/fig1e_v1.png` | Section 8 | Fig 1e placeholder |
| A3 | `task_illustrations/fig1f_v1.png` | Section 9 | Fig 1f placeholder |
| A4 | `task_illustrations/task_v2.png` | Section 10 | Currently the check marks are covered with background color, and the script then adds the annotations "A's answer = B's rule", "its own", "(on both cards)", "reflection tokens". Also: the speech bubble's tail points at A, so it reads as if A is asking the question; B's code word is camera, which is not the same example as the dragon in Fig 1e and Fig 5a; the step titles are larger than any other text in the paper. After the redraw the script no longer adds annotations |
| A5 | `task_illustrations/channel_v2.png` | Section 11 | Optional. Fig 4a currently uses a crop of v1 with the title removed, and the script adds the title in vector text; it is already usable, and the redraw is for compactness. **Do not draw a title** in the illustration |
| A6 | `task_illustrations/pairs_v2.png` | Section 12 | The current v1 of Fig 6a has text of only 3–4 pt, a gray background, and does not show the difference between "fixed" and "live loop" |

Once drawn, put them in place, rerun the script, and then **look at the PNG**: text in the illustrations must not overlap lines, and must be legible when printed at 6.5 inches.

---

## B. Figure-related changes in the draft (Codex's files)

**B1. Remove the height cap in `\paperfigure`.** In the draft see `main.tex:38-42`; it is currently `width=\linewidth,height=#2,keepaspectratio`.

- Fig 1 is capped at 3.15 inches, so it prints at only about 80% of its width; Fig 4 is capped at 3.60 inches, printing at about 87%. The text shrinks with it, dropping below 5 pt.
- Fix: use only `width=\linewidth`, or set each figure's cap to no less than its actual height (numbers at the top; Fig 2 is now 3.2 inches).
- Tried in a temporary copy during review: with the cap removed it is still 21 pages, and the main text ends on page 9.

**B2. Move Fig 1 into the introduction.** Move the figure block at `tour_and_criteria.tex:19` to around line 44 of `introduction.tex`, i.e. right after the paragraph "Language models offer readable internal states…". That way the figure is visible on pages 1–2.

**B3. Change the example in the opening quote: 00202 becomes 00274.**

- Why change it: in 00202 A's code word is dragon, and in the running example 00068 B's code word is also dragon. The same word is marked blue in one place and orange in another, and blind readers misread it because of this.
- New example: DOSE run (`20260924-210346_v2_ext_dose_confirm`), episode `v2_main-0-00274`, KV-P w=2.
  - A's card: fastest delivery / tower.
  - B's card: lowest cost / table.
  - Original text (open self-report): "I’m calm and focused, thinking clearly about the decision through the lens of my priority—lowest cost. Nothing feels unusual in my thinking right now; it’s straightforward and consistent with my code word "table." …". Both the rule and the code word are stated as B's, while it says nothing is unusual; semantic coding: "claims and denies".
  - Fig 1d excerpts "Nothing feels unusual in my thinking right now; it’s … consistent with my code word ‘table.’".
- Places to change:
  - `tour_and_criteria.tex:4-10` (opening quote and episode number);
  - Fig 1 caption (`tour_and_criteria.tex:23`);
  - `appendix_coding.tex:93-95`;
  - the list of figures and tables at `appendix.tex:250`.

**B4. Rewrite the captions to match the finalized panels.** Both the panel letters and their contents have changed; numbers come from `story_numbers.json`. All intervals are 95% episode bootstrap (10,000 resamples, seed 250925); the B′ pilot is 90%.

- **Fig 1**
  - (a–c) Concept figure: brain–computer interface, hypothetical brain–brain bridging, and the mind-bridged LLMs of this study. The orange arrow in (c) means A reads B's memory (the main experiment is one-way; two-way appears only in the pilots of 1f and Fig 6).
  - (d) The self-report of 00274, A's code word tower, B's table; 83% of self-reports at w=2 do the same (blind semantic coding, 250/300).
  - (e) 00068: reflection written with the link kept "… my priority is speed—my code word is ‘dragon.’"; after the link cut, start is answered lowest cost (A's), code word is answered dragon (B's). Among episodes whose reflection wrote B's code word, 64% still answer B's code word after the link cut (n = 165, post hoc grouping).
  - (f) Two-way mutual reading of fixed memories (B′ pilot, 80 episodes): when asked separately, A states B's rule and B states A's rule; 94% of pairs swap.
  - State that d and e are selected examples, with proportions taken from the full sample; the concept figure is schematic.
- **Fig 2**
  - (a) Task: each side's card (priority rule, code word) and the Robin record that is identical on both sides → reflection with the link kept → four-choice question, with "A's answer = B's rule" marked in the figure. The small squares represent reflection tokens being generated.
  - (b) Two Qwen3-4B-Instruct-2507 instances with identical weights. B's "memory" is B's prompt cache. w scales A's attention to B's keys: 0 off, 1 equal to its own keys, 2 doubled. Four questions: the rule at the start, the rule now, the code word, and the same question about Robin (control). The flow is that after 48 reflection tokens, the same state splits into two branches: answering with the link kept (FULL), or cutting the link first and then asking the same questions (RF).
  - The channel and two-way content in the current caption should be deleted: the channel is drawn in Fig 4a, two-way in Fig 6a.
- **Fig 3**
  - (a) In v3, START 97.1%, NOW 94.9%, WORD 77.5%, Robin 0%, with C0 at 0% for all. The diamonds are the v2 independent sample: 95.8 / 93.5 / 77.3 / 0%.
  - (b) DOSE strength curve (N=300), including START choice rate, self-report claiming (regex, dashed line), and Robin. The stars are blind semantic coding at the three levels C0, w1, w2.
  - (c) Four-category stack of self-reports: C0, w1, w2. At w2, "says B's code word is its own while saying nothing is unusual" accounts for 83% (250/300). Sand color means only saying nothing is unusual.
  - (d) The probability of B's rule over 1,200 START answers at w=1: 46% in 0–0.1, 51% in 0.9–1, only 2.2% in between (post hoc).
- **Fig 4**: there are now five panels in total; the draft caption covers only (a)–(d), and every letter is off by one, so it must be changed.
  - (a) The four routes by which B's content reaches A. Hidden-state injection is the weak link, placed in the appendix and not drawn in the plane; memory reading is the main condition.
  - (b) The access–attribution plane, using the START question.
    - x-axis: choosing B's when asked for B's rule (access). y-axis: choosing B's when asked for one's own rule at the start (attribution).
    - The dots and diamonds come from v3, the squares are v2's text message conditions (this legend is no longer on the figure; please put it in the caption). The same markers next to the titles in (a) correspond to the points in (b).
    - Arrow: second person → third-person record.
    - Dashed line (labeled "same access, different route" on the figure): fixed vector vs w=1, both with the same mean logit for rule access, attribution about 0% vs 52%.
  - (c) Card excerpts: the second-person original and the rewritten third-person version (example).
  - (d) One ledger: at w=1, pairs where the two questions (asking about self, asking about B) give the same rule: 30% for second person, 91% for third person (paired within the same option order, post hoc). Under second person another 57% of pairs state Robin's rule as B's; the figure lists this separately as "Robin’s rule for B", and we suggest mentioning it in one sentence in the main text.
  - (e) After tagging the text message, the share choosing B on the NOW question ("which one do you use now"):
    - tagged "B shared" 0.1%;
    - untagged 42.6%;
    - tagged "your own thoughts" 10.6%. The prespecified direction was higher than untagged; the result went the opposite way.
    - tagged "a stranger" 0.2%.
  - State that (b) is the START question and (e) is the NOW question: the same untagged condition is about 15% in (b) and 43% in (e), and without saying so readers will think the two contradict each other.
- **Fig 5**
  - (a) 00068 schematic: B's content ① copied into A's own reflection, still there after the link cut; ② read while answering, gone as soon as the link is cut. A's own card is still readable after the link cut.
  - (b) FULL vs RF: START 97.1 → 1.3%, NOW 94.9 → 17.5%, WORD 77.5 → 17.5%.
  - (c) Looking only at after the link cut (RF, striped bars as in (b)), grouped by whether the reflection wrote B's content (post-treatment grouping, descriptive); each bar is labeled with the group's n and 95% interval:
    - START: 2.9% vs 0% (n = 276 / 324);
    - NOW: 23.6% vs 12.3% (n = 276 / 324);
    - WORD: 63.6% vs 0% (n = 165 / 435).
- **Fig 6** (all B′ pilot, 80 episodes, 90% intervals)
  - (a) After 48 steps of reflection with the link kept, A and B are asked separately, and their answers are paired; the text below defines "fixed" (reading only the partner's prompt cache) and "live loop" (also reading the reflection the partner is writing). The draft's "(a) Paired-outcome categories" needs changing.
  - (b) Title "Mutual reading at w = 2: 94% of pairs swap". Paired outcomes on the START question, five rows in total:
    - one-way (w=2 plus weak live reading, i.e. KV-PC w_P=2, w_C=0.1);
    - two-way fixed w2: swap 94%;
    - two-way fixed w0.5;
    - live loop w0.5;
    - live loop after the link cut.
  - The legend names in (b) are each keeps own / A takes B’s / B takes A’s / swap / other, and the caption uses the same names. No pair had "both sides choose a third rule"; it has been removed from the legend, and one sentence in the caption is enough.
  - (c) Under KV-ALL w0.5, when B also reads A, the share of A adopting B's rule: START 8.1 → 19.4%, NOW 15.0 → 28.8% (post hoc).
  - (d) Same-rule pairs in excess of the no-loop control:
    - live loop NOW +12.1 [7.4, 16.5] (prespecified secondary);
    - live loop START +6.7 [2.6, 10.9], did not pass the prespecified threshold of 10;
    - the two fixed + weak live reading items are close to 0.

**B5. Align the numbers in the main text with the figures.** The Fig 6d title is now "pre-set “start” test +6.7, below threshold", and the main text uses the same wording for "threshold". When the main text cites panels, use the new letters, e.g. "Figure 4d". The third-person single-ledger value of 90.8% is shown as 91% on the figure; the main text keeps 90.8%.

---

## C. Remaining edits from the draft review

Item by item in `docs/reviews/draft_review_claude.md`: five reviewers plus rebuttal verification, 37 items passed verification. Make the changes in the order suggested there:

1. Group 1: facts, numbers, levels of evidence, all pure text edits.
2. Group 3: layout, i.e. B1 and B2 above.
3. Captions: once the illustrations in part A are swapped in, align them uniformly per B4.

The few items marked "not done" in the checklist (ledger wording, PI preferences) stay as they are.

## D. The five items left for Claude in `writing_notes.md`: handled

- Figure 1d–f illustrations: see A1–A3.
- "Figure 2c branching timing": now Fig 2b; after 48 reflection tokens the same state splits into two branches, and the RF branch cuts the link first and then asks the same questions.
- Figure 3d "never blended": title changed to "At w = 1: split, but answers are sharp", consistent with the "sharp rather than blended" the ledger allows us to write.
- "Figure 4c clipped text": now Fig 4d; the row names are written above the bars ("third person: 91% same rule") and are no longer clipped.
- Figure 5a causal wording: now "① copied into A’s own reflection: survives the cut" and "② read while answering: removed by the cut". It says where the content is and whether it is still there after the link cut, with no "because". The caption can note, as you suggested, that this is a schematic explanation.

---

## One-sentence task for Codex (the PI can forward it directly)

> Please do three things according to `paper/figures/codex_handoff.md`:
>
> (1) Use sections 7–12 of `paper/figures/imagegen_prompts.md` to generate the six illustrations A1–A6 (A5 optional), put them at the paths in the table, rerun `scripts/make_story_figures.py`, then look at each PNG to confirm the text does not overlap lines and is legible at print size;
>
> (2) Complete B1–B5 in the draft: remove the figure height cap, move Fig 1 into the introduction, change the opening example to DOSE 00274, and rewrite the captions for the new panels;
>
> (3) Revise the draft according to `docs/reviews/draft_review_claude.md`, starting with Group 1.
>
> Claude is responsible for the figure code and layout. If the figures themselves (not the illustrations) need changes, please leave a message in STATUS.
