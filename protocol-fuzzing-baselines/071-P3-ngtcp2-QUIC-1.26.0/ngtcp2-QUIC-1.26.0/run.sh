#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/ngtcp2-preflight-60s-20261113}
DURATION=${2:-60s}
WORKDIR=${WORKDIR:-/opt/benchmark}
SEED_DIR=${SEED_DIR:-${WORKDIR}/seeds}
FUZZER_BIN=${AFLNET_BIN:-/opt/aflnet/afl-fuzz}
PORT=${NGTCP2_PORT:-4433}
if [[ ! -x "$FUZZER_BIN" || ! -x "$NGTCP2_SERVER" || ! -d "$SEED_DIR" ]]; then
  echo "AFLNet, instrumented ngtcp2 osslserver, or QUIC seeds missing" >&2
  exit 2
fi
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$OUTDIR"
python3 "$WORKDIR/validate_seeds.py" "$SEED_DIR" > "$OUTDIR/seeds-validation.json"
export NGTCP2_PORT="$PORT" AFL_FAST_CAL=1 AFL_NO_UI=1 AFL_MAP_SIZE=262144 AFL_PATH=/opt/aflnet
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=QUIC v1 over UDP; one Initial datagram is one AFLNet input region
implementation=ngtcp2 v1.26.0 official release 6a22a4d7a111f6b52391910e40ad3681a09cfb9c
tls_backend=OpenSSL 4.1.0 QUIC-TLS API; nghttp3 v1.19.0
target=official examples/osslserver; no target source patch
target_scope=valid Initial and malformed/public-header packet processing; no completed TLS handshake or HTTP/3 exchange
seed_provenance=1,200-byte QUIC v1 Initial with TLS 1.3 ClientHello and QUIC transport parameters; SHA256 c6332ee934a5701e00f670618e1e151725be421bce4ea8396e30e24f4983a748
reset=AFLNet -K terminates the osslserver child and starts a fresh server process per testcase
request_parser=custom QUIC parser preserves UDP datagram atomicity; input cap 65,507 bytes
response_parser=custom QUIC public-header state parser; encrypted frames are not decoded
coverage=ngtcp2 C/C++, nghttp3 C, OpenSSL 4.1.0 C target compiled with AFLNet 2.56b wrappers
forkserver=target and fuzzer both use AFLNet 2.56b vanilla protocol
coverage_map=AFLNet MAP_SIZE_POW2=18 (262,144 bytes)
certificate=ephemeral self-signed localhost certificate generated at image build time; loopback-only target
container_cpu_quota=2
container_memory_limit=1g
campaign_duration=$DURATION
target=127.0.0.1:$PORT/udp
PARAMS
cleanup() {
  local status=$?
  pkill -TERM -x osslserver 2>/dev/null || true
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
  "$NGTCP2_SERVER" 127.0.0.1 "$PORT" "$NGTCP2_KEY" "$NGTCP2_CERT"
FUZZ_STATUS=$?
set -e
echo "AFLNet exit status: $FUZZ_STATUS"
python3 "$WORKDIR/protocol_smoke.py" --seed "$SEED_DIR/quic-v1-client-initial.bin" \
  --port "$PORT" --passes 3 --output "$OUTDIR/postrun-smoke.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" \
  --output "$OUTDIR/listener-closed.json"
mkdir -p "$OUTDIR/replayable-hangs" "$OUTDIR/replayable-crashes"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/queue" --port "$PORT" \
  --output "$OUTDIR/replay-summary.json"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/replayable-hangs" --port "$PORT" \
  --allow-target-exit --output "$OUTDIR/hangs-replay-summary.json"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/replayable-crashes" --port "$PORT" \
  --allow-target-exit --output "$OUTDIR/crashes-replay-summary.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" \
  --output "$OUTDIR/replay-listener-closed.json"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ ! -f "$OUTDIR/plot_data" ]] || cp "$OUTDIR/plot_data" "$OUTDIR/fuzz-stats.csv"
[[ "$FUZZ_STATUS" -eq 124 || "$FUZZ_STATUS" -eq 130 ]] && exit 0
exit "$FUZZ_STATUS"
