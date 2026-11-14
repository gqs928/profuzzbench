#!/usr/bin/env bash
set -u

OUTDIR=${1:-/results/fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-${WORKDIR}/mongo-target-hold}
CONTROL_SCRIPT=${MONGODB_CONTROL_SCRIPT:-${WORKDIR}/mongo-server-control.sh}
INPUTS=${INPUTS:-${WORKDIR}/seeds}
DICT=${DICT:-${WORKDIR}/mongo.dict}
PORT=${MONGODB_PORT:-27017}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-10000}

cd "${WORKDIR}"
sha256sum -c source-checksums.sha256
[[ -x ${FUZZER_BIN} ]] || { echo "缺少 AFLNet：${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "MongoDB launcher 缺失：${TARGET}" >&2; exit 2; }
[[ -x ${CONTROL_SCRIPT} ]] || { echo "MongoDB cleanup hook 缺失：${CONTROL_SCRIPT}" >&2; exit 2; }
[[ -d ${INPUTS} && -f ${DICT} ]] || { echo "MongoDB 语料或字典缺失" >&2; exit 2; }
grep -a -q MONGODB "${FUZZER_BIN}" || { echo "AFLNet 未包含 MongoDB 解析器" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "结果目录必须为空：${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"

cleanup_mongodb() {
  "${CONTROL_SCRIPT}" stop >/dev/null 2>&1 || true
}
trap cleanup_mongodb EXIT
cleanup_mongodb

process_running() {
  local proc_stat
  proc_stat=$(ps -o stat= -p "$1" 2>/dev/null | tr -d ' ')
  [[ -n ${proc_stat} && ${proc_stat:0:1} != Z ]]
}

cat > "${OUTDIR}/run-parameters.txt" <<EOF
protocol=MongoDB Wire Protocol OP_MSG
target=MongoDB Server 9.0.8 official Docker image, linux/amd64
target_git_version=115a0fe2dcd8edd5bacd4557bd2e741a8e080665
target_image_digest=sha256:ff6cea7aa40c3ee44be503ed11f817928239d660b3927c79df4a1405e0923c1c
endpoint=tcp://127.0.0.1/${PORT}
scope=unauthenticated standalone OP_MSG commands; no TLS, authentication, compression, legacy opcodes, replica-set or sharding flows
target_reset=AFLNet cleanup hook restarts mongod with a clean WiredTiger dbPath on tmpfs before each testcase; a small helper process is terminated after each exchange
fuzzer=AFLNet ProFuzzBench snapshot 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=MongoDB 16-byte little-endian message framing; OP_MSG responses classified by ok and server error code
feedback_scope=black-box AFLNet response-state feedback; mongod is the uninstrumented official release binary
bitmap_scope=AFL helper bitmap only; do not report as MongoDB server source coverage
fuzzer_and_target_cpu_quota=2 shared CPUs
container_memory_limit=3g; WiredTiger cache=0.25GB
docker_swap=disabled
execution_timeout_ms=${EXEC_TIMEOUT_MS}
EOF

export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
echo "开始 MongoDB Server OP_MSG 状态反馈模糊测试：${DURATION}；结果=${OUTDIR}"
"${FUZZER_BIN}" \
  -n -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" -c "${CONTROL_SCRIPT}" \
  -N "tcp://127.0.0.1/${PORT}" -P MONGODB -E -q 3 -s 3 -R -K \
  -D 200000 -W 1000 -w 500000 -m none -t "${EXEC_TIMEOUT_MS}" \
  -- "${TARGET}" &
FUZZ_PID=$!
sleep "${DURATION}" &
TIMER_PID=$!

DEADLINE_REACHED=0
while process_running "${FUZZ_PID}"; do
  if ! process_running "${TIMER_PID}"; then
    DEADLINE_REACHED=1
    break
  fi
  sleep 0.2
done

if [[ ${DEADLINE_REACHED} -eq 1 ]]; then
  echo "到达计时终点，向 AFLNet 发送 SIGINT 并等待其保存状态。"
  printf 'deadline_reached=1\nstop_signal=SIGINT\n' > "${OUTDIR}/stop-reason.txt"
  for _ in {1..15}; do
    kill -INT "${FUZZ_PID}" 2>/dev/null || true
    sleep 1
    process_running "${FUZZ_PID}" || break
  done
  if process_running "${FUZZ_PID}"; then
    echo "AFLNet 未响应 SIGINT，尝试 SIGTERM。"
    printf 'stop_signal=SIGTERM\n' >> "${OUTDIR}/stop-reason.txt"
    kill -TERM "${FUZZ_PID}" 2>/dev/null || true
    for _ in {1..10}; do
      sleep 1
      process_running "${FUZZ_PID}" || break
    done
  fi
  if process_running "${FUZZ_PID}"; then
    echo "AFLNet 未能清理退出，发送 SIGKILL；本次运行将标为不完整。" >&2
    printf 'stop_signal=SIGKILL\nincomplete=1\n' >> "${OUTDIR}/stop-reason.txt"
    kill -KILL "${FUZZ_PID}" 2>/dev/null || true
  fi
  wait "${FUZZ_PID}"
  FUZZ_STATUS=$?
  wait "${TIMER_PID}" 2>/dev/null || true
else
  kill "${TIMER_PID}" 2>/dev/null || true
  wait "${TIMER_PID}" 2>/dev/null || true
  wait "${FUZZ_PID}"
  FUZZ_STATUS=$?
fi
echo "AFLNet 退出状态：${FUZZ_STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(start_time|last_update|execs_done|paths_total|paths_favored|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done|pending_total|max_depth)[[:space:]]*:' \
    "${OUTDIR}/fuzzer_stats" || true
fi
[[ ! -f ${OUTDIR}/plot_data ]] || cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"
exit "${FUZZ_STATUS}"
