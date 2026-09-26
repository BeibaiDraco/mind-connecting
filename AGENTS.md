# AGENTS.md — Project governance and collaboration rules

Every agent and every new session reads this file before starting work. All code in this project is written by agents, and the project is governed as a fast, lean, small research project: few rules, but they must be followed.

## 0. The project in one sentence

Connect two instances of the same LLM (Qwen3-4B-Instruct-2507) directly at the level of internal state, and test whether they can still tell which content is "mine" and which is "its", and whether what matters is "the other side responds" or "the content the signal carries". The research is motivated by the brain-bridging experiment envisioned by the PI.

## 1. Start and end of every session

**Start:**
1. Read `STATUS.md` for the current stage, next steps and blockers.
2. Read this file.
3. Run `git status` and `git log --oneline -15`.
4. Read the last 10 entries of `decision_log.md`.
5. Read the sections of `docs/protocol/EXPERIMENT_DESIGN.md` relevant to the task at hand.

**End, or at each milestone:**
1. Run the offline tests (`pytest -m "not gpu"`).
2. Update `STATUS.md`: what was done, next steps, blockers, time of update.
3. Append any research decision to `decision_log.md`; append only, never edit old entries.
4. Commit according to Section 4.

## 2. Roles and coordination

| Role | Held by | Responsibilities |
|---|---|---|
| Principal investigator (PI) | Draco (Yunlong) Xu | Sets the research questions and makes all research decisions; carries out actions that cost money or face outward |
| Agent | Claude Code, Codex | **Both may write code and both may review.** Core engines (runtime, bridge) should preferably be reviewed by the agent that did not write them. Review conclusions go into a new file under `docs/reviews/` |

The same rules apply whoever takes over a new session.

**Coordination rules (both agents share one working directory on this machine):**
1. **Claim**: before starting, add a row to the "In progress" table in `STATUS.md` (agent, task, files involved, time) and commit.
2. **Do not touch the other agent's files**: do not modify files the other agent has claimed. If a change is needed, leave a message in STATUS or ask the PI to coordinate.
3. **Release**: when done, run the tests, commit, then remove the row from the "In progress" table.
4. **Commit promptly**: do not leave uncommitted changes piling up in the working directory for long.

## 3. Sources of truth (in this order when they conflict)

1. `decision_log.md`: research decisions.
2. Protocols: `docs/protocol/EXPERIMENT_DESIGN.md` (v1, frozen as `protocol-v1`); `docs/protocol/PROTOCOL_V2.md` (follow-up studies A–E, frozen as `protocol-v2`); `docs/protocol/PROTOCOL_V3.md` (B′, A′, T3, frozen as `protocol-v3`). A frozen protocol is never changed; a new version is written instead.
3. `STATUS.md`: current state.
4. Code and `configs/`.

`docs/background/` and `docs/reviews/` are historical records and read only. Relative paths in them may still be the paths from before the reorganization. All documents were translated from Chinese to English on 2026-09-25 for the public release, with content otherwise unchanged.

## 4. Git rules

- **Language**: everything in the repository is in English: code, comments, documents, `STATUS.md`, `decision_log.md` and commit messages. Chinese is used only in conversation with the PI.
- Use a single branch, `main`. Commit in small steps; the offline tests must pass before every commit. Agents may commit at milestones on their own (the PI has delegated git management). Force-pushing and rewriting pushed history are forbidden.
- Commit messages take the form `<scope>: <what was done>`, with scope one of: runtime, bridge, conditions, tasks, readouts, analysis, run, config, docs, chore. Do not add `Co-Authored-By` lines for AI agents; the repository will be public, and AI contributions are disclosed in the paper's AI use statement.
- **Never commit**: `results/`, model weights, `materials/tokenizer/`, secrets and tokens, `.venv/`, `scratch/`.
- Tags:

  | Tag | Meaning |
  |---|---|
  | `design-v0.5` | Design before implementation |
  | `code-v0` | First code that runs end to end |
  | `protocol-v1` | Protocol frozen before the formal experiment |
  | `results-<stage>` | Key result milestones |

  The tags created before 2026-09-25 live in the archived development history (see `docs/protocol/README.md`); the public repository starts from a single commit made on that date.

- **Freezing a protocol**:
  1. Create the `protocol-v1` tag and write `docs/protocol/FREEZE_protocol_v1.txt`, containing the SHA256 of the key files and configurations and the git commit.
  2. Any later change to the protocol goes into a new version file, with an entry in the decision log. Old files are not changed.
- **Remote**: private GitHub repository `BeibaiDraco/mind-connecting`; `gh` on this machine is logged in. Code is synced to the GPU machine with rsync, and no GitHub credentials are kept on the GPU machine. Before pushing, confirm that no large files or secrets are included.

## 5. Research discipline

Details are in the protocols.

