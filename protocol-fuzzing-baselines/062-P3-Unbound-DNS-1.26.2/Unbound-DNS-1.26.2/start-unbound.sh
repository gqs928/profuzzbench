#!/usr/bin/env bash
set -euo pipefail
UNBOUND_PORT=${UNBOUND_PORT:-5300}
PID_FILE=${PID_FILE:-/tmp/unbound-target.pid}
LOG_FILE=${UNBOUND_LOG_FILE:-/results/unbound.log}
mkdir -p "$(dirname "$LOG_FILE")"
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Unbound already running: pid=$(cat "$PID_FILE")"
  exit 0
fi
/opt/unbound/sbin/unbound -V | grep -Fq 'Version 1.26.2' || {
  echo "Unbound runtime version assertion failed" >&2; exit 2;
}
nohup /opt/unbound/sbin/unbound -d -c /opt/benchmark/unbound.conf -vv \
  >>"$LOG_FILE" 2>&1 &
pid=$!
echo "$pid" > "$PID_FILE"
if ! python3 /opt/benchmark/unbound_probe.py --port "$UNBOUND_PORT" --deadline 25; then
  echo "Unbound failed protocol readiness; recent log:" >&2
  tail -80 "$LOG_FILE" >&2 || true
  kill -TERM "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  exit 1
fi
echo "Unbound ready: pid=$pid port=$UNBOUND_PORT"
