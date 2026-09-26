# Paper and figure plan (draft, for review by the PI and Codex)

Date: 2026-09-25. Author: Claude Code. Status: draft plan; writing of the main text has not started. The paper is written by Codex (PI decision).

> **2026-09-25 update**: Sections 1–4 of this document (claims, title, structure, contributions) have been superseded by `paper/STORY.md`, which incorporates the corrections from the Codex review (`docs/reviews/paper_plan_review_codex.md`); the figure rationale from Section 5 onward can still be consulted.

- Results relied on: `docs/results/ALL_RESULTS.md` (all raw results) and `docs/results/summary_2026-09-25.md` (summary).
- Figures: `paper/figures/`; the figure booklet is at `paper/figures_booklet.pdf`.

## 1. What the paper says

### 1.1 One sentence

For two copies of the same language model, as soon as one's attention can read the other's memory, it takes the other's private information as its own, without noticing. What decides "whose it is" is the way the information enters, not the information itself. This is a source error at the moment of recall, not a rewriting of memory; it is not caused by the grammatical-person wording; and two-way connection does not merge the two into one either.

### 1.2 Title candidates

1. *Mine or Yours? Language Models That Read a Partner's Memory Claim It as Their Own* (recommended: picks up Figure 1's "Mine or yours?" and states the main finding in one sentence)
2. *Reading Another Model's Memory Makes Language Models Misattribute Its Source*
3. *Whose Memory Is It? Source Misattribution Between Coupled Language Models*

### 1.3 Claims and evidence (each claim in the paper uses only evidence of matching strength)

| ID | Claim | Evidence | Evidence level |
|---|---|---|---|
| C1 | Reading the partner's memory leads to claiming: specific to "me", follows the content, capability unimpaired | v2 D +55.8; G2-KV (rule +38.8, lower bound +34.3); E +52.5; self questions +59 vs Robin question +3.5 | Confirmatory (600 episodes) |
| C2 | Does not notice | Open self-report: at w2, 99% treat B's code word as "my code word" and hardly mention B; in closed self-report, "two minds" answers actually decrease | Descriptive (stated as such) |
| C3 | The channel decides ownership | A′: with matched information, memory reading +33.4, static direction about 0; C: language tag +26.6; v1: weak residual bridge, no claiming | Confirmatory (A′, C); v1 is a confirmatory negative |
| C4 | It is an error at retrieval, and it leaves a trace | connected − cut +54.8; after the cut M_NOW +13.3 | Confirmatory |
| C5 | Not caused by wording | T3-K\* equivalence test (−0.7, bound −11.3); T3-w1 −3.2 (secondary, while the third-person version is easier to decode) | Confirmatory (equivalence test) + secondary comparison |
| N1 | Connection is not merging | Neither B′ family passed its threshold; mutual reading of fixed memories mostly gives swaps; the live loop adds only +0.07 one-side-wins, which disappears once the link is cut | Pilot, did not pass the prespecified threshold (stated as such) |
| N2 | A weak link does not cause claiming | v1: TWO − ONE −0.07; the residual bridge shifts self questions and the Robin question equally | Confirmatory negative |

**What not to write**: consciousness, number of minds, "merging into one" or "phase transition". Discuss only functional source attribution (AGENTS.md §5.7).

### 1.4 Contributions (listed at the end of the introduction)

1. We identify and quantify a risk no one has measured before: latent communication between models can make the receiver lose the provenance of information. Previous work of this kind looked only at accuracy and efficiency (references in `paper/refs_verification.md`; phrase it as "to our knowledge").
2. With preregistered, strength-matched experiments, we separate "amount of information" from "ownership": given the same information, memory reading leads to claiming, the static direction does not, and neither does source-tagged language.
3. We localize the mechanism: the error occurs at the moment of retrieval (it recovers once the link is cut), but it leaves a trace on the current intention. This matches human source-monitoring research.
4. We rule out the main alternative explanation: grammatical-person wording. We also report that two-way connection does not bring merging.
5. Method: a reusable paradigm, including three frozen protocol versions, strength thresholds, content counterfactuals, channel swaps, a third-person control and link-cut answering. All trial records are public.

## 2. Structure and length (planned for an ICML/NeurIPS main text of about 9 pages)

