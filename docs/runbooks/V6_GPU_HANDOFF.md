# V6 native execution handoff

Prepared 2026-10-12. Local implementation and review are not hardware acceptance.
No V6 rental, model run or scientific freeze has occurred. The PI has delegated
renting a new instance and starting after preparation. The newly explicit
admission contract and new numerical budget still require prospective ratification.
Do not reuse a V5 instance binding, financial anchor, exception or controller.

## Scientific package to ratify

Read `docs/protocol/PROTOCOL_V6_CONTINUOUS_DRAFT.md` together with
`docs/protocol/V6_EXECUTION_ADDENDUM_DRAFT.md` and
`configs/v6/admission_proposal.json`. The latter two resolve the neutral-probe,
aggregation and calibration-rule ambiguities from the earlier implementation.
Neither document retroactively changes a previous result.

For each of the two existing pinned checkpoints, use separate same-model pairs:

| Stage | Episodes | Purpose |
|---|---:|---|
| Actual checkpoint acceptance | 1 | Native math, caches, recovery and persisted replay |
| Main smoke | 2 | All branches, text reference, archives, timing and exact no-op resume |
| Baseline | 60 | Supplied-fact task/assignment competence and format |
| Calibration | 40 per gain | Three disjoint cohorts at 0.25, 0.5 and 1.0 |
| Independent validation | 80 | Same neutral predicate at the smallest passing gain |
| Formal | 240 | Five natural trajectories, early/late interventions and goal probes |

Formal text reference uses a material-only balanced subset of 60. Formal output
is 80,160 records per model, not 80,160 independent observations. The statistical
unit remains the base episode. Keep both models' estimates separate, the 22/4
families, all original errors, and every unavailable contrast. No effect or
significance statistic may influence admission, candidate choice or continuation.
All three calibration cohorts must be complete. Validation failure ends the
model path; do not substitute a runner-up or new samples.

## Prepare and inspect immutable inputs

Use the existing offline environment. Do not install torch or run a model locally.

```sh
.venv/bin/python scripts/prepare_v6_launch.py package --output /private/tmp/v6-reviewed-package
```

The output directory must not exist. This generates all 16 stage material files,
checks both real tokenizer manifests, rejects repeated task-core content across
all stages/models, and fixes both text subsets. It creates no authorization.
The package includes the scientific source manifest, exact material catalog,
runtime clocks and proposed spending/storage boundaries. Regenerate a new
package after a source change; never overwrite an already approved package.

The generated catalog initially contains absolute local paths. Before recording
the authority receipt, prepare the deployment-path copy with a documented
path-only mapping, preserving every material byte/hash, source hash, count,
runtime setting and text subset. Bind the authority to that final catalog.
Native evidence capture walks all nested pins, so every catalog path must exist
on the executing host. Never rewrite catalog paths after authorization is pinned.

After explicit ratification, record a separate private `v6-approval-1` receipt
that binds the prepared package, source and admission contract hashes, permitted
stages/models, and exact monetary ceilings. Include the actual PI authorization
evidence. Do not turn a proposal's status into an approval or create a receipt
from anticipated consent. For formal freezing, record the approved document and
code/input hashes before collection, preserving all draft/history files.

`prepare_v6_launch.py plan` creates a non-authorizing, fixed per-stage plan.
Prerequisites are original hashed completion/acceptance/resume files. Conditional
gain must come from the independently recomputed neutral selection; manually
supplying it is not sufficient admission. Approved material hashes/counts/text
subsets/clocks cannot be changed by a new plan.

## Financial and storage commissioning

The current recommendation is a new USD100 total ceiling, initial USD12,
USD1.60/hour including disk, five-minute shutdown reserve, one A100 80 GB GPU,
at least 650 GiB remote disk and a 600 GiB reservation on the mounted SD volume.
These are proposed, not inherited V5 limits. Recheck current quotes, account
credit, actual allocated disk and transfer tariffs before any create request.
Never alter automatic recharge. Prefer both transfer tariffs at most USD10/TB.

Tokenizer-only formal raw payload estimates are about 229.39 GiB Qwen and
208.83 GiB Llama; these omit overhead and must be replaced by native smoke
measurements. Keep all four pair checkpoints and twelve tapes per base episode.
No archive thinning, quantization or Mac-disk fallback is allowed.

Use a fresh private execution root and a uniquely tagged rental intent. Before
one create request, arm an independent local creation/setup deadline guard. An
ambiguous create response is not permission to create again: resolve the unique
intent through inventory, including delayed creation. Bind the single returned
instance exactly, verify the quoted class/rate/allocation, then arm fresh local
and instance-local budget guards. Their stop paths must use that exact binding.
Record the financial start before paid provisioning; charge installation, idle
time and all transfers conservatively. Never reset the anchor after a restart.

