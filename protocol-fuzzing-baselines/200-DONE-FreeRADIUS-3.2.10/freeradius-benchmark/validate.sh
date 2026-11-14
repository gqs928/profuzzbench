#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-freeradius-radius-fuzz}
RESULTS_DIR=${2:-"$(pwd)/freeradius-validation"}
FUZZ_DURATION=${3:-60s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

docker image inspect "${IMAGE}" >/dev/null
if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "验收结果目录非空，请选择新目录：${RESULTS_DIR}" >&2
	exit 2
fi
mkdir -p "${RESULTS_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh

docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	-e "RADIUS_SMOKE_REPETITIONS=${RADIUS_SMOKE_REPETITIONS:-10}" \
	"${IMAGE}" python3 /workspace/protocol_smoke.py /results/protocol-smoke \
	2>&1 | tee "${RESULTS_DIR}/protocol-smoke.log"
docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/run.sh /results/fuzz-smoke "${FUZZ_DURATION}" \
	2>&1 | tee "${RESULTS_DIR}/fuzz-smoke.log"

test -s "${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
test -s "${RESULTS_DIR}/fuzz-smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
	"${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
docker run --rm -i "${IMAGE}" dot -Tplain \
	< "${RESULTS_DIR}/fuzz-smoke/ipsm.dot" > "${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' \
	"${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' \
	"${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
for state in 2 3 5; do
	if ! awk '$1 == "node" { print $2 }' "${RESULTS_DIR}/fuzz-smoke/ipsm.plain" \
		| grep -Fxq "${state}"; then
		echo "IPSM 状态图缺少预期 RADIUS Code 状态：${state}" >&2
		exit 1
	fi
done
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
	> "${RESULTS_DIR}/build-versions.txt"
(
	cd "${RESULTS_DIR}"
	find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "通过：UDP/TCP 业务回放、10 轮重置一致性、AFLNet 执行和 RADIUS 状态图；证据目录：${RESULTS_DIR}"
