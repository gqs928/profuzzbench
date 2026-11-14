#!/usr/bin/env bash
set -euo pipefail

PREFIX=${CYRUS_PREFIX:-/home/ubuntu/experiments/cyrus-reference}
export PATH="$PREFIX/bin:$PREFIX/sbin:$PREFIX/libexec:$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p /tmp/cyrus-benchmark-state/{config/socket,proc,lock,mail,sieve,saslauthd}
saslauthd -a sasldb -n 2 -m /tmp/cyrus-benchmark-state/saslauthd
for _ in {1..100}; do
  [[ -S /tmp/cyrus-benchmark-state/saslauthd/mux ]] && break
  sleep 0.05
done
[[ -S /tmp/cyrus-benchmark-state/saslauthd/mux ]] || { echo 'saslauthd socket did not appear' >&2; exit 1; }
exec "$PREFIX/libexec/master" -D -C /home/ubuntu/experiments/cyrus-imap-bootstrap.conf \
  -M /home/ubuntu/experiments/cyrus-imap-bootstrap.services.conf
