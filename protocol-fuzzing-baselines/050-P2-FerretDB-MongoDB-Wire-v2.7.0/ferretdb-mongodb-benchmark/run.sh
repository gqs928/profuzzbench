#!/usr/bin/env bash
set -u

OUTDIR=${1:-/results/ferretdb-mongodb-smoke}
DURATION=${2:-60s}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-/bin/bash}
INPUTS=${INPUTS:-${WORKDIR}/seeds}
DICT=${DICT:-${WORKDIR}/mongo.dict}
PORT=${PORT:-27017}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-30000}
OPTIONS=${3:-}

[[ -x ${FUZZER_BIN} ]] || { echo "缺少 AFLNet：${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${WORKDIR}/start-ferretdb.sh ]] || { echo "FerretDB launcher 缺失" >&2; exit 2; }
[[ -d ${INPUTS} && -f ${DICT} ]] || { echo "MongoDB 语料或字典缺失" >&2; exit 2; }
grep -a -q MONGODB "${FUZZER_BIN}" || { echo "AFLNet 未包含 MongoDB 解析器" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "结果目录必须为空：${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"

cat > "${OUTDIR}/run-parameters.txt" <<EOF
protocol=MongoDB Wire Protocol OP_MSG
target=FerretDB v2.7.0 official production binary commit 0d5eb3343a50b800634cc08ace608bb6f3a3f74b
backend=PostgreSQL 17 with DocumentDB v0.107.0 matched to FerretDB v2.7.0
endpoint=tcp://127.0.0.1/${PORT}
target_reset=terminate FerretDB after each testcase; call DocumentDB drop_database for each MongoDB database in the initialized postgres database before the next process
fuzzer=AFLNet ProFuzzBench commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=MongoDB 16-byte little-endian message frames; OP_MSG responses classified by ok/error and server error code
feedback_scope=black-box protocol response-state feedback; FerretDB binary is not coverage-instrumented
bitmap_scope=launcher/helper bitmap only; do not report it as FerretDB source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
state_feedback=-n -P MONGODB -E -q 3 -s 3 -R -K; retain_queue_on_novel_response_state_path
fuzzer_cpu_quota=1
fuzzer_memory_limit=1280m
backend_cpu_quota=0.5
backend_memory_limit=768m
docker_swap=disabled
execution_timeout_ms=${EXEC_TIMEOUT_MS}
additional_options=${OPTIONS}
EOF

export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
echo "开始 FerretDB MongoDB Wire 状态反馈模糊测试：${DURATION}；结果=${OUTDIR}"
set +e
timeout --signal=INT --kill-after=120s "${DURATION}" "${FUZZER_BIN}" \
  -n -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${PORT}" -P MONGODB -E -q 3 -s 3 -R -K \
  -D 5000 -W 1000 -w 500000 -m none -t "${EXEC_TIMEOUT_MS}" \
  "${EXTRA_OPTIONS[@]}" -- "${TARGET}" "${WORKDIR}/start-ferretdb.sh"
FUZZ_STATUS=$?
set -e
echo "AFLNet 退出状态：${FUZZ_STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "${OUTDIR}/fuzzer_stats" || true
fi
[[ ! -f ${OUTDIR}/plot_data ]] || cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"
if [[ ${FUZZ_STATUS} -eq 124 || ${FUZZ_STATUS} -eq 130 ]]; then exit 0; fi
exit "${FUZZ_STATUS}"
