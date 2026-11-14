#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/apache-http2-fuzz-30m}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
SEED_DIR=${SEED_DIR:-${WORKDIR}/seeds}
FUZZER_BIN=${FUZZER_BIN:-/opt/aflnet/afl-fuzz}
PORT=${HTTPD_PORT:-20240}
if [[ ! -x "$FUZZER_BIN" || ! -x /opt/httpd/bin/httpd || ! -d "$SEED_DIR" ]]; then
  echo "AFLNet, Apache httpd, or HTTP/2 seeds missing" >&2; exit 2
fi
grep -a -q HTTP2 "$FUZZER_BIN" || { echo "AFLNet lacks the HTTP2 parser" >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2; exit 2
fi
mkdir -p "$OUTDIR"
export HTTPD_PORT="$PORT" AFL_FAST_CAL=1 AFL_NO_UI=1
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=HTTP/2 cleartext h2c direct preface mode over TCP
product_release=Apache HTTP Server 2.4.71 built from official signed source with AFL instrumentation
target_scope=mod_http2 and single-process prefork MPM serving one local static document; no TLS or external services
seed_dir=${SEED_DIR}
reset=AFL's forkserver forks a fresh AFL-instrumented single-process Apache httpd for each testcase; AFLNet drains 100 ms, -K sends SIGTERM, and the forkserver reaps each child
request_parser=custom HTTP2 parser; combine client preface and valid initial SETTINGS, then split later complete 9-byte-header frames by 24-bit payload length
response_parser=custom HTTP2 response-state parser; frame type and flags, no HPACK status decoding
feedback_scope=AFL-instrumented Apache server/core/modules plus parsed HTTP/2 response frame states
uninstrumented_dependencies=distribution libnghttp2 shared library; bitmap is not full Apache source coverage
campaign_duration=${DURATION}
container_cpu_quota=2
container_memory_limit=1g
target=127.0.0.1:${PORT}/tcp
PARAMS
cleanup() {
  local status=$?
  /bin/bash "$WORKDIR/stop-target.sh" >/dev/null 2>&1 || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup EXIT
/bin/bash "$WORKDIR/prepare-target.sh"
python3 "$WORKDIR/protocol_smoke.py" --host 127.0.0.1 --port "$PORT" --passes 3 \
  --output "$OUTDIR/preflight-smoke.json"
/bin/bash "$WORKDIR/stop-target.sh"
python3 "$WORKDIR/make_seeds.py" "$SEED_DIR"
set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -d -i "$SEED_DIR" -o "$OUTDIR" \
  -N "tcp://127.0.0.1/${PORT}" -P HTTP2 -D 100000 -q 3 -s 3 -E -K -W 30 \
  -m none -t 5000 -- /opt/httpd/bin/httpd -f /opt/benchmark/httpd.conf -DFOREGROUND -X
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: ${FUZZ_STATUS}"
/bin/bash "$WORKDIR/prepare-target.sh"
python3 "$WORKDIR/protocol_smoke.py" --host 127.0.0.1 --port "$PORT" --passes 3 \
  --output "$OUTDIR/postrun-smoke.json"
/bin/bash "$WORKDIR/stop-target.sh"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" --output "$OUTDIR/listener-closed.json"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ ! -f "$OUTDIR/plot_data" ]] || cp "$OUTDIR/plot_data" "$OUTDIR/fuzz-stats.csv"
[[ "$FUZZ_STATUS" -eq 124 || "$FUZZ_STATUS" -eq 130 ]] && exit 0
exit "$FUZZ_STATUS"
