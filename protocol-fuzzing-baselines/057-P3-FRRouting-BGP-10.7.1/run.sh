#!/usr/bin/env bash
set -u
OUTDIR=${1:-/results/frr-bgp-fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
BGP_HOST=${BGP_HOST:-127.0.0.1}
BGP_PORT=${BGP_PORT:-179}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-10000}
OPTIONS=${3:-}
[[ -x "$FUZZER_BIN" ]] || { echo "missing AFLNet binary: $FUZZER_BIN" >&2; exit 2; }
[[ -x /usr/lib/frr/bgpd ]] || { echo "FRR bgpd binary missing" >&2; exit 2; }
[[ -s "$WORKDIR/bgpd.conf" && -d "$WORKDIR/seeds" && -f "$WORKDIR/bgp.dict" ]] || {
  echo "FRR BGP config, seed corpus, or dictionary missing" >&2; exit 2;
}
grep -a -q BGP "$FUZZER_BIN" || { echo "AFLNet lacks BGP parser" >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$OUTDIR"
cleanup() {
  local status=$?
  /bin/bash "$WORKDIR/stop-bgpd.sh" || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup EXIT
version=$(/usr/lib/frr/bgpd --version 2>&1 | sed -n '1p')
grep -Fq "${FRR_EXPECTED_VERSION:-10.7.1}" <<< "$version" || {
  echo "FRR version assertion failed: $version" >&2
  exit 2
}
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=BGP-4 over TCP/${BGP_PORT}
product_release=FRRouting ${FRR_EXPECTED_VERSION:-10.7.1}; runtime asserted by bgpd --version
endpoint=single dynamic loopback IPv4-unicast peer at ${BGP_HOST}:${BGP_PORT}
target_scope=OPEN, KEEPALIVE, UPDATE, NOTIFICATION, ROUTE-REFRESH; excludes other address families, BGP-LS, EVPN, BMP, BFD, RPKI and multi-router topology
reset=restart standalone bgpd process with empty in-memory peer/RIB state before every testcase; Zebra and kernel route installation disabled
fuzzer=AFLNet ProFuzzBench snapshot commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
protocol_parser=BGP marker+length+type message framing; response state includes message type and NOTIFICATION code/subcode
feedback_scope=black-box BGP response-state feedback; FRR bgpd is not coverage-instrumented
bitmap_scope=AFL helper bitmap only; do not report it as FRR source coverage
forkserver=disabled; AFL_NO_FORKSRV=1
target_stub=/usr/bin/python3 -c pass (bgpd is separately managed as the actual TCP target)
campaign_duration=${DURATION}
container_cpu_quota=2; fuzzer and bgpd share the CPU budget
container_memory_limit=1200m
execution_timeout_ms=${EXEC_TIMEOUT_MS}
additional_options=${OPTIONS}
PARAMS
export BGP_HOST BGP_PORT AFL_NO_FORKSRV=1 AFL_FAST_CAL=1 AFL_NO_UI=1
read -r -a EXTRA_OPTIONS <<< "$OPTIONS"
echo "starting FRRouting BGP response-state campaign: ${DURATION}; ${version}; results=${OUTDIR}"
/bin/bash "$WORKDIR/start-bgpd.sh"
set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -n -d -i "$WORKDIR/seeds" -x "$WORKDIR/bgp.dict" \
  -o "$OUTDIR" -c "$WORKDIR/reset-bgpd.sh" \
  -N "tcp://${BGP_HOST}/${BGP_PORT}" -P BGP -E -q 3 -s 3 -R -K \
  -D 100000 -W 250 -w 250000 -m none -t "$EXEC_TIMEOUT_MS" \
  "${EXTRA_OPTIONS[@]}" -- /usr/bin/python3 -c pass
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: ${FUZZ_STATUS}"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ ! -f "$OUTDIR/plot_data" ]] || cp "$OUTDIR/plot_data" "$OUTDIR/fuzz-stats.csv"
[[ "$FUZZ_STATUS" -eq 124 || "$FUZZ_STATUS" -eq 130 ]] && exit 0
exit "$FUZZ_STATUS"
