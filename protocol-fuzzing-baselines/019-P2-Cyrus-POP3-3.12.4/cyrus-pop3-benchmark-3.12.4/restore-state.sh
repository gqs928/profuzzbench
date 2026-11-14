#!/usr/bin/env bash
set -euo pipefail

STATE_ARCHIVE=${CYRUS_SEED_STATE:-/home/ubuntu/experiments/pop3-seed-state.tar.gz}
/workspace/reset-state.sh
test -s "$STATE_ARCHIVE" || { echo "Missing Cyrus POP3 mailbox snapshot: $STATE_ARCHIVE" >&2; exit 2; }
tar -xzf "$STATE_ARCHIVE" -C /tmp
mkdir -p /tmp/cyrus-benchmark-state/{config/socket,proc,lock,mail,sieve,saslauthd}
find /tmp/cyrus-benchmark-state -type s -delete
chown -R ubuntu:ubuntu /tmp/cyrus-benchmark-state
