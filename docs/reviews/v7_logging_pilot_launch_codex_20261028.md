# V7 compact pilot launch

Codex, 2026-10-28. This records an execution launch, not a pilot result. No ownership output was inspected.

## Admission

The PI's existing approval covers only the revised protocol's engineering and pilot stages, SHA256 `608350de020b9392672142916484afc953e846344fe733f00e0b3c3f27479e09`. All prior revised engineering gates passed at `3cf67f8`. After the PI chose answer-position diagnostics and all 80 open-answer prediction positions, implementation `e44a643` passed 1,407 offline tests (11 skipped, one GPU deselection). Claude found no blocking issue and explicitly allowed retaining the previous acceptance and batch 12 for the persistence-only change. Its complete review and SD retention advice are in `v7_logging_review_claude_20261028.md`.

Deployment is `6a5c5a5995d17febba094366b539d4c18f46fc61`. The only package source changed since the accepted engineering deployment is `src/mb/v7_run.py`. All 746 tracked files were hash-verified on the H100. The selected pilot configuration is byte-identical to the earlier admitted configuration: SHA256 `5e78668fb891152760bd3a168111db1f6f15d913e4f4fdcdb039d7dbc83f80d6`, 80 base episodes, batch 12 / 24 rows. There is no acceptance retry, model change or outcome-informed selection.

## Deployment and launch

Vast confirmed retained instance `58065462` running at 16:29:55 UTC, with the existing 120 GB disk and quoted USD 2.6430667/hour including storage. No replacement or additional disk was rented. The initial bundle clone did not select `main`, so the checkout verification failed before model loading. `deployment_attempt_001.json` preserves the failure. Explicitly selecting the only reviewed remote `main` branch recovered this packaging issue without altering any source or old evidence.

After deployment, current disk free was 92,779,536,384 bytes. The container memory limit was 194,660,794,368 bytes with 186,142,720 bytes in use; host available memory was about 386.6 GB. Both exceed the conservative controls' 30 GB disk and 16 GB available-memory checks. The declared retained diagnostic positions require about 9.47 GB of uncompressed span/bank arrays, excluding records/metadata.

The one-shot controller launched at **16:35:57 UTC**, PID 419. Actual pilot collection was confirmed at `/workspace/v7-data-compact/results/20261028-163606_v7_pilot_base_approved`, initially 62 record lines and one tick archive. These are file counts only, not outcome checks. The controller runs the normal V7 collector with one pass and stops immediately after persisting/flushing any failed record. It invokes Claude's existing `scripts/v7_pilot_gates.py` only after all 20,880 records are complete and failure-free. Twelve private synthetic tests cover source/config/receipt/capacity admission, duplicate dispatch, stage failures, gate failure and persistence before failure-stop. No automatic scientific revision or continuation is implemented.

## Backup and follow-up

Private controls: `/private/tmp/mb-v7-compact-pilot-20261028/`. Remote controls/code/data: `/workspace/v7-control-compact`, `/workspace/mind-connecting-v7-compact`, `/workspace/v7-data-compact`. Prelaunch control/source backup was verified on SD at `/Volumes/VERBATIM SD/mind-connecting-data/execution/v7/20261028-compact-pilot/control/` (nine files, 48,760,713 bytes), with sanitized provider lifecycle receipts in `lifecycle/`.

A 10-minute thread heartbeat is active for progress and final byte-verified data/cache backup. It must not inspect ownership outcomes, repeat acceptance, start a second pilot or run variance/formal/generalization stages. Successful collection and instrument gates plus complete SD/cache verification permit stop and destruction under the PI's prior authorization; any failure preserves the instance and evidence for PI direction.

The two preceding V7 SD directories remain intact. Their sizes are about 11.23 GB and 2.45 GB. The second cache backup depends on the first 11.1 GB base archive plus a small delta, and that base archive also holds original failed-attempt evidence. Claude recommends no cleanup now. The PI requested this assessment, not deletion. Its review did not access the SD inventory directly and relied on the supplied dependency facts; no duplicate or safe deletion candidate is claimed.

## Pilot gate source review (Codex)

Reviewed `scripts/v7_pilot_gates.py`, `src/mb/v7_scores.py`, the completeness adapter and `tests/test_v7_pilot_gates.py` against approved section 7 step 2. No blocking finding for this pilot. This was a code review and synthetic-test check, not a pilot-outcome analysis.

The gate selects USE outcomes only in c0, c0_fullinfo, orig_w2 and orig_w2_cf; it reads CAP0/CAP1 in every arm and only scalar label mass for the other closed questions. U_OPEN is skipped. The guarded-record test raises on ownership or translated-arm USE outcome access and passes. USE rates, CAP pooling and paired differences are calculated per episode with exact fractions; the U1/U2/U3 and CAP boundaries match the protocol, including equality. Q1 label mass is averaged per arm. Complete scheduled records and matching arm hashes are required before evaluation, and only an unlimited non-smoke base pilot is consumable. The controller additionally requires every gate to pass before successful closeout; a consumable failed gate cannot trigger continuation. No variance, ownership-estimate or formal-analysis script is invoked. The source remains Claude's unchanged implementation.
