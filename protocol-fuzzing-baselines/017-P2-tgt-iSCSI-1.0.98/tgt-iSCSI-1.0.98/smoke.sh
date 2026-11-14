#!/usr/bin/env bash
set -Eeuo pipefail

RESULT_DIR=${1:-/results/iscsi-smoke}
mkdir -p "${RESULT_DIR}"
if [[ -n $(find "${RESULT_DIR}" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Output directory is not empty: ${RESULT_DIR}" >&2
  exit 2
fi

TGT_PREFIX=/opt/tgt-reference /opt/benchmark/start-target.sh \
  >"${RESULT_DIR}/server.log" 2>&1 &
server_pid=$!
cleanup() {
  kill -TERM "${server_pid}" 2>/dev/null || true
  wait "${server_pid}" 2>/dev/null || true
}
trap cleanup EXIT TERM INT

python3 - <<'PY'
import os, socket, time
for _ in range(100):
    if os.path.exists("/tmp/tgt-benchmark-ready"):
        break
    time.sleep(0.05)
else:
    raise SystemExit("iSCSI target did not complete configuration")
with socket.create_connection(("127.0.0.1", 3260), timeout=0.5):
    pass
PY

python3 /opt/benchmark/protocol_client.py --save-seeds "${RESULT_DIR}/seeds" \
  | tee "${RESULT_DIR}/protocol-smoke.json"
cp /opt/benchmark/build-versions.txt "${RESULT_DIR}/build-versions.txt"
