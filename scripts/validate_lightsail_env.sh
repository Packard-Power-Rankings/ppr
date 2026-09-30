#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/.env/production}"

fail() {
  printf '[lightsail] ERROR: %s\n' "$*" >&2
  exit 1
}

[[ -f "$ENV_FILE" ]] || fail "Environment file not found: $ENV_FILE. Run 'make lightsail-init'."

set -a
# This file is maintained by the deployer and contains shell-safe hex secrets.
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required=(
  DOMAIN
  MONGO_DB_NAME
  MONGO_USER
  MONGO_PASS
  REDIS_PASSWORD
  SETUP_TOKEN
  SECRET_KEY
  CORS_ORIGINS
  ALLOWED_HOSTS
)

for name in "${required[@]}"; do
  [[ -n "${!name:-}" ]] || fail "$name is empty in $ENV_FILE"
done

[[ "$DOMAIN" != *"://"* ]] || fail "DOMAIN must not include http:// or https://"
[[ "$DOMAIN" != */* ]] || fail "DOMAIN must not include a path or trailing slash"
[[ "$DOMAIN" != *" "* ]] || fail "DOMAIN must not contain spaces"
[[ "$DOMAIN" =~ ^([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$ ]] || fail "DOMAIN must be a fully qualified DNS name"
[[ "$MONGO_DB_NAME" =~ ^[A-Za-z0-9_-]+$ ]] || fail "MONGO_DB_NAME contains unsupported characters"
[[ "$MONGO_USER" =~ ^[A-Za-z0-9_-]+$ ]] || fail "MONGO_USER contains unsupported characters"
[[ "$MONGO_PASS" =~ ^[A-Fa-f0-9]+$ ]] || fail "MONGO_PASS must be hexadecimal so it is safe in the MongoDB URI"

for name in MONGO_PASS REDIS_PASSWORD SETUP_TOKEN SECRET_KEY; do
  value="${!name}"
  [[ "$value" != *"replace-with"* ]] || fail "$name still contains the example placeholder"
  [[ "$value" != *"change-this"* ]] || fail "$name still contains a development placeholder"
  [[ ${#value} -ge 32 ]] || fail "$name must contain at least 32 characters"
done

secrets=("$MONGO_PASS" "$REDIS_PASSWORD" "$SETUP_TOKEN" "$SECRET_KEY")
for ((i = 0; i < ${#secrets[@]}; i++)); do
  for ((j = i + 1; j < ${#secrets[@]}; j++)); do
    [[ "${secrets[$i]}" != "${secrets[$j]}" ]] || fail "Production secrets must use different values"
  done
done

[[ ",$ALLOWED_HOSTS," == *",$DOMAIN,"* ]] || fail "ALLOWED_HOSTS must include $DOMAIN"
[[ ",$CORS_ORIGINS," == *",https://$DOMAIN,"* ]] || fail "CORS_ORIGINS must include https://$DOMAIN"

printf '[lightsail] Environment looks valid for %s\n' "$DOMAIN"
