# V4 engineering checkpoint and independent review

Date: 2026-10-08. Offline implementation checkpoint, not experimental validation.

## Decision and state

The PI approved `docs/protocol/PROTOCOL_V4.md`, Llama 3.1 8B Instruct,
the eight-condition plan (seven unique if K*=K1), fixed N=600 and the
USD 60 total / USD 10 initial acceptance ceilings. Official model access remains
pending. The PI subsequently asked to stop the replacement A100 while applying.
The provider accepted the stop and reported actual_status=exited and
intended_status/cur_state/next_state=stopped. The disk was retained.

Before stopping, an isolated remote Python 3.12 environment was installed with
torch 2.6.0+cu124, Transformers 4.57.1, Tokenizers 0.22.1 and Hugging Face Hub
0.36.0. Dependency consistency, a BF16 matrix operation and SDPA passed on the
A100. These are environment checks, not model or bridge correctness tests.
No model was downloaded or loaded. The installed package list is retained on
the remote disk at `/workspace/mb-setup/replication-environment.txt`.

## Implemented

- Pinned explicit model profiles; actual asset size/SHA and architecture checks;
  profile-specific labels, stop tokens, padding and native conversation assembly.
  Llama revision is `0e9e39f249a16976918f6564b8830bc894c89659`.
  Qwen's legacy serialization and condition hashes retain regression coverage.
- A credential-free asset-fetch interface using the official pinned repository.
  Small assets must pass their native tokenizer contract before installation;
  optional weight downloads require the explicit remote Linux GPU mode.
  Actual gated assets have not been fetched or certified.
- Model and tokenizer identity through run preparation, calibration, records and
  resume. Source and calibration blob hashes are checked before writing a run.
- One retained reflection state per chunk/condition family for FULL/RF branches.
  Snapshot hashes cover state/cache fields and reject changed states on retry or
  resume; no whole-run collection of GPU snapshots is retained.
- Side-specific baseline gates, access-only KV/STATIC selection, content-validity
  checks, and fixed five-primary/four-secondary multiplicity families. Unavailable
  primary comparisons retain p=1 for adjustment without imputed observations.
- Staged config generation with raw-record completeness and selection recomputation,
  pinned dependency evidence, exact v1 materials and role/calibration checks.
  Semantic fingerprints exclude episode IDs and are checked across all seven new
  draws and prior configured Qwen splits. No actual v4 config was generated.
- Separate immutable algorithm, selected-settings and formal freeze support.
  No v4 manifest or tag was created; real verified assets are required first.

## Independent review and corrections

The runner author independently reviewed the model/chat/runtime implementation;
the adapter author independently reviewed v4 selection/config provenance. The
coordinator reviewed runtime changes, pure analysis and freeze membership.
Corrections made before this checkpoint:

1. Restrict the explicit-profile dimension guard so legacy D=16 fake-runner tests
   remain usable on a torch-equipped host; real Engine architecture checks remain.
2. Require hashes for every optional tokenizer file that can affect loading,
   including special token maps, added tokens and external chat templates.
3. Require a passing strength selection before generating STATIC matching.
4. Recompute source decisions from complete raw access records and bind formal
   settings to the exact dependencies, roles, arms and calibration used by validity.
5. Reject balanced-material inputs in this replication, which fixes v1 materials.
6. Include asset-fetch and GPU environment setup scripts in the algorithm freeze.

The identified paths were rechecked. No remaining blocker was found within this
offline review scope. The full offline suite and targeted boundary tests pass;
the exact checkpoint test count is recorded in STATUS.md. Local torch remains
absent. Skipped torch/GPU tests must not be represented as passing model tests.

## Required before experiments

1. Obtain official access, sync committed code to the prepared remote checkout and
   install the project in its isolated environment, then fetch pinned real assets and validate the native
   tokenizer/template, contextual labels and all end tokens.
2. Add a Llama-specific or parameterized GPU acceptance entry point. The existing
   `tests/test_runtime.py` fixture still loads Qwen by default, so invoking the old
   generic GPU suite is not a Llama acceptance test. Run the new real-BF16 snapshot
   test on the GPU host as well as donor isolation, zero-weight, mask, snapshot,
   branch and readout tests on the approved model.
3. Prepare the stage chain, budget accounting, stop-on-error behavior, result sync
   and actual provider shutdown supervision. Confirm the SD card mount first.
4. Complete the four-episode smoke, including measured throughput and memory;
   establish STATIC/control timing once calibration is available. Keep smoke
   attribution outputs unavailable for parameter tuning.
5. Freeze the approved algorithm/assets before pilots, selected settings before
   independent validity, and the final inputs before N=600. Continue only through
   the approved gates and remaining budget; do not restart merely to await access.

Frozen v1-v3, manuscript figures and numerical results were not changed.
