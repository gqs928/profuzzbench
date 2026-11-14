#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-inspircd-fuzz}
RESULTS_DIR=${2:-"$(pwd)/inspircd-validation"}
DURATION=${3:-60s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
chmod +x "${PACKAGE_DIR}"/*.sh
docker image inspect "${IMAGE}" >/dev/null
mkdir -p "${RESULTS_DIR}"

docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" bash /workspace/protocol_smoke.sh /results/protocol-smoke \
  2>&1 | tee "${RESULTS_DIR}/protocol-smoke.log"
docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" python3 /workspace/repeatability.py /results/repeatability 10 \
  2>&1 | tee "${RESULTS_DIR}/repeatability.log"
docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" bash /workspace/run.sh aflnet /results/smoke '' "${DURATION}" \
  2>&1 | tee "${RESULTS_DIR}/fuzz.log"
docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" bash /workspace/coverage_replay.sh /results/smoke 1 \
  2>&1 | tee "${RESULTS_DIR}/coverage-replay.log"
docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" python3 /workspace/coverage_check.py \
  /results/smoke/cov_html/index.html /workspace/coverage-core-files.txt \
  2>&1 | tee "${RESULTS_DIR}/coverage-check.log"
docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" python3 /workspace/crash_injection.py /results/crash-injection 180 \
  2>&1 | tee "${RESULTS_DIR}/crash-injection.log"

test -s "${RESULTS_DIR}/smoke/fuzzer_stats"
test -s "${RESULTS_DIR}/smoke/ipsm.dot"
test -s "${RESULTS_DIR}/smoke/cov_over_time.csv"
test -s "${RESULTS_DIR}/crash-injection/crash-injection.json"
docker run --rm -v "${RESULTS_DIR}:/results" "${IMAGE}" \
  dot -Tplain /results/smoke/ipsm.dot > "${RESULTS_DIR}/smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' "${RESULTS_DIR}/smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' "${RESULTS_DIR}/smoke/ipsm.plain"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
  > "${RESULTS_DIR}/build-versions.txt"
echo "PASS: IRC behavior, repeatability, AFLNet state feedback, coverage and controlled-crash replay; evidence=${RESULTS_DIR}"
