# V6 bottleneck proposal — independent review

Date: 2026-10-14, America/Chicago. Reviewer: Codex agent
`v6_perf_review`; recorded by the coordinating agent from the completed review.
This is a new historical record, not an edit of an earlier review.

The reviewer inspected the native backend, runtime, performance candidate,
benchmark harness, completed Qwen engineering timing snapshot and the new
tokenizer-only structural audit. No GPU, provider or network call, code change,
commit or scientific-effect inspection was performed by the reviewer.

## Conclusion

Prioritize fixed-window question prefill, followed by independent-lane batching
at 2, 4 and 8 only after correctness/memory checks. Retain exact native comparison.
The proposed direction is scientifically compatible at the causal-contract
level; neither numerical equality nor any speed multiplier is established.

## Findings incorporated into the plan

1. `v6_native.py:413` serializes a known linked question into one-token calls.
   `probe` holds one foreign window throughout question consumption. A vector
   implementation must retain every receiver query's own causal mask, absolute
   position, original foreign RoPE positions, gain and own/foreign mixing.
   The present callback accepts one history/query and takes only the final mask
   row. Removing its assertion alone would be incorrect.
2. Start batching with same-model, same-shape independent computations before
   padding/heterogeneous scheduling. Preserve the paired tick barrier at
   `v6_runtime.py:131`: both sides consume the old window and publish only
   after both finish. Known-input prefill cannot be applied across live ticks.
   Cohort composition and batch shape must not silently change results.
3. Strict prefix reuse is limited to linked positive-gain inputs, where the
   reference already consumes individual tokens. Splitting OFF/zero-gain
   native multi-token prefill changes its shape. Same-parent token tries can
   remove only 1,120 of 13,108 linked input forwards (8.54%) in the structural
   full-task audit, before overhead; this is not overall measured speedup.
4. Digest work is substantial (about 197 inclusive seconds in the full task,
   65 in the baseline). Version counters/pointers alone weaken byte-integrity
   checks because some storage changes can bypass them. Explore owned verified
   snapshots and complete byte-equality checks before returning a cached hash;
   keep all metadata, integrity boundaries and the original SHA definition.
5. Clone timing is about one second in the full task. Shared KV is primarily
   a memory/batching enabler, not a demonstrated large time saving. Deleting
   `.clone()` permits mutable sharing and violates isolation. Copy-on-write
   must cover every mutation path and restored archives as well as ordinary
   execution.
6. Skipping intermediate `lm_head` removes existing full-vocabulary finite-value
   checks; finite hidden states and weights do not prove finite projections.
   This is not a strict-equivalence optimization without a separately proven
   equivalent check. Final full-vocabulary native selection and FP32 probability
   denominator must remain; four-label-only scoring changes the experiment.

## Required acceptance

Cover both fixed BF16 checkpoints, zero/all nonzero gains, window/question
lengths, side orders, all recovery categories, parent/sibling isolation,
archive restoration and two-round replay. Compare actual tokens, probabilities,
legal logits/mass, sealed/committed state bytes, exports and logical archive
digests exactly. Include injected intermediate NaN/overflow and cache mutation.
Retain failure evidence; do not replace a failed exact check with a tolerance.

The existing Qwen result establishes only a 45.1-second (2.61%) reduction for
one instrumented complete example. Probe/consume/digest timers overlap and
cannot be summed. The approximately 205-second archive restore is outside
the episode timer. New forecasts require synchronized complete-workload timing,
not token-count extrapolation. No new backend or paid attempt is accepted here.
