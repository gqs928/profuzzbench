#!/usr/bin/env bash
set -Eeuo pipefail
OUTDIR=${1:-/results/xmpp-30m}
TIMEOUT=${2:-30m}
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Output directory is not empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$(dirname "$OUTDIR")"
set +e
timeout --signal=INT --kill-after=15s "$TIMEOUT" \
  env AFL_SKIP_BIN_CHECK=1 \
  /opt/aflnet/afl-fuzz -d -n -i /opt/benchmark/seeds -x /opt/benchmark/xmpp.dict \
  -o "$OUTDIR" -N tcp://127.0.0.1/5222 -P XMPP -E -q 3 -s 3 -R -K \
  -D 100000 -W 100 -w 100000 -m none -t 5000+ \
  /opt/benchmark/run.sh afl
status=$?
set -e
echo "AFLNet exit status: $status"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(start_time|last_update|execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "$OUTDIR/fuzzer_stats" || true
fi
[[ $status -eq 124 ]] && exit 0
exit "$status"
