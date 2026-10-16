# V6 pre-model connection recovery review — 2026-10-16

The single newly authorized A100 80GB rental was created at 15:25:03 UTC,
at USD1.29962963/hour including the quoted 700GB disk. The first commissioning
controller failed its SSH host-key scan before deployment or model setup.
Provider actual stop, local guard retirement and the rehashed local-control
backup were confirmed. No model was run. The original failure remains intact;
its evidence does not establish the underlying reason for the empty/failed scan.

A separate recovery copy allows one start of that exact unused instance, with
fresh protection before the paid API call. It contains no create or destroy
operation. The original creation start, USD8 incremental limit, cumulative
USD100 limit and lifecycle deadline of 19:25:03 UTC remain unchanged. Time spent
stopped is not credited. The original unused-host evidence, exact binding,
financial anchor and backups are checked before restoration.

Only the local connection controller changed. A bounded readiness check retains
private scan diagnostics, validates the expected host/port and key type, then
verifies the authenticated container identity. Readiness transport failures may
be observed within that bounded window; a wrong identity fails immediately.
No model attempt, scientific setting, package source, remote control or deployed
bundle changed. This is first model commissioning after a connection failure,
not a model retry or a second rental.

Independent reviewer `/root/v6_benchmark_review` accepted the recovery controller
and independently ran 40 private offline checks, six pure key-scan boundary
checks, and AST checks confirming one start call with no create/destroy calls.
All 68 package source pins, deployed controls and original failure/authority
receipts matched. The accepted controller SHA256 is
`8056f820cfbb23dff0e6fe4c2897e1dcc76c5367493165913a756501b4f3bdeb`.

This review does not certify CUDA correctness, speed, numerical scientific
adoption, or successful future closure. Both models' engineering gates and
final evidence/actual-stop checks remain required. The unrelated account
instance is excluded, and the historical 61-file backup gap remains unresolved.
