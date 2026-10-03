#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${LIGHTSAIL_ENV:-$ROOT_DIR/.env/production}"

"$ROOT_DIR/scripts/validate_lightsail_env.sh" "$ENV_FILE" >/dev/null

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

CONNECT_TIMEOUT_SECONDS="${LIGHTSAIL_HEALTH_CONNECT_TIMEOUT_SECONDS:-10}"
MAX_TIME_SECONDS="${LIGHTSAIL_HEALTH_MAX_TIME_SECONDS:-30}"

printf '[lightsail] Checking https://%s/api/health\n' "$DOMAIN"
curl \
  --connect-timeout "$CONNECT_TIMEOUT_SECONDS" \
  --max-time "$MAX_TIME_SECONDS" \
  --fail \
  --silent \
  --show-error \
  "https://$DOMAIN/api/health"
printf '\n[lightsail] Deployment is healthy\n'
