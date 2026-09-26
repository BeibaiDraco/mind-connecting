#!/usr/bin/env bash
# Run the frozen protocol-v2 confirmatory stages in order on the GPU machine (one process at a time).
#   bash scripts/run_formal_v2.sh [LOG]        (default LOG=/workspace/formal_v2.log; use nohup)
set -uo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
source .mb_env
LOG=${1:-/workspace/formal_v2.log}
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
for cfg in configs/v2/v2_main.yaml configs/v2/v2_main_diag.yaml configs/v2/v2_bal.yaml configs/v2/v2_ext_dose.yaml; do
  [ -f "$cfg" ] || continue
  if ! python scripts/freeze_protocol.py --verify --version v2 >> "$LOG" 2>&1; then
    echo "[$(stamp)] ABORT: freeze verification failed before $cfg" >> "$LOG"
    exit 1
  fi
  echo "[$(stamp)] START $cfg" >> "$LOG"
  python -m mb.run "$cfg" >> "$LOG" 2>&1
  echo "[$(stamp)] END $cfg exit=$?" >> "$LOG"
done
echo "[$(stamp)] ALL DONE" >> "$LOG"
