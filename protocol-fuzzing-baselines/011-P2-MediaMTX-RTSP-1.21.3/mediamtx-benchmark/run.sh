#!/usr/bin/env bash
set -euo pipefail

OUTDIR="${1:-/work/results/rtsp-30m}"
DURATION="${2:-1800s}"
SECONDS_RUN="${DURATION%s}"
[[ "${SECONDS_RUN}" =~ ^[0-9]+$ ]] || { echo "Duration must be integer seconds (optional s suffix)." >&2; exit 2; }
if [[ -e "${OUTDIR}" ]] && [[ -n "$(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi

mkdir -p "${OUTDIR}/go-coverdata" "${OUTDIR}/post-smoke/go-coverdata"
export GOCACHE="${OUTDIR}/go-build-cache"
mkdir -p "${GOCACHE}"
cp /work/build-evidence/build-lock.txt "${OUTDIR}/build-lock.txt"
cp /work/build-evidence/go-version-info.txt "${OUTDIR}/go-version-info.txt"

export AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
GO=/usr/local/go/bin/go
[[ -x "${GO}" ]] || { echo "Go toolchain is missing at ${GO}." >&2; exit 2; }
date -u +%s > "${OUTDIR}/external-start-epoch.txt"
printf 'target=/opt/mediamtx/mediamtx v1.21.3, compiled with Go native coverage (-coverpkg=./...)\n' > "${OUTDIR}/run-method.txt"
printf 'network=RTSP over TCP, 127.0.0.1:8554; AFLNet -n response-state mode; MediaMTX is a separately managed persistent service\n' >> "${OUTDIR}/run-method.txt"
printf 'lifecycle=each campaign and post-smoke phase uses a fresh MediaMTX process; AFLNet uses an AFL-instrumented forkserver helper that exits normally on per-testcase SIGTERM (-K); each Go process receives graceful SIGTERM and is reaped before coverage merge\n' >> "${OUTDIR}/run-method.txt"
printf 'coverage_scope=Go native counters from the campaign service plus a separate fresh post-smoke service; AFL bitmap/crash/hang counters describe only rtsp-fuzz-helper\n' >> "${OUTDIR}/run-method.txt"

SERVER_PID=''
SERVER_LABEL=''
FUZZER_PID=''
TIMER_PID=''
server_state() {
  local state
  [[ -r "/proc/$1/status" ]] || { printf 'gone'; return; }
  state="$(awk '/^State:/ {print $2}' "/proc/$1/status")"
  printf '%s' "${state:-gone}"
}
wait_server_ready() {
  local pid="$1" deadline=$((SECONDS + 30)) last=''
  while (( SECONDS < deadline )); do
    local state
    state="$(server_state "${pid}")"
    [[ "${state}" == gone || "${state}" == Z || "${state}" == X ]] && break
    if python3 - <<'PY' >/dev/null 2>&1
import socket
with socket.create_connection(("127.0.0.1", 8554), timeout=1) as s:
    s.sendall(b"OPTIONS rtsp://127.0.0.1:8554/stream RTSP/1.0\r\nCSeq: 1\r\n\r\n")
    if not s.recv(4096).startswith(b"RTSP/1.0 200"):
        raise SystemExit(1)
PY
    then
      return 0
    else
      last='RTSP OPTIONS readiness probe did not return 200'
    fi
    sleep 0.2
  done
  echo "MediaMTX (${SERVER_LABEL}) did not become RTSP-ready: ${last}" >&2
  [[ -n "${SERVER_LABEL}" && -s "${OUTDIR}/${SERVER_LABEL}/server.log" ]] && tail -60 "${OUTDIR}/${SERVER_LABEL}/server.log" >&2 || true
  return 1
}
start_server() {
  local label="$1" coverdir="$2" workdir="${OUTDIR}/server-work/$1"
  mkdir -p "${OUTDIR}/${label}" "${coverdir}" "${workdir}"
  SERVER_LABEL="${label}"
  (
    cd "${workdir}"
    GOCOVERDIR="${coverdir}" exec /opt/mediamtx/mediamtx /work/mediamtx.yml
  ) > "${OUTDIR}/${label}/server.log" 2>&1 &
  SERVER_PID=$!
  printf '%s\n' "${SERVER_PID}" > "${OUTDIR}/${label}/server.pid.txt"
  wait_server_ready "${SERVER_PID}"
}
stop_server() {
  local phase="$1" pid="${SERVER_PID}" graceful=yes exit_code=0 state
  [[ -n "${pid}" ]] || return 0
  state="$(server_state "${pid}")"
  if [[ "${state}" != gone && "${state}" != Z && "${state}" != X ]]; then
    kill -TERM "${pid}" >/dev/null 2>&1 || true
    for _ in $(seq 1 300); do
      state="$(server_state "${pid}")"
      [[ "${state}" == gone || "${state}" == Z || "${state}" == X ]] && break
      sleep 0.1
    done
    state="$(server_state "${pid}")"
    if [[ "${state}" != gone && "${state}" != Z && "${state}" != X ]]; then
      graceful=no
      kill -KILL "${pid}" >/dev/null 2>&1 || true
    fi
  fi
  set +e
  wait "${pid}"
  exit_code=$?
  set -e
  printf 'signal=SIGTERM\ngraceful=%s\nprocess_exit_code=%s\n' "${graceful}" "${exit_code}" > "${OUTDIR}/${phase}/stop-status.txt"
  SERVER_PID=''
  SERVER_LABEL=''
  if [[ "${graceful}" != yes || "${exit_code}" -ne 0 ]]; then
    echo "MediaMTX ${phase} process did not exit cleanly (graceful=${graceful}, code=${exit_code})." >&2
    return 1
  fi
}
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  if [[ -n "${FUZZER_PID}" ]] && kill -0 "${FUZZER_PID}" >/dev/null 2>&1; then
    kill -INT "${FUZZER_PID}" >/dev/null 2>&1 || true
    wait "${FUZZER_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${TIMER_PID}" ]] && kill -0 "${TIMER_PID}" >/dev/null 2>&1; then
    kill "${TIMER_PID}" >/dev/null 2>&1 || true
    wait "${TIMER_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${SERVER_PID}" ]]; then stop_server "${SERVER_LABEL}" || true; fi
  exit "${rc}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

