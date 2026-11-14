#!/usr/bin/env bash
set -euo pipefail

WORKDIR=${WORKDIR:-/opt/benchmark}
ZK_HOME=${ZK_HOME:-/apache-zookeeper-3.9.7-bin}
CONF_DIR=${ZK_CONF_DIR:-${WORKDIR}/conf}
DATA_DIR=${ZK_DATA_DIR:-/tmp/zookeeper-native-bench-data}
DATA_LOG_DIR=${ZK_DATA_LOG_DIR:-/tmp/zookeeper-native-bench-datalog}
PID_FILE=${ZK_PID_FILE:-/tmp/zookeeper-native-bench.pid}
LOG_DIR=${ZK_LOG_DIR:-/results/zookeeper-logs}
LOG_FILE=${ZK_LOG_FILE:-${LOG_DIR}/zookeeper-server.log}
LIFECYCLE_LOG=${ZK_LIFECYCLE_LOG:-/results/zookeeper-lifecycle.tsv}
VERSION_FILE=${ZK_VERSION_FILE:-/results/zookeeper-version.txt}
EXPECTED_VERSION=${ZK_EXPECTED_VERSION:-3.9.7}
ZK_HOST=${ZK_HOST:-$(hostname -i | awk '{print $1}')}
ZK_PORT=${ZK_PORT:-2181}
ZK_SERVER=${ZK_HOME}/bin/zkServer.sh

mkdir -p "$(dirname "$PID_FILE")" "$(dirname "$LIFECYCLE_LOG")" "$LOG_DIR"
export ZOO_CONF_DIR="$CONF_DIR" ZOOCFGDIR="$CONF_DIR"
export ZOO_DATA_DIR="$DATA_DIR" ZOO_DATA_LOG_DIR="$DATA_LOG_DIR" ZOO_LOG_DIR="$LOG_DIR"
record() { printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$LIFECYCLE_LOG"; }
process_running() {
  local pid=$1 state
  [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null || return 1
  state=$(ps -o stat= -p "$pid" 2>/dev/null || true)
  [[ -n "$state" && "$state" != Z* ]]
}
ready() {
  python3 "${WORKDIR}/zookeeper_client.py" check "$ZK_HOST" "$ZK_PORT" >/dev/null 2>&1
}

if [[ -f "$PID_FILE" ]]; then
  existing_pid=$(cat "$PID_FILE")
  if [[ "$existing_pid" =~ ^[0-9]+$ ]] && process_running "$existing_pid"; then
    /bin/bash "${WORKDIR}/stop-zookeeper.sh"
  fi
  rm -f "$PID_FILE"
fi

rm -rf "$DATA_DIR"
rm -rf "$DATA_LOG_DIR"
mkdir -p "$DATA_DIR" "$DATA_LOG_DIR"
: > "$LOG_FILE"
version_output=$("$ZK_SERVER" --config "$CONF_DIR" version 2>&1)
grep -Fq "$EXPECTED_VERSION" <<< "$version_output" || {
  record "version-mismatch expected=$EXPECTED_VERSION output=${version_output//$'\n'/ }"
  printf '%s\n' "$version_output" >&2
  exit 1
}
if [[ ! -f "$VERSION_FILE" ]]; then
  printf '%s\n' "$version_output" > "$VERSION_FILE"
fi

/docker-entrypoint.sh zkServer.sh --config "$CONF_DIR" start-foreground \
  >> "$LOG_FILE" 2>&1 < /dev/null &
server_pid=$!
printf '%s\n' "$server_pid" > "$PID_FILE"
record "server-started pid=$server_pid version=$EXPECTED_VERSION host=$ZK_HOST port=$ZK_PORT"
deadline=$((SECONDS + ${ZK_READY_TIMEOUT:-120}))
while (( SECONDS < deadline )); do
  if ! process_running "$server_pid"; then
    record "server-exited-before-ready pid=$server_pid"
    tail -60 "$LOG_FILE" >&2 || true
    exit 1
  fi
  if ready; then
    record "server-ready pid=$server_pid version=$EXPECTED_VERSION host=$ZK_HOST port=$ZK_PORT"
    exit 0
  fi
  sleep 1
done
record "server-ready-timeout pid=$server_pid seconds=${ZK_READY_TIMEOUT:-120}"
tail -60 "$LOG_FILE" >&2 || true
exit 1
