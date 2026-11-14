#!/usr/bin/env bash
set -Eeuo pipefail
for _ in $(seq 1 120); do
  if ( exec 3<>/dev/tcp/127.0.0.1/1830 ) >/dev/null 2>&1; then exit 0; fi
  sleep .5
done
echo 'NETCONF proxy TCP port 1830 is not ready' >&2
cat /tmp/netopeer2-server.log /tmp/netconf-proxy.log 2>/dev/null || true
exit 1
