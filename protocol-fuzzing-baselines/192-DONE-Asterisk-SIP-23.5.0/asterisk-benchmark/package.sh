#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
OUTPUT=${1:-"$(dirname "${PACKAGE_DIR}")/asterisk-sip-fuzz-benchmark-delivery-2026-10-15.zip"}
EVIDENCE_DIR=${2:-}

python3 - "${PACKAGE_DIR}" "${OUTPUT}" "${EVIDENCE_DIR}" <<'PY'
import pathlib
import sys
import zipfile

root = pathlib.Path(sys.argv[1])
archive = pathlib.Path(sys.argv[2])
evidence = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None
archive.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
	for path in sorted(root.rglob("*")):
		relative = path.relative_to(root)
		if not path.is_file() or "__pycache__" in path.parts or relative.parts[0] == "results":
			continue
		package.write(path, pathlib.Path(root.name) / relative)
	if evidence is not None and evidence.is_dir():
		for path in sorted(evidence.rglob("*")):
			if not path.is_file() or "__pycache__" in path.parts:
				continue
			package.write(path, pathlib.Path(root.name) / "evidence" / path.relative_to(evidence))
PY
sha256sum "${OUTPUT}" > "${OUTPUT}.sha256"
echo "交付包：${OUTPUT}"
cat "${OUTPUT}.sha256"
