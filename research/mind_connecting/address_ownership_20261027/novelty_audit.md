# Novelty audit: is "ownership follows placement" new?

October 27, 2026, Claude Code. Four literature strands were run as independent subagent searches that read primary sources (arXiv HTML methods and results unless marked). Claude re-read the passages marked **[verified]** directly. Unmarked numbers come from the subagent's reading of the source and were not re-checked. This file covers strands B (binding and parallel contexts) and C (LLM self-attribution). Strands A (KV communication systems) and D (human, philosophy, brain bridges) are in the sections below them.

> **Corrections (October 27, 2026), after Codex's review; see [response_to_codex_review.md](response_to_codex_review.md).**
> - LACO's remedy is training-free.
> - Feng & Steinhardt motivate a null hypothesis for relocation; they do not predict our outcome.
> - Absolute "no one has" statements should read "the inspected sources do not report this comparison".
> - "Every source-monitoring feature equalized exactly" is withdrawn.

## Bottom line

1. **As a general thesis, "mine is an address, not a label" is not new.** For text, Li et al. (2026) state outright that the self-index "is attached to the Assistant slot" and that "a stateless model cannot distinguish its own earlier tokens from identical tokens placed in that slot by someone else" **[verified]**. Ye, Cui & Hadfield-Menell (ICML 2026) find that position and style, more than tags, write the latent role. The prefill literature shows that models mostly own whatever sits in their assistant slot.
2. **The ~50% collision at equal weight is forced by the design and predicted by binding work.** With identical templates, identical positions, identical scoring and counterbalanced rules, the two cards are exchangeable from the readout's view (see the symmetry concession in [internal_evidence.md](internal_evidence.md)). Feng & Steinhardt (ICLR 2024): "When v1 is close to v0, the LM gets close to 50% accuracy, which indicates confusion" **[verified]**. The source monitoring framework predicts the same for memories with matched features (strand D).
3. **The same binding work predicts that the proposed RoPE relocation will do little.** Feng & Steinhardt changed RoPE rotations to move activations and found "position interventions result in little change in model behavior" **[verified]**. Dai et al. (EMNLP 2024) find that the ordering-ID subspace is nearly uncorrelated with absolute position. The binding "address" is carried in the activations, not in the rotary coordinate.
4. **No precedent was found for a training-free change of position or rotation that restores source separation.** ASIDE, Instructional Segment Embedding and position-gap fine-tuning (PFT) all fine-tune. TurboRAG and KVCOMM re-rotate cached keys without training, but only for accuracy. The relocation test is new, and the literature does not agree on its outcome.
5. **What our existing data add beyond the precedents:**
   - It is ownership of a self-referring *memory* ("whose assignment is this?"), not authorship of text.
   - The two histories were formed independently by two instances and are superposed, not juxtaposed or overwritten.
   - The route dissociation holds at matched access (52.3% vs 0%).
   - Claims are winner-take-all, with almost no report of conflict.
   - A "your own earlier thoughts" label lowers adoption, which runs against label-following.
   - Line-order counterbalancing rules out ordinal-index dereferencing and points to **role** collision ([internal_evidence.md](internal_evidence.md)).

## Claim-by-claim

| Claim | Status | Closest precedent |
|---|---|---|
| Self-attribution follows slot or structure, not true authorship | **Established for text** | Li et al. 2026; Ye et al. 2026; Nguyen et al. 2026; Wang et al. 2026 (prefill awareness) |
| Records with identical binding structure are confused about 50/50 | **Predicted** by binding-ID collision | Feng & Steinhardt 2024 §4.2 |
| Retrieval in short two-group lists is positional (ordinal) | **Established** in general | Gur-Arieh et al. 2026; Enouen & Galhotra 2026 (Qwen3-4B listed, numbers unverified) |
| Same-model KV swap flips a self-attribution verdict | **Established** for authorship of an output | G & Lindsey 2026 (Llama-3.1-70B, user-token KV overwrite) **[verified]** |
| A shared KV cache leaks goals across clients | **Established**, juxtaposed records | Gupta, Krier & Matlin 2026 (Goals Leak) |
| A receiver claims another instance's superposed memory as its own; same rate for a third party's conflicting record | **Ours** (draft; V5) | No superposition precedent found |
| Claiming dissociates from access at matched mean access (memory link vs steering vector) | **Ours** | Ackerman & Panickssery 2025 show a static *self* vector can raise authorship claims, a different vector and readout |
| Collision is by role, not ordinal index or name | **Ours** (existing counterbalancing and strict third-person data) | Contradicts a pure ordinal account; consistent with role-binding |
| "Your own earlier thoughts" label reduces adoption (10.6% vs 42.6%) | **Ours**, against the label-following of Panickssery et al. 2024 and the in-slot advantage of Li et al. and Tsui 2025 | None found |
| Training-free RoPE relocation separates sources | **Untested anywhere**; binding work predicts null, role-position work (Wang et al. 2025; Ye et al. 2026) allows a positive result | None found |

