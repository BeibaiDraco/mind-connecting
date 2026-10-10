# Fixed Llama continuation: prepared locally, awaiting funding and start

Prepared 2026-10-10. Read STATUS.md for later changes. The PI requested full
local preparation before topping up and authorizing a restart. No instance is
started by preparation, a source freeze, or an inert budget proposal.

## Scientific package

Use `docs/protocol/PROTOCOL_V5_CONTINUATION.md` as the proposed continuation
contract. Run provenance first, STATIC second, each fixed N600. Keep the original
v5 gate failures and report the amended Llama results separately. No new
calibration, matching search, scientific N80, model, prompt or effect-based
continuation decision is allowed. The exact exceptions concern the named
5.625-point provenance CAP loss and 6.25/5.9375-point STATIC-prerequisite losses.
Every other historical validity requirement must still reproduce.

Prepared configurations and complete prerequisite inventories are in
`configs/v5_continuation/`. They refer to immutable original execution-host
source paths. Local auditing explicitly maps those paths to the SD backup;
neither the old files nor their recorded paths are rewritten. Fresh formal
source identity is required; no historical run is resumed with changed code.

The CF metadata correction changes only validation to follow the frozen
producer's donor-swapped episode. The question/physical-answer collection code
is unchanged. Its regression tests reject corrupted label meanings and wrong
physical candidates. The old N80 remains a failed original-v5 gate.

## Budget and expected duration

Measured timing predicts about 11.5 hours for provenance and 6.9 hours for STATIC,
including half an hour of overhead per study. Conservative planning reserves
17.775 and 13.90625 hours respectively; these are allowances, not guaranteed
upper bounds. Fresh native/smoke/resume acceptance reserves another 25 minutes
per restart. Combined nominal time is about 19--20 hours; conservative room is
about 33 hours. A new hardware/rate observation requires a revised forecast.

The retained instance was independently queried on 2026-10-10: actually stopped,
USD 1.12/hour including disk. Budget protection uses USD 1.40/hour. The remaining
work therefore needs approximately USD 22 at normal speed, or USD 46 with the
conservative allowances, before any unexpected recovery. Recommend at least
USD 60 available account balance. This is an account-balance recommendation,
not a claim about the current balance or the amount already billed.

A proposed USD 100 **cumulative v5 ceiling** is prepared, not approved. Preserve
the original v5 accounting anchor, prior-spend field, rate and reserves. Do not
call this a fresh USD 100 allowance. Before starting, obtain the PI's explicit
confirmation of the prepared two-study package and numerical cumulative cap;
record it in a new private approval receipt. Recompute room at that time. The
conservative accounting model includes stopped time and is not an invoice.
An expired proposal or insufficient remaining room requires a fresh decision,
not an implicit anchor reset or unlimited spending.

## Local artifacts and source freeze

The preparer and freeze tools do not load model weights or start a provider:

```bash
.venv/bin/python scripts/prepare_v5_continuation.py --results-root "$RESULTS_ROOT"
.venv/bin/pytest -m 'not gpu' -q
```

Use the preparer's actual CLI help if regenerating. Generated files are
write-once; a changed regeneration is an error. Commit the inputs before
creating the separate continuation algorithm freeze, then create the three
stage freezes (provenance, STATIC and original Llama smoke) with
`scripts/freeze_v5_continuation.py`. Verify every manifest using explicit local
`--results-root` for the SD mirror. Historical v5 manifests remain untouched.

Deploy a separate checkout with its Git history, because historical source
verification reads the original `ff2387d` blobs. Do not overwrite the old
`/workspace/mind-connecting-v5` checkout. Install the new checkout into its
isolated environment and verify `mb.__file__`. Reuse pinned cached model assets;
network/offline settings are unchanged. Verify every deployed file and freeze
before using the new code. The data root remains `/workspace/mb-data`.

## Private plans and protections

