#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
IMAGE=${1:-freeradius-radius-fuzz}
RESULTS_DIR=${2:-"${PACKAGE_DIR}/results/strict-acceptance"}
SMOKE_DURATION=${RADIUS_SMOKE_FUZZ_DURATION:-90s}
FUZZ_DURATION=30m

if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "完整验收目录非空，请指定全新目录：${RESULTS_DIR}" >&2
	exit 2
fi
mkdir -p "${RESULTS_DIR}"

BUILD_LOG_DIR="${RESULTS_DIR}/build-logs" \
	"${PACKAGE_DIR}/build.sh" "${IMAGE}" --no-cache
"${PACKAGE_DIR}/validate.sh" "${IMAGE}" "${RESULTS_DIR}/preflight" "${SMOKE_DURATION}"

mkdir -p "${RESULTS_DIR}/fuzz-30m"
date -u '+started_at_utc=%Y-%m-%dT%H:%M:%SZ' > "${RESULTS_DIR}/fuzz-30m/runtime.txt"
docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" \
	-v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/run.sh /results/fuzz-30m/aflnet 30m \
	2>&1 | tee "${RESULTS_DIR}/fuzz-30m/run.log"
date -u '+finished_at_utc=%Y-%m-%dT%H:%M:%SZ' >> "${RESULTS_DIR}/fuzz-30m/runtime.txt"

test -s "${RESULTS_DIR}/fuzz-30m/aflnet/fuzzer_stats"
test -s "${RESULTS_DIR}/fuzz-30m/aflnet/plot_data"
test -s "${RESULTS_DIR}/fuzz-30m/aflnet/ipsm.dot"
docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" \
	-v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/coverage-run.sh \
		/results/fuzz-30m/aflnet/queue /results/coverage \
		/results/fuzz-30m/aflnet/replayable-crashes \
	2>&1 | tee "${RESULTS_DIR}/coverage-run.log"

docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" \
	-v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/fault-probe.sh /results/fault-probe \
	2>&1 | tee "${RESULTS_DIR}/fault-probe-run.log"

python3 "${PACKAGE_DIR}/acceptance_report.py" "${RESULTS_DIR}" \
	> "${RESULTS_DIR}/ACCEPTANCE-REPORT.md"
(
	cd "${RESULTS_DIR}"
	find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
cp "${RESULTS_DIR}/ACCEPTANCE-REPORT.md" "${PACKAGE_DIR}/RESULTS.md"
"${PACKAGE_DIR}/package.sh"
echo "完整验收通过；报告：${RESULTS_DIR}/ACCEPTANCE-REPORT.md"
