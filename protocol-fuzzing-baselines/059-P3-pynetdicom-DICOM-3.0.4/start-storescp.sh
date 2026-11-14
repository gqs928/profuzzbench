#!/usr/bin/env bash
set -euo pipefail
DICOM_PORT=${DICOM_PORT:-11112}
DICOM_RECEIVE_DIR=${DICOM_RECEIVE_DIR:-/tmp/pynetdicom-receive}
DICOM_LOG_FILE=${DICOM_LOG_FILE:-/results/storescp.log}
PID_FILE=${PID_FILE:-/tmp/storescp.pid}
mkdir -p "$DICOM_RECEIVE_DIR" "$(dirname "$DICOM_LOG_FILE")"
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "storescp already running: pid=$(cat "$PID_FILE")"
  exit 0
fi
python - <<'PY'
import importlib.metadata as m
assert m.version("pynetdicom") == "3.0.4", m.version("pynetdicom")
assert m.version("pydicom") == "3.0.2", m.version("pydicom")
PY
cd "$DICOM_RECEIVE_DIR"
nohup python -m pynetdicom storescp -aet STORESCP -od "$DICOM_RECEIVE_DIR" -ll warn "$DICOM_PORT" \
  >>"$DICOM_LOG_FILE" 2>&1 &
pid=$!
echo "$pid" > "$PID_FILE"
if ! python3 /opt/benchmark/dicom_probe.py --port "$DICOM_PORT" --deadline 25; then
  echo "pynetdicom storescp failed protocol readiness; recent server log:" >&2
  tail -80 "$DICOM_LOG_FILE" >&2 || true
  kill -TERM "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  exit 1
fi
echo "pynetdicom storescp ready: pid=$pid port=$DICOM_PORT"
