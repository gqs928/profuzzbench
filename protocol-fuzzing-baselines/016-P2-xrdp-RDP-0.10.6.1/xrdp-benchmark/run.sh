#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:-/work/results/rdp-30m}"
DURATION="${2:-1800s}"
SECONDS_RUN="${DURATION%s}"
[[ "$SECONDS_RUN" =~ ^[0-9]+$ ]] || { echo 'Duration must be integer seconds.' >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n "$(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: $OUTDIR" >&2; exit 2
fi
mkdir -p "$OUTDIR/preflight" "$OUTDIR/campaign" "$OUTDIR/post-smoke"
cp /work/build-evidence/build-lock.txt "$OUTDIR/build-lock.txt"
cp /work/build-evidence/config-check.txt "$OUTDIR/config-check.txt"
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
wait_ready() {
  local end=$((SECONDS + 45))
  while (( SECONDS < end )); do
    if python3 /work/smoke.py --timeout 1 --output "$OUTDIR/$SERVER_LABEL/readiness.json" >/dev/null 2>&1; then return 0; fi
    kill -0 "$SERVER_PID" 2>/dev/null || break
    sleep .25
  done
  echo "xrdp did not become ready in $SERVER_LABEL" >&2
  tail -80 "$OUTDIR/$SERVER_LABEL/server.log" >&2 || true
  return 1
}
start_server() {
  SERVER_LABEL="$1"
  mkdir -p "$OUTDIR/$SERVER_LABEL"
  /opt/xrdp/sbin/xrdp -n -c /work/xrdp.ini > "$OUTDIR/$SERVER_LABEL/server.log" 2>&1 &
  SERVER_PID=$!
  echo "$SERVER_PID" > "$OUTDIR/$SERVER_LABEL/server.pid.txt"
  wait_ready
}
date -u +%s > "$OUTDIR/external-start-epoch.txt"
{
  echo 'target=xrdp 0.10.6.1; RDP/X.224 negotiation; TCP 127.0.0.1:3390'
  echo 'feedback=AFLNet -P RDP TPKT segmentation and negotiation states; AFL bitmap/crash counters describe only xrdp-fuzz-helper, not xrdp'
  echo 'scope=local classic RDP security negotiation only; no MCS login, session manager, or external network'
} > "$OUTDIR/run-method.txt"
start_server preflight
python3 /work/smoke.py --timeout 10 --output "$OUTDIR/preflight/rdp-smoke.json"
stop_server
start_server campaign

set +e
/opt/aflnet/afl-fuzz -d -i /work/seeds -o "$OUTDIR/aflnet-out" \
  -N tcp://127.0.0.1/3390 -P RDP -E -q 3 -s 3 -R -K -D 700000 -W 1000 -w 500000 -m none -t 5000+ \
  -- /opt/aflnet/xrdp-fuzz-helper > "$OUTDIR/aflnet.log" 2>&1 &
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
stop_server
date -u +%s > "$OUTDIR/fuzz-end-epoch.txt"
printf '%s\n' "$FUZZER_STATUS" > "$OUTDIR/fuzzer-exit-code.txt"
printf '%s\n' "$WRAPPER_STATUS" > "$OUTDIR/wrapper-exit-code.txt"
if [[ -s "$OUTDIR/aflnet-out/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' \
    "$OUTDIR/aflnet-out/fuzzer_stats" > "$OUTDIR/fuzzer-summary.txt" || true
fi

start_server post-smoke
python3 /work/smoke.py --timeout 10 --output "$OUTDIR/post-smoke/rdp-smoke.json"
stop_server
date -u +%s > "$OUTDIR/external-end-epoch.txt"
if [[ "$WRAPPER_STATUS" -ne 124 && "$WRAPPER_STATUS" -ne 0 ]]; then exit "$WRAPPER_STATUS"; fi
