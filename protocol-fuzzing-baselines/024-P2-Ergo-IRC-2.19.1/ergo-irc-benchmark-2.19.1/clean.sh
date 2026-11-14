#!/usr/bin/env bash
set -Eeuo pipefail
IMAGE=profuzzbench/ergo-irc:2.19.1
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker image rm -f "$IMAGE"
else
  echo "Image already absent: $IMAGE"
fi
