#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-cyrus-pop3-aflnet}
RESULTS_DIR=${2:-$(pwd)/results/pop3-validation}
DURATION=${3:-60s}
REPETITIONS=${POP3_SMOKE_REPETITIONS:-5}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

python3 -c 'import pathlib,sys; d=pathlib.Path(sys.argv[1]).read_bytes(); bad=[(i,b) for i,b in enumerate(d) if b<32 and b not in (9,10)]; print("dictionary contains raw control bytes: "+repr(bad[:8]), file=sys.stderr) if bad else None; sys.exit(bool(bad))' "${PACKAGE_DIR}/pop3.dict"
docker image inspect "${IMAGE}" >/dev/null
if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Results directory is nonempty: ${RESULTS_DIR}" >&2
  exit 2
fi
mkdir -p "${RESULTS_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh

for variant in reference afl; do
  prefix="/home/ubuntu/experiments/cyrus-${variant}"
  docker run --rm --hostname localhost --network none \
    -e CYRUS_PREFIX="${prefix}" \
    -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
    bash /workspace/protocol-smoke-loop.sh "/results/protocol-smoke-${variant}" "${REPETITIONS}" \
    2>&1 | tee "${RESULTS_DIR}/protocol-smoke-${variant}.log"
done

docker run --rm --hostname localhost --network none \
  -e CYRUS_PREFIX=/home/ubuntu/experiments/cyrus-afl \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
  bash /workspace/run.sh /results/smoke "${DURATION}" 2>&1 | tee "${RESULTS_DIR}/fuzz.log"

test -s "${RESULTS_DIR}/smoke/fuzzer_stats"
test -s "${RESULTS_DIR}/smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' "${RESULTS_DIR}/smoke/fuzzer_stats"
docker run --rm --network none -i "${IMAGE}" dot -Tplain < "${RESULTS_DIR}/smoke/ipsm.dot" > "${RESULTS_DIR}/smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' "${RESULTS_DIR}/smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' "${RESULTS_DIR}/smoke/ipsm.plain"
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt > "${RESULTS_DIR}/build-versions.txt"
(
  cd "${RESULTS_DIR}"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "PASS: POP3 smoke, authenticated mail transaction, AFLNet execution and state feedback; evidence=${RESULTS_DIR}"
