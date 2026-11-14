#!/usr/bin/env bash
set -euo pipefail

OUTDIR=${1:?output directory required}
REPETITIONS=${2:-5}
mkdir -p "${OUTDIR}"
/workspace/start-server.sh >"${OUTDIR}/server.log" 2>&1 &
server_pid=$!
cleanup() {
  kill -TERM "${server_pid}" 2>/dev/null || true
  wait "${server_pid}" 2>/dev/null || true
  /workspace/reset-state.sh
}
trap cleanup EXIT
for repetition in $(seq 1 "${REPETITIONS}"); do
  python3 /workspace/protocol_smoke.py --password resp-benchmark-pass \
    >"${OUTDIR}/session-${repetition}.json"
done
echo "PASS: ${REPETITIONS} POP3 protocol sessions (${CYRUS_PREFIX})"
