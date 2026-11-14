#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/dns-tcp-smoke-post-20261112-powerdns}
PDNS_PORT=${PDNS_PORT:-5300}
export PDNS_PORT PDNS_LOG_FILE="$OUTDIR/pdns-recursor.log"
mkdir -p "$OUTDIR"
/bin/bash /opt/benchmark/start-pdns.sh
trap '/bin/bash /opt/benchmark/stop-pdns.sh' EXIT
python3 /opt/benchmark/protocol_smoke.py --passes 3 \
  --output "$OUTDIR/protocol-smoke.json"
/bin/bash /opt/benchmark/stop-pdns.sh
trap - EXIT
python3 /opt/benchmark/verify_listener_closed.py --port "$PDNS_PORT" \
  --output "$OUTDIR/listener-closed.json"
chmod -R a+rX "$OUTDIR" 2>/dev/null || true
