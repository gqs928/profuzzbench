#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
docker build --pull=false -t profuzzbench/leafnode-nntp:1.12.0 . \
  2>&1 | tee build-logs/docker-build.log
