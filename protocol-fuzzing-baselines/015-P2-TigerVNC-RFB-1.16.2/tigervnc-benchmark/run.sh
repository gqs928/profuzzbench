#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:-/work/results/rfb-30m}"
DURATION="${2:-1800s}"
SECONDS_RUN="${DURATION%s}"
[[ "$SECONDS_RUN" =~ ^[0-9]+$ ]] || { echo 'Duration must be integer seconds.' >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n "$(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: $OUTDIR" >&2; exit 2
fi
mkdir -p "$OUTDIR/preflight" "$OUTDIR/campaign" "$OUTDIR/post-smoke"
cp /work/build-evidence/build-lock.txt "$OUTDIR/build-lock.txt"
export AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 DISPLAY=:1
XVFB_PID='' TARGET_PID='' FUZZER_PID='' TIMER_PID=''
stop_pid() {
  local pid="$1" label="$2" state=running rc=0
  [[ -n "$pid" ]] || return 0
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 200); do
    if ! kill -0 "$pid" 2>/dev/null; then state=stopped; break; fi
    sleep .1
  done
  if [[ "$state" != stopped ]]; then state=forced; kill -KILL "$pid" 2>/dev/null || true; fi
  set +e; wait "$pid"; rc=$?; set -e
  printf 'shutdown=%s\nexit_code=%s\n' "$state" "$rc" > "$OUTDIR/$label/stop-status.txt"
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
  if [[ -n "$TARGET_PID" ]]; then stop_pid "$TARGET_PID" "$TARGET_LABEL" || true; fi
  if [[ -n "$XVFB_PID" ]]; then kill -TERM "$XVFB_PID" 2>/dev/null || true; wait "$XVFB_PID" 2>/dev/null || true; fi
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
start_xvfb() {
  Xvfb :1 -screen 0 640x480x24 -nolisten tcp > "$OUTDIR/xvfb.log" 2>&1 &
  XVFB_PID=$!
  for _ in $(seq 1 100); do
    if xdpyinfo -display :1 >/dev/null 2>&1; then return 0; fi
    kill -0 "$XVFB_PID" 2>/dev/null || break
    sleep .1
  done
  echo 'Xvfb did not become ready' >&2
  cat "$OUTDIR/xvfb.log" >&2
  return 1
}
start_target() {
  TARGET_LABEL="$1"
  mkdir -p "$OUTDIR/$TARGET_LABEL"
  /opt/tigervnc/bin/x0vncserver -display :1 -rfbport 5901 -SecurityTypes None -localhost \
    > "$OUTDIR/$TARGET_LABEL/server.log" 2>&1 &
  TARGET_PID=$!
  echo "$TARGET_PID" > "$OUTDIR/$TARGET_LABEL/server.pid.txt"
}
start_xvfb
date -u +%s > "$OUTDIR/external-start-epoch.txt"
{
  echo 'target=TigerVNC 1.16.2 x0vncserver; RFB 3.8; TCP 127.0.0.1:5901'
  echo 'feedback=AFLNet -P RFB response-state graph; raw AFL bitmap is retained separately and counts as target code feedback only when nonzero'
  echo 'scope=localhost-only, SecurityTypes=None, isolated Xvfb :1 at 640x480x24; no external X server or display'
} > "$OUTDIR/run-method.txt"
start_target preflight
python3 /work/smoke.py --timeout 15 --output "$OUTDIR/preflight/rfb-smoke.json"
stop_pid "$TARGET_PID" preflight; TARGET_PID=''

set +e
/opt/aflnet/afl-fuzz -d -i /work/seeds -o "$OUTDIR/aflnet-out" \
  -N tcp://127.0.0.1/5901 -P RFB -E -q 3 -s 3 -R -K -D 700000 -W 1000 -w 500000 -m none -t 30000+ \
  -- /opt/tigervnc/bin/x0vncserver -display :1 -rfbport 5901 -SecurityTypes None -localhost \
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

start_target post-smoke
python3 /work/smoke.py --timeout 15 --output "$OUTDIR/post-smoke/rfb-smoke.json"
stop_pid "$TARGET_PID" post-smoke; TARGET_PID=''
date -u +%s > "$OUTDIR/external-end-epoch.txt"
if [[ "$WRAPPER_STATUS" -ne 124 && "$WRAPPER_STATUS" -ne 0 ]]; then exit "$WRAPPER_STATUS"; fi
