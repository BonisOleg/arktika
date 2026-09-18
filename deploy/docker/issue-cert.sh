#!/usr/bin/env bash
# Перший сертифікат Let's Encrypt (certbot на хості, standalone).
# DNS A @ і www уже мають вказувати на цей Droplet.
# Usage: bash deploy/docker/issue-cert.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

read_env() {
  local key="$1"
  grep -E "^${key}=" .env | tail -1 | cut -d= -f2- | tr -d '\r' | sed 's/^["'\'']//;s/["'\'']$//'
}

if [[ ! -f .env ]]; then
  echo "FATAL: .env not found"
  exit 1
fi

SITE_DOMAIN="$(read_env SITE_DOMAIN)"
if [[ -z "$SITE_DOMAIN" || "$SITE_DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "FATAL: SITE_DOMAIN must be a hostname (arctica.od.ua), not an IP"
  exit 1
fi

EMAIL="${CERTBOT_EMAIL:-admin@${SITE_DOMAIN}}"
export COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"

echo "==> stop container nginx (standalone займає :80)"
docker compose stop nginx 2>/dev/null || true

if command -v systemctl >/dev/null 2>&1; then
  systemctl stop nginx 2>/dev/null || true
fi

apt-get install -y certbot
mkdir -p /var/www/certbot

certbot certonly --standalone \
  -d "$SITE_DOMAIN" -d "www.${SITE_DOMAIN}" \
  --agree-tos -m "$EMAIL"

echo "==> cert OK: /etc/letsencrypt/live/${SITE_DOMAIN}/"
echo "У .env вистав:"
echo "  USE_HTTPS=True"
echo "  SITE_PROTOCOL=https"
echo "  CSRF_TRUSTED_ORIGINS=https://${SITE_DOMAIN},https://www.${SITE_DOMAIN},http://$(read_env DROPLET_IP)"
echo "Потім: bash deploy/docker/deploy.sh"
echo "Renew: certbot renew && docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.ssl.yml exec nginx nginx -s reload"
