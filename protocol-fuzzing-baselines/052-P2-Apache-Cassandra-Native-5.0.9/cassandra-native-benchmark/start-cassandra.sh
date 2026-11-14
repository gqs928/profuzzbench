#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT=${CASSANDRA_DATA_ROOT:-/var/lib/cassandra}
PID_FILE=${CASSANDRA_PID_FILE:-/run/cassandra-native-bench.pid}
LOG_FILE=${CASSANDRA_LOG_FILE:-/results/cassandra-node.log}
LIFECYCLE_LOG=${CASSANDRA_LIFECYCLE_LOG:-/results/cassandra-lifecycle.tsv}
READY_TIMEOUT=${CASSANDRA_READY_TIMEOUT:-300}
EXPECTED_VERSION=${CASSANDRA_EXPECTED_VERSION:-5.0.9}

mkdir -p "$(dirname "$PID_FILE")" "$(dirname "$LOG_FILE")" "$(dirname "$LIFECYCLE_LOG")"

record() {
  printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$LIFECYCLE_LOG"
}

process_running() {
  local pid=$1 stat
  kill -0 "$pid" 2>/dev/null || return 1
  stat=$(ps -o stat= -p "$pid" 2>/dev/null || true)
  [[ -n "$stat" && "$stat" != Z* ]]
}

ready() {
  local result
  result=$(cqlsh 127.0.0.1 9042 --protocol-version=4 --request-timeout=5 \
    -e "SELECT release_version FROM system.local" 2>/dev/null) || return 1
  grep -Fq "$EXPECTED_VERSION" <<< "$result"
}

wait_ready() {
  local pid=$1 deadline=$((SECONDS + READY_TIMEOUT))
  while (( SECONDS < deadline )); do
    if ! process_running "$pid"; then
      record "server-exited-before-ready pid=$pid"
      return 1
    fi
    if ready; then
      record "server-ready pid=$pid version=$EXPECTED_VERSION"
      return 0
    fi
    sleep 1
  done
  record "server-ready-timeout pid=$pid seconds=$READY_TIMEOUT"
  return 1
}

if ready; then
  record "server-already-ready version=$EXPECTED_VERSION"
  exit 0
fi

if [[ -f "$PID_FILE" ]]; then
  existing_pid=$(cat "$PID_FILE")
  if [[ "$existing_pid" =~ ^[0-9]+$ ]] && process_running "$existing_pid"; then
    if wait_ready "$existing_pid"; then exit 0; fi
    kill -TERM "$existing_pid" 2>/dev/null || true
    for _ in {1..30}; do
      process_running "$existing_pid" || break
      sleep 1
    done
    kill -KILL "$existing_pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
fi

for name in data commitlog saved_caches hints; do
  rm -rf "${DATA_ROOT:?}/${name}"
  mkdir -p "${DATA_ROOT}/${name}"
done
chown -R cassandra:cassandra "$DATA_ROOT"
: > "$LOG_FILE"

setsid /usr/local/bin/docker-entrypoint.sh cassandra -f \
  >> "$LOG_FILE" 2>&1 < /dev/null &
server_pid=$!
printf '%s\n' "$server_pid" > "$PID_FILE"
record "server-started pid=$server_pid version=$EXPECTED_VERSION"

if ! wait_ready "$server_pid"; then
  tail -80 "$LOG_FILE" >&2 || true
  exit 1
fi
