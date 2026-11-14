#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then echo "Smoke server must start as root" >&2; exit 2; fi
OUTDIR=${1:?output directory required}
REPETITIONS=${2:-5}
PREFIX=${DOVECOT_PREFIX:-/home/ubuntu/experiments/dovecot-reference}
mkdir -p "${OUTDIR}"
chown -R ubuntu:ubuntu "${OUTDIR}"
export LD_LIBRARY_PATH="${PREFIX}/lib"
/usr/local/sbin/dovecot-root-launcher "${DOVECOT_VARIANT:-reference}" reset
runuser -u ubuntu -- python3 /workspace/prepare_maildir.py
"${PREFIX}/sbin/dovecot" -F -c /workspace/dovecot.conf >"${OUTDIR}/server.log" 2>&1 &
server_pid=$!
cleanup() {
  "${PREFIX}/sbin/dovecot" -c /workspace/dovecot.conf stop >/dev/null 2>&1 || true
  kill -TERM "${server_pid}" 2>/dev/null || true
  wait "${server_pid}" 2>/dev/null || true
}
trap cleanup EXIT
for repetition in $(seq 1 "${REPETITIONS}"); do
  runuser -u ubuntu -- python3 /workspace/protocol_smoke.py \
    --port 1110 --password dovecot-benchmark-pass \
    --save-seeds "${OUTDIR}/session-${repetition}"
  runuser -u ubuntu -- python3 /workspace/prepare_maildir.py
done
echo "PASS: ${REPETITIONS} authenticated POP3 transactions against ${PREFIX}"
