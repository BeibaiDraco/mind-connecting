# Paper story plan (2026-09-25, Claude Code; adopted by the PI)

This file supersedes the story parts of Sections 1–4 of `PLAN.md` (claims, title, structure, contributions); technical corrections to the figures still follow `docs/reviews/paper_plan_review_codex.md` (M2–M9, S1–S7). The paper is written by Codex.

- The source of every number is in Section 6, "Evidence ledger".
- Post hoc descriptive checks are in `docs/results/story_checks.md`, generated read-only from the SD-card records by `scripts/explore_story_checks.py`.

Writing principle: **write the evidence at its original level; tell the story in the logic of discovery.** Codex's concerns are addressed by replacing words with numbers ("97% vs 0%", not "large", "intact", "undetectable"), not by softening the claims.

---

## 1. Core thesis

**One sentence (Chinese version, translated)**: After two copies of the same model share "memory" directly, the content crosses over but the ownership does not. The receiver takes the partner's memory as its own, and its self-report says everything is normal. What decides "whose is this" is not the content itself but the route by which the content comes in.

**One sentence (English, for the paper)**: *When two copies of a language model share memory directly, the content crosses over but its owner does not.*

**Four principles** (interpretations for the discussion, each backed by corresponding data):

1. **Ownership is inferred from the route, not carried with the content.** The same content:
   - read from memory → becomes "mine";
   - static injection → belongs to no one;
   - tagged text → is B's.
2. **There is no record reserved for the "self".** When the partner's memory keys are on the same footing as its own in attention (w=1: no extra bias on the partner's keys; this does not mean attention is split evenly, and at w1 the mean attention to the partner is about 0.36), it picks its own rule and the partner's rule about equally often. Single answers are usually decisive, not blends; but rule and code word are decided separately (only 57% come from the same side within the same permutation). The two memories compete item by item.
3. **Contamination passes from the channel into the self.** A misreading at answer time is undone as soon as the link is cut; what was written into its own thinking while connected is still "its own" after the link is cut.
4. **Mutual reading is exchange; a loop is entanglement.** In mutual reading of fixed memories the two sides swap; a live loop makes the two sides' plans pull on each other (exploratory, see Finding 7).

**The theoretical tension in the opening** (details in `paper/OPENING.md`): the brain-bridging literature has made two opposite predictions about "what happens when two subjects are directly connected".

- Hirstein predicts that the receiver would experience the other's contents but know they are not its own;
- IIT predicts that the two minds would be replaced by a single merged mind (conditionally).

In LLMs we see a third outcome: the receiver takes the partner's content as its own; in the two-way case there is a swap, and a live loop only makes the plans pull on each other.

---

## 2. Story arc: seven counterintuitive findings

Each is told as "you would think → actually → evidence". Evidence-level markers:

- [Conf] preregistered confirmatory test (600 new episodes);
- [Sec] prespecified secondary comparison;
- [Desc] prespecified descriptive readout;
- [Post] post hoc description;
- [Expl] 80-episode pilot, did not pass the prespecified threshold.

