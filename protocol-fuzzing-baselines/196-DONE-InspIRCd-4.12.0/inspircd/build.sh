#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-inspircd-fuzz}
if (($# > 0)); then shift; fi
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs"}
MAKE_OPT=${MAKE_OPT:--j1}
UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT:-20260928T000000Z}
mkdir -p "${LOG_DIR}"

docker build --progress=plain "$@" \
  --build-arg "MAKE_OPT=${MAKE_OPT}" \
  --build-arg "UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT}" \
  -t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
  | tee "${LOG_DIR}/build-versions.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
  | tee "${LOG_DIR}/image-id.txt"
sha256sum "${PACKAGE_DIR}/Dockerfile" "${PACKAGE_DIR}/aflnet-irc.patch" \
  "${PACKAGE_DIR}/inspircd-shutdown.patch" "${PACKAGE_DIR}/irc_aflnet.c" "${PACKAGE_DIR}/parser-test.c" \
  "${PACKAGE_DIR}/normalize_source.py" \
  "${PACKAGE_DIR}/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz" \
  "${PACKAGE_DIR}/source-lock.json" \
  "${PACKAGE_DIR}/inspircd-78159a35a6dba909c654a96ae92d8cb3340c8646.tar.gz" \
  | tee "${LOG_DIR}/build-input-sha256.txt"
echo "PASS: pinned InspIRCd image built; logs and source manifest are in ${LOG_DIR}"
