#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
IMAGE_TAG=profuzzbench-openldap-ldap:2.7.2
if docker container inspect openldap-ldap-272 >/dev/null 2>&1; then echo 'container openldap-ldap-272 already exists' >&2; exit 2; fi
docker run -d --name openldap-ldap-272 --publish 127.0.0.1:1389:3389 -v "$ROOT/results:/results" "$IMAGE_TAG"
docker exec openldap-ldap-272 bash /opt/benchmark/server.sh
