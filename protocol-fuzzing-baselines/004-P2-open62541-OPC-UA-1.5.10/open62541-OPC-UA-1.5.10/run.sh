#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
image=open62541-opcua:1.5.10
mode=${1:-formal}
shift || true

if [[ "$mode" == smoke ]]; then
  mkdir -p results/smoke/artifacts
  exec docker run --rm --network none --user "$(id -u):$(id -g)" \
    -v "$PWD:/work" --entrypoint /usr/local/bin/fuzz_tcp_message "$image" \
    -runs=10 -max_len=65536 -timeout=5 -rss_limit_mb=2048 \
    -dict=/work/seeds/fuzz_binary_message_header.dict \
    -artifact_prefix=/work/results/smoke/artifacts/ \
    /work/seeds/opcua-hello.bin "$@"
fi

if [[ "$mode" != formal ]]; then
  echo "usage: $0 [smoke|formal] [additional libFuzzer args...]" >&2
  exit 2
fi

run_dir=results/opcua-30m
mkdir -p "$run_dir/artifacts"
rm -rf "$run_dir/corpus"
cp -a seeds/formal-corpus "$run_dir/corpus"
start=$(date +%s)
set +e
docker run --rm --network none --user "$(id -u):$(id -g)" \
  --memory=3g --cpus=1 -v "$PWD:/work" \
  --entrypoint /usr/local/bin/fuzz_tcp_message "$image" \
  -fork=1 -ignore_timeouts=1 \
  -max_total_time=1800 -max_len=65536 -timeout=5 -rss_limit_mb=2048 \
  -print_final_stats=1 -print_corpus_stats=1 \
  -dict=/work/seeds/fuzz_binary_message_header.dict \
  -artifact_prefix=/work/$run_dir/artifacts/ \
  /work/$run_dir/corpus "$@" 2>&1 | tee "$run_dir/libfuzzer.log"
rc=${PIPESTATUS[0]}
set -e
end=$(date +%s)
printf '{"requested_seconds":1800,"observed_seconds":%s,"exit_code":%s,"image":"%s"}\n' \
  "$((end-start))" "$rc" "$image" > "$run_dir/run.json"
exit "$rc"
