# V6 smoke supervision failure — 2026-10-14

## Verified state

The first Qwen smoke worker launched at 20:14:26 UTC. The external supervisor
failed at 20:25:15 during the first periodic backup and concurrent admission
refresh. It terminated the worker, copied the final partial inventory, confirmed
actual provider stop at 20:30:33, and independently rehashed the SD copy.

The retained copy contains 78 files totaling 983,380,170 bytes. An additional
independent check at this heartbeat reproduced every expected hash. Zero of the
two smoke episodes is complete; there is no smoke completion receipt. The eight
previous Qwen native acceptance checks remain valid. Neither Llama acceptance
nor a neutral or formal scientific stage has run. This is an engineering failure,
not a scientific gate failure or a result about interaction.

## Diagnostic evidence and limits

The original adapter suppressed its detailed exception, leaving a supervisor
`ValueError`. A narrowly scoped same-instance diagnostic restore used fresh local
full and short guards under the unchanged initial allowance. It only retrieved
the retained worker, native and guard logs; it launched no model and ended in
verified actual stop. Five mocked lifecycle checks cover successful retrieval,
guard failure, restore failure, collection failure and unverified stop. Nine
diagnostic/control files plus the audit receipt were copied and rehashed on SD.

The native log contains checkpoint loading and no model traceback. The wrapper
reports interruption after the supervisor failure. The first incremental transfer
had received about 122.5 MB when it was interrupted. A concurrent refresh had
successfully mirrored its new admission immediately before failure, but did not
record its final lease renewal or become the supervisor's accepted proof. Its
observed span is approximately 40.04 seconds, against the private adapter's
40-second aggregate bound for non-backup requests. The preserved admission also
passes historical validation at the failure time.

These observations make the aggregate refresh timeout under concurrent transfer
the leading engineering explanation. They do not conclusively identify the
discarded original exception. Do not report an out-of-memory error, model failure,
or failed research gate without further evidence.

## Recovery prerequisites

Both sequential controller attempts are terminal and must not be restarted.
Preserve their evidence and the partial smoke files. Prepare a narrowly versioned
private operational correction with safe diagnostic reasons and a regression
check for concurrent refresh/backup timing. Do not relax the scientific contract,
financial cap, or independent lease as a workaround.

Any subsequent smoke continuation needs a separately reviewed exact-plan resume,
fresh single-attempt control and guard identities, original-byte verification,
and the original retry limit. A partial smoke is not a completed prerequisite.
Both complete model smokes, exact no-op resumes, measured whole-workload and
transfer costs, and all frozen neutral gates remain mandatory before formal work.

The cumulative initial USD25, total USD100, hourly USD1.60 ceiling, original
financial origin and current deadlines are unchanged. No new stopped-time credit,
scientific adjustment, sample reduction or parameter choice was made. No core
effect or significance was inspected. Public offline suite: 758 passed, six
skipped, one GPU test deselected.
