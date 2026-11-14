#!/usr/bin/env bash
set -euo pipefail
PDNS_PORT=${PDNS_PORT:-5300}
PID_FILE=${PID_FILE:-/tmp/pdns-target.pid}
LOG_FILE=${PDNS_LOG_FILE:-/results/pdns-recursor.log}
mkdir -p /run/pdns-benchmark "$(dirname "$LOG_FILE")"
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "PowerDNS Recursor already running: pid=$(cat "$PID_FILE")"
  exit 0
fi
[[ $(dpkg-query -W -f='${Version}' pdns-recursor) == 5.4.9-1pdns.ubuntu24.04 ]] || {
  echo "PowerDNS Recursor package version assertion failed" >&2; exit 2;
}
pdns_recursor --version | grep -Fq '5.4.9' || {
  echo "PowerDNS Recursor runtime version assertion failed" >&2; exit 2;
}
nohup pdns_recursor --config-dir=/opt/benchmark --daemon=no \
  >>"$LOG_FILE" 2>&1 &
pid=$!
echo "$pid" > "$PID_FILE"
if ! python3 /opt/benchmark/recursor_probe.py --port "$PDNS_PORT" --deadline 25; then
  echo "PowerDNS Recursor failed protocol readiness; recent log:" >&2
  tail -80 "$LOG_FILE" >&2 || true
  kill -TERM "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  exit 1
fi
echo "PowerDNS Recursor ready: pid=$pid port=$PDNS_PORT"
