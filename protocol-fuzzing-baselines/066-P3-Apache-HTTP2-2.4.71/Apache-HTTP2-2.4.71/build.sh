#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
docker compose --env-file images.env -f compose.yaml build --pull=false 2>&1 | tee build-logs/build.log
docker image inspect "$HTTPD_IMAGE" --format '{{.Id}}' | tee build-logs/image-id.txt
