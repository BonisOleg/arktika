#!/usr/bin/env bash
# Каталог/CMS/замовлення між локалкою і Droplet.
#
#   ./deploy/docker/sync-data.sh pull-remote arktika:/var/www/arktika
#   ./deploy/docker/sync-data.sh push-pg arctica-prod:/var/www/arctica --yes
#   ./deploy/docker/sync-data.sh export | import [--yes] | push user@host:/path [--yes]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DATA_DIR="$ROOT/deploy/data"
DUMP_JSON="$DATA_DIR/arctica_dump.json"
DUMP_SQL="$DATA_DIR/arctica.sql"
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

split_target() {
  local target="${1:-}"
  if [ -z "$target" ] || [ "$target" = "${target#*:}" ]; then
    echo "Usage: $0 $2 user@host:/path"
    exit 1
  fi
  REMOTE_HOST="${target%%:*}"
  REMOTE_PATH="${target#*:}"
}

cmd_pull_remote() {
  split_target "${1:-}" "pull-remote"
  mkdir -p "$DATA_DIR"
  echo "==> pg_dump $REMOTE_HOST:$REMOTE_PATH → $DUMP_SQL"
  ssh "$REMOTE_HOST" "cd '$REMOTE_PATH' && export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml && docker compose exec -T db pg_dump -U arctica arctica --no-owner --no-acl --clean --if-exists" > "$DUMP_SQL"
  echo "==> media $REMOTE_HOST → $MEDIA_TAR"
  ssh "$REMOTE_HOST" "cd '$REMOTE_PATH' && export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml && docker compose exec -T backend tar -czf - -C /app/media ." > "$MEDIA_TAR"
  echo "==> pull-remote OK"
  ls -lh "$DUMP_SQL" "$MEDIA_TAR"
}

cmd_import_pg() {
  confirm_replace "${1:-}"
  if [ ! -f "$DUMP_SQL" ]; then
    echo "FATAL: missing $DUMP_SQL — run pull-remote first"
    exit 1
  fi
  if [ ! -f "$MEDIA_TAR" ]; then
    echo "FATAL: missing $MEDIA_TAR — run pull-remote first"
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

  echo "==> restore Postgres dump (замінює дані, як на джерелі)"
  compose_cmd cp "$DUMP_SQL" db:/tmp/arctica.sql
  compose_cmd exec -T db psql -U arctica -d arctica -v ON_ERROR_STOP=1 -f /tmp/arctica.sql
  compose_cmd exec -T db rm -f /tmp/arctica.sql

  echo "==> media → volume"
  compose_cmd exec -T backend mkdir -p /app/media
  compose_cmd cp "$MEDIA_TAR" backend:/tmp/media.tar.gz
  compose_cmd exec -T backend tar -xzf /tmp/media.tar.gz -C /app/media
  compose_cmd exec -T backend rm -f /tmp/media.tar.gz

  echo "==> import-pg OK"
}

cmd_push_pg() {
  local target="${1:-}"
  local yes_flag="${2:-}"
  split_target "$target" "push-pg"
  if [ ! -f "$DUMP_SQL" ] || [ ! -f "$MEDIA_TAR" ]; then
    echo "FATAL: missing $DUMP_SQL or $MEDIA_TAR — run pull-remote first"
    exit 1
  fi
  echo "==> scp dump → $REMOTE_HOST:$REMOTE_PATH/deploy/data/"
  ssh "$REMOTE_HOST" "mkdir -p '$REMOTE_PATH/deploy/data'"
  scp "$DUMP_SQL" "$MEDIA_TAR" "$REMOTE_HOST:$REMOTE_PATH/deploy/data/"
  echo "==> remote import-pg"
  ssh "$REMOTE_HOST" "cd '$REMOTE_PATH' && bash ./deploy/docker/sync-data.sh import-pg ${yes_flag:---yes}"
}

usage() {
  echo "Usage: $0 export | import [--yes] | push user@host:/path [--yes]"
  echo "       $0 pull-remote user@host:/path"
  echo "       $0 import-pg [--yes] | push-pg user@host:/path [--yes]"
  exit 1
}

case "${1:-}" in
  export) cmd_export ;;
  import) cmd_import "${2:-}" ;;
  push) cmd_push "${2:-}" "${3:-}" ;;
  pull-remote) cmd_pull_remote "${2:-}" ;;
  import-pg) cmd_import_pg "${2:-}" ;;
  push-pg) cmd_push_pg "${2:-}" "${3:-}" ;;
  *) usage ;;
esac
