#!/usr/bin/env bash
set -u

# Usage: crash_script.sh SAMPLE_FILE
SAMPLE=${1:?Usage: crash_script.sh SAMPLE_FILE}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
SERVER=${SERVER:-${WORKDIR}/memcached-fuzz/memcached}
PORT=${PORT:-11213}
LOG=${LOG:-/tmp/memcached-crash-replay.log}
[[ -f ${SAMPLE} ]] || { echo "Sample not found: ${SAMPLE}" >&2; exit 2; }
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}

if [[ -n ${SERVER_PRELOAD:-} ]]; then
  LD_PRELOAD="${SERVER_PRELOAD}" "${SERVER}" -B ascii -p "${PORT}" -U 0 -t 1 >"${LOG}" 2>&1 &
else
  "${SERVER}" -B ascii -p "${PORT}" -U 0 -t 1 >"${LOG}" 2>&1 &
fi
pid=$!
trap 'kill -TERM "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT
for attempt in $(seq 1 100); do
  if nc -z 127.0.0.1 "${PORT}" >/dev/null 2>&1; then break; fi
  if ! kill -0 "${pid}" 2>/dev/null; then break; fi
  sleep 0.02
done
timeout 5s nc -N 127.0.0.1 "${PORT}" < "${SAMPLE}" >/dev/null 2>&1 || true
sleep 0.1
if kill -0 "${pid}" 2>/dev/null; then
  echo 'Server survived the replay; stopping it normally.'
  kill -TERM "${pid}" 2>/dev/null || true
  wait "${pid}" 2>/dev/null
  status=0
else
  wait "${pid}"
  status=$?
  echo "Server exited during replay (status ${status})."
fi
trap - EXIT
cat "${LOG}"
exit "${status}"
