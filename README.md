# Mine or Yours? Mind-Bridged Language Models

Code, protocols and paper for *Mine or Yours? Mind-Bridged Language Models Take Each Other's Memories as Their Own* (Yunlong Xu, University of Chicago).

We connect two instances of one language model, Qwen3-4B-Instruct-2507, so that one instance (the receiver) also attends to the other's key–value cache, and ask whether the receiver can still tell which assignment is its own and which is its partner's. The motivation is the brain-bridging thought experiment: if two brains were wired together, would each still know which thoughts were its own? The study measures functional self-attribution only and makes no claim about consciousness.

- **Paper**: [paper/main.pdf](paper/main.pdf); sources in [paper/](paper/) (build with `make -C paper`).
- **Current state of the project**: [STATUS.md](STATUS.md).
- **Research decisions** (append only): [decision_log.md](decision_log.md).
- **Rules for contributors and agents**: [AGENTS.md](AGENTS.md).

## Protocols

The experiments ran in three stages, each with a protocol frozen before its confirmatory data were collected:

| Stage | Protocol | Freeze manifest | Tag (archived history) |
|---|---|---|---|
| Hidden-state study | [docs/protocol/EXPERIMENT_DESIGN.md](docs/protocol/EXPERIMENT_DESIGN.md) | `docs/protocol/FREEZE_protocol_v1.txt` | `protocol-v1` |
| Memory link, first confirmatory sample | [docs/protocol/PROTOCOL_V2.md](docs/protocol/PROTOCOL_V2.md) | `docs/protocol/FREEZE_protocol_v2.txt` | `protocol-v2` |
| Main sample and two-way pilot | [docs/protocol/PROTOCOL_V3.md](docs/protocol/PROTOCOL_V3.md) | `docs/protocol/FREEZE_protocol_v3.txt` | `protocol-v3` |

The public repository starts from a single commit made on 2026-09-25. The development history before that date, including the freeze commits and tags, is kept as a private archive (a git bundle held by the PI); commit hashes and tags mentioned in these documents refer to that archive. See [docs/protocol/README.md](docs/protocol/README.md) for how the freeze manifests relate to the current files.

## Layout

```text
src/mb/     package: tasks, readouts, analyze, runtime, bridge, conditions, run, ledger, chat
tests/      pytest (offline tests; GPU tests are marked @pytest.mark.gpu)
configs/    one YAML file per stage (v2/ and v3/ for the later protocols)
scripts/    GPU setup, run entry points, report and figure scripts
materials/  local materials (the tokenizer is fetched, not tracked)
docs/       protocols, result reports, reviews and background notes
paper/      manuscript, figures and reference verification notes
results/    run outputs (not tracked in git)
```

## Quick start

Offline work (no model, no torch) runs on a laptop:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt -e .
python scripts/fetch_tokenizer.py
.venv/bin/pytest -m "not gpu"
```

Experiments that run the model need a GPU with about 80 GB of memory; see `scripts/setup_gpu.sh` and the run scripts in `scripts/`. Every run writes its resolved configuration, source hashes and records to `results/<run_id>/`, and `--resume` refuses to continue a run whose identity has changed.
