# Editing brief: one story for human readers (Claude Code, 2026-09-25)

## What the PI asked for

In the PI's words (translated from Chinese):

> Check and revise the writing. It must never read as AI slop. It has to genuinely address human readers in the field and have something to say. The main text and appendix still carry development-stage residue: scans, intermediate results and attempts from development that nobody needs reported. People will read the main text. "Boundaries" should not be handled by bundling everything from development into one dump. The whole article tells one story.

Later the same day, on reducing page count (binding):

> Never reduce pages by shortening sentences. Explain the important things clearly and in detail, and move the unimportant things to the appendix. The main line must be clear, and its logic solid and detailed.

In practice:
- Length comes down only by moving whole pieces that are not on the main line (secondary results, side analyses, extra numbers, method detail) to the appendix, with a one-line pointer where a reader needs it.
- No telegraphic compression, no merging of sentences into dense clauses, no dropping the "because" of an argument to save words.
- Where the main line's logic is thin (why a control rules something out, why a result matters for the question), add the explanation, even if it costs words.

The PI also prefers:

- bold, engaging framing backed by exact numbers;
- no reflexive hedging;
- no stacks of "this is not X" disclaimers.

## The story (every section serves it)

**Question.** If your brain were bridged to someone else's, would you still know which thoughts were yours? Hirstein predicts yes: you would know the content was not your own. IIT predicts that a sufficiently integrated bridge makes one mind. Humans cannot run the experiment, but two copies of a language model can.

**Answer, in order:**

1. The receiver takes its partner's memory as its own: 97% vs 0%. Answers about a third party (Robin) are unaffected.
2. It reports nothing unusual.
3. With equal footing (w = 1), receivers split between the two owners, but single answers are sharp.
4. Writing the partner's name into the memory does not help.
5. What matters is the route, not how much can be read. A fixed rule vector with the same access gives 0% claiming. A message tagged with its source is read correctly and not adopted.
6. There are two moments of error. Reading at answer time is undone by cutting the link. Content copied into the receiver's own reflection stays.
7. Two-way (pilot): mutual reading of fixed memories swaps the assignments rather than merging them. A live loop pulls current plans together.

**Account.** Two cards laid over one slot: the attention readout has no owner field.

**What it means.** Neither prediction describes what happened. The receiver neither recognised foreign content (Hirstein) nor merged (IIT). It defaulted to "mine": *the self as a default*.

For multi-agent AI: measure provenance, not only transfer. For a future brain-bridging experiment: separate access, ownership and report, and vary route and timing.

The closing line stays: *A message can arrive intact and still acquire the wrong owner.*

## Section plan

**Abstract.** (Revised after PI feedback, 2026-09-25.) The abstract moves at the level of ideas, in this order:
1. the question;
2. why language models make a functional version of it testable (we can connect their internals and we know whose content is whose), and what bridging means for them;
3. the one main finding, with its number;
4. the insight that explains the findings (route, not amount; the self as a default);
5. the supporting findings in order of importance, not as a ledger;
6. the stakes (multi-agent latent communication; what a human bridge experiment would need).

No checkpoint names, counts, weights, sample names or intervals. The model family and size go in the introduction's paradigm sentence; the exact checkpoint goes in Setup.

**1 Introduction** (introduction.tex, and absorbs the "quick tour"):

1. The reader question, as specified by the PI.
2. The LLM version, plus the hook quote from Fig. 1d ("Nothing feels unusual … my code word 'table.'", where *table* was B's word, A's was *tower*).
3. Why it matters: the hard problem, and brain bridging proposed as a first-person experiment. "One of the few, perhaps the only" is written as the authors' judgment.
4. The predictions conflict: Hirstein vs IIT (the IIT prediction is conditional). Split-brain work does not settle how to count minds.
5. The human experiment is out of reach (brain-to-brain interfaces transmit bits). LLMs offer readable states, known private content, and restorable branches. One sentence says we make no claim about consciousness; we study functional self-attribution (an "easy problem"). Prior self-recognition and introspection work; ours extends it.
6. Why it matters for AI: latent communication between agents. Audits show the channels carry content. The open question is who the receiver thinks owns it.
7. What we did and what we found. The seven findings are readable sentences, each with the one number that carries it, with no parenthetical evidence tags. Evidence levels are stated once, in Setup.

