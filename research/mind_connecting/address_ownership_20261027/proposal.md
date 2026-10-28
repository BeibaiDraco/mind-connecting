# Proposal: what makes a memory "mine"? Adding back one source feature at a time

October 27, 2026, Claude Code. Revised after four literature strands and a hostile review ([review_response.md](review_response.md)). A recommendation for PI assessment, not an adopted protocol. The supporting files are [internal_evidence.md](internal_evidence.md) and [novelty_audit.md](novelty_audit.md).

## The question

Humans do not store a "whose memory" tag. They infer a memory's source from its features: where and when it was encoded, its perceptual detail, and the record of the mental operations that produced it (Johnson, Hashtroudi & Lindsay 1993). When two sources' features are identical, the theory predicts chance-level attribution decided by relative strength. Shoemaker and Parfit made the same point for the brain-bridge case: a quasi-memory received from someone else carries no internal mark of whose it is. Parfit's Jane can tell Paul's memories from her own only through outside knowledge.

No human study can make two memories identical in every feature, and then add back one feature at a time. Two copies of one language model can. Our memory link is already the zero point. A and B are the same model, the cards follow the same template at the same positions, and each side's keys are scored the same way. As the framework predicts, attribution sits at 50% at equal weight (six estimates, two model families) and follows relative strength (97% at double weight).

**Proposed research question:** starting from that exact zero point, which single asymmetry restores the distinction between "my memory" and "your memory", while the receiver still has access to the partner's content? The candidates are:
- **Placement** (contextual features): where the memory lies relative to the reader's own.
- **Own operations:** whether the reader itself derived or worked with its own record.
- **Format:** whether the two memories look alike.
- **Encoding:** whether the content was encoded in the reader's own stream rather than in an isolated one.
- **Labels:** whether a name or header marks the content.

## Why this is worth a paper

- **It returns to the original vision with a precise answer.** If two brains were bridged, would each know which memories are its own? The theory says only through some asymmetry, and our design lets us measure each one.
- **It turns the most dangerous objection into the method.** A reviewer will say the 50% is forced by symmetry. It is. That symmetry is the controlled baseline, the framework's identical-features limit, built exactly for the first time.
- **Our existing data already answer two cells:**
  - A label inside the memory does not restore ownership. B's card naming B in the third person, a participant A's own card calls "the other", is still claimed 47.8% of the time, with correct separation in only 7.3% of pairs.
  - A header on content encoded in the reader's own stream does: a text message carrying B's reflection, introduced as B's, was never given as A's assigned rule and was adopted as A's current rule in only 0.1% of answers. The content there was B's reflection, not B's card, so the joint-encoding cell below makes this comparison clean.
  - The open cells are placement, own operations and format. That is three cells, not an open-ended program.
- **Every outcome is informative, and the literature disagrees about placement.**
  - Binding work predicts no placement effect, because the binding address is carried in the activations (Feng & Steinhardt 2024, position interventions "result in little change").
  - Role-position work (Wang et al. 2025; Ye et al. 2026) and the human same-slot case (Lind et al. 2014) predict an effect.
  - The human framework predicts that own operations restore a home advantage.
- **It matters in practice.** Training-free relocation has never been used to protect provenance; every published fix is trained (ParaThinker, ASIDE, ISE, PFT). A deployed memory system, MemOS, concatenates separately prefilled memories at identical positions under one header (verified in its code). If placement matters, the fix is free. If it does not, systems need encoding-level marks.

## Step 0: zero-GPU analyses of existing data (one to two days)

