#!/usr/bin/env bash
set -euo pipefail
out=${1:?usage: run-container.sh RESULTS_DIR DURATION_SECONDS}
duration=${2:?usage: run-container.sh RESULTS_DIR DURATION_SECONDS}
[[ "$duration" =~ ^[0-9]+$ ]] || { echo "duration must be seconds" >&2; exit 2; }
mkdir -p "$out/corpus" "$out/artifacts"
cp -n /opt/benchmark/seeds/* "$out/corpus/" 2>/dev/null || true
printf 'target=upstream fuzz-sip (PJSIP 2.17)
engine=LLVM libFuzzer + ASan
duration_seconds=%s
workers=1
' "$duration" > "$out/run-parameters.txt"
start=$(date -u +%Y-%m-%dT%H:%M:%SZ); printf 'start_utc=%s
' "$start" > "$out/run-times.txt"
set +e
ASAN_OPTIONS="${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0}" \
  /opt/benchmark/fuzz-sip -max_total_time="$duration" -timeout=10 \
  -rss_limit_mb=3072 -max_len=5120 -print_final_stats=1 \
  -artifact_prefix="$out/artifacts/" "$out/corpus" 2>&1 | tee "$out/run.log"
code=${PIPESTATUS[0]}
set -e
end=$(date -u +%Y-%m-%dT%H:%M:%SZ); printf 'end_utc=%s
exit_code=%s
' "$end" "$code" >> "$out/run-times.txt"
python3 /opt/benchmark/summarize_fuzz_log.py "$out/run.log" "$duration" "$code" > "$out/metrics.json"
exit "$code"
