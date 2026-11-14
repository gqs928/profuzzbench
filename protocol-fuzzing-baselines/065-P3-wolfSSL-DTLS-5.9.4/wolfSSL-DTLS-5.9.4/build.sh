#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
docker compose --progress plain --env-file images.env -f compose.yaml build --pull=false 2>&1 | tee build-logs/build.log
docker image inspect wolfssl-dtls-aflnet-bench:5.9.4 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
