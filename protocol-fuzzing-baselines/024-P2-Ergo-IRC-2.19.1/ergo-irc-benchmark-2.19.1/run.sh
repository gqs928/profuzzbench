#!/usr/bin/env bash
set -Eeuo pipefail
OUTDIR=/results/irc-30m
TIMEOUT=30m
if [[ $# -ge 1 ]]; then OUTDIR=$1; fi
if [[ $# -ge 2 ]]; then TIMEOUT=$2; fi
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Output directory is not empty: $OUTDIR" >&2
  exit 2
fi
mkdir -p "$(dirname "$OUTDIR")"
mkdir -p /tmp/ergo-data/afl
cd /tmp/ergo-data/afl
set +e
AFL_SKIP_BIN_CHECK=1 timeout --signal=INT --kill-after=15s "$TIMEOUT" \
  /opt/aflnet/afl-fuzz -d -n -i /opt/benchmark/in-irc -x /opt/benchmark/irc.dict \
  -o "$OUTDIR" -N tcp://127.0.0.1/6667 -P IRC -E -q 3 -s 3 -R -K \
  -D 1000000 -W 100 -w 100000 -m none -t 15000+ \
  /opt/benchmark/ergo-target.sh run --conf /opt/benchmark/configs/ergo.yaml
status=$?
set -e
echo "AFLNet exit status: $status"
if [[ -f "$OUTDIR/fuzzer_stats" ]]; then
  grep -E '^(start_time|last_update|execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "$OUTDIR/fuzzer_stats" || true
fi
[[ $status -eq 124 ]] && exit 0
exit "$status"
