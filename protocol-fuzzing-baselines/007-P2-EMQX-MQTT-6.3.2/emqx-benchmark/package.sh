#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${ROOT}/../deliverables"
ARCHIVE="${OUT_DIR}/EMQX-MQTT-6.3.2.zip"

for required in \
  results/build/build-lock.txt \
  results/preflight/service-smoke/service-smoke.json \
  results/preflight/aflnet-60s/aflnet-out/fuzzer_stats \
  results/preflight/state-summary.txt \
  results/mqtt-30m/aflnet-out/fuzzer_stats \
  results/mqtt-30m/aflnet-out/ipsm.dot \
  results/mqtt-30m/fuzzer-summary.txt \
  results/mqtt-30m/external-start-epoch.txt \
  results/mqtt-30m/external-end-epoch.txt \
  results/mqtt-30m/wrapper-exit-code.txt \
  results/mqtt-30m/image-id.txt; do
  if [[ ! -s "${ROOT}/${required}" ]]; then
    echo "Required completed evidence is missing: ${required}" >&2
    exit 2
  fi
done

RUN_SECONDS="$(( $(<"${ROOT}/results/mqtt-30m/external-end-epoch.txt") - $(<"${ROOT}/results/mqtt-30m/external-start-epoch.txt") ))"
if [[ "$(<"${ROOT}/results/mqtt-30m/wrapper-exit-code.txt")" != "124" ]] || [[ "${RUN_SECONDS}" -lt 1799 ]]; then
  echo "The formal campaign did not complete its 1,800-second timeout (elapsed=${RUN_SECONDS}s)" >&2
  exit 2
fi

mkdir -p "${OUT_DIR}"
python3 - "${ROOT}" "${ARCHIVE}" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(sys.argv[1]).resolve()
archive_path = Path(sys.argv[2]).resolve()
files = sorted(
    path for path in root.rglob("*")
    if path.is_file()
    and "__pycache__" not in path.relative_to(root).parts
    and path.suffix != ".pyc"
)

with ZipFile(archive_path, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
    for path in files:
        relative = path.relative_to(root)
        archive.write(path, Path("emqx-benchmark") / relative)

print(f"Packaged {len(files)} files into {archive_path}")
PY

ARCHIVE_NAME="$(basename "${ARCHIVE}")"
(cd "${OUT_DIR}" && sha256sum "${ARCHIVE_NAME}" > "${ARCHIVE_NAME}.sha256")
echo "Package checksum: ${ARCHIVE}.sha256"
