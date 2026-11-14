#!/usr/bin/env bash
set -euo pipefail
PID_FILE=${PID_FILE:-/tmp/unbound-target.pid}
if [[ ! -f "$PID_FILE" ]]; then
  exit 0
fi
pid=$(cat "$PID_FILE")
kill -TERM "$pid" 2>/dev/null || true
for _ in $(seq 1 100); do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$PID_FILE"
    exit 0
  fi
  sleep 0.1
done
kill -KILL "$pid" 2>/dev/null || true
rm -f "$PID_FILE"
