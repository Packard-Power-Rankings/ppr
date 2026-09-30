#!/usr/bin/env bash

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  printf 'Run this script with sudo: sudo ./deploy/lightsail/bootstrap-ubuntu.sh\n' >&2
  exit 1
fi

if [[ ! -f /etc/os-release ]]; then
  printf 'Unable to identify this operating system. This script supports Ubuntu.\n' >&2
  exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  printf 'This script supports Ubuntu; detected %s.\n' "${ID:-unknown}" >&2
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl git jq unattended-upgrades
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

ARCH="$(dpkg --print-architecture)"
CODENAME="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu %s stable\n' \
  "$ARCH" "$CODENAME" >/etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

DEPLOY_USER="${SUDO_USER:-ubuntu}"
if id "$DEPLOY_USER" >/dev/null 2>&1; then
  usermod -aG docker "$DEPLOY_USER"
fi

printf 'Docker is installed. Log out and back in so %s receives Docker group access.\n' "$DEPLOY_USER"
