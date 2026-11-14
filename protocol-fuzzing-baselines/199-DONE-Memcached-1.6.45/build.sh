#!/usr/bin/env bash
set -euo pipefail

# Build a pinned image and retain both the complete build log and resolved
# source/package manifest. Additional docker build options may follow IMAGE.
IMAGE=${1:-memcached-fuzz}
if (($# > 0)); then shift; fi
LOG_DIR=${BUILD_LOG_DIR:-$(pwd)/build-logs}
MAKE_OPT=${MAKE_OPT:--j1}
UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT:-20260928T000000Z}
mkdir -p "${LOG_DIR}"
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

docker build --progress=plain "$@" --build-arg "MAKE_OPT=${MAKE_OPT}" --build-arg "UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT}" -t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt | tee "${LOG_DIR}/build-versions.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" | tee "${LOG_DIR}/image-id.txt"
sha256sum "${PACKAGE_DIR}/Dockerfile" "${PACKAGE_DIR}/aflnet-memcached.patch" "${PACKAGE_DIR}/memcached_aflnet.c" "${PACKAGE_DIR}/parser-test.c" | tee "${LOG_DIR}/build-input-sha256.txt"
echo "PASS: build log and pinned source manifest are saved in ${LOG_DIR}"