## Strand B: binding mechanisms and parallel contexts

- **Feng & Steinhardt, "How do Language Models Bind Entities in Context?", ICLR 2024, arXiv 2310.17191.** Causal mean interventions on LLaMA models in two- to three-pair binding tasks.
  - Swapping binding-ID differences flips binding.
  - Binding IDs transfer across tasks.
  - Moving activations by changing the RoPE rotation barely changes behavior (Section 3.2, Appendix C) **[verified]**.
  - Collision of binding IDs gives about 50% **[verified]**.
  - *Bearing:* predicts our 50% and the near-independent choice of rule and code word (57.1% same side). It forecasts a null for relocation.
- **Dai, Heinzerling & Inui, "Representational Analysis of Binding in Language Models", EMNLP 2024, arXiv 2409.05448.** A low-rank ordering-ID subspace whose patching changes the bound attribute. It correlates with order, not absolute token position. *Bearing:* the address is computed in the residual stream.
- **Prakash et al., "Language Models use Lookbacks to Track Beliefs", NeurIPS 2025, arXiv 2505.14685.** Characters, objects and states are bound by ordering IDs. Retrieval uses address, pointer and payload copies, with interchange effects near 1.0. *Bearing:* the "address" vocabulary is already taken for order-based retrieval and must be cited.
- **Gur-Arieh, Geva & Geiger, "Mixing Mechanisms", ICLR 2026, arXiv 2510.06182.** Ten tasks and nine models. Positional, lexical and reflexive mechanisms mix. The positional mechanism dominates with two or three groups and at list edges. *Bearing:* a reviewer will call our cards a two-group positional retrieval. Our counterbalancing shows the receiver does not dereference by ordinal index (no Robin answers when the line orders differ). That points to role-based rather than purely positional retrieval for this task.
- **Enouen & Galhotra, "Shifting Mechanisms", arXiv 2609.38530 (September 2026).** Across 22 models, RoPE models rely mainly on positional retrieval and hybrids with NoPE global layers shift toward semantic retrieval **[verified abstract]**. The per-model figures (Qwen3-4B r_pos 0.82) are from the subagent and were not verified.
- **Parallel and superposed contexts.**
  - **Parallel Context Windows** (Ratner et al., ACL 2023) reuses position IDs across windows.
  - **Structured Prompting** (Hao et al. 2022) right-aligns groups and rescales attention to the test input by M×. This is a precedent for our log-w joint softmax.
  - **APE** (Yang et al., ICLR 2025) shares positions and fixes failures caused by duplicated sink states. Rotating initial keys beyond 90–150° breaks parallel encoding.
  - **Attention entropy** (Zhang et al., ACL 2025): overlapping positions raise query attention entropy.
  - None measures which context a fact is attributed to.
  - *Bearing:* the superposition engineering is old; the attribution question is not asked. Shared or duplicated sink tokens are a known confound that our relocation design must handle.
- **Source separation by embeddings or positions.**
  - **ASIDE** (Zverev et al., ICLR 2026) applies a 90° rotation of data-token embeddings *plus* instruction tuning.
  - **ISE** (Wu et al., ICLR 2025) uses trained segment embeddings.
  - **The Illusion of Role Separation** (Wang et al. 2025, arXiv 2505.00626): fine-tuned models assign role by proximity to the beginning of text, and shifting position IDs degrades it. Their fix is a position-ID gap applied with fine-tuning.
  - *Bearing:* the only evidence that raw position IDs carry role. It allows a positive relocation result, but in fine-tuned models.
- **Knowledge conflicts** (Xu et al. 2024 survey): inter-context conflicts are resolved by relevance, frequency, parametric agreement and order. No symmetric 50/50 experiment is reported.

## Strand C: LLM self-attribution, role slots, prefills, introspection

