# V6 bottlenecks and a smaller scientific exploration — 2026-10-18

Status: read-only source/data audit and a proposal for PI review. No GPU was
started, no scientific outcomes were inspected, and no frozen protocol, sample
size, gate, backend admission rule or execution controller was changed.

## What the long estimate means

The completed Qwen timing and its closure are documented in
`v6_qwen_timing_closure_20261018.md`. The 68.93-hour projection includes model
work, synchronous state management, raw archive writes and within-run Replay;
it is not a measurement of GPU arithmetic alone. It comprises 55.82 hours for
N240 formal work, 1.69 hours for baseline N60, and 11.43 hours for the three
N40 calibration cohorts plus N80 validation, assuming all gates pass.

Adding every backup after computation gives 91.11 hours. Adding a separate 50%
planning sensitivity gives 136.66 hours. Neither is a compulsory production
schedule or a confidence bound. They do not describe two models. Only two
new engineering episodes per fixture support these extrapolations; gain-1
neutral timing proxies the other gains and validation. The full fixture has
50% TEXT versus 25% planned, deliberately overcovered rather than adjusted
using an unmeasured new-backend TEXT cost.

## Workload is much larger than six conversations

Per episode the existing full runner performs these paired work periods:

| Work | Paired 64-token periods |
|---|---:|
| Five continuing policies, six rounds each | 30 |
| FRESH's independent outgoing preparation | 6 |
| Early and late pulse branches: four arms, two event versions, two rounds | 32 |
| Two goal checkpoints: three arms, two versions | 12 |
| Total, before preparation, TEXT and readout ingestion | 80 |

That is 10,240 generated work tokens across the two participants per base
episode, plus preparation and hundreds of isolated questions. The current
two-episode/four-side batch still makes 5,120 sequential work-step calls.
Within an interacting pair, the next token can depend on the partner's last
committed state. Parallelizing those causally dependent ticks changes the
experiment; independent episodes and independent discarded branches can be
scheduled together if isolation and numerical acceptance are retained.

The full two-episode case measured 1,674.476 seconds of model work and
2,724.673 seconds including exhaustive archive restoration. Compilation was
about 6.29 seconds cumulatively; two model load/hash operations totaled about
40.25 seconds. Loading and compilation do not explain the multi-day projection.

## Backup can overlap computation

Serial means: compute closed cohort A; stop computing while A is copied;
then compute B. A final single copy after all computation has the same additive
cost. A pipeline instead computes B while a separate worker copies the sealed,
immutable files of A. It never copies a growing archive as if it were complete.

Observed final copy plus whole-tar hash: 3.644 GB in 1,136.678 seconds, or
3.206 MB/s effective throughput, not isolated network bandwidth. Projected
raw output generation averages about 1.031 MB/s. A full cohort produces
2.132 GB: roughly 665 seconds to copy at that rate versus 1,674 seconds of
model work. This makes overlap plausible, but concurrent contention has not
been measured.

The ideal planning envelope is max(68.93, 22.17), not 68.93 + 22.17 hours:
about 69 hours plus final tail and other overhead, potentially hiding about
22 hours (24% of the serialized total). This is not an achieved speedup.
The observed one-cohort transfer tail is roughly eleven minutes, with
additional tails at stage boundaries. Slow or disconnected local backup,
CPU/disk contention, rehashing and bounded backlog can reduce the benefit.

Implementation requirements for the proposed pipeline:

1. Publish immutable shards and a closed manifest only after successful writes.
2. Copy and hash each newly sealed shard in a bounded background queue; retry
   failed transfers without copying every already verified byte again.
3. Retain all remote originals; stop admission of new cohorts on excessive
   unverified backlog, missing SD volume or inadequate remaining disk space.
4. At stage end close the inventory, finish the delta and bind the receipt;
   confirm actual provider stop. Then independently rehash every final local
   file, preserving remote disk until this check succeeds.
5. Measure producer time with and without the copier, maximum backlog, copy
   throughput and final tail. Compression cannot be counted as a second wall
   time gain once all transfer is already hidden behind computation.

The existing execution addendum already permits this architecture. The closed
engineering attempt deliberately used a simpler final serial copy. Historical
control failures during periodic copies mean overlap must be tested for lease
refresh and failure handling, not reintroduced by an unreviewed background
shell command. No live or historical controller was edited here.

## Repeated checks: keep the invariant, remove redundant placement

