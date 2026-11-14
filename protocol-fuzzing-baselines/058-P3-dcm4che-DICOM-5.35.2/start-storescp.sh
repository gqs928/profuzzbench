#!/usr/bin/env bash
set -euo pipefail
DCM4CHE_HOME=${DCM4CHE_HOME:-/opt/dcm4che}
DICOM_PORT=${DICOM_PORT:-11112}
DICOM_RECEIVE_DIR=${DICOM_RECEIVE_DIR:-/tmp/dcm4che-receive}
DICOM_LOG_FILE=${DICOM_LOG_FILE:-/results/storescp.log}
PID_FILE=${PID_FILE:-/tmp/storescp.pid}
mkdir -p "$DICOM_RECEIVE_DIR" "$(dirname "$DICOM_LOG_FILE")"
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "storescp already running: pid=$(cat "$PID_FILE")"
  exit 0
fi
version_output=$("$DCM4CHE_HOME/bin/storescp" -V 2>&1) || {
  echo "storescp version command failed" >&2
  exit 2
}
if ! grep -Fq '5.35.2' <<< "$version_output"; then
  echo "storescp version assertion failed" >&2
  exit 2
fi
cd "$DICOM_RECEIVE_DIR"
export DCM4CHE_HOME
export JAVA_OPTS="${JAVA_OPTS:--Xms32m -Xmx512m -XX:+ExitOnOutOfMemoryError -Djava.awt.headless=true}"
nohup "$DCM4CHE_HOME/bin/storescp" --accept-unknown \
  -b "STORESCP@0.0.0.0:${DICOM_PORT}" >>"$DICOM_LOG_FILE" 2>&1 &
pid=$!
echo "$pid" > "$PID_FILE"
if ! python3 /opt/benchmark/dicom_probe.py --port "$DICOM_PORT" --deadline 25; then
  echo "storescp failed protocol readiness; recent server log:" >&2
  tail -80 "$DICOM_LOG_FILE" >&2 || true
  kill -TERM "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  exit 1
fi
echo "storescp ready: pid=$pid port=$DICOM_PORT"
