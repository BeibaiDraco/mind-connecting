# V5 GPU handoff

Prepared locally on 2026-10-09. **No GPU has been started.** The PI explicitly
selected “complete implementation first; leave gates and sample size unfrozen.”
The numerical values in configs and PROTOCOL_V5.md are executable planning
defaults awaiting that decision, not a frozen protocol or a paid authorization.

## What is prepared

* Two-checkpoint three-arm provenance experiment, twelve formal question types,
  donor-only Robin mutation, fixed physical answers, separate record truth, and
  original START/WORD anchors. Baseline 60 and validity 80 are implemented defaults.
* Llama STATIC calibration at three layers, 15 coarse candidates, at most 2
  deterministic refinements reusing exact original note IDs, one untouched 80-
  episode validation, and a conditional three-arm formal comparison.
* Source-backed stage generators. Later configs cannot be fabricated as passing
  from a copied Boolean: the generators recompute the complete pinned raw chain.
* Native GPU acceptance wrapper, four-episode smoke/no-op-resume auditor, staged
  source freezes, detached supervisor, cumulative budget guard, backup and stop
  hooks. Native/GPU evidence has not been collected on this machine.
* Full local material/tokenizer and split-overlap evidence in
  `docs/results/v5/local_preflight.json`; split hashes in
  `configs/v5/split_manifest.json`. Original v4 input hashes were verified against
  its recorded Git commit. Existing frozen sources and results are not rewritten.

## Before commissioning a rented instance

1. PI chooses final gates/sample size and new spending cap. If choices differ
   from the implemented defaults, update the new code/configs and associated
   tests before freezing; do not edit any historical freeze. The old USD 60 cap
   belongs to completed v4 and is not carried forward automatically.
2. Finish `PROTOCOL_V5.md` with the exact approved contract, including the header
   `Execution contract approved by the PI`. This is a factual approval record,
   not a bypass string to add while approval is pending.
3. Run the offline suite, retain the independent scientific/engineering reviews,
   commit the complete inputs, then write the algorithm freeze:

   ```bash
   .venv/bin/pytest -m 'not gpu' -q
   .venv/bin/python scripts/freeze_v5.py --write algorithm
   ```

   Commit the resulting new manifest. Freeze verification refuses the current
   unfrozen draft by design. Later stage manifests are written separately.
4. Check the actual offer, available storage and existing model cache. A native
   BF16 GPU with ample memory is required; an 80 GB class instance has prior Llama
   headroom, but a new device still needs acceptance and measured throughput.
   No server endpoint or credential belongs in tracked files. Transfer code and
   both verified tokenizer asset directories; do not transfer credentials through
   Git. Review file lists before syncing; preserve the old result directories.

## Private execution controls

Copy `configs/v5/launch_budget.template.json` outside the repository and populate
it only after approval. Record actual rate, prior setup/idle spend, bandwidth
reserve and the original session start epoch. The shutdown reserve must cover
at least five minutes of rental time. `approved=false` and null placeholders
are deliberately unusable. Keep the same spending anchor throughout the session.

Three private JSON files each contain an argv array, never a shell string:

* stop: requests stopping the exact rented instance (not destruction);
* verify-stopped: exits 0 only when a fresh provider query confirms actual stopped
  state, and nonzero on unknown/running/error;
* verified-backup: copies immutable data and append-only shards to the approved
  durable destination, checks hashes/prefix preservation, and exits 0 only after
  verification. The latest exact run path is in control `last_stage.json`.

Commission these helpers against the actual instance before scientific work.
A successful stop request alone is insufficient. No-log failures still attempt
shutdown. Provider API outages can still prevent stop; retain failed evidence
and alert the PI. Files and tokens remain private, outside the repository.

## Launch ordering

Set explicit `MB_DATA_ROOT` to an existing data directory. Set Hub/Transformers
offline after the approved pinned weights are cached. Use the isolated Linux
environment from `scripts/setup_replication_gpu.sh`; never install torch locally.

For each selected config, create a stage freeze and verify it. Example:

```bash
.venv/bin/python scripts/freeze_v5.py --write stage \
  --config configs/v5/provenance/llama31_smoke.yaml \
  --output /workspace/private/v5/llama-smoke-freeze.json
```

