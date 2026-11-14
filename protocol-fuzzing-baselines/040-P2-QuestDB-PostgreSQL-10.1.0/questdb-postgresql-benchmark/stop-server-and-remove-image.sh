#!/usr/bin/env bash
set -Eeuo pipefail
docker rm -f questdb-pg-1010 >/dev/null 2>&1 || true
docker image rm questdb/questdb:10.1.0 >/dev/null 2>&1 || true
