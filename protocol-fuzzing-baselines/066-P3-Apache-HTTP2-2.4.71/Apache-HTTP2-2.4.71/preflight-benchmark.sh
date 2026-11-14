#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  bash /opt/benchmark/preflight.sh /results/apache-http2-preflight-60s-20261112 2>&1 | tee results/preflight-console.log
