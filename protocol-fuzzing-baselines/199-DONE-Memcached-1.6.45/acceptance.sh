#!/usr/bin/env bash
set -euo pipefail

# Full acceptance run. Default duration is 30 minutes; pass a shorter duration
# (for example 60s) only for a smoke/preflight run, not final acceptance.
IMAGE=${1:-memcached-fuzz}
RESULTS_DIR=${2:-$(pwd)/results/memcached-acceptance-$(date +%Y%m%d-%H%M%S)}
DURATION=${3:-30m}
SKIPCOUNT=${SKIPCOUNT:-5}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

chmod +x "${PACKAGE_DIR}"/*.sh
docker image inspect "${IMAGE}" >/dev/null
mkdir -p "${RESULTS_DIR}"
RESULTS_DIR=$(cd "$(dirname "${RESULTS_DIR}")" && pwd)/$(basename "${RESULTS_DIR}")

docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" bash /workspace/protocol_smoke.sh /results/protocol-smoke 2>&1 | tee "${RESULTS_DIR}/protocol-smoke.log"

docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" python3 /workspace/repeatability.py --server /home/ubuntu/experiments/memcached-gcov/memcached --seed /home/ubuntu/experiments/in-memcached/seed-business --out /results/repeatability --runs 10 2>&1 | tee "${RESULTS_DIR}/repeatability.log"

docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" bash /workspace/run.sh aflnet /results/fuzz '' "${DURATION}" "${SKIPCOUNT}" 2>&1 | tee "${RESULTS_DIR}/fuzz.log"
test -s "${RESULTS_DIR}/fuzz/fuzzer_stats"
test -s "${RESULTS_DIR}/fuzz/ipsm.dot"
test -s "${RESULTS_DIR}/fuzz/fuzz_bitmap"
docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" dot -Tplain /results/fuzz/ipsm.dot > "${RESULTS_DIR}/fuzz/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' "${RESULTS_DIR}/fuzz/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' "${RESULTS_DIR}/fuzz/ipsm.plain"

docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" bash /workspace/cov_script.sh /results/fuzz "${SKIPCOUNT}" 2>&1 | tee "${RESULTS_DIR}/coverage.log"
test -s "${RESULTS_DIR}/fuzz/cov_over_time.csv"
test -s "${RESULTS_DIR}/fuzz/cov_html/index.html"
test "$(wc -l < "${RESULTS_DIR}/fuzz/cov_over_time.csv")" -ge 2
docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" python3 /workspace/coverage_check.py /results/fuzz/cov_html/index.html /results/coverage-core-files.txt 2>&1 | tee "${RESULTS_DIR}/coverage-core-files.log"

docker run --rm -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" bash /workspace/crash_injection.sh /results/crash-injection 2>&1 | tee "${RESULTS_DIR}/crash-injection.log"
test -s "${RESULTS_DIR}/crash-injection/summary.txt"

docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt > "${RESULTS_DIR}/build-versions.txt"
VARIABLE_PATHS=$(awk -F: '/^variable_paths[[:space:]]*:/ {gsub(/[[:space:]]/, "", $2); print $2}' "${RESULTS_DIR}/fuzz/fuzzer_stats")
if [[ -d ${RESULTS_DIR}/fuzz/.state/variable_behavior ]]; then
  find "${RESULTS_DIR}/fuzz/.state/variable_behavior" -type f -printf '%f\n' | sort > "${RESULTS_DIR}/variable-paths.txt"
fi
{
  echo 'Acceptance checks executed by acceptance.sh.'
  echo "fuzz_duration=${DURATION}"
  echo "variable_paths=${VARIABLE_PATHS:-not-reported}"
  echo 'Protocol: Memcached ASCII over TCP; target port 11211; AFLNet -P MEMCACHED -E -K -R.'
  echo 'Build identity: see build-versions.txt; all upstream sources are pinned by commit and image digest.'
  echo 'Reset/repeatability: repeatability/repeatability.csv and ten response logs.'
  echo 'Protocol states: fuzz/ipsm.dot and fuzz/ipsm.plain.'
  echo 'Coverage: fuzz/cov_over_time.csv and fuzz/cov_html/index.html.'
  echo 'Crash observation: crash-injection/summary.txt, controlled-crash.sample and replay.log.'
} > "${RESULTS_DIR}/acceptance-summary.txt"

mkdir -p "${RESULTS_DIR}/source-snapshot"
cp "${PACKAGE_DIR}/Dockerfile" "${PACKAGE_DIR}/.dockerignore" "${PACKAGE_DIR}/aflnet-memcached.patch" "${PACKAGE_DIR}/memcached_aflnet.c" "${PACKAGE_DIR}/parser-test.c" "${PACKAGE_DIR}/build.sh" "${PACKAGE_DIR}/acceptance.sh" "${PACKAGE_DIR}/validate.sh" "${PACKAGE_DIR}/run.sh" "${PACKAGE_DIR}/clean.sh" "${PACKAGE_DIR}/cov_script.sh" "${PACKAGE_DIR}/crash_script.sh" "${PACKAGE_DIR}/protocol_smoke.sh" "${PACKAGE_DIR}/repeatability.py" "${PACKAGE_DIR}/crash_injection.sh" "${PACKAGE_DIR}/fault_injection.c" "${PACKAGE_DIR}/prepare_seeds.py" "${PACKAGE_DIR}/coverage_check.py" "${PACKAGE_DIR}/README.md" "${PACKAGE_DIR}/ACCEPTANCE.md" "${RESULTS_DIR}/source-snapshot/"
cp -a "${PACKAGE_DIR}/seeds" "${RESULTS_DIR}/source-snapshot/"
if [[ -f ${PACKAGE_DIR}/build-logs/docker-build.log ]]; then cp -a "${PACKAGE_DIR}/build-logs" "${RESULTS_DIR}/"; fi
(cd "${RESULTS_DIR}" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
ARCHIVE="$(dirname "${RESULTS_DIR}")/$(basename "${RESULTS_DIR}").tar.gz"
tar -czf "${ARCHIVE}" -C "$(dirname "${RESULTS_DIR}")" "$(basename "${RESULTS_DIR}")"

cat "${RESULTS_DIR}/acceptance-summary.txt"
echo "PASS: evidence bundle ${ARCHIVE}"
