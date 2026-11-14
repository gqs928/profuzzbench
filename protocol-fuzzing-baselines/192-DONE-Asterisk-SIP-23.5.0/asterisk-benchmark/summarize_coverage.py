#!/usr/bin/env python3
"""导出 SIP 核心源文件/函数的行与分支覆盖率 CSV 和中文摘要。"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import subprocess
import sys

report_path = pathlib.Path(sys.argv[1])
output_dir = pathlib.Path(sys.argv[2])
source_root = pathlib.Path(sys.argv[3])
report = json.loads(report_path.read_text(encoding="utf-8"))
core_files = []
function_rows = []

for item in report.get("files", []):
    name = item.get("file", "").replace("\\", "/")
    normalized_name = "/" + name.lstrip("/")
    if not (
        "/res/res_pjsip" in normalized_name
        or normalized_name.endswith("/channels/chan_pjsip.c")
    ):
        continue
    # gcovr 会把空行和注释标为非代码行；行覆盖分母只统计可执行代码。
    lines = [
        line for line in item.get("lines", [])
        if not line.get("gcovr/noncode", False)
    ]
    covered_lines = sum(int(line.get("count", 0)) > 0 for line in lines)
    branches = [branch for line in lines for branch in line.get("branches", [])]
    covered_branches = sum(int(branch.get("count", 0)) > 0 for branch in branches)
    core_files.append((
        name,
        len(lines),
        covered_lines,
        covered_lines / len(lines) if lines else 0.0,
        len(branches),
        covered_branches,
        covered_branches / len(branches) if branches else 0.0,
    ))

output_dir.mkdir(parents=True, exist_ok=True)
gcov_log = []
function_pattern = re.compile(r"^function (.+?) called (\d+) returned")
source_line_pattern = re.compile(r"^\s*[0-9#-]+:\s*(\d+):")
for data_file in sorted(source_root.rglob("*.gcda")):
    relative = data_file.relative_to(source_root).as_posix()
    if not (
        relative.startswith("res/res_pjsip")
        or relative == "channels/chan_pjsip.gcda"
    ):
        continue
    source_file = data_file.with_suffix(".c")
    if not source_file.is_file():
        continue
    result = subprocess.run(
        ["gcov", "-b", "-c", "-f", source_file.name],
        cwd=source_file.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    gcov_log.append(f"### {relative}\n{result.stdout}")
    if result.returncode != 0:
        raise SystemExit(f"gcov 函数摘要失败：{relative}\n{result.stdout}")
    details_path = source_file.with_name(source_file.name + ".gcov")
    if not details_path.is_file():
        raise SystemExit(f"gcov 未生成函数明细：{relative}")
    details = details_path.read_text(errors="replace").splitlines()
    for index, line in enumerate(details):
        match = function_pattern.match(line)
        if not match:
            continue
        count = int(match.group(2))
        if count <= 0:
            continue
        start_line = ""
        for following in details[index + 1 : index + 4]:
            line_match = source_line_pattern.match(following)
            if line_match:
                start_line = line_match.group(1)
                break
        function_rows.append((
            source_file.relative_to(source_root).as_posix(),
            match.group(1),
            start_line,
            count,
        ))

(output_dir / "protocol-core-gcov.log").write_text(
    "\n".join(gcov_log), encoding="utf-8"
)

with (output_dir / "protocol-core-coverage.csv").open(
    "w", newline="", encoding="utf-8"
) as stream:
    writer = csv.writer(stream)
    writer.writerow((
        "source_file", "instrumented_lines", "covered_lines", "line_coverage",
        "branches", "covered_branches", "branch_coverage",
    ))
    writer.writerows(core_files)

with (output_dir / "protocol-core-functions.csv").open(
    "w", newline="", encoding="utf-8"
) as stream:
    writer = csv.writer(stream)
    writer.writerow(("source_file", "function", "start_line", "execution_count"))
    writer.writerows(sorted(function_rows))

required = (
    "res/res_pjsip/pjsip_distributor.c",
    "res/res_pjsip_registrar.c",
    "res/res_pjsip_session.c",
    "channels/chan_pjsip.c",
)
missing = [
    required_name for required_name in required
    if not any(required_name in row[0] and row[2] > 0 for row in core_files)
]
if missing:
    raise SystemExit("SIP 核心文件没有实测覆盖行：" + ", ".join(missing))
if not function_rows:
    raise SystemExit("没有导出任何已命中的 SIP 核心函数")

line_total = sum(row[1] for row in core_files)
line_hit = sum(row[2] for row in core_files)
branch_total = sum(row[4] for row in core_files)
branch_hit = sum(row[5] for row in core_files)
with (output_dir / "protocol-core-functions.md").open("w", encoding="utf-8") as stream:
    stream.write("# SIP 核心覆盖函数\n\n")
    stream.write(
        f"核心文件 {len(core_files)} 个，行覆盖 {line_hit}/{line_total}，"
        f"分支覆盖 {branch_hit}/{branch_total}。函数命中清单取自独立 gcov 回放数据。\n\n"
    )
    stream.write("| 源文件 | 函数 | 起始行 | 调用次数 |\n|---|---|---:|---:|\n")
    for source, name, line, count in sorted(function_rows):
        stream.write(f"| `{source}` | `{name}` | {line} | {count} |\n")
print(
    f"已导出 SIP 核心覆盖率：{line_hit}/{line_total} 行、"
    f"{branch_hit}/{branch_total} 分支；命中函数 {len(function_rows)} 个"
)
