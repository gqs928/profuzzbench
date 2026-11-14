#!/usr/bin/env bash
set -euo pipefail
BGPD_PID_FILE=${BGPD_PID_FILE:-/tmp/frr-benchmark-bgpd.pid}
BGPD_VTY_DIR=${BGPD_VTY_DIR:-/tmp/frr-benchmark-bgpd.vty}
if [[ ! -f "$BGPD_PID_FILE" ]]; then exit 0; fi
pid=$(cat "$BGPD_PID_FILE")
if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 50); do
    if ! kill -0 "$pid" 2>/dev/null; then break; fi
    sleep 0.1
  done
  if kill -0 "$pid" 2>/dev/null; then kill -KILL "$pid" 2>/dev/null || true; fi
fi
rm -f "$BGPD_PID_FILE"
rm -rf "$BGPD_VTY_DIR" "$BGPD_VTY_DIR".*
echo "bgpd stopped"
