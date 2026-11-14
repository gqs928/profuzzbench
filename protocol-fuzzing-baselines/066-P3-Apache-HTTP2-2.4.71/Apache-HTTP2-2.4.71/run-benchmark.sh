#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
OUTDIR=${1:-/results/apache-http2-fuzz-30m}
DURATION=${2:-30m}
mkdir -p results
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  bash /opt/benchmark/run.sh "$OUTDIR" "$DURATION" 2>&1 | tee results/campaign-console.log
