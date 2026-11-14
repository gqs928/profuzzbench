#!/usr/bin/env bash
set -Eeuo pipefail
ready=0
for _ in $(seq 1 120); do
  if ( exec 3<>/dev/tcp/127.0.0.1/10389 ) >/dev/null 2>&1; then ready=1; break; fi
  sleep .5
done
[[ $ready == 1 ]] || { echo 'ApacheDS LDAP port 10389 is not ready' >&2; exit 1; }
exit 0
