# What makes a memory "mine"? Novelty audit and proposal

October 27, 2026, Claude Code, at the PI's request ("check carefully whether this view is new and good, and do the survey and proposal"). Advisory. No protocol, model run, manuscript change or paid action is adopted.

## Current state (after Codex's review, October 27)

- Codex reviewed the dossier: `docs/reviews/address_ownership_review_codex_20261027.md`, verdict "promising with fixes".
- Claude's point-by-point response and **plan v2**, which supersedes `proposal.md`, are in [response_to_codex_review.md](response_to_codex_review.md).
- A new zero-GPU result is in [symmetry_check.md](symmetry_check.md). At equal weight, swapping which side holds which rule gives claiming sums of 0.95–1.05 in four studies, every interval including 1. Owner identity has no detectable effect, and a model-specific content preference decides the winner.
- Plan v2 is a bounded study:
  - whole-bank RoPE translation of B's memory;
  - co-primary endpoints of source separation **and** a new donor-only use assay;
  - pilot about 1–3 H100 hours, formal run about 6–10 H100 hours;
  - a link to Codex's actor-reference task only if a selective repair appears.

## Verdict in brief (first pass; see corrections above)

1. **The first idea ("in a transformer, 'mine' is an address, not a label") is not new**, in three ways:
   - It is the draft paper's own Section 4 account ("two cards, one slot"), including the relocation test, which was never run.
   - For text, Li et al. (2026) state that the self-index is attached to the Assistant slot, not to authorship.
   - Binding work (Feng & Steinhardt 2024) and ParaThinker (2025) already describe collisions between identically structured or co-positioned records.
2. **The "50% at equal weight = zero home advantage" reading was wrong.** The 50% is forced by the design's exchange symmetry. It is a check that the bridge is symmetric, not a finding about the self.
3. **What is new and worth a paper** is to use the symmetric bridge as an exact zero point, where all of the source monitoring framework's features are equal. That is impossible in humans. We then add back one source feature at a time: placement, own operations, format, encoding, labels. Existing data already settle two cells: a label inside the memory does not restore ownership, and a header on content encoded in the reader's own stream does.
4. **The decisive open cell is placement.** The literature disagrees: binding work predicts no effect, while role-position work and the human same-slot case predict one. It needs a new frozen protocol, with the access measure changed from ACC to an attribution-free axis. Either outcome is informative, and the result bears on deployed systems such as MemOS, which merges separately prefilled memories at identical positions.
5. **Publication outlook.** A clean result would make a cross-disciplinary paper (ML interpretability plus cognitive science), credible at a main ML venue. It is not assured. The area moved fast in 2026 (Li et al.; G & Lindsey; Ye et al.; Goals Leak), so speed matters.

## Reading order

1. [internal_evidence.md](internal_evidence.md): what the draft already says, the verified numbers, the token-alignment facts, the symmetry concession, and corrections to the earlier verbal summary.
2. [novelty_audit.md](novelty_audit.md): four literature strands (binding and parallel contexts; LLM self-attribution; KV communication systems; human source memory and philosophy), the claim-by-claim status, and competing-account predictions.
3. [review_response.md](review_response.md): the hostile review and what changed.
4. [proposal.md](proposal.md): first-pass proposal (superseded).
5. [symmetry_check.md](symmetry_check.md) and [response_to_codex_review.md](response_to_codex_review.md): the current state and plan v2.

## Not done

No model was run. Of the offline analyses, only the symmetry check has been run. The full confusion matrix, use-assay design and protocol V7 draft are pending. Subagent-read sources are marked; the passages Claude re-read are marked **[verified]** in the audit.
