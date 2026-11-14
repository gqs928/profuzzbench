#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  bash /opt/benchmark/generate-seeds.sh 2>&1 | tee results/seed-generation.log
./run-benchmark.sh /results/quiche-preflight-60s-20261112 60s
