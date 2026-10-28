## Review of the V7 relocation follow-up (read-only, incremental)

Claude (Opus 5.5), 2026-10-28. I read `AGENTS.md`, the current phase and the claim table in `STATUS.md`, and my earlier review of `ce7b635`. I then reviewed only the new additions in `src/mb/v7_relocation.py`, `src/mb/v7_acceptance.py`, `tests/test_v7_relocation.py` and `tests/test_v7_acceptance.py`. The only other source I opened was `load_model`/`State`/`cache_layers` in `runtime.py` (`:152-204`), to check the dtype assumptions. I did not run any tests, model or GPU work. I did not open any outcomes or private caches, and I changed no files. The suite result of 1402 passed, 11 skipped and one GPU deselection is Codex's, not mine.

**Verdict: no blocking issues. Ready for the authorized GPU engineering checks.** These are protocol `608350de020b9392672142916484afc953e846344fe733f00e0b3c3f27479e09`, §7 steps 1–2 only. FP32 is the only gate, BF16 is descriptive only, and there is no ownership analysis. This review does not authorize anything beyond that scope.

### 1. `precision_metadata` (`v7_relocation.py:94-107`): correct
- **The model dtype is enforced.** The set of all parameter dtypes must equal exactly `{float32}` for FP32 or `{bfloat16}` for BF16, and anything else raises.
- **No false failure is expected in BF16.** `load_model` calls `from_pretrained(..., dtype=dtype)` and does not add any extra parameters (`runtime.py:163-170`).
- **It runs before any trace** (`:188`), and its receipt is stored in `relocation_<precision>.json`.
- **The backend settings are recorded, not enforced.** These are TF32 matmul, float32 matmul precision, the attention implementation and the four SDPA flags. That is enough here: the FP32 gate checks the actual tolerances, so a TF32 regression would fail the gate rather than slip through.
  - The attention implementation is the custom `KV_ATTENTION`, so the SDPA flags are context only.
  - The `getattr(..., lambda: None)` fallback keeps the receipt robust across torch versions.

### 2. `check_cache_precision` (`:110-116`): correct, one small limit
- **Both caches are checked.** It covers every K and V tensor of `native` and `reference` (`:196-197`).
- **The check is applied after the donor rows are slice-assigned.** That assignment would quietly cast the offset-prefill tensors to the destination dtype, so the check cannot catch a different dtype in the temporary offset cache itself.
- This does not matter in practice. The offset prefill uses the same model whose parameters were just verified, and `translated` is a copy of the checked `native`. Not blocking.

### 3. Donor-key change guard (`:87-90`): correct, and it closes my earlier P2-a concern
- **What it checks.** Each B row must have at least one layer whose keys are not bit-identical to the native keys.
- **It cannot fire falsely.** Keys include RoPE, and the shift is −L_B with L_B ≥ 1, so every valid slot moves.
- **It closes the vacuous-pass route.** A gate could only pass vacuously if both the B replacement and the translation were no-ops. The guard now catches the replacement half.
- **On its own it is weak** (any one-bit difference satisfies it). That is acceptable: if the reference prefill ignored `position_ids`, the translated and reference traces would differ, so the gate fails in the safe direction.
- **Only the positive case is tested.** No offline test shows the guard raising when the offset cache equals the native cache. The same is true of the A-state and mask-mismatch raises (P3, below).

### 4. Unconditional material reconstruction and the `material_check` phase (`v7_acceptance.py:211-214`): correct
- **The test-only shortcut is gone.** The `if hashes:` branch is removed, and the test stubs `validate_material_compatibility` instead (`test_v7_acceptance.py:70`).
- **Placement is right.** The check runs after the tokenizer loads and before any model loads. It reads the hash-verified copy of `notes.jsonl` in the output directory.
- **Failures are recorded.** A mismatch produces `failed_phase: material_check` with its own duration entry.
- **Cosmetic only:** a missing GPU or a tokenizer load failure is still labelled `fp32_model_load`.

### 5. Exclusive `pilot.yaml` creation (`:258-260`): correct
- **No overwrite is possible.** `open("x")` is used, and the output directory is new anyway (`mkdir(exist_ok=False)`).
- **No pilot can be produced on a failure path.** `pilot.yaml` is still written before `acceptance.json`, but the only code between the two is a hash and a dict.
- The test checks that `pilot.yaml` is absent after an FP32 failure and after a CAP0 failure.

### Non-blocking items (carry-over P3, all optional)
- **Dispatcher check.** The pilot dispatcher should require `acceptance.json` to say `passed: true` and its `pilot_config_sha256` to equal the hash of `pilot.yaml`, rather than relying on `pilot.yaml` existing.
- **Negative offline tests.** Add tests showing that the donor guard, the A-state check and the A-cache check actually raise.
- **Still open from the earlier review:**
  - persist the deltas the engine actually used;
  - record where the worst error occurs when the gate fails;
  - add a local `torch.no_grad()` (callers already wrap these calls in `inference_mode`).

### What only the GPU run can confirm
Everything listed in my earlier review still applies:
- negative `position_ids` work in the HF Qwen3 prefill;
- the actual FP32 errors across all 384 comparisons;
- the deployed protocol and source hashes match;
- memory and timing at batch 12;
- all 336 CAP0 trials complete.

In addition, the BF16 parameter set must turn out to be exactly `{bfloat16}`. I expect it to be, but if not, the run would fail safely at the BF16 descriptive step.

**Final verdict: no blocking issues; ready for the authorized GPU engineering checks within §7 steps 1–2.**
