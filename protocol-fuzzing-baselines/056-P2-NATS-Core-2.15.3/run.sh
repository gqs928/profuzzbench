#!/usr/bin/env bash
set -u
OUTDIR=${1:-/results/nats-fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-5000+}
OPTIONS=${3:-}
NATS_HOST=${NATS_HOST:-127.0.0.1}
NATS_PORT=${NATS_PORT:-4222}
[[ -x ${FUZZER_BIN} ]] || { echo "missing AFLNet binary: ${FUZZER_BIN}" >&2; exit 2; }
[[ -x /usr/local/bin/nats-server ]] || { echo "NATS server binary missing" >&2; exit 2; }
[[ -d ${WORKDIR}/seeds && -f ${WORKDIR}/nats.dict ]] || { echo "NATS corpus/dictionary missing" >&2; exit 2; }
grep -a -q NATS "${FUZZER_BIN}" || { echo "AFLNet lacks NATS protocol parser" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: ${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
cleanup_permissions() {
  chmod -R a+rX "${OUTDIR}" 2>/dev/null || true
}
trap cleanup_permissions EXIT
NATS_EXPECTED_VERSION=${NATS_EXPECTED_VERSION:-2.15.3}
version=$(/usr/local/bin/nats-server -v 2>&1)
grep -Fq "v${NATS_EXPECTED_VERSION}" <<< "${version}" || {
  echo "NATS version mismatch: expected ${NATS_EXPECTED_VERSION}, got ${version}" >&2
  exit 2
}
cat > "${OUTDIR}/run-parameters.txt" <<PARAMS
protocol=NATS Core client protocol v1 over plaintext TCP/${NATS_PORT}
product_release=NATS Server ${NATS_EXPECTED_VERSION}; runtime asserted by official binary -v
target_scope=single standalone server, no authentication; excludes TLS, WebSocket, JetStream, clustering, gateways, leafnodes and account/JWT flows
target_identity=official docker.io/library/nats:${NATS_EXPECTED_VERSION} image pinned by manifest digest; scratch target binary copied into Debian benchmark runtime
reset=each AFLNet testcase starts an isolated NATS server process; JetStream and disk state are disabled; AFLNet -K sends SIGTERM after testcase
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=CRLF control lines; PUB payload byte counts; HPUB header/total lengths; INFO, +OK, -ERR, PING/PONG, MSG and HMSG response states
feedback_scope=black-box NATS protocol response-state feedback; NATS Go binary is not coverage-instrumented
bitmap_scope=helper bitmap only; do not report it as NATS source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
target_binary=/usr/local/bin/nats-server -a 127.0.0.1 -p ${NATS_PORT}
campaign_duration=${DURATION}
container_cpu_quota=2; fuzzer and NATS server share the CPU budget
container_memory_limit=1500m
execution_timeout_ms=${EXEC_TIMEOUT_MS}
nats_host=${NATS_HOST}; nats_port=${NATS_PORT}
additional_options=${OPTIONS}
PARAMS
export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
echo "starting NATS Core response-state campaign: ${DURATION}; results=${OUTDIR}; target=${NATS_HOST}:${NATS_PORT}; ${version}"
set +e
python3 "${WORKDIR}/deadline_wrapper.py" "${DURATION}" "${OUTDIR}/fuzzer-deadline.json" "${FUZZER_BIN}" \
  -n -d -i "${WORKDIR}/seeds" -x "${WORKDIR}/nats.dict" -o "${OUTDIR}" \
  -N "tcp://${NATS_HOST}/${NATS_PORT}" -P NATS -E -q 3 -s 3 -R -K \
  -D 100000 -W 250 -w 200000 -m none -t "${EXEC_TIMEOUT_MS}" \
  "${EXTRA_OPTIONS[@]}" -- /usr/local/bin/nats-server -a 127.0.0.1 -p "${NATS_PORT}"
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: ${FUZZ_STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
[[ ! -f ${OUTDIR}/plot_data ]] || cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"
[[ ${FUZZ_STATUS} -eq 124 || ${FUZZ_STATUS} -eq 130 ]] && exit 0
exit "${FUZZ_STATUS}"
