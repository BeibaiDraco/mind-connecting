# V6 flex compilation repair — independent local review

2026-10-16. The PI asked how to resolve the repeated engineering failure. This
milestone implements and reviews a local repair; it performs no provider call,
GPU/model execution, paid action, automatic retry or scientific continuation.
The last hardware attempt stays closed and the automation stays paused.

## Implementation and evidence

The saved failure and pinned PyTorch 2.6.0 source identify symbolic batch/head
metadata in flex decoding's split heuristic. Both joint and packed attention now
specialize structural axes inside the compiled graph while keeping the growing
KV length dynamic. Masks, bias precision, padding, causal barriers, tokens and
state-publication rules remain unchanged. New engineering versions and source
packages bind the explicit compiler policy; old failed packages are rejected by
the new sources rather than overwritten or retrospectively passed.

A separate code object per compiler owner preserves the callable bytecode,
globals, defaults and closure while isolating the Dynamo cache owner. Actual
compiler callbacks are counted and timed, limited to eight per owner. Compilation
or runtime failure makes the owner terminal. No global limit raise, cache reset,
eager fallback or backend switch is used. Reports retain success/failure events
and clearly distinguish callback time from complete first-call and phase time.

The first local focused run passed 422 tests; after package additions, the full
offline suite passed 1234 tests, with ten skipped and one deselected. A later
coverage-only CUDA-test expansion was syntax/count checked, and 52 focused tests
passed. The independent reviewer `/root/v6_perf_review` passed 424 relevant
offline tests on the final snapshot and found no unresolved local issue.

The review required expanding hardware coverage from small shapes to all six
real-model B/T combinations and twelve production-range KV lengths for B4/T1
and B4/T16. That revision is included. The original 47 CUDA cases are retained;
eight additional cases bring the required complete gate to 55. They test reuse
across twelve lengths, nine compiler owners without resets, actual attention
shapes and stable compilation counts. These CUDA tests remain unrun. All local
checks are torch-free and do not prove compiler correctness or numerical speed.

The accepted 11-file review-manifest digest is
`3e0500f8caad5ced1eb1aaa065b3386a222fd26bd542b3b87970aa2bc4fb450b`.
The inert 75-source compiler-check package is at
`/private/tmp/mb-v6-flex-repair-20261016/compiler-check-01/package.json`, SHA256
`609946f3f13bc7e42cd2b226a4ae7fb77247f677371a027408087f9717e30edc`.
Every package source pin was independently recomputed locally. It explicitly
grants no paid launch, real-checkpoint loading, forecast or continuation.

## Next proposed bounded check

The new proposal runs ten targeted cases first, then requires the complete
55-case gate, retaining failure/no-skip rules. Proposed containment is USD2
additional and 30 minutes through actual stop within original cumulative USD100;
all historical charges and the original deadline remain. This is not an approved
allowance or guaranteed runtime. Fresh financial/instance/guard/controller
admission is still unbound. No real-checkpoint benchmark or science follows this
compiler diagnostic. See `docs/runbooks/V6_FLEX_COMPILE_REPAIR_20261016.md` for the
pinned sources, timing limits and scope. All previous evidence gaps and failures
remain explicitly preserved.
