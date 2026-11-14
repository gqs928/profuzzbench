#!/usr/bin/env bash
set -u
OUTDIR=${1:-/results/unbound-fuzz-30m-20261112}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
UNBOUND_PORT=${UNBOUND_PORT:-5300}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-10000}
if [[ ! -x "$FUZZER_BIN" || ! -x "$WORKDIR/start-unbound.sh" || ! -d "$WORKDIR/seeds" ]]; then
  echo "fuzzer, Unbound launcher, or DNS/TCP seeds missing" >&2
  exit 2
fi
grep -a -q DNS_TCP "$FUZZER_BIN" || { echo "AFLNet lacks DNS/TCP adapter" >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$OUTDIR"
export UNBOUND_PORT
export UNBOUND_LOG_FILE="$OUTDIR/unbound.log"
export AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=DNS/TCP RFC 7766 with two-byte big-endian message-length prefix on TCP/${UNBOUND_PORT}
product_release=Unbound 1.26.2 official signed source build
target_scope=local immutable static fuzz.test zone; TCP inputs only; external recursion, DNSSEC validation, DoT, DoH, and DoQ excluded
reset=stop and restart one isolated Unbound process before each testcase; local zone configuration is immutable
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
request_parser=DNS_TCP adapter segments each two-byte length-prefixed DNS message
response_parser=DNS response QR/opcode/AA/TC/RCODE states
feedback_scope=black-box DNS/TCP response-state feedback; Unbound target is not AFL-instrumented
bitmap_scope=AFL helper bitmap only; do not report it as Unbound source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
target_stub=/usr/bin/python3 -c pass (unbound is the actual TCP target)
campaign_duration=${DURATION}
container_cpu_quota=2
container_memory_limit=768m
execution_timeout_ms=${EXEC_TIMEOUT_MS}
target=127.0.0.1:${UNBOUND_PORT}
PARAMS
echo "starting Unbound DNS/TCP state-feedback campaign: ${DURATION}; results=${OUTDIR}"
cleanup_target() {
  local status=$?
  /bin/bash "$WORKDIR/stop-unbound.sh" || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup_target EXIT
/bin/bash "$WORKDIR/start-unbound.sh"
set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -n -d -i "$WORKDIR/seeds" -x "$WORKDIR/dns-tcp.dict" \
  -o "$OUTDIR" -c "$WORKDIR/reset-unbound.sh" \
  -N "tcp://127.0.0.1/${UNBOUND_PORT}" -P DNS_TCP -E -q 3 -s 3 -R -K \
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
