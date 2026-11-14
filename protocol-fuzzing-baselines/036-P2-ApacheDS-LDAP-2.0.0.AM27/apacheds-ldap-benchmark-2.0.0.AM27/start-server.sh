#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
IMAGE_TAG=$(cat "$ROOT/configs/image-tag.txt")
if docker container inspect apacheds-ldap-am27 >/dev/null 2>&1; then echo 'container apacheds-ldap-am27 already exists' >&2; exit 2; fi
docker run -d --name apacheds-ldap-am27 --publish 127.0.0.1:1389:10389 -v "$ROOT/results:/results" "$IMAGE_TAG"
docker exec apacheds-ldap-am27 bash /opt/benchmark/server.sh
