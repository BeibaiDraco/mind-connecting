#!/usr/bin/env bash
# Protocol v3 pilots from a separate checkout, started only after the frozen v2 stages finish.
#   bash scripts/run_v3_pilots.sh V2_LOG [LOG]      (run from the v3 checkout; use nohup)
# The v3 checkout shares the v2 checkout's venv; PYTHONPATH makes it import its own src/.
# GPU/CPU tests run first on the new code; any failure stops the chain before a pilot starts.
set -uo pipefail
cd "$(dirname "$0")/.."
V2_LOG=$1
LOG=${2:-/workspace/v3_pilots.log}
PY=/workspace/mind-connecting/.venv/bin/python
export PYTHONPATH="$PWD/src"
source /workspace/mind-connecting/.mb_env
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
until grep -qE "ALL DONE|ABORT" "$V2_LOG" 2>/dev/null && ! pgrep -f "mb.run" > /dev/null; do sleep 30; done
echo "[$(stamp)] v2 finished; testing v3 code at $(git rev-parse --short HEAD 2>/dev/null || echo '?')" >> "$LOG"
if ! $PY -m pytest -q -m "not gpu" >> "$LOG" 2>&1 || ! $PY -m pytest -q -m gpu >> "$LOG" 2>&1; then
  echo "[$(stamp)] ABORT: tests failed" >> "$LOG"
  exit 1
fi
for cfg in configs/v3/s_static_a.yaml configs/v3/s_live.yaml configs/v3/sig_t3.yaml; do
  echo "[$(stamp)] START $cfg" >> "$LOG"
  $PY -m mb.run "$cfg" >> "$LOG" 2>&1
  echo "[$(stamp)] END $cfg exit=$?" >> "$LOG"
done
echo "[$(stamp)] ALL DONE" >> "$LOG"
