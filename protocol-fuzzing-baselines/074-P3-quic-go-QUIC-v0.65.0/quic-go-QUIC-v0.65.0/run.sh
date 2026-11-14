#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-/results/quic-go-fuzz-30m-20261113}
DURATION=${2:-30m}
mkdir -p "$OUTDIR"
if [[ -e "$OUTDIR/run.log" ]]; then
  echo "result directory already contains a run: $OUTDIR" >&2
  exit 2
fi
RUN_GOCACHE="$OUTDIR/.gocache"
export GOCACHE="$RUN_GOCACHE"
mkdir -p "$GOCACHE"
cat > "$OUTDIR/run-parameters.txt" <<PARAMS
implementation=quic-go v0.65.0
toolchain=Go 1.27.4 official linux/amd64 archive
target=internal/wire.FuzzHeaderParser in internal/wire/header_test.go
fuzz_backend=Go testing native fuzz engine; in-process package target
scope=QUIC v1/v2 long and short header parser; no UDP service, complete handshake, or HTTP/3 exchange
command=go test -run '^$' -fuzz '^FuzzHeaderParser$' -fuzztime=$DURATION -parallel=2 -timeout=45m ./internal/wire
gomaxprocs=2
fuzz_cache=$GOCACHE
fuzz_workers=2
PARAMS
printf '%s\n' "start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUTDIR/run-times.txt"
set +e
go test -run '^$' -fuzz '^FuzzHeaderParser$' -fuzztime="$DURATION" \
  -parallel=2 -timeout=45m ./internal/wire 2>&1 | tee "$OUTDIR/run.log"
GO_STATUS=${PIPESTATUS[0]}
set -e
printf '%s\n' "end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" "go_test_exit_code=$GO_STATUS" >> "$OUTDIR/run-times.txt"
python3 /opt/benchmark/summarize_fuzz_log.py "$OUTDIR/run.log" "$OUTDIR/metrics.json" "$GO_STATUS"
if [[ -d "$GOCACHE/fuzz" ]]; then
  mkdir -p "$OUTDIR/fuzz-corpus-cache"
  cp -a "$GOCACHE/fuzz/." "$OUTDIR/fuzz-corpus-cache/"
fi
TARGET_CORPUS=/opt/quic-go/internal/wire/testdata/fuzz/FuzzHeaderParser
if [[ -d "$TARGET_CORPUS" ]]; then
  mkdir -p "$OUTDIR/failure-corpus/FuzzHeaderParser"
  cp -a "$TARGET_CORPUS/." "$OUTDIR/failure-corpus/FuzzHeaderParser/"
fi
rm -rf "$GOCACHE"
chmod -R a+rX "$OUTDIR"
exit "$GO_STATUS"
