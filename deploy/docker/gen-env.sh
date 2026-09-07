#!/usr/bin/env bash
# Generate server .env from .env.docker.example with unique SECRET_KEY + POSTGRES_PASSWORD.
# Usage (on Droplet): bash deploy/docker/gen-env.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SRC="$ROOT/.env.docker.example"
DST="$ROOT/.env"
DROPLET_IP="157.230.99.135"

if [ ! -f "$SRC" ]; then
  echo "FATAL: missing $SRC"
  exit 1
fi
if [ -f "$DST" ]; then
  echo "FATAL: $DST already exists — refuse to overwrite"
  exit 1
fi

SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
POSTGRES_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"

sed \
  -e "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" \
  -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" \
  "$SRC" > "$DST"

chmod 600 "$DST"
echo "==> wrote $DST (SECRET_KEY + POSTGRES_PASSWORD generated)"
echo "==> verify:"
grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|USE_HTTPS|SITE_PROTOCOL|SITE_DOMAIN)=' "$DST" || true

if grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS)=.*DROPLET_IP' "$DST"; then
  echo "FATAL: DROPLET_IP token still in ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS"
  exit 1
fi
if ! grep -q "$DROPLET_IP" "$DST"; then
  echo "FATAL: expected droplet IP $DROPLET_IP missing from .env"
  exit 1
fi
if grep -qE '^USE_HTTPS=True' "$DST"; then
  echo "FATAL: USE_HTTPS=True on HTTP-first droplet — set False until certbot"
  exit 1
fi

echo "==> OK. Next: bash deploy/docker/deploy.sh"
