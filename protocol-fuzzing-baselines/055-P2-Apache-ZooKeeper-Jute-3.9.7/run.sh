#!/usr/bin/env bash
set -u
OUTDIR=${1:-/results/zookeeper-fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-300000}
OPTIONS=${3:-}
ZK_PORT=${ZK_PORT:-2181}
ZK_HOST=${ZK_HOST:-$(hostname -i | awk '{print $1}')}
[[ -x ${FUZZER_BIN} ]] || { echo "missing AFLNet binary: ${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${WORKDIR}/start-zookeeper.sh ]] || { echo "ZooKeeper launcher missing" >&2; exit 2; }
[[ -d ${WORKDIR}/seeds && -f ${WORKDIR}/zookeeper.dict ]] || { echo "ZooKeeper corpus/dictionary missing" >&2; exit 2; }
grep -a -q ZOOKEEPER "${FUZZER_BIN}" || { echo "AFLNet lacks ZooKeeper Jute framing parser" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: ${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
export ZK_HOST ZK_PORT
cat > "${OUTDIR}/run-parameters.txt" <<PARAMS
protocol=Apache ZooKeeper client Jute binary protocol over TCP/${ZK_PORT}
product_release=Apache ZooKeeper ${ZK_EXPECTED_VERSION:-3.9.7}; runtime asserted by zkServer.sh version
target_scope=standalone mode, unauthenticated plaintext client port only; quorum/ZAB ports, TLS, SASL and multi-node consensus excluded
reset=restart one isolated ZooKeeper process and erase data/dataLog directories before each testcase
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=4-byte big-endian Jute length frames; first ConnectResponse is classified separately from subsequent ReplyHeader states
feedback_scope=black-box ZooKeeper Jute response-state feedback; ZooKeeper JVM is not coverage-instrumented
bitmap_scope=launcher/helper bitmap only; do not report it as ZooKeeper source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
target_stub=/usr/bin/python3 -c pass (separately managed ZooKeeper JVM is the actual TCP target)
campaign_duration=${DURATION}
container_cpu_quota=2; fuzzer and ZooKeeper share the CPU budget
container_memory_limit=2300m; single-node standalone ZooKeeper with bounded JVM heap
execution_timeout_ms=${EXEC_TIMEOUT_MS}
zookeeper_host=${ZK_HOST}; zookeeper_port=${ZK_PORT}
additional_options=${OPTIONS}
PARAMS
export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
export ZK_LOG_FILE="${OUTDIR}/zookeeper-node.log"
export ZK_LIFECYCLE_LOG="${OUTDIR}/zookeeper-lifecycle.tsv"
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
echo "starting ZooKeeper Jute state-feedback campaign: ${DURATION}; results=${OUTDIR}; target=${ZK_HOST}:${ZK_PORT}"
cleanup_target() {
  local status=$?
  /bin/bash "${WORKDIR}/stop-zookeeper.sh" || true
  chmod -R a+rX "${OUTDIR}" 2>/dev/null || true
  return "$status"
}
trap cleanup_target EXIT
/bin/bash "${WORKDIR}/start-zookeeper.sh"
set +e
python3 "${WORKDIR}/deadline_wrapper.py" "${DURATION}" "${OUTDIR}/fuzzer-deadline.json" "${FUZZER_BIN}" \
  -n -d -i "${WORKDIR}/seeds" -x "${WORKDIR}/zookeeper.dict" -o "${OUTDIR}" \
  -c "${WORKDIR}/reset-zookeeper.sh" \
  -N "tcp://${ZK_HOST}/${ZK_PORT}" -P ZOOKEEPER -E -q 3 -s 3 -R -K \
  -D 100000 -W 1000 -w 500000 -m none -t "${EXEC_TIMEOUT_MS}" \
  "${EXTRA_OPTIONS[@]}" -- /usr/bin/python3 -c pass
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: ${FUZZ_STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
[[ ! -f ${OUTDIR}/plot_data ]] || cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"
[[ ${FUZZ_STATUS} -eq 124 || ${FUZZ_STATUS} -eq 130 ]] && exit 0
exit "${FUZZ_STATUS}"

