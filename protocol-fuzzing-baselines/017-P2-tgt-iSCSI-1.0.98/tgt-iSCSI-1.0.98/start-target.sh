#!/usr/bin/env bash
set -Eeuo pipefail

PREFIX=${TGT_PREFIX:-/opt/tgt-afl}
IPC=${TGT_IPC_SOCKET:-/tmp/tgt-benchmark-ipc}
TARGET_IQN=${TARGET_IQN:-iqn.2026-11.invalid:codex-tgt}
BACKING_STORE=${BACKING_STORE:-/tmp/tgt-benchmark.img}
READY_FILE=${TGT_READY_FILE:-/tmp/tgt-benchmark-ready}

rm -f "${IPC}" "${IPC}.0" /tmp/tgt-benchmark-tgtd.pid "${READY_FILE}"
mkdir -p "$(dirname "${IPC}")"
truncate -s 16M "${BACKING_STORE}"
export TGT_IPC_SOCKET=${IPC}

"${PREFIX}/sbin/tgtd" -f >/tmp/tgt-benchmark-tgtd.log 2>&1 &
daemon_pid=$!
cleanup() {
  trap - EXIT TERM INT
  if kill -0 "${daemon_pid}" 2>/dev/null; then
    kill -TERM "${daemon_pid}" 2>/dev/null || true
    for _ in {1..20}; do
      kill -0 "${daemon_pid}" 2>/dev/null || break
      sleep 0.1
    done
    # tgtd may remain in its event loop after TERM in an isolated container.
    kill -KILL "${daemon_pid}" 2>/dev/null || true
  fi
  wait "${daemon_pid}" 2>/dev/null || true
  rm -f "${IPC}" "${IPC}.0" /tmp/tgt-benchmark-tgtd.pid "${READY_FILE}"
}
trap cleanup EXIT TERM INT

ready=0
for _ in {1..100}; do
  if "${PREFIX}/sbin/tgtadm" --lld iscsi --op show --mode target >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! kill -0 "${daemon_pid}" 2>/dev/null; then
    cat /tmp/tgt-benchmark-tgtd.log >&2
    exit 1
  fi
  sleep 0.05
done
[[ ${ready} == 1 ]] || { cat /tmp/tgt-benchmark-tgtd.log >&2; exit 1; }

"${PREFIX}/sbin/tgtadm" --lld iscsi --op new --mode target --tid 1 \
  --targetname "${TARGET_IQN}"
"${PREFIX}/sbin/tgtadm" --lld iscsi --op new --mode logicalunit --tid 1 \
  --lun 1 --backing-store "${BACKING_STORE}"
"${PREFIX}/sbin/tgtadm" --lld iscsi --op bind --mode target --tid 1 \
  --initiator-address ALL
touch "${READY_FILE}"

wait "${daemon_pid}"
