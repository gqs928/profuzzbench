#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
OUTDIR=${1:-/results/google-quiche-preflight-60s-20261113}
DURATION=${2:-60s}
mkdir -p results
LOGNAME=${OUTDIR##*/}
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  bash /opt/benchmark/run.sh "${OUTDIR}" "${DURATION}" 2>&1 | tee "results/${LOGNAME}-console.log"
