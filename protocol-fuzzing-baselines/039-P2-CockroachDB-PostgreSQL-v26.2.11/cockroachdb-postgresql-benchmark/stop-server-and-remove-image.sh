#!/usr/bin/env bash
set -Eeuo pipefail
docker rm -f cockroachdb-pg-2611 >/dev/null 2>&1 || true
docker image rm cockroachdb/cockroach:v26.2.11 >/dev/null 2>&1 || true
