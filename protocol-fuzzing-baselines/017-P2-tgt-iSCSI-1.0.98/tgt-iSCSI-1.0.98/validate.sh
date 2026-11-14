#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE=${1:-profuzzbench/tgt-aflnet:1.0.98}
RESULTS_DIR=${2:-"$(pwd)/results/iscsi-validation"}
DURATION=${3:-60s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
DOCKER_USER=$(id -u):$(id -g)

docker image inspect "${IMAGE}" >/dev/null
if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Results directory is not empty: ${RESULTS_DIR}" >&2
  exit 2
fi
mkdir -p "${RESULTS_DIR}/seeds"

docker run --rm --network none --user "${DOCKER_USER}" \
  -v "${PACKAGE_DIR}:/workspace:ro" \
  -v "${RESULTS_DIR}:/results" "${IMAGE}" \
  bash /opt/benchmark/smoke.sh /results/protocol-smoke \
  2>&1 | tee "${RESULTS_DIR}/protocol-smoke.log"

cp "${RESULTS_DIR}/protocol-smoke/seeds"/* "${RESULTS_DIR}/seeds/"
docker run --rm --network none --user "${DOCKER_USER}" \
  -v "${PACKAGE_DIR}:/workspace:ro" \
  -v "${RESULTS_DIR}:/results" -e SEEDS=/results/seeds \
  "${IMAGE}" \
  bash /opt/benchmark/run.sh /results/fuzz-smoke "${DURATION}" \
  2>&1 | tee "${RESULTS_DIR}/fuzz-smoke.log"

test -s "${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
test -s "${RESULTS_DIR}/fuzz-smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
  "${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
docker run --rm --network none --user "${DOCKER_USER}" -i "${IMAGE}" dot -Tplain \
  <"${RESULTS_DIR}/fuzz-smoke/ipsm.dot" >"${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' \
  "${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' \
  "${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
docker run --rm --network none --user "${DOCKER_USER}" "${IMAGE}" \
  cat /opt/benchmark/build-versions.txt >"${RESULTS_DIR}/build-versions.txt"
(
  cd "${RESULTS_DIR}"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum >SHA256SUMS
)
echo "PASS: iSCSI login/inquiry, AFLNet execution and state feedback; evidence=${RESULTS_DIR}"
