#!/usr/bin/env bash
# Mac side: mirror GPU results onto the SD card every INTERVAL seconds until the formal driver
# finishes (ALL DONE) or aborts; prints the driver's stage lines on exit.
#   scripts/watch_formal.sh HOST PORT [INTERVAL=1200] [LOG=/workspace/formal.log]
set -uo pipefail
HOST=$1; PORT=$2; INTERVAL=${3:-1200}; LOG=${4:-/workspace/formal.log}
cd "$(dirname "$0")/.."
while true; do
  bash scripts/sync_results.sh "$HOST" "$PORT" >/dev/null 2>&1 || echo "[$(date)] sync failed (will retry)"
  # Stop watching (so the agent wakes up) on completion, abort, or any stage with a non-zero exit.
  status=$(ssh -p "$PORT" -o ConnectTimeout=20 "root@$HOST" "grep -E 'ALL DONE|ABORT|exit=[1-9]' $LOG | tail -1" 2>/dev/null || true)
  if [ -n "$status" ]; then
    bash scripts/sync_results.sh "$HOST" "$PORT" >/dev/null 2>&1 || true
    ssh -p "$PORT" -o ConnectTimeout=20 "root@$HOST" "grep -E 'START|END|ALL DONE|ABORT' $LOG" 2>/dev/null
    exit 0
  fi
  sleep "$INTERVAL"
done
