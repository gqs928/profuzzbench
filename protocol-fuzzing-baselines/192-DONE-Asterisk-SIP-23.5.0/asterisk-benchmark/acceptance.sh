#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
IMAGE=${1:-asterisk-sip-fuzz}
RESULTS_DIR=${2:-"${PACKAGE_DIR}/results/strict-acceptance"}
SMOKE_FUZZ_DURATION=${ASTERISK_SMOKE_FUZZ_DURATION:-180s}
FUZZ_DURATION=30m
QUEUE_LIMIT=${ASTERISK_COVERAGE_QUEUE_LIMIT:-200}

if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "严格验收目录非空，请指定全新目录：${RESULTS_DIR}" >&2
	exit 2
fi
mkdir -p "${RESULTS_DIR}"

BUILD_LOG_DIR=${RESULTS_DIR}/build-logs \
	"${PACKAGE_DIR}/build.sh" "${IMAGE}" --no-cache
"${PACKAGE_DIR}/validate.sh" "${IMAGE}" \
	"${RESULTS_DIR}/preflight" "${SMOKE_FUZZ_DURATION}"

mkdir -p "${RESULTS_DIR}/fuzz-30m"
date -u '+started_at_utc=%Y-%m-%dT%H:%M:%SZ' \
	> "${RESULTS_DIR}/fuzz-30m/runtime.txt"
docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/run.sh /results/fuzz-30m/aflnet "${FUZZ_DURATION}" \
	2>&1 | tee "${RESULTS_DIR}/fuzz-30m/run.log"
date -u '+finished_at_utc=%Y-%m-%dT%H:%M:%SZ' \
	>> "${RESULTS_DIR}/fuzz-30m/runtime.txt"
test -s "${RESULTS_DIR}/fuzz-30m/aflnet/fuzzer_stats"
test -s "${RESULTS_DIR}/fuzz-30m/aflnet/plot_data"
test -s "${RESULTS_DIR}/fuzz-30m/aflnet/ipsm.dot"
cp "${RESULTS_DIR}/fuzz-30m/aflnet.parameters.txt" \
	"${RESULTS_DIR}/fuzz-30m/parameters.txt"
VARIABLE_PATH_GROUPS=$(python3 "${PACKAGE_DIR}/audit_variable_paths.py" \
	prepare "${RESULTS_DIR}" 10)
if [[ ${VARIABLE_PATH_GROUPS} -gt 0 ]]; then
	docker run --rm --network none \
		-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
		"${IMAGE}" python3 /workspace/coverage_replay.py \
			--fuzz-dir /results/variable-path-replay-input \
			--output /results/variable-path-replay --limit 0 \
		2>&1 | tee "${RESULTS_DIR}/variable-path-replay-run.log"
fi
python3 "${PACKAGE_DIR}/audit_variable_paths.py" \
	verify "${RESULTS_DIR}" 10

docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/coverage-run.sh \
		/results/fuzz-30m/aflnet "/results/coverage" "${QUEUE_LIMIT}" \
	2>&1 | tee "${RESULTS_DIR}/coverage-run.log"
docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/fault-probe.sh /results/fault-probe \
	2>&1 | tee "${RESULTS_DIR}/fault-probe-run.log"

python3 "${PACKAGE_DIR}/acceptance_report.py" "${RESULTS_DIR}" \
	> "${RESULTS_DIR}/ACCEPTANCE-REPORT.md"
cp "${RESULTS_DIR}/ACCEPTANCE-REPORT.md" "${PACKAGE_DIR}/RESULTS.md"
(
	cd "${RESULTS_DIR}"
	find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
"${PACKAGE_DIR}/package.sh" \
	"$(dirname "${PACKAGE_DIR}")/asterisk-sip-fuzz-benchmark-delivery-2026-10-15.zip" \
	"${RESULTS_DIR}"
echo "严格验收通过；报告：${RESULTS_DIR}/ACCEPTANCE-REPORT.md"
