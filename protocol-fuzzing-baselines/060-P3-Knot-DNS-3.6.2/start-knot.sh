#!/usr/bin/env bash
set -euo pipefail
KNOT_PORT=${KNOT_PORT:-5300}
PID_FILE=${PID_FILE:-/tmp/knot-target.pid}
LOG_FILE=${KNOT_LOG_FILE:-/results/knotd.log}
mkdir -p /tmp/knot-rundir /tmp/knot-storage "$(dirname "$LOG_FILE")"
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "knotd already running: pid=$(cat "$PID_FILE")"
  exit 0
fi
knotd -V | grep -Fq '3.6.2' || { echo "Knot DNS 3.6.2 assertion failed" >&2; exit 2; }
nohup knotd -c /opt/benchmark/knot.conf >>"$LOG_FILE" 2>&1 &
pid=$!
echo "$pid" > "$PID_FILE"
if ! python3 /opt/benchmark/knot_probe.py --port "$KNOT_PORT" --deadline 25; then
  echo "knotd failed protocol readiness; recent log:" >&2
  tail -80 "$LOG_FILE" >&2 || true
  kill -TERM "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  exit 1
fi
echo "knotd ready: pid=$pid port=$KNOT_PORT"
