#!/usr/bin/env bash
set -euo pipefail

# Benchmark daemons run only inside the isolated benchmark container.
for name in pop3d imapd master saslauthd; do
  pkill -x "$name" 2>/dev/null || true
done
sleep 0.1
rm -rf /tmp/cyrus-benchmark-state
mkdir -p /tmp/cyrus-benchmark-state/{config/socket,proc,lock,mail,sieve,saslauthd}
