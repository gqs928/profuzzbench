#!/usr/bin/env bash
set -euo pipefail
DATA_ROOT=${SCYLLA_DATA_ROOT:-/var/lib/scylla}
PID_FILE=${SCYLLA_PID_FILE:-/tmp/scylla-native-bench.pid}
LOG_FILE=${SCYLLA_LOG_FILE:-/results/scylla-node.log}
LIFECYCLE_LOG=${SCYLLA_LIFECYCLE_LOG:-/results/scylla-lifecycle.tsv}
READY_TIMEOUT=${SCYLLA_READY_TIMEOUT:-300}
EXPECTED_VERSION=${SCYLLA_EXPECTED_VERSION:-2026.3.5}
EXPECTED_CQL_RELEASE=${SCYLLA_CQL_RELEASE_VERSION:-3.0.8}
SCYLLA_MEMORY=${SCYLLA_MEMORY:-1536M}
mkdir -p "$(dirname "$PID_FILE")" "$(dirname "$LOG_FILE")" "$(dirname "$LIFECYCLE_LOG")"
record() { printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$LIFECYCLE_LOG"; }
process_running() {
  local pid=$1 proc_stat state
  [[ "$pid" =~ ^[0-9]+$ && -r "/proc/$pid/stat" ]] || return 1
  IFS= read -r proc_stat < "/proc/$pid/stat" || return 1
  proc_stat=${proc_stat##*) }
  state=${proc_stat%% *}
  [[ "$state" != Z ]]
}
product_version() { /usr/bin/scylla --version 2>/dev/null | head -1; }
ready() {
  local result product
  product=$(product_version) || return 1
  [[ "$product" == "${EXPECTED_VERSION}"-* ]] || return 1
  result=$(timeout 20s cqlsh 127.0.0.1 9042 --protocol-version=4 --request-timeout=10 -e 'SELECT release_version FROM system.local' 2>/dev/null) || return 1
  grep -Eq "(^|[[:space:]])${EXPECTED_CQL_RELEASE//./\.}([[:space:]]|$)" <<< "$result"
}
wait_ready() {
  local pid=$1 deadline=$((SECONDS + READY_TIMEOUT))
  while (( SECONDS < deadline )); do
    if ! process_running "$pid"; then record "server-entrypoint-exited-before-ready pid=$pid"; return 1; fi
    if ready; then record "server-ready pid=$pid product_version=$(product_version) cql_release_version=$EXPECTED_CQL_RELEASE"; return 0; fi
    sleep 2
  done
  record "server-ready-timeout pid=$pid seconds=$READY_TIMEOUT"
  return 1
}
if ready; then record "server-already-ready product_version=$(product_version) cql_release_version=$EXPECTED_CQL_RELEASE"; exit 0; fi
if [[ -f "$PID_FILE" ]]; then
 existing_pid=$(cat "$PID_FILE")
 if [[ "$existing_pid" =~ ^[0-9]+$ ]] && process_running "$existing_pid"; then
  if wait_ready "$existing_pid"; then exit 0; fi
  kill -TERM "$existing_pid" 2>/dev/null || true
  for _ in {1..30}; do process_running "$existing_pid" || break; sleep 1; done
  kill -KILL "$existing_pid" 2>/dev/null || true
 fi
 rm -f "$PID_FILE"
fi
for name in data commitlog saved_caches hints; do rm -rf "${DATA_ROOT:?}/${name}"; mkdir -p "${DATA_ROOT}/${name}"; done
chown -R scylla:scylla "$DATA_ROOT"
: > "$LOG_FILE"
setsid /docker-entrypoint.py --smp 1 --memory "$SCYLLA_MEMORY" --overprovisioned 1 --developer-mode 1 \
  --listen-address 127.0.0.1 --rpc-address 127.0.0.1 --broadcast-address 127.0.0.1 --broadcast-rpc-address 127.0.0.1 \
  >> "$LOG_FILE" 2>&1 < /dev/null &
server_pid=$!
printf '%s\n' "$server_pid" > "$PID_FILE"
record "server-started pid=$server_pid product_version=$EXPECTED_VERSION configured_memory=$SCYLLA_MEMORY smp=1"
if ! wait_ready "$server_pid"; then tail -80 "$LOG_FILE" >&2 || true; exit 1; fi
