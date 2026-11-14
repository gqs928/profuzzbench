#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
IMAGE=profuzzbench/ejabberd-xmpp:26.09
RESULTS=${1:-$ROOT/results/validation}
DURATION=${2:-120s}
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
  bash /opt/benchmark/fuzz.sh /results/fuzz-smoke "$DURATION" \
  2>&1 | tee "$RESULTS/fuzz-smoke.log"
test -s "$RESULTS/fuzz-smoke/fuzzer_stats"
test -s "$RESULTS/fuzz-smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
  "$RESULTS/fuzz-smoke/fuzzer_stats"
test "$(find "$RESULTS/fuzz-smoke/queue" -maxdepth 1 -type f -name '*,+state' | wc -l)" -gt 0
docker run --rm --network none --user "$USER_ID" -i "$IMAGE" dot -Tplain \
  <"$RESULTS/fuzz-smoke/ipsm.dot" >"$RESULTS/fuzz-smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' "$RESULTS/fuzz-smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' "$RESULTS/fuzz-smoke/ipsm.plain"
docker run --rm --network none --user "$USER_ID" -v "$RESULTS:/results" "$IMAGE" \
  python3 /opt/benchmark/coverage_replay.py \
  /results/fuzz-smoke/queue /results/coverage-smoke \
  2>&1 | tee "$RESULTS/coverage-smoke.log"
docker run --rm --network none --user "$USER_ID" "$IMAGE" \
  cat /opt/benchmark/build-versions.txt >"$RESULTS/build-versions.txt"
(
  cd "$RESULTS"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum >SHA256SUMS
)
echo "PASS: ejabberd 26.09 XMPP/TLS differential smoke, AFLNet response-state queue feedback, and queue replay"