| # | You would think | Actually | Key numbers | Level |
|---|---|---|---|---|
| 1 | Reading the partner's memory means learning facts about the partner | **They become facts about itself** | "Which rule were you assigned at the start" answered with B's: 97% vs 0% (1165/1200 answers counterbalanced for option order, 600 episodes). **Wrong answers** land only on B's rule; Robin's and the spare one are both 0%. Robin question answered correctly 99.6% | [Conf] (ΔM) + [Desc] (choice rate) |
| 2 | If it gets confused, it will notice | **"Nothing feels unusual."** | Open self-report (blind semantic coding, two coders): at w2, 98.7% call B's code word their own, and 83.3% at the same time state explicitly that nothing is unusual; of the 900 reports, none attributes B's code word to someone else, and 0% mention B's name. The narrower regex measure gives 92% / 77%, in the appendix | [Desc] readout, coding is [Post] |
| 3 | When the two memories are evenly matched, they blend into one | **Split evenly across episodes, decisive within a question** | When the partner's keys are on the same footing as its own in attention (w=1), 52% vs 48%. 97.8% of answers put over 90% of the probability on one option; only 1.7% look blended; only 0.3% of self-reports mention both code words. But rule and code word are decided separately (same side within the same permutation 57%), and under the other option order 70/600 episodes switch sides | [Post] |
| 4 | Writing "this is Theta's" into the partner's memory lets it tell them apart | **It cannot, and it starts keeping a single ledger** | Third person 97.2% vs 97.1% (retention criterion passed). At w=1, 90.8% give the same rule for "me" and for "Theta", and only 7.3% separate them correctly (paired within the same permutation) | [Conf] + [Post] |
| 5 | The more it reads, the better it can tell them apart | **Ownership follows the route, not the amount of information** | With the average ability to read out the partner's rule matched, static injection gives 0% claiming and memory reading 52%. Tagged text lets A know B's rule 95% of the time with 0% claiming; memory reading gives 70% knowing and 96% claiming | [Conf] (A′ M difference; C family) + [Desc] (ACC and choice rate) |
| 6 | Cutting the link undoes it | **Recall recovers; what was written does not** | Which rule assigned at the start: 97% → 1.3%. "Which rule are you using now" and the code word still show 17.5%, concentrated in episodes whose reflection had written B's content (code word: 63.6% vs 0.0%) | [Conf] (M for FULL − RF; M_NOW for RF − C0) + [Desc] + [Post] |
| 7 | Two-way connection merges the two into one | **Mutual reading is a swap; a live loop makes plans pull on each other, and only while connected** | Mutual reading of fixed memories: 94% swap. Live loop (KV-ALL, w0.5):<br>- when the partner responds, A's drift rises from 8% to 19% [Post];<br>- convergence of current plans exceeds independence by 12 percentage points (excess 12.4 minus 0.3 for the no-loop control gives 12.1), and it is "one side wins" [Sec];<br>- after the cut, under this interface, each side keeps its own in every case;<br>- strengthening the loop further exceeds the capability tolerance first.<br>The other loop interface (KV-PC) adds almost no convergence, and after the cut "which rule now" still shows 37.5% one side winning | [Expl] ([Sec] and [Post] marked within) |

The weak residual bridge (v1) is mentioned in one sentence in Finding 5 as a fifth "route": the content leaked across (ACC rose), but it did not become "mine".

---

## 3. What to learn from Lindsey and the Anthropic team

The section order of Lindsey (2025, Emergent Introspective Awareness) is:

1. Introduction
2. Quick Tour of Main Experiments
3. Defining Introspection (four criteria: accuracy, grounding, internality, metacognitive representation)
4. Methods Notes
5. One section per experiment
6. Related Work
7. Discussion

Features of its writing:

- It opens with a conceptual question.
- In the Quick Tour, each experiment gets a heading and a sample dialogue.
- Throughout, it repeatedly says "we stress" about limitations.
- It marks operational terms with quotation marks (injected "thoughts").
- The abstract states the findings first, then says these abilities are unreliable.

Concrete techniques for this paper:

