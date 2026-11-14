#!/usr/bin/env bash
set -euo pipefail

OUTDIR="$1"
DURATION="$2"
[[ "$DURATION" =~ ^[0-9]+$ ]] || { echo "Duration must be whole seconds." >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n "$(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: $OUTDIR" >&2
  exit 2
fi

mkdir -p "$OUTDIR/preflight/go-coverdata" "$OUTDIR/campaign/go-coverdata" \
  "$OUTDIR/post-smoke/go-coverdata" "$OUTDIR/post-smoke"
cp /work/build-evidence/build-lock.txt "$OUTDIR/build-lock.txt"
cp /work/build-evidence/go-version-info.txt "$OUTDIR/go-version-info.txt"
cp /work/build-evidence/rtmp-adapter.sha256 "$OUTDIR/rtmp-adapter.sha256"
printf 'target=/opt/mediamtx/mediamtx v1.21.3 with Go native coverage (-coverpkg=./...)\n' > "$OUTDIR/run-method.txt"
printf 'protocol=RTMP v3 over TCP; MediaMTX 127.0.0.1:1935, local handshake bridge 127.0.0.1:1936\n' >> "$OUTDIR/run-method.txt"
printf 'AFLNet -P RTMP uses parsed AMF command response states; every testcase starts with C0/C1 and a placeholder C2; bridge emits the per-connection S1 echo required by RTMP\n' >> "$OUTDIR/run-method.txt"
printf 'coverage=campaign Go counters are separate from validation and post-smoke counters; AFL bitmap and process counters describe only the lifecycle helper\n' >> "$OUTDIR/run-method.txt"
date -u +%s > "$OUTDIR/external-start-epoch.txt"

SERVER_PID=""
PROXY_PID=""
FUZZER_PID=""
TIMER_PID=""
server_state() {
  if [[ ! -r "/proc/$1/status" ]]; then printf gone; return; fi
  awk '/^State:/ {print $2}' "/proc/$1/status"
}
start_server() {
  local label="$1" coverdir="$2" workdir="$OUTDIR/$1/server-work"
  mkdir -p "$OUTDIR/$label" "$coverdir" "$workdir"
  (
    cd "$workdir"
    GOCOVERDIR="$coverdir" exec /opt/mediamtx/mediamtx /work/mediamtx.yml
  ) > "$OUTDIR/$label/server.log" 2>&1 &
  SERVER_PID=$!
  printf '%s\n' "$SERVER_PID" > "$OUTDIR/$label/server.pid.txt"
  local deadline=$((SECONDS + 30))
  while (( SECONDS < deadline )); do
    local state
    state="$(server_state "$SERVER_PID")"
    [[ "$state" == gone || "$state" == Z || "$state" == X ]] && break
    if python3 -c 'import socket; s=socket.create_connection(("127.0.0.1",1935),timeout=.2); s.close()' >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.2
  done
  echo "MediaMTX RTMP listener failed to start." >&2
  tail -80 "$OUTDIR/$label/server.log" >&2 || true
  return 1
}
start_proxy() {
  local label="$1"
  python3 /work/rtmp_proxy.py --stats "$OUTDIR/$label/proxy-stats.json" \
    > "$OUTDIR/$label/proxy.log" 2>&1 &
  PROXY_PID=$!
  sleep 0.25
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
  [[ -n "$SERVER_PID" ]] || return 0
  state="$(server_state "$SERVER_PID")"
  if [[ "$state" != gone && "$state" != Z && "$state" != X ]]; then
    kill -TERM "$SERVER_PID" >/dev/null 2>&1 || true
    for _ in $(seq 1 300); do
      state="$(server_state "$SERVER_PID")"
      [[ "$state" == gone || "$state" == Z || "$state" == X ]] && break
      sleep 0.1
    done
    state="$(server_state "$SERVER_PID")"
    if [[ "$state" != gone && "$state" != Z && "$state" != X ]]; then
      graceful=no
      kill -KILL "$SERVER_PID" >/dev/null 2>&1 || true
    fi
  fi
  set +e
  wait "$SERVER_PID"
  exit_code=$?
  set -e
  printf 'signal=SIGTERM\ngraceful=%s\nprocess_exit_code=%s\n' "$graceful" "$exit_code" > "$OUTDIR/$label/server-stop-status.txt"
  SERVER_PID=""
  if [[ "$graceful" != yes || "$exit_code" -ne 0 ]]; then
    echo "MediaMTX $label did not stop cleanly (graceful=$graceful, code=$exit_code)." >&2
    return 1
  fi
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
  if [[ -n "$SERVER_PID" ]]; then stop_server interrupted || true; fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

start_server preflight "$OUTDIR/preflight/go-coverdata"
start_proxy preflight
python3 /work/rtmp_smoke.py --host 127.0.0.1 --port 1936 --timeout 8 \
  --output "$OUTDIR/preflight/rtmp-smoke.json"
stop_proxy preflight
stop_server preflight

start_server campaign "$OUTDIR/campaign/go-coverdata"
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

start_server post-smoke "$OUTDIR/post-smoke/go-coverdata"
start_proxy post-smoke
python3 /work/rtmp_smoke.py --host 127.0.0.1 --port 1936 --timeout 8 \
  --output "$OUTDIR/post-smoke/rtmp-smoke.json"
printf 'rtmp_health=pass_on_fresh_post_campaign_process\n' > "$OUTDIR/post-smoke/health.txt"
stop_proxy post-smoke
stop_server post-smoke
trap - EXIT INT TERM
date -u +%s > "$OUTDIR/external-end-epoch.txt"

GO=/usr/local/go/bin/go
export GOCACHE="${GOCACHE:-/tmp/go-build}"
for phase in campaign post-smoke; do
  input="$OUTDIR/$phase/go-coverdata"
  test -n "$(find "$input" -type f -name 'covcounters.*' -print -quit)" || {
    echo "No Go coverage counters were flushed from $input." >&2
    exit 1
  }
  raw="$OUTDIR/$phase/go-coverage.out"
  "$GO" tool covdata textfmt -i="$input" -o="$raw"
  (cd /src/mediamtx && "$GO" tool cover -func="$raw") > "$OUTDIR/$phase/go-coverage-summary.txt"
done
mkdir -p "$OUTDIR/go-coverdata-merged"
"$GO" tool covdata merge -i="$OUTDIR/campaign/go-coverdata,$OUTDIR/post-smoke/go-coverdata" \
  -o="$OUTDIR/go-coverdata-merged"
"$GO" tool covdata textfmt -i="$OUTDIR/go-coverdata-merged" -o="$OUTDIR/go-coverage.out"
(cd /src/mediamtx && "$GO" tool cover -func="$OUTDIR/go-coverage.out") > "$OUTDIR/go-coverage-summary.txt"
date -u +%s > "$OUTDIR/external-end-epoch.txt"
printf 'run_exit_status=0\n' > "$OUTDIR/ACCEPTANCE.txt"
