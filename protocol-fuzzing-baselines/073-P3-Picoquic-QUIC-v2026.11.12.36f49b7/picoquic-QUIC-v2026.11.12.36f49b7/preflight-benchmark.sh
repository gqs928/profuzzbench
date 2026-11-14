#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  /opt/benchmark/run.sh /results/picoquic-preflight-60s-20261113-attempt-2 60s
