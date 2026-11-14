#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-profuzzbench/courier-aflnet:6.0.7}
RESULTS=${2:-$(pwd)/results/validation}
DURATION=${3:-60s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
mkdir -p "${RESULTS}"
for profile in pop3 imap; do
  output="${RESULTS}/${profile}"
  mkdir -p "${output}"
  docker run --rm --network none --user root -v "${PACKAGE_DIR}:/workspace:ro" -v "${output}:/results" "${IMAGE}" bash /workspace/smoke.sh "${profile}" /results/protocol-smoke
  docker run --rm --network none --user root -v "${PACKAGE_DIR}:/workspace:ro" -v "${output}:/results" "${IMAGE}" bash /workspace/run.sh "${profile}" /results/fuzz-validation "${DURATION}"
done