Deploy only the pinned source and materials. Set up the pinned environment,
download only the two authorized checkpoint revisions, and validate actual
assets. Host identity, credentials, connection details and provider receipts
belong only in the private execution root, never the repository or chat output.

## Worker and external supervisor

`scripts/v6_execute.py` is the native single-stage worker. It loads a checkpoint
only after fresh `v6_launch.validate_execution` admission. The admission names
the exact plan, approval, budget anchor, instance, live dual guards, verified
backup and free storage. All post-smoke stages additionally need a measured
whole-remaining-work forecast fitting the original total cap and hard deadline.
An explicit historical-time audit cannot launch new work.

The external supervisor is `scripts/supervise_v6.py` with the separately pinned
private provider/SSH adapter. It must run on the control host; the GPU worker
cannot prove its own instance is stopped. Before first use, commission and
independently inspect the private adapter against the supervisor's exact request
and receipt contract. A generic tested supervisor alone is insufficient to claim
a live deployment is protected. This host-bound adapter and real observations
remain deployment acceptance items, not evidence that GPU execution occurred.

```sh
.venv/bin/python scripts/supervise_v6.py --spec /private/path/supervision.json --control-dir /private/path/new-stage-control
```

An explicitly justified partial-run continuation adds `--resume`; a reused
launch intent never silently starts another child. The detached remote guard
must self-stop on worker exit or expired supervisor lease, in addition to the
immutable financial deadline, so a control-host outage does not leave idle GPU
billing until the full cap.

The adapter must refresh matching proofs, run remote validate-only admission,
launch the worker detached with one exclusive intent, return only structural
progress, synchronize and rehash backups, and request/verify actual provider
stop. No effect fields belong in its observations. On an ambiguous launch result,
preserve the exact intent and fail closed through termination/backup/actual stop;
never start a second child. Local logs or backup errors
must not suppress the stop path. A successful stop request is not actual stop.

Use short bounded provider/SSH calls, monotonic as well as wall deadlines, exact
process start identity, and one stage per supervised invocation. Stage transition
is separate: a saved `passed` flag is insufficient; the scientific worker
recomputes its complete pinned predecessor chain from raw records. Fresh proofs
must be published while work is in progress, without changing its immutable
financial/source/material identity. Preserve original admitted proof bytes so
expired observations remain auditable without becoming new execution permission.

## Hardware acceptance and automatic continuation

Acceptance must pass on each actual pinned checkpoint: independent same-shape
native logits/caches, zero gain with nonempty foreign state, independent positive
joint attention, evaluation order, original pair/tape serialization and two-round
zero-pulse replay, finite recovery and text control policy. Additional small
random-model GPU tests do not replace it. Preserve failed attempts and diagnostics.

Run the two-episode main smoke with its fixed text subset, then call the
byte-identical no-op resume audit. Rehash the source, materials, all smoke records
and archives onto the mounted SD card. Use measured native elapsed time, full
cache payloads, hashing and backup throughput to forecast all remaining work,
including slower later-round contexts and a conservative overhead margin.
If initial allowance or total forecast cannot contain the plan, stop and report
the measured constraint; do not reduce N, drop controls or weaken gates.

Only after real technical acceptance, exact resume, verified backup, sufficient
storage/credit, protected deadlines and an affordable full forecast may the
ratified neutral sequence continue. Report a defensible ETA once formal data
are actually writing. Sparse completion-near checks are sufficient; the external
controller and independent guards should not depend on an active chat turn.

## Completion and failure

Native output is append-only and identity-bound. There is at most one exact
episode retry; retained successes must match. Incomplete/altered/orphan archives
fail closed. Completed no-op resume rehashes all records and artifacts before
model loading and must leave every run byte unchanged.

For every terminal stage, preserve source, evidence, failed attempts, records,
archive inventory and checksums. Copy the closed final inventory under the paid
deadline, confirm actual provider exited/stopped state, then independently rehash
the complete SD copy. Full local rehashing of hundreds of GiB must not keep an
idle GPU running. Periodic copies may reuse prior immutable-file verification
and verify additions; they are not a substitute for the final independent full
rehash. Report backup failure separately
from computational completion and from actual stop. Never report a scientific
result from synthetic acceptance fixtures. Model-specific gate failure does not
authorize a relaxed threshold. Final interpretation begins only after collection
and provenance verification, and cannot retroactively justify continuation.
