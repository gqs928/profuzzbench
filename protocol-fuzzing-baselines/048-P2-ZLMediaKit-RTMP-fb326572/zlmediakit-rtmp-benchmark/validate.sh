#!/usr/bin/env bash
set -euo pipefail

OUT="$1"
for required in \
  preflight/rtmp-smoke.json \
  campaign/aflnet-out/fuzzer_stats campaign/aflnet-out/ipsm.dot \
  campaign/fuzzer-summary.txt campaign/coverage-summary.txt \
  campaign/proxy-stats.json campaign/server-stop-status.txt \
  replay/queue-replay.json replay/post-replay-smoke.json \
  replay/coverage-summary.txt replay/server-stop-status.txt \
  post-smoke/rtmp-smoke.json post-smoke/coverage-summary.txt \
  post-smoke/server-stop-status.txt; do
  test -s "$OUT/$required" || { echo "Missing completed evidence: $required" >&2; exit 2; }
done
grep -q '"has_connect_result": true' "$OUT/preflight/rtmp-smoke.json"
grep -q '"has_connect_result": true' "$OUT/replay/post-replay-smoke.json"
grep -q '"has_connect_result": true' "$OUT/post-smoke/rtmp-smoke.json"
[[ "$(<"$OUT/campaign/wrapper-exit-code.txt")" == 124 ]]
grep -qx 'graceful=yes' "$OUT/campaign/server-stop-status.txt"
grep -qx 'process_exit_code=0' "$OUT/campaign/server-stop-status.txt"
grep -qx 'graceful=yes' "$OUT/post-smoke/server-stop-status.txt"
grep -qx 'process_exit_code=0' "$OUT/post-smoke/server-stop-status.txt"
test -n "$(find "$OUT/campaign/gcov-data" -type f -name '*.gcda' -print -quit)"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' "$OUT/campaign/aflnet-out/fuzzer_stats"
awk -F: '/^paths_total[[:space:]]*:/ { if ($2+0 > 1) ok=1 } END { exit !ok }' "$OUT/campaign/aflnet-out/fuzzer_stats"
grep -q -- ' -> ' "$OUT/campaign/aflnet-out/ipsm.dot"
grep -Eq 'lines:.*[1-9][0-9]*(\.[0-9]+)?%' "$OUT/campaign/coverage-summary.txt"
python3 - "$OUT/replay/queue-replay.json" <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
if data['queue_files'] < 1 or data['handshake_ok'] < 1:
    raise SystemExit('queue replay did not complete any RTMP handshake')
PY
echo "PASS: RTMP handshake bridge, AFLNet state graph, queue replay, graceful ZLMediaKit shutdown, and native target coverage."
