#!/usr/bin/env bash
set -euo pipefail

WORKDIR=${WORKDIR:-/opt/benchmark}
BASE_DIR=${YUGABYTE_BASE_DIR:-/tmp/yugabyte-native-bench}
PID_FILE=${YUGABYTE_PID_FILE:-/tmp/yugabyte-native-bench.pid}
LOG_FILE=${YUGABYTE_LOG_FILE:-/results/yugabyte-node.log}
LIFECYCLE_LOG=${YUGABYTE_LIFECYCLE_LOG:-/results/yugabyte-lifecycle.tsv}
EXPECTED_VERSION=${YUGABYTE_EXPECTED_VERSION:-2026.1.3.0}
EXPECTED_BUILD=${YUGABYTE_EXPECTED_BUILD:-100}
YCQL_PORT=${YCQL_PORT:-9042}
YCQL_HOST=${YCQL_HOST:-$(hostname -i | awk '{print $1}')}
READY_TIMEOUT=${YUGABYTE_READY_TIMEOUT:-360}
YCQLSH=/home/yugabyte/bin/ycqlsh
YB_SERVER=/home/yugabyte/bin/yb-server
YUGABYTED=/home/yugabyte/bin/yugabyted

mkdir -p "$(dirname "$PID_FILE")" "$(dirname "$LOG_FILE")" "$(dirname "$LIFECYCLE_LOG")" "$BASE_DIR"
chown -R yugabyte:users "$BASE_DIR"
record() { printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$LIFECYCLE_LOG"; }
product_version() { "$YB_SERVER" --version 2>&1 | head -1; }
process_running() {
  local pid=$1 state
  [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null || return 1
  state=$(ps -o stat= -p "$pid" 2>/dev/null || true)
  [[ -n "$state" && "$state" != Z* ]]
}
ready() {
  local version result
  version=$(product_version) || return 1
  [[ "$version" == *"version ${EXPECTED_VERSION} build ${EXPECTED_BUILD}"* ]] || return 1
  result=$(timeout 15s "$YCQLSH" "$YCQL_HOST" "$YCQL_PORT" --request-timeout=10 \
    -e 'SELECT cluster_name FROM system.local' 2>/dev/null) || return 1
  grep -Eq '\([0-9]+ rows?\)' <<< "$result"
}
wait_ready() {
  local pid=$1 deadline=$((SECONDS + READY_TIMEOUT))
  while (( SECONDS < deadline )); do
    if ! process_running "$pid"; then
      record "yugabyted-entrypoint-exited-before-ready pid=$pid"
      return 1
    fi
    if ready; then
      record "server-ready pid=$pid host=$YCQL_HOST port=$YCQL_PORT product_version=$(product_version)"
      return 0
    fi
    sleep 2
  done
  record "server-ready-timeout pid=$pid seconds=$READY_TIMEOUT host=$YCQL_HOST"
  return 1
}

if ready; then
  record "server-already-ready product_version=$(product_version) host=$YCQL_HOST"
  exit 0
fi

if [[ -f "$PID_FILE" ]]; then
  existing_pid=$(cat "$PID_FILE")
  if [[ "$existing_pid" =~ ^[0-9]+$ ]] && process_running "$existing_pid"; then
    runuser -u yugabyte -- "$YUGABYTED" stop --base_dir="$BASE_DIR" \
      >> "$LOG_FILE" 2>&1 || true
    for _ in {1..30}; do process_running "$existing_pid" || break; sleep 1; done
    kill -TERM "$existing_pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
fi

: > "$LOG_FILE"
runuser -u yugabyte -- env HOME=/home/yugabyte \
  "$YUGABYTED" start --background=false --insecure --ui=false --base_dir="$BASE_DIR" \
  >> "$LOG_FILE" 2>&1 < /dev/null &
server_pid=$!
printf '%s\n' "$server_pid" > "$PID_FILE"
record "server-started pid=$server_pid expected_version=${EXPECTED_VERSION} expected_build=${EXPECTED_BUILD} host=$YCQL_HOST port=$YCQL_PORT"
if ! wait_ready "$server_pid"; then
  tail -80 "$LOG_FILE" >&2 || true
  exit 1
fi
