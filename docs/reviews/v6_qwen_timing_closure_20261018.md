# Qwen engineering timing: closure and qualified estimate — 2026-10-18

The independently audited Qwen-only attempt is complete and closed. This is
engineering evidence, not numerical scientific adoption or scientific collection.
No Llama model or scientific baseline/calibration/validation/formal stage ran.

## Closure and integrity

Root: `/private/tmp/mb-v6-execution-20261012/qwen-timing-20261018/`.
The worker ended successfully at 19:27:12 UTC. Actual provider stop was recorded
at 19:47:12 UTC and independently reconfirmed. Exact controller and local guard
identities are gone. Restore-to-observed-stop duration was 6714.940 seconds,
inside four hours; at the observed USD1.29962963/hour this implies about USD2.42
in lifecycle rental, excluding transfer and later retained-disk charges. This
is a rate-based estimate, not an invoice. Original charges/origin and historical
USD100 target remain unchanged. No retry or further paid execution is admitted.

Independent review verified all 163 remote evidence files, 75 final controls,
141 prelaunch files, 75 scientific pins and 97 source/assets. The complete
3,644,016,640-byte tar and its restored inventory match. Five new independent
audit receipts were separately copied to SD and rehashed. Exact 55 CUDA test
identities passed with no skips, errors or failures. All 80 raw micro positions
across the four Qwen gains reproduce zero greedy disagreements. Case
measurement/result pairs, record key coverage, partial/final rows and archive
restore/reopen coverage match. Neutral fixtures correctly do not claim archive
or Replay checks that they do not perform. Historical missing 61-file evidence
remains unresolved. Automation is paused.

Final independent audit SHA256:
`7c4c080b5d6158b253c048398d1873f40afb093237df0c6fe9d85cb0a08c3922`.

## Complete measured cases

Each fixture contains two engineering episodes. Model-work time includes raw
archive writes and the original within-run Replay where applicable.

| Case | Model work | Entire case | Records |
|---|---:|---:|---:|
| Short repeat | 643.694 s | 1975.846 s | 680 |
| Full six-round cohort | 1674.476 s | 2724.673 s | 680 |
| Baseline engineering fixture | 202.839 s | 202.879 s | 216 |
| Gain-1 neutral engineering fixture | 411.409 s | 411.472 s | 336 |

The short case's extra time includes an additional complete repeat, not just
archive restoration. Full-cohort post-compute restoration/verification consumed
1050.197 seconds (17.50 minutes). Neither should be silently hidden in an
end-to-end estimate or assumed mandatory for every production episode.

The final transfer plus local whole-tar hash took 1136.678 seconds for 3.644 GB,
about 3.206 MB/s effective throughput. This is not isolated network wire speed.
Loading, CUDA checks and compilation are separate; compilation counters are
cumulative within a backend and must not be added again for each case.

## Historical speed comparison and limits

Compared with the October 14 Qwen reference, the full workload's historical
throughput ratio is approximately **2.03x**, baseline **1.48x**, and gain-1 neutral
**2.58x**. These are descriptive comparisons, not a contemporaneous paired
benchmark or a confidence interval. The native model identity/revision and
full runtime match, but material and TEXT mix differ.

The new two-episode cohort contains the old full episode plus a new episode;
TEXT is on the new one. Its TEXT fraction is 50%, versus the old single
episode's 100%. The quoted full comparison uses `(2 * old elapsed - old
separately measured TEXT time) / new elapsed`, an explicitly approximate
historical workload adjustment. It does not subtract old TEXT cost from the
new measurement. Neutral balanced generation also changes material when N
changes from one to two, including the shared episode ID. No matched-output
or cross-backend trajectory-equivalence claim follows from these speed ratios.

## Qwen-only planning estimate

Assume all future scientific gates pass, unchanged N240 formal / N60 TEXT,
N60 baseline, three N40 calibration cohorts and N80 validation. Use the observed
two-episode timings, with gain 1 as an unverified timing proxy for the other
gains and validation. Retain the measured 50% TEXT fraction when scaling formal
work, deliberately overcovering the planned 25% rather than guessing its cost.

| Component | Explicit scaling | Hours |
|---|---|---:|
| Formal model work | 120 full cohorts | 55.82 |
| Baseline model work | 30 baseline fixtures | 1.69 |
| Calibration + validation proxy | 100 gain-1 neutral fixtures | 11.43 |
| Total model work, including raw writes | Sum above | **68.93** |

Approximately 255.9 GB of raw output is implied by the same scaling. Copying it
serially at this attempt's effective backup rate adds about **22.17 hours**,
yielding **91.11 hours before additional setup, smoke, final verification and
uncertainty margin**. At the observed rate, model work alone is about USD89.59;
model work plus serialized copying about USD118.41, excluding bandwidth,
additional setup and stopped storage. These are planning arithmetic, not an
affordability admission or an upper bound.

The frozen execution design permits incremental backup overlapping compute.
How much transfer can be hidden this way was not measured here. If the
benchmark's exhaustive GPU archive-restoration checks were additionally copied
into every formal cohort, they would add **35.01 hours**, producing a separate
**126.11-hour serialized diagnostic scenario** before remaining overhead.
This is not a mandated scientific cost and must not be presented as the only
valid production schedule. A separate 50% engineering planning sensitivity on
the 91.11-hour work-plus-serialized-copy scenario gives 136.66 hours and about
USD177.61 at the observed rate. That margin is neither a confidence interval
nor the frozen production affordability check. Any removal of required verification still needs
engineering review; no source or execution change is made by this estimate.

Only two new engineering episodes support each measurement. No sampling
uncertainty, performance-tail bound or rigorous completion date is available.
No Llama or combined two-model forecast is made. Further numerical admission,
scientific gates, protected production scheduling and fresh financial authority
remain separate; no formal run follows automatically.

## Reproduction

Root arithmetic with exact input hashes and explicit assumptions is preserved
in `/private/tmp/mb-v6-qwen-timing-analysis-20261018/root_projection_reviewed.json`.
Independent analysis is under the same directory's `independent/` subdirectory.
The raw results remain in the SD-backed `v6/qwen-timing-20261018/restored/` tree.
Full offline suite: 1234 passed, ten skipped, one deselected.
