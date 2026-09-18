#!/usr/bin/env bash
# Production deploy on DigitalOcean Droplet (HTTP-first, django-droplet-http-first).
# Usage on server: bash deploy/docker/deploy.sh
# Requires .env (gen-env.sh). Never merges docker-compose.override.yml.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Explicit file list — ignore auto-merged override.yml if someone recreates it.
export COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"
COMPOSE=(docker compose)
SERVICES=(db backend nginx)

read_env() {
  local key="$1"
  grep -E "^${key}=" .env | tail -1 | cut -d= -f2- | tr -d '\r' | sed 's/^["'\'']//;s/["'\'']$//'
}

free_host_ports() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl stop nginx 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    for svc in $(systemctl list-units --type=service --all 2>/dev/null | grep -oE 'gunicorn[^ ]*' || true); do
      systemctl stop "$svc" 2>/dev/null || true
      systemctl disable "$svc" 2>/dev/null || true
    done
  fi
}

backend_healthz_ok() {
  "${COMPOSE[@]}" exec -T backend python3 -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=5)" \
    >/dev/null 2>&1
}

if [[ ! -f .env ]]; then
  echo "FATAL: .env not found. bash deploy/docker/gen-env.sh"
  exit 1
fi

DROPLET_IP="$(read_env DROPLET_IP)"
if [[ -z "$DROPLET_IP" ]]; then
  DROPLET_IP="$(read_env ALLOWED_HOSTS | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1 || true)"
fi
if [[ -z "$DROPLET_IP" ]]; then
  echo "FATAL: set DROPLET_IP=x.x.x.x in .env (або IPv4 у ALLOWED_HOSTS)"
  exit 1
fi

# Лише значення змінних (коментарі з текстом DROPLET_IP ігноруємо).
if grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|DROPLET_IP)=' .env | grep -q '__DROPLET_IP__'; then
  echo "FATAL: placeholder __DROPLET_IP__ left in .env. Re-run gen-env.sh"
  exit 1
fi

if ! grep -E '^ALLOWED_HOSTS=' .env | grep -q "$DROPLET_IP"; then
  echo "FATAL: ALLOWED_HOSTS must include $DROPLET_IP (доступ до DNS)"
  exit 1
fi
if ! grep -E '^CSRF_TRUSTED_ORIGINS=' .env | grep -q "$DROPLET_IP"; then
  echo "FATAL: CSRF_TRUSTED_ORIGINS must include http://$DROPLET_IP"
  exit 1
fi

if grep -qE '^USE_HTTPS=True' .env; then
  echo "FATAL: USE_HTTPS=True — healthz/cookies break until certbot. Set False for HTTP-first."
  exit 1
fi

if [[ -f docker-compose.override.yml ]]; then
  echo "WARN: docker-compose.override.yml present — COMPOSE_FILE ignores it, but prefer removing on Droplet."
fi

echo "==> Freeing host ports 80/443"
free_host_ports

echo "==> stop nginx (уникнути 502 під час recreate backend)"
"${COMPOSE[@]}" stop nginx 2>/dev/null || true

echo "==> build + up db backend"
"${COMPOSE[@]}" up -d --build --remove-orphans db backend || true

echo "==> wait backend /healthz/ (up to ~4 min)"
ok=0
for _ in $(seq 1 80); do
  if backend_healthz_ok; then
    ok=1
    break
  fi
  sleep 3
done

if [[ "$ok" -ne 1 ]]; then
  echo "WARN: backend /healthz/ not ready — logs:"
  "${COMPOSE[@]}" logs --tail=50 backend db
  exit 1
fi

echo "==> start nginx"
"${COMPOSE[@]}" up -d --remove-orphans nginx || true

if curl -sf -H "Host: ${DROPLET_IP}" http://127.0.0.1/healthz/ >/dev/null; then
  echo "HTTP /healthz/ OK (Host: ${DROPLET_IP})"
else
  echo "WARN: HTTP /healthz/ via nginx failed — check logs"
  "${COMPOSE[@]}" logs --tail=30 nginx backend || true
fi

echo "==> inventory"
missing=0
for svc in "${SERVICES[@]}"; do
  if "${COMPOSE[@]}" ps "$svc" 2>/dev/null | grep -qiE "Up|running"; then
    echo "OK: $svc"
  else
    echo "MISSING: $svc"
    missing=1
  fi
done

"${COMPOSE[@]}" ps

if [[ "$missing" -ne 0 ]]; then
  echo "ERROR: some services not Up — source of truth: curl /healthz/"
  exit 1
fi

echo "All ${#SERVICES[@]} services are running."
echo "Site: http://${DROPLET_IP}/"
echo "Next (optional data): from Mac ./deploy/docker/sync-data.sh push root@${DROPLET_IP}:/var/www/arctica --yes"
echo "Or seed: ${COMPOSE[*]} exec backend python3 manage.py seed_demo"
echo "Admin: ${COMPOSE[*]} exec -T backend python3 manage.py createsuperuser"