| Item | Assessment |
|---|---|
| Exhaustively restore every archive to GPU after every engineering cohort | Measured 17.50 minutes per full two-episode cohort. A serializer/backend acceptance diagnostic, not automatically required for every production cohort. Production still needs every archive's integrity and the prescribed Replay checks. |
| Repeat the complete short engineering fixture | A deliberate determinism test. Do not reproduce the entire engineering qualification for every formal episode. |
| Final local independent rehash | Necessary, but run after verified GPU stop; already intended by the addendum. Do not charge it twice as GPU idle time. |
| Complete source and configuration verification | Bind at launch/restore and exact resume; retain required ongoing tamper/deadline/lease checks. The small repeated configuration reads are not evidence of an hours-long bottleneck. |
| Unchanged-event scientific Replay and parent isolation | Essential. Do not eliminate them merely because they are called checks. |
| Same LIVE continuation repeated as a causal branch | Potential exact reuse, only after proving identical full inputs, states, gains, positions, token clocks and complete output keys. It is not sufficient that two prompts look similar. |

The optional exhaustive restoration cost would scale to 35.01 hours, but it
was **already excluded** from both 68.93 and 91.11. Removing it cannot be
advertised as another 35-hour saving from those numbers. The two scheduled
q1/L pulse continuations are candidates for reusing four already computed
natural work periods, at most 4/80 of the work-period count before other costs;
this is not a measured 5% wall-time gain. Reuse must not replace independent
Replay validation with a tautological reference to the same computed object.

## Remaining compute hot spots and what is actually known

The new full timing has no disjoint per-operation CPU/GPU profile. It cannot
justify a precise split of 68.93 hours into attention, copies, hashes and I/O.

The older native full episode recorded 352 probes with 836.91 seconds of
inclusive host time, 11,200 steps with 628.96 seconds, and 1,548 state digests
with 199.15 seconds. These are nested, asynchronously charged host timings;
do not add them, call them GPU percentages or apply the old shares to the new
implementation. They identify question ingestion and state auditing as serious
candidates alongside token generation.

Current source findings, in priority order:

1. `PackedBackend.consume_many` recreates zero-filled 4,096-position K/V buffers
   for every layer at every call, copies the existing histories, and rebuilds
   output caches using concatenation and cloning. For Qwen's four physical
   lanes, the own-prefix buffers alone total 2.25 GiB per batched call; 5,120
   work calls imply 11.25 TiB of requested zero initialization before other
   traffic. This is allocation arithmetic, not measured bandwidth or time.
   Persistent privately owned buffers, separate valid lengths and copy-on-write
   branch storage could remove repeated construction. Audit aliasing, stale
   padding, masks, donor positions, failed publication and numerical behavior.
2. `step_many` hashes every exported token's per-layer payload through CPU
   transfers; `probe_many` and `commit_many` also seal/check whole states.
   Preserve byte identities, parent immutability and fail-closed publication.
   Owned immutable block identities and bounded asynchronous archival are
   candidates; simply skipping hashes or trusting an unsafe tensor view is not.
3. Nonfeeding question branches and independent episodes offer batching work.
   The current cohort holds only two episodes. Larger cohorts or batching
   isolated probes need measured peak memory, exact lane isolation, original
   full-vocabulary scoring, and prospective numerical acceptance. They are not
   guaranteed linear speedups. Within-pair dependent generation remains serial.
4. The already implemented lossless block archive stored one historical fixture
   in 54.11% of its original bytes. Verify it on representative Qwen shards and
   retain every original-file hash. This saves storage/transfer; it does not
   imply 46% faster computation or combine multiplicatively with hidden I/O.

Next instrumentation should time explicit work/probe/commit/archive regions,
record CPU launch and synchronization, GPU kernel and copy traces, peak memory
and backup backlog on a bounded representative portion. Do not insert a CUDA
synchronization into every operation and then treat the distorted run as normal
throughput. Instrumentation and core-pilot work can share a session; a separate
multi-hour complete timing campaign should not be the default again.

Only the approximately 22-hour overlap opportunity is currently quantitatively
supported by a measured producer/consumer scenario. A further 15–25% reduction
in model-work time would give roughly 52–59 hours before tail/overheads, but this
is an optimization target, not a forecast. There is no basis yet for promising
another 2–4x speedup on the unchanged full design.

## The more consequential change: scientific exploration before confirmation

The original package already stages engineering, baseline, gain calibration,
independent validation and formal collection. However, its selectors deliberately
cannot see core interaction effects. Thus those stages can establish capability
and transfer without giving the PI an early scientific picture of reciprocity.
Treating that as a reason never to inspect a small exploratory experiment was
unhelpful. Engineering success, a scientific cue and a confirmatory conclusion
are three different deliverables.

Recommended **new, separate proposal**, not adopted by this review:

