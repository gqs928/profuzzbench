#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
IMAGE=profuzzbench/ergo-irc:2.19.1
mkdir -p "$ROOT/build-logs"
docker build --pull=false --progress=plain -t "$IMAGE" "$ROOT" \
  2>&1 | tee "$ROOT/build-logs/docker-build.log"
docker image inspect "$IMAGE" --format '{{.Id}}' \
  | tee "$ROOT/build-logs/image-id.txt"
