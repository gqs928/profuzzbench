#!/usr/bin/env bash
set -Eeuo pipefail

out=${1:?usage: run-container.sh RESULTS_DIR DURATION_SECONDS}
duration=${2:?usage: run-container.sh RESULTS_DIR DURATION_SECONDS}
[[ "$duration" =~ ^[0-9]+$ ]] || { echo "duration must be integer seconds" >&2; exit 2; }
mkdir -p "$out/corpus" "$out/artifacts" "$out/build-evidence"
cp -an /work/seeds/. "$out/corpus/"
cp -an /work/build-evidence/. "$out/build-evidence/"
printf 'implementation=BoringSSL 0.20261105.0\ntarget=upstream TLS server handshake fuzzer\nbackend=LLVM libFuzzer with AddressSanitizer and upstream coverage instrumentation\nduration_seconds=%s\nworkers=1\nexecution_model=in-process TLS state machine (no TCP listener)\n' "$duration" > "$out/run-parameters.txt"
start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf 'start_utc=%s\n' "$start" > "$out/run-times.txt"
set +e
ASAN_OPTIONS="${ASAN_OPTIONS:-detect_leaks=1:abort_on_error=1:symbolize=1}" \
  /build/boringssl/fuzz/server \
  -max_total_time="$duration" -timeout=10 -rss_limit_mb=4096 \
  -max_len=4096 -use_value_profile=1 -print_final_stats=1 \
  -artifact_prefix="$out/artifacts/" "$out/corpus" 2>&1 | tee "$out/run.log"
code=${PIPESTATUS[0]}
set -e
end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf 'end_utc=%s\nexit_code=%s\n' "$end" "$code" >> "$out/run-times.txt"
python3 /work/summarize.py "$out" "$duration" "$code"
exit "$code"
