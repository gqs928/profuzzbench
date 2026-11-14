#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
docker build --pull=false -t profuzzbench/unrealircd-irc:6.2.7.1 . \
  2>&1 | tee build-logs/docker-build.log