0. Before renting or collecting again, use the two already completed full-clock
   engineering episodes for a clearly labeled qualitative case walkthrough.
   Show both episodes and all selected contrasts, not only interesting moments.
   They can reveal an obvious task/interface failure or illustrate the actual
   loop, but their engineering purpose, fixed gain and tiny sample cannot supply
   population effects, gate passage or a gain-selection result. This review did
   not inspect those outcomes; any later outcome-informed design work must be
   recorded as exploration rather than disguised as blind selection.
1. Start with Qwen only and material disjoint from every existing engineering,
   baseline/calibration/validation and formal allocation. Keep the six-round
   task, native private inputs, 64-token clock, 16-token generated window,
   two active participants and early/late role reversal.
2. A small neutral preparation option is baseline N8 and N8 at each of the
   existing three gains. Inspect comprehension, fact access, capability and
   formatting only. This is exploratory feasibility evidence, not passage of
   the frozen N60/N40/N80 confidence-bound gates. Before collection, specify
   the provisional gain rule and what happens if no setting is usable; freeze
   the selected gain before reading core outcomes. Do not optimize it using
   response-chain or goal effects. Exact pilot admission/ranking rules remain
   a PI-reviewed preparation item; no selection is implemented here.
3. Use N12 new core episodes, all retained, with LIVE/OFF/FRESH trajectories and
   the complete L/Fcut/Rcut/Replay pulse comparison at rounds 2 and 5. This is
   56 paired work periods and 136 core readouts per episode before extra neutral
   diagnostics, versus 80 periods and 328 non-TEXT readouts in the full design.
   Preserve zero-event Replay and branch-isolation checks. Defer the two full
   one-way trajectories, extensive goal-substitution probes, TEXT and Llama.
   This changes the scope of a separately labeled pilot, not the frozen formal
   design. It cannot establish goal separation or cross-model replication.
4. Examine all episode trajectories, actual action/device changes, direction-
   specific propagation and Q_chain, early versus late behavior, absolute task
   accuracy, invalid outputs and LIVE/FRESH differences. Show failures and
   uncertainty. A small positive effect is a cue, not significance or a reliable
   power estimate; a small null is not proof of no effect. FRESH can support
   cross-round interaction, and LIVE need not beat it for feedback to exist.
5. Stop after the pilot and present an interpretable report before any scale-up.
   The PI can change the task or hypotheses, continue, or end the program based
   on the exploratory evidence. Record all attempted versions, including null
   results. Any revised confirmatory question/conditions/N/analysis belong in a
   prospective new version; use independent data for its final tests. Do not
   fold these N12 into the frozen N240 or retrospectively describe exploration
   as preregistered confirmation.

The current optimized Qwen backend has engineering evidence, not scientific
adoption. A pilot package must explicitly fix its backend/numerical contract
and technical acceptance. Small pilot results cannot establish cross-backend
equivalence or excuse Llama's failed comparison. Using the existing reference
backend instead is possible but has a different, slower timing. No automatic
promotion or GPU execution is authorized by this proposal.

For scale only: the optimized full-suite proxy for N12 is 2.79 hours of model
work. The suggested N8 baseline plus three N8 neutral cohorts adds 1.60 hours,
using gain-1 timing as the proxy. Thus 4.39 hours of work is a useful deliberately
overcovered scope estimate for this smaller subset, not a guaranteed upper
bound. Approximately 5–6 elapsed hours is a conditional planning allowance if
the candidate is admitted, no new failure occurs, and backup overlaps normally;
startup, acceptance and transfer remain to be measured for the actual pilot.
For comparison, the historical reference full-suite/neutral proxies give about
9.64 hours of model work for the same N12/N8/three-N8 counts, before overhead.
The actual subset may be faster, but no per-condition timing establishes how
much. These are new-execution estimates, not permission, a budget admission or
a promise; no Llama prediction is made.

This approach pursues earlier scientific information without discarding
rigor. The separation of exploratory analysis and independent confirmation,
including pilot work and transparent prospective amendments, follows the
[Center for Open Science's preregistration guidance](https://www.cos.io/initiatives/prereg).

## Evidence and validation

Source audit: `src/mb/v6_batch.py`, `v6_batch_native.py`, `v6_native.py`,
`v6_state_guard.py`, `v6_efficiency_trial.py`, `v6_performance.py`; protocol
sections 4–11 and execution-addendum backup requirements. The current private
worker's live-check path was inspected read-only: it verifies local config and
lease, not a provider network round trip for each token.

Reproducible arithmetic is retained in
`/private/tmp/mb-v6-bottleneck-review-20261018/arithmetic.json`, bound to the
previous reviewed projection by SHA256. Historical profiler values are from
the saved October 14 native `full_with_text/summary.json`; they are not new
GPU measurements. No result/weight/credential/connection file is added to git.
Offline validation: 1,234 passed, ten skipped, one deselected.
