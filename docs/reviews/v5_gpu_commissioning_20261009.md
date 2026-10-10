# V5 GPU commissioning and engineering review

Date: 2026-10-09 (America/Chicago). Scientific source: `ff2387d90035a110c37e4aeeb69e083543b16500`, local tag `protocol-v5`.

The PI explicitly approved the implemented v5 gates, fixed formal N600 and a new USD 60 ceiling, initially USD 10 for correctness and throughput. The 56-file algorithm freeze and model assets are unchanged. No attribution effect or significance determined parameters, continuation or spending.

## Host and failure recovery

The retained host could not restore; its queued start was cancelled and actual stop verified. A replacement A100 SXM4 80 GB with 200 GB disk was commissioned at USD 1.12/hour including allocated disk. Its real instance-local self-stop was independently confirmed through the provider, before restoring the same instance. All setup, idle and restart time remains charged from the original anchor at a conservative USD 1.40/hour plus bandwidth/shutdown reserves.

The first engineering attempt stopped before any model child. The frozen launcher waits 3 seconds for a watchdog, but the measured cold import took 3.934 seconds. Preserved receipts place watchdog readiness 3.290 seconds after launch and 0.204 seconds after the stop worker started. Budget hashes and deadlines matched. The failed attempt remains preserved privately. Independent review confirmed the cause and a narrow remedy: prearm the exact unchanged frozen watchdog, verify its live PID, command, budget hash and deadline for up to 60 seconds, then invoke the original launcher in a fresh control directory. No frozen code or scientific contract was altered.

## Verified acceptance

- Both pinned BF16 weight sets, canonical weight hashes, tokenizer assets and isolated dependency versions were verified.
- Native tests passed: Llama 8/8 and Qwen 17/17; no skipped test qualified as acceptance.
- Each four-episode smoke completed all 768 expected records. Each same-run no-op resume passed the frozen audit, added no successful readout and preserved prior artifacts.
- Each stage and the complete aggregate were independently copied and hash-verified on the mounted SD card before continuation.
- Smoke elapsed time including backup: Llama 304.075 seconds; Qwen 382.604 seconds.

The unchanged repository offline suite passed 361 tests with 5 skips. Private setup, acceptance, prearm, backup, budget handoff, projection and scientific-chain helpers received separate independent reviews and focused tests. Their exact hashes and receipts are in the private execution handoff; credentials and connection coordinates are excluded from Git.

## Budget and continuation

The full maximal package includes 144,480 scientific readouts (122,400 formal), plus 60 calibration episodes and overhead. Each checkpoint uses its own measured smoke time. Shorter question sets retain a full fixed note/reflection-work allowance. Estimated workload before extra margin is 21.19 hours; adding a 1.5 multiplier and one overhead hour gives 32.79 hours. At the conservative rate and original spending anchor, the cumulative forecast including reserves is USD 49.13, below USD 60. This is a planning estimate, not a guaranteed runtime bound. STATIC is unmeasured and requires a timing recheck after calibration/matching.

New independent remote and Mac full-budget guards were proven live before retiring the original setup guardian, the initial stage watchdog and the local replacement guardian by exact process identity. The financial anchor and reserves were preserved. The new scientific controller reserves the other model, STATIC and overhead at each stage, including a second budget check after config generation and before GPU launch.

The Llama provenance baseline is running. The frozen source-backed generators must pass baseline and independent validity before generating/freezing formal N600. Failure retains evidence and requests stop; formal completion requires verified backup and stop. A returned PID alone is not formal startup. Qwen provenance and bounded conditional Llama STATIC remain approved, pending separate execution after verified stop/resume under the original cumulative budget. No uninterrupted unattended completion of all three studies is claimed.