- **Li, Li, Fan, Yong & Tran, "Where Is the 'Self' of a Large Language Model? From Self-Index to Self-Reference", arXiv 2610.16717v3.** Identical bodies are placed in Assistant, User or System slots.
  - Assistant-slot text is attributed to "you" at 0.770, and external text at most 0.07.
  - A wrong first step is adopted 0.92 from the Assistant slot vs 0.75 from the User slot (+0.110, CI 0.059–0.168) **[verified]**.
  - Patching the post-message tokens removes self-attribution in late layers.
  - *Bearing:* the text-level version of our thesis, stated explicitly. The paper calls the interaction with genuinely self-generated text "open".
- **G & Lindsey, "From Simulation to Enaction: Post-trained Language Models Recognize and React to their own Generations", arXiv 2605.25459.**
  - Overwriting user-token KV with a paired prompt's KV in Llama-3.1-70B-Instruct suppresses true prefill detection: P(PREFILLED) goes from 0.56 to <0.01 for food and from 0.89 to <0.01 for sport.
  - The overwrite induces false positives in 8 of 8 domains **[verified]**.
  - *Bearing:* the closest KV-level precedent. It is the same instance with replaced KV and an authorship verdict; there is no superposition, no second history and no relocation.
- **Lindsey, "Emergent Introspective Awareness in Large Language Models", transformer-circuits 2025 / arXiv 2601.01828.** Models disown prefilled words. Injecting the word's concept *before* the prefill reduces disowning, while injection afterwards does not. The proposed mechanism is a consistency check between prior activations and output. *Bearing:* a competing account of ownership; see the predictions below.
- **Ye, Cui & Hadfield-Menell, "Prompt Injection as Role Confusion", ICML 2026, arXiv 2603.12277.** Role probes show style overrides tags: assistant chain-of-thought text under user tags stays at 85% chain-of-thought-ness. In Appendix K (gpt-oss-20b, probes only), position writes role more strongly than tags.
- **Panickssery, Bowman & Feng, NeurIPS 2024, arXiv 2404.13076.** Self-recognition and self-preference. Preference follows a swapped authorship label for GPT-4 on XSUM (0.73 → 0.32). *Bearing:* a label effect in the opposite direction from our label inversion.
- **Ackerman & Panickssery, ICLR 2025, arXiv 2410.02064.** A layer-16 self-recognition vector in Llama3-8B. Adding it raises authorship claims on text the model did not write from about 35% to about 80%.
- **Davidson et al., EMNLP Findings 2024.** No consistent self-recognition across ten models. Names the risk of copies that differ only in client information, but does not test it.
- **Wang et al., "Prefill Awareness", arXiv 2606.12747.** Most models are at floor in detecting opposing prefills; detection and resistance are decoupled.
- **Nguyen, Ahmed & Kim, arXiv 2606.23671.** Ten open models, including Qwen3-4B. Prefilled harmful continuations are claimed as intended at 25.3% on average. The per-model cell was not verified.
- **Gupta, Krier & Matlin, "When Goals Leak Across Relationships", arXiv 2610.17365.** One OLMo-3-7B with a shared cache across two clients; 22.0% goal deviation. Goal ownership is decodable from goal-span K/V (AUROC 0.982).
- **Fraile Navarro, arXiv 2610.01490.** Without the system-prompt persona anchor, assistant-turn history alone does not keep the persona: disowned in 37 of 40 sessions.
- **Zou et al., arXiv 2609.35108.** Qwen3-4B localizes an injected static concept vector at 54.5% (random direction 0.84%). Static perturbations are detectable in our model, so failure to notice under the memory link is not a general blindness.

## Competing accounts and what each predicts for relocation

| Account | Core claim | Prediction at matched access, B's cache relocated to a preceding document |
|---|---|---|
| Region or placement (draft Section 4) | A reads "my assignment" from the stretch of positions where its card lies | Claiming falls far below the original placement |
| Content-borne role binding (Feng & Steinhardt; Dai; our order and third-person data) | Each cached card carries its own holder-role code; the reader matches role, wherever it lies | Claiming about unchanged |
| Position writes role (Wang et al. 2025; Ye et al. 2026 Appendix K) | Distance from the start of text sets role authority | Claiming falls, possibly because B's card loses authority rather than because sources separate; check Robin and ACC |
| Consistency check (Lindsey 2025; G & Lindsey 2026) | Ownership is judged by agreement between earlier cached states and the answer, position-agnostic | Claiming about unchanged; a retroactive static injection at A's card positions should produce claiming |
| Access only | Claiming tracks how much of B's content reaches A | Unchanged at matched access (already contradicted once by STATIC, with a different payload) |

