# V6 bounded benchmark independent review — 2026-10-14

Scope: independent engineering review of the new `src/mb/v6_benchmark.py`,
`scripts/v6_prepare_benchmark.py`, and their offline tests. This review does not
authorize hardware, spending, source adoption, scientific admission, or formal
collection. The implementation author retains the repository claim and owns the
full-suite check, status update, and commit.

The original instance was reported freshly stopped by the coordinating agent;
this reviewer did not query a provider, use SSH, load a model, import torch,
inspect scientific outcome files, or change any historical evidence. The
additional benchmark allowance remains a proposed PI amendment, not authority
created by this review.

## Initial findings supplied to the author

1. **Preserve failure evidence before re-raising.** Initially, `run_model`
   created an empty attempt directory and wrote its microcomparison only after
   every gain passed. A mismatch or exception before then discarded the reason,
   phase, and completed gain evidence. `run_case` retained partial rows but no
   terminal error receipt. This repeats the previously documented diagnostic
   weakness. An attempt identity and write-once failure receipt must retain the
   original exception and phase without exposing scientific effect values;
   completed comparison hashes should survive a later failure.
2. **Revalidate forecast evidence, including synthetic exclusion.** The first
   `project` implementation accepted three `{case, exact: true}` markers and
   positive candidate durations/byte counts without reference results, a
   microcomparison, pinned-model evidence, or the frozen runtime. An independent
   offline reproduction confirmed acceptance of precisely that incomplete
   input. The projection must reject synthetic/short-clock measurements and
   rederive exact reference/candidate comparisons rather than trust markers.
3. **Validate the pinned architecture and revision.** Exact `NativeBackend`
   type and tokenizer profile do not establish the approved checkpoint:
   `NativeBackend` intentionally supports tiny/custom models. The benchmark
   entry point must validate the approved model configuration and revision, or
   consume an equivalently bound independently verified receipt, before
   labelling the timing as pinned-model evidence.
4. **Recheck expiration before success.** Initially, callbacks ran before
   step/probe operations but not after final synchronization or archive restore.
   An offline baseline fixture whose synchronization expired its lease at the
   end of collection still returned `status=complete` and wrote `summary.json`.
   Check around model/archive operations and immediately before terminal success
   receipts. A cooperative callback cannot interrupt an in-flight native call;
   independently operating local/remote stop guards remain necessary.

These findings concern engineering correctness and evidence integrity. They do
not propose changes to research questions, sample sizes, metrics, gains,
selection, numerical tolerances, or financial caps.

## Independently checked scope and arithmetic

- Reconstructed all 1,006 original prepared task fingerprints from the public
  preparation recipe, excluding episode IDs, stages, and seeds. The six new
  benchmark task fingerprints are unique and have zero overlap with those
  original tasks. No scientific records were read for this check.
- The complete task comparison executes the real scheduler including the text
  branch: 352 readouts and 16 pair/tape archives. The neutral baseline and
  calibration cases are separate workloads. Generated export identities,
  sealed probe readouts, raw records, and archive event identities are suitable
  exact-comparison evidence; each native archive is loaded and verified.
- Forecast count algebra retains 240 formal episodes, text on 60, baseline 60,
  three 40-episode calibration cohorts, and validation 80 per checkpoint.
  There are six future stages per model. The conservative compute component
  keeps the factor of 1.5 and uses the largest observed workload when a neutral
  stage/gain has no direct pilot. This is deliberately more conservative than
  the illustrative text-subtracted calculation.
- A single example per workload has no estimated sampling uncertainty. Gain 1
  neutral timing is a proxy for other gains and validation. Setup, backup,
  throughput, transfer, prior charges, further acceptance/smoke, shutdown, and
  retained storage still require the external lifecycle accounting. A forecast
  component cannot replace the frozen complete-workload admission gate.
- The public preparation command is inert and has no hardware/provider launch
  route. The executor requires an existing backend and external callback. Its
  new filenames and engineering-only markers keep these outputs outside the
  scientific stage ledger. Neither a successful comparison nor this review
  creates automatic formal continuation.

Initial offline validation: `tests/test_v6_performance.py` passed all 16 tests.
The two small independent reproductions above used only synthetic/incomplete
fixtures and temporary directories. They are software checks, not performance
measurements.

## Lifecycle and coverage limitations

The external supervisor must bind the exact new source/package, current exact
instance, original cumulative session, approved additional allowance (if any),
deadline, storage, credit, backup destination, and both independent stop guards.
It must own model loading/unloading, the second-model transition, completion or
failure backup, actual provider-stop verification, and durable archival of all
attempts. None of those paid or private-control operations was exercised here.

The initial complete-episode trace hashed step exports and sealed probes but not
every post-commit state. The microcomparison independently covered committed
state digests at all four gains, and the candidate inherits the reference commit
implementation. Claims must reflect that exact coverage unless the trace is
expanded. Additional instrumentation overhead belongs to the measured workload
and should not be presented as an uninstrumented production speed estimate.

Final fix validation and disposition will be appended after the author supplies
the revised implementation and focused tests.

## Follow-up finding and final closure

The follow-up review found a serialization defect: direct equality between
in-memory tuples and JSON-loaded lists rejected both saved package materials and
saved report runtimes. The original forecast fixture passed in memory but failed
after a JSON round trip. The author replaced those comparisons with canonical
digests and added saved-package/material and saved-report tests. This defect is
closed.

