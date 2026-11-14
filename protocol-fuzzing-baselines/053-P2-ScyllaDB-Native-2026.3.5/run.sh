#!/usr/bin/env bash
set -u
OUTDIR=${1:-/results/scylla-fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-300000}
OPTIONS=${3:-}
[[ -x ${FUZZER_BIN} ]] || { echo "missing AFLNet binary: ${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${WORKDIR}/start-scylla.sh ]] || { echo "Scylla launcher missing" >&2; exit 2; }
[[ -d ${WORKDIR}/seeds && -f ${WORKDIR}/cassandra.dict ]] || { echo "Native Protocol corpus/dictionary missing" >&2; exit 2; }
grep -a -q CASSANDRA "${FUZZER_BIN}" || { echo "AFLNet lacks Cassandra-compatible Native Protocol parser" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: ${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
cat > "${OUTDIR}/run-parameters.txt" <<PARAMS
protocol=ScyllaDB Native Protocol v4 over TCP/9042
product_version=ScyllaDB 2026.3.5 (asserted by /usr/bin/scylla --version)
cql_compatibility_version=3.0.8 (system.local.release_version; compatibility value, not product version)
reset=keep one isolated ScyllaDB process; drop every user keyspace before each testcase
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=9-byte Cassandra Native Protocol v4/v5 frame parser; feedback states classified by response opcode and error code
feedback_scope=black-box Native Protocol response-state feedback; ScyllaDB binary is not coverage-instrumented
bitmap_scope=launcher/helper bitmap only; do not report it as ScyllaDB source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
state_feedback=-n -P CASSANDRA -E -q 3 -s 3 -R -K; queue retention patched for novel response-state paths
campaign_duration=${DURATION}
container_cpu_quota=2; fuzzer and ScyllaDB share the CPU budget, ScyllaDB uses --smp 1
container_memory_limit=3200m; ScyllaDB --memory=1536M, matching the documented minimum with cgroup headroom
execution_timeout_ms=${EXEC_TIMEOUT_MS}
additional_options=${OPTIONS}
target_stub=/usr/bin/python3 -c pass (ELF placeholder for AFLNet network mode; ScyllaDB is the separately managed TCP target)
PARAMS
export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
export SCYLLA_LOG_FILE="${OUTDIR}/scylla-node.log"
export SCYLLA_LIFECYCLE_LOG="${OUTDIR}/scylla-lifecycle.tsv"
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
echo "starting ScyllaDB Native Protocol state-feedback campaign: ${DURATION}; results=${OUTDIR}"
cleanup_target() {
  local status=$?
  "${WORKDIR}/stop-scylla.sh" || true
  chmod -R a+rX "${OUTDIR}" 2>/dev/null || true
  return "$status"
}
trap cleanup_target EXIT
"${WORKDIR}/start-scylla.sh"
set +e
timeout --signal=INT --kill-after=120s "${DURATION}" "${FUZZER_BIN}" \
  -n -d -i "${WORKDIR}/seeds" -x "${WORKDIR}/cassandra.dict" -o "${OUTDIR}" \
  -c "${WORKDIR}/reset-scylla.sh" \
  -N tcp://127.0.0.1/9042 -P CASSANDRA -E -q 3 -s 3 -R -K \
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
