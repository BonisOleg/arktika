#!/usr/bin/env bash
# Local catalog/CMS/orders → Postgres volume on the Droplet.
#
#   ./deploy/docker/sync-data.sh export
#   ./deploy/docker/sync-data.sh import --yes
#   ./deploy/docker/sync-data.sh push root@157.230.99.135:/var/www/arctica --yes
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DATA_DIR="$ROOT/deploy/data"
DUMP_JSON="$DATA_DIR/arctica_dump.json"
MEDIA_TAR="$DATA_DIR/media.tar.gz"
DUMP_APPS=(
  accounts
  catalog
  content
  commerce
  shipping
)

compose_cmd() {
  export COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"
  docker compose "$@"
}

local_python() {
  if [ -x "$ROOT/venv/bin/python3" ]; then
    echo "$ROOT/venv/bin/python3"
  elif [ -x "$ROOT/.venv/bin/python3" ]; then
    echo "$ROOT/.venv/bin/python3"
  else
    echo "python3"
  fi
}

cmd_export() {
  mkdir -p "$DATA_DIR"
  local py
  py="$(local_python)"
  echo "==> dumpdata → $DUMP_JSON (${DUMP_APPS[*]})"
  DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.develop}" \
  POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}" \
    "$py" manage.py dumpdata "${DUMP_APPS[@]}" \
    --natural-foreign --natural-primary \
    --indent 2 \
    -o "$DUMP_JSON"
  echo "==> media → $MEDIA_TAR"
  if [ -d "$ROOT/media" ] && [ "$(find "$ROOT/media" -type f ! -name '.gitkeep' 2>/dev/null | head -1)" ]; then
    tar -C "$ROOT/media" -czf "$MEDIA_TAR" .
  else
    echo "WARN: media/ empty — empty archive"
    tar -czf "$MEDIA_TAR" -T /dev/null
  fi
  echo "==> export OK"
  ls -lh "$DUMP_JSON" "$MEDIA_TAR"
}

confirm_replace() {
  if [ "${1:-}" = "--yes" ] || [ "${1:-}" = "-y" ]; then
    return 0
  fi
  echo "Import FLUSHES Postgres (catalog/CMS/orders). Run BEFORE createsuperuser if dump has users."
  read -r -p "Continue? [y/N] " ans
  case "$ans" in
    y|Y|yes|YES) ;;
    *) echo "Cancelled"; exit 1 ;;
  esac
}

cmd_import() {
  confirm_replace "${1:-}"
  if [ ! -f "$DUMP_JSON" ]; then
    echo "FATAL: missing $DUMP_JSON — run export first"
    exit 1
  fi
  if [ ! -f "$MEDIA_TAR" ]; then
    echo "FATAL: missing $MEDIA_TAR — run export first"
    exit 1
  fi

  echo "==> wait backend /healthz/"
  local i=0
  while [ "$i" -lt 40 ]; do
    if compose_cmd exec -T backend python3 -c \
      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=5)" \
      >/dev/null 2>&1; then
      break
    fi
    i=$((i + 1))
    sleep 3
  done
  if [ "$i" -ge 40 ]; then
    echo "FATAL: backend/healthz not ready"
    compose_cmd logs --tail=40 backend
    exit 1
  fi

  echo "==> flush + loaddata"
  compose_cmd cp "$DUMP_JSON" backend:/tmp/arctica_dump.json
  compose_cmd exec -T backend python3 manage.py flush --noinput
  compose_cmd exec -T backend python3 manage.py loaddata /tmp/arctica_dump.json

  echo "==> reset Postgres sequences"
  compose_cmd exec -T backend sh -c \
    "python3 manage.py sqlsequencereset accounts catalog content commerce shipping 2>/dev/null | python3 manage.py dbshell" \
    || echo "WARN: sqlsequencereset skipped — check next PK inserts"

  echo "==> media → volume"
  compose_cmd exec -T backend mkdir -p /app/media
  compose_cmd cp "$MEDIA_TAR" backend:/tmp/media.tar.gz
  compose_cmd exec -T backend tar -xzf /tmp/media.tar.gz -C /app/media
  compose_cmd exec -T backend rm -f /tmp/arctica_dump.json /tmp/media.tar.gz

  echo "==> import OK"
  echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python3 manage.py createsuperuser"
}

cmd_push() {
  local target="${1:-}"
  local yes_flag="${2:-}"
  if [ -z "$target" ] || [ "$target" = "${target#*:}" ]; then
    echo "Usage: $0 push user@host:/path/to/arctica [--yes]"
    exit 1
  fi
  local host="${target%%:*}"
  local rpath="${target#*:}"
  cmd_export
  echo "==> scp → $host:$rpath/deploy/data/"
  ssh "$host" "mkdir -p '$rpath/deploy/data'"
  scp "$DUMP_JSON" "$MEDIA_TAR" "$host:$rpath/deploy/data/"
  echo "==> remote import"
  ssh "$host" "cd '$rpath' && bash ./deploy/docker/sync-data.sh import ${yes_flag:---yes}"
}

usage() {
  echo "Usage: $0 export | import [--yes] | push user@host:/path [--yes]"
  exit 1
}

case "${1:-}" in
  export) cmd_export ;;
  import) cmd_import "${2:-}" ;;
  push) cmd_push "${2:-}" "${3:-}" ;;
  *) usage ;;
esac