All four initial findings are now closed for the reviewed offline scope:

- Each admitted model attempt saves its identity before candidate construction.
  Microcomparison progress retains each completed backend/gain hash. Exceptions
  preserve a write-once failure receipt and the original traceback, and exact
  mismatches retain both hashes. Existing attempt directories are never reused
  or changed by this failure path. Partial engineering rows remain intact.
- The forecast requires native-marked, complete measurements with the original
  runtime and deterministic material identities; it recomputes each paired
  comparison against the reference. It rejects synthetic measurements, changed
  materials, shortened clocks, altered comparisons, invalid timing, incomplete
  reference work, missing gain checks, and different source versions across the
  two models. Four exact microcomparison gains are required.
- The model entry point validates the pinned architecture and revision, the
  externally supplied previously accepted model identity, and the exact expected
  source manifest. The accepted identity and its authority still belong to the
  separately reviewed external supervisor; a caller-generated string is not an
  acceptance receipt.
- Callback checks now surround native consumption, steps, probes, micro calls,
  archive writes/restores, and final synchronization/success. The previously
  reproduced expiry-after-collection case fails with a retained traceback and
  no complete summary. The external independent guards are still required to
  stop a hung call or process and to verify actual provider shutdown.

The trace was also expanded to hash every returned `commit_answer` state. This
closes the post-commit coverage limitation described in the initial review.
That extra state hashing contributes to the observed comparison time; report
the result as an instrumented engineering workload and retain the conservative
forecast/admission separation.

Independent final verification:

- `tests/test_v6_benchmark.py` plus `tests/test_v6_performance.py`: **38 passed**.
  No CUDA/native test was run or counted as passed.
- A separate JSON-loaded-material entry-point check used an uninitialized mock
  backend object and a callback that deliberately refused before candidate
  construction. It reached the intended guard and retained both the attempt
  identity and failure receipt. No model constructor or forward was called.
- The original six-versus-1,006 substantive-material disjointness check remains
  valid; the material recipe did not change during correction.

Reviewed final SHA256 values:

| File | SHA256 |
|---|---|
| `src/mb/v6_benchmark.py` | `2fff9bebaa51df88a83ac2a373b91ae3380161e9ff66d32b058b86d9aae0be70` |
| `scripts/v6_prepare_benchmark.py` | `99fc31c342f8919f1a78f181a5cb7f8750b8bb3368f926deb3bd48839a6b7478` |
| `tests/test_v6_benchmark.py` | `f0ba620a01569a9fa36507fd396951a2080bdede8c51765dc6b45938ef98b337` |

**Disposition:** no unresolved blocker to retaining this implementation as an
offline, independently reviewed engineering candidate. This is not a paid-run
approval, native equivalence pass, measured speed claim, financial admission, or
production-source adoption. The proposed additional allowance, exact private
supervision/guard boundary, actual hardware comparison, backup/stop verification,
and complete-suite milestone remain outside this review and must be completed
by the coordinating agent and PI as applicable. This reviewer made no commit.

## Final narrow follow-up

The author subsequently extracted `validate_materials` so the saved-package
round-trip test exercises the same validation function used by `run_model`.
The function preserves canonical material equality and rejects missing/changed
cases. The failure wrapper now catches an `OSError` while writing its evidence,
adds a diagnostic note to the original exception, and re-raises that original
exception. A new test proves that unavailable storage does not replace the
original deadline failure. An unavailable disk can still prevent durable local
evidence; external supervision must retain the worker traceback and stop safely.

The new `V6_BENCHMARK_HANDOFF.md` accurately limits the request to engineering
comparison, preserves the cumulative financial origin and existing caps, keeps
the additional allowance pending PI approval, forbids automatic scientific
continuation, and states the instrumentation/projection limits. A requested
wording clarification now explicitly preserves the lifecycle order: close and
copy complete/partial outputs under the paid deadline, verify actual provider
stop, then perform the independent full SD rehash locally.

Independent focused validation after these changes: **39 passed**. The
coordinating agent separately reported the complete offline suite as 797 passed,
seven skipped, and one GPU test deselected; this reviewer did not rerun that
suite. No paid action or native/GPU execution was performed by this review.

The following hashes supersede the earlier reviewed snapshot for this narrow
follow-up, without altering the historical review above:

| File | SHA256 |
|---|---|
| `src/mb/v6_benchmark.py` | `d50b4d7484aa78d3ec2f776dc7d0186c59a58641305906af809400a100527e2c` |
| `scripts/v6_prepare_benchmark.py` | `99fc31c342f8919f1a78f181a5cb7f8750b8bb3368f926deb3bd48839a6b7478` |
| `tests/test_v6_benchmark.py` | `10d16bbbe53213f8c9f986bb528b536b3b1a59b6f3e19b174236ccc0376aa1c5` |
| `docs/runbooks/V6_BENCHMARK_HANDOFF.md` | `0416a0bc5911a83817278b5940d93ddbde11c10e400a91ea27b29710b32190a9` |

The offline-candidate disposition remains unchanged: no unresolved finding in
the reviewed code, tests, or handoff. Paid admission, exact private controls,
actual native equivalence, speed, and complete lifecycle costs remain separate
uncompleted requirements. No commit was made by this reviewer.
