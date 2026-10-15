# Independent review: substantial V6 efficiency proposal

2026-10-15. Read-only review by the separate `v6_perf_review` agent; recorded by
Codex. Scope: mathematical reformulation, B/T scheduling, scientific invariants,
CPU algebra check and financial claims. No model, GPU or scientific outcomes
were used by the reviewer. This is not native acceptance or PI ratification.

## Findings incorporated in the prospective proposal

1. Joint weighted attention is a plausible new numerical implementation, not an
   exact-bit migration. Existing own attention is already rounded before FP32
   mixing. Keep study settings but explicitly amend numerical acceptance before
   adoption; do not excuse trajectory changes with similar research conclusions.
2. Test tiny joint-kernel and B/T feasibility before a scheduler rewrite. The
   864-case FP64 checker shares score preparation, so it is an algebra cross-check
   rather than an independent implementation oracle. A future kernel needs an
   independent reference, layout/mask/GQA adversarial cases and native acceptance.
   A supplied mask can change the adapter's GQA dispatch or cause a slow fallback.
3. Known-input prefill and independent-pair batching are the main plausible
   throughput opportunities. Preserve full-vocabulary and hidden finite checks
   for every previously checked token. Use own-prefix causal masking, fully
   visible held foreign keys and original donor post-RoPE positions. Ragged
   histories require accurate per-lane positions; padding must not enter history.
4. Freeze numerical scheduling. Exact same-shape Replay and resume remain strict;
   cohort/lane/chunk rules must not change silently after invalid-token recovery.
   Cross-shape numerical proximity is a different test. Verify lane isolation
   and permutation, and stop if these guarantees cannot be met.
5. Treat raw archival volume as a separate critical cost. Lossless deduplication
   and bounded CPU staging require owned buffers, copy completion, backpressure,
   failure handling, deadline draining and independently verified restore. The
   approximately 477.8 GB projection and incomplete copy evidence prohibit a
   certified full transfer forecast. Do not delete retained raw data.
6. Optional DAG sharing: source inspection confirms natural LIVE rounds 2–3 and
   5–6 have pulse L/version1 event and action-question semantics. Full state,
   window and numerical-schedule identity must still be proved. Retain logical
   records and separately owned continuing states. Never reuse Replay diagnostic
   computations. Maximum work-period reduction is 4/80, about 5%.
7. The 6–8x values are targets/sensitivity, not established savings or financial
   admission. Even an 8x division of the unchanged conservative compute estimate
   exceeds USD100 before prior costs and backup. New measurements are essential.

## Disposition

Recommend the prospective architecture with these qualifications. No unresolved
claim in the earlier exact-preserving feasibility runbook is newly approved by
this review. The larger proposal needs its own prospective numerical acceptance
decision, reviewed implementation and separately authorized engineering test.
Neither historical freezes nor original experiment authorization are expanded.

Primary-agent offline verification: 797 passed, seven skipped, one GPU deselected;
the standalone 864-case CPU algebra check also reproduced its saved result. No
native equivalence or speed claim follows from these offline checks.
