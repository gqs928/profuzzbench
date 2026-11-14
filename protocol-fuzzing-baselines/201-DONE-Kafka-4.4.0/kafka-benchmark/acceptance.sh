#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
IMAGE=${1:-apache-kafka-fuzz-bench}
RESULTS_DIR=${2:-"${PACKAGE_DIR}/results/strict-acceptance"}
PACKAGE_OUTPUT=${PACKAGE_OUTPUT:-"$(dirname "${PACKAGE_DIR}")/$(basename "${RESULTS_DIR}")-delivery.zip"}
FUZZ_DURATION=30m
ACCEPTANCE_NO_CACHE=${ACCEPTANCE_NO_CACHE:-false}
KAFKA_CPU_LIMIT=${KAFKA_CPU_LIMIT:-1}
KAFKA_MEMORY_LIMIT=${KAFKA_MEMORY_LIMIT:-1g}
KAFKA_BUILD_MODE=${KAFKA_BUILD_MODE:-full}
BUILD_MIN_AVAILABLE_MIB=1024

if [[ ${ACCEPTANCE_NO_CACHE} != true && ${ACCEPTANCE_NO_CACHE} != false ]]; then
	echo "ACCEPTANCE_NO_CACHE 只能设为 true 或 false：${ACCEPTANCE_NO_CACHE}" >&2
	exit 2
fi
if [[ ! ${KAFKA_CPU_LIMIT} =~ ^[0-9]+([.][0-9]+)?$ ]] || [[ ${KAFKA_CPU_LIMIT} == 0 ]]; then
	echo "KAFKA_CPU_LIMIT 必须是大于零的十进制核数：${KAFKA_CPU_LIMIT}" >&2
	exit 2
fi
if [[ ${KAFKA_BUILD_MODE} != full ]]; then
	echo "当前严格验收只支持已锁定 4.4.0 官方发行归档的 full 构建；overlay 基础镜像仍是 4.2.2，拒绝复用。" >&2
	exit 2
fi

# 在创建验收目录前检查内存；低于构建安全线时不留下半成品目录。
HOST_AVAILABLE_KIB=$(awk '/^MemAvailable:/ { print $2; exit }' /proc/meminfo)
if [[ ! ${HOST_AVAILABLE_KIB} =~ ^[0-9]+$ ]]; then
	echo "无法读取宿主机可用内存，验收已在 Docker 操作前停止。" >&2
	exit 75
fi
HOST_AVAILABLE_MIB=$((HOST_AVAILABLE_KIB / 1024))
if ((HOST_AVAILABLE_MIB < BUILD_MIN_AVAILABLE_MIB)); then
	echo "宿主机可用内存仅 ${HOST_AVAILABLE_MIB} MiB；Kafka 构建至少需要 ${BUILD_MIN_AVAILABLE_MIB} MiB 可用内存。" >&2
	echo "验收未启动。请给虚拟机增加内存后再运行。" >&2
	exit 75
fi

if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "完整验收目录非空，请指定全新目录：${RESULTS_DIR}" >&2
	exit 2
fi
mkdir -p "${RESULTS_DIR}"
cat > "${RESULTS_DIR}/resource-limits.txt" <<EOF
host_visible_cpus=$(getconf _NPROCESSORS_ONLN)
host_available_memory_mib=${HOST_AVAILABLE_MIB}
build_min_available_memory_mib=${BUILD_MIN_AVAILABLE_MIB}
docker_cpu_quota=${KAFKA_CPU_LIMIT}
docker_memory_limit=${KAFKA_MEMORY_LIMIT}
docker_swap_limit=disabled
build_mode=${KAFKA_BUILD_MODE}
kafka_build=verified-official-release-binary; no local Gradle compile
broker_heap_max=384m
java_active_processor_count=1
make_jobs=1
EOF

