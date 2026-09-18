#!/usr/bin/env bash
# Перший залив коду на Droplet БЕЗ git remote.
# Usage:
#   ./deploy/docker/rsync-up.sh root@157.230.99.135
#   REMOTE_PATH=/var/www/arctica ./deploy/docker/rsync-up.sh root@IP
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 user@host|ssh-alias"
  exit 1
fi

REMOTE_PATH="${REMOTE_PATH:-/var/www/arctica}"
SSH_IDENTITY="${SSH_IDENTITY:-}"

RSYNC_RSH="ssh"
if [[ -n "$SSH_IDENTITY" && -f "$SSH_IDENTITY" ]]; then
  RSYNC_RSH="ssh -i $SSH_IDENTITY -o IdentitiesOnly=yes"
fi

echo "==> mkdir $TARGET:$REMOTE_PATH"
# shellcheck disable=SC2086
$RSYNC_RSH "$TARGET" "mkdir -p '$REMOTE_PATH'"

echo "==> rsync → $TARGET:$REMOTE_PATH"
# shellcheck disable=SC2086
rsync -avz --delete \
  -e "$RSYNC_RSH" \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'staticfiles/' \
  --exclude 'media/' \
  --exclude 'deploy/data/*.json' \
  --exclude 'deploy/data/*.tar.gz' \
  --exclude 'deploy/data/*.sql' \
  --exclude 'postgres_data/' \
  --exclude '.DS_Store' \
  --exclude 'mockup/' \
  --exclude 'docs/' \
  --exclude 'docker-compose.override.yml' \
  --exclude '*.docx' \
  --exclude '*.pdf' \
  "$ROOT/" "$TARGET:$REMOTE_PATH/"

echo "==> done. On server:"
echo "  ssh $TARGET && cd $REMOTE_PATH"
echo "  bash deploy/docker/install-docker.sh"
echo "  bash deploy/docker/gen-env.sh"
echo "  bash deploy/docker/deploy.sh"
echo "  curl -sf -H 'Host: 157.230.99.135' http://127.0.0.1/healthz/"
echo "  # з Mac: ./deploy/docker/sync-data.sh push $TARGET:$REMOTE_PATH --yes"
