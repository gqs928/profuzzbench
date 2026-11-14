#!/usr/bin/env bash
set -euo pipefail

OUTDIR="${1:-/work/results/rtsp-30m}"
DURATION="${2:-1800s}"
PIPELINE='( videotestsrc is-live=true ! video/x-raw,width=16,height=16,framerate=1/1 ! rtpvrawpay name=pay0 pt=96 )'

if [[ -e "${OUTDIR}" ]] && [[ -n "$(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
cp /work/build-evidence/build-lock.txt "${OUTDIR}/build-lock.txt"
cp /work/build-evidence/version.txt "${OUTDIR}/target-versions.txt"

export LD_LIBRARY_PATH="/opt/gst-rtsp/lib:${LD_LIBRARY_PATH:-}"
export GST_PLUGIN_SYSTEM_PATH_1_0=/usr/lib/x86_64-linux-gnu/gstreamer-1.0
export AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
date -u +%s > "${OUTDIR}/external-start-epoch.txt"
printf 'target=/opt/gst-rtsp/test-launch from gst-rtsp-server 1.28.8 (AFL-instrumented executable and library)\n' > "${OUTDIR}/run-method.txt"
printf 'network=RTSP over TCP, 127.0.0.1:8554, GStreamer response-code state extraction\n' >> "${OUTDIR}/run-method.txt"
printf 'media_pipeline=%s\n' "${PIPELINE}" >> "${OUTDIR}/run-method.txt"
printf 'runtime_dependency_versions=\n' >> "${OUTDIR}/run-method.txt"
cat /work/build-evidence/version.txt >> "${OUTDIR}/run-method.txt"

SECONDS_RUN="${DURATION%s}"
[[ "${SECONDS_RUN}" =~ ^[0-9]+$ ]] || { echo "Duration must be an integer number of seconds (optionally suffixed by s)." >&2; exit 2; }
/opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/rtsp.dict \
  -o "${OUTDIR}/aflnet-out" -N tcp://127.0.0.1/8554 -P RTSP \
  -E -q 3 -s 3 -R -K -D 100000 -W 1000 -w 500000 -m none -t 5000+ \
  -- /opt/gst-rtsp/test-launch -p 8554 "${PIPELINE}" \
  > "${OUTDIR}/aflnet.log" 2>&1 &
FUZZER_PID=$!
sleep "${SECONDS_RUN}" &
TIMER_PID=$!
set +e
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
pkill -TERM -x test-launch >/dev/null 2>&1 || true
sleep 1
pkill -KILL -x test-launch >/dev/null 2>&1 || true
date -u +%s > "${OUTDIR}/external-end-epoch.txt"
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

mkdir -p "${OUTDIR}/post-smoke"
export GST_PLUGIN_SYSTEM_PATH_1_0=/usr/lib/x86_64-linux-gnu/gstreamer-1.0
/opt/gst-rtsp/test-launch -p 8554 "${PIPELINE}" > "${OUTDIR}/post-smoke/server.log" 2>&1 &
SERVER_PID=$!
cleanup() {
  kill -TERM "${SERVER_PID}" >/dev/null 2>&1 || true
  sleep 1
  kill -KILL "${SERVER_PID}" >/dev/null 2>&1 || true
  wait "${SERVER_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM
python3 /work/service_smoke.py --host 127.0.0.1 --port 8554 --timeout 30 \
  --output "${OUTDIR}/post-smoke/rtsp-smoke.json"
printf 'rtsp_health=pass_after_campaign\n' > "${OUTDIR}/post-smoke/health.txt"
cleanup
trap - EXIT INT TERM