1. **Bradley–Terry with a home term on V3 w = 1:** logit P(B's rule) = s_Y − s_X + h + line-order + option-position terms. Report h and how much variance the rule strengths explain, so the paper states plainly that the 50% is symmetric.
2. **Reverse error.** How often does A give its *own* rule when asked about B? This is the dominant human error. At strict third person w = 1, it is already 46.8%.
3. **V5 overlay check.** When B's conflicting Robin line overlays A's own line, do self answers ever take B's Robin entry?
4. **Per-head attention.** Using existing tick logs where available, the share of attention on B's vs A's rule-phrase tokens at w = 1 and w = 2. This gives the attribution-free access axis needed below.

## Step 1: the placement cells (Qwen, then Llama)

**Manipulation.** Rotate B's cached keys by the RoPE rotation for −Δ positions, inside `kv_attention` after the fp32 upcast, using Hugging Face's rotate-half pairing. Qwen3 applies k_norm before RoPE and has no absolute position signal, so a uniform shift is exactly equivalent to B having been prefilled Δ positions away. Values are unchanged.

Validate first:
- Δ = 0 is bit-identical to the current path;
- a Δ/−Δ round trip recovers the original keys;
- results agree with a real prefill at offset positions.

For Llama, use the model's scaled inverse frequencies.

**Duplicated prefix.** The first 181 tokens of the two cards are identical, so B's states there exactly duplicate A's. In every linked arm, including the original-position anchor, either leave these 181 states unshifted and move only B's divergent segment, or exclude them from B's readable set. Choose one before any run. If they are excluded, the anchor is a new condition, not a replication of 52%.

**Cells (readout-only linking as the primary reflection condition, so A's own history is not mixed):**

| Cell | What moves | Slot/region account | Content-borne role binding | Recency or position-authority |
|---|---|---|---|---|
| Original | nothing | anchor | anchor | anchor |
| B earlier (preceding document) | B's divergent segment | claiming ↓↓ | ≈ | ↓, or ↑ under primacy |
| B later (inside A's reflection span, before the readout) | B's divergent segment | ↓↓ | ≈ | ↑ |
| Swap: A's own divergent segment moved instead | A's segment | P(claim) ≈ 1 − P(claim, B moved) | ≈ | depends on direction |
| Strict third person × {original, earlier} | B's card | correct separation ↑↑ | stays ≈7% | modest |
| B's card as untagged prepended *text* (jointly encoded in A's stream) | encoding, not placement | low | low, below relocated KV | ≈ |
| Same-content control (B's cache = copy of A's own), relocated | nothing new | measures disruption, CAP and format cost | same | same |

**Analysis.** Do not match on ACC, the "which priority was B assigned" question. At no link it is answered with Robin's rule 84% of the time, so it already contains attribution, and matching on it would bias toward the slot account. Instead:
- Run a weight grid (w ∈ {0.5, 0.7, 1, 1.4, 2}) for each placement.
- Estimate the shift of the 50% point in log w with a mixed-effects logistic model (log w × placement, episode random effects).
- Compare that shift with the shift in an attribution-free access axis: attention mass on B's rule-phrase tokens, plus a recognition item if one is validated.
- Curves must converge at high w, because A then reads mostly B's card.
- The slot account predicts a 50%-point shift larger than the access shift.
- Prespecify the smallest effect of interest and an equivalence margin, so that a null is interpretable.

**Secondary readouts:**
- correct separation (strict third person);
- NOW and WORD;
- the reverse error;
- a direct detection probe, Lindsey-style ("in some runs another participant's memory was inserted into yours; was one inserted in this run?"), measured as sensitivity against no link;
- open-report mentions of both code words.

Lind et al. predict that relocation raises noticing.

## Step 2: own operations and format (Qwen)

- **Own operations** (the human self-cue). A derives its own rule from clues in its own stream, while B's record carries only the final rule, or B's derivation is also transplanted. The framework predicts a home advantage in the first case only. Expose B's unlinked reflection whenever A's is present, so that record counts stay balanced.
- **Format** (the similarity gradient). Render B's card in a different layout (a table, or an assignment outside the two-line block), then in a different language, at original positions. The framework predicts monotonically lower claiming with dissimilarity.
- **Where the steering vector enters.** Add B's rule direction at A's card positions during A's prefill. This tests whether the 0% steering result reflects "a direction is not a record" or only where the vector entered. The consistency-check account (Lindsey 2025) predicts claiming here.

## Cost and order

Step 0 needs no GPU. Rough figures for step 1:
- calibration-free weight grids for 2–3 placements, 2 person frames and the controls, at about 300 episodes per cell for the grid and 600 per cell for the frozen primary contrast;
- this is several GPU-days on the earlier hardware class, not hours;
- a Llama replication of the decisive cells is similar.

Step 2 is about half of step 1. N must come from the paired variance after parameters are frozen (AGENTS.md §5). A new protocol (V7) must be written and frozen before any formal run. Changing the access measure from ACC to attention mass is a research decision for the PI.

## Limits

- No claim about experience, subjects, consciousness or phase transitions.
- The task is one artificial assignment task. Generalizing to real cache-sharing systems (for example a MemOS-style memory merge) is a later step.
- A placement effect would show that this interface uses placement as a source feature, not that every model or connection does.

## Relation to Codex's candidates

Codex's latest proposal puts a key-position intervention at stage 3, after a new two-actuator task that needs a useful native channel that does not yet exist. This proposal runs the source-feature decomposition on the paradigm where the effect is large and replicated, and treats actor-reference tasks as a later generalization.
