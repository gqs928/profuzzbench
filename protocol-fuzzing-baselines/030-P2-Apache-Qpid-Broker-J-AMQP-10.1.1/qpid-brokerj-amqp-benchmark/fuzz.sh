#!/usr/bin/env bash
set -Eeuo pipefail
OUTDIR=${1:-/results/amqp-30m}
DURATION=${2:-1800}
mkdir -p "$OUTDIR"
if find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
  echo "Output directory is not empty: $OUTDIR" >&2
  exit 2
fi
rm -f /tmp/amqp-aflnet-target-count /tmp/amqp-aflnet-fuzz-active
/opt/aflnet/afl-fuzz -d -n -i /opt/benchmark/seeds -x /opt/benchmark/amqp.dict \
  -o "$OUTDIR" -N tcp://127.0.0.1/5672 -P AMQP -E -q 3 -s 3 -R -K \
  -D 4000000 -W 1000 -w 500000 -m none -t 10000+ \
  /opt/benchmark/server.sh > "$OUTDIR/campaign.log" 2>&1 &
fuzz_pid=$!
start_active=""
trap 'kill -INT "$fuzz_pid" 2>/dev/null || true; wait "$fuzz_pid" 2>/dev/null || true' INT TERM
while kill -0 "$fuzz_pid" 2>/dev/null; do
  # AFLNet writes fuzzer_stats after the initial seed dry-run has completed.
  if [[ -z "$start_active" && -f "$OUTDIR/fuzzer_stats" ]]; then
    start_active=$(date +%s)
    touch /tmp/amqp-aflnet-fuzz-active
  elif [[ -n "$start_active" ]]; then
    now=$(date +%s)
    if (( now - start_active >= DURATION )); then kill -INT "$fuzz_pid" 2>/dev/null || true; break; fi
  fi
  sleep 2
done
set +e
wait "$fuzz_pid"
status=$?
set -e
printf 'fuzzer_exit_status=%s\nactive_seconds=%s\n' "$status" "${start_active:+$(( $(date +%s) - start_active ))}" | tee "$OUTDIR/run-status.txt"
[[ -f "$OUTDIR/fuzzer_stats" ]] || { cat "$OUTDIR/campaign.log"; exit 1; }
grep -E '^(start_time|last_update|execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' "$OUTDIR/fuzzer_stats" | tee "$OUTDIR/fuzzer-summary.txt"
find "$OUTDIR" -mindepth 1 -type d -exec chmod a+rx {} +
find "$OUTDIR" -type f ! -name broker.log -exec chmod a+r {} +
