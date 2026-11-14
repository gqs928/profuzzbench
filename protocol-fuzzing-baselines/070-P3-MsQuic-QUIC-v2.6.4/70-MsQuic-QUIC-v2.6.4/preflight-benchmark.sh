#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  /opt/benchmark/run.sh /results/msquic-preflight-60s-20261113-v2 60s
