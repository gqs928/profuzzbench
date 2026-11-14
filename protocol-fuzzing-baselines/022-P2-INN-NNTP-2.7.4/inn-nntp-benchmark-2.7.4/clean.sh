#!/usr/bin/env bash
set -Eeuo pipefail
IMAGE=${1:-profuzzbench/inn-nntp:2.7.4}
docker image rm -f "$IMAGE"
docker builder prune -af
