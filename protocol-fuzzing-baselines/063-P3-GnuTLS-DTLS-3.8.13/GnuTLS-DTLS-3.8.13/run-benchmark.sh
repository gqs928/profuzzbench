#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
OUTDIR=${1:-/results/gnutls-dtls-fuzz-30m}
DURATION=${2:-30m}
mkdir -p results
RUN_ENV=()
if [[ -n "${SEED_DIR:-}" ]]; then RUN_ENV=(-e "SEED_DIR=${SEED_DIR}"); fi
docker compose --env-file images.env -f compose.yaml run --rm --no-deps "${RUN_ENV[@]}" fuzz \
  bash /opt/benchmark/run.sh "$OUTDIR" "$DURATION" 2>&1 | tee results/campaign-console.log
