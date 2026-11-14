#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-mosquitto-fuzz}
if (($# > 0)); then shift; fi
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs"}
MAKE_OPT=${MAKE_OPT:--j1}
UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT:-20260928T000000Z}
mkdir -p "${LOG_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh

(
  cd "${PACKAGE_DIR}"
  sha256sum -c source-checksums.sha256
)

DOCKER_BUILDKIT=1 docker build --progress=plain "$@" \
  --build-arg "MAKE_OPT=${MAKE_OPT}" \
  --build-arg "UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT}" \
  -t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"

docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
  | tee "${LOG_DIR}/build-versions.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
  | tee "${LOG_DIR}/image-id.txt"
(
  cd "${PACKAGE_DIR}"
  sha256sum Dockerfile .dockerignore aflnet-mqtt.patch mqtt_aflnet.c parser-test.c \
    mqtt_packets.py prepare_seeds.py protocol_smoke.py mqtt.dict mosquitto.conf \
    clean.sh parser-check.sh run.sh validate.sh acceptance.sh coverage-run.sh \
    coverage_replay.py \
    source-checksums.sha256 \
    aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
    mosquitto-2.1.2.tar.gz \
    | tee "${LOG_DIR}/build-input-sha256.txt"
)
echo "PASS: pinned Mosquitto/AFLNet image built; logs are in ${LOG_DIR}"
