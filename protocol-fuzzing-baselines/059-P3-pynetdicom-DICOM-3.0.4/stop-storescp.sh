#!/usr/bin/env bash
set -u
PID_FILE=${PID_FILE:-/tmp/storescp.pid}
[[ -f "$PID_FILE" ]] || exit 0
pid=$(cat "$PID_FILE")
if kill -0 "$pid" 2>/dev/null; then
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 100); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.1
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL "$pid" 2>/dev/null || true
  fi
fi
rm -f "$PID_FILE"
