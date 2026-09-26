#!/usr/bin/env bash
# Run stage configs one after another on the GPU box and stop at the first failure.
#   bash scripts/run_chain.sh LOG CONFIG...          (use nohup)
# Tests run first (RUN_TESTS=0 skips them). mb.run exits non-zero when a stage crashes or ends
# incomplete; the chain then writes ABORT, which scripts/watch_formal.sh stops on, instead of ALL DONE.
# PY picks the interpreter (default .venv/bin/python). A checkout that borrows another checkout's venv
# sets PY and PYTHONPATH=$PWD/src so that it imports its own code; MB_ENV names the data-root env file.
# FREEZE_VERSION=vN re-verifies that protocol's freeze manifest before every stage (formal runs).
set -uo pipefail
cd "$(dirname "$0")/.."
LOG=$1
shift
PY=${PY:-.venv/bin/python}
MB_ENV=${MB_ENV:-.mb_env}
if [ -f "$MB_ENV" ]; then
  # shellcheck disable=SC1090
  source "$MB_ENV"
fi
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
abort() {
  echo "[$(stamp)] ABORT: $1" >> "$LOG"
  exit "${2:-1}"
}
echo "[$(stamp)] chain at $(git rev-parse --short HEAD 2>/dev/null || echo '?'): $*" >> "$LOG"
if [ "${RUN_TESTS:-1}" = 1 ]; then
  "$PY" -m pytest -q -m "not gpu" >> "$LOG" 2>&1 || abort "offline tests failed"
  "$PY" -m pytest -q -m gpu >> "$LOG" 2>&1 || abort "GPU tests failed"
fi
for cfg in "$@"; do
  if [ -n "${FREEZE_VERSION:-}" ]; then
    "$PY" scripts/freeze_protocol.py --verify --version "$FREEZE_VERSION" >> "$LOG" 2>&1 \
      || abort "freeze verification failed before $cfg"
  fi
  echo "[$(stamp)] START $cfg" >> "$LOG"
  "$PY" -m mb.run "$cfg" >> "$LOG" 2>&1
  rc=$?  # read it now: the command substitution in the next echo would reset $?
  echo "[$(stamp)] END $cfg exit=$rc" >> "$LOG"
  [ "$rc" -eq 0 ] || abort "$cfg exit=$rc" "$rc"
done
echo "[$(stamp)] ALL DONE" >> "$LOG"
