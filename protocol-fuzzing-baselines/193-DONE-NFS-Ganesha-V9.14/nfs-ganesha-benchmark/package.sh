#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
OUTPUT=${1:-"$ROOT/nfs-ganesha-benchmark.zip"}
python3 - "$ROOT" "$OUTPUT" <<'PY'
import os
import pathlib
import sys
import zipfile

root = pathlib.Path(sys.argv[1]).resolve()
output = pathlib.Path(sys.argv[2]).resolve()
checksum = pathlib.Path(str(output) + ".sha256")
excluded = {".git", "__pycache__"}
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.resolve() in {output, checksum}:
            continue
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts):
            continue
        if relative.parts and relative.parts[0] == "build-logs":
            continue
        if relative.parts and relative.parts[0] == "results":
            # 只把带完整证据清单的验收运行放进交付包，跳过临时调试结果。
            if len(relative.parts) < 2 or not (
                root / "results" / relative.parts[1] / "evidence-manifest.json"
            ).is_file():
                continue
            # 验收结论单独交付；其余运行证据仍随交付包发送。
            if path.name == "验收结论.md":
                continue
        archive.write(path, pathlib.PurePosixPath(root.name, *relative.parts))
print(output)
PY
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
printf '交付包：%s\n校验：%s\n' "$OUTPUT" "$OUTPUT.sha256"
