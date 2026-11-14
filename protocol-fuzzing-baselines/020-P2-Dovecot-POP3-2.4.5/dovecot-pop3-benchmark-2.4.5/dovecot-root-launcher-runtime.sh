#!/usr/bin/env bash
set -euo pipefail
if (($# < 1 || $# > 2)); then
  echo "Expected variant and optional start/stop/reset action" >&2
  exit 2
fi
variant=$1
action=${2:-start}
case "${variant}" in
  reference) prefix=/home/ubuntu/experiments/dovecot-reference ;;
  afl) prefix=/home/ubuntu/experiments/dovecot-afl ;;
  gcov) prefix=/home/ubuntu/experiments/dovecot-gcov ;;
  *) echo "Unknown Dovecot variant: ${variant}" >&2; exit 2 ;;
esac
case "${action}" in
  start) export LD_LIBRARY_PATH="${prefix}/lib"; exec "${prefix}/sbin/dovecot" -F -c /workspace/dovecot.conf ;;
  stop) export LD_LIBRARY_PATH="${prefix}/lib"; exec "${prefix}/sbin/dovecot" -c /workspace/dovecot.conf stop ;;
  reset)
    export LD_LIBRARY_PATH="${prefix}/lib"
    "${prefix}/sbin/dovecot" -c /workspace/dovecot.conf stop >/dev/null 2>&1 || true
    rm -rf -- /tmp/dovecot-pop3-benchmark-state
    mkdir -p /tmp/dovecot-pop3-benchmark-state/{run,state,log,mail}
    chown -R ubuntu:ubuntu /tmp/dovecot-pop3-benchmark-state
    ;;
  *) echo "Unknown Dovecot action: ${action}" >&2; exit 2 ;;
esac
