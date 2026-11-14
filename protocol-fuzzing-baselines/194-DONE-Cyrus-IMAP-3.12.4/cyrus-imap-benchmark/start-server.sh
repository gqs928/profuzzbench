#!/usr/bin/env bash
set -euo pipefail

CYRUS_PREFIX=${CYRUS_PREFIX:-/home/ubuntu/experiments/cyrus-afl}
export LD_LIBRARY_PATH="${CYRUS_PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export PATH="${CYRUS_PREFIX}/bin:${CYRUS_PREFIX}/sbin:${CYRUS_PREFIX}/libexec:${PATH}"
mkdir -p /tmp/cyrus-benchmark-state/config /tmp/cyrus-benchmark-state/proc \
  /tmp/cyrus-benchmark-state/lock /tmp/cyrus-benchmark-state/mail \
  /tmp/cyrus-benchmark-state/sieve /tmp/cyrus-benchmark-state/saslauthd
mkdir -p /tmp/cyrus-benchmark-state/config/socket
saslauthd -a sasldb -n 2 -m /tmp/cyrus-benchmark-state/saslauthd
for _ in {1..40}; do
  [[ -S /tmp/cyrus-benchmark-state/saslauthd/mux ]] && break
  sleep 0.05
done
[[ -S /tmp/cyrus-benchmark-state/saslauthd/mux ]] || {
  echo "saslauthd did not create its socket" >&2
  exit 1
}
exec "${CYRUS_PREFIX}/libexec/master" -D -C /workspace/imapd.conf \
  -M /workspace/cyrus.conf
