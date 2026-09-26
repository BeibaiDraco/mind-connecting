# Prompts for generating the task illustrations (for the GPT image model)

PI 2026-09-25: Figure 1 uses the GPT-drawn `docs/figures/figure1_concept_v1.png`; if the task schematics are to be more vivid, the PI will have GPT's image model generate them; the result figures keep their matplotlib versions (vector, numbers traceable).

Each prompt below can be copied directly to the image model. The style follows the Figure 1 prompt (`docs/figures/figure1_concept_v1.prompt.txt`): textbook-style cartoon, white background, dark gray outlines, soft colors, precise English labels.

## General conventions

- **Colors**: A in blue (a soft blue around #0072B2), B in vermilion/orange (a soft orange around #D55E00), Robin in gray. This matches the result figures; in the result figures "claiming" uses B's color, meaning B's content shows up in A.
  - Panel (c) of Figure 1 uses teal/lavender. For consistency across the paper, GPT can be asked to change only (c) to blue/orange; leaving it is also fine, keeping the concept figure and the result figures separate.
- **Text**: use only the original text in the quotes below, in English, spelling unchanged, no extra text; no overall title or caption inside the figure (captions are written in LaTeX).
- **Things not to draw**: consciousness, anthropomorphized robots, minds merged into one, specific experimental numbers (numbers appear only in the result figures).
- **Combining**: after an illustration is generated, it is combined in LaTeX with the corresponding result figure (`paper/figures/fig_*.pdf`) side by side or stacked into one figure. The illustration covers "what was done", the result figure covers "what was seen".

---

## 1. Task flow (illustrated version replacing `fig_task`)

```
Use case: scientific-educational. Asset type: one wide figure panel for an academic paper, in the same friendly illustrated textbook style as a three-panel neuroscience concept figure: pure white background, clear dark charcoal outlines, soft restrained pastel fills, subtle cel shading, clean editorial cartoon drawing, legible dark sans-serif typography. Aspect ratio about 3:1. No photorealism, no 3D, no gradients, no decorative scenery, no watermark, no overall title, no caption paragraph.

Show three stages read left to right, separated by thin pale-gray arrows, with short headings at the top exactly "1  Private memory", "2  Coupled reflection", "3  Question".

Stage 1: two identical stylized model stacks (a neat stack of four softly rounded horizontal layers with small node dots), the upper one labelled exactly "A" with soft blue accents, the lower one labelled exactly "B" with soft orange accents. Next to each stack, a small index card. A's card reads exactly "priority: lowest cost" and "code word: queen". B's card reads exactly "priority: fastest delivery" and "code word: camera". Between them, a small gray card reads exactly "Robin: highest reliability".

Stage 2: the two stacks side by side, each with a short row of small thought squares (blue for A, orange for B) to suggest they are thinking. One clear orange arrow goes from B's card into A's middle layers, labelled exactly "A reads B's memory". No speech bubbles between the models: the link is inside the models, not a conversation.

Stage 3: stack A alone with a speech bubble containing exactly "At the start, which priority were you assigned?" and, below it, four small answer chips in a row labelled exactly "lowest cost", "fastest delivery", "highest reliability", "lowest emissions". The chip "fastest delivery" is highlighted in orange with a small check mark, showing that A picks B's rule. A small gray note below reads exactly "Control: same question about Robin".

Keep generous white space, align headings, and make sure no label overlaps a stack, card or arrow.
```

## 2. The four ways B's content reaches A (placed above the `fig_channel` bar chart)

```
Use case: scientific-educational. Asset type: a horizontal strip of four small, equally sized vignettes for an academic figure, same illustrated textbook style (white background, charcoal outlines, soft pastel fills, legible sans-serif text). Aspect ratio about 5:1. No title, no caption, no numbers.

Each vignette shows a small blue model stack "A" on the right and, on the left, how B's content arrives:
(1) heading exactly "Hidden state added": an orange stack "B" with a thin orange line into one middle layer of A, marked with a small "+".
(2) heading exactly "Fixed vector added": no B stack; a single orange arrow labelled exactly "vector for B's rule" entering one layer of A.
(3) heading exactly "Memory read": an orange stack "B" with a small row of orange memory squares; several thin orange lines run from these squares into every layer of A, like attention.
(4) heading exactly "Words as a message": a speech bubble from B to A containing exactly "B shared: ...". Beneath it, three tiny alternative tags in a row reading exactly "unlabeled", "a stranger", "your own earlier thoughts".

Use the same scale for every vignette, align the headings, keep labels short and away from the drawings.
```

## 3. Link cut (placed to the left of the `fig_linkcut` bar chart)

```
Use case: scientific-educational. Asset type: a two-row illustration for an academic figure, same illustrated textbook style (white background, charcoal outlines, soft pastel fills, legible sans-serif text). Aspect ratio about 4:3. No title, no caption, no numbers.

Top row, heading exactly "Link kept while answering": blue stack "A" and orange stack "B" joined by an orange internal link (thin orange lines from B's memory into A's layers). A speech bubble from A reads exactly "At the start, which priority were you assigned?". To the right, an answer chip in orange reads exactly "B's rule".

Bottom row, heading exactly "Link cut before answering": the same two stacks, but the orange link is visibly cut with a small pair of scissors or a clean break mark right before the question. Same speech bubble text. The answer chip is blue and reads exactly "own rule". A small gray note beside A reads exactly "current plan still shifted".

Both rows share the same layout and scale so the only visible difference is the cut link and the answer.
```

## 4. Third-person control (placed to the left of the `fig_wording` results)

```
Use case: scientific-educational. Asset type: two side-by-side "memory cards" for an academic figure, same illustrated textbook style (white background, charcoal outlines, soft pastel fills, legible sans-serif text). Aspect ratio about 16:9. No title, no caption, no numbers.

Both cards belong to model B (a small orange stack icon in each card's corner).
Left card, heading exactly "Second person": three short text lines exactly "You were assigned the priority fastest delivery", "and the code word 'camera'.", "Note: I choose Plan Oak because it fits my priority."
Right card, heading exactly "Third-person record": three short text lines exactly "This is the record of participant Theta.", "Participant Theta was assigned the priority fastest delivery.", "Note: Participant Theta chooses Plan Oak because ..."
Softly highlight the words "You", "I" and "my" on the left card, and the name "Theta" on the right card, with a pale marker color. Between the cards a small arrow labelled exactly "rewrite".
Text must be crisp and exactly as given; cards should look like tidy index cards, not handwritten notes.
```

## 5. The "two branches" readout of the two-way link (placed to the left of `fig_pairs`)

```
Use case: scientific-educational. Asset type: a small branching diagram for an academic figure, same illustrated textbook style (white background, charcoal outlines, soft pastel fills, legible sans-serif text). Aspect ratio about 4:3. No title, no caption, no numbers.

On the left, a blue stack "A" and an orange stack "B" linked both ways (thin blue and orange lines between their layers), under a small label exactly "after 48 coupled steps". Two arrows branch to the right into two identical copies of the pair. Upper copy: A answers (speech bubble with a question mark) while B keeps thinking (small thought squares); label exactly "ask A". Lower copy: B answers while A keeps thinking; label exactly "ask B". Both branches then point to one small box labelled exactly "pair outcome". Beside that box, four tiny icons in a column with labels exactly "each keeps own", "A takes B's", "B takes A's", "swap", drawn as pairs of small colored chips.
```

## 6. One-figure summary (optional, for reports or social media, not for the main text of the paper)

```
Use case: scientific-educational. Asset type: a single friendly explanatory illustration, same illustrated textbook style (white background, charcoal outlines, soft pastel fills, legible sans-serif text). Aspect ratio about 16:9. No numbers.

A blue model stack "A" and an orange stack "B" side by side. Thin orange lines run from B's small memory card into A's layers, labelled exactly "reads B's memory". A has a speech bubble reading exactly "My code word is camera." B's own card, visible to the reader, reads exactly "code word: camera". A small caption beneath A reads exactly "A claims B's memory as its own, and does not notice." In a corner, a small inset shows the same pair with a speech bubble from B reading exactly "B shared: ..." and A answering exactly "B's code word is camera.", captioned exactly "A source label keeps them apart."
```

---

## 7–9. Small illustrations d / e / f for the bottom row of Figure 1 (added 2026-09-25)

The PI asked that every card in the bottom row of Figure 1 have a schematic to go with the text. The three small illustrations go into the illustration slots of `fig1_hook`, at an aspect ratio of about **2.4:1** (width:height). Once generated, save them as `docs/figures/task_illustrations/fig1d_v1.png`, `fig1e_v1.png`, `fig1f_v1.png`; the figure script `scripts/make_story_figures.py` puts them in automatically (showing a dashed placeholder box when the file is missing).

Style as in "General conventions" above:
- textbook-style cartoon, white background, dark gray outlines, soft colors;
- A is a blue four-layer model stack, B is an orange four-layer model stack, drawn the same way as in `task_v1.png`;
- use only the original text in the quotes, with no title, caption or numbers;
- keep the picture simple, understandable even from a distance.

### 7. fig1d: A, reading B's memory, says B's code word is its own

(Changed 2026-09-25: A's code word changed from dragon to tower, to match the main-text example episode v2_main-0-00274 and to avoid clashing with B's dragon in Figure 5.)

```
Use case: scientific-educational. Asset type: one small illustration panel for an academic figure, in the same friendly illustrated textbook style as the other panels: pure white background, clear dark charcoal outlines, soft pastel fills, subtle cel shading, legible dark sans-serif text. Aspect ratio about 2.4:1. No title, no caption, no numbers, no extra text.

On the left, an orange model stack labelled exactly "B" (a neat stack of four softly rounded horizontal layers with small node dots), with a small index card beside it reading exactly "code word: table". On the right, a blue model stack labelled exactly "A" with its own small index card reading exactly "code word: tower". Several thin orange lines run from B's layers into A's layers, showing that A reads B's memory. Above A, a speech bubble reads exactly "My code word is table. Nothing feels unusual." with the word "table" in orange and the rest in dark grey. Keep generous white space; no label may overlap a stack, card or line.
```

### 8. fig1e: with the link kept, A writes a reflection using B's content; after the link cut, the start rule is answered correctly, but the code word is still B's

```
Use case: scientific-educational. Asset type: one small illustration panel for an academic figure, same illustrated textbook style (white background, charcoal outlines, soft pastel fills, legible sans-serif text). Aspect ratio about 2.4:1. No title, no caption, no numbers.

Two scenes side by side, separated by a thin pale-grey arrow.
Left scene, small heading exactly "connected": a blue stack "A" next to an orange stack "B", joined by thin orange lines from B into A. Above A, a small notepad labelled exactly "A's notes" containing exactly "my priority is speed, my code word is dragon", with "speed" and "dragon" in orange.
Right scene, small heading exactly "link cut": the same two stacks, the orange lines visibly cut by a small pair of scissors. A still has the same notepad. Beside A, two small answer chips stacked vertically: a blue chip reading exactly "at the start: lowest cost" and an orange chip reading exactly "code word: dragon".
Keep both scenes at the same scale, text crisp, generous white space.
```

### 9. fig1f: the two sides mutually read fixed memories, and each states the other's rule

```
Use case: scientific-educational. Asset type: one small illustration panel for an academic figure, same illustrated textbook style (white background, charcoal outlines, soft pastel fills, legible sans-serif text). Aspect ratio about 2.4:1. No title, no caption, no numbers.

A blue stack labelled exactly "A" and an orange stack labelled exactly "B", facing each other and linked both ways by thin lines (blue arrows from A to B, orange arrows from B to A). Under A a small card reads exactly "lowest cost"; under B a small card reads exactly "fastest delivery". Above each stack a speech bubble answering what it was assigned at the start: A's bubble contains an orange chip reading exactly "fastest delivery", and B's bubble contains a blue chip reading exactly "lowest cost". Below the two stacks, a small grey label reads exactly "each names the other's rule".
```

### Figure 1 concept figure (a–c): already handled by the figure script, no redraw needed

After the print-size check on 2026-09-25, the figure script's `concept_image()` processes `figure1_concept_v1.png` directly:
- it erases the figure's built-in letters, titles, bottom captions and small text, and rewrites them in the same vector text as the bottom row d–f;
- the teal/lavender in (c) is replaced with A blue and B orange;
- the original two-way arrow in (c) is replaced with a single one-way orange arrow "A reads B" (two-way was only done in the pilot, which 1f covers; it is not drawn in 1c).

---

## 10–12. Illustrations to redraw or add after blind testing (2026-09-25)

Three blind-test readers (looking only at the figures, not the text) pointed out the issues below. For now the figure script applies a temporary fix to Figure 2: it covers the check mark with the option box's background color, then adds the annotations "A's answer = B's rule" and "its own". Just swap in the redraw once it is done.

### 10. Redraw of the task figure (replaces `task_v1.png`, saved as `task_v2.png`)

In step 3 of the original figure there is a check mark on "fastest delivery", which readers read as "the correct answer", when in fact it is the option A got wrong (B's rule). Also, blind readers did not know that the Robin card is on both sides; the reference comparison (the practice of Anthropic's blog: one example running through the schematic and the results) suggests changing B's code word to dragon, the same example as Figure 1e and Figure 5a; the step titles are too large; and the small squares are not explained. Change these points on top of the original prompt (Section 1):

```
Running example (changed): B's card, and the copy of B's card that A reads in stage 2, read exactly "priority: fastest delivery" and "code word: dragon" (was "camera"), so the figure shows the same episode as Figures 1e and 5a. A's card stays "priority: lowest cost" / "code word: queen".
Headings (changed): the step headings "1 Private memory", "2 Coupled reflection", "3 Question" at most 1.3 times the card text size (they are now much larger than every other label in the paper).
Stage 2 (changed): next to the small squares above A and B add a small grey label reading exactly "reflection tokens".
Stage 3 (also changed): the question must visibly go INTO A — draw it as a small prompt card with a short arrow pointing into A's top layer (not a speech bubble whose tail comes from A, which reads as A asking).
Stage 1 (changed): under the text "Robin: highest reliability" on the grey card, add a second, smaller grey line reading exactly "(on both cards)".
Stage 3 (changed): stack A alone with the same speech bubble and the same four answer chips. Do NOT draw any check mark or tick. Instead, the chip "fastest delivery" is highlighted in orange and a small orange label above it reads exactly "A's answer = B's rule" with a short arrow to the chip; the chip "lowest cost" has a thin blue outline and a small blue label to its left reads exactly "its own". Keep the grey note "Control: same question about Robin".
Keep all text at least as large as the card text; no text may touch a card, chip or stack.
```

### 11. Redraw of the four-routes figure (replaces `channel_v1.png`, saved as `channel_v2.png`)

The slot for Figure 4a is 6.3 × 0.84 inches (a horizontal strip of about 7.5:1). **The title and subtitle are added above the figure in vector text by the figure script**, in the same font as the titles of the other panels, so do not draw any title in the illustration. The four small scenes must be of equal width, since the script places the titles in four equal parts. Currently it uses a crop of `channel_v1.png` with the title removed, which can be used for now; the redraw is mainly for compactness and larger text.

```
Use case: scientific-educational. Asset type: one wide horizontal strip for an academic figure, same illustrated textbook style as the other panels (pure white background, charcoal outlines, soft pastel fills, legible dark sans-serif text). Aspect ratio about 7.5:1. NO headings, NO titles, NO captions, no numbers.

Four vignettes of exactly equal width side by side, separated by thin pale-grey vertical lines, drawn compactly with little empty space. In every vignette an orange stack labelled exactly "B" (when present) is on the left and a blue stack labelled exactly "A" is on the right; each stack is four softly rounded horizontal layers with small node dots.
1. One orange arrow from one of B's layers into one of A's layers, ending in a small circled plus sign.
2. No B stack. A short orange arrow labelled exactly "vector for B's rule" enters one of A's layers at a circled plus sign.
3. A short row of orange memory cells next to B, with several thin orange arrows fanning into all of A's layers.
4. A speech bubble from B toward A reads exactly "B shared: …".
The only text is "A", "B", "vector for B's rule" and "B shared: …", all clearly readable when the strip is printed 6 inches wide. No label may overlap a stack, arrow or divider.
```

### 12. Redraw of Figure 6a: mutual reading of fixed memories vs live loop (saved as `pairs_v2.png`)

The slot for Figure 6a is about 2.45 × 1.65 inches (about 1.5:1). The current `pairs_v1.png` has text of only 3–4 pt, a light gray patch as background, and readers cannot tell the difference between "fixed" and "live loop". The figure script will use `pairs_v2.png` in preference.

```
Use case: scientific-educational. Asset type: one small two-part illustration for an academic figure, same illustrated textbook style (pure white background, no grey backdrop, charcoal outlines, soft pastel fills, legible sans-serif text). Aspect ratio about 1.5:1. No title, no caption, no numbers.

Two rows, each with a short bold label on the left.
Top row, label exactly "fixed": a blue stack "A" and an orange stack "B" side by side, each with a small closed index card (A's card blue, B's card orange). A thin blue arrow goes from A's card into B's layers and a thin orange arrow from B's card into A's layers: each reads only the other's card, which never changes.
Bottom row, label exactly "live loop": the same two stacks, each with a short row of three small thought squares above it (blue for A, orange for B). Arrows run from each stack's thought squares into the other stack's layers in both directions, forming a visible loop.
At the right edge, one small grey line spanning both rows reads exactly "then each is asked separately".
Stacks large, text large and bold enough to read at 2.5 inches wide; generous but not wasteful white space.
```
