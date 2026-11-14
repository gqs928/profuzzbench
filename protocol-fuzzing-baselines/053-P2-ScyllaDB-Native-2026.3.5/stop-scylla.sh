#!/usr/bin/env bash
set -euo pipefail
PID_FILE=${SCYLLA_PID_FILE:-/tmp/scylla-native-bench.pid}
LIFECYCLE_LOG=${SCYLLA_LIFECYCLE_LOG:-/results/scylla-lifecycle.tsv}
mkdir -p "$(dirname "$LIFECYCLE_LOG")"
record() { printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$LIFECYCLE_LOG"; }
process_running() {
 local pid=$1 proc_stat state
 [[ "$pid" =~ ^[0-9]+$ && -r "/proc/$pid/stat" ]] || return 1
 IFS= read -r proc_stat < "/proc/$pid/stat" || return 1
 proc_stat=${proc_stat##*) }
 state=${proc_stat%% *}
 [[ "$state" != Z ]]
}
if [[ -f "$PID_FILE" ]]; then
 pid=$(cat "$PID_FILE")
 if [[ "$pid" =~ ^[0-9]+$ ]] && process_running "$pid"; then
  kill -TERM "$pid" 2>/dev/null || true
  for _ in {1..60}; do process_running "$pid" || break; sleep 1; done
  if process_running "$pid"; then record "stop-timeout pid=$pid"; kill -KILL "$pid" 2>/dev/null || true; fi
 fi
 rm -f "$PID_FILE"
fi
record 'server-stopped'