BUILD_ARGS=()
if [[ ${ACCEPTANCE_NO_CACHE} == true ]]; then BUILD_ARGS+=(--no-cache); fi
BUILD_LOG_DIR="${RESULTS_DIR}/build-logs"
BUILD_LOG_DIR="${BUILD_LOG_DIR}" "${PACKAGE_DIR}/build.sh" "${IMAGE}" "${BUILD_ARGS[@]}"
KAFKA_CPU_LIMIT="${KAFKA_CPU_LIMIT}" KAFKA_MEMORY_LIMIT="${KAFKA_MEMORY_LIMIT}" \
	"${PACKAGE_DIR}/validate.sh" "${IMAGE}" "${RESULTS_DIR}/preflight" 120s

mkdir -p "${RESULTS_DIR}/fuzz-30m"
date -u '+started_at_utc=%Y-%m-%dT%H:%M:%SZ' > "${RESULTS_DIR}/fuzz-30m/runtime.txt"
docker run --rm --cpus="${KAFKA_CPU_LIMIT}" --memory="${KAFKA_MEMORY_LIMIT}" \
	--memory-swap="${KAFKA_MEMORY_LIMIT}" --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	-e "KAFKA_CPU_LIMIT=${KAFKA_CPU_LIMIT}" -e "KAFKA_MEMORY_LIMIT=${KAFKA_MEMORY_LIMIT}" \
	"${IMAGE}" bash /workspace/run.sh /results/fuzz-30m/aflnet 30m \
	2>&1 | tee "${RESULTS_DIR}/fuzz-30m/run.log"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
	> "${RESULTS_DIR}/fuzz-build-versions.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
	> "${RESULTS_DIR}/fuzz-image-id.txt"
date -u '+finished_at_utc=%Y-%m-%dT%H:%M:%SZ' >> "${RESULTS_DIR}/fuzz-30m/runtime.txt"

test -s "${RESULTS_DIR}/fuzz-30m/aflnet/fuzzer_stats"
test -s "${RESULTS_DIR}/fuzz-30m/aflnet/plot_data"
test -s "${RESULTS_DIR}/fuzz-30m/aflnet/ipsm.dot"
docker run --rm --cpus="${KAFKA_CPU_LIMIT}" --memory="${KAFKA_MEMORY_LIMIT}" \
	--memory-swap="${KAFKA_MEMORY_LIMIT}" --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/coverage-run.sh \
		/results/fuzz-30m/aflnet /results/coverage \
	2>&1 | tee "${RESULTS_DIR}/coverage-run.log"

docker run --rm --cpus="${KAFKA_CPU_LIMIT}" --memory="${KAFKA_MEMORY_LIMIT}" \
	--memory-swap="${KAFKA_MEMORY_LIMIT}" --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/fault-probe.sh /results/fault-probe \
	2>&1 | tee "${RESULTS_DIR}/fault-probe-run.log"

python3 "${PACKAGE_DIR}/acceptance_report.py" "${RESULTS_DIR}" \
	> "${RESULTS_DIR}/ACCEPTANCE-REPORT.md"
(
	cd "${RESULTS_DIR}"
	CHECKSUM_EXCLUDES=()
	if [[ -d preflight-jacoco-fix ]]; then CHECKSUM_EXCLUDES+=(-not -path './preflight/*'); fi
	if [[ -d coverage-jacoco-fix ]]; then CHECKSUM_EXCLUDES+=(-not -path './coverage/*'); fi
	find . -type f ! -name SHA256SUMS "${CHECKSUM_EXCLUDES[@]}" \
		-print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
cp "${RESULTS_DIR}/ACCEPTANCE-REPORT.md" "${PACKAGE_DIR}/RESULTS.md"
"${PACKAGE_DIR}/package.sh" "${PACKAGE_OUTPUT}" "${RESULTS_DIR}"
echo "完整验收通过；报告：${RESULTS_DIR}/ACCEPTANCE-REPORT.md"
