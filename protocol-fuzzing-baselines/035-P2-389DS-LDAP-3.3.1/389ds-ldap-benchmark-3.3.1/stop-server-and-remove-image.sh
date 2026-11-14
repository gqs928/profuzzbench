#!/usr/bin/env bash
set -Eeuo pipefail
IMAGE_TAG=$(cat "$(dirname "${BASH_SOURCE[0]}")/configs/image-tag.txt")
docker rm -f 389ds-ldap-331 >/dev/null 2>&1 || true
docker image rm "$IMAGE_TAG"
