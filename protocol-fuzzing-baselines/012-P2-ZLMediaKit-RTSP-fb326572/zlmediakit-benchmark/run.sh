#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:-/work/results/rtsp-30m}"
DURATION="${2:-1800s}"
SECONDS_RUN="${DURATION%s}"
[[ "$SECONDS_RUN" =~ ^[0-9]+$ ]] || { echo 'Duration must be integer seconds.' >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n "$(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: $OUTDIR" >&2; exit 2
fi
mkdir -p "$OUTDIR/preflight" "$OUTDIR/campaign" "$OUTDIR/post-smoke"
cp /work/build-evidence/build-lock.txt "$OUTDIR/build-lock.txt"
export AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
SERVER_PID='' FUZZER_PID='' TIMER_PID='' SERVER_LABEL=''
stop_server() {
  local pid="$SERVER_PID" state=running rc=0
  [[ -n "$pid" ]] || return 0
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 200); do
    if ! kill -0 "$pid" 2>/dev/null; then state=stopped; break; fi
    sleep .1
  done
  if [[ "$state" != stopped ]]; then state=forced; kill -KILL "$pid" 2>/dev/null || true; fi
  set +e; wait "$pid"; rc=$?; set -e
  printf 'shutdown=%s\nexit_code=%s\n' "$state" "$rc" > "$OUTDIR/$SERVER_LABEL/stop-status.txt"
  SERVER_PID=''
  [[ "$state" == stopped ]]
}
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  if [[ -n "$FUZZER_PID" ]] && kill -0 "$FUZZER_PID" 2>/dev/null; then
    kill -INT "$FUZZER_PID" 2>/dev/null || true; wait "$FUZZER_PID" 2>/dev/null || true
  fi
  if [[ -n "$TIMER_PID" ]] && kill -0 "$TIMER_PID" 2>/dev/null; then
    kill "$TIMER_PID" 2>/dev/null || true; wait "$TIMER_PID" 2>/dev/null || true
  fi
  if [[ -n "$SERVER_PID" ]]; then stop_server || true; fi
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
start_server() {
  SERVER_LABEL="$1"
  mkdir -p "$OUTDIR/$SERVER_LABEL"
  cd /work
  /opt/zlmediakit/MediaServer -c /work/config.ini -l 2 -t 2 \
    > "$OUTDIR/$SERVER_LABEL/server.log" 2>&1 &
  SERVER_PID=$!
  echo "$SERVER_PID" > "$OUTDIR/$SERVER_LABEL/server.pid.txt"
}
date -u +%s > "$OUTDIR/external-start-epoch.txt"
{
  echo 'target=ZLMediaKit pinned snapshot fb3265725f0880da1f52a3cc6e6eb04bbc327fa3; RTSP over TCP 127.0.0.1:8554'
  echo 'feedback=AFLNet -P RTSP response-state feedback; target AFL bitmap reported separately and may be unavailable'
  echo 'launcher=target-wrapper.sh execs MediaServer so AFLNet forkserver reaches the instrumented service binary'
  echo 'scope=RTSP enabled; all other listener ports disabled; no RTP/RTSP media source and no external network'
} > "$OUTDIR/run-method.txt"
start_server preflight
python3 /work/smoke.py --timeout 20 --output "$OUTDIR/preflight/rtsp-smoke.json"
stop_server

set +e
AFL_SKIP_BIN_CHECK=1 /opt/aflnet/afl-fuzz -d -i /work/seeds -o "$OUTDIR/aflnet-out" \
  -N tcp://127.0.0.1/8554 -P RTSP -E -q 3 -s 3 -R -K -D 700000 -W 1000 -w 500000 -m none -t 5000+ \
  -- /work/target-wrapper.sh \
  > "$OUTDIR/aflnet.log" 2>&1 &
FUZZER_PID=$!
sleep "$SECONDS_RUN" & TIMER_PID=$!
wait -n -p FIRST_EXITED_PID "$FUZZER_PID" "$TIMER_PID"
FIRST_STATUS=$?
set -e
if [[ "${FIRST_EXITED_PID:-}" == "$TIMER_PID" ]]; then
  echo "SIGINT after $SECONDS_RUN seconds" > "$OUTDIR/duration-signal.txt"
  kill -INT "$FUZZER_PID" 2>/dev/null || true
  set +e; wait "$FUZZER_PID"; FUZZER_STATUS=$?; set -e
  WRAPPER_STATUS=124
else
  FUZZER_STATUS="$FIRST_STATUS"
  kill "$TIMER_PID" 2>/dev/null || true; wait "$TIMER_PID" 2>/dev/null || true
  WRAPPER_STATUS="$FUZZER_STATUS"
fi
FUZZER_PID='' TIMER_PID=''
date -u +%s > "$OUTDIR/fuzz-end-epoch.txt"
printf '%s\n' "$FUZZER_STATUS" > "$OUTDIR/fuzzer-exit-code.txt"
printf '%s\n' "$WRAPPER_STATUS" > "$OUTDIR/wrapper-exit-code.txt"
if [[ -s "$OUTDIR/aflnet-out/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' \
    "$OUTDIR/aflnet-out/fuzzer_stats" > "$OUTDIR/fuzzer-summary.txt" || true
fi

start_server post-smoke
python3 /work/smoke.py --timeout 20 --output "$OUTDIR/post-smoke/rtsp-smoke.json"
stop_server
date -u +%s > "$OUTDIR/external-end-epoch.txt"
if [[ "$WRAPPER_STATUS" -ne 124 && "$WRAPPER_STATUS" -ne 0 ]]; then exit "$WRAPPER_STATUS"; fi