So relocation separates "where it lies" from "what it carries". The extra cells needed are a retroactive static injection at A's card positions (the consistency account) and a direct detection probe (Lindsey-style: "a memory may have been inserted; was it?") before treating "no conflict noticed" as a positive result.

## Strand A: KV, latent and activation communication, and cache reuse

About 35 sources were checked. **None measures whether a receiver confuses its own record with a partner's**: no ownership, "who was assigned what", or self/other readout.

- **The mechanism has been stated, but only as an accuracy concern.** ParaThinker (Wen et al., arXiv 2509.04475, Section 3.4): with parallel reasoning paths sharing position indices, "the model cannot differentiate which reasoning stream a token originated from" **[verified]**.
  - Their fix is a learned per-path embedding added to keys before RoPE and to values.
  - Ablation on AIME 2024 with 8 paths: 48.1 with the embedding, 46.7 without **[verified]**.
  - Giving each path its own position range ("flattened") was worse, which they attribute to RoPE distance decay. No numbers are given for that comparison.
  - There is no attribution metric.
- **Layouts in practice.**
  - *Overlapping positions with different content:* Parallel Context Windows; APE; Multiverse; KV-Fusion; TurboRAG "composite" (LongBench average 31.76 vs 36.29 re-ordered); superposition prompting; ParaThinker without its embedding.
  - *Hidden-state superposition at one index:* Ramesh & Li (ICML 2025, one token); the Bicameral Model (arXiv 2605.11167, lockstep).
  - *Same content at the same positions:* C2C (ICLR 2026).
  - *Appended or sequential, no overlap:*
    - KVComm (ICLR 2026, arXiv 2510.03346): in code, the sender cache precedes the receiver's. In effect this is our proposed "preceding document" layout, and access survives it.
    - KVCOMM (NeurIPS 2025), which de-rotates and re-rotates keys.
    - LatentMAS, Hogwild!, Group Think, Interlat, ThoughtComm, LatComm.
- **Deployed accidental overlap: MemOS** (code at commit adcb9f2, 2026-10-23) **[verified]**.
  - `build_kv_cache` (`src/memos/llms/hf.py:354`) prefills each memory separately from position 0, under one system template: "Below is some information about the user."
  - `_concat_caches` (`src/memos/memories/activation/kv.py:200`) merges caches with a bare `torch.cat` per layer, without re-rotation.
  - So several memories carry the same header at the same rotary phases. Whether this causes attribution errors in MemOS is untested. GitHub issue #2315 on the positional bug was reportedly closed as "not planned"; the subagent reported this and Claude did not check it.
- **Nearest named "identity confusion": LACO** (Chen, Wu & Lee, arXiv 2605.22504), a collaborative-driving system. Direct latent fusion "entangles decision representations across vehicles". The evidence is attention maps and driving score; there is no verbal ownership and no position analysis.
- **Audits.** "When Does Latent Communication Pay?" (arXiv 2608.04893): a cache relayed from the wrong example makes 64–65% of answers match the donor example (control 21–23%). That is content substitution with no competing own record. Attribution is not measured.
- **Re-rotation is benign for access.** TurboRAG, CacheBlend, EPIC, Block-Attention, KVLink and KVCOMM re-rotate cached keys without training and keep accuracy. That supports the feasibility of relocation. ParaThinker's distance-decay warning makes access matching essential.

**Verdict for this strand.** A measured ownership error in KV sharing is new. The idea that shared positions erase stream identity must be credited to ParaThinker, which fixed it with trained embeddings. A training-free RoPE relocation used as a causal test of ownership at matched access has not been done. MemOS gives a concrete deployed case where our result would apply, if relocation matters.

## Strand D: human source memory, philosophy, brain bridges

[P] = the subagent read the primary text (OCR for scans); [S] = abstract or secondary source only. Claude did not re-read these.

- **Source monitoring framework** (Johnson, Hashtroudi & Lindsay 1993, Psych Bull 114:3–28 [P]).
  - Memories carry no "abstract tag or label" of origin. Source is inferred at retrieval from perceptual, contextual (spatial/temporal), semantic, affective and cognitive-operation features.
  - "The more similar the memory characteristics from two or more sources, the more difficult it will be to specify the source correctly."
  - Without source cues, judgments fall back on fluency, familiarity and availability.
  - *Bearing:* our symmetric bridge matches every feature class by construction. The framework then predicts chance discrimination resolved by relative strength, which is our w curve. This is the theory behind the reviewer's symmetry objection, and it predicts our result rather than being discovered by it.
