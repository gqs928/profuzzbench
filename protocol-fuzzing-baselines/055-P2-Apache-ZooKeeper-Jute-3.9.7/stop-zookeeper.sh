#!/usr/bin/env bash
set -euo pipefail

PID_FILE=${ZK_PID_FILE:-/tmp/zookeeper-native-bench.pid}
LIFECYCLE_LOG=${ZK_LIFECYCLE_LOG:-/results/zookeeper-lifecycle.tsv}
mkdir -p "$(dirname "$LIFECYCLE_LOG")"
record() { printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$LIFECYCLE_LOG"; }
process_running() {
  local pid=$1 state
  [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null || return 1
  state=$(ps -o stat= -p "$pid" 2>/dev/null || true)
  [[ -n "$state" && "$state" != Z* ]]
}

if [[ -f "$PID_FILE" ]]; then
  pid=$(cat "$PID_FILE")
  if [[ "$pid" =~ ^[0-9]+$ ]] && process_running "$pid"; then
    kill -TERM "$pid" 2>/dev/null || true
    for _ in {1..30}; do process_running "$pid" || break; sleep 1; done
    if process_running "$pid"; then
      record "graceful-stop-timeout pid=$pid"
      kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$PID_FILE"
fi
record 'server-stopped'
