#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
OUTDIR=${1:-results/${TARGET_SLUG}-30m}
DURATION=${2:-1800}
if [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then echo "Output directory is not empty: $OUTDIR" >&2; exit 2; fi
MYSQL_BACKEND_PORT=$MYSQL_BACKEND_PORT "$ROOT/build-aflnet.sh"
python3 "$ROOT/generate_seeds.py"
"$ROOT/build/mysql-ready-check" --once
python3 "$ROOT/protocol_smoke.py" --port "$MYSQL_PROXY_PORT"
FUZZER="$ROOT/build/afl-fuzz"
PARAMS="$OUTDIR-run-parameters.txt"
mkdir -p "$OUTDIR"
cat > "$PARAMS" <<EOF
protocol=MySQL Classic Protocol (COM_QUERY through local auth-terminating proxy)
implementation=$TARGET_NAME $TARGET_VERSION
backend_endpoint=tcp://127.0.0.1/$MYSQL_BACKEND_PORT
fuzzer_endpoint=tcp://127.0.0.1/$MYSQL_PROXY_PORT
authentication=proxy performs fresh upstream handshake/auth for each AFLNet testcase; SQL request stream is forwarded unchanged
fuzzer=AFLNet upstream 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732 with MySQL packet parser and dumb-mode state feedback patches
mode=network-only MySQL response-state feedback (-n -E); no target source instrumentation
requested_active_seconds=$DURATION
execution_timeout=5000ms+
inputs=$ROOT/seeds
EOF
setsid "$FUZZER" -d -n -i "$ROOT/seeds" -x "$ROOT/mysql.dict" \
  -o "$OUTDIR" -N "tcp://127.0.0.1/$MYSQL_PROXY_PORT" -P MYSQL -E -q 3 -s 3 -R -K \
  -c "$ROOT/server-recover.sh" -D 10000 -W 100 -w 200000 -m none -t 5000+ \
  "$ROOT/build/mysql-ready-check" >"$OUTDIR/campaign.log" 2>&1 &
fuzz_pid=$!
wall_start=$(date +%s)
active_start=""
trap 'kill -INT -- "-"$fuzz_pid 2>/dev/null || true; wait "$fuzz_pid" 2>/dev/null || true' INT TERM
while kill -0 "$fuzz_pid" 2>/dev/null; do
  state=$(ps -p "$fuzz_pid" -o stat= 2>/dev/null || true)
  if [[ -z "$state" || "$state" == Z* ]]; then break; fi
  now=$(date +%s)
  if [[ -z "$active_start" && -f "$OUTDIR/fuzzer_stats" ]]; then
    active_start=$now; printf '%s\n' "$active_start" >"$OUTDIR/campaign-active-started"
  elif [[ -n "$active_start" ]] && (( now - active_start >= DURATION )); then
    printf '%s\n' "$now" >"$OUTDIR/campaign-active-stopped"
    kill -INT -- "-"$fuzz_pid 2>/dev/null || true; break
  elif [[ -z "$active_start" ]] && (( now - wall_start >= 600 )); then
    echo 'AFLNet did not initialize within 600 seconds' >&2
    kill -TERM -- "-"$fuzz_pid 2>/dev/null || true; break
  fi
  sleep 2
done
for _ in $(seq 1 20); do
  state=$(ps -p "$fuzz_pid" -o stat= 2>/dev/null || true)
  if [[ -z "$state" || "$state" == Z* ]]; then break; fi
  sleep 1
done
state=$(ps -p "$fuzz_pid" -o stat= 2>/dev/null || true)
if [[ -n "$state" && "$state" != Z* ]]; then kill -TERM -- "-"$fuzz_pid 2>/dev/null || true; fi
for _ in $(seq 1 10); do
  state=$(ps -p "$fuzz_pid" -o stat= 2>/dev/null || true)
  if [[ -z "$state" || "$state" == Z* ]]; then break; fi
  sleep 1
done
state=$(ps -p "$fuzz_pid" -o stat= 2>/dev/null || true)
if [[ -n "$state" && "$state" != Z* ]]; then kill -KILL -- "-"$fuzz_pid 2>/dev/null || true; fi
set +e
wait "$fuzz_pid"; status=$?
set -e
wall_seconds=$(( $(date +%s) - wall_start )); active_seconds=0
if [[ -f "$OUTDIR/campaign-active-started" ]]; then
  active_start=$(cat "$OUTDIR/campaign-active-started"); active_end=$(date +%s)
  [[ ! -f "$OUTDIR/campaign-active-stopped" ]] || active_end=$(cat "$OUTDIR/campaign-active-stopped")
  active_seconds=$((active_end-active_start))
fi
printf 'exit_status=%s\nwall_seconds=%s\nactive_seconds=%s\nrequested_active_seconds=%s\n' "$status" "$wall_seconds" "$active_seconds" "$DURATION" | tee "$OUTDIR/run-status.txt"
[[ -f "$OUTDIR/fuzzer_stats" ]] || { cat "$OUTDIR/campaign.log"; exit 1; }
grep -E '^(start_time|last_update|execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' "$OUTDIR/fuzzer_stats" >"$OUTDIR/fuzzer-summary.txt" || true
cp "$PARAMS" "$OUTDIR/run-parameters.txt"
if ((active_seconds<DURATION)); then echo 'active run shorter than requested duration' >&2; exit 1; fi
[[ $status -eq 124 || $status -eq 130 || $status -eq 0 ]]
