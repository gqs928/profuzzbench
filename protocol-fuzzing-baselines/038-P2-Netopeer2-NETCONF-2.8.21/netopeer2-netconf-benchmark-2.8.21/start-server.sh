#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
IMAGE_TAG=profuzzbench-netopeer2-netconf:2.8.21
NAME=netopeer2-netconf-2821
if docker container inspect "$NAME" >/dev/null 2>&1; then echo "container $NAME already exists" >&2; exit 2; fi
mkdir -p "$ROOT/results"
docker run -d --name "$NAME" --publish 127.0.0.1:1830:1830 \
  -v "$ROOT/results:/results" "$IMAGE_TAG"
docker exec "$NAME" bash /opt/benchmark/server.sh
