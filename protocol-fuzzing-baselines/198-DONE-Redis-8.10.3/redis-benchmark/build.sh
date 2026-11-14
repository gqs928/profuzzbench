#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-redis-resp-fuzz}
if (($# > 0)); then shift; fi
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs"}
MAKE_OPT=${MAKE_OPT:--j2}
UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT:-20260928T000000Z}
BUILD_NETWORK=${BUILD_NETWORK:-host}
mkdir -p "${LOG_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh

# Docker build does not inherit proxy environment variables by default. Pass
# only variables already present in the caller environment; Docker keeps these
# predefined proxy arguments out of image history and normal build output.
PROXY_ARGS=()
for proxy_name in http_proxy https_proxy no_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY; do
  if [[ -n ${!proxy_name:-} ]]; then PROXY_ARGS+=(--build-arg "${proxy_name}"); fi
done

(
  cd "${PACKAGE_DIR}"
  sha256sum -c source-checksums.sha256
)

DOCKER_BUILDKIT=1 docker build --progress=plain --network="${BUILD_NETWORK}" \
  "${PROXY_ARGS[@]}" "$@" \
  --build-arg "MAKE_OPT=${MAKE_OPT}" \
  --build-arg "UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT}" \
  -t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"

docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
  | tee "${LOG_DIR}/build-versions.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
  | tee "${LOG_DIR}/image-id.txt"
(
  cd "${PACKAGE_DIR}"
  sha256sum Dockerfile .dockerignore aflnet-redis.patch redis_aflnet.c \
    parser-test.c prepare_seeds.py protocol_smoke.py coverage_replay.py \
    compare_replays.py plot_data_to_csv.py summarize_coverage.py \
    redis-state-mapping.md \
    source-lock.json \
    redis.dict redis.conf clean.sh parser-check.sh run.sh validate.sh \
    acceptance.sh coverage-run.sh source-checksums.sha256 \
    aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
    redis-8.10.3.tar.gz | tee "${LOG_DIR}/build-input-sha256.txt"
)
echo "PASS: pinned Redis/AFLNet image built; logs are in ${LOG_DIR}"
