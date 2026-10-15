# V6 bounded engineering execution review — 2026-10-14

Reviewer: Codex independent agent `v6_benchmark_review`.

## Scope and authority

This is a new review of the dedicated private benchmark dispatch. It does not
amend the earlier implementation review or any scientific freeze. The latest
decision-log entry records the PI's explicit incremental USD8, maximum four-hour
lifecycle allowance inside the original cumulative USD100 ceiling, retaining
hourly USD1.60, prior charges and the original full-session deadline. The scope
is the prepared engineering comparison only; scientific baseline, calibration,
validation and formal collection remain unauthorized for this dispatch.

Reviewed private files are `benchmark_controller.py`, `benchmark_remote.py` and
`benchmark_worker.py` under the dedicated benchmark `control-src` directory.
The review also reads their private offline tests, the unchanged provider,
transport, restore, local-guard, remote-control and remote-guard helpers, and the
public benchmark implementation and handoff. Imports and test doubles only are
used locally. This reviewer has made no provider, SSH, paid, model or GPU call,
has not inspected scientific outcomes, and has not modified the author's source
or committed files. The coordinating agent owns the claim and full-suite check.

## Findings raised during review

1. The actual local stop guard must carry the narrowed benchmark deadline, not
   merely the remote process or its caller. The four-hour endpoint includes
   verified stop, so shutdown and evidence-copy margins must precede it.
2. The unchanged restore helper's full-phase credit and host-lifetime checks
   are stricter than the benchmark's incremental requirement. They must be
   checked before a paid start; the full phase denotes the original financial
   ceiling and cannot authorize scientific continuation.
3. The inherited launcher probes both boolean command variants. Rejecting its
   `True` probe made the fresh-only adapter unlaunchable. Both variants must
   resolve to the same exact engineering command, with exclusive intent/output
   creation preventing a retry or resume.
4. The public source manifest alone omits the package initializer, support tests
   and tokenizer assets. Pin the complete deployment and verify imported `mb`
   modules resolve into the isolated benchmark repository, avoiding the old
   editable installation.
5. A completion receipt can precede the final worker process exit. Inventory
   sealing must wait for both exact processes to be dead and refuse unclosed
   data. Failed attempts also need sealing and copying when available.
6. Failed or partial transfers were not debited, and success of the first copy
   followed by failure of the second also lost accounting. Conservatively
   reserve every attempted transfer before network activity; do not refund an
   ambiguous attempt.
7. Failure before the output directory exists could prevent the control logs
   from being copied. An ambiguous launch response could leave the local worker
   identifier unset and skip cleanup despite an actual remote launch. Cleanup
   must remain scoped by the original configuration and launch nonce and try to
   preserve available evidence independently of those two cases.
8. Evidence-write errors must not replace the original exception or prevent
   remaining cleanup. Local guard, restore, handoff, transfer and stop receipts
   also need durable SD copies and rehashing after actual stop. The terminal
   journal event must be written before the final journal copy.

## Initial independent verification

The initial private control suite passed **23 tests** independently. It covers
financial/scope refusals, expired validation for stop-only guards, inherited
fresh-only launch behavior and duplicate prevention, arbitrary/scientific
command refusal, actual-stop refusal and separate work/backup/stop deadlines.
All process/provider effects in those tests are mocked. This is not a native
equivalence or live supervision test.

Final disposition and reviewed hashes will be recorded below after the pending
failure/accounting corrections are reviewed. No execution-review acceptance is
issued by this initial entry.

## Closure after corrections

The reviewed revision resolves the findings above:

- The local and remote guards use the same narrowed stop deadline, at least
  300 seconds before the lifecycle endpoint. The worker deadline is another
  900 seconds earlier. The original financial anchor and full-session ceiling
  are unchanged. A fresh exact stopped-instance, price, resource, credit and
  SD-capacity preflight precedes the one exclusive restore intent.
- The inherited process identities, per-instance locks, independent local
  guard, short restore guard and fresh dual-proof handoff remain in use. The
  engineering adapter permits only one exact worker command. A separate thread
  refreshes a 55-second lease at 15-second intervals; cooperative checks add
  protection around native operations, while independent guards cover hung
  calls and process loss. No scientific continuation command is reachable.
- The deployment manifest pins all package modules, both support-test files,
  tokenizer assets and accepted native receipts. The worker rejects imported
  project modules outside the isolated source tree. Nine CUDA structural tests
  must pass without skips before the fixed real-checkpoint comparisons. These
  checks remain unrun by this reviewer.
- There are no live periodic transfers in this bounded comparison. On success
  or failure, exact worker closure precedes inventory sealing. Copies use only
  the sealed file list, try control evidence first, and independently attempt
  available trees. Each attempted tree is fully debited before transfer; an
  ambiguous or failed attempt retains that debit. Only a successful bounded
  transfer statistic can reduce its conservative reservation. A repeated copy
  cannot exceed the 16 GiB payload-transfer bound. The quote reserves both
  transfer directions with additional overhead and uncertainty margin.
