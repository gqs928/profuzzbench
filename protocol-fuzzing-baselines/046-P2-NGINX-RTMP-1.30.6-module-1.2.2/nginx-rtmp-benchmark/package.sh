#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/results/rtmp-30m"
DELIVERABLES="$ROOT/.."
ZIP="$DELIVERABLES/46-NGINX-RTMP-1.30.6-module-1.2.2.zip"

for required in \
  results/cleanup.txt source-lock.json source/SHA256SUMS \
  results/build/build-lock.txt results/build/image-id.txt \
  results/preflight/aflnet-60s/campaign/aflnet-out/fuzzer_stats \
  results/preflight/aflnet-60s/campaign/aflnet-out/ipsm.dot \
  results/rtmp-30m/campaign/aflnet-out/fuzzer_stats \
  results/rtmp-30m/campaign/aflnet-out/ipsm.dot \
  results/rtmp-30m/campaign/fuzzer-summary.txt \
  results/rtmp-30m/campaign/coverage-summary.txt \
  results/rtmp-30m/replay/queue-replay.json \
  results/rtmp-30m/replay/post-replay-smoke.json \
  results/rtmp-30m/replay/coverage-summary.txt \
  results/rtmp-30m/post-smoke/rtmp-smoke.json \
  results/rtmp-30m/campaign/server-stop-status.txt \
  results/rtmp-30m/post-smoke/server-stop-status.txt \
  results/rtmp-30m/external-start-epoch.txt results/rtmp-30m/external-end-epoch.txt \
  results/rtmp-30m/campaign/wrapper-exit-code.txt; do
  [[ -s "$ROOT/$required" ]] || { echo "Missing completed evidence: $required" >&2; exit 2; }
done
[[ "$(<"$OUT/campaign/wrapper-exit-code.txt")" == 124 ]] || { echo 'Formal campaign timer did not expire normally.' >&2; exit 2; }
START="$(awk -F: '/^start_time[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
END="$(awk -F: '/^last_update[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
ELAPSED=$((END - START))
[[ "$ELAPSED" -ge 1799 ]] || { echo "AFLNet ran only $ELAPSED seconds." >&2; exit 2; }
bash "$ROOT/validate.sh" "$OUT"

QUEUE_FILES="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["queue_files"])' "$OUT/replay/queue-replay.json")"
QUEUE_HANDSHAKES="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["handshake_ok"])' "$OUT/replay/queue-replay.json")"
EXECUTIONS="$(awk -F: '/^execs_done[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
PATHS="$(awk -F: '/^paths_total[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
STABILITY="$(awk -F: '/^stability[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
CRASHES="$(awk -F: '/^unique_crashes[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
HANGS="$(awk -F: '/^unique_hangs[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
cat > "$OUT/ACCEPTANCE.md" <<EOF
# NGINX RTMP benchmark acceptance

- Target: NGINX 1.30.6 stable with upstream nginx-rtmp-module v1.2.2 (commit 23e1873aa62acb58b7881eed2a501f5bf35b82e9); exact source archives and hashes are in source-lock.json.
- Protocol: RTMP v3 over TCP. NGINX listens on 127.0.0.1:1935 and AFLNet reaches it through the C2 handshake bridge on 127.0.0.1:1936.
- Method: AFLNet $ELAPSED active seconds (requested 1,800), RTMP response-state parser, queue replay through fresh RTMP sessions, and GCC/gcovr target coverage.
- AFLNet: $EXECUTIONS executions, $PATHS response paths, stability $STABILITY, $CRASHES unique crashes, $HANGS unique hangs.
- Queue replay: $QUEUE_HANDSHAKES/$QUEUE_FILES queue entries completed the dynamic RTMP handshake.
- Formal target coverage is captured before the separate queue replay under results/rtmp-30m/campaign. Queue replay and its independent coverage are under results/rtmp-30m/replay; the fresh post-smoke is under results/rtmp-30m/post-smoke.
- Container and image cleanup are recorded in results/cleanup.txt.

The AFLNet bitmap describes only the lifecycle helper; target coverage is reported separately from NGINX and the RTMP module through GCC native coverage.
EOF

(cd "$ROOT/results" && find . -type f ! -name SHA256SUMS.txt ! -path '*/__pycache__/*' ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt)
python3 - "$ROOT" "$ZIP" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import sys
root = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
files = sorted(
    p for p in root.rglob("*")
    if p.is_file() and "__pycache__" not in p.relative_to(root).parts and p.suffix != ".pyc"
)
with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=6) as z:
    for p in files:
        z.write(p, Path("nginx-rtmp-benchmark") / p.relative_to(root))
print(f"Packaged {len(files)} files into {archive}")
PY
(cd "$DELIVERABLES" && sha256sum "$(basename "$ZIP")" > "$(basename "$ZIP").sha256")
unzip -tq "$ZIP"
(cd "$DELIVERABLES" && sha256sum -c "$(basename "$ZIP").sha256")
printf 'packaged=%s\nobserved_fuzz_seconds=%s\n' "$ZIP" "$ELAPSED"
