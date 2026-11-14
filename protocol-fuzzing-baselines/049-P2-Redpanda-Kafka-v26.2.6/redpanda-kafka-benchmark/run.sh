#!/usr/bin/env bash
set -u

OUTDIR=${1:-/results/redpanda-smoke}
DURATION=${2:-60s}
WORKDIR=${WORKDIR:-/home/redpanda/benchmark}
AFLNET=${AFLNET:-/home/redpanda/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-${WORKDIR}/redpanda-launcher}
INPUTS=${INPUTS:-${WORKDIR}/seeds}
DICT=${DICT:-${WORKDIR}/kafka.dict}
PORT=${PORT:-9092}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-60000}
OPTIONS=${3:-}

[[ -x ${FUZZER_BIN} ]] || { echo "缺少 AFLNet：${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "Redpanda 启动器不可执行：${TARGET}" >&2; exit 2; }
[[ -d ${INPUTS} && -f ${DICT} ]] || { echo "Kafka 语料或字典缺失" >&2; exit 2; }
grep -a -q KAFKA "${FUZZER_BIN}" || { echo "AFLNet 未包含 Kafka 解析器" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "结果目录必须为空：${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"

PARAMETERS_FILE="${OUTDIR}/run-parameters.txt"
cat > "${PARAMETERS_FILE}" <<EOF
protocol=Kafka native TCP binary protocol
target=Redpanda v26.2.6 official server image
server_image=docker.redpanda.com/redpandadata/redpanda:v26.2.6@sha256:8b1076e0d61bfceb66594dc01536427ce0b529f8ead35fdab9763ab6085891ce
endpoint=tcp://127.0.0.1/${PORT}
target_reset=stop one Redpanda broker after every testcase, clear its single-node data dir, restart
fuzzer=AFLNet ProFuzzBench commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=Kafka 4-byte request framing; response correlation IDs map ApiVersions/Metadata/Produce/Fetch
feedback_scope=black-box protocol response-state feedback; official Redpanda executable is not coverage-instrumented
bitmap_scope=launcher/helper bitmap only; do not report it as Redpanda code coverage
forkserver=disabled; AFL_NO_FORKSRV=1
state_feedback=-P KAFKA -E -q 3 -s 3 -R -K
broker_smp=1
docker_cpu_quota=${REDPANDA_CPU_LIMIT:-1}
docker_memory_limit=${REDPANDA_MEMORY_LIMIT:-2g}
docker_swap=disabled
execution_timeout_ms=${EXEC_TIMEOUT_MS}
additional_options=${OPTIONS}
EOF

export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
echo "开始 Redpanda Kafka 状态反馈模糊测试：${DURATION}；结果=${OUTDIR}"
set +e
timeout --signal=INT --kill-after=120s "${DURATION}" "${FUZZER_BIN}" \
  -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${PORT}" -P KAFKA -E -q 3 -s 3 -R -K \
  -D 5000 -W 1000 -w 500000 -m none -t "${EXEC_TIMEOUT_MS}" \
  "${EXTRA_OPTIONS[@]}" -- "${TARGET}"
STATUS=$?
set -e
echo "AFLNet 退出状态：${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "${OUTDIR}/fuzzer_stats" || true
fi
[[ ! -f ${OUTDIR}/plot_data ]] || cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"
if [[ ${STATUS} -eq 124 || ${STATUS} -eq 130 ]]; then exit 0; fi
exit "${STATUS}"
