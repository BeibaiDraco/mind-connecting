# V6 new-card engineering trial: first CUDA gate failure

The new A100 80GB rental reached actual CUDA testing after the separately
recorded connection, packaging and deployment repairs. The first operator
test failed. The frozen 23-test admission gate therefore did not pass and the
controller stopped; no fallback kernel, numerical retry or scientific run
was launched.

The failed test was
`test_fused_operator_independent_oracle_and_exact_repetition[efficient_sdpa]`.
Its BF16 query was passed to the memory-efficient SDPA backend with an FP32
additive attention mask. PyTorch 2.6.0+cu124 rejected that dtype combination
at `src/mb/v6_efficient.py:184`, before returning an operator result. The test
command stopped on first failure: one test, one failure, zero errors/skips,
11.10 seconds reported by pytest. This is a CUDA implementation compatibility
failure, not an observed numerical disagreement with the independent oracle.

The compiled-flex case and remaining admission checks did not complete.
Neither real model's native binding/microcomparison/full engineering cases
were produced. Consequently this attempt supplies no model speedup estimate,
no complete-workload time/cost estimate and no scientific result. It does not
establish whether the selected compiled-flex candidate would pass its own
checks; skipping the failed gate would change the approved admission rule.

The controller sealed and copied the failure evidence, verified provider
actual stop and exact local-guard retirement, and independently rehashed its
backup. The supervising agent additionally verified all 35 sealed evidence
files and all 55 local-control SD files. Final receipts are under
`/private/tmp/mb-v6-execution-20261012/optimization-benchmark-20261016/compressed-deployment4/`;
the restored evidence is under
`/Volumes/VERBATIM SD/mind-connecting-data/v6/optimization-benchmark-20261016-compressed-deployment4/restored/`.

An independent reviewer also verified the sealed archive's exact member set,
all 35 evidence files, all 55 SD control files, all 90 source-inventory entries
and all 68 immutable package pins. The worker fails its CUDA-test check before
entering the real-model loading loops. Saved actual-stop and exact-target
guard-completion receipts agree; the review did not perform another provider
action or a live process observation.

The completion automation is paused. All preceding failed attempts, original
financial origin, cumulative charges, USD8 trial/USD100 total limits and
source freezes remain intact. The instance is stopped with its disk/cache
retained; stopping GPU compute does not remove disk storage charges. No
destruction, further rental, restarted test or formal collection occurred.
Any subsequent implementation repair needs fresh concrete hardware-admission
planning; this failed trial does not authorize skipping a check or silently
changing the frozen source package. The separate historical 61-file backup
gap remains unresolved.
