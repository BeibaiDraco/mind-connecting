# V7 compact pilot execution closeout — Codex, 2026-10-28

The authorized 80-episode base pilot collected all 20,880 expected records with no failed records. Claude's existing pilot-gate script ran once on the complete run and returned a consumable failure. The controller stopped; no retry, material revision, further model work, variance calculation, formal run or generalization run followed. Instance 58065462 is retained running for PI direction.

## Authority and engineering admission

PI approval covers only protocol section 7 steps 1–2, commit `f978be0`, SHA256 `608350de020b9392672142916484afc953e846344fe733f00e0b3c3f27479e09`. Earlier deployment `3cf67f8` passed all three GPU checkpoint tests, 384 FP32 production-relocation comparisons, R1 timing and all 336 CAP0 runner checks; batch 12 episodes / 24 rows was selected. BF16 remained descriptive. Original failed BF16 evidence is unchanged.

The pilot used deployment `6a5c5a5995d17febba094366b539d4c18f46fc61`, containing the independently reviewed persistence-only change `e44a643`. Closed questions retain the final prediction position; U_OPEN retains all 80 prediction positions. Claude approved retention of the prior engineering admission and batch because model computation was unchanged. The resolved pre-model bundle checkout error remains preserved separately in `deployment_attempt_001.json`.

## Collection and admission status

- Run: `20261028-163606_v7_pilot_base_approved`; split `v7_pilot`, 80 base episodes, 14 arms, two rotations.
- Worker dispatched once at 16:35:57 UTC. Collection succeeded in 16,680.307 seconds (about 4 hours 38 minutes).
- Completeness: 20,880 / 20,880 successful records, zero failed records; 182 tick archives.
- Claude's `scripts/v7_pilot_gates.py` executed once, in 18.085 seconds, and returned `consumable: true`, `all_pass: false`.
- Passed: U2, Q1_cap, Q1_mass. Failed: U1, U3_fact, U3_cf.
- Controller terminal state: `failed`, phase `pilot_gates`, at 21:14:20 UTC; `preserve_instance: true`, `no_further_dispatch: true`.

Only admission booleans, collection counts, operational timing, file metadata and byte hashes were inspected. No ownership answer, START/PROV/DETECT outcome, translated-arm USE outcome or attention value was opened or analyzed. The gate script's existing outputs were neither recomputed nor modified. This report records instrument admission, not a scientific result or a diagnosis of the failed assay.

## Backup and lifecycle

SD destination: `/Volumes/VERBATIM SD/mind-connecting-data/execution/v7/20261028-compact-pilot/`. Independent verification succeeded at 21:38:29 UTC: 196 data files / 9,536,799,879 bytes, 53 control files plus their manifest, four tokenizer assets and 28,851 current cache members. The new cache delta contains four changed/new files, compressed to 20,743 bytes; SHA256 `c534c952d6496558291565ab2cdd9bc2d9ad76adfcdcf3629f40fcb4debdad84`. Five local control/helper files were separately copied and verified.

Evidence: `terminal_sd_verification.json` (SHA256 `01f42bcd40ae0a3f6170510537e9a2a83cd1a7ba5ba1026d85fb8fb33d77698c`), `terminal_backup_completed.json`, `local_closeout_controls_verification.json`, the `remote-control/terminal_*manifest.json` files, cache-delta receipt and lifecycle receipts. The terminal control manifest is pinned by SHA256 `c0d534ef86ae9b9bfb5107add3db3976623a0bd117c8c5b418df25c91fd3ade7`.

All nine incremental transfers were independently hash-verified before terminal synchronization. The final verification checks the complete data/control file set, file sizes and SHA256 values, tokenizer assets, every member of the original/prior/new cache archives, and exact coverage of the current cache. Original engineering and relocation backups remain required and untouched; the current backup depends on their cache archives. No cloud or SD data was deleted.

A sanitized Vast receipt at 21:39:04 UTC confirms instance `58065462` remains running with its disk and all evidence retained. No stop or destroy request was sent after this failure. The provider quotes approximately USD 2.6431 per hour including storage; further lifecycle action awaits PI direction.

## Validation and next step

The full offline suite passes: 1407 passed, 11 skipped, one GPU deselection. No additional model test or pilot-gate execution was performed during closeout.

No code, protocol, material or gate threshold changed during collection or closeout. Historical reviews and failure records remain immutable. Further research work is blocked on PI direction; no remedy or new run is proposed as already authorized. Codex releases only its completed V7 execution claim after verified backup and documentation. The monitoring heartbeat is removed once this closeout is recorded.
