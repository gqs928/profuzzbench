#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${ROOT}/../deliverables/VerneMQ-MQTT-2.2.1.zip"
for required in results/ACCEPTANCE.md results/SHA256SUMS source/SHA256SUMS \
  results/build/build-lock.txt results/build/image-id.txt \
  results/preflight/state-summary.txt \
  results/preflight/aflnet-60s-plugin-bootstrap/aflnet-out/fuzzer_stats \
  results/preflight/aflnet-60s-plugin-bootstrap/plugin-bootstrap.log \
  results/preflight/aflnet-60s-plugin-bootstrap/service-smoke/service-smoke.json \
  results/mqtt-30m/aflnet-out/fuzzer_stats results/mqtt-30m/aflnet-out/ipsm.dot \
  results/mqtt-30m/plugin-bootstrap.log results/mqtt-30m/service-smoke/service-smoke.json \
  results/mqtt-30m/fuzzer-summary.txt results/mqtt-30m/broker-health.txt \
  results/mqtt-30m/external-start-epoch.txt results/mqtt-30m/external-end-epoch.txt \
  results/mqtt-30m/wrapper-exit-code.txt results/mqtt-30m/image-id.txt; do
  [[ -s "${ROOT}/${required}" ]] || { echo "Missing completed evidence: ${required}" >&2; exit 2; }
done
SECONDS_RUN="$(( $(<"${ROOT}/results/mqtt-30m/external-end-epoch.txt") - $(<"${ROOT}/results/mqtt-30m/external-start-epoch.txt") ))"
[[ "$(<"${ROOT}/results/mqtt-30m/wrapper-exit-code.txt")" == 124 && "${SECONDS_RUN}" -ge 1799 ]] || {
  echo "Formal campaign incomplete (${SECONDS_RUN}s)" >&2; exit 2;
}
mkdir -p "$(dirname "${OUT}")"
python3 - "${ROOT}" "${OUT}" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import sys
root=Path(sys.argv[1]).resolve(); archive=Path(sys.argv[2]).resolve()
files=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.relative_to(root).parts and p.suffix!='.pyc')
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
    for p in files: z.write(p,Path('vernemq-benchmark')/p.relative_to(root))
print(f'Packaged {len(files)} files into {archive}')
PY
(cd "$(dirname "${OUT}")" && sha256sum "$(basename "${OUT}")" > "$(basename "${OUT}").sha256")
