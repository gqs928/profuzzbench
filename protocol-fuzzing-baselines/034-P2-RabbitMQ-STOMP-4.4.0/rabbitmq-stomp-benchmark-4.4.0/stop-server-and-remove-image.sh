#!/usr/bin/env bash
set -Eeuo pipefail
docker rm -f rabbitmq-stomp-440 2>/dev/null || true
docker image rm profuzzbench-rabbitmq-stomp:4.4.0
