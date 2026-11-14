#!/usr/bin/env bash
set -euo pipefail
/bin/bash /opt/benchmark/stop-pdns.sh
rm -f /tmp/pdns-cache/* 2>/dev/null || true
/bin/bash /opt/benchmark/start-pdns.sh
