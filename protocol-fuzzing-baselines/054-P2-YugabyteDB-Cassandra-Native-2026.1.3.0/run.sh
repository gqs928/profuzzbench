#!/usr/bin/env bash
set -u
OUTDIR=${1:-/results/yugabyte-fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-300000}
OPTIONS=${3:-}
YCQL_PORT=${YCQL_PORT:-9042}
YCQL_HOST=${YCQL_HOST:-$(hostname -i | awk '{print $1}')}
[[ -x ${FUZZER_BIN} ]] || { echo "missing AFLNet binary: ${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${WORKDIR}/start-yugabyte.sh ]] || { echo "YugabyteDB launcher missing" >&2; exit 2; }
[[ -d ${WORKDIR}/seeds && -f ${WORKDIR}/cassandra.dict ]] || { echo "YCQL corpus/dictionary missing" >&2; exit 2; }
grep -a -q CASSANDRA "${FUZZER_BIN}" || { echo "AFLNet lacks Cassandra-compatible Native Protocol parser" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: ${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
export YCQL_HOST YCQL_PORT
cat > "${OUTDIR}/run-parameters.txt" <<PARAMS
protocol=YugabyteDB YCQL Native Protocol v4 over TCP/${YCQL_PORT}
product_release=v${YUGABYTE_EXPECTED_VERSION:-2026.1.3.0}; image build=${YUGABYTE_EXPECTED_BUILD:-100}; runtime asserted by /home/yugabyte/bin/yb-server --version
target_scope=unauthenticated YCQL only; YSQL, TLS, authentication, multi-node consensus and non-YCQL APIs excluded
reset=one isolated YugabyteDB process; reset hook drops all non-system keyspaces before each testcase
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=9-byte Cassandra Native Protocol v4/v5 frame parser; response opcode/error states drive feedback
feedback_scope=black-box YCQL Native Protocol response-state feedback; YugabyteDB binaries are not coverage-instrumented
bitmap_scope=launcher/helper bitmap only; do not report it as YugabyteDB source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
target_stub=/usr/bin/python3 -c pass (ELF placeholder only; the separately managed YugabyteDB service is the actual TCP target)
campaign_duration=${DURATION}
container_cpu_quota=2; fuzzer and YugabyteDB share the CPU budget
container_memory_limit=4300m; official minimum is 2 GiB RAM and cgroup headroom is retained
execution_timeout_ms=${EXEC_TIMEOUT_MS}
ycql_host=${YCQL_HOST}; ycql_port=${YCQL_PORT}
additional_options=${OPTIONS}
PARAMS
export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
export YUGABYTE_LOG_FILE="${OUTDIR}/yugabyte-node.log"
export YUGABYTE_LIFECYCLE_LOG="${OUTDIR}/yugabyte-lifecycle.tsv"
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
echo "starting YugabyteDB YCQL state-feedback campaign: ${DURATION}; results=${OUTDIR}; target=${YCQL_HOST}:${YCQL_PORT}"
cleanup_target() {
  local status=$?
  /bin/bash "${WORKDIR}/stop-yugabyte.sh" || true
  chmod -R a+rX "${OUTDIR}" 2>/dev/null || true
  return "$status"
}
trap cleanup_target EXIT
/bin/bash "${WORKDIR}/start-yugabyte.sh"
set +e
python3 "${WORKDIR}/deadline_wrapper.py" "${DURATION}" "${OUTDIR}/fuzzer-deadline.json" "${FUZZER_BIN}" \
  -n -d -i "${WORKDIR}/seeds" -x "${WORKDIR}/cassandra.dict" -o "${OUTDIR}" \
  -c "${WORKDIR}/reset-yugabyte.sh" \
  -N "tcp://${YCQL_HOST}/${YCQL_PORT}" -P CASSANDRA -E -q 3 -s 3 -R -K \
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
