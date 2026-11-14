#!/usr/bin/env bash
set -Eeuo pipefail
IMAGE=${1:-profuzzbench/inn-nntp:2.7.4}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$PACKAGE_DIR/build-logs"
docker build --pull=false -f "$PACKAGE_DIR/Dockerfile" -t "$IMAGE" "$PACKAGE_DIR" 2>&1 | tee "$PACKAGE_DIR/build-logs/docker-build.log"
docker image inspect "$IMAGE" --format '{{.Id}}' | tee "$PACKAGE_DIR/build-logs/image-id.txt"
docker run --rm --network none --user 1000:1000 "$IMAGE" cat /opt/benchmark/build-versions.txt >"$PACKAGE_DIR/build-logs/build-versions.txt"
echo "Built and version-checked $IMAGE"
