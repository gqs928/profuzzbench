#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs results
docker compose --env-file images.env -f compose.yaml build fuzz 2>&1 | tee build-logs/docker-build.log
docker image inspect --format '{{.Id}}' quic-go-native-fuzz-bench:v0.65.0 | tee build-logs/image-id.txt
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz go version | tee build-logs/go-version.txt
