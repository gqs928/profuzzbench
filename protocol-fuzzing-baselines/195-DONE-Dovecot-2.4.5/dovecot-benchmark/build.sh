#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-dovecot-imap-fuzz}
if (($# > 0)); then shift; fi
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs"}
MAKE_OPT=${MAKE_OPT:--j2}
UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT:-20260928T000000Z}
BUILD_NETWORK=${BUILD_NETWORK:-host}
PULL_BASE_IMAGE=${PULL_BASE_IMAGE:-1}
CLEAR_BUILD_PROXY=${CLEAR_BUILD_PROXY:-0}
NO_CACHE_BUILD=${NO_CACHE_BUILD:-1}
mkdir -p "${LOG_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh

PULL_ARGS=()
if [[ ${PULL_BASE_IMAGE} == 1 ]]; then PULL_ARGS+=(--pull); fi
PROXY_ARGS=()
if [[ ${CLEAR_BUILD_PROXY} == 1 ]]; then
  for proxy_name in http_proxy https_proxy no_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY; do
    PROXY_ARGS+=(--build-arg "${proxy_name}=")
  done
else
  for proxy_name in http_proxy https_proxy no_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY; do
    if [[ -n ${!proxy_name:-} ]]; then PROXY_ARGS+=(--build-arg "${proxy_name}"); fi
  done
fi

(
  cd "${PACKAGE_DIR}"
  sha256sum -c source-checksums.sha256
)

NO_CACHE_ARGS=()
if [[ ${NO_CACHE_BUILD} == 1 ]]; then NO_CACHE_ARGS+=(--no-cache); fi
DOCKER_BUILDKIT=1 docker build "${PULL_ARGS[@]}" "${NO_CACHE_ARGS[@]}" --progress=plain \
  --network="${BUILD_NETWORK}" --build-arg "MAKE_OPT=${MAKE_OPT}" \
  --build-arg "UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT}" \
  "${PROXY_ARGS[@]}" "$@" \
  -t "${IMAGE}-base" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"

DOCKER_BUILDKIT=1 docker build "${NO_CACHE_ARGS[@]}" \
  --progress=plain --build-arg "BASE_IMAGE=${IMAGE}-base" \
  -f "${PACKAGE_DIR}/Dockerfile.runtime" -t "${IMAGE}" "${PACKAGE_DIR}" \
  2>&1 | tee -a "${LOG_DIR}/docker-build.log"

docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
  | tee "${LOG_DIR}/build-versions.txt"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/package-manifest.txt \
  | tee "${LOG_DIR}/package-manifest.txt"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/ucd-sha256.txt \
  | tee "${LOG_DIR}/ucd-sha256.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
  | tee "${LOG_DIR}/image-id.txt"

(
  cd "${PACKAGE_DIR}"
  sha256sum README.md Dockerfile .dockerignore source-lock.json source-checksums.sha256 \
    ucd-checksums.sha256 \
    aflnet-imap.patch imap_aflnet.c parser-test.c dovecot.conf passwd imap.dict \
    prepare_seeds.py prepare_maildir.py seeds-manifest.json seeds/* \
    protocol_smoke.py imap_tools.py seed_replay.py coverage_run.py coverage-run.sh parser-check.sh \
    acceptance_report.py fault_probe_server.c fault-seeds/* fault-probe.sh \
    dovecot-fault-injection.patch dovecot-fault.dict fault-kill-helper.c dovecot-fault-seeds/* \
    clean.sh reset-state.sh \
    start-server.sh start-server-runtime.sh dovecot-root-launcher.sh \
    dovecot-root-launcher-runtime.sh \
    Dockerfile.runtime sudoers.dovecot-benchmark \
    clean-maildir-runtime.sh run.sh validate.sh full-acceptance.sh build.sh state-mapping.md \
    fault.dict sudoers.dovecot-benchmark-runtime \
    aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
    dovecot-core-0cbb641e3e88d1616c2e8c1ff109c67c0985ddc6.tar.gz \
    | tee "${LOG_DIR}/build-input-sha256.txt"
)
echo "通过：固定 Dovecot/AFLNet 源码构建完成；构建记录位于 ${LOG_DIR}"
