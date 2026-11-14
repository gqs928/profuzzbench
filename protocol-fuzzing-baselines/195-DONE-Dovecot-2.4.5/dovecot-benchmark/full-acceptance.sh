#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-dovecot-imap-fuzz}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
RESULTS_DIR=${2:-"${PACKAGE_DIR}/results/dovecot-acceptance-${STAMP}"}
DURATION=${3:-30m}

if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "验收目录非空，请选择新目录：${RESULTS_DIR}" >&2
  exit 2
fi
mkdir -p "${RESULTS_DIR}"
RESULTS_DIR=$(cd "${RESULTS_DIR}" && pwd)
BUILD_LOG_DIR="${RESULTS_DIR}/build-logs" \
  "${PACKAGE_DIR}/build.sh" "${IMAGE}"
"${PACKAGE_DIR}/validate.sh" "${IMAGE}" "${RESULTS_DIR}" "${DURATION}"
