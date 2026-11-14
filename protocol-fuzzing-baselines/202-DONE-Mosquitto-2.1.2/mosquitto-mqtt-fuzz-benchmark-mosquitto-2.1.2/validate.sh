#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-mosquitto-fuzz}
RESULTS_DIR=${2:-$(pwd)/mosquitto-validation}
DURATION=${3:-60s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

docker image inspect "${IMAGE}" >/dev/null
if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Results directory is nonempty: ${RESULTS_DIR}. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "${RESULTS_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh

docker run --rm --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" python3 /workspace/protocol_smoke.py /results/protocol-smoke \
  2>&1 | tee "${RESULTS_DIR}/protocol-smoke.log"
docker run --rm --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
  "${IMAGE}" bash /workspace/run.sh /results/smoke "${DURATION}" \
  2>&1 | tee "${RESULTS_DIR}/fuzz.log"

test -s "${RESULTS_DIR}/smoke/fuzzer_stats"
test -s "${RESULTS_DIR}/smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
  "${RESULTS_DIR}/smoke/fuzzer_stats"
docker run --rm --network none -i "${IMAGE}" dot -Tplain \
  < "${RESULTS_DIR}/smoke/ipsm.dot" > "${RESULTS_DIR}/smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' "${RESULTS_DIR}/smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' "${RESULTS_DIR}/smoke/ipsm.plain"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt \
  > "${RESULTS_DIR}/build-versions.txt"
(
  cd "${RESULTS_DIR}"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "PASS: MQTT smoke, 10-run repeatability, AFLNet execution and IPSM state feedback; evidence=${RESULTS_DIR}"
