#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:-/work/results/smtp-30m}"
DURATION="${2:-1800s}"
SECONDS_RUN="${DURATION%s}"
[[ "$SECONDS_RUN" =~ ^[0-9]+$ ]] || { echo 'Duration must be integer seconds.' >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n "$(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: $OUTDIR" >&2; exit 2
fi
mkdir -p "$OUTDIR" "$OUTDIR/coverage" "$OUTDIR/post-smoke/coverage"
cp /work/build-evidence/build-lock.txt "$OUTDIR/build-lock.txt"
export AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
SERVER_PID='' FUZZER_PID='' TIMER_PID=''
stop_server() {
  local pid="$1" graceful=yes
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 100); do kill -0 "$pid" 2>/dev/null || break; sleep .1; done
  if kill -0 "$pid" 2>/dev/null; then graceful=no; kill -KILL "$pid" 2>/dev/null || true; fi
  set +e; wait "$pid"; local status=$?; set -e
  printf 'graceful=%s\nexit_code=%s\n' "$graceful" "$status" > "$OUTDIR/${SERVER_LABEL}/stop-status.txt"
  [[ "$graceful" == yes ]]
}
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  if [[ -n "$FUZZER_PID" ]] && kill -0 "$FUZZER_PID" 2>/dev/null; then kill -INT "$FUZZER_PID" 2>/dev/null || true; wait "$FUZZER_PID" 2>/dev/null || true; fi
  if [[ -n "$TIMER_PID" ]] && kill -0 "$TIMER_PID" 2>/dev/null; then kill "$TIMER_PID" 2>/dev/null || true; wait "$TIMER_PID" 2>/dev/null || true; fi
  if [[ -n "$SERVER_PID" ]]; then stop_server "$SERVER_PID" || true; fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
wait_ready() {
  local end=$((SECONDS + 45))
  while (( SECONDS < end )); do
    if python3 - <<'PY' >/dev/null 2>&1
import socket
with socket.create_connection(('127.0.0.1', 2525), timeout=1) as s:
    s.settimeout(1)
    if not s.recv(1024).startswith(b'220'): raise SystemExit(1)
    s.sendall(b'QUIT\r\n')
PY
    then return 0; fi
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then break; fi
    sleep .3
  done
  echo 'Haraka SMTP readiness failed' >&2
  tail -80 "$OUTDIR/$SERVER_LABEL/server.log" >&2 || true
  return 1
}
start_server() {
  SERVER_LABEL="$1"
  local coverage="$2"
  mkdir -p "$coverage" "$OUTDIR/$SERVER_LABEL"
  YES_REALLY_DO_DISCARD=1 NODE_V8_COVERAGE="$coverage" node /src/Haraka/bin/haraka -c /work/config > "$OUTDIR/$SERVER_LABEL/server.log" 2>&1 &
  SERVER_PID=$!
  echo "$SERVER_PID" > "$OUTDIR/$SERVER_LABEL/server.pid.txt"
  wait_ready
}
date -u +%s > "$OUTDIR/external-start-epoch.txt"
{
  echo "target=Haraka 3.4.0, Node.js $(node --version), SMTP over TCP 127.0.0.1:2525"
  echo 'feedback=AFLNet -P SMTP response-state graph; helper bitmap and crash counters are helper-only, not Haraka instrumentation'
  echo 'coverage=NODE_V8_COVERAGE runtime counters collected from Haraka source during campaign; independent of AFLNet mutation feedback'
  echo 'scope=loopback SMTP only; controlled rcpt_to.in_host_list and queue/discard; no outbound mail'
} > "$OUTDIR/run-method.txt"
start_server campaign "$OUTDIR/coverage"
set +e
/opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/smtp.dict -o "$OUTDIR/aflnet-out" \
  -N tcp://127.0.0.1/2525 -P SMTP -E -q 3 -s 3 -R -K -D 500000 -W 1000 -w 500000 -m none -t 5000+ \
  -- /opt/aflnet/haraka-fuzz-helper > "$OUTDIR/aflnet.log" 2>&1 &
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
stop_server "$SERVER_PID"; SERVER_PID=''
node /work/summarize-v8-coverage.js "$OUTDIR/coverage" > "$OUTDIR/v8-coverage-summary.json"
start_server post-smoke "$OUTDIR/post-smoke/coverage"
python3 /work/smoke.py --timeout 10 --output "$OUTDIR/post-smoke/smtp-smoke.json"
stop_server "$SERVER_PID"; SERVER_PID=''
node /work/summarize-v8-coverage.js "$OUTDIR/post-smoke/coverage" > "$OUTDIR/post-smoke/v8-coverage-summary.json"
date -u +%s > "$OUTDIR/external-end-epoch.txt"
if [[ "$WRAPPER_STATUS" -ne 124 && "$WRAPPER_STATUS" -ne 0 ]]; then exit "$WRAPPER_STATUS"; fi
