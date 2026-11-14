#!/usr/bin/env bash
set -Eeuo pipefail
export HOME=/tmp/openfire-home
export OPENFIRE_HOME=/opt/openfire
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export OPENFIRE_OPTS="-Xms128m -Xmx768m -XX:+UseSerialGC"
mkdir -p "$HOME"
count_file=/tmp/openfire-aflnet-target-count
count=0
if [[ -f "$count_file" ]]; then count=$(cat "$count_file"); fi
count=$((count + 1))
printf '%s\n' "$count" >"$count_file.tmp"
mv "$count_file.tmp" "$count_file"
seed_count=$(find /opt/benchmark/seeds -maxdepth 1 -type f | wc -l)
if (( count > seed_count )); then touch /tmp/openfire-aflnet-fuzz-active; fi
if python3 - <<'PY'
import socket
s=socket.socket(); s.settimeout(.2)
try: raise SystemExit(0 if s.connect_ex(("127.0.0.1",5222)) == 0 else 1)
finally: s.close()
PY
then exit 0; fi
if [[ -f /tmp/openfire.pid ]] && kill -0 "$(cat /tmp/openfire.pid)" 2>/dev/null; then exit 0; fi
cd "$OPENFIRE_HOME"
nohup "$OPENFIRE_HOME/bin/openfire.sh" -demoboot >/tmp/openfire-server.log 2>&1 </dev/null &
echo "$!" >/tmp/openfire.pid
exit 0
