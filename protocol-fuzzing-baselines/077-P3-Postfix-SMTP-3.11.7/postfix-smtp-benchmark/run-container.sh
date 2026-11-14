#!/usr/bin/env bash
set -Eeuo pipefail
OUTDIR=$1
DURATION=$2
[[ $DURATION =~ ^[0-9]+$ ]] || { echo "duration must be integer seconds" >&2; exit 2; }
mkdir -p "$OUTDIR"
[[ -z "$(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit)" ]] || {
  echo "output directory must be empty: $OUTDIR" >&2
  exit 2
}
cp /work/build-evidence/build-lock.txt "$OUTDIR/build-lock.txt"
cp /work/build-evidence/*-ldd.txt "$OUTDIR/"
export MAIL_CONFIG=/etc/postfix

SERVER_PID=
FUZZER_PID=
TIMER_PID=
SERVER_LABEL=

prepare_gcov_prefix() {
  local prefix=$1 source_dir relative
  mkdir -p "$prefix"
  while IFS= read -r -d '' source_dir; do
    relative=${source_dir#/src/postfix}
    mkdir -p "$prefix$relative"
  done < <(find /src/postfix -type d -print0)
  chmod -R a+rwX "$prefix"
}

stop_server() {
  [[ -n "$SERVER_LABEL" ]] || return 0
  local state=stopped stop_rc=0
  if /usr/sbin/postfix status >/dev/null 2>&1; then
    /usr/sbin/postfix stop >> "$OUTDIR/$SERVER_LABEL/server.log" 2>&1 || stop_rc=$?
    for _ in $(seq 1 200); do
      if ! /usr/sbin/postfix status >/dev/null 2>&1; then
        state=stopped
        break
      fi
      sleep 0.1
    done
  fi
  if /usr/sbin/postfix status >/dev/null 2>&1; then
    state=forced
    if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
      kill -TERM "$SERVER_PID" 2>/dev/null || true
      for _ in $(seq 1 20); do
        if ! /usr/sbin/postfix status >/dev/null 2>&1; then break; fi
        sleep 0.1
      done
    fi
    /usr/sbin/postfix status >/dev/null 2>&1 && stop_rc=1
  fi
  printf 'shutdown=%s\npostfix_stop_exit_code=%s\n' "$state" "$stop_rc" > "$OUTDIR/$SERVER_LABEL/stop-status.txt"
  if ss -ltn | grep -q '127.0.0.1:2525'; then
    echo "SMTP listener remained open after shutdown" >&2
    stop_rc=1
  fi
  SERVER_PID=
  SERVER_LABEL=
  [[ $state == stopped && $stop_rc == 0 ]]
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
  if [[ -n "$SERVER_LABEL" ]]; then stop_server || true; fi
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

start_server() {
  SERVER_LABEL=$1
  local profile_dir=$2
  mkdir -p "$OUTDIR/$SERVER_LABEL"
  find /src/postfix -type f -name '*.gcda' -delete
  prepare_gcov_prefix "$profile_dir"
  export GCOV_PREFIX="$profile_dir"
  export GCOV_PREFIX_STRIP=2
  /usr/sbin/postfix start > "$OUTDIR/$SERVER_LABEL/server.log" 2>&1 || {
    tail -80 "$OUTDIR/$SERVER_LABEL/server.log" >&2 || true
    return 1
  }
  SERVER_PID=$(cat /var/spool/postfix/pid/master.pid 2>/dev/null || true)
  printf '%s\n' "$SERVER_PID" > "$OUTDIR/$SERVER_LABEL/server.pid.txt"
  local deadline=$((SECONDS + 45))
  while (( SECONDS < deadline )); do
    if python3 - <<'PY' >/dev/null 2>&1
import socket
with socket.create_connection(("127.0.0.1", 2525), timeout=1) as sock:
    sock.settimeout(1)
    greeting = sock.recv(256)
    if not greeting.startswith(b"220"):
        raise SystemExit(1)
    sock.sendall(b"QUIT\r\n")
PY
    then
      /usr/sbin/postfix status >/dev/null 2>&1 || return 1
      return 0
    fi
    if [[ -n "$SERVER_PID" ]] && ! kill -0 "$SERVER_PID" 2>/dev/null; then
      break
    fi
    sleep 0.25
  done
  echo "Postfix failed SMTP readiness in $SERVER_LABEL" >&2
  tail -80 "$OUTDIR/$SERVER_LABEL/server.log" >&2 || true
  return 1
}

collect_coverage() {
  local label=$1 profile_dir=$2
  local count file relative
  count=$(find "$profile_dir" -type f -name '*.gcda' | wc -l)
  printf 'gcda_files=%s\n' "$count" > "$OUTDIR/$label/coverage-files.txt"
  (( count > 0 )) || { echo "No Postfix gcov counters flushed for $label" >&2; return 1; }
  find /src/postfix -type f -name '*.gcda' -delete
  cp -a "$profile_dir/." /src/postfix/
  (
    cd /src/postfix
    gcovr --root /src/postfix --object-directory /src/postfix \
      --json-summary-pretty --json-summary "$OUTDIR/$label/gcov-summary.json" \
      --print-summary
  ) > "$OUTDIR/$label/gcov-summary.txt"
  mkdir -p "$OUTDIR/$label/gcda"
  while IFS= read -r -d '' file; do
    relative=${file#/src/postfix/}
    mkdir -p "$OUTDIR/$label/gcda/$(dirname "$relative")"
    cp "$file" "$OUTDIR/$label/gcda/$relative"
  done < <(find /src/postfix -type f -name '*.gcda' -print0)
  find /src/postfix -type f -name '*.gcda' -delete
  find "$OUTDIR/$label/gcda" -depth -type d -empty -delete
}

date -u +%Y-%m-%dT%H:%M:%SZ > "$OUTDIR/external-start-utc.txt"
prepare_gcov_prefix "$OUTDIR/config-check-gcov"
GCOV_PREFIX="$OUTDIR/config-check-gcov" GCOV_PREFIX_STRIP=2 \
  /usr/sbin/postfix check > "$OUTDIR/config-check.txt" 2>&1
find "$OUTDIR/config-check-gcov" -type f -name '*.gcda' | wc -l \
  > "$OUTDIR/config-check-gcda-count.txt"
rm -rf "$OUTDIR/config-check-gcov"
find /src/postfix -type f -name '*.gcda' -delete

start_server preflight "$OUTDIR/preflight-gcov"
python3 /work/smoke.py --timeout 10 --output "$OUTDIR/preflight-smoke.json"
stop_server
collect_coverage preflight "$OUTDIR/preflight-gcov"

start_server campaign "$OUTDIR/campaign-gcov"
{
  printf 'implementation=Postfix 3.11.7; SMTP loopback TCP 127.0.0.1:2525\n'
  printf 'feedback=AFLNet SMTP response-state graph; bitmap is helper-only\n'
  printf 'target_coverage=GCC gcov counters from Postfix daemon processes, collected separately\n'
  printf 'scope=SMTP command, envelope, DATA framing, and response state; no STARTTLS or external relay\n'
  printf 'duration_seconds=%s\n' "$DURATION"
} > "$OUTDIR/run-method.txt"
printf 'start_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUTDIR/run-times.txt"
set +e
/opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/smtp.dict -o "$OUTDIR/aflnet-out" \
  -N tcp://127.0.0.1/2525 -P SMTP -E -q 3 -s 3 -R -K -D 10000 \
  -W 250 -w 100000 -m none -t 5000+ -- /opt/aflnet/postfix-fuzz-helper \
  > "$OUTDIR/aflnet.log" 2>&1 &
FUZZER_PID=$!
sleep "$DURATION" &
TIMER_PID=$!
wait -n -p FIRST_EXITED_PID "$FUZZER_PID" "$TIMER_PID"
FIRST_STATUS=$?
set -e
if [[ $FIRST_EXITED_PID == "$TIMER_PID" ]]; then
  printf 'timer_signal_utc=%s\nduration_seconds=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$DURATION" \
    > "$OUTDIR/duration-signal.txt"
  kill -INT "$FUZZER_PID" 2>/dev/null || true
  set +e
  wait "$FUZZER_PID"
  FUZZER_STATUS=$?
  set -e
  WRAPPER_STATUS=124
else
  FUZZER_STATUS=$FIRST_STATUS
  kill "$TIMER_PID" 2>/dev/null || true
  wait "$TIMER_PID" 2>/dev/null || true
  WRAPPER_STATUS=$FUZZER_STATUS
fi
FUZZER_PID=
TIMER_PID=
printf 'end_utc=%s\nfuzzer_exit_code=%s\nwrapper_exit_code=%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$FUZZER_STATUS" "$WRAPPER_STATUS" >> "$OUTDIR/run-times.txt"
if [[ -s "$OUTDIR/aflnet-out/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' \
    "$OUTDIR/aflnet-out/fuzzer_stats" > "$OUTDIR/fuzzer-summary.txt" || true
  printf 'new_ipsm_paths : %s\n' "$(find "$OUTDIR/aflnet-out/replayable-new-ipsm-paths" -type f 2>/dev/null | wc -l)" >> "$OUTDIR/fuzzer-summary.txt"
  printf 'replayable_queue : %s\n' "$(find "$OUTDIR/aflnet-out/replayable-queue" -type f 2>/dev/null | wc -l)" >> "$OUTDIR/fuzzer-summary.txt"
fi
stop_server
collect_coverage campaign "$OUTDIR/campaign-gcov"

start_server replay "$OUTDIR/replay-gcov"
python3 /work/replay.py --aflnet-output "$OUTDIR/aflnet-out" --timeout 1 \
  --output "$OUTDIR/queue-replay.json"
stop_server
collect_coverage replay "$OUTDIR/replay-gcov"

start_server post-smoke "$OUTDIR/post-smoke-gcov"
python3 /work/smoke.py --timeout 10 --output "$OUTDIR/post-smoke.json"
stop_server
collect_coverage post-smoke "$OUTDIR/post-smoke-gcov"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUTDIR/external-end-utc.txt"

if [[ $WRAPPER_STATUS != 124 && $WRAPPER_STATUS != 0 ]]; then
  exit "$WRAPPER_STATUS"
fi
