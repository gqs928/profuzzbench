#!/usr/bin/env python3
"""将 gcovr 的协议核心报告整理为可复查的逐文件覆盖率 CSV。"""

import csv
import json
import pathlib
import sys


report = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
destination = pathlib.Path(sys.argv[2])
rows = []
for item in report.get("files", []):
    source_name = item.get("file", "")
    if not any(name in source_name for name in ("src/lib/radius.c", "src/main/listen.c", "src/main/process.c")):
        continue
    lines = item.get("lines", [])
    line_count = len(lines)
    covered_lines = sum(1 for line in lines if int(line.get("count", 0)) > 0)
    branches = [branch for line in lines for branch in line.get("branches", [])]
    branch_count = len(branches)
    covered_branches = sum(1 for branch in branches if int(branch.get("count", 0)) > 0)
    rows.append(
        (
            source_name,
            line_count,
            covered_lines,
            round(covered_lines / line_count, 6) if line_count else 0.0,
            branch_count,
            covered_branches,
            round(covered_branches / branch_count, 6) if branch_count else 0.0,
        )
    )

destination.parent.mkdir(parents=True, exist_ok=True)
with destination.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.writer(stream)
    writer.writerow(
        (
            "source_file",
            "instrumented_lines",
            "covered_lines",
            "line_coverage",
            "branches",
            "covered_branches",
            "branch_coverage",
        )
    )
    writer.writerows(rows)

if not rows:
    raise SystemExit("未找到 RADIUS 核心处理文件覆盖数据")
required = ("src/lib/radius.c", "src/main/listen.c", "src/main/process.c")
missing = [name for name in required if not any(name in row[0] and row[2] > 0 for row in rows)]
if missing:
    raise SystemExit(f"协议核心文件尚无已覆盖代码行：{', '.join(missing)}")
print(f"已导出 {len(rows)} 个协议核心文件的覆盖率：{destination}")
