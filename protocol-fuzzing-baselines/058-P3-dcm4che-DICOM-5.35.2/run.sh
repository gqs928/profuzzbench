#!/usr/bin/env bash
set -u
OUTDIR=${1:-/results/dcm4che-fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
DICOM_PORT=${DICOM_PORT:-11112}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-10000}
if [[ ! -x "$FUZZER_BIN" || ! -x "$WORKDIR/start-storescp.sh" || ! -d "$WORKDIR/seeds" ]]; then
  echo "fuzzer, storescp launcher, or seeds missing" >&2
  exit 2
fi
grep -a -q DICOM "$FUZZER_BIN" || { echo "AFLNet lacks DICOM parser" >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$OUTDIR"
export DICOM_PORT
export DICOM_LOG_FILE="$OUTDIR/storescp.log"
export DICOM_RECEIVE_DIR=/tmp/dcm4che-receive
export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=DICOM Upper Layer over plaintext TCP/${DICOM_PORT}
product_release=dcm4che 5.35.2; storescp -V asserted before server start
target_scope=storescp Verification and Storage SCP; C-ECHO and one-pixel Secondary Capture C-STORE seeds; TLS/DICOMweb/HL7/LDAP excluded
reset=stop and restart one isolated storescp JVM and clear received objects before each testcase
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
request_parser=upstream six-byte DICOM UL PDU framing selected by -P DICOM
response_parser=profile parser emits every PDU type and DIMSE Command Field when carried by a complete command PDV
feedback_scope=black-box DICOM UL/DIMSE response-state feedback; target JVM is not coverage-instrumented
bitmap_scope=AFL helper bitmap only; do not report it as dcm4che source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
target_stub=/usr/bin/python3 -c pass (storescp JVM is the actual TCP target)
campaign_duration=${DURATION}
container_cpu_quota=2
container_memory_limit=1200m; JVM max heap 512 MiB
execution_timeout_ms=${EXEC_TIMEOUT_MS}
target=127.0.0.1:${DICOM_PORT}
PARAMS
echo "starting dcm4che DICOM UL state-feedback campaign: ${DURATION}; results=${OUTDIR}"
cleanup_target() {
  local status=$?
  /bin/bash "$WORKDIR/stop-storescp.sh" || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup_target EXIT
/bin/bash "$WORKDIR/start-storescp.sh"
set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -n -d -i "$WORKDIR/seeds" -x "$WORKDIR/dicom.dict" \
  -o "$OUTDIR" -c "$WORKDIR/reset-storescp.sh" \
  -N "tcp://127.0.0.1/${DICOM_PORT}" -P DICOM -E -q 3 -s 3 -R -K \
  -D 100000 -W 250 -w 250000 -m none -t "$EXEC_TIMEOUT_MS" -- \
  /usr/bin/python3 -c pass
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: ${FUZZ_STATUS}"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ ! -f "$OUTDIR/plot_data" ]] || cp "$OUTDIR/plot_data" "$OUTDIR/fuzz-stats.csv"
[[ "$FUZZ_STATUS" -eq 124 || "$FUZZ_STATUS" -eq 130 ]] && exit 0
exit "$FUZZ_STATUS"
