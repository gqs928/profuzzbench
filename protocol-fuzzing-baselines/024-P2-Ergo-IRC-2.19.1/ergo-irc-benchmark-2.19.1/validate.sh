#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
IMAGE=profuzzbench/ergo-irc:2.19.1
RESULTS="$ROOT/results/validation"
DURATION=180s
if [[ $# -ge 1 ]]; then RESULTS=$1; fi
if [[ $# -ge 2 ]]; then DURATION=$2; fi
USER_ID=$(id -u):$(id -g)
docker image inspect "$IMAGE" >/dev/null
if [[ -e "$RESULTS" ]] && [[ -n $(find "$RESULTS" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Output directory is not empty: $RESULTS" >&2
  exit 2
fi
mkdir -p "$RESULTS"
docker run --rm --network none --user "$USER_ID" -v "$RESULTS:/results" "$IMAGE" \
  python3 /opt/benchmark/protocol_smoke.py /results/protocol-smoke \
  2>&1 | tee "$RESULTS/protocol-smoke.log"
docker run --rm --network none --user "$USER_ID" -v "$RESULTS:/results" "$IMAGE" \
  bash /opt/benchmark/run.sh /results/fuzz-smoke "$DURATION" \
  2>&1 | tee "$RESULTS/fuzz-smoke.log"
test -s "$RESULTS/fuzz-smoke/fuzzer_stats"
test -s "$RESULTS/fuzz-smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' "$RESULTS/fuzz-smoke/fuzzer_stats"
test "$(find "$RESULTS/fuzz-smoke/queue" -maxdepth 1 -type f -name '*,+state' | wc -l)" -gt 0
docker run --rm --network none --user "$USER_ID" -v "$RESULTS:/results" -i "$IMAGE" \
  dot -Tplain <"$RESULTS/fuzz-smoke/ipsm.dot" >"$RESULTS/fuzz-smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' "$RESULTS/fuzz-smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' "$RESULTS/fuzz-smoke/ipsm.plain"
docker run --rm --network none --user "$USER_ID" -v "$RESULTS:/results" "$IMAGE" \
  python3 /opt/benchmark/coverage_replay.py \
  /results/fuzz-smoke/queue /results/coverage-smoke \
  2>&1 | tee "$RESULTS/coverage-smoke.log"
test -s "$RESULTS/coverage-smoke/coverage.txt"
test -s "$RESULTS/coverage-smoke/go-cover-summary.txt"
docker run --rm --network none --user "$USER_ID" "$IMAGE" \
  cat /opt/benchmark/build-versions.txt >"$RESULTS/build-versions.txt"
(
  cd "$RESULTS"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum >SHA256SUMS
)
echo "PASS: Ergo 2.19.1 IRC differential smoke, AFLNet response-state queue feedback, state graph, and Go coverage replay"
