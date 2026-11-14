#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/picoquic-fuzz-30m-20261113}
DURATION=${2:-30m}
WORKDIR=${WORKDIR:-/opt/benchmark}
SEED_DIR=${SEED_DIR:-${WORKDIR}/seeds}
FUZZER_BIN=${AFLNET_BIN:-/opt/aflnet/afl-fuzz}
PORT=${PICOQUIC_PORT:-4433}
TARGET=${PICOQUIC_SERVER:-/opt/benchmark/picoquicdemo}
CERT=${PICOQUIC_CERT:-/opt/benchmark/server.crt}
KEY=${PICOQUIC_KEY:-/opt/benchmark/server.key}
HTMLROOT=${PICOQUIC_HTMLROOT:-/opt/benchmark/htmlroot}

if [[ ! -x "$FUZZER_BIN" || ! -x "$TARGET" || ! -d "$SEED_DIR" || ! -d "$HTMLROOT" ]]; then
  echo "AFLNet, instrumented picoquicdemo, HTML root, or QUIC seeds missing" >&2
  exit 2
fi
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$OUTDIR"
python3 "$WORKDIR/validate_seeds.py" "$SEED_DIR" > "$OUTDIR/seeds-validation.json"
export PICOQUIC_PORT="$PORT" AFL_FAST_CAL=1 AFL_NO_UI=1 AFL_MAP_SIZE=262144 AFL_PATH=/opt/aflnet
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
protocol=QUIC v1 over UDP; one Initial datagram is one AFLNet testcase
implementation=picoquic v2026.11.12.36f49b7; official picoquicdemo, no target-source patch
dependencies=PicoTLS e446233b4100ebcdec60901c05bfb7f4cd369c5d and picotest a99858e0c33b97b24cd09ceae729f2be33ec01e1
target_scope=valid Initial processing and first server response; no completed TLS handshake or HTTP/3 exchange
seed_sha256=c6332ee934a5701e00f670618e1e151725be421bce4ea8396e30e24f4983a748
reset=AFLNet -K terminates server and starts a fresh process per testcase
request_parser=QUIC long-header UDP datagram framing; encrypted payload is not decoded
coverage=picoquic and PicoTLS compiled with AFLNet 2.56b; system OpenSSL is not instrumented; map=262144
container_cpu_quota=2
container_memory_limit=1g
campaign_duration=$DURATION
target=127.0.0.1:$PORT/udp
PARAMS
printf '%s\n' "start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUTDIR/run-times.txt"
cleanup() {
  local status=$?
  pkill -TERM -f '^/opt/benchmark/picoquicdemo' 2>/dev/null || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup EXIT

python3 "$WORKDIR/protocol_smoke.py" --seed "$SEED_DIR/quic-v1-client-initial.bin" --port "$PORT" --passes 3 --output "$OUTDIR/preflight-smoke.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" --output "$OUTDIR/preflight-listener-closed.json"
set +e
python3 "$WORKDIR/deadline_wrapper.py" "$DURATION" "$OUTDIR/fuzzer-deadline.json" \
  "$FUZZER_BIN" -d -i "$SEED_DIR" -o "$OUTDIR" \
  -N "udp://127.0.0.1/$PORT" -P QUIC -D 50000 -W 30 -w 50000 \
  -q 3 -s 3 -E -K -m none -t 2000 -- "$TARGET" \
  -p "$PORT" -c "$CERT" -k "$KEY" -w "$HTMLROOT"
FUZZ_STATUS=$?
set -e
printf '%s\n' "end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" "aflnet_exit_status=$FUZZ_STATUS" >> "$OUTDIR/run-times.txt"
echo "AFLNet exit status: $FUZZ_STATUS"
python3 "$WORKDIR/protocol_smoke.py" --seed "$SEED_DIR/quic-v1-client-initial.bin" --port "$PORT" --passes 3 --output "$OUTDIR/postrun-smoke.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" --output "$OUTDIR/listener-closed.json"
if [[ ! -d "$OUTDIR/queue" ]]; then
  echo "AFLNet did not create a queue; refusing to report a successful run or replay" >&2
  exit 1
fi
mkdir -p "$OUTDIR/replayable-hangs" "$OUTDIR/replayable-crashes"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/queue" --port "$PORT" --output "$OUTDIR/replay-summary.json"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/replayable-hangs" --port "$PORT" --allow-target-exit --output "$OUTDIR/hangs-replay-summary.json"
python3 "$WORKDIR/replay_queue.py" "$OUTDIR/replayable-crashes" --port "$PORT" --allow-target-exit --output "$OUTDIR/crashes-replay-summary.json"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" --output "$OUTDIR/replay-listener-closed.json"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ ! -f "$OUTDIR/plot_data" ]] || cp "$OUTDIR/plot_data" "$OUTDIR/fuzz-stats.csv"
[[ "$FUZZ_STATUS" -eq 124 || "$FUZZ_STATUS" -eq 130 ]] && exit 0
exit "$FUZZ_STATUS"
