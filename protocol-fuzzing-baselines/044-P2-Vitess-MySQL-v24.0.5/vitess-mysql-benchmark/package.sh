#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/results/vitess-mysql-30m"
DELIVERABLES="$ROOT/../"
ZIP="$DELIVERABLES/44-Vitess-MySQL-v24.0.5.zip"

for required in \
  source-lock.json source/SHA256SUMS target-version.txt target.env \
  results/vitess-mysql-30m/run-status.txt \
  results/vitess-mysql-30m/fuzzer_stats \
  results/vitess-mysql-30m/ipsm.dot \
  results/vitess-mysql-30m/fuzzer-summary.txt \
  results/vitess-mysql-30m/queue-replay.json \
  results/vitess-mysql-30m/post-run-smoke.json \
  results/vitess-mysql-30m/container-final-state.txt \
  results/vitess-mysql-30m/cleanup.txt \
  results/vitess-preflight-60s/run-status.txt; do
  [[ -s "$ROOT/$required" ]] || { echo "Missing acceptance evidence: $required" >&2; exit 2; }
done
grep -qx 'active_seconds=1801' "$OUT/run-status.txt"
grep -qx 'exit_status=0' "$OUT/run-status.txt"
grep -qx 'stability         : 100.00%' "$OUT/fuzzer-summary.txt"
grep -qx 'unique_crashes    : 0' "$OUT/fuzzer-summary.txt"
grep -qx 'unique_hangs      : 0' "$OUT/fuzzer-summary.txt"
grep -q '"connected": 362' "$OUT/queue-replay.json"
grep -q '"connect_errors": 0' "$OUT/queue-replay.json"
grep -q '"has_result_or_ok": true' "$OUT/post-run-smoke.json"
grep -q '^0 running 0$' "$OUT/container-final-state.txt"

cat > "$ROOT/results/ACCEPTANCE.md" <<EOF
# Vitess MySQL Classic v24.0.5 benchmark acceptance

- Target: official Vitess v24.0.5 vttestserver image, pinned by digest in source-lock.json; runtime reported v24.0.5.
- Protocol path: AFLNet MySQL Classic COM_QUERY through a loopback authentication proxy to vtgate.
- Formal campaign: 1,801 active seconds; AFLNet exit 0; 7,415 executions; 362 paths (354 newly found); stability 100%; 0 variable paths, 0 crashes, 0 hangs; cycles_done=0.
- Feedback: MySQL response-state feedback only. AFL bitmap 0% is not Vitess source coverage.
- Queue replay: 362/362 connected; 0 connect/send errors; all 79 reset-on-read cases had already returned response bytes. The remaining samples ended by peer close or idle timeout. Full packet and error-marker counts are in queue-replay.json.
- Fresh post-run SELECT 1 smoke passed with five MySQL response packets. Container restart count was 0.
- No saved hang candidates required replay triage. The exact Vitess container and image were removed after validation; cleanup evidence is in cleanup.txt.
- Generated replayable-queue and replayable-new-ipsm-paths copies are omitted from the ZIP to avoid duplicating the retained 362-file queue corpus.

See run-status.txt, fuzzer_stats, run-parameters.txt, queue-replay.json, post-run-smoke.json, vttestserver-container.log, and container-final-state.txt for raw evidence. Reusable lessons are maintained centrally in the framework experience library, outside this profile package.
EOF

(cd "$ROOT" && find . -type f ! -name SHA256SUMS.txt ! -path './build/aflnet-src/*' \
  ! -path '*/replayable-queue/*' ! -path '*/replayable-new-ipsm-paths/*' \
  ! -name '.cur_input' -print0 | sort -z | xargs -0 sha256sum > package-manifest.txt)
python3 - "$ROOT" "$ZIP" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import sys
root = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
excluded = {
    Path("build/aflnet-src"),
    Path("results/vitess-mysql-30m/replayable-queue"),
    Path("results/vitess-mysql-30m/replayable-new-ipsm-paths"),
}
files = []
for path in root.rglob("*"):
    if not path.is_file():
        continue
    rel = path.relative_to(root)
    if rel == Path(".cur_input") or "__pycache__" in rel.parts or path.suffix == ".pyc":
        continue
    if any(rel == folder or folder in rel.parents for folder in excluded):
        continue
    files.append(path)
files.sort()
with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=6) as output:
    for path in files:
        output.write(path, Path("vitess-mysql-benchmark") / path.relative_to(root))
print(f"Packaged {len(files)} files into {archive}")
PY
(cd "$DELIVERABLES" && sha256sum "$(basename "$ZIP")" > "$(basename "$ZIP").sha256")
unzip -tq "$ZIP"
(cd "$DELIVERABLES" && sha256sum -c "$(basename "$ZIP").sha256")
printf 'packaged=%s\n' "$ZIP"
