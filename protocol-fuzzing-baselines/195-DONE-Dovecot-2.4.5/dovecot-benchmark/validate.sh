#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-dovecot-imap-fuzz}
RESULTS_DIR=${2:-$(pwd)/dovecot-validation}
DURATION=${3:-30m}
REPETITIONS=${IMAP_SMOKE_REPETITIONS:-10}
FAULT_PROBE_DURATION=${DOVECOT_FAULT_PROBE_DURATION:-30m}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

docker image inspect "${IMAGE}" >/dev/null
mkdir -p "${RESULTS_DIR}"
RESULTS_DIR=$(cd "${RESULTS_DIR}" && pwd)
chmod +x "${PACKAGE_DIR}"/*.sh
: > "${RESULTS_DIR}/stage-statuses.txt"

run_stage() {
  local name=$1
  local log=$2
  shift 2
  set +e
  "$@" 2>&1 | tee "${RESULTS_DIR}/${log}"
  local status=${PIPESTATUS[0]}
  set -e
  printf '%s=%s\n' "${name}" "${status}" >> "${RESULTS_DIR}/stage-statuses.txt"
  return 0
}

run_stage parser parser-check-container.log docker run --rm --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" bash /workspace/parser-check.sh /results/parser-check.log

run_stage protocol-smoke protocol-smoke-container.log docker run --rm --hostname localhost --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" python3 /workspace/protocol_smoke.py \
    /results/protocol-smoke "${REPETITIONS}"

run_stage seed-replay seed-replay-container.log docker run --rm --hostname localhost --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" python3 /workspace/seed_replay.py \
    /workspace/seeds/login-mailbox.imap /results/seed-replay \
    --repeat 10 --variant afl

run_stage fuzz fuzz-container.log docker run --rm --user root --hostname localhost --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" bash /workspace/run.sh "/results/fuzz-${DURATION}" "${DURATION}"

run_stage state-graph state-graph-container.log docker run --rm --user root --network none \
  -v "${RESULTS_DIR}:/results" "${IMAGE}" \
  dot -Tplain "/results/fuzz-${DURATION}/ipsm.dot" \
    -o "/results/fuzz-${DURATION}/ipsm.plain"

run_stage coverage coverage-container.log docker run --rm --hostname localhost --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" bash /workspace/coverage-run.sh \
    "/results/fuzz-${DURATION}" /results/coverage "${COVERAGE_MAX_INPUTS:-0}"

run_stage fault-probe fault-probe-container.log docker run --rm --user root --network none \
  -e "DOVECOT_FAULT_PROBE_DURATION=${FAULT_PROBE_DURATION}" \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" bash /workspace/fault-probe.sh /results/fault-probe

docker run --rm --user root --network none -v "${RESULTS_DIR}:/results" "${IMAGE}" \
  chmod -R a+rX /results
set +e
python3 "${PACKAGE_DIR}/acceptance_report.py" "${RESULTS_DIR}"
REPORT_STATUS=$?
set -e
(
  cd "${RESULTS_DIR}"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
if [[ ${REPORT_STATUS} -ne 0 ]]; then exit "${REPORT_STATUS}"; fi
echo "通过：Dovecot IMAP 模糊测试验收证据位于 ${RESULTS_DIR}"
