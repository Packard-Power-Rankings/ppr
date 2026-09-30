#!/bin/sh

set -eu

LOCK_HASH="$(sha256sum package-lock.json | cut -d ' ' -f 1)"
INSTALLED_HASH=""

if [ -f node_modules/.package-lock.sha256 ]; then
  INSTALLED_HASH="$(cat node_modules/.package-lock.sha256)"
fi

if [ "$LOCK_HASH" != "$INSTALLED_HASH" ] || [ ! -x node_modules/.bin/react-scripts ]; then
  printf '[frontend] Installing dependencies from package-lock.json\n'
  npm ci
  printf '%s\n' "$LOCK_HASH" > node_modules/.package-lock.sha256
fi

exec npm start