- **Similarity gradients.**
  - Johnson & Raye 1981 [P]: source accuracy 62/68/74% as self-generated words became less similar to heard ones.
  - Johnson, Foley & Leach 1988 [P]: heard-vs-imagined discrimination .89 (imagined in own voice), .78 (third voice), .62 (speaker's voice). Errors run one way: imagined→heard.
  - Lindsay, Johnson & Kwon 1991 [P]: .66 (similar storytellers) vs .82 (dissimilar); 6-year-olds at chance with similar sources on a shared topic.
  - *Bearing:* making B's memory dissimilar (layout, language, persona) should lower claiming monotonically.
- **The human self-advantage is feature-based.** Self-vs-other discrimination beats other-vs-other (Raye & Johnson 1980). The "it-had-to-be-you" bias holds. Errors are mostly own→other (Hollins et al. 2016 [S]). Ross & Sicoly 1979 [P] link egocentric credit to availability. The framework explains the advantage by records of cognitive operations and strength, not by an owner tag.
  - *Bearing:* an LLM home advantage should appear exactly when A's record carries operations that B's does not (A derived or worked with its rule in its own stream), and vanish otherwise.
- **Same voice, same moment: Lind et al. 2014**, Psych Sci 25:1198–1205 [P]. Participants' own recorded voice saying the other word was played at the moment they spoke; only 32% of swaps were detected, and 85% of undetected swaps were accepted as what they had said. Detection rose when timing was off.
  - *Bearing:* the closest human "same slot" case. It predicts that relocation should lower claiming *and* raise noticing.
- **Cryptomnesia** (Brown & Murphy 1989 [P]): 7.3% of recalled "own" items were others' (chance 1.6%), most from the immediately preceding speaker, and plagiarized items got *low* confidence. Humans keep a partial metacognitive warning; our receiver showed none.
- **Memory conformity** (Gabbert et al. 2003 [S]: 71% of discussing witnesses reported partner-only details). Humans absorb communicated content readily. Our explicitly attributed text message was never claimed: stronger source preservation than humans show for communicated content.
- **Philosophy.**
  - Shoemaker 1970 [S]: a quasi-memory implies only that "someone or other" had the experience. Memory is only circumstantially immune to error through misidentification, and "in the absence of evidence to the contrary" self-attribution is the reasonable default.
  - Parfit 1984, pp. 220–222 [S, via Roache 2006]: Jane, given Paul's memory traces, can identify them as Paul's only from outside knowledge. The belief that a memory is one's own is "a separable belief".
  - *Bearing:* both predict default self-attribution of a mark-free foreign memory. Our receiver has no outside knowledge, unlike Jane.
- **Brain bridges.**
  - Hirstein 2008 [P]: a mindmelded receiver would experience the other's states intimately yet know they are "in some important sense not his", with "an odd feeling of lack of control". The paper already reports this prediction failing for our memory link.
  - Brain-to-brain interfaces (Pais-Vieira 2013; Rao 2014; Jiang 2019 BrainNet [P]): no study measured self/other attribution, and all used perceptually foreign, labelled channels. They correspond to our explicit-message condition, not to the memory-slot condition.
  - Hogan craniopagus twins: no peer-reviewed first-hand report; anecdotes only (Cochrane 2021 [S]).
- **Is the combination stated?** The parts are: the framework's similarity principle and fluency fallback, and Shoemaker and Parfit on mark-free q-memory. No source was found that combines identical features and an identical slot and draws the "relative strength decides" conclusion. Safest framing: we put q-memory and the identical-features limit into practice and measure them. We do not discover the principle.

## Overall verdict

- **Not new:** "mine is an address", stated generally (Li et al. 2026 for text; binding work for the mechanism; ParaThinker for shared-position confusion), and "about 50% at equal weight" (forced by the design's symmetry and predicted by the source monitoring framework).
- **New and worth doing:** using two identical copies as the one system where every source-monitoring feature can be equalized exactly, then adding back **one asymmetry at a time** (placement, encoding context, own cognitive operations, format, labels) and measuring which ones restore ownership while keeping access. No human study can equalize features this way. No KV-communication study has measured ownership. No study has used a training-free relocation as a causal test.
