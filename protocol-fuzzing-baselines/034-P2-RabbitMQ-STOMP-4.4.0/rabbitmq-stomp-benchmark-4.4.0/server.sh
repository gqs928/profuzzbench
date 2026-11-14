#!/usr/bin/env bash
set -Eeuo pipefail
port_open() { ( exec 3<>/dev/tcp/127.0.0.1/61613 ) >/dev/null 2>&1; }
for _ in $(seq 1 120); do
  if port_open; then exit 0; fi
  sleep .5
done
cat /tmp/rabbitmq/server.log >&2
exit 1
