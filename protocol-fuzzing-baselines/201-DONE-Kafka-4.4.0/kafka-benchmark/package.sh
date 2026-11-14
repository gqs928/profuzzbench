#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
OUTPUT=${1:-"$(dirname "${PACKAGE_DIR}")/kafka-kafka-fuzz-benchmark-delivery-2026-10-13.zip"}
RESULTS_DIR=${2:-}

python3 - "${PACKAGE_DIR}" "${OUTPUT}" "${RESULTS_DIR}" <<'PY'
import pathlib
import sys
import zipfile

root = pathlib.Path(sys.argv[1])
archive = pathlib.Path(sys.argv[2])
results = pathlib.Path(sys.argv[3]).resolve() if sys.argv[3] else None
archive.parent.mkdir(parents=True, exist_ok=True)
selected_evidence = {}
if results is not None:
    selected_evidence = {
        "preflight": next((name for name in ("preflight-jacoco-colon", "preflight-jacoco-fix", "preflight")
                           if (results / name).is_dir()), "preflight"),
        "coverage": next((name for name in ("coverage-jacoco-colon", "coverage-jacoco-fix", "coverage")
                          if (results / name).is_dir()), "coverage"),
        "fault-probe": next((name for name in ("fault-probe-jacoco-fixed4", "fault-probe-jacoco-fixed3",
                                                "fault-probe-jacoco-fixed2",
                                                "fault-probe-jacoco-fixed",
                                                "fault-probe-jacoco-colon", "fault-probe-jacoco-fix", "fault-probe")
                             if (results / name).is_dir()), "fault-probe"),
        "build-logs": next((name for name in ("build-logs-jacoco-delivery", "build-logs-jacoco-final",
                                               "build-logs-jacoco-colon", "build-logs")
                            if (results / name).is_dir()), "build-logs"),
    }
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED,
                     compresslevel=6) as package:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root)
        if relative.parts[0] == "results":
            if results is None or (path.resolve() != results and results not in path.resolve().parents):
                continue
            if results is not None and results in path.resolve().parents:
                result_relative = path.resolve().relative_to(results)
                alternatives = {
                    "preflight": ("preflight", "preflight-jacoco-fix", "preflight-jacoco-colon"),
                    "coverage": ("coverage", "coverage-jacoco-fix", "coverage-jacoco-colon"),
                    "fault-probe": ("fault-probe", "fault-probe-jacoco-fix", "fault-probe-jacoco-colon",
                                    "fault-probe-jacoco-fixed", "fault-probe-jacoco-fixed2",
                                    "fault-probe-jacoco-fixed3", "fault-probe-jacoco-fixed4"),
                    "build-logs": ("build-logs", "build-logs-jacoco-colon", "build-logs-jacoco-final",
                                   "build-logs-jacoco-delivery"),
                }
                if result_relative.parts:
                    for category, names in alternatives.items():
                        if result_relative.parts[0] in names and result_relative.parts[0] != selected_evidence[category]:
                            continue_path = True
                            break
                    else:
                        continue_path = False
                    if continue_path:
                        continue
                    if len(result_relative.parts) == 1 and path.suffix == ".log":
                        continue
        if relative.parts[0] == "build-logs":
            continue
        if archive.resolve() == path.resolve():
            continue
        package.write(path, pathlib.Path(root.name) / path.relative_to(root))
PY
sha256sum "${OUTPUT}" > "${OUTPUT}.sha256"
echo "交付包：${OUTPUT}"
cat "${OUTPUT}.sha256"
