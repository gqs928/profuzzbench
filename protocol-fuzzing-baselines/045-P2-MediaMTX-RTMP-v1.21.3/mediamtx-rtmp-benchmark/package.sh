#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/results/rtmp-30m"
DELIVERABLES="$ROOT/.."
ZIP="$DELIVERABLES/45-MediaMTX-RTMP-v1.21.3.zip"

for required in \
  source-lock.json source/SHA256SUMS results/cleanup.txt \
  results/build/build-lock.txt results/build/image-id.txt \
  results/preflight/aflnet-60s/campaign/aflnet-out/fuzzer_stats \
  results/preflight/aflnet-60s/campaign/aflnet-out/ipsm.dot \
  results/rtmp-30m/campaign/aflnet-out/fuzzer_stats \
  results/rtmp-30m/campaign/aflnet-out/ipsm.dot \
  results/rtmp-30m/campaign/fuzzer-summary.txt \
  results/rtmp-30m/campaign/go-coverage-summary.txt \
  results/rtmp-30m/post-smoke/rtmp-smoke.json \
  results/rtmp-30m/campaign/server-stop-status.txt \
  results/rtmp-30m/post-smoke/server-stop-status.txt \
  results/rtmp-30m/campaign/server.log results/rtmp-30m/post-smoke/server.log \
  results/rtmp-30m/campaign/proxy-stats.json results/rtmp-30m/post-smoke/proxy-stats.json \
  results/rtmp-30m/external-start-epoch.txt results/rtmp-30m/external-end-epoch.txt \
  results/rtmp-30m/campaign/wrapper-exit-code.txt; do
  [[ -s "$ROOT/$required" ]] || { echo "Missing completed evidence: $required" >&2; exit 2; }
done
[[ "$(<"$OUT/campaign/wrapper-exit-code.txt")" == 124 ]] || { echo 'Formal campaign timer did not expire normally.' >&2; exit 2; }
START="$(awk -F: '/^start_time[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
END="$(awk -F: '/^last_update[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "$OUT/campaign/aflnet-out/fuzzer_stats")"
ELAPSED=$((END - START))
[[ "$ELAPSED" -ge 1799 ]] || { echo "AFLNet ran only $ELAPSED seconds." >&2; exit 2; }
grep -qx 'graceful=yes' "$OUT/campaign/server-stop-status.txt"
grep -qx 'process_exit_code=0' "$OUT/campaign/server-stop-status.txt"
grep -qx 'graceful=yes' "$OUT/post-smoke/server-stop-status.txt"
grep -qx 'process_exit_code=0' "$OUT/post-smoke/server-stop-status.txt"

cat > "$ROOT/results/ACCEPTANCE.md" <<EOF
# MediaMTX RTMP v1.21.3 benchmark acceptance

- Target: official MediaMTX v1.21.3 source archive, SHA-256 recorded in source-lock.json.
- Protocol: RTMP v3 over TCP. MediaMTX listens at 127.0.0.1:1935; AFLNet reaches a local handshake bridge at 127.0.0.1:1936.
- Method: AFLNet 0f51f9e response-state campaign, with the profile's RTMP chunk/AMF response parser and a corpus covering connect, createStream, releaseStream, and publish.
- Handshake handling: each testcase includes C0/C1 and a placeholder C2; the bridge obtains server S1 per connection and supplies the protocol-correct C2 echo.
- Formal fuzz active time: $ELAPSED seconds (requested 1800).
- AFLNet states and Go-native coverage are preserved under results/rtmp-30m; preflight and fresh post-campaign smoke are separate.
- Image/container cleanup is recorded in results/cleanup.txt.
EOF

(cd "$ROOT/results" && find . -type f ! -name SHA256SUMS ! -path '*/__pycache__/*' ! -name '*.pyc' ! -path '*/go-build-cache/*' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
mkdir -p "$DELIVERABLES"
python3 - "$ROOT" "$ZIP" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import sys
root = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
files = sorted(
    p for p in root.rglob("*")
    if p.is_file() and "__pycache__" not in p.relative_to(root).parts
    and "go-build-cache" not in p.parts and p.suffix != ".pyc"
)
with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=6) as z:
    for p in files:
        z.write(p, Path("mediamtx-rtmp-benchmark") / p.relative_to(root))
print(f"Packaged {len(files)} files into {archive}")
PY
(cd "$DELIVERABLES" && sha256sum "$(basename "$ZIP")" > "$(basename "$ZIP").sha256")
unzip -tq "$ZIP"
(cd "$DELIVERABLES" && sha256sum -c "$(basename "$ZIP").sha256")
printf 'packaged=%s\nobserved_fuzz_seconds=%s\n' "$ZIP" "$ELAPSED"
