#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/results/rtmp-30m"
DELIVERABLES="$ROOT/../deliverables"
ZIP="$DELIVERABLES/48-ZLMediaKit-RTMP-fb326572.zip"

for required in \
  results/cleanup.txt source-lock.json source/SHA256SUMS \
  results/build/build-lock.txt results/build/image-id.txt results/build/BUILD_ACCEPTANCE.txt \
  results/build/zlm-version.txt results/build/zlm-binary.sha256 \
  results/build/aflnet-binaries.sha256 results/build/rtmp-adapter.sha256 \
  results/build/ubuntu-packages.txt results/build/source-checksums.txt \
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
# ZLMediaKit RTMP benchmark acceptance

- Target: ZLMediaKit master source snapshot at commit fb3265725f0880da1f52a3cc6e6eb04bbc327fa3; the GitHub Releases page had no published release; this commit was the current master head on 2026-11-11. Main and submodule digests/revisions are in source-lock.json and source/COMPONENTS.txt.
- Protocol: RTMP v3 over TCP. ZLMediaKit listens on 127.0.0.1:1935 and AFLNet reaches it through the local dynamic C2 handshake bridge at 127.0.0.1:1936.
- Method: AFLNet ran $ELAPSED active seconds with the RTMP response-state parser; AFLNet helper bitmap and ZLMediaKit native GCC coverage are reported separately.
- AFLNet: $EXECUTIONS executions, $PATHS response paths, stability $STABILITY, $CRASHES unique crashes, $HANGS unique hangs.
- Queue replay: $QUEUE_HANDSHAKES/$QUEUE_FILES entries completed the dynamic RTMP handshake; replay and fresh post-smoke coverage are separate from formal campaign coverage.
- Container and target image cleanup are recorded in results/cleanup.txt.
EOF

(cd "$ROOT/results" && find . -type f ! -name SHA256SUMS.txt ! -path '*/__pycache__/*' ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt)
python3 - "$ROOT" "$ZIP" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import sys
root = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
files = sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.relative_to(root).parts and p.suffix != '.pyc')
with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=6) as z:
    for p in files:
        z.write(p, Path('zlmediakit-rtmp-benchmark') / p.relative_to(root))
print(f'Packaged {len(files)} files into {archive}')
PY
(cd "$DELIVERABLES" && sha256sum "$(basename "$ZIP")" > "$(basename "$ZIP").sha256")
unzip -tq "$ZIP"
(cd "$DELIVERABLES" && sha256sum -c "$(basename "$ZIP").sha256")
printf 'packaged=%s\nobserved_fuzz_seconds=%s\n' "$ZIP" "$ELAPSED"
