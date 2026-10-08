# V4 authenticated launch readiness

Date: 2026-10-08. This is an engineering checkpoint, not a model-validation or research result.

## Verified assets and materials

Official access to the exact approved `meta-llama/Llama-3.1-8B-Instruct`
revision `0e9e39f249a16976918f6564b8830bc894c89659` was verified with an
authenticated small-file download. The complete tokenizer/configuration assets
were hashed and installed separately from the original Qwen assets. Credentials
remain outside the repository; no model weights were downloaded to the Mac.

The official tokenizer declares some control tokens through `added_tokens_decoder`
without listing them in `all_special_ids`. The validation check was corrected to
accept their explicit special designation while still requiring exact one-token
encoding, decoding and ID agreement. The official asset files were not edited.
The complete stop set is 128001, 128008 and 128009; padding is 128001, BOS is
128000, and answer labels are 16, 17, 18 and 19.

An independent CPU-only check covered all 884 prescribed v4 episodes, both A/B
sides and 35,360 questions. Full native and incremental message serialization,
TAG/UNTAG consecutive-user messages, CF receiver-input invariance and 28,768
contextual label appends passed. The private prefix is always 287 tokens.
START/START_R, NOW/NOW_R and WORD/WORD_R have equal paired lengths of 50, 48 and
40 tokens. CAP lengths vary by item from 40 to 49; real GPU padding checks remain
necessary.

## Acceptance and supervision

`scripts/check_llama_acceptance.py` runs exactly eight dedicated Llama GPU tests
using already-cached weights with network access disabled. It records source and
asset hashes, versions, per-test evidence and peak GPU memory. Missing tests,
skips and any failed phase cannot pass. Tests cover full stop-token handling,
no-link equality, inactive attention and zero weighting, donor isolation and
previous-tick visibility, padding/positions/cache/causality, partner masks and
scope, C48 FULL/RF branch isolation and BF16 snapshot hashing. Numerical bounds
are fixed before execution. The runner owner independently reviewed the harness.

`scripts/supervise_v4.py` enforces cumulative estimated costs, bounded process
lifetimes, explicit stage evidence and a mandatory provider-stop callback. Initial
acceptance permits engineering, smoke and baseline; later stages require a measured
remaining-work estimate. Success and failure both request shutdown. Actual provider
state must be checked separately. Prior setup/idle costs and bandwidth reserves
must be included; the supervisor is not a provider invoice or protection against
loss of the supervising host.

Independent review corrected a possible miswired result directory: stage, split,
seed, v1 material, post-step, model identity and relevant calibration/asset fields
must agree with the expected stage. Smoke requires four episodes and 480/480
successful readouts. Missing STATIC/route comparisons and null/opposite formal
outcomes do not veto the approved core experiment. Freeze verification remains an
explicit command before scientific stages; the runner does not enforce it itself.

The initial configuration files and non-overlap split manifest were generated.
The algorithm freeze inventory now includes the acceptance and supervision scripts
and their tests. No v4 freeze manifest or tag has been created.

## Provider state and remaining work

The previously stopped A100 returned `resources_unavailable` on two bounded restart
attempts. The queued starts were cancelled and actual_status=exited with
intended_status/cur_state/next_state=stopped was verified. No weights, GPU model
execution, acceptance result or new research outcome exists. Infrastructure IDs,
addresses and account authorization are kept in private task files.

After a usable GPU is available: install/sync the committed checkout, download the
pinned weights into the remote HF cache, run the dedicated correctness suite and
four-episode throughput/memory smoke, verify resume behavior, and establish a
conservative cost projection. Commit engineering fixes before freezing the algorithm;
then run the approved baseline, calibration and selection stages. Freeze selected
settings before independent validity and formal inputs before N=600. Preserve all
failed attempts and verify backups and final provider shutdown.

Final offline test counts are recorded in STATUS.md. Local torch remains absent;
skipped GPU tests do not count as successful model validation.
