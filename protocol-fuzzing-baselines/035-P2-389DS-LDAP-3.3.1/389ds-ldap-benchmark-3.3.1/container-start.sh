#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG_DIR=/etc/dirsrv/slapd-benchmark
if [[ ! -f "$CONFIG_DIR/dse.ldif" ]]; then
  dscreate from-file /opt/benchmark/instance.inf
fi

dsctl benchmark status >/dev/null 2>&1 || dsctl benchmark start
for _ in $(seq 1 120); do
  if ( exec 3<>/dev/tcp/127.0.0.1/3389 ) >/dev/null 2>&1; then break; fi
  sleep .5
done
if ! ( exec 3<>/dev/tcp/127.0.0.1/3389 ) >/dev/null 2>&1; then
  echo '389 DS LDAP port 3389 did not become ready' >&2
  exit 1
fi

while dsctl benchmark status >/dev/null 2>&1; do sleep 1; done
echo '389 DS instance benchmark stopped unexpectedly' >&2
exit 1
