# V6 offline performance preparation

Prepared 2026-10-14 at the PI's request to explain the experiment and optimize
performance before any further GPU start. This is an engineering candidate, not
a scientific amendment, production source freeze, cost pass or spending request.

## What the experiment measures

Two persistent instances of the same pinned checkpoint control separate private
devices for six rounds. Each action depends on the participant's own assigned
goal and its partner's beacon. An actual action changes the acting participant's
next beacon. The partner must respond to that new state, potentially changing the
state that the first participant subsequently observes. Repeat independently
with Qwen and Llama; do not connect the two different model families.

Full trajectories compare LIVE, both one-way directions, OFF and FRESH. FRESH
exchanges current information once per round and can itself sustain cross-round
interaction. A balanced subset adds ordinary text communication. LIVE does not
have to beat FRESH, and text is a descriptive comparator with different costs and
source cues.

Early and late branches compare an unchanged versus flipped private beacon,
with full coupling, forward cut, return cut and a matched unchanged return tape.
The question is whether the appropriate response travels to the partner and then
back, beyond arbitrary switching. Separate fixed-world goal probes distinguish
lawful adaptation to a new world from following the wrong assigned goal. These
are tests of functional feedback and goal separation, not consciousness, general
planning, or the impossibility of describing interaction as dynamic steering.

## Verified workload, not GPU timing from a simulator

Run `.venv/bin/python scripts/v6_performance_audit.py` locally. This uses the real
scheduler with a synthetic backend and a shortened fixture clock; its outputs
are structural counts, never model outcomes or a model speed estimate.

| Work in one base episode | Paired work periods |
|---|---:|
| Five natural policies, six rounds each | 30 |
| Extra FRESH sending shadows | 6 |
| Two pulse checkpoints, four arms, two event versions, two rounds | 32 |
| Two goal checkpoints, three arms, two versions, one round | 12 |
| Total | 80 |

At the adopted clock this is 80 × 2 × 64 = **10,240 generated work tokens**,
plus160 preparation tokens, prompt ingestion, answer commits and closure tokens.
There are328 readouts:120 natural,64 pulse and144 goal. A text-reference episode
adds768 message-generation tokens,32 preparation tokens and24 readouts. These
branches and readouts are paired measurements within one statistical episode,
not separate independent samples. Each base episode also archives four pair
checkpoints and twelve replay tapes.

The frozen native backend processes a linked multi-token question one token at
a time. Thus328 readouts do not mean328 total decoder passes. It also repeatedly
checks full state hashes, clones branches and transfers archive tensors. Static
inspection identifies possible costs; it does not establish their fraction of
the measured26-minute episode time.

Formal collection remains240 episodes per model, with text on60 of them.
Separate neutral cohorts remain baseline60, three gains at40 each, validation80.
Neutral cohorts have different workloads: do not simply multiply the full smoke
episode time by every neutral sample and call that a measured ETA.

## Implemented candidate

`src/mb/v6_performance.py` leaves the frozen native backend, scheduler, attention
arithmetic, token counts, selectors, outcomes and historical files untouched.
Nothing imports this candidate into production execution automatically.

1. `PerformanceBackend._foreign` reuses at most two already concatenated foreign
   windows. Every call retains the reference source validation. Cache hits also
   validate the cached tensor stamps. Exports are strongly retained and ordered;
   cache entries cannot be reused under recycled object identities. Gains are
   applied by unchanged attention, and zero gain still validates source inputs.
2. Archive transfer groups same-dtype/device small tensors in bounded4MiB
   buffers. Oversized tensors retain the reference copying path. CPU results
   never alias source storage. `dump_export` validates and archives the same CPU
   bytes, avoiding a second GPU read solely to hash them. Logical archive schema,
   tensor values and SHA256 checksums remain the reference contract. Storage
   layout and serialized file bytes can differ; never overwrite old archives or
   reuse their file manifests for the candidate.
3. `profile_backend` counts calls/failures and inclusive host wall time without
   recording questions, answers or model effects. Nested times overlap and GPU
   work may be asynchronous. Do not add these times to estimate total runtime;
   compare complete synchronized episode wall time separately.

This is an overhead optimization. It does not remove the80 work periods or the
serial linked-question forwards. No speed multiplier or affordable full run is
claimed. Larger changes such as batched linked prefills require a separate
implementation and numerical audit; they are not silently enabled here.

## Verification and remaining execution boundary

The final complete offline suite passed774 tests, with seven skipped and one
GPU test deselected. Sixteen focused offline checks cover workload counts, bounded copying, mixed
types/devices, ownership, exact logical archive checksums, corruption detection,
window eviction, source/cached mutation rejection, gain changes and profiler
restoration. Independent review is in
`../reviews/v6_performance_independent_20261014.md`.

`tests/test_v6_performance_gpu.py` prepares exact CUDA comparisons for both model
families using tiny random models: generated tokens, state digests, probabilities,
legal logits, answers, commits, archives and weights-only restore. Separate copy
tests cover BF16, dtype alignment, noncontiguous/oversized/empty tensors and CPU
source ownership. These CUDA tests have **not** run. Tiny-model tests alone would
not certify the pinned scientific weights or predict their speed.

Before any paid continuation:

1. Review and seal a new prospective engineering source identity, preserving old
   freezes, runs, failed attempts and the original cumulative financial anchor.
   New `v6_*.py` files also affect the source-manifest glob; an old exact-resume
   identity must never be reused with this candidate.
2. Verify actual stopped identity and current cumulative costs, original caps,
   deadlines, reserves, fresh guards and enough authorized acceptance allowance.
   This local work grants no new paid time or stopped-time credit.
3. Use a protected, bounded engineering comparison on identical inputs. Run
   native exact-equivalence checks before accepting any speed result. Stop on
   changed actions/readouts/state checksums; do not adopt a loose tolerance
   retrospectively or use scientific effect sizes to justify the candidate.
4. Compare complete reference/candidate timing and backup sizes/throughput on
   the pinned models before a new full-workload forecast. If still unaffordable,
   remain stopped and present a concrete PI choice. Do not reduce N, controls,
   the confidence-bound gates or the conservative cost rule on the PI's behalf.

Current preserved evidence: Qwen smoke times1545.4461/1580.5817 seconds. The
existing1.5×maximum rule projects158.06 hours / USD252.89 at the1.60 hourly cap
for **Qwen formal compute alone**. This excludes other phases and Llama; it is
neither an actual bill nor a complete two-model ETA. No further GPU run was
started for this optimization. The terminal controllers and paused automation
remain inactive.
