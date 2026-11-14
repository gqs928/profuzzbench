#!/usr/bin/env bash
set -Eeuo pipefail
for _ in $(seq 1 120); do
  if ( exec 3<>/dev/tcp/127.0.0.1/3389 ) >/dev/null 2>&1; then exit 0; fi
  sleep .5
done
echo '389 DS LDAP port 3389 is not ready' >&2; exit 1
