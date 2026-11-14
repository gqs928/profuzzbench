#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-postgres-protocol-fuzz}
if (($#)); then shift; fi
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs"}
MAKE_OPT=${MAKE_OPT:--j2}
UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT:-20260928T000000Z}
BUILD_NETWORK=${BUILD_NETWORK:-host}
mkdir -p "${LOG_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh
(cd "${PACKAGE_DIR}" && sha256sum -c source-checksums.sha256)

PROXY_ARGS=()
for proxy_name in http_proxy https_proxy no_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY; do
	if [[ -n ${!proxy_name:-} ]]; then PROXY_ARGS+=(--build-arg "${proxy_name}"); fi
done

DOCKER_BUILDKIT=1 docker build --progress=plain --network="${BUILD_NETWORK}" "${PROXY_ARGS[@]}" "$@" --build-arg "MAKE_OPT=${MAKE_OPT}" --build-arg "UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT}" -t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"
docker run --rm --network none "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt | tee "${LOG_DIR}/build-versions.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" | tee "${LOG_DIR}/image-id.txt"
(cd "${PACKAGE_DIR}" && sha256sum Dockerfile .dockerignore aflnet-postgres.patch aflnet-no-forkserver-fix.patch postgres_aflnet.c parser-test.c prepare_seeds.py protocol_smoke.py seed_replay.py coverage_replay.py summarize_coverage.py acceptance_report.py postgres-state-mapping.md postgres.dict clean.sh parser-check.sh run.sh target-launcher.c validate.sh acceptance.sh acceptance-inner.sh coverage-run.sh fault-probe.sh fault_probe_server.c fault_probe_replay.py package.sh source-checksums.sha256 aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz postgresql-18.6.tar.bz2 | tee "${LOG_DIR}/build-input-sha256.txt")
echo "通过：固定源码和依赖的 PostgreSQL/AFLNet 容器已构建；日志位于 ${LOG_DIR}"
