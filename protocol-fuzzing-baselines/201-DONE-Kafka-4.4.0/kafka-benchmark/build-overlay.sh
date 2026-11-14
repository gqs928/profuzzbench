#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
IMAGE=${1:-apache-kafka-fuzz-bench}
if (($# > 0)); then shift; fi
LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/build-logs-overlay"}
BASE_SOURCE_IMAGE=${KAFKA_BASE_SOURCE_IMAGE:-apache-kafka-fuzz-bench}
BASE_TAG=${KAFKA_BASE_IMAGE_TAG:-apache-kafka-fuzz-bench-base:20261014}
BASE_BUILD_LOGS=${KAFKA_BASE_BUILD_LOGS:-"${PACKAGE_DIR}/results/strict-acceptance-1cpu-smoke2-20261014/build-logs"}
EXPECTED_BASE_IMAGE_ID=sha256:793f166f6373d683631c70bf435a443bbffd43d770c2a8dda74e099df33947fd

mkdir -p "${LOG_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh
(
	cd "${PACKAGE_DIR}"
	sha256sum -c source-checksums.sha256
)

if ! docker image inspect "${BASE_TAG}" >/dev/null 2>&1; then
	docker image tag "${BASE_SOURCE_IMAGE}" "${BASE_TAG}"
fi
BASE_IMAGE_ID=$(docker image inspect --format='{{.Id}}' "${BASE_TAG}")
if [[ ${BASE_IMAGE_ID} != "${EXPECTED_BASE_IMAGE_ID}" ]]; then
	echo "本地派生构建基础镜像不匹配；期望 ${EXPECTED_BASE_IMAGE_ID}，实际 ${BASE_IMAGE_ID}" >&2
	exit 1
fi
BASE_KAFKA_VERSION=$(docker run --rm "${BASE_TAG}" sh -c "sed -n 's/^kafka_version=//p' /home/ubuntu/experiments/build-versions.txt | head -n1")
if [[ ${BASE_KAFKA_VERSION} != 4.4.0 ]]; then
	echo "拒绝派生构建：本地基础镜像实际 Kafka ${BASE_KAFKA_VERSION:-unknown}，目标必须为 4.4.0。" >&2
	exit 1
fi
if [[ ! -s ${BASE_BUILD_LOGS}/image-id.txt ]] || \
	! grep -Fq "image_id=${EXPECTED_BASE_IMAGE_ID}" "${BASE_BUILD_LOGS}/image-id.txt"; then
	echo "缺少与基础镜像 ID 对应的完整构建日志：${BASE_BUILD_LOGS}" >&2
	exit 1
fi
mkdir -p "${LOG_DIR}/base-build"
cp -a "${BASE_BUILD_LOGS}/." "${LOG_DIR}/base-build/"
printf 'base_image=%s\nbase_image_id=%s\n' "${BASE_TAG}" "${BASE_IMAGE_ID}" \
	> "${LOG_DIR}/overlay-base-image.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${BASE_TAG}" \
	> "${LOG_DIR}/base-image.txt"

DOCKER_BUILDKIT=1 docker build --progress=plain --network=host \
	--build-arg "BASE_IMAGE=${BASE_TAG}" \
	--build-arg "BASE_IMAGE_ID=${BASE_IMAGE_ID}" \
	"$@" -f "${PACKAGE_DIR}/Dockerfile.method-presence" \
	-t "${IMAGE}" "${PACKAGE_DIR}" 2>&1 | tee "${LOG_DIR}/docker-build.log"

docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
	| tee "${LOG_DIR}/build-versions.txt"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/package-manifest.txt \
	| tee "${LOG_DIR}/package-manifest.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
	| tee "${LOG_DIR}/image-id.txt"
(
	cd "${PACKAGE_DIR}"
	sha256sum .dockerignore Dockerfile.method-presence build-overlay.sh \
		kafka_jvm_agent.c aflnet-kafka-fuzz.patch start-kafka.sh coverage-run.sh \
		coverage_replay.py source-lock.json \
		source-checksums.sha256 acceptance.sh acceptance_report.py validate.sh \
		run.sh protocol_smoke.py fault-probe.sh fault-probe-replay.py \
		package.sh README.md \
		fault_probe_server.c \
		| tee "${LOG_DIR}/build-input-sha256.txt"
)
echo "通过：已验证基础镜像 ID，并更新 AFLNet、JVMTI 协议入口覆盖代理与 JaCoCo 回放启动脚本。"
