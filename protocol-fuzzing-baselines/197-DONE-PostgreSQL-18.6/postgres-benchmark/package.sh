#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
OUTPUT=${1:?usage: package.sh OUTPUT.zip [RESULTS_DIR]}
RESULTS_DIR=${2:-"${PACKAGE_DIR}/results/strict-acceptance"}
mkdir -p "$(dirname "$OUTPUT")"
OUTPUT=$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$OUTPUT")
RESULTS_DIR=$(cd "$RESULTS_DIR" && pwd)
python3 - "$PACKAGE_DIR" "$OUTPUT" "$RESULTS_DIR" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import json
import sys

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
results = Path(sys.argv[3]).resolve()
report = results / "acceptance-report.json"
if not report.is_file():
    raise SystemExit(f"验收报告不存在：{report}")
data = json.loads(report.read_text(encoding="utf-8"))
if not data.get("all_passed"):
    raise SystemExit("验收报告未全部通过，拒绝打包。")
try:
    rel_results = results.relative_to(root)
except ValueError as exc:
    raise SystemExit("结果目录必须位于协议包根目录下。") from exc

prefix = root.name
with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part == ".git" for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] == "results":
            if rel != rel_results and rel_results not in rel.parents:
                continue
            if rel == Path("results"):
                continue
        if path.is_file() and path.resolve() != output:
            archive.write(path, Path(prefix) / rel)

with ZipFile(output) as archive:
    bad = archive.testzip()
    if bad:
        raise SystemExit(f"ZIP 校验失败：{bad}")
print(f"打包完成：{output}（验收证据：{rel_results}）")
PY
sha256sum "$OUTPUT" > "${OUTPUT}.sha256"
