#!/usr/bin/env bash
# Push the repo (code, configs, docs, .git; no data, venv or tokenizer) to the GPU machine. Excludes
# are anchored at the repo root: an unanchored results/* also dropped docs/results/ and left the
# remote checkout looking dirty to git.
#   scripts/sync_to_gpu.sh HOST PORT [REMOTE_DIR]
set -euo pipefail
HOST=$1; PORT=$2; REMOTE_DIR=${3:-/workspace/mind-connecting}
cd "$(dirname "$0")/.."
rsync -az --delete --no-owner --no-group -e "ssh -p $PORT" \
  --exclude .venv --exclude /data --include /results/.keep --exclude '/results/*' --exclude materials/tokenizer \
  --exclude __pycache__ --exclude .pytest_cache --exclude '._*' --exclude .mb_env --exclude '/*.png' \
  ./ "root@$HOST:$REMOTE_DIR/"
echo "synced to root@$HOST:$REMOTE_DIR"
