# V5 local engineering review

2026-10-09. Reviewer: Codex `/root/pdf_visual_audit`, independently reviewing
the launch, freeze and acceptance tools written by `/root`. This review does
not constitute protocol approval, a freeze, GPU acceptance or paid execution
authorization. The PI explicitly left gate thresholds and sample sizes
unfrozen; their current values are implemented planning defaults.

## Conclusion and scope

No remaining blocking defect was found in the reviewed local implementation
after the corrections below. The tools are ready for the next, separately
authorized commissioning step once the numerical contract and spending cap
are approved and frozen. No model, provider command or network operation was
executed in this review.

The review covered `run_v5_stage.py`, `freeze_v5.py`, native acceptance and
smoke/resume evidence, their tests, and the GPU handoff. The provenance
materials/runner integration was authored by this reviewer and is therefore
not presented as independently reviewed here. Separate agents reviewed that
integration and the scientific selectors/scorers.

## Verified contracts and corrections

* **Launch prerequisites.** Linux-only execution requires a verified stage
  freeze, its exact configuration, the complete algorithm/source chain, model
  assets, an explicit existing data directory, and a newly approved cumulative
  budget. Current draft wording prevents an algorithm freeze. The budget
  template is deliberately unusable until populated and approved.
* **Budget and shutdown.** The spending anchor includes prior spend, bandwidth
  and shutdown reserves and cannot silently reset between stages. Both the
  detached watchdog and child runner enforce wall-clock and monotonic
  deadlines. Prelaunch failures also attempt shutdown when private controls
  are usable. Log/lock write failures do not prevent a shutdown attempt.
  Request success is insufficient: a separate command must verify stopped
  state. The minimum shutdown reserve was corrected to five billed minutes.
* **Detachment and duplicate prevention.** `--detach` detaches the entire
  supervisor, not just its child. A stage lock rejects a concurrent owner
  without stopping that owner's healthy process. A persisted launch intent
  precedes child creation and remains a recovery blocker after an uncertain
  launch or SIGKILL. An unresolved receipt must not be deleted and blindly
  retried. A returned supervisor PID alone is not proof of successful startup.
* **Immutable inputs.** The algorithm freeze includes the imported
  `supervise_v4.py` termination helper. Stage verification now requires the
  configuration, algorithm manifest and every consumed source pin to be
  covered by the hash map. Freeze creation is write-once; source or asset
  changes invalidate verification.
* **Native acceptance.** Evidence binds the model profile, source hash, test
  file hash and tokenizer manifest. All 17 Qwen runtime tests or all 8 Llama
  acceptance tests must execute and pass; missing, skipped, duplicate or
  stale evidence is rejected. These are future GPU checks, not local results.
* **Smoke and completed resume.** The prescribed four-episode, four-arm,
  two-recipient smoke has 768 readouts. The auditor rederives current identity,
  arm hashes, questions and physical-source truth; checks completeness,
  unexpected keys, finite logits/log probabilities and label mass; requires
  one C48 snapshot identity per episode/arm across questions; and checks the
  original/conflict private-note identities. Completed resume must preserve
  prior shard bytes and immutable config, identity, manifest, arm, note and
  snapshot files, while adding only empty record shards. Smoke evidence is
  explicitly non-scientific and profile-specific.
* **Post-run gate handling.** Exit code zero alone is insufficient. The
  launcher identifies the exact newly created or resumed run and recomputes
  its typed scientific result. A failed prerequisite is backed up and stops
  even with `--keep-session`; later audit/backup errors reset success before
  shutdown. The final review found and corrected a STATIC integration error:
  complete formal output has no prerequisite `gate` field. Formal completion
  now requires only a consumable complete analysis for either study. A failed
  formal matching recheck, effect direction or significance cannot reject or
  prolong formal collection. Formal N600 completion cannot keep the session.

The smoke identity comparison was checked against the actual producer:
`build_identity` already JSON-normalizes tuples into lists. No correction to
that comparison was needed.

## Local verification

* Full offline suite before the final formal-completion regression:
  **360 passed, 5 skipped** (23.27 seconds).
* Final focused launch/freeze/acceptance/smoke suite:
  **22 passed**. It includes a synthetic complete 768-record smoke and empty
  resume, snapshot mutation rejection, skipped native evidence rejection,
  timeout behavior under wall-clock rollback, shutdown despite unavailable
  logs, and formal completion independent of matching/effect values.
* `git diff --check` passed. No torch installation or local model execution.

The reviewed source hashes are:

| File | SHA256 |
|---|---|
| `scripts/run_v5_stage.py` | `97aa0d6cacb6145ceec7e9db2d21b2866a97a0cc5b3b5f4cb94cf85cf2964628` |
| `scripts/freeze_v5.py` | `80677cc49a75d651f12b2bb52c26cd4f82e75d0624dcf4ff98d6dc5184b7072c` |
| `scripts/check_v5_acceptance.py` | `0a332b851180f1b8e249602cbf0ac6fbadd00c70d9d1d9695b2cb93488203f7b` |
| `scripts/check_v5_smoke.py` | `76069132aeb9ac577eac5b6df7f512532f71a62491693d261844a9f308030c09` |
| `scripts/check_v5_preflight.py` | `42adcf0d3f5d214cb954e9a5899ae1525f5f2b283a531675ceec2db5fb876e19` |
| `tests/test_v5_preflight.py` | `34b0f8a31d211456ea8c79bec8baace1ce42cdf43c65a18f97151613cb22887a` |

## Remaining commissioning work

On the approved rented host, commission the exact-instance stop, fresh-state
verification and hash-verified backup commands; then collect the pinned native
acceptance, smoke and no-op-resume evidence for each checkpoint. Replace initial
runtime projections with measured throughput before research stages. Private
command contents and actual provider behavior are outside this local review.
Provider/API outages can prevent verified shutdown, so these mechanisms do not
constitute an unconditional billing guarantee. Retain failure evidence and
escalate an unverified stop rather than claiming the instance is stopped.

No existing research record, historical freeze or manuscript was changed by
this review.
