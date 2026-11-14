#!/usr/bin/env bash
set -euo pipefail

OUTDIR="$1"
DURATION="$2"
[[ "$DURATION" =~ ^[0-9]+$ ]] || { echo "Duration must be whole seconds." >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n "$(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: $OUTDIR" >&2
  exit 2
fi

mkdir -p "$OUTDIR/preflight" "$OUTDIR/campaign" \
  "$OUTDIR/post-smoke" "$OUTDIR/interrupted"
cp /work/build-evidence/build-lock.txt "$OUTDIR/build-lock.txt"
cp /work/build-evidence/srs-version.txt "$OUTDIR/srs-version.txt"
cp /work/build-evidence/srs-binary.sha256 "$OUTDIR/srs-binary.sha256"
printf 'protocol=RTMP v3/TCP; SRS listener 127.0.0.1:1935; AFLNet bridge 127.0.0.1:1936\n' > "$OUTDIR/run-method.txt"
printf 'AFLNet parser uses handshake and RTMP command response states; SRS is compiled with GCC native coverage and gcovr reports target code coverage.\n' >> "$OUTDIR/run-method.txt"
date -u +%s > "$OUTDIR/external-start-epoch.txt"

SRS_PID=""
PROXY_PID=""
FUZZER_PID=""
TIMER_PID=""

server_state() {
  if [[ ! -r "/proc/$1/status" ]]; then printf gone; return; fi
  awk '/^State:/ {print $2}' "/proc/$1/status"
}

clear_gcov_data() {
  find /src/srs/trunk/objs -type f -name '*.gcda' -delete
}

start_server() {
  local label="$1" workdir="$OUTDIR/$1/server-work"
  mkdir -p "$OUTDIR/$label" "$workdir/logs" "$workdir/objs"
  clear_gcov_data
  (
    cd "$workdir"
    exec /src/srs/trunk/objs/srs -c /work/rtmp.conf
  ) > "$OUTDIR/$label/server.log" 2>&1 &
  SRS_PID=$!
  printf '%s\n' "$SRS_PID" > "$OUTDIR/$label/server.pid.txt"
  local deadline=$((SECONDS + 30))
  while (( SECONDS < deadline )); do
    local state
    state="$(server_state "$SRS_PID")"
    [[ "$state" == gone || "$state" == Z || "$state" == X ]] && break
    if python3 -c 'import socket; s=socket.create_connection(("127.0.0.1",1935),timeout=.2); s.close()' >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.2
  done
  echo "SRS RTMP listener failed to start." >&2
  tail -80 "$OUTDIR/$label/server.log" >&2 || true
  return 1
}

start_proxy() {
  local label="$1"
  python3 /work/rtmp_proxy.py --stats "$OUTDIR/$label/proxy-stats.json" \
    > "$OUTDIR/$label/proxy.log" 2>&1 &
  PROXY_PID=$!
  sleep 0.2
}

stop_proxy() {
  local label="$1" status=0
  if [[ -n "$PROXY_PID" ]]; then
    kill -TERM "$PROXY_PID" >/dev/null 2>&1 || true
    wait "$PROXY_PID" >/dev/null 2>&1 || status=$?
    printf 'signal=SIGTERM\nprocess_exit_code=%s\n' "$status" > "$OUTDIR/$label/proxy-stop-status.txt"
    PROXY_PID=""
  fi
}

stop_server() {
  local label="$1" graceful=yes exit_code=0 state
  [[ -n "$SRS_PID" ]] || return 0
  state="$(server_state "$SRS_PID")"
  if [[ "$state" != gone && "$state" != Z && "$state" != X ]]; then
    kill -TERM "$SRS_PID" >/dev/null 2>&1 || true
    for _ in $(seq 1 300); do
      state="$(server_state "$SRS_PID")"
      [[ "$state" == gone || "$state" == Z || "$state" == X ]] && break
      sleep 0.1
    done
    state="$(server_state "$SRS_PID")"
    if [[ "$state" != gone && "$state" != Z && "$state" != X ]]; then
      graceful=no
      kill -KILL "$SRS_PID" >/dev/null 2>&1 || true
    fi
  fi
  set +e
  wait "$SRS_PID"
  exit_code=$?
  set -e
  printf 'signal=SIGTERM\ngraceful=%s\nprocess_exit_code=%s\n' "$graceful" "$exit_code" > "$OUTDIR/$label/server-stop-status.txt"
  SRS_PID=""
  if [[ "$graceful" != yes || "$exit_code" -ne 0 ]]; then
    echo "SRS $label did not stop cleanly (graceful=$graceful, code=$exit_code)." >&2
    return 1
  fi
}

collect_coverage() {
  local label="$1" data_dir="$OUTDIR/$1/gcov-data"
  mkdir -p "$data_dir"
  find /src/srs/trunk/objs -type f -name '*.gcda' -print0 | while IFS= read -r -d '' file; do
    rel="${file#/src/srs/trunk/objs/}"
    mkdir -p "$data_dir/$(dirname "$rel")"
    cp "$file" "$data_dir/$rel"
  done
  test -n "$(find /src/srs/trunk/objs -type f -name '*.gcda' -print -quit)" || {
    echo "SRS did not flush GCC coverage counters for $label." >&2
    return 1
  }
  (cd /src/srs/trunk && gcovr --root /src/srs/trunk --object-directory /src/srs/trunk/objs --txt-summary) \
    > "$OUTDIR/$label/coverage-summary.txt"
}

cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  mkdir -p "$OUTDIR/interrupted"
  if [[ -n "$FUZZER_PID" ]] && kill -0 "$FUZZER_PID" >/dev/null 2>&1; then
    kill -INT "$FUZZER_PID" >/dev/null 2>&1 || true
    wait "$FUZZER_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$TIMER_PID" ]] && kill "$TIMER_PID" >/dev/null 2>&1; then wait "$TIMER_PID" >/dev/null 2>&1 || true; fi
  if [[ -n "$PROXY_PID" ]]; then stop_proxy interrupted || true; fi
  if [[ -n "$SRS_PID" ]]; then stop_server interrupted || true; fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