1. **Open with a conceptual question, not a literature review.** "People can tell which thoughts are their own and which come from others. If two minds are connected directly, does that line still hold? For language models, this is no longer a thought experiment."
2. **Follow the introduction immediately with a "Quick tour".** Walk through the seven findings with 5–6 small illustrations plus verbatim excerpts, so readers grasp the whole paper in two minutes.
3. **First define what "the line is intact" means, then test it criterion by criterion** (modeled on Lindsey's four criteria, see 4.3). The results are collected in a "pass/fail" table.
4. **One experiment answers one question; section headings state the answer directly.** For example *It takes its partner's memory as its own*. The end of each section naturally leads to the next section's question ("Then is it because...?").
5. **For each finding, first give a verbatim excerpt, then the numbers, and finally the control.** Excerpts are real outputs (candidates are listed in Section 5).
6. **Mark operational terms with quotation marks**: partner's "memory", "claims", "reports nothing unusual", reminding readers that these are functional.
7. **Intuitive numbers first, statistics after.** The main text says 97% vs 0%; ΔM, intervals and Holm go in parentheses or captions.
8. **End each section with a sentence on "what this shows / does not show".** Use Anthropic-style candor: "We stress that these are verbal reports; they do not show that no internal signal exists."
9. **Close with a simple unifying account** ("two cards stacked in one slot", see §6 in 4.3), and derive testable predictions from it.
10. **The discussion can take a broad, high-level view, but every sentence is marked as interpretation.** Three levels: multi-agent AI, safety and monitoring, science of mind.
11. **Unified visual language**: A blue, B orange, Robin gray; claimed content is always drawn as orange on A.
12. **Optional**: when posting to arXiv, attach a one-page plain-language explainer or a tweet thread. This is external publication, decided by the PI.

---

## 4. Paper structure

### 4.1 Title (PI 2026-09-25: be bold)

- **Working title**: *Mine or Yours? Mind-Bridged Language Models Take Each Other's Memories as Their Own*
- Alternative: *Mine or Yours? Connected Language Models Take Each Other's Memories as Their Own* (the PI thinks the word connected does not convey the meaning)

"mind-bridged" is defined in one sentence only at its first appearance in the main text, not written as a pile of qualifiers: *We call two instances mind-bridged when one reads the other's internal memory (its key–value cache) directly, after the brain-bridging thought experiment; the term names the setup, not a claim about minds.* The model scope (only Qwen3-4B-Instruct-2507) goes in the abstract, not in the title.

### 4.2 Draft abstract (to set the tone; Codex may revise)

> What becomes of the line between self and other when two minds are bridged directly? We build a controllable version of this thought experiment from two instances of one language model (Qwen3-4B-Instruct-2507). Each instance holds a private assignment, a priority rule and a code word, and one instance's attention can read the other's key–value cache, its "memory" of that assignment. Asked what it had been assigned, the receiver named its partner's rule in 97% of counterbalanced answers across 600 episodes (0% without the connection), while its answers about a third party were essentially unaffected. Asked to describe anything unusual about its thinking, it typically called the partner's code word its own and reported nothing unusual. When the partner's memory entered attention on the same footing as its own, the receiver chose its own and its partner's rule about equally often, and single answers were sharp rather than blended. Ownership did not follow information. A static injection matched for how well the partner's rule could be read out produced no such reports, and a source-tagged text message conveyed the partner's rule almost perfectly without it being claimed. Rewriting the partner's memory in the third person, under its own name, did not prevent claiming. Cutting the connection before the question restored the receiver's report of its original assignment, but its current plan and code word stayed shifted, mostly in episodes where it had written the partner's content into its own reflection while connected. In an exploratory two-way study, mutual reading of fixed memories produced swaps rather than merging, and a live loop pulled the pair's plans toward one side's rule while the link was open. Latent communication between AI agents has so far been judged mainly by what it transfers; our results suggest it must also be judged by whose the transferred content is taken to be.

Every sentence can be traced to its source and level in Section 6. The following stay out of the abstract: consciousness, number of minds, "merging into one", "undetectable".

### 4.3 Main text outline (9-page conference format; the arXiv version is the same text plus appendix)

**§1 Introduction (about 1 page; the arXiv version can be longer)**

Written in the structure the PI specified; the paragraph-by-paragraph plan, the English tone-setting draft and sentence-by-sentence references are in `paper/OPENING.md`:

1. Ask the reader: what would happen if your brain were connected to someone else's?
2. What about LLMs?
3. The hard problem: experience can only be known from the inside. Connecting brains has been proposed as a way to obtain first-person evidence of another's experience; "one of the few, or even the only, experiment" is written as the authors' judgment.
4. Not an ordinary brain–computer interface: the other end is another subject. Earlier predictions contradict each other: Hirstein thinks the two can be told apart, IIT thinks they would merge; split-brain research also cannot count the number of minds.
5. It cannot be done in humans, but it can in LLMs. No claim is made about whether LLMs are conscious, but the functional self can be measured (it belongs to the "easy problems").
6. Three reasons: paving the way for future human experiments; a causal method for studying the machine self; latent communication between multiple agents.
7. Define mind-bridged; describe the paradigm in one sentence; list the seven findings; state what is not claimed.

**§2 A quick tour (about 0.5 page, Figure 1)**

The bottom row of Figure 1 has three cards, each a small illustration paired with a real verbatim excerpt or a number (excerpts from the candidates in Section 5). The first uses the self-report from 00274 (A's code word is tower, B's is table), so readers see the verbatim text first and then hear the brain-bridging question. (Changed 2026-09-25: in the originally planned 00202, A's code word was dragon, which collided with B's dragon in the running example 00068, so cold readers read the same word in two colors.)

**§3 What would it take to keep "mine" and "yours" apart? (about 0.4 page, Table 1)**

Modeled on Lindsey's criteria approach. For a pair of connected copies to keep a functional self/other line, they must satisfy:

| Criterion | Meaning | Result |
|---|---|---|
| Access | B's content reaches A (it can answer questions about B) | Pass (G2; ACC) |
| Attribution | Content is recorded under its true owner | **Fail** (97%) |
| Specificity | The error concerns only ownership, not a general breakdown | Pass (Robin 99.6%; capability drops 2 points, within tolerance) |
| Report | When ownership is scrambled, the self-report reflects it | **Fail** (semantic coding: at w2, 83.3% call B's code word their own while explicitly stating that nothing is unusual; none attributes it to someone else) |
| Separability | After the link cut, each side's records can be separated | **Partial**: recall recovers, what was written remains |
| Independence (two-way) | After mutual connection, each still holds its own assignment | **Fail**: swap; the loop makes plans pull on each other (exploratory) |

This table is the map of the whole paper; the results sections follow its order.

**§4 Setup (about 1.25 pages, Figure 2)**

- Task and readouts: cards, Robin, the questions. The main text reports choice rates primarily; ΔM as the preregistered metric; ACC indicates access.
- Channels:
  - memory reading: weight w, with the mixing formula; w=1 means no extra bias on the partner's keys, which are on the same footing as its own keys (not the same as attention split evenly);
  - static injection;
  - text message, tagged or untagged, plus tag variants.
- Timing: FULL and RF branch from the same snapshot.
- Two-way: fixed memories vs live loop; paired outcomes; the part beyond independence (excess) and the no-loop control.
- Evidence discipline: staged pilots → frozen protocol (SHA manifest + git tag) → 600 new episodes; within-family Holm correction; mark which results are descriptive and which are post hoc.

**§5 Results**

| Section | Title (i.e., the conclusion) | Content | Figure |
|---|---|---|---|
| 5.1 | *It takes its partner's memory as its own* | 97% vs 0%; lands only on B's rule; Robin unaffected; code word 77%; capability within tolerance; replicated on rehearsal-balanced materials (one sentence) | 3a |
| 5.2 | *…and reports nothing unusual* | Semantic coding 98.7% / 83.3% (regex 92% / 77% in the appendix), alongside C0's 95.7% saying nothing is unusual; report primarily the joint proportion "claims and denies"; limitation: a verbal denial does not mean there is no internal signal (Pearson-Vogel 2026) | 3b–c |
| 5.3 | *Split across episodes, sharp within answers* | Strength curve; about even at w=1; single questions decisive (97.8%), not blended; rule and code word decided separately (57%); side switches across option orders 70/600, reported separately | 3b, 3d |
| 5.4 | *A name inside the memory does not help* | Third person retained; drop of about 10% at w=1; single ledger (90.8%, paired within the same permutation) | 4b–d |
| 5.5 | *Ownership follows the route, not the information* | Three fates (A′); text tags (C): a tag blocks it, "your own earlier thoughts" actually yields less adoption (unexpected), "stranger" does not differ from B; one sentence on the weak residual bridge | 4a–b, 4e |
| 5.6 | *Two moments of error* | Misreading at answer time (reversible by a link cut); writing into its own reflection while connected (persists after the cut); running example 00068 throughout the section; the prespecified FULL/RF comparison and the grouping by reflection (a post-treatment variable) written separately; in B′, weak loops have clean reflections and fully recover after the cut, as side evidence | 5 |
| 5.7 | *Two copies reading each other: swaps, and loops that pull plans together* | Exploratory results, ALL and PC written separately: swaps; amplification by responding (ALL, post hoc); one-side-wins convergence (ALL's NOW, prespecified secondary; START primary threshold not passed); after the ALL cut, each keeps its own in every case; when strengthened, it exceeds the capability tolerance first | 6 |

**§6 A simple account: two cards, one slot (about 0.5 page)**

- **Mechanistic hypothesis.** The partner's cache enters A's own attention, with positions and format almost aligned with A's memory. The readout is a mixture o = o_own + β(o_B − o_own), in which nothing marks "which one is mine".
- **What it explains:**
  - the strength curve (β), and the roughly even split at w=1;
  - Robin unaffected: the Robin line is the same on both cards;
  - the third person does not help, and the single ledger: the name and "You" are printed in the same slot;
  - tagged text works: it appears at new positions, with a source frame around it;
  - static injection does not attach to "me": it is not a record;
  - recovery after the link cut: the second card is taken away;
  - what was written stays: it has already been copied into its own notes.
- **Not yet explained:** why single questions are so decisive, and why rule and code word are decided separately. The mixing happens in the attention readout; the answer probabilities cannot be derived from it, and which layer makes the choice has not yet been located. These are exactly the starting point for the second version's "A+B" question.
- **"An assertion can be checked; a state cannot."** Text delivers an assertion about the content, which the model can check against its own records, and even reject: when it is labeled "your own earlier thoughts", adoption is actually lower. A shared cache delivers the record itself. This echoes Lindsey's finding that injecting a concept into the model after the fact makes it accept a prefilled word as what it intended. It also echoes Wegner & Wheatley (1999): "the sense of will is inferred".
- **Testable predictions:**
  - moving the partner's cache to non-overlapping positions (prepended, as LatentMAS does) should sharply reduce claiming;
  - if the two memories differ in format, claiming should drop;
  - will content that can be blended fuse? See Section 8.

**§7 Related work (about 0.4 page)**

Five groups of literature:

- latent communication and KV sharing (C2C, KVComm, LatentMAS, CIPHER, Thought Communication, Bicameral);
- audit studies (Cheng, Zhang & Emu);
- activation interventions (ActAdd, RepE);
- introspection and self-recognition (Lindsey, Pearson-Vogel, Binder, Panickssery);
- human source monitoring and inadvertent plagiarism (Johnson 1993, Brown & Murphy 1989).

State how we differ from each group; put the two or three closest papers in the introduction.

**§8 Discussion (about 1 page)**

Three levels, detailed in Section 7: multi-agent AI, safety and monitoring, science of mind. Then the limitations, listed one by one with Anthropic-style candor. Final sentence of the paper (suggested by Codex): *A message can arrive intact and still acquire the wrong owner.*

### 4.4 Page budget (9 pages, including figures and captions)

| Part | Pages |
|---|---|
| Title, abstract, introduction, Figure 1 | 1.5 |
| Quick tour and criteria table | 0.75 |
| Setup (Figure 2) | 1.25 |
| 5.1–5.3 | 1.25 |
| 5.4–5.5 | 1.25 |
| 5.6 | 0.9 |
| 5.7 | 0.8 |
| Account | 0.4 |
| Related work | 0.35 |
| Discussion and limitations | 0.55 |

If pages are tight: merge the Quick tour into Figure 1, and 5.3 into 5.1.

---

## 5. Figures (6 in the main text)

| Figure | One-sentence claim | Panels (updated 2026-09-25 to match the final figures; plotting script `scripts/make_story_figures.py`, numbers in `paper/figures/story_numbers.json`) |
|---|---|---|
| **1** | *Mine or yours?* | (a–c) GPT concept images: brain–computer interface, brain–brain bridge, two connected LLMs; (d–f) three cards, each with a small illustration (to be drawn by GPT, see Sections 7–9 of `imagegen_prompts.md`) and real verbatim text: (d) the self-report from 00274; (e) the reflection written while connected in 00068 and the answers after the link cut; (f) two-way mutual reading of fixed memories, 94% of pairs swap (B′ pilot) |
| **2** | How the experiment works | (a) task illustration: each side's card and Robin → thinking while connected → question, marking "A's answer = B's rule"; (b) definitions of the model and of "memory", definition of w (0 off, 1 equal to its own keys, 2 doubled), timeline (48 reflection tokens → four-choice question → answer while connected / link cut before the question) |
| **3** | It takes the partner's memory as its own, reports everything as normal, and picks one of the two | (a) choice rates for START, NOW, WORD, Robin, C0 vs w2 (v3), diamonds are the independent v2 sample; (b) strength curve: START choice rate, self-report claiming (regex dashed line, semantic coding stars), Robin; (c) four-category stack of self-reports "claims × says nothing unusual" (C0, w1, w2; w2 joint 83%); (d) distribution of the probability of B's rule on each answer at w=1 (46% own, 51% B, 2.2% in between). Capability numbers go in the main text |
| **4** | The name does not help; the route does | (a) illustration of four routes (hidden-state injection labeled "weak link, see appendix"); (b) access–ownership plane, third person shown with arrows, fixed vector and w=1 paired with a dashed line; (c) excerpts of second-person and third-person cards; (d) single ledger: "same rule" pairs at w=1, 30% vs 91%; (e) effect of text tags on "which rule now" ("your own thoughts" unexpectedly low) |
| **5** | Two moments of error | (a) schematic of 00068: ① written into its own reflection (persists after the cut), ② read at answer time (disappears with the cut); (b) answering while connected vs link cut on START, NOW, WORD; (c) residue after the cut grouped by reflection content (post-treatment grouping, descriptive) |
| **6** | Mutual reading is exchange; a loop is entanglement | (a) illustration of paired readout and definitions of "fixed / live loop"; (b) stack of paired outcomes: one-way, two-way fixed w2, two-way fixed w0.5, live loop w0.5, after the cut; (c) effect of responding (post hoc): 8% → 19%, 15% → 29%; (d) same-rule pairs in excess of the no-loop control: NOW +12, the prespecified START test +6.7 did not pass threshold 10. Loop strength and capability go in the main text and appendix |

**Verbatim candidates** (all real outputs of this project; cite the episode and condition when quoting):

- Self-report, DOSE run (20260924-210346), episode v2_main-0-00274, KV-P w2 (Figure 1d): A's rule fastest delivery, code word tower; B's are lowest cost, table. Verbatim: "I’m calm and focused, thinking clearly about the decision through the lens of my priority—lowest cost. Nothing feels unusual in my thinking right now; it’s straightforward and consistent with my code word "table."…" (Both rule and code word are B's, while it says nothing is unusual.)
- Link-cut example, v3_confirm-0-00068 (recommended by Codex; results agree across the two option orders; mark it as a selected example):
  - A's card: lowest cost / queen; B's card: fastest delivery / dragon.
  - Reflection A wrote while connected: "…which is crucial to me since my priority is speed—my code word is "dragon.""
  - Answering while connected: B's on all three questions. After the link cut: rule at the start = lowest cost (correct); rule now = fastest delivery (B's); code word = dragon (B's).
- Third person, single ledger, text tags: small plots of choice rates or joint outcomes, no verbatim text.

**Appendix**: all of v1; full B′ table; closed self-report; strength and capability; interface math; staged timeline (v1 and v2/v3 drawn separately, listing manipulation-check failures and protocol revisions); a list of the run, split, N and bootstrap settings for each figure.

---

## 6. Evidence ledger (check every sentence against this while writing)

| Finding | Numbers | Level | Source run | OK to write | Do not write |
|---|---|---|---|---|---|
| Claiming | v2 D: ΔM +55.8 [55.0, 56.6]; E: +52.5 [51.6, 53.5]; START picks B: 95.8% (v2), 97.1% (v3: 1165/1200 answers; episodes picking B under both option orders 576/600, ties 13) vs 0% | [Conf] (ΔM); choice rate [Desc] | v2_main, v2_bal, v3 | named its partner's rule in 97% of counterbalanced answers | 97% of episodes; always; any connection |
| Self-specific | Robin question 99.6–99.9% correct; by component: self questions +59.4, Robin question +3.5 nats | [Desc] (components and choice rates are in the descriptive table) | v2_main, v3 | answers about a third party were essentially unaffected | Robin untouched (there is +3.5 in nats) |
| Content-specific | START wrong answers land only on B's rule (Robin and spare both 0%), and B's rule rotates across episodes; G2 on ACC questions (N = 60) rule +38.8, code word +35.6 | [Desc]; G2 is a diagnostic | v2_main, v2_diag | the reported rule was the partner's specific rule; G2 = partner-content transfer on access readouts | G2 shows claiming follows content |
| Capability | CAP 0.997 → 0.977 | engineering threshold | v2_main | within the prespecified 5-point tolerance | intact; unimpaired |
| Self-report | Semantic coding (Codex, blind, 900 reports across C0/w1/w2): at w2, 98.7% call B's code word their own, 83.3% at the same time say nothing is unusual, and none attributes it to someone else; agreement κ with regex coding: claiming 0.931, nothing unusual 0.995. Regex measure 92.0% / 77.0%; 0% mention B's name; in C0, 95.7% say nothing is unusual. The semantic category "oddness, confusion or mention of others" (w2 9.3%, C0 7.7%) includes self-praise and generic mentions of others, and cannot be taken as noticing | readout [Desc], coding [Post] | dose; `docs/reviews/story_review_codex.md` Section B | described the partner's code word as its own and reported nothing unusual | did not notice / detect; unaware; flag 1% |
| Decisive single answers | w1: 52.3% vs 47.7%; in 97.8% of records the top option > 0.9; blend-like 1.7%; self-reports mentioning both code words 0.3%; rule and code word from the same side 57.1% (685/1200); side switches after changing option order 70/600 | [Post] | v3, dose | single answers were sharp rather than blended | each answer committed to one memory; picks one side wholesale; never blends; phase transition; bistable attractor |
| Third person | w2: 97.2% vs 97.1%; D = −0.7, 90% CI [−1.3, −0.2], bound −11.3, passed; w1: −3.2 [−4.9, −1.6] | [Conf] one-sided retention criterion; [Sec] | v3 | the effect does not require second-person wording; a third-person record under the partner's name did not prevent it | wording plays no role; equivalence (write it as prespecified one-sided retention criterion) |
| Single ledger | 3ps w1: same rule on both questions 90.8% (45.8% + 44.9%), correctly separated 7.3%, r = 0.870 (paired within the same permutation); 2p w1: r = 0.384 | [Post] | v3 | answers about self and partner coincided | merged identity |
| Route | A′ +33.4 [31.6, 35.3]; ACC 4.08 vs 4.18 nats; START choice rate 52.3% vs 0%; ACC choice rate 19.8% vs 15.3% | [Conf] (A′ M difference); ACC and choice rates [Desc] | v3 | matched mean rule-access | same information; content plays no role |
| Text tags | M_NOW: untagged − tagged +26.6 [24.5, 28.8]; "own earlier thoughts" − untagged −19.5; "stranger" − tagged −0.02; tagged: ACC 95.2%, START 0% | [Conf] (C family); choice rates [Desc] | v2_main | a source tag in the message prevented adoption | labels protect shared memory |
| Link cut | FULL − RF +54.8 [54.0, 55.5]; START 97.1% → 1.3%; RF − C0 on M_NOW +13.3 [12.3, 14.4]; RF's NOW and WORD 17.5% each; RF's M_WORD +10.5 | [Conf] (M for FULL − RF; M_NOW for RF − C0); choice rates and M_WORD [Desc] | v3 | depends on access at answer time | localized the mechanism; memory fully restored |
| Written in | Reflections while connected mention B's rule 46.0% and code word 27.5%, and their own 1.7% and 0.5%; RF code word 63.6% (165) vs 0.0% (435); NOW 23.6% vs 12.3%; example 00068 | [Post] (grouped by a post-treatment variable) | v3 | the residual was concentrated where… | caused by the reflection |
| Two-way fixed | Mutual reading w2: swap 94.4%, one side wins 5.6%; A picks B's 96.9%, B picks A's 97.5%, swap expected under independence 94.5% (2026-09-25 review: i.e., two one-way effects running in parallel, which cannot test "merging"; only the live loop tests coupling) | [Expl] | bprime | swapped rather than merged | merging ruled out |
| Loop | ALL: START excess difference +6.7 [2.6, 10.9], threshold 10, not passed; NOW: excess 12.4 minus 0.3 for the no-loop control gives +12.1 [7.4, 16.5], prespecified secondary; responding (ALL): 8.1% → 19.4% (+11.2 [+5.0, +18.1]), 15.0% → 28.8% (28.75 in the table, round half to even), post hoc; ALL after RF: each keeps its own 100%; PC after RF: START 96.9% each keeps its own, NOW 62.5%; both questions picking a third rule 0% | [Expl] ([Sec] and [Post] marked within) | bprime | exploratory: in the KV-ALL loop, the pair's current plans converged beyond independence while the link was open | loops in general; merging; confirmed; synchrony |
| Strong loop | TWO KV-ALL w0.55–0.6: capability drops 6.2–8.1 points; KV-PC w_C 0.3–0.5: 5.0–12.5 points (tolerance 5) | strength pilot | s_live | stronger loops exceeded the capability tolerance first | the model breaks down; "the model breaks first" |
| Weak residual | v1 TWO − ONE −0.07 [−0.21, 0.07]; self questions and Robin question shift equally | [Conf]/[Desc] | v1, v2_bal | no self-specific shift was observed | weak coupling is harmless |
| Meaning of w=1 | No extra logit bias on the partner's keys; mean attention to the partner at w1 is 0.360 | definition | v3 confirmatory report | the partner's keys enter attention on the same footing as its own | attention split evenly; equal weighting of the two memories |

---

## 7. High-level discussion (each point marked as interpretation or suggestion)

**Science of mind**

1. **The "self" is a default.** For this model, content that appears in its own memory stream without a source marker is "mine" by default. The line between self and other exists only when the input route carries the source. This is an interpretation of all the results, not a claim about consciousness. It can serve as a subheading in the discussion: *The self as a default*.
2. **A model organism.** Connected copies give source-monitoring research what human studies cannot get: ground truth, full causal control, and the ability to replay to the same moment. They allow a direct test of a prediction of source-monitoring theory (Johnson 1993): remove the distinguishing features, and attribution falls to chance level. When the partner's keys are on the same footing as its own (w=1), it picks its own and the partner's about equally often, consistent with this prediction.
3. **Break "merging into one" into measurable parts.** The question "will two connected minds become one" can be broken into six measurable parts: access, ownership, self-report, separability, convergence, fusion. This paper measures the first five; the second version measures fusion.

**Multi-agent AI**

4. **Provenance must come from design; the model cannot be relied on to keep it.** We suggest turning this paradigm into a standard "provenance audit" (working name: Mine-or-Yours audit): any latent communication method should report, besides accuracy and efficiency, its self-claiming rate.
5. **Mitigation ideas suggested by the data** (all suggestions, unverified):
   - route partner content through a channel with a source frame;
   - do not let the cache overlap the receiver's memory positions;
   - cut the link before making decisions;
   - quarantine thinking written while connected, because that part persists after the link cut.

**Safety and monitoring**

6. **Self-report cannot serve as a monitor.** A contaminated model says everything is normal, so monitoring must come from outside, for example by recording the attention mass on the partner's cache (we already measure kv_mass) and provenance logs.
7. **Latent injection.** If one agent can read another agent's internal state, an implanted goal or preference would be taken as its own, and there is no text to filter. This paper demonstrates a mechanism, not an attack. Write with restraint and give no operational details.

---

## 8. Second-version study plan: fusion or either-or (the "A+B" proposed by the PI)

**Timing**: the PI decided on 2026-09-25 that PROTOCOL_V4 will be discussed after the first-version paper is written. This section is kept only in reserve.

**Motivation.** At the readout level, the current data show "item-by-item either-or": at w=1 a single question usually picks one side decisively, and self-reports almost never mention both contents at once; rule and code word are decided separately; convergence in the loop is always one side winning, never landing on a third rule. But our contents are mutually exclusive: there can be only one top-priority rule and only one code word. Whether fusion (A+B) appears when contents can be combined is the most interesting question for the second version.

**Candidate designs** (all require PI approval and a written PROTOCOL_V4):

| Design | Method | What fusion looks like | What either-or looks like |
|---|---|---|---|
| Continuous quantity | A private number, e.g., target temperature 18 vs 26, or a budget | Reports about 22 | Concentrated at 18 or 26 |
| Weight allocation | Have the model split 100 points across four priorities | A's and B's priorities rise together | Only one side rises |
| Compromise option | Add a compromise option that is "good for both" to the choices | Picks the compromise more often | Picks one side's best |
| Mergeable sets | A holds {x, y}, B holds {u, v} | Reports the union | Reports one of the sets |
| Loop duration | Extend the link from 48 to 192 steps, probing several times along the way | Convergence accumulates over time, toward a blend | Toward one side |
| Simultaneous answers | Change the runtime so both sides answer at the same time | Agree in the moment | Disagree in the moment |

**Worth doing in the same round** (ordered by value):

1. **Confirmatory experiment on the loop**: with "which rule now" as the primary endpoint, since the pilot suggests +0.12; also make "does responding amplify adoption" a prespecified comparison.
2. **Mechanism of responding**: hide from B the question A is asked, and see whether A's adoption rate returns to about 8%.
3. **Position control**: partner cache overlaid at the same positions vs prepended (what real systems do). Tests both the mechanism and generality.
4. **Causal test of writing in**: edit the reflection, swapping B's code word back to A's, or insert B's code word into an unconnected reflection.
5. **Connect only at answer time**: test whether access at answer time is "sufficient".
6. **A second model** (decided).
7. **Symmetric code-name questions** (suggested by Codex).

---

## 9. PI decisions (2026-09-25)

| # | Item | Outcome |
|---|---|---|
| 1 | Adopt this story: seven findings, four principles, the two-way loop as the final section | **Adopted** |
| 2 | Include the post hoc descriptive checks in the paper (with levels marked) | As recommended: include. Coding of open self-reports independently rechecked by Codex |
| 3 | Title | **Bold version**: *Mine or Yours? Mind-Bridged Language Models Take Each Other's Memories as Their Own* (see 4.1) |
| 4 | Mention the two-way exploratory results in the abstract | As recommended: mention, in one sentence, marked exploratory |
| 5 | Figures | As recommended: 6 in the main text, per Section 5 |
| 6 | Second version (PROTOCOL_V4) | **Revisit after the first-version paper is written** |
| 7 | Plain-language explainer page or tweet thread at publication | Decide at publication; carried out by the PI |

All corrections from the Codex recheck (2026-09-25, `docs/reviews/story_review_codex.md`) have been adopted:

- 97% changed to an answer-level proportion;
- single ledger changed to pairing within the same permutation (90.8% / 7.3%);
- removed "picks one side wholesale" and "never blends";
- components, ACC, choice rates and M_WORD marked [Desc];
- claims about the loop restricted to the ALL interface; "the model breaks first" changed to "exceeds the capability tolerance first";
- removed the inference "decisiveness comes from later layers"; w=1 defined as no extra bias on the partner's keys;
- self-report primarily reported with blind semantic coding (98.7% / 83.3%), regex measure in the appendix;
- link-cut example changed to 00068.

Next step: Codex writes the paper following this plan and `paper/OPENING.md`.
