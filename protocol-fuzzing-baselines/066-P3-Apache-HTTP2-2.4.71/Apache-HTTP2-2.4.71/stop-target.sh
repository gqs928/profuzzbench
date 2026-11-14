#!/usr/bin/env bash
set -euo pipefail
if [[ -f /tmp/httpd-benchmark-launch.pid ]]; then
  pid=$(cat /tmp/httpd-benchmark-launch.pid)
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 50); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.1
  done
fi
pkill -TERM -x httpd 2>/dev/null || true
rm -f /tmp/httpd-benchmark.pid /tmp/httpd-benchmark.pid.lock /tmp/httpd-benchmark-launch.pid