Run the **entire supervisor** detached with `--detach --log-file`, not just the
model subprocess. Provide private budget/control paths and a conservative or
measured `--estimated-seconds` which fits the remaining cumulative cap. Verify
the control receipts after dispatch; a returned PID is not proof of healthy
startup. Never launch a second GPU worker if a prior receipt is unresolved.

1. Native acceptance: use that model's smoke config with `--limit 4`,
   `--native-acceptance-output` and `--keep-session`. This invokes 17
   Qwen or 8 Llama existing native runtime tests. No skip can pass.
2. Smoke: same config, `--limit 4`, `--native-evidence` pointing to its passing
   native evidence, and `--keep-session`. The supervisor audits all 768 records
   and stores `<model_profile>_smoke_before_audit.json` in the private control directory.
3. No-op resume: repeat smoke with `--resume` pointing to that exact run and
   `--smoke-before` pointing to the original audit. It must append no successful
   readout, change no prior shard/input/note/snapshot, and create an empty shard.
4. Scientific stages additionally require `--smoke-run`, `--smoke-before` and
   the matching `--native-evidence`. The supervisor rejects another model's,
   stale-source, incomplete or failed engineering evidence.
5. Small prerequisite stages may use `--keep-session` while the next stage is
   prepared. A scientific gate failure backs up and stops even with that flag.
   Formal completion always backs up and verifies shutdown; `--keep-session`
   is disallowed for N=600. No result's sign or significance affects continuation.

STATIC branch (Llama only):

```bash
.venv/bin/python scripts/make_v5_static.py initial
.venv/bin/python scripts/make_v5_static.py match --calibration-run CAL_RUN
.venv/bin/python scripts/make_v5_static.py next --calibration-run CAL_RUN --match-run MATCH_RUN
```

`next` returns a stop decision, one deterministic refinement, or the selected
validity config. After a refinement, call `next` with ordered `--refine-run`
arguments; at most two are allowed. Freeze the selected validity config BEFORE
collecting validity. `confirm` takes the same calibration/match/refinement chain
and `--validity-run VALIDITY_RUN`. It refuses failed validity and cannot reselect.
Freeze the generated formal config before collection. Each output config is
write-once. Repeated identical generation is harmless; changed replacement is refused.

Provenance branch (each of `--model qwen` and `--model llama31`):

```bash
.venv/bin/python scripts/make_v5_provenance.py initial --model llama31
.venv/bin/python scripts/make_v5_provenance.py validity --model llama31 --source-run BASE_RUN
.venv/bin/python scripts/make_v5_provenance.py confirm --model llama31 --source-run VALIDITY_RUN
```

Both source studies remain independent of STATIC's outcome. A valid rule branch
with failed word access receives the prespecified word interpretation limitation.
Complete raw data are retained; no sample exclusions or significance stopping.

## Runtime and recovery

The implemented defaults entail 86,400 provenance formal readouts across two
models, plus 36,000 conditional STATIC formal readouts, 8,640 maximum STATIC
selection/validation readouts, 13,440 provenance baseline/validity readouts and
engineering/calibration overhead. The main formal package has 122,400 readouts if
STATIC validates. Qwen and Llama need separately measured throughput; readout
counts are not interchangeable wall-clock estimates. Historical Llama matching
5,760 reads took 3,503 seconds and validity 4,480 took 3,206 seconds; use these only for an initial
conservative feasibility projection and replace it with new measured timings.

The independent instance-local watchdog survives an SSH or supervisor failure.
It checks both absolute and monotonic deadlines. A persisted child intent blocks
duplicate recovery after an uncertain launch or SIGKILL. If such a receipt exists,
first verify provider state and exact child/run identity, preserve all evidence,
then resume the SAME run with the SAME source/config. Never delete the receipt
and blindly restart. Do not use `--allow-code-change` for these experiments.

Final output analysis is already implemented in v5 postprocessing. Combine the
two model-specific provenance summaries with `mb.v5_provenance.combine_formal`;
keep fixed Holm family sizes even when a model's prespecified validity failed.
Report unavailable models explicitly. Positive logit movement alone is not an
increased error rate, and rule-only STATIC matching is not word matching.
