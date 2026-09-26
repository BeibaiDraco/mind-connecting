#!/usr/bin/env bash
# One-time setup on the rented GPU machine. Run from the synced repo:
#   bash scripts/setup_gpu.sh
# Creates a Python 3.12 venv with uv, installs a CUDA torch build matching the driver
# (default torch 2.6.0 + cu124, fine for drivers >= 550), the pinned project deps,
# fetches the tokenizer and the pinned model revision, then runs both test suites.
set -euo pipefail
cd "$(dirname "$0")/.."

PY_VERSION="${PY_VERSION:-3.12}"
TORCH_VERSION="${TORCH_VERSION:-2.6.0}"
TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu124}"
export MB_DATA_ROOT="${MB_DATA_ROOT:-/workspace/mb-data}"
export HF_HOME="${HF_HOME:-/workspace/.hf_home}"

nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
command -v uv >/dev/null || { echo "uv not found; install it first (pip install uv)" >&2; exit 1; }
[ -x .venv/bin/python ] || uv venv --python "$PY_VERSION" .venv
uv pip install --python .venv/bin/python "torch==${TORCH_VERSION}" --index-url "$TORCH_INDEX"
uv pip install --python .venv/bin/python -r requirements.txt -e .
.venv/bin/python -c "import torch; assert torch.cuda.is_available(); print('torch', torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0))"
.venv/bin/python scripts/fetch_tokenizer.py
.venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
path = snapshot_download("Qwen/Qwen3-4B-Instruct-2507", revision="cdbee75f17c01a7cc42f958dc650907174af0554",
                         allow_patterns=["*.json", "*.safetensors", "*.txt"])
print("model files at", path)
PY
mkdir -p "$MB_DATA_ROOT"
printf 'export MB_DATA_ROOT=%s\nexport HF_HOME=%s\n' "$MB_DATA_ROOT" "$HF_HOME" > .mb_env
.venv/bin/pytest -q -m "not gpu"
.venv/bin/pytest -q -m gpu
echo "setup ok; next: source .venv/bin/activate && source .mb_env && python -m mb.run configs/g1.yaml --limit 2"