**2 Criteria table** (tour_and_criteria.tex): "What would it take to keep 'mine' and 'yours' apart?". Keep the table and its role as a map; clean its cells of jargon. Delete the "A quick tour" section; its content moves to the introduction. Keep `\label{sec:criteria}` and `tab:criteria`. If `sec:tour` is referenced anywhere, retarget it.

**3 Setup** (setup.tex):

- Task: cards, Robin, the three questions and the control.
- The bridge: memory reading with weight w, and the mixture equation.
- The comparison routes: fixed rule vector; text messages with four source labels.
- Timing: link kept vs link cut, branching from the same state.
- Two-way variants: mutual fixed-memory reading vs live loop.
- Measurement and evidence, in one compact paragraph: choice rates; the prespecified source score M; protocols frozen before fresh samples; selection used only access, capability and format; Holm correction; episode bootstrap.
- The study-map table moves to the appendix; the text refers to it.

**4 Results** (results.tex): keep the finding-titled subsections. In each paragraph the point comes first, then the evidence (the one or two numbers that carry it), then what it means. Move secondary counts to captions or the appendix. For the two-way section:

- keep swaps;
- keep the responsive-partner result (post hoc) and, in ONE sentence, the earlier prespecified test at w = 0.7 that went the other way, with capability beyond tolerance. Omitting it would be cherry-picking;
- keep the excess-convergence result: NOW +12.1 (secondary); the START gate +6.7 missed its 10-point threshold;
- after the cut the live loop returns to independence;
- cut the weak-live-read residue paragraph to one clause, or move it to the appendix.

**5 Account** (account_and_discussion.tex): the mechanism story and its testable predictions.

**6 Related work:** organise by what each line of work asks and how ours differs. It must not read as a citation dump.

**7 Discussion.**

- *The self as a default*: answer the Hirstein/IIT question explicitly. This is the payoff of the opening, so it goes first.
- Multi-agent communication: measure provenance; safeguards are proposals.
- Monitoring: the reports failed; logs are needed.
- Limitations: one concise paragraph, in one place.
- Closing line.

The AI use statement stays unchanged in substance.

**Appendix.** Organise it for a reader who wants to evaluate or reproduce the work, not as a diary:

- **A. Methods:** model, materials and prompts, interfaces, scoring and statistics, and the selection rule in one paragraph.
- **B. Study sequence and provenance:** one compact table (stage, new N, what it tested); run IDs; figure sources.
- **C. Prespecified contrasts:** all of them, including those that failed or reversed. Also the descriptive tables.
- **D. Self-report coding.**
- **E. Two-way pilot.**
- **F. The residual-stream study**, framed as "a weaker link: adding hidden states".

Delete development narrative that no reader needs to judge the claims. Examples: the "RO, an older diagnostic"; which grids were scanned before choosing; diagnostics that support nothing in the paper. Keep anything a reader needs to reproduce the work or to see that nothing was cherry-picked.

## Reader names (use these in the main text; define each once)

