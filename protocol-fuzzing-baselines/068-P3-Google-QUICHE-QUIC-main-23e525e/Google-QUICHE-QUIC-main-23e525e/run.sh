#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/google-quiche-preflight-60s-20261113}
DURATION=${2:-60s}
WORKDIR=${WORKDIR:-/opt/benchmark}
SEED_DIR=${SEED_DIR:-${WORKDIR}/seeds}
FUZZER_BIN=${AFLNET_BIN:-/opt/aflnet/afl-fuzz}
PORT=${QUICHE_PORT:-4433}
if [[ ! -x "$FUZZER_BIN" || ! -x "$QUICHE_SERVER" || ! -d "$SEED_DIR" ]]; then
  echo "AFLNet, instrumented Google QUICHE quic_server, or QUIC seeds missing" >&2
  exit 2
fi
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$OUTDIR"
python3 "$WORKDIR/validate_seeds.py" "$SEED_DIR" > "$OUTDIR/seeds-validation.json"
export QUICHE_PORT="$PORT" AFL_FAST_CAL=1 AFL_NO_UI=1 AFL_MAP_SIZE=262144 \
  AFL_PATH=/opt/aflnet
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=QUIC v1 over UDP; one Initial datagram is one AFLNet input region
implementation=Google QUICHE official main commit 23e525e5184bbd98d9722bc3bb3f4ce181efcde4
target=official standalone //quiche:quic_server binary
target_scope=valid Initial and malformed/public-header packet processing; no completed TLS handshake or HTTP/3 request-response
seed_provenance=TLS 1.3 ClientHello from Python/OpenSSL with QUIC transport parameters, protected as QUIC v1 Initial; SHA256 c6332ee934a5701e00f670618e1e151725be421bce4ea8396e30e24f4983a748
reset=AFLNet -K terminates the quic_server child and starts a fresh server process per testcase
request_parser=custom QUIC parser preserves datagram atomicity; input cap 65,507 bytes
response_parser=custom public QUIC header state parser; encrypted frames are not decoded
coverage=Google QUICHE C++ compiled with AFLNet 2.56b afl-gcc/afl-g++ assembler wrappers; parser supplies protocol-state feedback
forkserver=target and fuzzer both use AFLNet 2.56b vanilla protocol
coverage_map=AFLNet MAP_SIZE_POW2=18 (262,144 bytes)
certificate=ephemeral self-signed localhost certificate generated at image build; loopback-only target
container_cpu_quota=2
container_memory_limit=1g
campaign_duration=$DURATION
target=127.0.0.1:$PORT/udp
PARAMS
cleanup() {
  local status=$?
  pkill -TERM -x quic_server 2>/dev/null || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup EXIT
python3 "$WORKDIR/protocol_smoke.py" --seed "$SEED_DIR/quic-v1-client-initial.bin" \
  --port "$PORT" --passes 3 --output "$OUTDIR/preflight-smoke.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" \
  --output "$OUTDIR/preflight-listener-closed.json"
set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -d -i "$SEED_DIR" -o "$OUTDIR" \
  -N "udp://127.0.0.1/$PORT" -P QUIC -D 50000 -W 30 -w 50000 \
  -q 3 -s 3 -E -K -m none -t 2000 -- \
  "$QUICHE_SERVER" "--port=$PORT" \
  "--certificate_file=$QUICHE_CERT" "--key_file=$QUICHE_KEY"
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: $FUZZ_STATUS"
python3 "$WORKDIR/protocol_smoke.py" --seed "$SEED_DIR/quic-v1-client-initial.bin" \
  --port "$PORT" --passes 3 --output "$OUTDIR/postrun-smoke.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" \
  --output "$OUTDIR/listener-closed.json"
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
