#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
OUTPUT=${1:-"$(dirname "${PACKAGE_DIR}")/freeradius-radius-fuzz-benchmark-delivery-2026-10-12.zip"}

python3 - "${PACKAGE_DIR}" "${OUTPUT}" <<'PY'
import pathlib
import sys
import zipfile

root = pathlib.Path(sys.argv[1])
archive = pathlib.Path(sys.argv[2])
archive.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        package.write(path, pathlib.Path(root.name) / path.relative_to(root))
PY
sha256sum "${OUTPUT}" > "${OUTPUT}.sha256"
echo "交付包：${OUTPUT}"
cat "${OUTPUT}.sha256"
