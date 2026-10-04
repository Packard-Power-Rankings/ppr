#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTAINER_NAME="ppr-caddy-policy-test-$$"
CADDY_IMAGE="${CADDY_TEST_IMAGE:-caddy:2-alpine}"

cleanup() {
  docker stop --time 2 "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run --detach --rm \
  --name "$CONTAINER_NAME" \
  --env DOMAIN=:8080 \
  --publish 127.0.0.1::8080 \
  --volume "$ROOT_DIR/deploy/lightsail/Caddyfile:/etc/caddy/Caddyfile:ro" \
  --volume "$ROOT_DIR/frontend/public/index.html:/srv/index.html:ro" \
  "$CADDY_IMAGE" \
  caddy run --config /etc/caddy/Caddyfile >/dev/null

PORT=""
for _ in {1..30}; do
  PORT="$(docker port "$CONTAINER_NAME" 8080/tcp 2>/dev/null | sed -n 's/.*://p' | head -n 1)"
  if [[ -n "$PORT" ]] && curl --silent --output /dev/null \
    --user-agent 'Mozilla/5.0' "http://127.0.0.1:$PORT/"; then
    break
  fi
  sleep 0.2
done

[[ -n "$PORT" ]] || {
  printf '[caddy-policy] ERROR: Caddy did not publish a test port.\n' >&2
  exit 1
}

request_status() {
  curl --silent --output /dev/null --write-out '%{http_code}' "$@"
}

assert_status() {
  local expected="$1"
  local description="$2"
  shift 2
  local actual
  actual="$(request_status "$@")"
  if [[ "$actual" != "$expected" ]]; then
    printf '[caddy-policy] ERROR: %s returned %s; expected %s.\n' \
      "$description" "$actual" "$expected" >&2
    exit 1
  fi
}

BASE_URL="http://127.0.0.1:$PORT"
assert_status 200 'browser request' \
  --user-agent 'Mozilla/5.0' "$BASE_URL/"
assert_status 403 'automated client request' "$BASE_URL/"
assert_status 403 'missing user-agent request' \
  --header 'User-Agent:' "$BASE_URL/"
assert_status 200 'permitted search crawler request' \
  --user-agent 'Googlebot/2.1' "$BASE_URL/"
assert_status 403 'vulnerability probe path' \
  --user-agent 'Mozilla/5.0' "$BASE_URL/wp-login.php"

health_status="$(request_status "$BASE_URL/api/health")"
if [[ "$health_status" == '403' ]]; then
  printf '[caddy-policy] ERROR: The infrastructure health endpoint was blocked.\n' >&2
  exit 1
fi

logs="$(docker logs "$CONTAINER_NAME" 2>&1)"
for reason in automated_user_agent missing_user_agent probe_path; do
  if [[ "$logs" != *"\"bot_block_reason\":\"$reason\""* ]]; then
    printf '[caddy-policy] ERROR: Missing %s detection in Caddy logs.\n' \
      "$reason" >&2
    exit 1
  fi
done

printf '[caddy-policy] Browser access allowed and automated requests blocked.\n'
