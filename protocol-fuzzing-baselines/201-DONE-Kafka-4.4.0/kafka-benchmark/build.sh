#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
IMAGE=${1:-apache-kafka-fuzz-bench}
if (($# > 0)); then shift; fi
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs"}
MAKE_OPT=${MAKE_OPT:--j1}
UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT:-20260928T000000Z}
BUILD_NETWORK=${BUILD_NETWORK:-host}
BUILD_PULL=${BUILD_PULL:-true}
BUILD_MIN_AVAILABLE_MIB=1024
UBUNTU_BASE_IMAGE=ubuntu:24.04@sha256:f610ab94648195aa356059f5b41d6085c9d4d903c072430cdd1af7bdb646106b
UBUNTU_CONFIG_DIGEST=sha256:69f919497cada9a8611f3de61df902d9f94bf20f84552ef5bd93125c38608ef9
UBUNTU_MANIFEST_DIGEST=sha256:f610ab94648195aa356059f5b41d6085c9d4d903c072430cdd1af7bdb646106b

if [[ ${BUILD_PULL} != true && ${BUILD_PULL} != false ]]; then
	echo "BUILD_PULL 只能设为 true 或 false：${BUILD_PULL}" >&2
	exit 2
fi

# 保留宿主机余量；构建只展开已校验发行包并编译轻量 AFLNet/代理代码。
HOST_AVAILABLE_KIB=$(awk '/^MemAvailable:/ { print $2; exit }' /proc/meminfo)
if [[ ! ${HOST_AVAILABLE_KIB} =~ ^[0-9]+$ ]]; then
	echo "无法读取宿主机可用内存，已在 Docker 操作前停止构建。" >&2
	exit 75
fi
HOST_AVAILABLE_MIB=$((HOST_AVAILABLE_KIB / 1024))
if ((HOST_AVAILABLE_MIB < BUILD_MIN_AVAILABLE_MIB)); then
	echo "宿主机可用内存仅 ${HOST_AVAILABLE_MIB} MiB；Kafka 镜像构建至少需要 ${BUILD_MIN_AVAILABLE_MIB} MiB 可用内存。" >&2
	echo "已在拉取镜像和启动编译前停止。请释放内存或给虚拟机增加内存后再运行。" >&2
	exit 75
fi

mkdir -p "${LOG_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh
(
	cd "${PACKAGE_DIR}"
	sha256sum -c source-checksums.sha256
)

# 只转发调用环境中已有的代理变量，不把代理凭据写进镜像层。
PROXY_ARGS=()
for proxy_name in http_proxy https_proxy no_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY; do
	if [[ -n ${!proxy_name:-} ]]; then PROXY_ARGS+=(--build-arg "${proxy_name}"); fi
done

if [[ ${BUILD_PULL} == true ]]; then
	docker pull "${UBUNTU_BASE_IMAGE}" 2>&1 | tee "${LOG_DIR}/base-image-pull.log"
fi
BASE_IMAGE_ID=$(docker image inspect --format='{{.Id}}' "${UBUNTU_BASE_IMAGE}")
if [[ ${BASE_IMAGE_ID} != "${UBUNTU_CONFIG_DIGEST}" ]]; then
	echo "Ubuntu 基础镜像内容摘要不匹配；期望 ${UBUNTU_CONFIG_DIGEST}，实际 ${BASE_IMAGE_ID}" >&2
	exit 1
fi

DOCKER_BUILDKIT=1 docker build --progress=plain --network="${BUILD_NETWORK}" \
	"${PROXY_ARGS[@]}" "$@" \
	--build-arg "MAKE_OPT=${MAKE_OPT}" \
	--build-arg "UBUNTU_SNAPSHOT=${UBUNTU_SNAPSHOT}" \
	--build-arg "UBUNTU_CONFIG_DIGEST=${UBUNTU_CONFIG_DIGEST}" \
	--build-arg "UBUNTU_MANIFEST_DIGEST=${UBUNTU_MANIFEST_DIGEST}" \
	-t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"

docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
	| tee "${LOG_DIR}/build-versions.txt"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/package-manifest.txt \
	| tee "${LOG_DIR}/package-manifest.txt"
docker image inspect --format='image_id={{.Id}} repo_digests={{json .RepoDigests}}' "${UBUNTU_BASE_IMAGE}" \
	| tee "${LOG_DIR}/base-image.txt"
printf 'config_digest=%s\nmanifest_digest=%s\n' \
	"${UBUNTU_CONFIG_DIGEST}" "${UBUNTU_MANIFEST_DIGEST}" \
	>> "${LOG_DIR}/base-image.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
	| tee "${LOG_DIR}/image-id.txt"
(
	cd "${PACKAGE_DIR}"
	sha256sum Dockerfile .dockerignore README.md aflnet-kafka.patch aflnet-kafka-fuzz.patch \
		kafka_aflnet.c \
		kafka_jvm_agent.c kafka_launcher.c parser-test.c fault_probe_server.c kafka-broker.properties \
		kafka.dict prepare_seeds.py protocol_smoke.py coverage_replay.py \
		build.sh run.sh validate.sh acceptance.sh coverage-run.sh fault-probe.sh fault-probe-replay.py \
		clean.sh start-kafka.sh prepare-cluster.sh acceptance_report.py package.sh \
		kafka-state-mapping.md source-lock.json source-checksums.sha256 test-stubs/* seeds/* \
		seeds-manifest.json aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
	| tee "${LOG_DIR}/build-input-sha256.txt"
)
echo "通过：固定提交 Kafka/AFLNet 镜像已构建；日志目录：${LOG_DIR}"
