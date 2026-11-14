#!/usr/bin/env bash
set -Eeuo pipefail
IMAGE=${1:-profuzzbench/inn-nntp:2.7.4}
RESULTS=${2:-"$(pwd)/results/validation"}
DURATION=${3:-60s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
USER_ID=$(id -u):$(id -g)
docker image inspect "$IMAGE" >/dev/null
if [[ -e "$RESULTS" ]] && [[ -n $(find "$RESULTS" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Results directory is not empty: $RESULTS" >&2
  exit 2
fi
mkdir -p "$RESULTS"
docker run --rm --network none --user "$USER_ID" --group-add 9 \
  -v "$RESULTS:/results" "$IMAGE" \
  python3 /opt/benchmark/protocol_smoke.py /results/protocol-smoke \
  2>&1 | tee "$RESULTS/protocol-smoke.log"
docker run --rm --network none --user "$USER_ID" --group-add 9 \
  -v "$RESULTS:/results" "$IMAGE" \
  bash /opt/benchmark/run.sh /results/fuzz-smoke "$DURATION" \
  2>&1 | tee "$RESULTS/fuzz-smoke.log"
test -s "$RESULTS/fuzz-smoke/fuzzer_stats"
test -s "$RESULTS/fuzz-smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' "$RESULTS/fuzz-smoke/fuzzer_stats"
docker run --rm --network none --user "$USER_ID" --group-add 9 -i "$IMAGE" dot -Tplain \
  <"$RESULTS/fuzz-smoke/ipsm.dot" >"$RESULTS/fuzz-smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' "$RESULTS/fuzz-smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' "$RESULTS/fuzz-smoke/ipsm.plain"
docker run --rm --network none --user "$USER_ID" --group-add 9 "$IMAGE" \
  cat /opt/benchmark/build-versions.txt >"$RESULTS/build-versions.txt"
(
  cd "$RESULTS"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum >SHA256SUMS
)
echo "PASS: INN 2.7.4 NNTP reference/AFL/gcov smoke, AFLNet execution, and state graph"