| Section | Content | Length | Figure |
|---|---|---|---|
| 1 Introduction | Brain-bridging thought experiment → a controllable version on two identical models; the state of latent communication; this paper's question; contributions | 1 page | Fig. 1 |
| 2 Related work | Latent communication between models (activations, KV cache, LatentMAS, C2C, KVComm, etc.); activation steering; model introspection and self-recognition; human source monitoring and sense of ownership | 0.75 page | — |
| 3 Paradigm and methods | Task and private memory (rule, code word, Robin control); four channels; readout questions and metric M; preregistration procedure (thresholds, parameter-selection rules, N, Holm, equivalence test) | 1.75 pages | Fig. 2 |
| 4.1 Memory reading leads to claiming | C1 and C2 | 1 page | Fig. 3 |
| 4.2 The channel decides ownership | C3 | 0.75 page | Fig. 4 |
| 4.3 An error at retrieval | C4 | 0.6 page | Fig. 5 |
| 4.4 Not the wording | C5 | 0.6 page | Fig. 6 |
| 4.5 Connection is not merging | N1, briefly | 0.3 page | Appendix figure |
| 5 Discussion | The source-monitoring analogy; implications for multi-agent latent communication (provenance labeling, channel isolation); limitations; a second model | 1 page | — |
| 6 Conclusion | — | 0.2 page | — |
| Statements | AI use statement (required); reproducibility statement (freeze tags, records, scripts) | — | — |
| Appendix | A materials and prompts; B interface math and tests; C research process and all pilots; D all results tables; E strength sweep; F two-way outcomes and the excess method; G T3/T3b details; H engineering checks | Unlimited | Appendix figures A1–A5 |

## 3. Figure plan

### 3.1 Main text: 6 figures

| Figure | Content | File | Claim it supports |
|---|---|---|---|
| 1 | Concept: brain–computer interface → brain bridging → two coupled models | `docs/figures/figure1_concept_v1.png` (GPT, chosen by the PI) | Motivation |
| 2 | Task flow: private memory → reflection while connected → question, A picks B's rule | `docs/figures/task_illustrations/task_v1.png` (GPT) | Paradigm |
| 3 | Main result: (a) self questions vs Robin question; (b) content counterfactual; (c) capability; (d) closed self-report | `paper/figures/fig_main.pdf` | C1, C2 |
| 4 | Channels: illustration strip (four channels) + bar chart (M and M_NOW) | `channel_v1.png` + `fig_channel_data.pdf` | C3 |
| 5 | Link cut: illustration (connected / cut) + bar chart of three metrics | `linkcut_v1.png` + `fig_linkcut_data.pdf` | C4 |
| 6 | Wording control: two versions of the memory card + dot plot at two strengths | `wording_v1.png` + `fig_wording_data.pdf` | C5 |

### 3.2 Appendix

| Figure | Content | File |
|---|---|---|
| A1 | Strength curve and open self-report | `fig_dose.pdf` |
| A2 | Two-way connection: readouts of the two branches + paired outcomes | `pairs_v1.png` + `fig_pairs_data.pdf` |
| A3 | Reading interface (methods) | `fig_interface.pdf` |
| A4 | Overview of the research process (three protocol versions, each gate and its conclusion, including negative results) | `fig_program.pdf` |
| A5 | One-page summary (can serve as a graphical abstract, if the conference allows) | `fig_summary.pdf` |

Figure for talks, not for the paper: `summary_v1.png` (GPT one-image summary). Backup vector version of the task figure: `fig_task.pdf`.

### 3.3 Why this arrangement and this drawing style

**Story order**: phenomenon → specificity → mechanism → ruling out alternative explanations → boundaries.

- Reviewers must first be convinced that the phenomenon is real, specific to "me", and follows the content (Fig. 3) before they will care about the mechanism.
- Channels (Fig. 4) and the link cut (Fig. 5) answer "how does it happen"; the wording control (Fig. 6) answers "is it an artifact".
- The negative result (merging did not happen) goes last, to frame the boundaries of the conclusions.

**One figure, one claim**: each main-text figure answers only one question, and its title states the conclusion directly, so readers can understand it without reading the main text.

**Illustration + data**: task-type figures are composed as "left or top: what was done (GPT illustration); right or bottom: what was seen (vector data plot)".

