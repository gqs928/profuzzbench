#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${ROOT}/results/rtsp-30m"
DELIVERABLES="${ROOT}/../deliverables"
ZIP="${DELIVERABLES}/MediaMTX-RTSP-1.21.3.zip"

(cd "${ROOT}/results/preflight-live" && find . -type f ! -name SHA256SUMS \
  ! -path '*/go-build-cache/*' ! -name '.SHA256SUMS.new.*' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)

for required in results/ACCEPTANCE.md source/SHA256SUMS \
  results/build/build-lock.txt results/build/image-id.txt \
  results/preflight-live/SHA256SUMS \
  results/preflight-live/aflnet-60s-final9/aflnet-out/ipsm.dot \
  results/rtsp-30m/aflnet-out/fuzzer_stats results/rtsp-30m/aflnet-out/ipsm.dot \
  results/rtsp-30m/fuzzer-summary.txt results/rtsp-30m/go-coverage.out \
  results/rtsp-30m/go-coverage-summary.txt results/rtsp-30m/post-smoke/rtsp-smoke.json \
  results/rtsp-30m/campaign/stop-status.txt results/rtsp-30m/post-smoke/stop-status.txt \
  results/rtsp-30m/campaign/server.log results/rtsp-30m/post-smoke/server.log \
  results/rtsp-30m/post-smoke/health.txt results/rtsp-30m/external-start-epoch.txt \
  results/rtsp-30m/external-end-epoch.txt results/rtsp-30m/wrapper-exit-code.txt; do
  [[ -s "${ROOT}/${required}" ]] || { echo "Missing completed evidence: ${required}" >&2; exit 2; }
done

[[ "$(<"${OUT}/wrapper-exit-code.txt")" == 124 ]] || { echo 'Formal timer did not expire normally.' >&2; exit 2; }
START="$(awk -F: '/^start_time[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "${OUT}/aflnet-out/fuzzer_stats")"
END="$(awk -F: '/^last_update[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "${OUT}/aflnet-out/fuzzer_stats")"
ELAPSED=$((END - START))
[[ "${ELAPSED}" -ge 1799 ]] || { echo "AFLNet ran only ${ELAPSED}s." >&2; exit 2; }
grep -q '^total:' "${OUT}/go-coverage-summary.txt"
grep -qx 'graceful=yes' "${OUT}/campaign/stop-status.txt"
grep -qx 'process_exit_code=0' "${OUT}/campaign/stop-status.txt"
grep -qx 'graceful=yes' "${OUT}/post-smoke/stop-status.txt"
grep -qx 'process_exit_code=0' "${OUT}/post-smoke/stop-status.txt"
test -n "$(find "${OUT}/go-coverdata" -type f -name 'covcounters.*' -print -quit)"
test -n "$(find "${OUT}/post-smoke/go-coverdata" -type f -name 'covcounters.*' -print -quit)"

cd "${ROOT}"
find results -type f ! -name SHA256SUMS ! -path '*/__pycache__/*' ! -name '*.pyc' \
  ! -path '*/go-build-cache/*' -print0 | sort -z | xargs -0 sha256sum > results/SHA256SUMS
mkdir -p "${DELIVERABLES}"
python3 - "${ROOT}" "${ZIP}" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import sys
root=Path(sys.argv[1]).resolve(); archive=Path(sys.argv[2]).resolve()
files=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.relative_to(root).parts and 'go-build-cache' not in p.parts and p.suffix!='.pyc')
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
    for p in files: z.write(p,Path('mediamtx-benchmark')/p.relative_to(root))
print(f'Packaged {len(files)} files into {archive}')
PY
(cd "${DELIVERABLES}" && sha256sum "$(basename "${ZIP}")" > "$(basename "${ZIP}").sha256")
unzip -tq "${ZIP}"
(cd "${DELIVERABLES}" && sha256sum -c "$(basename "${ZIP}").sha256")
printf 'packaged=%s\nobserved_fuzz_seconds=%s\n' "${ZIP}" "${ELAPSED}"
