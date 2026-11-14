#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/knot-dns-fuzz-30m-20261112}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
FUZZER_BIN=${FUZZER_BIN:-/opt/aflnet/afl-fuzz}
KNOT_PORT=${KNOT_PORT:-5300}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-10000}
if [[ ! -x "$FUZZER_BIN" || ! -x "$WORKDIR/start-knot.sh" || ! -d "$WORKDIR/seeds" ]]; then
  echo "fuzzer, knotd launcher, or DNS/TCP seeds missing" >&2
  exit 2
fi
grep -a -q DNS_TCP "$FUZZER_BIN" || { echo "AFLNet lacks DNS/TCP adapter" >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$OUTDIR"
export KNOT_PORT
export KNOT_LOG_FILE="$OUTDIR/knotd.log"
export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=DNS/TCP with RFC 7766 2-byte big-endian length prefix on TCP/${KNOT_PORT}
product_release=Knot DNS 3.6.2; source SHA-256 and release GPG signature verified
target_scope=authoritative fuzz.test DNS/TCP query/response; daemon may also listen for UDP at server.listen, but the driver sends TCP only; TLS/QUIC/recursion/AXFR/DDNS/DNSSEC signing excluded
reset=stop/restart isolated knotd; recreate runtime storage and run directories; immutable zone file retained
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
request_parser=DNS_TCP profile adapter segments each two-byte length-prefixed DNS message
response_parser=profile adapter emits DNS QR/opcode/AA/TC/RCODE states; malformed/truncated length marker
feedback_scope=black-box DNS/TCP response-state feedback; Knot target is not AFL-instrumented
bitmap_scope=AFL helper bitmap only; do not report it as Knot source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
target_stub=/usr/bin/python3 -c pass (knotd is the actual TCP target)
campaign_duration=${DURATION}
container_cpu_quota=2
container_memory_limit=768m
execution_timeout_ms=${EXEC_TIMEOUT_MS}
PARAMS
echo "starting Knot DNS/TCP state-feedback campaign: ${DURATION}; results=${OUTDIR}"
cleanup_target() {
  local status=$?
  /bin/bash "$WORKDIR/stop-knot.sh" || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup_target EXIT
/bin/bash "$WORKDIR/start-knot.sh"
set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -n -d -i "$WORKDIR/seeds" -x "$WORKDIR/dns-tcp.dict" \
  -o "$OUTDIR" -c "$WORKDIR/reset-knot.sh" \
  -N "tcp://127.0.0.1/${KNOT_PORT}" -P DNS_TCP -E -q 3 -s 3 -R -K \
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
