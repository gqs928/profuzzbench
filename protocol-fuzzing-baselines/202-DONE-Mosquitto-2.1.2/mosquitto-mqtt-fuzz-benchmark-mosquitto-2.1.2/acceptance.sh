#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-mosquitto-fuzz}
RESULTS_DIR=${2:-$(pwd)/results/mqtt-validation}
DURATION=${3:-60s}
if (($# >= 3)); then shift 3; else set --; fi
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

"${PACKAGE_DIR}/build.sh" "${IMAGE}" "$@"
"${PACKAGE_DIR}/validate.sh" "${IMAGE}" "${RESULTS_DIR}" "${DURATION}"
