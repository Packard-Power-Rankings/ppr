#!/bin/sh

set -eu

if [ "$(id -u)" -eq 0 ]; then
  archive_dir="${ARCHIVE_DIR:-/var/lib/ppr-archives}"
  upload_dir="${UPLOAD_DIR:-/var/lib/ppr-uploads}"
  mkdir -p "$archive_dir" "$upload_dir"
  chown -R app:app "$archive_dir" "$upload_dir"

  exec setpriv --reuid=app --regid=app --init-groups "$@"
fi

exec "$@"
