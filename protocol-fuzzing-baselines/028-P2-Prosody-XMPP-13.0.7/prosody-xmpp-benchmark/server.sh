#!/usr/bin/env bash
set -Eeuo pipefail
export HOME=/tmp/prosody-home
export PROSODY_SRCDIR=/opt/prosody
export PROSODY_CFGDIR=/opt/benchmark/configs
export PROSODY_PLUGINDIR=/opt/prosody/plugins
export PROSODY_DATADIR=/tmp/prosody-data
mkdir -p "$HOME" "$PROSODY_DATADIR"
count_file=/tmp/prosody-aflnet-target-count
count=0
if [[ -f "$count_file" ]]; then count=$(cat "$count_file"); fi
count=$((count + 1))
printf '%s\n' "$count" >"$count_file.tmp"
mv "$count_file.tmp" "$count_file"
seed_count=$(find /opt/benchmark/seeds -maxdepth 1 -type f | wc -l)
if (( count > seed_count )); then touch /tmp/prosody-aflnet-fuzz-active; fi
if python3 - <<'PY'
import socket
s=socket.socket(); s.settimeout(.2)
try: raise SystemExit(0 if s.connect_ex(("127.0.0.1",5222)) == 0 else 1)
finally: s.close()
PY
then exit 0; fi
if [[ -f /tmp/prosody.pid ]] && kill -0 "$(cat /tmp/prosody.pid)" 2>/dev/null; then exit 0; fi
cd "$PROSODY_SRCDIR"
nohup /opt/benchmark/server-foreground.sh >/tmp/prosody-server.log 2>&1 </dev/null &
echo "$!" >/tmp/prosody.pid
exit 0
