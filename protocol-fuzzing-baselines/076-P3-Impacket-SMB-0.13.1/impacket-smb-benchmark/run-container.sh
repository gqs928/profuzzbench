#!/usr/bin/env bash
set -euo pipefail
out=${1:?usage: run-container.sh RESULTS_DIR DURATION_SECONDS}
duration=${2:?usage: run-container.sh RESULTS_DIR DURATION_SECONDS}
[[ "$duration" =~ ^[0-9]+$ ]] || { echo "duration must be seconds" >&2; exit 2; }
mkdir -p "$out/corpus" "$out/artifacts"
cp -n /opt/benchmark/seeds/* "$out/corpus/" 2>/dev/null || true
printf 'implementation=Impacket 0.13.1\ntarget=SMB2/SMB3 upstream packet and command structures\nbackend=Atheris 3.1.0 with LLVM libFuzzer\nduration_seconds=%s\nworkers=1\n' "$duration" > "$out/run-parameters.txt"
start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf 'start_utc=%s\n' "$start" > "$out/run-times.txt"
set +e
python /opt/benchmark/fuzz_smb.py \
  -max_total_time="$duration" -timeout=10 -rss_limit_mb=3072 \
  -max_len=8192 -print_final_stats=1 \
  -artifact_prefix="$out/artifacts/" "$out/corpus" 2>&1 | tee "$out/run.log"
code=${PIPESTATUS[0]}
set -e
end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf 'end_utc=%s\nexit_code=%s\n' "$end" "$code" >> "$out/run-times.txt"
python /opt/benchmark/summarize_fuzz_log.py "$out/run.log" "$duration" "$code" "$out/corpus" > "$out/metrics.json"
exit "$code"
