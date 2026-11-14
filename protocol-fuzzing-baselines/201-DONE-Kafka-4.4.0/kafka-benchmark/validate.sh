#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-apache-kafka-fuzz-bench}
RESULTS_DIR=${2:-"$(pwd)/kafka-validation"}
FUZZ_DURATION=${3:-120s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
REPETITIONS=${KAFKA_SMOKE_REPETITIONS:-10}
KAFKA_CPU_LIMIT=${KAFKA_CPU_LIMIT:-1}
KAFKA_MEMORY_LIMIT=${KAFKA_MEMORY_LIMIT:-1g}

docker image inspect "${IMAGE}" >/dev/null
if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "验收目录非空，请选择全新目录：${RESULTS_DIR}" >&2
	exit 2
fi
mkdir -p "${RESULTS_DIR}"

docker run --rm --cpus="${KAFKA_CPU_LIMIT}" --memory="${KAFKA_MEMORY_LIMIT}" \
	--memory-swap="${KAFKA_MEMORY_LIMIT}" --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	-e "KAFKA_SMOKE_REPETITIONS=${REPETITIONS}" -e "KAFKA_CPU_LIMIT=${KAFKA_CPU_LIMIT}" \
	-e "KAFKA_MEMORY_LIMIT=${KAFKA_MEMORY_LIMIT}" \
	"${IMAGE}" python3 /workspace/protocol_smoke.py /results/protocol-smoke "${REPETITIONS}" \
	2>&1 | tee "${RESULTS_DIR}/protocol-smoke.log"
mkdir -p "${RESULTS_DIR}/smoke-seeds"
cp "${PACKAGE_DIR}/seeds/api-versions.bin" "${RESULTS_DIR}/smoke-seeds/"
cp "${PACKAGE_DIR}/seeds/metadata-produce.bin" "${RESULTS_DIR}/smoke-seeds/"
docker run --rm --cpus="${KAFKA_CPU_LIMIT}" --memory="${KAFKA_MEMORY_LIMIT}" \
	--memory-swap="${KAFKA_MEMORY_LIMIT}" --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	-e "INPUTS=/results/smoke-seeds" -e AFL_EXEC_TIMEOUT_MS=45000 \
	-e "KAFKA_CPU_LIMIT=${KAFKA_CPU_LIMIT}" -e "KAFKA_MEMORY_LIMIT=${KAFKA_MEMORY_LIMIT}" \
	"${IMAGE}" bash /workspace/run.sh /results/fuzz-smoke "${FUZZ_DURATION}" \
	2>&1 | tee "${RESULTS_DIR}/fuzz-smoke.log"

test -s "${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
test -s "${RESULTS_DIR}/fuzz-smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
	"${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
# 对应图片中的“覆盖轨迹基本一致”：短预检要求 AFL 校准稳定度至少 90%。
awk -F: '
/^stability[[:space:]]*:/ {
	value=$2; gsub(/[[:space:]%]/, "", value)
	printf "短预检 AFLNet 覆盖稳定度：%s%%\n", value
	if ((value + 0) < 90) exit 1
	found=1
}
END { if (!found) exit 1 }
' "${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
# 短预检确认真实 ApiVersions 响应反馈；正式 30 分钟验收检查完整业务状态图。
for state in 1; do
	if ! awk -v wanted="${state}" '$1 == wanted && $2 ~ /^\[/ { found=1 } END { exit !found }' \
		"${RESULTS_DIR}/fuzz-smoke/ipsm.dot"; then
		echo "Kafka IPSM 状态图缺少 ApiVersions 响应反馈状态：${state}" >&2
		exit 1
	fi
done

docker run --rm --cpus="${KAFKA_CPU_LIMIT}" --memory="${KAFKA_MEMORY_LIMIT}" \
	--memory-swap="${KAFKA_MEMORY_LIMIT}" "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
	> "${RESULTS_DIR}/build-versions.txt"
docker image inspect --format='image_id={{.Id}} created={{.Created}}' "${IMAGE}" \
	> "${RESULTS_DIR}/image-id.txt"
(
	cd "${RESULTS_DIR}"
	find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "通过：参考/插桩会话、10 轮重置回放、AFLNet 覆盖和 Kafka 状态图；证据：${RESULTS_DIR}"
