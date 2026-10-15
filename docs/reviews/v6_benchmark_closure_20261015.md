# V6 benchmark closure audit: exact comparison complete, backup incomplete

Audit: 2026-10-15 04:30–04:35 UTC, Codex. This is a read-only/offline closure
audit, not a new hardware attempt or adoption of the candidate backend.

## Outcome

Both pinned real checkpoints completed all four exact microchecks and all three
paired engineering workloads. The controller reached worker state `complete`,
but final backup failed. Original `terminal.json` and `closure_complete.json`
remain `success=false`, with `data_backup_verified=false`. No scientific
baseline, calibration, validation or formal sample was dispatched.

Actual provider stop was recorded at 04:17:19 UTC and independently queried again
at 04:31 UTC: actual state exited and intended/current/next states all stopped,
with the same instance identity. Original controller and local full guard are
both absent; the guard's verified stop receipt is present. The v6 heartbeat is
paused. No automatic restart, retry or additional model call occurred.

## Verified timing

Times are synchronized episode measurements, in seconds. Each cell is one
disjoint engineering fixture, not a runtime distribution or scientific result.

| Checkpoint | Workload | Reference | Candidate | Time reduction |
|---|---|---:|---:|---:|
| Qwen | Full with TEXT | 1728.354 | 1683.278 | 2.61% |
| Qwen | Baseline fixture | 149.953 | 147.910 | 1.36% |
| Qwen | Gain-1 neutral fixture | 531.156 | 531.247 | -0.02% |
| Llama | Full with TEXT | 1340.802 | 1309.473 | 2.34% |
| Llama | Baseline fixture | 117.846 | 118.620 | -0.66% |
| Llama | Gain-1 neutral fixture | 417.462 | 414.801 | 0.64% |

Both full comparison JSON documents match the remote sealed inventory's original
SHA256 and byte length. The existing offline projection helper revalidated all
exact comparison markers, source/model/material/runtime bindings and summaries.
The Llama complete-episode number is 1309.473 seconds; the earlier approximately
1496-second progress interval included acceptance activity outside that timer.

## Backup failure and retained evidence

The sealed inventory has 134 files / 4,026,176,147 bytes. Independent SD rehash
found 65 matching files / 1,497,402,141 bytes, no mismatches, and 69 missing files.
All 53 private control-backup files independently rehash correctly.

Two different backup failures occurred:

- Control rsync returned a `Total transferred file size: 10057 B` statistic.
  The controller parser requires the literal word `bytes`, so it rejected an
  otherwise copied control tree. Both saved logs reproduce this parser mismatch;
  all 11 control files independently match their original inventory hashes.
- The output-tree copy hit its 180-second subprocess limit twice. The two partial
  transfers do not establish a successful full-backup rate. Timeout stderr was
  not retained by the existing exception path, so no more specific network or
  storage cause is claimed.

A prior read-only local Qwen timing snapshot contains the complete comparison,
microcheck and six summaries. Re-encoding each with the original serializer
reproduced its **exact original sealed hash and byte length**. These eight files
were saved separately as recovered evidence and copied/rehashed to SD; original
failed-copy directories and failure receipts were not rewritten. This is
byte-verified JSON recovery, not reconstruction of model tensors or raw rows.
There remain **61 missing local files / 2,528,741,777 bytes**. Full raw backup is
still incomplete; retain the stopped instance and do not destroy its disk.

The new audit, missing list, recovered JSON and source receipts were also copied
to SD and independently rehashed. Private audit location is the benchmark's
`closure-audit-20261015-0430` directory; connection information stays outside Git.

## Qualified workload estimate and budget

At the actual combined rental rate USD1.47074074/hour, using the complete measured
candidate fixtures and unchanged N240/text60, baseline60, calibration3x40 and
validation80 for each model:

| Compute component | Hours | Rental USD |
|---|---:|---:|
| Illustrative Qwen + Llama compute | 251.52 | 369.92 |
| Existing conservative compute rule | 555.33 | 816.75 |

The illustrative estimate includes about141.39 Qwen hours and110.14 Llama hours.
It uses gain1 neutral timing as a proxy for other gains/validation and assumes
both models pass all future gates. Each workload has only one measured example.
The conservative rule retains the original maximum-workload fallback and1.5
multiplier for unmeasured stages; it is not a statistical confidence interval.

Neither row includes loading, backup, transfer, further acceptance, prior spending,
shutdown or retained storage. The helper's setup/fixed-backup assumption adds
4.8 hours, but actual full-backup throughput is unvalidated. A separately saved
partial-transfer scenario is explicitly non-certifying and is not presented as
a complete ETA or spending authorization. Current execution is already
unaffordable within USD100 on compute alone; do not launch formal collection.

The bounded benchmark's restore-to-verified-stop interval was2.86989 hours. Its
rental component is approximately USD4.22, not an invoice. At the original1.60
ceiling plus the entire1.60 noncompute reserve, the bound is USD6.19, below the
approved incremental USD8. All earlier session costs, original financial origin,
totalUSD100 and historical deadlines remain unchanged. Retained disk continues
to incur storage charges after GPU stop.

## Next boundary

Continue offline optimization preparation only. Before any file-retrieval
restore, prepare a separate bounded, reviewed recovery that copies only missing
sealed files, accepts the actual rsync units, retains timeout diagnostics and
allows enough transfer time while preserving protection and all prior charges.
It must not launch a model, overwrite original failure evidence, or become a
benchmark/model retry. No such recovery was launched or newly authorized here.

Full offline suite: 797 passed, seven skipped, one GPU deselected.
