#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-freeradius-radius-fuzz}
if (($# > 0)); then shift; fi
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs"}
MAKE_OPT=${MAKE_OPT:--j2}
UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT:-20260928T000000Z}
BUILD_NETWORK=${BUILD_NETWORK:-host}

mkdir -p "${LOG_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh
(
	cd "${PACKAGE_DIR}"
	sha256sum -c source-checksums.sha256
)

# 仅转发调用环境中已有的代理变量，不把凭据写入镜像层。
PROXY_ARGS=()
for proxy_name in http_proxy https_proxy no_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY; do
	if [[ -n ${!proxy_name:-} ]]; then PROXY_ARGS+=(--build-arg "${proxy_name}"); fi
done

DOCKER_BUILDKIT=1 docker build --progress=plain --network="${BUILD_NETWORK}" \
	"${PROXY_ARGS[@]}" "$@" \
	--build-arg "MAKE_OPT=${MAKE_OPT}" \
	--build-arg "UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT}" \
	-t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"

docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
	| tee "${LOG_DIR}/build-versions.txt"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/package-manifest.txt \
	| tee "${LOG_DIR}/package-manifest.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
	| tee "${LOG_DIR}/image-id.txt"
(
	cd "${PACKAGE_DIR}"
	sha256sum Dockerfile .dockerignore aflnet-radius.patch radius_aflnet.c \
		build-scope.patch parser-test.c prepare_seeds.py protocol_smoke.py \
		coverage_replay.py summarize_coverage.py acceptance_report.py fault-probe.sh \
		site-default clients.conf authorize radius-state-mapping.md radius.dict \
		clean.sh build.sh run.sh validate.sh acceptance.sh coverage-run.sh package.sh README.md \
		source-checksums.sha256 freeradius-3.2.10.tar.gz seeds/* seeds-manifest.json \
		aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
	| tee "${LOG_DIR}/build-input-sha256.txt"
)

echo "PASS: 固定版本 FreeRADIUS/AFLNet 镜像已构建；日志目录：${LOG_DIR}"
