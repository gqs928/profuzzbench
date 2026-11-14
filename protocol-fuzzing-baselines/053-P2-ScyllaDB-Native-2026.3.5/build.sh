#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
SCYLLA_IMAGE=$(sed -n 's/^SCYLLA_IMAGE=//p' images.env)
docker build --pull --build-arg SCYLLA_IMAGE="$SCYLLA_IMAGE" --tag scylla-native-fuzz-bench:2026.3.5 .
docker image inspect scylla-native-fuzz-bench:2026.3.5 --format '{{.Id}}' | tee build-logs/image-id.txt
