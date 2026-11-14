#!/usr/bin/env bash
set -euo pipefail
IMAGE=${1:-cyrus-pop3-aflnet:3.12.4}
MAKE_OPT=${MAKE_OPT:--j2}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR=${BUILD_LOG_DIR:-${PACKAGE_DIR}/build-logs}
mkdir -p "${LOG_DIR}"
(
  cd "${PACKAGE_DIR}"
  sha256sum -c source-checksums.sha256
)
DOCKER_BUILDKIT=1 docker build --pull --progress=plain \
  --build-arg "MAKE_OPT=${MAKE_OPT}" -t "${IMAGE}" "${PACKAGE_DIR}" \
  2>&1 | tee "${LOG_DIR}/docker-build.log"
docker run --rm --network none "${IMAGE}" \
  cat /home/ubuntu/experiments/build-versions.txt \
  | tee "${LOG_DIR}/build-versions.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
  | tee "${LOG_DIR}/image-id.txt"
