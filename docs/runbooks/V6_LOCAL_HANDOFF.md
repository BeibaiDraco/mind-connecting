# V6 local implementation handoff

Date: 2026-10-12. Status: local prototype implemented; no GPU execution or
scientific freeze. Design: `docs/protocol/PROTOCOL_V6_CONTINUOUS_DRAFT.md`.
Contracts and limits: `docs/protocol/V6_IMPLEMENTATION_NOTES.md`.

## What is ready locally

The task generator, persistent six-round scheduler, directional cuts, FRESH
shadows, pulse replay, independent goal probes, actual action continuation,
material-only text subset, episode-level statistics and append-only synthetic
ledger are implemented. The isolated native KV backend and native archive
schema are implemented with unrun CUDA acceptance tests. Independent reviews
covered modules authored by other agents and the final integration changes.

All repository offline tests pass: 543 passed, six skipped. Skipped/native CUDA
tests are not evidence that a real model, KV bridge or persisted CUDA replay has
passed. The new local code adds 115 passing tests to the prior 428-test baseline.

## Reproduce local checks

Run from the repository root using the existing Python 3.12 environment. Do not
install torch or load a model on this Mac.

```bash
.venv/bin/pytest -m "not gpu"
.venv/bin/python scripts/v6_local_preflight.py materials --audit-tokenizers --output /private/tmp/v6-material-review-UNIQUE
.venv/bin/python scripts/v6_local_preflight.py dry-run --output /private/tmp/v6-fixture-UNIQUE --n 2
.venv/bin/python scripts/v6_local_preflight.py dry-run --output /private/tmp/v6-fixture-UNIQUE --n 2 --resume
.venv/bin/python scripts/v6_simulate_analysis.py --repetitions 50 --n 240 --bootstrap 200
```

Use a fresh output directory, replacing `UNIQUE` each time. Reuse the exact same
arguments for a no-op resume. The materials command reads existing pinned local
tokenizers only. The dry-run uses a deterministic hash-based fixture, including
when its schema is named after Qwen or Llama. It never runs those models. Its
short clocks are for software checks; full 64/16/16 clocks can also be exercised
through `RuntimeSpec()` without a model.

The simulation uses the actual ledger validator, episode scoring and multiplicity
code. Bootstrap 200 is only a cheap simulation setting; the draft scientific
analysis remains 10,000 draws. A small Monte Carlo exercise does not establish
power against the models' unknown behavior.

## Remaining work before a GPU request

1. Put the four unresolved neutral admission details in the implementation notes
   to the PI as a concrete prospective proposal. Implement and review the neutral
   collector, neutral-only selector and full-duration gates after that decision.
   Retain disjoint materials and prohibit outcome-based parameter selection.
2. Review draft prompt wording, all material balance reports, N240, N60 text,
   clocks, gain grid and 22/4 test families together before a scientific freeze.
   Local coding approval alone has not ratified these numbers.
3. Finish production native orchestration with exact source/config admission,
   complete pair/world restore, bounded failure handling and a guarded acceptance
   command. The current command-line entry point deliberately exposes no GPU
   run. The archive API alone is not a production resume certificate.
4. Prepare a bounded hardware acceptance package: both pinned models, independent
   no-link reference, exact native attention and replay, all control-token
   recoveries, invalid-action continuation, A/B order invariance, branch
   isolation, archive/restart roundtrip, smoke and byte-preserving no-op resume.
   Text-control spelling failures must be addressed prospectively, not by
   discarding a formal episode or silently changing its text.
5. Include full-weight hashing, cache growth, FRESH shadows, FP32 diagnostics,
   snapshot volume, disk space and verified backup in timing/cost measurements.
   Previous static-cache runs provide no reliable ETA for this implementation.
   Present a new initial allowance and total cap before renting anything.

Only after local completion and separate paid authorization should hardware
acceptance begin. Admission data and parameters must then be prospectively
frozen under the agreed sequence before any formal collection. No old instance,
budget, continuation exception or automation is inherited.

## Evidence locations

The compact tracked review is `docs/reviews/v6_local_implementation_review_20261012.md`.
Generated material fixtures and full local simulation/dry-run artifacts reside
under `/private/tmp/mb-v6-local-*20261012*`; these are reproducible temporary
engineering artifacts, not durable scientific results. Do not cite them as new
LLM evidence or edit the existing manuscript on their basis.
