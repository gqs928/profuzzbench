#!/usr/bin/env bash
set -Eeuo pipefail
port_open() { ( exec 3<>/dev/tcp/127.0.0.1/61613 ) >/dev/null 2>&1; }
if ! port_open; then
  if [[ ! -f /tmp/artemis-stomp.pid ]] || ! kill -0 "$(cat /tmp/artemis-stomp.pid)" 2>/dev/null; then
    nohup /opt/benchmark/server-foreground.sh >>/tmp/artemis-stomp.log 2>&1 </dev/null &
    echo "$!" >/tmp/artemis-stomp.pid
  fi
  ready=0
  for _ in $(seq 1 120); do
    if port_open; then ready=1; break; fi
    sleep .5
  done
  [[ $ready == 1 ]] || { cat /tmp/artemis-stomp.log >&2; exit 1; }
fi
exit 0
