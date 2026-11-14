#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
IMAGE=${1:-redpanda-kafka-fuzz-bench}
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs"}
mkdir -p "${LOG_DIR}"
(
  cd "${PACKAGE_DIR}"
  sha256sum -c source-checksums.sha256
)
DOCKER_BUILDKIT=1 docker build --progress=plain --network=host \
  -t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"
docker run --rm "${IMAGE}" cat /home/redpanda/benchmark/redpanda-server-version.txt \
  | tee "${LOG_DIR}/redpanda-server-version.txt"
docker run --rm "${IMAGE}" cat /home/redpanda/benchmark/build-package-manifest.txt \
  | tee "${LOG_DIR}/build-package-manifest.txt"
docker image inspect --format='image_id={{.Id}}' "${IMAGE}" \
  | tee "${LOG_DIR}/image-id.txt"
