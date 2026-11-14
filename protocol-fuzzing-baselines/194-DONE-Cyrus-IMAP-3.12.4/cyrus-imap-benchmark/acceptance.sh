#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-cyrus-imap-fuzz}
RESULTS_DIR=${2:-$(pwd)/imap-validation}
DURATION=${3:-60s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
"${PACKAGE_DIR}/build.sh" "${IMAGE}"
"${PACKAGE_DIR}/validate.sh" "${IMAGE}" "${RESULTS_DIR}" "${DURATION}"