- Readers understand the manipulation first, then see the results, without searching the main text for condition names.
- The PI likes this style, and it is consistent with Fig. 1.
- The data parts stay vector, and the numbers can be traced back to the raw records (`numbers.json`).

**Why Fig. 3 has these four panels**: each panel rules out one alternative explanation.

- (a) the Robin question as a control rules out "B's rule is just more salient";
- (b) the content counterfactual rules out "any perturbation makes it answer at random";
- (c) capability rules out "the model has been broken";
- (d) self-report corresponds to "does not notice".

**Why Fig. 4 plots both M and M_NOW**:

- The language channel's effect on "which rule now" (+25) is much larger than its effect on "which rule assigned at the start" (+10); memory reading affects both equally.
- This difference is itself informative: language changes intention, while memory reading changes memory ownership.
- Icons and bars align one to one, so the independent variable (channel) is visible at a glance.

**Why Fig. 5 plots three metrics**: after the cut the three come apart—"which rule assigned at the start" largely recovers (+1.9), "which rule now" stays shifted (+13.3), and B's content can hardly be read out any more (+3.8). This separation is exactly what supports "a source error at retrieval + a trace left behind"; plotting only one metric would not show it.

**Why Fig. 6 plots two strengths**:

- At the main strength (w=2) claiming is saturated, which can only show that "the main result does not depend on wording".
- At w=1 there is no saturation, and at equal weight the two versions receive the same attention (ratio 1.006). Here the third-person version is clearly easier to decode, yet claiming is only slightly lower, showing that wording has a very small effect.

**Colors and fonts**:

- A blue, B vermilion, Robin gray (Okabe–Ito palette, colorblind-friendly).
- "Claiming" uses B's color, indicating B's content appearing on A; consistent throughout.
- Arial, main text width 5.5 inches (single-column conference layout), fonts embedded in the PDF.

**Units**: the main metric is in nats (log-odds difference), because that is the preregistered metric. Nats are not intuitive, so we suggest adding a "choice rate" column in the main text or tables, for example what proportion of the time A states B's rule as its own under K\* (to be computed, see §5).

**Transparency**: appendix figure A4 lists the fate of every study across the three protocol versions, including negative results and studies that did not pass their thresholds. This answers concerns about "cherry-picking": every parameter was selected only by ACC and capability, and every confirmatory comparison was tested after the freeze, on new episodes.

## 4. Writing points

- **Terminology**: figures use "claiming" (short). The main text defines it as "self-specific adoption of the partner's content", and the framing calls it source misattribution. "appropriation" in the v1 documents is replaced throughout.
- **Write the two kinds of results separately**: preregistered conclusions are kept apart from descriptive results, and the descriptive ones (self-report, strength curve, B′) are labeled every time.
- **Explain clearly what happened to each pilot**: T3 was judged "not clean" and T3b "not matched", and it was they that prompted the corrections to the confirmatory design. These are reported faithfully in the appendix and mentioned in one sentence in the main text.
- **Examples of open self-report**: chosen by a fixed rule (for example, the first 3 by episode number), not hand-picked.
- **Limitations**:
  - one model, one type of task;
  - claiming saturates at the main strength;
  - after the cut, M still has a residue of +1.9;
  - two-way outcomes come from two separate questions;
  - the reading interface is an artificial design, not an existing system as-is.
- **AI use statement**:
  - code, experiments, analysis and figures were done by AI agents (Claude Code, Codex) under PI supervision, and all research decisions were made by the PI;
  - Fig. 1 and the task illustrations were generated by OpenAI image tools from the authors' prompts;
  - citations were verified one by one.

## 5. To do and to decide

| Item | Who | Status |
|---|---|---|
| 5 or 6 figures in the main text (whether Fig. 6 goes in the main text) | PI | Open; this plan recommends 6 |
| Which venue (ICML 2027 / COLM 2027 / NeurIPS 2027 / TMLR) | PI | Open |
| Add "choice rate": convert the key nat effects into the proportion of A stating B's rule | Claude | Can be computed any time (no GPU needed) |
| Select open self-report examples by a fixed rule | Claude | Can be done any time |
| A second model (an open model from another company), for the second arXiv version | PI chooses the model | Open |
| Writing the main text | Codex | Awaiting approval of this plan |
| arXiv submission | PI | After finalization |
