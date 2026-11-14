#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_IMAGE=${BASE_IMAGE:-profuzzbench/courier-aflnet:6.0.7-base}
IMAGE=${IMAGE:-profuzzbench/courier-aflnet:6.0.7}
mkdir -p "${PACKAGE_DIR}/build-logs"

DOCKER_BUILDKIT=1 docker build --pull --progress=plain \
  -f "${PACKAGE_DIR}/Dockerfile" \
  -t "${BASE_IMAGE}" "${PACKAGE_DIR}" \
  2>&1 | tee "${PACKAGE_DIR}/build-logs/docker-build-base.log"

DOCKER_BUILDKIT=1 docker build --progress=plain \
  --build-arg "BASE_IMAGE=${BASE_IMAGE}" \
  -f "${PACKAGE_DIR}/Dockerfile.imap-adapter" \
  -t "${IMAGE}" "${PACKAGE_DIR}" \
  2>&1 | tee "${PACKAGE_DIR}/build-logs/docker-build-imap-adapter.log"
