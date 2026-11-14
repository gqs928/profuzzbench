#!/usr/bin/env bash
set -euo pipefail

BASE_DIR=${YUGABYTE_BASE_DIR:-/tmp/yugabyte-native-bench}
PID_FILE=${YUGABYTE_PID_FILE:-/tmp/yugabyte-native-bench.pid}
LOG_FILE=${YUGABYTE_LOG_FILE:-/results/yugabyte-node.log}
LIFECYCLE_LOG=${YUGABYTE_LIFECYCLE_LOG:-/results/yugabyte-lifecycle.tsv}
YUGABYTED=/home/yugabyte/bin/yugabyted
mkdir -p "$(dirname "$LIFECYCLE_LOG")" "$(dirname "$LOG_FILE")"
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
    timeout 90s runuser -u yugabyte -- "$YUGABYTED" stop --base_dir="$BASE_DIR" \
      >> "$LOG_FILE" 2>&1 || record "graceful-stop-command-failed pid=$pid"
    for _ in {1..60}; do process_running "$pid" || break; sleep 1; done
    if process_running "$pid"; then
      record "graceful-stop-timeout pid=$pid"
      kill -TERM "$pid" 2>/dev/null || true
      for _ in {1..10}; do process_running "$pid" || break; sleep 1; done
      kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$PID_FILE"
fi
record 'server-stopped'
