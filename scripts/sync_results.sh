#!/usr/bin/env bash
# Pull results from the GPU machine onto the local VERBATIM SD card (ExFAT-safe flags).
#   scripts/sync_results.sh HOST PORT [REMOTE_DATA_ROOT]
set -euo pipefail
HOST=$1; PORT=$2; REMOTE_DATA=${3:-/workspace/mb-data}
LOCAL="/Volumes/VERBATIM SD/mind-connecting-data/results"
[ -d "$LOCAL" ] || { echo "SD card not mounted: $LOCAL" >&2; exit 1; }
rsync -az --no-perms --no-owner --no-group --exclude '._*' -e "ssh -p $PORT" \
  "root@$HOST:$REMOTE_DATA/results/" "$LOCAL/"
echo "results synced into $LOCAL"
