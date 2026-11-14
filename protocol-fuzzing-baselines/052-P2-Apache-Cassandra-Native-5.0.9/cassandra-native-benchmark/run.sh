#!/usr/bin/env bash
set -u
OUTDIR=${1:-/results/cassandra-smoke}
DURATION=${2:-60s}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-300000}
OPTIONS=${3:-}
[[ -x ${FUZZER_BIN} ]] || { echo "missing AFLNet binary: ${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${WORKDIR}/start-cassandra.sh ]] || { echo "Cassandra launcher missing" >&2; exit 2; }
[[ -d ${WORKDIR}/seeds && -f ${WORKDIR}/cassandra.dict ]] || { echo "Cassandra corpus/dictionary missing" >&2; exit 2; }
grep -a -q CASSANDRA "${FUZZER_BIN}" || { echo "AFLNet lacks Cassandra parser" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: ${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"

cat > "${OUTDIR}/run-parameters.txt" <<PARAMS
protocol=Cassandra Native Protocol v4 over TCP/9042
target=Apache Cassandra 5.0.9 official Docker image pinned by manifest digest
reset=keep one isolated Cassandra node alive; before each testcase drop every user keyspace and start the node if unavailable
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=9-byte Cassandra v4/v5 frame header; response states classified by opcode and Cassandra error code
feedback_scope=black-box Cassandra Native response-state feedback; Cassandra binary is not coverage-instrumented
bitmap_scope=launcher/helper bitmap only; do not report it as Cassandra source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
state_feedback=-n -P CASSANDRA -E -q 3 -s 3 -R -K; queue retention patched for novel response-state paths
campaign_duration=${DURATION}
container_cpu_quota=2; fuzzer and Cassandra share the container CPU budget
memory_limit=2048m
execution_timeout_ms=${EXEC_TIMEOUT_MS}
additional_options=${OPTIONS}
PARAMS

export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
export CASSANDRA_LOG_FILE="${OUTDIR}/cassandra-node.log"
export CASSANDRA_LIFECYCLE_LOG="${OUTDIR}/cassandra-lifecycle.tsv"
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
echo "starting Cassandra Native state-feedback campaign: ${DURATION}; results=${OUTDIR}"
cleanup_target() {
  local status=$?
  "${WORKDIR}/stop-cassandra.sh" || true
  # Docker's user namespace maps the target UID to an unmapped host UID.
  # Expose completed evidence to the workspace owner before the bind mount ends.
  chmod -R a+rX "${OUTDIR}" 2>/dev/null || true
  return "$status"
}
trap cleanup_target EXIT
"${WORKDIR}/start-cassandra.sh"
set +e
timeout --signal=INT --kill-after=120s "${DURATION}" "${FUZZER_BIN}" \
  -n -d -i "${WORKDIR}/seeds" -x "${WORKDIR}/cassandra.dict" -o "${OUTDIR}" \
  -c "${WORKDIR}/reset-cassandra.sh" \
  -N tcp://127.0.0.1/9042 -P CASSANDRA -E -q 3 -s 3 -R -K \
  -D 100000 -W 1000 -w 500000 -m none -t "${EXEC_TIMEOUT_MS}" \
  "${EXTRA_OPTIONS[@]}" -- /bin/true
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: ${FUZZ_STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "${OUTDIR}/fuzzer_stats" || true
fi
[[ ! -f ${OUTDIR}/plot_data ]] || cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"
if [[ ${FUZZ_STATUS} -eq 124 || ${FUZZ_STATUS} -eq 130 ]]; then exit 0; fi
exit "${FUZZ_STATUS}"