start_server campaign "${OUTDIR}/go-coverdata"
printf 'AFLNet response-state graph feedback is measured by AFLNet; AFL bitmap/counters describe /opt/aflnet/rtsp-fuzz-helper only, not MediaMTX\n' >> "${OUTDIR}/run-method.txt"
set +e
/opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/rtsp.dict \
  -o "${OUTDIR}/aflnet-out" -N tcp://127.0.0.1/8554 -P RTSP \
  -E -q 3 -s 3 -R -K -D 500000 -W 1000 -w 500000 -m none -t 5000+ \
  -- /opt/aflnet/rtsp-fuzz-helper > "${OUTDIR}/aflnet.log" 2>&1 &
FUZZER_PID=$!
sleep "${SECONDS_RUN}" &
TIMER_PID=$!
wait -n -p FIRST_EXITED_PID "${FUZZER_PID}" "${TIMER_PID}"
FIRST_EXIT_STATUS=$?
set -e
if [[ "${FIRST_EXITED_PID:-}" == "${TIMER_PID}" ]]; then
  printf 'SIGINT after %s seconds\n' "${SECONDS_RUN}" > "${OUTDIR}/duration-signal.txt"
  kill -INT "${FUZZER_PID}" >/dev/null 2>&1 || true
  set +e
  wait "${FUZZER_PID}"
  FUZZER_STATUS=$?
  set -e
  WRAPPER_STATUS=124
else
  FUZZER_STATUS="${FIRST_EXIT_STATUS}"
  kill "${TIMER_PID}" >/dev/null 2>&1 || true
  wait "${TIMER_PID}" >/dev/null 2>&1 || true
  WRAPPER_STATUS="${FUZZER_STATUS}"
fi
FUZZER_PID=''
TIMER_PID=''
date -u +%s > "${OUTDIR}/fuzz-end-epoch.txt"
printf '%s\n' "${FUZZER_STATUS}" > "${OUTDIR}/fuzzer-exit-code.txt"
printf '%s\n' "${WRAPPER_STATUS}" > "${OUTDIR}/wrapper-exit-code.txt"
if [[ -s "${OUTDIR}/aflnet-out/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' \
    "${OUTDIR}/aflnet-out/fuzzer_stats" > "${OUTDIR}/fuzzer-summary.txt" || true
fi
if [[ "${WRAPPER_STATUS}" -ne 124 && "${WRAPPER_STATUS}" -ne 0 ]]; then
  echo "AFLNet exit status: ${FUZZER_STATUS}" >&2
  exit "${FUZZER_STATUS}"
fi

stop_server campaign
mkdir -p "${OUTDIR}/post-smoke"
start_server post-smoke "${OUTDIR}/post-smoke/go-coverdata"
python3 /work/service_smoke.py --host 127.0.0.1 --port 8554 --timeout 30 \
  --output "${OUTDIR}/post-smoke/rtsp-smoke.json"
printf 'rtsp_health=pass_on_fresh_post_campaign_process\n' > "${OUTDIR}/post-smoke/health.txt"
stop_server post-smoke
trap - EXIT INT TERM
date -u +%s > "${OUTDIR}/external-end-epoch.txt"

for coverdir in "${OUTDIR}/go-coverdata" "${OUTDIR}/post-smoke/go-coverdata"; do
  test -n "$(find "${coverdir}" -type f -name 'covcounters.*' -print -quit)" || {
    echo "No Go coverage counters were flushed from ${coverdir}." >&2
    exit 1
  }
done
mkdir -p "${OUTDIR}/go-coverdata-merged"
"${GO}" tool covdata merge -i="${OUTDIR}/go-coverdata,${OUTDIR}/post-smoke/go-coverdata" -o="${OUTDIR}/go-coverdata-merged"
"${GO}" tool covdata textfmt -i="${OUTDIR}/go-coverdata-merged" -o="${OUTDIR}/go-coverage.out"
(cd /src/mediamtx && "${GO}" tool cover -func="${OUTDIR}/go-coverage.out") > "${OUTDIR}/go-coverage-summary.txt"

if [[ "${WRAPPER_STATUS}" -ne 124 && "${WRAPPER_STATUS}" -ne 0 ]]; then
  exit "${WRAPPER_STATUS}"
fi
