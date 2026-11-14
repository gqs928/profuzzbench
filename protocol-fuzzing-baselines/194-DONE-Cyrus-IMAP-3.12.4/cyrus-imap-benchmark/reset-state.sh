#!/usr/bin/env bash
set -euo pipefail

# Called by the launcher before it starts a fresh Cyrus master for this input.
pkill -TERM -x imapd 2>/dev/null || true
pkill -TERM -x saslauthd 2>/dev/null || true
sleep 0.05
rm -rf /tmp/cyrus-benchmark-state
