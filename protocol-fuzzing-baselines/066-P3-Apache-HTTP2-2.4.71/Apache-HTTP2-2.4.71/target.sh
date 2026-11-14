#!/usr/bin/env bash
set -euo pipefail
rm -f /tmp/httpd-benchmark.pid /tmp/httpd-benchmark.pid.lock
exec /opt/httpd/bin/httpd -f /opt/benchmark/httpd.conf -DFOREGROUND -X
