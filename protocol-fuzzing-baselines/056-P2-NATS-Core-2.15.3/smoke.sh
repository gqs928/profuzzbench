#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:?usage: smoke.sh OUTDIR [REPETITIONS]}
REPETITIONS=${2:-3}
HOST=${NATS_HOST:-127.0.0.1}
PORT=${NATS_PORT:-4222}
LOG_FILE=${OUTDIR}.server.log
mkdir -p "$(dirname "$OUTDIR")"
[[ ! -e "$OUTDIR" || -z $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit) ]] || {
  echo "smoke output directory must be empty: $OUTDIR" >&2
  exit 2
}
/usr/local/bin/nats-server --addr "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
SERVER_PID=$!
stop_server() {
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" || true
  fi
}
trap stop_server EXIT
ready=no
for _ in {1..80}; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    cat "$LOG_FILE" >&2
    exit 1
  fi
  if NATS_HOST="$HOST" NATS_PORT="$PORT" python3 /opt/benchmark/nats_client.py check "$HOST" "$PORT" >/dev/null 2>&1; then
    ready=yes
    break
  fi
  sleep 0.1
done
[[ "$ready" == yes ]] || { cat "$LOG_FILE" >&2; echo "NATS readiness timeout" >&2; exit 1; }
NATS_HOST="$HOST" NATS_PORT="$PORT" python3 /opt/benchmark/protocol_smoke.py "$OUTDIR" "$REPETITIONS"
stop_server
SERVER_PID=0
closed=$(python3 -c 'import socket,sys; s=socket.socket(); s.settimeout(.25); r=s.connect_ex((sys.argv[1], int(sys.argv[2]))); s.close(); print("closed" if r else "open"); sys.exit(0 if r else 1)' "$HOST" "$PORT")
python3 - "$OUTDIR/listener-closed.json" "$closed" <<'PY'
import json, sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({"listener_state": sys.argv[2]}, indent=2) + "\n")
PY
trap - EXIT
echo "PASS: NATS stopped; listener state=${closed}"