- A timed-out launch response still triggers termination scoped by the same
  configuration and launch nonce, even without a returned worker identifier.
  Missing output does not prevent control-log preservation. Evidence-write
  failures do not mask the worker's original exception or skip outer cleanup.
- Data copying precedes actual provider-stop verification. Independent data
  rehashing and private local-control custody then occur locally. The final
  journal includes its terminal event before copying; control receipts and
  logs receive a separate SD manifest and rehash. A last closure marker is
  distinct from the worker's completion receipt. Failure to verify stop or
  evidence cannot produce a successful terminal state.

Independent validation of this revision:

- Private offline controls: **25 passed**. Added tests exercise failed-copy
  precharging, refusal of a repeat beyond the cap, and inventory preservation
  when a child failed before creating output.
- A separate mocked end-to-end controller exercise injected an ambiguous launch
  timeout. It verified termination with the unknown worker identifier but
  original scoped request, followed by sealing, copying, actual-stop handling
  and local-control rehashing. The terminal remained unsuccessful, and the
  handoff and terminal journal event were preserved in the temporary backup.
  All provider, SSH, guard, thread and process-start effects were replaced by
  inert test doubles.
- The inherited remote-control, remote-guard and financial-source hashes match
  the existing accepted-stage pins. No paid or model action was performed.

Reviewed SHA256 values:

| Private control file | SHA256 |
|---|---|
| `benchmark_controller.py` | `f569d7a5d15526f87473a7187e5a971176ca7176d6f1fc6a964c8467b7a3d1dc` |
| `benchmark_remote.py` | `60b5b61468f4a575c3f05298e87aedbe814ede13b092fcddf848f2fdcceb0922` |
| `benchmark_worker.py` | `c80e36e8d16a9157b0d241f15410fb6b376ec1b9ec0173e56d1f7eaa6eaa77fa` |
| `test_benchmark_controls.py` | `b854b7c091923ed26e2abb264cd8c769c45d5e954b0c62f3a39ab22dc1ce25c6` |

**Disposition:** no unresolved implementation blocker in this reviewed private
dispatch. A private review receipt binds precisely the three executable control
hashes. Before execution, the author must rebuild the inert deployment to match
these bytes while preserving the earlier package, pass the actual fresh
preflight, and establish the live guards and handoff. The code acceptance does
not certify current provider state, available credit, native equality, speed,
complete measured cost, or successful backup/stop. It adds no authority beyond
the PI's explicit engineering-only USD8/four-hour exception.

After actual stop, verify the exact local guard consumes its abort and retires,
retaining its final stopped receipt. In an emergency shutdown or inaccessible
disk, evidence may remain only on the retained remote disk; do not claim a
verified SD backup or restore merely to retrieve it without a valid remaining
boundary. Hardware measurement and any later research decision remain separate.
The coordinating agent owns the full offline-suite milestone and repository
commit; this reviewer made no commit.

## Final local-guard retirement follow-up

The author added a bounded, post-stop retirement check before copying the final
private protection receipts. It reads the original ready-process identity,
waits at most 45 seconds without sending any signal, and requires both process
absence and the guard's verified stopped receipt. A live process, changed/reused
identity, missing readiness identity or missing stopped receipt cannot satisfy
the check. Overall success now also requires verified local-guard retirement.
The initially permissive missing-readiness branch was corrected to fail closed.

The private suite again passes **25 tests**. Separate independent tests, with
process inspection and clock waits mocked, confirmed refusal for missing
readiness, a live guard, a reused process identity and exit without a verified
receipt; exit with the original stopped receipt passes. No real process was
inspected or signaled by these tests, and no provider/model action occurred.

This narrow follow-up supersedes only the controller hash above:

| File | Final SHA256 |
|---|---|
| `benchmark_controller.py` | `d34a67cb0df4c0107759efa4ed5d3356d8d3d3dac81528196b22dd155241ce73` |
| `benchmark_remote.py` | `60b5b61468f4a575c3f05298e87aedbe814ede13b092fcddf848f2fdcceb0922` |
| `benchmark_worker.py` | `c80e36e8d16a9157b0d241f15410fb6b376ec1b9ec0173e56d1f7eaa6eaa77fa` |

The prior private acceptance receipt is preserved as
`execution_review_pre_retirement.json`; a new `execution_review.json` binds these
three final hashes. The author also reports successful inert validation of the
repacked deployment against the original cumulative anchor, all deployed file
pins and both accepted native identities. That dry validation is not a provider
state check. The accepted code-review disposition and all fresh preflight/live
execution conditions remain unchanged.
