#!/usr/bin/env bash
# Install the replication environment only. No model download or experiment.
set -euo pipefail
cd "$(dirname "$0")/.."

[[ "$(uname -s)" == Linux ]] || { echo 'GPU setup is restricted to the rented Linux host.' >&2; exit 1; }
command -v nvidia-smi >/dev/null
command -v uv >/dev/null
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

if [[ ! -x .venv/bin/python ]]; then
  uv venv --python 3.12 .venv
fi
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'
uv pip install --python .venv/bin/python 'torch==2.6.0' --index-url https://download.pytorch.org/whl/cu124
uv pip install --python .venv/bin/python -r requirements.txt 'huggingface-hub==0.36.0'
uv pip check --python .venv/bin/python

.venv/bin/python - <<'PY'
import json
import torch
import tokenizers
import transformers

assert torch.__version__ == '2.6.0+cu124', torch.__version__
assert transformers.__version__ == '4.57.1', transformers.__version__
assert tokenizers.__version__ == '0.22.1', tokenizers.__version__
assert torch.cuda.is_available()
assert torch.cuda.is_bf16_supported()
x = torch.ones((16, 16), device='cuda', dtype=torch.bfloat16)
assert bool(torch.isfinite(x @ x).all())
q = torch.ones((1, 2, 8, 16), device='cuda', dtype=torch.bfloat16)
assert bool(torch.isfinite(torch.nn.functional.scaled_dot_product_attention(q, q, q)).all())
torch.cuda.synchronize()
print(json.dumps({'torch': torch.__version__, 'cuda_runtime': torch.version.cuda,
                  'transformers': transformers.__version__, 'tokenizers': tokenizers.__version__,
                  'gpu': torch.cuda.get_device_name(0), 'bf16_check': 'passed',
                  'sdpa_check': 'passed', 'model_loaded': False}))
PY
mkdir -p /workspace/mb-setup
uv pip freeze --python .venv/bin/python > /workspace/mb-setup/replication-environment.txt
echo 'Replication dependencies ready; gated model access and model-specific acceptance checks remain.'
