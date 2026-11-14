#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
OUTDIR=${1:-/results/ngtcp2-fuzz-30m-20261113}
DURATION=${2:-30m}
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  /opt/benchmark/run.sh "$OUTDIR" "$DURATION"
