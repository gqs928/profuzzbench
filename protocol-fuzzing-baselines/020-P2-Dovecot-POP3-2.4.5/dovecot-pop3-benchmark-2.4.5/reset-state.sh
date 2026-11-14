#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then
  echo "Dovecot state reset must run as container root" >&2
  exit 2
fi
prefix=${DOVECOT_AFL_PREFIX:-/home/ubuntu/experiments/dovecot-afl}
export LD_LIBRARY_PATH="${prefix}/lib"
"${prefix}/sbin/dovecot" -c /workspace/dovecot.conf stop >/dev/null 2>&1 || true
rm -rf /tmp/dovecot-pop3-benchmark-state
mkdir -p /tmp/dovecot-pop3-benchmark-state/{run,state,log,mail}
chown -R ubuntu:ubuntu /tmp/dovecot-pop3-benchmark-state
runuser -u ubuntu -- python3 /workspace/prepare_maildir.py