start_server preflight
start_proxy preflight
python3 /work/rtmp_smoke.py --host 127.0.0.1 --port 1936 --timeout 8 \
  --output "$OUTDIR/preflight/rtmp-smoke.json"
stop_proxy preflight
stop_server preflight
collect_coverage preflight

start_server campaign
start_proxy campaign
mkdir -p "$OUTDIR/campaign/aflnet-out"
date -u +%s > "$OUTDIR/campaign/start-epoch.txt"
export AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
set +e
/opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/rtmp.dict \
  -o "$OUTDIR/campaign/aflnet-out" -N tcp://127.0.0.1/1936 -P RTMP \
  -E -q 3 -s 3 -R -K -D 10000 -W 100 -w 100000 -m none -t 5000+ \
  -- /opt/aflnet/rtmp-fuzz-helper > "$OUTDIR/campaign/aflnet.log" 2>&1 &
FUZZER_PID=$!
sleep "$DURATION" &
TIMER_PID=$!
wait -n -p FIRST_EXITED_PID "$FUZZER_PID" "$TIMER_PID"
FIRST_EXIT_STATUS=$?
set -e
if [[ "$FIRST_EXITED_PID" == "$TIMER_PID" ]]; then
  printf 'SIGINT after %s seconds\n' "$DURATION" > "$OUTDIR/campaign/duration-signal.txt"
  kill -INT "$FUZZER_PID" >/dev/null 2>&1 || true
  set +e
  wait "$FUZZER_PID"
  FUZZER_STATUS=$?
  set -e
  WRAPPER_STATUS=124
else
  FUZZER_STATUS="$FIRST_EXIT_STATUS"
  kill "$TIMER_PID" >/dev/null 2>&1 || true
  wait "$TIMER_PID" >/dev/null 2>&1 || true
  WRAPPER_STATUS="$FUZZER_STATUS"
fi
FUZZER_PID=""
TIMER_PID=""
date -u +%s > "$OUTDIR/campaign/end-epoch.txt"
printf '%s\n' "$FUZZER_STATUS" > "$OUTDIR/campaign/fuzzer-exit-code.txt"
printf '%s\n' "$WRAPPER_STATUS" > "$OUTDIR/campaign/wrapper-exit-code.txt"
if [[ -s "$OUTDIR/campaign/aflnet-out/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' \
    "$OUTDIR/campaign/aflnet-out/fuzzer_stats" > "$OUTDIR/campaign/fuzzer-summary.txt" || true
fi
if [[ "$WRAPPER_STATUS" -ne 124 && "$WRAPPER_STATUS" -ne 0 ]]; then
  echo "AFLNet exit status: $FUZZER_STATUS" >&2
  tail -80 "$OUTDIR/campaign/aflnet.log" >&2 || true
  exit "$FUZZER_STATUS"
fi
stop_proxy campaign
stop_server campaign
collect_coverage campaign

start_server replay
start_proxy replay
python3 /work/replay_queue.py --queue "$OUTDIR/campaign/aflnet-out/replayable-queue" \
  --host 127.0.0.1 --port 1936 --output "$OUTDIR/replay/queue-replay.json"
python3 /work/rtmp_smoke.py --host 127.0.0.1 --port 1936 --timeout 8 \
  --output "$OUTDIR/replay/post-replay-smoke.json"
stop_proxy replay
stop_server replay
collect_coverage replay

start_server post-smoke
start_proxy post-smoke
python3 /work/rtmp_smoke.py --host 127.0.0.1 --port 1936 --timeout 8 \
  --output "$OUTDIR/post-smoke/rtmp-smoke.json"
printf 'rtmp_health=pass_on_fresh_post_campaign_process\n' > "$OUTDIR/post-smoke/health.txt"
stop_proxy post-smoke
stop_server post-smoke
collect_coverage post-smoke

trap - EXIT INT TERM
date -u +%s > "$OUTDIR/external-end-epoch.txt"
printf 'run_exit_status=0\n' > "$OUTDIR/ACCEPTANCE.txt"
