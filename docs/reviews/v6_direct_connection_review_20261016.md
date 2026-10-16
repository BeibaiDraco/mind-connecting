# V6 direct-connection commissioning review — 2026-10-16

The bounded proxy-readiness recovery also stopped before deployment or any
model call. Its actual provider stop, exact local-guard retirement and all 63
SD control-file hashes were independently verified. Both historical connection
failures remain intact. Their deadlines and costs have not been reset.

A read-only diagnostic using the freshly matched provider record found that
the proxy route returned no SSH host key, while the direct route returned a key
and authenticated the exact container identity. Free disk exceeded 500GiB and
the container-scoped stop capability was available. This identifies a usable
route; it does not explain the provider's proxy failure.

The new inert control copy selects the direct SSH mapping from each fresh
matched provider response. It requires a numeric public unicast address,
filters port bindings by address family and unspecified/exact interface, and
rejects missing or ambiguous compatible mappings. Real provider metadata had
IPv4 and IPv6 wildcard bindings to the same port; the offline test reproduces
that shape and verifies either list order. Multicast, scoped, loopback,
malformed and wrong-family endpoints are rejected.

Independent reviewer `/root/v6_benchmark_review` accepted the final snapshot
after 57 private offline tests, real-metadata route validation, exact source and
closure comparisons, and AST checks for one start call with no create/destroy
calls. Final controller SHA256:
`d52d6b86f8d951ccc23f70bf93eefff6dd10bd56146cd25ae515bf13c0612621`.
Final private test SHA256:
`8d714d2a15a9e22c6ce6a63d3af9fcca06cac34a37dec7a3f0d4367c81f79365`.
The accepted copy is sealed under
`/private/tmp/mb-v6-execution-20261012/optimization-benchmark-20261016/direct-connection-recovery2/`.

Scope remains the first model engineering trial on the same newly authorized
unused instance, with fresh guards before one restore. Original creation start
15:25:03 UTC, worker deadline 18:40:03 UTC, guard stop 19:20:03 UTC and verified
actual-stop lifecycle deadline 19:25:03 UTC remain fixed. All prior costs,
USD8 incremental/USD100 cumulative limits and the unchanged 68-file package
remain. No model retry, new rental, stopped-time credit, scientific collection,
numerical adoption or unrelated-instance action is authorized by this repair.
Remote/bundle controls are unchanged. CUDA and full-model correctness/speed
remain unmeasured until the actual engineering worker completes.
