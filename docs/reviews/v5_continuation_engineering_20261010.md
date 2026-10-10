# V5 continuation engineering review

Date: 2026-10-10. Reviewer: Codex engineering review agent.

## Verdict and scope

The reviewed local implementation is ready for the source commit and separate
continuation freezes. No unresolved blocking implementation issue was found in
the final versions below. This is not approval to restart an instance, a claim
that the new source has passed GPU acceptance, or a guarantee about runtime or
provider availability.

The review independently covered the continuation controller, stage-launcher
changes, source/evidence preparation and freeze interfaces, and the operational
runbook. The reviewer authored the narrow CF checker repair and private guard
helper; another agent independently reviewed both. No model, GPU, provider,
network or operational guard action was performed by this reviewer.

## Findings and resolutions

- The CF checker now reconstructs A's question metadata from the donor-swapped
  episode, matching the unchanged Runner. Original physical `cf_r0`/`cf_r1`
  candidates remain anchored to the original episode. Text, options, meanings,
  configuration hashes and identity checks are still enforced. Tests exercise
  the real `_donors`, `_pending_questions` and `_base_record` producer methods,
  accept correct CF records, and reject substituted meanings and corrupted
  options, text hashes and physical candidates. Token serialization alone is
  stubbed in these metadata tests; they are not GPU tests.
- Read-only reconstruction of the preserved STATIC N80 returned 2,560 complete,
  unique usable records across 80 episodes, with no invalid records or torn
  tails. The unchanged scientific gate still fails, despite passing the mean
  access match. No historical result, protocol, freeze or verdict was rewritten.
  Independent calls to the continuation history audit also reproduced both
  named chains and their exact capability exceptions, covering inventories of
  290 provenance files and 984 STATIC files.
- Historical identities are checked against the original Git tree and assets.
  New collection uses a new source identity, new run tags and separate freezes;
  it does not resume an old run with changed code. The historical-code migration
  check permits only the reviewed STATIC record-checker change among existing
  collection modules. Calibration bytes and all consumed historical sources
  remain pinned.
- Execution requires a private approval receipt for both fixed studies and the
  exact cumulative cap. Original accounting anchor, rate, prior spend and
  reserves are retained. The first study reserves the remaining STATIC work at
  every phase boundary. The private guard helper additionally pins the original
  full-budget artifact and refuses to arm an inert proposal. Its finite
  commissioning guard, full local guard and independent remote guard use fresh
  control directories and exact process/plan proofs; no old USD 60 guard is
  assumed live or silently repurposed.
- Native acceptance, the four-episode smoke and its no-op resume are required
  under the new source before formal collection. The new freeze verifier and
  stage-launcher dispatch agree on the algorithm/stage interfaces. Formal
  completion depends on source-backed ledger integrity and successful analysis,
  not effect direction, significance, capability drift or formal match drift.
- The outer controller now supports explicit detached execution only after
  Linux, funding and guard checks. A shared lease, persisted active intent and
  per-control intent block duplicate or unresolved launches. Review found a
  check-then-create race at `controller.log`: the losing exclusive creation now
  raises `StageBusy`, rather than requesting shutdown of the winning controller.
  The author added a regression for this exact case.
- STATIC now requires a prior provenance completion/backup/stop receipt tied to
  the original target and exact hashes of `last_stage.json`, the backup request
  and its matching ACK. The controller checks the formal stage and receipt
  chronology. This enforces the declared study order without using provenance
  effect values to decide whether STATIC proceeds.
- Postprocessing failure attempts raw-data backup before the shutdown path;
  backup inventory accepts preserved failed collections. Formal completion
  always backs up and requests stop. The runbook now retains the 600-second
  commissioning guard until the backup observer, detached controller and first
  child are verified live; only then is it acknowledged using fresh full-guard
  proofs. Deployment or launch failures require stop verification, not idle
  waiting until the full budget deadline.

## Validation evidence

The reviewer ran 34 focused CF/STATIC tests, 26 private guard tests, and a combined
72-test CF/controller/guard checkpoint. All passed. The independently rerun full
offline suite passed **426 tests, with 5 skipped**, before the final ordering and
detach-race additions. The author reported **14 targeted launch tests passed**
for those final changes; their code and regression were read independently.
After all final code changes, the parent confirmed the full offline suite passed
**428 tests, with 5 skipped**, in 22.85 seconds before committing.
`git diff --check` was clean at this review checkpoint.

The private guard tests cover absent approval, exact study/cap/anchor binding,
rate and reserve preservation, expiration, exclusive controls, PID reuse,
stale or foreign proofs, commissioning ACK requirements, clock rollback and
shutdown despite a readiness-file write failure. They use synthetic approval
receipts and mocked operational dependencies, with no child or provider actions.

## Reviewed SHA256 values

| File | SHA256 |
|---|---|
| `scripts/run_v5_continuation.py` | `8d934c56d1c181fe30d782bdea1a064070d0a47a26685215e3c1eb5757a62a4f` |
| `scripts/run_v5_stage.py` | `8dfb22041253f117d4037067cac2bcb238c233145c784a99a6a4262d0c58453a` |
| `scripts/freeze_v5_continuation.py` | `70d8d3308ebeab97e3c75b89dc442f1a311ae3c602c466bc23c9b2c2639b82f5` |
| `scripts/prepare_v5_continuation.py` | `4a432cca2a67a74b0ae9ab77ec066fbc7614c2433c909ea9c4e55082e5b0a1bf` |
| `src/mb/v5_continuation.py` | `98599ecac364b11616c6a27978ea0375d50ce57b148c6dfa45227a4ac83470fb` |
| `src/mb/v5_static.py` | `f9dafe48a287a0c868936d584dcc7b6fd8d1912fccc070b1d36a3ce7f0426d6c` |
| `tests/test_v5_static_cf_metadata.py` | `efc092fd2834aac721b231dd197f6e9c41542281eaad4c8a67709d889812ffd1` |
| `tests/test_v5_continuation_launch.py` | `88cf8d215d47d46c8caabc4b7a4c5a9bfbf9893faf61b9be1c8df87725bfc6c4` |
| `docs/runbooks/V5_CONTINUATION_HANDOFF.md` | `adb106c673e88326b9a61ae48e7b5c44d8c4d6843dd1c831b0700b041b355b8f` |
| Private `continuation_guards.py` | `e1014c1b5f74ef44d1bf4f74e93064c0b755617649e44887bd88ac3bae01dcfe` |

## Remaining execution conditions

Commit the reviewed inputs, create and verify the new algorithm and three stage
freezes, and verify the deployed checkout and private helper hashes. Paid work
still requires explicit PI ratification and a numerical funding receipt. A
fresh same-instance status/rate check, mounted SD backup observer, fresh guard
proofs and new-source GPU acceptance are execution-time prerequisites. They
cannot be established by local tests and are not unresolved local code defects.

The independent local observer must verify actual provider stop: a remote
self-stop can terminate its own verification process before it records success.
An interrupted or ambiguous controller requires explicit reconciliation of the
original run and receipts before an identity-preserving resume. The reviewed
controller intentionally refuses an automatic fresh restart in that case.
Timing allowances are conservative forecasts, not physical upper bounds, and
must still fit the preserved cumulative budget at launch.
