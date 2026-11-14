#!/usr/bin/env bash
set -euo pipefail
HTTPD=/opt/httpd/bin/httpd
CONF=/opt/benchmark/httpd.conf
PORT=${HTTPD_PORT:-20240}
if pgrep -x httpd >/dev/null 2>&1; then
  pkill -TERM -x httpd || true
  sleep 0.2
fi
rm -f /tmp/httpd-benchmark.pid /tmp/httpd-benchmark.pid.lock
"$HTTPD" -f "$CONF" -DFOREGROUND -X >/tmp/httpd-benchmark.log 2>&1 &
pid=$!
echo "$pid" >/tmp/httpd-benchmark-launch.pid
for _ in $(seq 1 100); do
  if ! kill -0 "$pid" 2>/dev/null; then
    cat /tmp/httpd-benchmark.log >&2
    exit 1
  fi
  if python3 - "$PORT" <<'PY' >/dev/null 2>&1
import socket, sys
s = socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=0.2)
s.close()
PY
  then
    echo "Apache h2c listener ready on 127.0.0.1:${PORT} (pid ${pid})"
    exit 0
  fi
  sleep 0.1
done
cat /tmp/httpd-benchmark.log >&2
exit 1
