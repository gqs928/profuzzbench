#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
IMAGE_TAG=$(cat "$ROOT/configs/image-tag.txt")
mkdir -p "$ROOT/results"
# The official container runs as its service account; let that UID write the
# bind-mounted campaign results while retaining sticky-directory semantics.
chmod 1777 "$ROOT/results"
if docker container inspect 389ds-ldap-331 >/dev/null 2>&1; then echo 'container 389ds-ldap-331 already exists' >&2; exit 2; fi
docker run -d --name 389ds-ldap-331 --publish 127.0.0.1:1389:3389 \
  -v "$ROOT/results:/results" "$IMAGE_TAG"
docker exec 389ds-ldap-331 bash /opt/benchmark/server.sh
