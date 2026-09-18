#!/usr/bin/env bash
# Generate server .env from .env.docker.example with unique SECRET_KEY + POSTGRES_PASSWORD.
#
#   DROPLET_IP=46.101.105.117 SITE_DOMAIN=arctica.od.ua bash deploy/docker/gen-env.sh
#   DROPLET_IP=157.230.99.135 bash deploy/docker/gen-env.sh   # HTTP-only test IP
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SRC="$ROOT/.env.docker.example"
DST="$ROOT/.env"

if [ ! -f "$SRC" ]; then
  echo "FATAL: missing $SRC"
  exit 1
fi
if [ -f "$DST" ]; then
  echo "FATAL: $DST already exists — refuse to overwrite"
  exit 1
fi

DROPLET_IP="${DROPLET_IP:-}"
if [ -z "$DROPLET_IP" ]; then
  echo "FATAL: set DROPLET_IP=x.x.x.x"
  echo "  DROPLET_IP=46.101.105.117 SITE_DOMAIN=arctica.od.ua bash deploy/docker/gen-env.sh"
  exit 1
fi
if ! [[ "$DROPLET_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "FATAL: DROPLET_IP must be IPv4, got: $DROPLET_IP"
  exit 1
fi

SITE_DOMAIN="${SITE_DOMAIN:-$DROPLET_IP}"
SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
POSTGRES_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"

if [[ "$SITE_DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  ALLOWED_HOSTS="${DROPLET_IP},127.0.0.1,localhost,backend"
  CSRF_TRUSTED_ORIGINS="http://${DROPLET_IP}"
else
  ALLOWED_HOSTS="${DROPLET_IP},${SITE_DOMAIN},www.${SITE_DOMAIN},127.0.0.1,localhost,backend"
  CSRF_TRUSTED_ORIGINS="http://${DROPLET_IP},http://${SITE_DOMAIN},http://www.${SITE_DOMAIN}"
fi

sed \
  -e "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" \
  -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" \
  -e "s|__DROPLET_IP__|${DROPLET_IP}|g" \
  -e "s|__SITE_DOMAIN__|${SITE_DOMAIN}|g" \
  -e "s|^DROPLET_IP=.*|DROPLET_IP=${DROPLET_IP}|" \
  -e "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${ALLOWED_HOSTS}|" \
  -e "s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}|" \
  -e "s|^SITE_DOMAIN=.*|SITE_DOMAIN=${SITE_DOMAIN}|" \
  "$SRC" > "$DST"

chmod 600 "$DST"
echo "==> wrote $DST (SECRET_KEY + POSTGRES_PASSWORD generated)"
echo "==> verify:"
grep -E '^(DROPLET_IP|ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|USE_HTTPS|SITE_PROTOCOL|SITE_DOMAIN)=' "$DST" || true

if grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|DROPLET_IP|SITE_DOMAIN)=' "$DST" | grep -q '__DROPLET_IP__\|__SITE_DOMAIN__'; then
  echo "FATAL: placeholder left in .env"
  exit 1
fi
if grep -qE '^USE_HTTPS=True' "$DST"; then
  echo "FATAL: USE_HTTPS=True on HTTP-first droplet — set False until certbot"
  exit 1
fi

echo "==> OK. Next: bash deploy/docker/deploy.sh"
