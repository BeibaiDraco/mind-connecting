#!/usr/bin/env bash
# Run the frozen formal stages in order on the GPU machine (protocol-v1).
#   bash scripts/run_formal.sh [LOG]        (default LOG=/workspace/formal.log; use nohup)
# Every stage first re-verifies the freeze manifest; a stage that fails is logged and the next
# one still runs. A crashed stage can be continued with: python -m mb.run CONFIG --resume RUN_DIR
set -uo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
source .mb_env
LOG=${1:-/workspace/formal.log}
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
for stage in main main_diag ext_layers ext_masks; do
  if ! python scripts/freeze_protocol.py --verify >> "$LOG" 2>&1; then
    echo "[$(stamp)] ABORT: freeze verification failed before $stage" >> "$LOG"
    exit 1
  fi
  echo "[$(stamp)] START $stage" >> "$LOG"
  python -m mb.run "configs/$stage.yaml" >> "$LOG" 2>&1
  echo "[$(stamp)] END $stage exit=$?" >> "$LOG"
done
echo "[$(stamp)] ALL DONE" >> "$LOG"