1. Do not train model weights or any interface; use one model only and do not switch models.
2. Selectors read only ACC, CAP and format; M, U or "borrowed intent" results must not be used to choose parameters or prompts. Only after the parameters are frozen does a separate step use the paired variance of M to set N.
3. Episodes used for calibration, pilots and the formal experiment do not overlap. The protocol must be frozen before the formal experiment.
4. Results are appended only, never overwritten. Failed trials are kept too, with the reason recorded. Missing values are never filled with 0.
5. The statistical unit is the episode. Sides A/B, tokens, orderings and measurement branches are not independent samples.
6. Every citation in the paper is checked against the original; the paper must include an "AI use statement" section.
7. Make no claims about consciousness, the number of subjects, or phase transitions.
8. Interpolated writes and KV sharing belong to v2 and are out of scope for v1. When the code reaches either branch, it raises an explicit "contract not implemented" error.

## 6. Code and experiment conventions

- **Directories**:
  - `src/mb/`: the package.
  - `tests/`: tests.
  - `configs/`: one YAML file per stage.
  - `scripts/`: GPU environment and entry-point scripts.
  - `materials/`: local materials; the tokenizer is not tracked in git.
  - `results/`: results, not tracked in git.
  - `docs/`: documentation.
- **Modules**:

  | File | Contents | Protocol section |
  |---|---|---|
  | `tasks.py` | Materials, templates, questions, donor variants, CAP item bank | §3, §4, §7 |
  | `readouts.py` | Pure scoring | §8 |
  | `analyze.py` | Statistics and plotting | §9 |
  | `runtime.py` | Two-instance runtime, snapshots and branches | §5 |
  | `bridge.py` | Hooks, normalization, writes, calibration | §6 |
  | `conditions.py` | Maps condition names to donor, gain, transform and configuration identity | §7 |
  | `run.py` | Scheduling, persistence, resume, gates and selector post-processing | §10 |
  | `ledger.py` | Torch-free record shards, resume identity, completeness checks | §10 |

- **Environment**:
  - Python 3.12; `transformers==4.57.1`, `tokenizers==0.22.1`.
  - Model revision: `cdbee75f17c01a7cc42f958dc650907174af0554`.
  - Locally (Mac) only offline work is done: generators, template tokenization, scoring, statistics. **Do not install torch and do not run the model.** Anything involving the model runs on a rented GPU with the 4B model.
  - Local environment:
    ```bash
    uv venv --python 3.12 .venv
    uv pip install --python .venv/bin/python -r requirements.txt -e .
    ```
    Then run the offline tests with `.venv/bin/pytest -m "not gpu"`.
  - The tokenizer lives in `materials/tokenizer/` and is not tracked. In a fresh clone, run `python scripts/fetch_tokenizer.py` to download it and check its hashes against `materials/tokenizer_manifest.json`.
- **Location of large data**:
  - Large local files live on the VERBATIM SD card: `/Volumes/VERBATIM SD/mind-connecting-data/`. `data` in the repository is a symlink to it and is not tracked.
  - Code finds the data root through the environment variable `MB_DATA_ROOT` and falls back to `results/` inside the repository when it is not set.
  - When the SD card is not mounted, scripts must exit with an error rather than silently write elsewhere.
  - The SD card is ExFAT. Use `--no-perms --no-owner --no-group --exclude '._*'` with rsync.
  - Results on the GPU machine are regularly rsynced back to the SD card.
- **Runs**:
  - Each run gets a `run_id` of the form `YYYYMMDD-HHMMSS_<stage>_<tag>`; smoke runs with `--limit N` get the suffix `-smokeN`.
  - `results/<run_id>/` contains:
    - Written once at creation and never changed: `config.yaml` (the input as given), `identity.json` (the fully resolved configuration, calibration path and hash, template/item-bank/tokenizer/source hashes), `manifest.json` (git, software versions, GPU, whether it is a smoke run).
    - Append only: `records/attempt-NNN.jsonl` (a new shard per invocation), `notes.jsonl`, `lang.jsonl`, `ticks.jsonl`, `ticks/*.npz` (per-tick C/R logs), `log.txt`, `resume_log.jsonl`.
    - Derived state (recomputable): `completeness.json`, `run_status.json`, and gate/selection outputs.
  - Resume: `--resume RUN_DIR` first recomputes the identity and refuses, before writing any file, if it differs from `identity.json`; if the source code changed, `--allow-code-change` is required and is recorded. Only trials without an `ok` record are rerun; a failed trial is retried once automatically and, if it fails again, stays missing and is not imputed.
  - Gates and selections give usable conclusions (`consumable: true`) only on complete, non-smoke runs; `calibration: latest` never selects a smoke or incomplete calibration.
  - Existing runs are never overwritten; failed runs are kept as well.
- **Tests**: use pytest. The offline tests must pass at all times; tests that need a GPU are marked `@pytest.mark.gpu`.
- **Style**: use type annotations; keep functions small; comments explain only "why"; do not introduce heavy frameworks.

## 7. Communicating with the PI

- Use plain Chinese with little jargon. For anything the PI must decide, give a recommended option and the reason.
- Research-related changes must be put to the PI first, including changes to questions, metrics or parameter-selection rules, switching models, and training. Pure engineering details are decided by the agent and noted in STATUS or the commit message.
- Actions that cost money or face outward (renting GPUs, creating remote repositories, publishing) are carried out by the PI, or only with the PI's explicit consent.