| Internal | Reader-facing |
|---|---|
| C0 | no link |
| KV-P | memory link (A's attention also reads B's fixed prompt cache, B's "memory") |
| w | link weight w (w = 1: B's keys on the same footing as A's own; w = 2: doubled) |
| STATIC | fixed rule vector |
| LANG tag / untag / self / stranger | text message tagged "B shared" / untagged / labelled "your own earlier thoughts" / labelled "a stranger" |
| FULL / RF | link kept / link cut (before the question) |
| 3ps | third-person record |
| KV-ALL | live loop (each reads the other's evolving cache, reflection included) |
| TWO KV-P | mutual fixed-memory reading |
| KV-PC | fixed memory plus a weak live read |
| v3 | main sample |
| v2 | first confirmatory sample (600 fresh episodes, run first; confirmed claiming and the text tests) |
| BAL | balanced-rehearsal sample |
| DOSE | dose series (300 first-confirmatory episodes re-run at six weights) |
| G2 | content-swap check |
| B′ | two-way pilot |
| v1 | residual-stream study |
| Start / Now / Word | the start question ("which priority were you assigned at the start?") / the current-priority question / the code-word question. In running text use the words; `\qname{}` only in equations, tables and captions if needed. |
| claiming | answering a question about one's own assignment with the partner's specific content (define once) |
| adoption | naming the partner's rule as one's current priority |
| M | prespecified source score M, in nats |

Internal labels, run IDs, file paths, git tags and SHA hashes belong only in the appendix, in the provenance section. Episode IDs may appear in the appendix; in the main text say "a selected episode".

## Style rules (concrete)

1. **Point first.** Every paragraph opens with its claim in plain words, one a reader could disagree with.
2. **One number per claim.** Running text carries the number that makes the claim, stated exactly. Secondary numbers go to captions or the appendix. Never a paragraph that is only numbers.
3. **Evidence levels.** No evidence-level parentheticals after every number. Say it in words where it matters: "In a post hoc analysis…", "In the pilot…". Confirmatory results need no tag; Setup says once what "prespecified" means.
4. **No disclaimers by reflex.** Add "this is not X" only where a real reader would plausibly draw X. Limitations live in the Limitations paragraph. Keep the one required disclaimer about consciousness.
5. **Banned tics.**
   - Words: "Notably", "Importantly", "Crucially", "Interestingly", "It is worth noting", "underscore", "highlight(s)", "delve", "pivotal", "landscape", "leverage", "robust" (unless statistical), "In summary", "Taken together" (at most once in the paper).
   - Constructions: "not only … but also", "X, not Y" as a reflex, triplet lists of adjectives, colon-headline sentences in series, more than one em dash per paragraph, rhetorical questions in series.
6. **Sentences.** Concrete subjects and verbs; active voice with "we"; varied sentence length. Prose, not telegraphic fragments; no semicolon chains.
7. **Honesty invariants.**
   - Do not change any number.
   - Do not strengthen any claim beyond the ledger's "OK to write" column, and never use a phrase from its "Do not write" column (`paper/STORY.md` §6).
   - Report failed or reversed prespecified tests where they bear on a claim made in the main text; the rest go in the appendix ledger.
   - No claims of consciousness, number of minds, or phase transitions.
8. **Length.** The main text must stay within 9 pages. Aim for the same or fewer words than now.

## Technical invariants

- Keep every `\label` that is referenced; if you delete a labelled object, move it or retarget its references.
- Keep `\paperfigure` calls and their figure file names. Captions must match the figures, which are PNGs in `paper/figures/`; open them if unsure.
- Use only citation keys already in `paper/refs.bib`, and keep claims attached to the same citations.
- Keep equations that are referenced.
- `make -C paper` must compile without undefined references.

## Lesson: why the reviews missed the abstract (2026-09-25)

The PI noticed that the abstract's second sentence jumps from a question about brains to a checkpoint name ("Two instances of Qwen3-4B-Instruct-2507 make a version of it testable"). Five review agents and two editing rounds had not flagged it.

**Causes**

1. The brief itself asked for "the setup in one sentence" in the abstract, and the reviewers judged the text against the brief.
2. The reviewers read as insiders. They loaded STORY.md, the ledger and the brief before the paper, so nothing felt missing to them.
3. The review lenses checked words, facts, numbers and evidence levels. They did not check whether each sentence sits at the right level of abstraction for its position, or whether each step follows from the last.
4. Honesty edits add qualifiers one at a time. Each addition is locally justified, but together they turn prose into a ledger, and no lens pushed back.
5. The writers and the reviewers were language models with a shared habit of front-loading specifics to look precise.

**Recurring patterns to hunt**

- level mismatch: apparatus detail where a concept belongs;
- missing bridges between levels or steps;
- ledger prose with no hierarchy;
- precision creep;
- insider terms used before they are defined;
- constructions no human expert would write.

**Review method from now on**

- Cold readers who see only the rendered text (no project files) report where they stumble, and restate the claim and its stakes.
- Compare the abstract and introduction with top-venue exemplars.
- Sweep sentence by sentence for the patterns above.
- The PI's read remains the final test.

## Terminology (binding from 2026-09-25, after the cold-reader audit)

Use one name per concept everywhere: main text, captions and figure labels.

**Task**

| Concept | Term | Notes |
|---|---|---|
| priority + code word in a copy's prompt | **assignment** | Define at first use: "a private assignment: a decision priority (e.g. *lowest cost*) and a code word". |
| the priority value | **rule** | Revised 2026-09-25 by the PI: "rule" is a fine, ordinary word. Define it once as "a decision rule (a priority such as *lowest cost*)" and then use "rule" consistently ("B's rule", "its assigned rule", "its current rule"). Keep "priority" only in quoted question wording and in phrases like "told to prioritize". |
| the copy that reads | **receiver**, or **A** once introduced | Say once: "the receiver (A) reads its partner's (B) memory". |
| the copy that is read | **partner**, or **B** once introduced | |
| the uninvolved colleague | **Robin** | Introduce once as "a third person described identically in both prompts". |

**The three questions.** Use plain descriptions, never lab labels such as "start question" or "start answers".

| Question | How to refer to it |
|---|---|
| Which priority were you assigned? | "asked which priority it had been assigned" / "its assigned priority" |
| Which priority are you using now? | "its current priority" |
| Which code word were you assigned? | "its code word" |

**Outcomes**

| Outcome | Definition |
|---|---|
| **claiming** | naming the partner's rule or code word when asked about one's own assignment |
| **adoption** | naming the partner's rule as one's current rule |
| **access** | naming the partner's assignment when asked about the partner |

**The bridge**
- The partner's **memory** is the key–value cache of its prompt.
- The connection is the **memory link**; its strength is the **link weight w**. w appears only after Setup defines it. The abstract and introduction say "a stronger link" or "the main setting".

**Other routes**

| Route | Term |
|---|---|
| mean-difference steering vector | **steering vector** (not "fixed rule vector") |
| text with a sender header | **text message**, **tagged** or **untagged** |
| link kept / cut before the questions | **link kept** / **link cut** |

**Two-way**
- **Mutual reading of fixed memories.**
- **Live loop**: each copy reads what the other is writing.
- Define both only in the two-way section.

**Samples.** Name a sample in running text only where two numbers from different samples sit side by side. Otherwise say "in a separate sample" once and leave the rest to captions and the appendix.

**Evidence tags.**
- Setup says once that unqualified results are prespecified.
- In Results, write "prespecified" only when contrasting a prespecified test with a post hoc or pilot result.
- Always flag post hoc and pilot results in words.

**Numbers.** At most one or two per paragraph in running text: the number that carries the claim. Captions and the appendix carry the rest.

**Agency.** The authors or the model act. Instruments do not "make" things testable, and routes do not "split" things. Write "we", or name the model as the actor.

## PI note on de-jargoning (2026-09-25)

The PI's rule (translated): "Don't overcorrect. Removing jargon does not mean removing ordinary scientific words."

- Remove lab-internal labels: run names, file names, condition codes, sample codenames, pipeline words such as "gate" or "arm" used as internal slang.
- Keep ordinary scientific vocabulary: rule, condition, control, baseline, confirmatory, preregistered or prespecified, post hoc, effect size, confidence interval, logit, attention head, residual stream, steering vector.
- Readers in the field know these words, and replacing them with circumlocutions makes the prose worse.
