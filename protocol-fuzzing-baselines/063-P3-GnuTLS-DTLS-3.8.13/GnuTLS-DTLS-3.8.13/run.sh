#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/gnutls-dtls-fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
SEED_DIR=${SEED_DIR:-${WORKDIR}/seeds}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
GNUTLS_PORT=${GNUTLS_PORT:-20220}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-10000}
if [[ ! -x "$FUZZER_BIN" || ! -x /opt/gnutls/bin/gnutls-serv || ! -d "$SEED_DIR" ]]; then
  echo "AFLNet, instrumented gnutls-serv, or DTLS seeds missing" >&2; exit 2
fi
grep -a -q DTLS12 "$FUZZER_BIN" || { echo "AFLNet lacks the DTLS12 parser" >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2; exit 2
fi
mkdir -p "$OUTDIR"
export GNUTLS_PORT GNUTLS_LOG_FILE="$OUTDIR/gnutls.log"
export AFL_FAST_CAL=1 AFL_NO_UI=1
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=DTLS 1.2 over UDP; AFLNet DTLS12 parser splits concatenated records into UDP datagrams
product_release=GnuTLS 3.8.13 built from official dual-signed source with AFLNet instrumentation
target_scope=local gnutls-serv --echo endpoint on UDP/${GNUTLS_PORT}; no external services
seed_dir=${SEED_DIR}
version_profile=NORMAL:-VERS-ALL:+VERS-DTLS1.2; DTLS 1.0, DTLS 1.3, and TLS/TCP excluded
cookie_mode=--nocookie to avoid cookie challenge and source-address coupling
reset=AFLNet starts a fresh instrumented gnutls-serv child for each testcase
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
request_parser=AFLNet built-in DTLS12 parser; record boundaries use the DTLS header length field
response_parser=AFLNet built-in DTLS12 response and handshake-state parser
feedback_scope=target library/server AFL instrumentation and DTLS response states; helper binary is not used
forkserver=enabled for instrumented target; each AFLNet testcase starts a clean service process
campaign_duration=${DURATION}
container_cpu_quota=2
container_memory_limit=768m
execution_timeout_ms=${EXEC_TIMEOUT_MS}
target=127.0.0.1:${GNUTLS_PORT}/udp
PARAMS
echo "starting GnuTLS DTLS 1.2 state-feedback campaign: ${DURATION}; results=${OUTDIR}"
cleanup_target() {
  local status=$?
  for pid in $(pgrep -x gnutls-serv 2>/dev/null || true); do kill -TERM "$pid" 2>/dev/null || true; done
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup_target EXIT
/bin/bash "$WORKDIR/prepare-target.sh"
python3 "$WORKDIR/protocol_smoke.py" --host 127.0.0.1 --port "$GNUTLS_PORT" --passes 3 \
  --output "$OUTDIR/preflight-smoke.json"
python3 "$WORKDIR/prepare_seeds.py" "$SEED_DIR"
set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -d -i "$SEED_DIR" -o "$OUTDIR" \
  -N "udp://127.0.0.1/${GNUTLS_PORT}" -P DTLS12 -D 10000 -q 3 -s 3 -E -K -W 30 \
  -m none -t "$EXEC_TIMEOUT_MS" -- /opt/gnutls/bin/gnutls-serv \
  --udp --nocookie --port="$GNUTLS_PORT" --echo \
  --priority='NORMAL:-VERS-ALL:+VERS-DTLS1.2' \
  --x509keyfile="${GNUTLS_CERT_DIR:-/run/gnutls-benchmark}/server.key" \
  --x509certfile="${GNUTLS_CERT_DIR:-/run/gnutls-benchmark}/server.crt"
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: ${FUZZ_STATUS}"
python3 "$WORKDIR/protocol_smoke.py" --host 127.0.0.1 --port "$GNUTLS_PORT" --passes 3 \
  --output "$OUTDIR/postrun-smoke.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$GNUTLS_PORT" \
  --output "$OUTDIR/listener-closed.json"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ ! -f "$OUTDIR/plot_data" ]] || cp "$OUTDIR/plot_data" "$OUTDIR/fuzz-stats.csv"
[[ "$FUZZ_STATUS" -eq 124 || "$FUZZ_STATUS" -eq 130 ]] && exit 0
exit "$FUZZ_STATUS"
