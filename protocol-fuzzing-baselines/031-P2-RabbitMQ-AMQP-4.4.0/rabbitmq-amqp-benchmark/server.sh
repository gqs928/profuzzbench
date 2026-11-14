#!/usr/bin/env bash
set -Eeuo pipefail
count_file=/tmp/amqp-aflnet-target-count
count=0
if [[ -f "$count_file" ]]; then count=$(cat "$count_file"); fi
count=$((count + 1))
printf '%s\n' "$count" >"$count_file.tmp"
mv "$count_file.tmp" "$count_file"
if python3 - <<'PY'
import socket
s=socket.socket(); s.settimeout(.2)
try: raise SystemExit(0 if s.connect_ex(("127.0.0.1",5672)) == 0 else 1)
finally: s.close()
PY
then exit 0; fi
if [[ -f /tmp/amqp-broker.pid ]] && kill -0 "$(cat /tmp/amqp-broker.pid)" 2>/dev/null; then exit 0; fi
nohup /opt/benchmark/server-foreground.sh >/tmp/amqp-broker.log 2>&1 </dev/null &
echo "$!" >/tmp/amqp-broker.pid
exit 0
