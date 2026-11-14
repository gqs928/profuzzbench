#!/usr/bin/env bash
set -euo pipefail
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
IMAGE=${1:-redis-resp-fuzz}
if (($# > 0)); then shift; fi
RESULTS_DIR=${1:-"${PACKAGE_DIR}/results/redis-validation"}
DURATION=${2:-60s}
"${PACKAGE_DIR}/build.sh" "${IMAGE}"
"${PACKAGE_DIR}/validate.sh" "${IMAGE}" "${RESULTS_DIR}" "${DURATION}"
