#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:-/work/results/smtp-30m}"
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
  if [[ "$state" != stopped ]]; then
    state=forced
    kill -KILL "$pid" 2>/dev/null || true
  fi
  set +e; wait "$pid"; rc=$?; set -e
  printf 'shutdown=%s\nexit_code=%s\n' "$state" "$rc" > "$OUTDIR/$SERVER_LABEL/stop-status.txt"
  SERVER_PID=''
  [[ "$state" == stopped ]]
}

cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  if [[ -n "$FUZZER_PID" ]] && kill -0 "$FUZZER_PID" 2>/dev/null; then
    kill -INT "$FUZZER_PID" 2>/dev/null || true
    wait "$FUZZER_PID" 2>/dev/null || true
  fi
  if [[ -n "$TIMER_PID" ]] && kill -0 "$TIMER_PID" 2>/dev/null; then
    kill "$TIMER_PID" 2>/dev/null || true
    wait "$TIMER_PID" 2>/dev/null || true
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
    if python3 - <<'PY' >/dev/null 2>&1
import socket
with socket.create_connection(('127.0.0.1',2525),timeout=1) as s:
    s.settimeout(1)
    if not s.recv(1024).startswith(b'220'): raise SystemExit(1)
    s.sendall(b'QUIT\r\n')
PY
    then return 0; fi
    kill -0 "$SERVER_PID" 2>/dev/null || break
    sleep .25
  done
  echo "OpenSMTPD did not become ready in $SERVER_LABEL" >&2
  tail -80 "$OUTDIR/$SERVER_LABEL/server.log" >&2 || true
  return 1
}

start_server() {
  SERVER_LABEL="$1"
  local profile_dir="$2"
  mkdir -p "$OUTDIR/$SERVER_LABEL" "$profile_dir"
  (
    cd /src/OpenSMTPD
    GCOV_PREFIX="$profile_dir" GCOV_PREFIX_STRIP=2 \
      exec /opt/opensmtpd/sbin/smtpd -d -f /work/smtpd.conf
  ) > "$OUTDIR/$SERVER_LABEL/server.log" 2>&1 &
  SERVER_PID=$!
  echo "$SERVER_PID" > "$OUTDIR/$SERVER_LABEL/server.pid.txt"
  wait_ready
}

collect_coverage() {
  local label="$1" profile_dir="$2"
  local gcda_count
  gcda_count="$(find "$profile_dir" -type f -name '*.gcda' | wc -l)"
  printf 'gcda_files=%s\n' "$gcda_count" > "$OUTDIR/$label/coverage-files.txt"
  (( gcda_count > 0 )) || { echo "No OpenSMTPD GCOV counters were flushed for $label." >&2; return 1; }
  cp -a "$profile_dir/." /src/OpenSMTPD/
  (
    cd /src/OpenSMTPD
    gcovr --root /src/OpenSMTPD --object-directory /src/OpenSMTPD \
      --json-summary-pretty --json-summary "$OUTDIR/$label/gcov-summary.json" --print-summary
  ) > "$OUTDIR/$label/gcov-summary.txt"
  find /src/OpenSMTPD -type f -name '*.gcda' -delete
}

date -u +%s > "$OUTDIR/external-start-epoch.txt"
{
  printf 'target=OpenSMTPD 7.9.0p0; SMTP loopback TCP 127.0.0.1:2525\n'
  printf 'feedback=AFLNet -P SMTP response-state graph; AFL bitmap/crash counters describe only opensmtpd-fuzz-helper\n'
  printf 'target_coverage=GCC --coverage counters from the persistent OpenSMTPD service, flushed after each phase and summarized separately\n'
  printf 'scope=local delivery only to fuzz.invalid; no relay rule; isolated mbox path\n'
} > "$OUTDIR/run-method.txt"
/opt/opensmtpd/sbin/smtpd -n -f /work/smtpd.conf > "$OUTDIR/config-check.txt" 2>&1

start_server preflight "$OUTDIR/preflight/gcov"
python3 /work/smoke.py --timeout 10 --output "$OUTDIR/preflight/smtp-smoke.json"
stop_server
rm -rf "$OUTDIR/preflight/gcov"

start_server campaign "$OUTDIR/campaign-gcov"
set +e
/opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/smtp.dict -o "$OUTDIR/aflnet-out" \
  -N tcp://127.0.0.1/2525 -P SMTP -E -q 3 -s 3 -R -K -D 500000 -W 1000 -w 500000 -m none -t 5000+ \
  -- /opt/aflnet/opensmtpd-fuzz-helper > "$OUTDIR/aflnet.log" 2>&1 &
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
stop_server
collect_coverage campaign "$OUTDIR/campaign-gcov"

start_server post-smoke "$OUTDIR/post-smoke/gcov"
python3 /work/smoke.py --timeout 10 --output "$OUTDIR/post-smoke/smtp-smoke.json"
stop_server
collect_coverage post-smoke "$OUTDIR/post-smoke/gcov"
date -u +%s > "$OUTDIR/external-end-epoch.txt"
if [[ "$WRAPPER_STATUS" -ne 124 && "$WRAPPER_STATUS" -ne 0 ]]; then exit "$WRAPPER_STATUS"; fi
