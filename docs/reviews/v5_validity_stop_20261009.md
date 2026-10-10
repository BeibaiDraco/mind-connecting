# V5 Llama provenance validity stop

Reviewed on 2026-10-09 (Chicago); validity completed at 2026-10-10 01:10:56 UTC.

The frozen Llama provenance validity gate failed. The stage is complete: 80
episodes, 2,880 expected and successful unique finite readouts, no missing or
malformed records. The independent reviewer recomputed the gate from the raw
ledger and obtained the saved output exactly. All 56 algorithm inputs and six
baseline source pins match their freezes. No attribution outcome was inspected.

Run: `20261010-002651_v5_llama31_provenance_validity_v5_llama31_provenance_validity`.

| Arm | CAP correct / readouts | CAP accuracy | Drop from C0 | Gate |
|---|---:|---:|---:|---|
| C0 | 303 / 320 | 94.6875% | — | pass |
| Ordinary KV | 285 / 320 | 89.0625% | 5.625 percentage points | fail |
| Conflict KV | 287 / 320 | 89.6875% | 5.000 percentage points | pass |

The 320 CAP readouts are repeated measurements within 80 episodes, not 320
independent observations. The sole failure exceeds the frozen five-point limit
by 0.625 points. The conflict arm's stored floating-point difference
`0.050000000000000044` is correctly accepted within numerical tolerance.

All format checks and access gates pass. Donor-own rule access gain is
3.440787816 (one-sided 95% episode-bootstrap lower bound 2.761912112); donor-Robin
content specificity is 11.980521452 (lower bound 10.948722578). Both word-access
diagnostics are also positive. This failure does not establish absence of
information transmission or any attribution effect: attribution outcomes are
not collected by this validity stage.

The backup observer verified 221 files before shutdown. Root independently
rehashed that exact SD-card inventory after shutdown, reproducing inventory
SHA256 `20b15fd5a219403670d7fb38c04105cb708a5f5a41795e1454e213d31be2e619`.
The provider subsequently confirmed actual status `exited` and intended/current/
next state `stopped`. Connection refusal was therefore not treated as proof of
an uncontrolled outage. Credentials, connection metadata and execution receipts
remain outside the repository.

## Frozen consequence

Do not launch Llama provenance N600, change the threshold, reselect settings or
retry the same scientific gate. Mark its confirmatory comparisons unavailable,
retaining the prespecified multiplicity family sizes. A new Llama study would
require a new prospective PI decision.

Qwen provenance and Llama STATIC remain independently approved under their own
frozen gates and the unchanged cumulative USD 60 budget. Continuation requires
the same-instance recovery checks, live local and fresh remote guards, verified
backup and a remaining-package cost forecast. This is mechanical application of
the existing protocol, not a revised research decision.
