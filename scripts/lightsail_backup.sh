#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${LIGHTSAIL_ENV:-$ROOT_DIR/.env.production}"
COMPOSE_FILE="$ROOT_DIR/docker-compose.lightsail.yml"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="$BACKUP_DIR/ppr-mongodb-$TIMESTAMP.archive.gz"

"$ROOT_DIR/scripts/validate_lightsail_env.sh" "$ENV_FILE" >/dev/null
mkdir -p "$BACKUP_DIR"
umask 077

printf '[lightsail] Writing MongoDB backup to %s\n' "$BACKUP_FILE"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db sh -c \
  'exec mongodump --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --gzip' \
  >"$BACKUP_FILE"

[[ -s "$BACKUP_FILE" ]] || {
  rm -f "$BACKUP_FILE"
  printf '[lightsail] ERROR: MongoDB produced an empty backup\n' >&2
  exit 1
}

printf '[lightsail] Backup complete (%s)\n' "$(du -h "$BACKUP_FILE" | cut -f1)"
