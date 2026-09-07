#!/usr/bin/env bash
set -euo pipefail

if command -v docker >/dev/null 2>&1; then
  docker --version
  docker compose version
  exit 0
fi

curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
if [ "${SUDO_USER:-}" != "" ]; then
  usermod -aG docker "$SUDO_USER" || true
fi
docker --version
docker compose version
