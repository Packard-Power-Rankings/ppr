#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_FILE="${1:-$ROOT_DIR/.env/production}"
DOMAIN="${2:-}"

if [[ -z "$DOMAIN" ]]; then
  printf 'Usage: make lightsail-init DOMAIN=packardpowerrankings.com\n' >&2
  exit 2
fi

if [[ ! "$DOMAIN" =~ ^([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$ ]]; then
  printf 'DOMAIN must be a fully qualified DNS name without a scheme or path.\n' >&2
  exit 2
fi

command -v openssl >/dev/null 2>&1 || {
  printf 'openssl is required to generate production secrets.\n' >&2
  exit 1
}

[[ ! -e "$OUTPUT_FILE" ]] || {
  printf '%s already exists; refusing to overwrite it.\n' "$OUTPUT_FILE" >&2
  exit 1
}

mkdir -p "$(dirname "$OUTPUT_FILE")"
umask 077
MONGO_PASS="$(openssl rand -hex 32)"
REDIS_PASSWORD="$(openssl rand -hex 32)"
SETUP_TOKEN="$(openssl rand -hex 32)"
SECRET_KEY="$(openssl rand -hex 32)"

{
  printf 'DOMAIN=%s\n' "$DOMAIN"
  printf 'MONGO_DB_NAME=ppr\n'
  printf 'MONGO_USER=ppr\n'
  printf 'MONGO_PASS=%s\n' "$MONGO_PASS"
  printf 'REDIS_PASSWORD=%s\n' "$REDIS_PASSWORD"
  printf 'SETUP_TOKEN=%s\n' "$SETUP_TOKEN"
  printf 'SECRET_KEY=%s\n' "$SECRET_KEY"
  printf 'CORS_ORIGINS=https://%s\n' "$DOMAIN"
  printf 'ALLOWED_HOSTS=%s\n' "$DOMAIN"
} >"$OUTPUT_FILE"

printf '[lightsail] Created %s with generated secrets for %s\n' "$OUTPUT_FILE" "$DOMAIN"
