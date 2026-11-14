#!/usr/bin/env bash
set -Eeuo pipefail
OUTDIR=${1:-/results/nntp-30m}
TIMEOUT=${2:-30m}
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Output directory is not empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$(dirname "$OUTDIR")"
export ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0
set +e
timeout --signal=INT --kill-after=10s "$TIMEOUT" \
  /opt/aflnet/afl-fuzz -d -i /opt/benchmark/in-nntp -x /opt/benchmark/nntp.dict \
  -o "$OUTDIR" -N tcp://127.0.0.1/1119 -P NNTP -E -q 3 -s 3 -R -K \
  -D 100000 -W 100 -w 100000 -m none -t 5000+ \
  /opt/inn-afl/bin/nnrpd -D -f -4 127.0.0.1 -p 1119 -n
status=$?
set -e
echo "AFLNet exit status: $status"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ $status -eq 124 ]] && exit 0
exit "$status"
