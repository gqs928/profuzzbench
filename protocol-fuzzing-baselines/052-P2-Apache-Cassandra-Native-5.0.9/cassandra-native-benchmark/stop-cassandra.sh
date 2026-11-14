#!/usr/bin/env bash
set -euo pipefail

PID_FILE=${CASSANDRA_PID_FILE:-/run/cassandra-native-bench.pid}
LOG_FILE=${CASSANDRA_LIFECYCLE_LOG:-/results/cassandra-lifecycle.tsv}
mkdir -p "$(dirname "$LOG_FILE")"

process_running() {
  local pid=$1 stat
  kill -0 "$pid" 2>/dev/null || return 1
  stat=$(ps -o stat= -p "$pid" 2>/dev/null || true)
  [[ -n "$stat" && "$stat" != Z* ]]
}

if [[ ! -f "$PID_FILE" ]]; then
  printf '%s\t%s\n' "$(date -u +%FT%TZ)" "stop-skipped=no-owned-pid" >> "$LOG_FILE"
  exit 0
fi

pid=$(cat "$PID_FILE")
if [[ ! "$pid" =~ ^[0-9]+$ ]] || ! process_running "$pid"; then
  rm -f "$PID_FILE"
  printf '%s\t%s\n' "$(date -u +%FT%TZ)" "stop-skipped=process-not-running pid=$pid" >> "$LOG_FILE"
  exit 0
fi

kill -TERM "$pid"
for _ in {1..60}; do
  process_running "$pid" || break
  sleep 1
done
if process_running "$pid"; then
  kill -KILL "$pid"
  for _ in {1..10}; do
    process_running "$pid" || break
    sleep 1
  done
fi
rm -f "$PID_FILE"
printf '%s\t%s\n' "$(date -u +%FT%TZ)" "server-stopped pid=$pid" >> "$LOG_FILE"
