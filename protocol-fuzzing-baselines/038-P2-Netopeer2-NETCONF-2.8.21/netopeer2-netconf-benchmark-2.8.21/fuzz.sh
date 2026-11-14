#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OUTDIR=${1:-/results/netconf-30m}
DURATION=${2:-1800}
mkdir -p "$OUTDIR"
if find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then echo "Output directory is not empty: $OUTDIR" >&2; exit 2; fi
"$ROOT/server.sh"
rm -f /tmp/netconf-aflnet-fuzz-active
/opt/aflnet/afl-fuzz -d -n -i "$ROOT/seeds" -x "$ROOT/netconf.dict" -o "$OUTDIR" \
  -N tcp://127.0.0.1/1830 -P NETCONF -E -q 3 -s 3 -R -K -c "$ROOT/server-recover.sh $OUTDIR" \
  -D 10000 -W 100 -w 200000 -m none -t 15000+ \
  "$ROOT/netconf-ready-check" >"$OUTDIR/campaign.log" 2>&1 &
fuzz_pid=$!
start_active=""
trap 'kill -INT "$fuzz_pid" 2>/dev/null || true; wait "$fuzz_pid" 2>/dev/null || true' INT TERM
while kill -0 "$fuzz_pid" 2>/dev/null; do
  if [[ -z "$start_active" && -f "$OUTDIR/fuzzer_stats" ]]; then start_active=$(date +%s); touch /tmp/netconf-aflnet-fuzz-active
  elif [[ -n "$start_active" ]] && (( $(date +%s) - start_active >= DURATION )); then kill -INT "$fuzz_pid" 2>/dev/null || true; break; fi
  sleep 2
done
set +e; wait "$fuzz_pid"; status=$?; set -e
active=0; [[ -z "$start_active" ]] || active=$(( $(date +%s) - start_active ))
printf 'fuzzer_exit_status=%s\nactive_seconds=%s\n' "$status" "$active" | tee "$OUTDIR/run-status.txt"
[[ -f "$OUTDIR/fuzzer_stats" ]] || { cat "$OUTDIR/campaign.log"; exit 1; }
grep -E '^(start_time|last_update|execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' "$OUTDIR/fuzzer_stats" | tee "$OUTDIR/fuzzer-summary.txt"
find "$OUTDIR" -mindepth 1 -type d -exec chmod a+rx {} +
find "$OUTDIR" -type f -exec chmod a+r {} +
