# V5 Qwen formal startup

Verified on 2026-10-09 (Chicago), 2026-10-10 UTC. This review concerns prerequisites,
data integrity and timing only. No formal attribution effect or significance was
inspected or used to continue the study.

## Prerequisites

Independent raw-ledger recomputation reproduced both complete gates: baseline
60 episodes / 3,840 readouts and validity 80 episodes / 2,880 readouts. All 56
algorithm inputs and six baseline source pins match. There are no duplicate,
nonfinite or truncated prerequisite records. The 221-file validity backup was
independently rehashed against the original ACK inventory:
`988df115184d045e6e2a6dfc0f88d5422437e8fa46b7ae9e70b396632b177f62`.

C0 CAP is 100%; ordinary and conflict KV are both 98.4375%, a 1.5625-percentage-
point drop, within five points. All format checks pass. The required rule-access
one-sided 95% episode-bootstrap lower bounds are 0.862682031 (donor-own) and
27.226120711 (donor-Robin specificity).

Donor-own WORD access does not pass: gain -0.510944843, lower bound -2.446982560.
Donor-Robin WORD specificity passes (lower bound 26.681169693). The frozen rule
therefore permits the rule experiment while limiting word interpretations.
It does not permit interpreting a null word result as preserved attribution.

## Formal startup and protections

Run: `20261010-025849_v5_qwen_provenance_confirm_v5_qwen_provenance_confirm`.
The reviewed controller generated the source-backed config, verified remaining
package cost, and froze the stage before collection. Formal freeze SHA256:
`38b59bfbe6b99dfdae6a183f2c7f2ca47282345c72f63c6b6479830c54a78430`.
Run identity SHA256:
`95a6378f980734c925be8207f3c419d0046d46e24f27678ed8352caa6af2a0a7`.

At 03:25 UTC, 1,528 of 43,200 readouts were successful, with 20 complete episodes
and two partial episodes. No successful key was duplicated. Fixed N remains 600;
the invocation has no smoke limit, code-change override or keep-session flag.
The controller and model child are live, and first records are writing normally.

The original budget start, USD 60 cap, conservative USD 1.40 hourly rate and
deadline are unchanged. The local and remote full-budget guards are live. The
formal launch projection reserves 18.93 hours for this stage and 12.40 hours for
the remaining STATIC package/overhead, for cumulative cost about USD 51.22 with
elapsed time and reserves included. This is a conservative forecast, not an
actual bill or guarantee. STATIC requires measured timing before costly stages.

## Timing and handoff

Using counts and elapsed time alone, the early rate is 1.0313 seconds/readout,
giving about 11.94 hours remaining at observation. The point estimate is
October 10 at 15:21 UTC / 10:21 Chicago, plus final processing and backup; an
early linear estimate can change as condition/chunk timings vary.

The `v5` heartbeat now has one check on October 10 at 10:30 Chicago, replacing
the half-hour schedule. If collection is still healthy, reschedule near the new
ETA without repeated polling. Completion requires full expected data, verified
backup and actual provider stop. The independently approved bounded Llama
STATIC branch remains pending; restart only the same instance with unchanged
budget and freshly verified protection. Llama provenance remains unavailable
after its own frozen validity failure and must not be retried or retuned.
