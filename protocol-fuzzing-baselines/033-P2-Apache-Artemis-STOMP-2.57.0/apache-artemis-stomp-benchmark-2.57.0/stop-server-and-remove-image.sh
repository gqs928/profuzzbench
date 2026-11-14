#!/usr/bin/env bash
set -Eeuo pipefail
docker rm -f artemis-stomp-2570 2>/dev/null || true
docker image rm profuzzbench-artemis-stomp:2.57.0
