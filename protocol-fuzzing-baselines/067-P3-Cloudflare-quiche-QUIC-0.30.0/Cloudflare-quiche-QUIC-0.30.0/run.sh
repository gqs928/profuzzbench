#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/quiche-preflight-60s}
DURATION=${2:-60s}
WORKDIR=${WORKDIR:-/opt/benchmark}
SEED_DIR=${SEED_DIR:-${WORKDIR}/seeds}
FUZZER_BIN=${AFLNET_BIN:-/opt/aflnet/afl-fuzz}
PORT=${QUICHE_PORT:-4433}

if [[ ! -x "$FUZZER_BIN" || ! -x "$QUICHE_SERVER" || ! -d "$SEED_DIR" ]]; then
  echo "AFLNet, instrumented quiche-server, or QUIC seeds missing" >&2; exit 2
fi
grep -a -q quiche-server "$QUICHE_SERVER" || { echo "unexpected target binary" >&2; exit 2; }
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty except for seed validation: $OUTDIR" >&2; exit 2
fi
mkdir -p "$OUTDIR"
python3 "$WORKDIR/validate_seeds.py" "$SEED_DIR" > "$OUTDIR/seeds-validation.json"
export QUICHE_PORT="$PORT" AFL_FAST_CAL=1 AFL_NO_UI=1 AFL_MAP_SIZE=262144 AFL_OLD_FORKSERVER=1 RUST_LOG=error
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=QUIC v1 over UDP; one Initial datagram is one AFLNet input region
product_release=Cloudflare quiche 0.30.0 with cargo-afl 0.18.2 LLVM SanitizerCoverage instrumentation
coverage_map=AFLNet compiled with MAP_SIZE_POW2=18 (262144 bytes); target forkserver uses AFL++ legacy mode because AFLNet 2.56b implements the vanilla AFL protocol
target_scope=official quiche-server example; valid Initial and malformed/public-header packet processing; no full handshake or HTTP/3 request-response completion
reset=AFLNet -K terminates the single quiche-server child and the forkserver starts a fresh server process per testcase
request_parser=custom QUIC parser preserving datagram atomicity; maximum AFLNet input limited to IPv4 UDP payload size 65,507 bytes
response_parser=custom QUIC public-header state parser; observes long-header packet type/version, short-header, Version Negotiation, Retry, malformed/truncated
coverage_scope=Rust quiche and quiche-server code instrumented via cargo-afl; C AFLNet parser provides protocol state feedback
container_cpu_quota=2
container_memory_limit=1g
campaign_duration=${DURATION}
target=127.0.0.1:${PORT}/udp
PARAMS

cleanup() {
  local status=$?
  pkill -TERM -x quiche-server 2>/dev/null || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup EXIT

python3 "$WORKDIR/protocol_smoke.py" --seed "$SEED_DIR/quic-v1-client-initial.bin" \
  --passes 3 --output "$OUTDIR/preflight-smoke.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" --output "$OUTDIR/preflight-listener-closed.json"

set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -d -i "$SEED_DIR" -o "$OUTDIR" \
  -N "udp://127.0.0.1/${PORT}" -P QUIC -D 50000 -W 30 -w 50000 \
  -q 3 -s 3 -E -K -m none -t 2000 -- \
  "$QUICHE_SERVER" --listen "127.0.0.1:${PORT}" --cert "$QUICHE_CERT" \
  --key "$QUICHE_KEY" --root "$QUICHE_ROOT" --no-retry --disable-gso --disable-pacing
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: ${FUZZ_STATUS}"

python3 "$WORKDIR/protocol_smoke.py" --seed "$SEED_DIR/quic-v1-client-initial.bin" \
  --passes 3 --output "$OUTDIR/postrun-smoke.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" --output "$OUTDIR/listener-closed.json"
mkdir -p "$OUTDIR/replayable-hangs" "$OUTDIR/replayable-crashes"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/queue" --port 46000 \
  --output "$OUTDIR/replay-summary.json"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/replayable-hangs" --port 47000 \
  --allow-target-exit --output "$OUTDIR/hangs-replay-summary.json"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/replayable-crashes" --port 48000 \
  --allow-target-exit --output "$OUTDIR/crashes-replay-summary.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" \
  --output "$OUTDIR/replay-listener-closed.json"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ ! -f "$OUTDIR/plot_data" ]] || cp "$OUTDIR/plot_data" "$OUTDIR/fuzz-stats.csv"
[[ "$FUZZ_STATUS" -eq 124 || "$FUZZ_STATUS" -eq 130 ]] && exit 0
exit "$FUZZ_STATUS"