Private preparation lives outside Git in the execution handoff's
`continuation-preparation` directory. It contains an inert cumulative-budget
proposal, an approval template, per-study controller plans and unapproved stage
budgets, reviewed shutdown guards and their offline tests. No credentials or
connection records belong in this runbook or the repository.

The new private guard helper requires a receipt naming both fixed studies and
the exact cap. Its original budget/target binding is hard-pinned. It supports a
local full-budget guard, a local commissioning guard limited to 600 seconds,
and a remote full-budget guard. Old guards have been retired and must not be
assumed active. Reuse only the pinned provider/self-stop/backup transport
helpers, not the old full-budget helper that hard-codes USD 60.

Before **each** restore:

1. Verify the same bound instance is actually stopped and has no unresolved
   prior worker; check its quoted rate against the guard rate and forecast.
2. Arm fresh local cumulative and commissioning guards before requesting start.
   Confirm exact PID, argv, process-start identity, budget and target hashes.
3. Request a bounded same-instance restore. If resources are unavailable,
   cancel the pending request, verify stop and retain the failure. Do not rent a
   replacement automatically. Keep credentials/connection output private.
4. After connection, deploy/verify the prepared checkout and private plans,
   establish the fresh remote full-budget guard. Keep the short commissioning
   guard active until the observer and detached controller below are healthy.
5. Start the existing reviewed SD backup observer for this study's new control
   directory. Confirm the SD is mounted and the observer is alive. A missing
   backup ACK fails closed; it never silently writes elsewhere.
6. Confirm no competing GPU process and no unresolved persisted controller
   intent. Launch the **outer** controller detached:

   ```bash
   .venv/bin/python scripts/run_v5_continuation.py execute --plan "$PRIVATE_PLAN" --detach
   ```

   The controller verifies the approval, fixed source freezes, full remaining
   package reservation and remote guard proof at phase boundaries. Its global
   lease and persistent intent prevent a second continuation from starting.
   A returned PID alone is insufficient; inspect its phase and child receipts.
   Once the observer and controller/first-child identities are verified live,
   acknowledge the commissioning guard with fresh local and remote full-guard
   proofs. Any deployment, observer or launch failure first preserves evidence
   and verifies stop; do not leave an idle instance until the full-budget limit.

Each study performs fresh eight-test native acceptance, four-episode smoke and
exact no-op resume under the new source, then its prepared formal N600. No
research baseline/selection/validity sample is recollected. These short checks
necessarily happen after a GPU is available; local preparation cannot establish
their success in advance. Failure preserves the evidence and requests stop.

Formal completion requires complete, unique finite records, the source-backed
analysis and hash-verified backup. Effect sign, significance, CAP drift and
formal access-match drift never determine whether a completed study is kept.
Report those diagnostics and their limitations. Postprocessing failures also
attempt raw-data backup before shutdown.

The remote process may be terminated by its own successful provider stop before
it can write a final acknowledgement. The independent local observer must
confirm actual stopped state, rehash the durable backup, and preserve control
receipts. Before STATIC, seal a private `provenance_stopped_backup.json` next to
the two study directories, containing `provider_stopped_verified`,
`target_sha256`, `prior_control_dir`, `checked_epoch`, and SHA256 values for the
provenance `last_stage.json`, `backup_ack.json` and `backup_request.json`.
The receipt is created only from the real verified stop and backup; the STATIC
controller refuses its absence or mismatch. Archive the active intent before
closing it after exact worker/stop reconciliation. Fresh guards are required
for the second restore; retain the same cumulative budget and original anchor.

## Completion and user notification

Verify first formal writes and compute an updated ETA from completed batches.
Use sparse checks near meaningful milestones; do not continually consume model
tokens monitoring a healthy job. Announce a new formal start, failure, required
PI action or final completion. Preserve the original Qwen access-limited word
interpretation and all historical failures. Once both studies are backed up and
actual provider stop is confirmed, pause the monitor and begin final reporting.
