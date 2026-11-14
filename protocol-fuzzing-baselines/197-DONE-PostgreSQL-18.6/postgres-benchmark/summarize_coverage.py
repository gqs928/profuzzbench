#!/usr/bin/env python3
"""从 gcovr JSON 导出 PostgreSQL 协议核心代码的行、分支及函数覆盖。"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


CORE_FILES = (
    "src/backend/tcop/postgres.c",
    "src/backend/libpq/pqcomm.c",
    "src/backend/libpq/auth.c",
    "src/backend/libpq/pqformat.c",
)
CORE_FUNCTIONS = (
    "PostgresMain",
    "exec_simple_query",
    "exec_parse_message",
    "exec_bind_message",
    "exec_execute_message",
    "pq_getmessage",
    "ClientAuthentication",
)


def main() -> int:
    if len(sys.argv) != 3:
        print("用法：summarize_coverage.py gcovr.json 输出目录", file=sys.stderr)
        return 2
    report_path = Path(sys.argv[1])
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    file_rows: list[dict[str, object]] = []
    function_rows: list[dict[str, object]] = []
    files = report.get("files", [])
    for source in files:
        name = str(source.get("file", "")).replace("\\", "/")
        core_name = next((item for item in CORE_FILES if name.endswith(item)), None)
        if core_name is None:
            continue
        lines = [line for line in source.get("lines", [])
                 if not line.get("gcovr/noncode")]
        branches = [branch for line in lines
                    for branch in line.get("branches", [])]
        covered_lines = sum(int(line.get("count", 0)) > 0 for line in lines)
        covered_branches = sum(int(branch.get("count", 0)) > 0
                               for branch in branches)
        file_rows.append({
            "source_file": core_name,
            "instrumented_lines": len(lines),
            "covered_lines": covered_lines,
            "line_coverage_percent": round(
                covered_lines * 100 / len(lines), 2) if lines else 0,
            "branches": len(branches),
            "covered_branches": covered_branches,
            "branch_coverage_percent": round(
                covered_branches * 100 / len(branches), 2)
                if branches else 0,
        })
        for function in source.get("functions", []):
            function_name = str(function.get("name", ""))
            if function_name in CORE_FUNCTIONS:
                function_coverage = float(
                    function.get("line_coverage_percent", 0))
                function_rows.append({
                    "source_file": core_name,
                    "function": function_name,
                    "instrumented_lines": int(
                        function.get("instrumented_lines", 0)),
                    "line_coverage_percent": function_coverage,
                    "covered": function_coverage > 0,
                })

    with (output / "protocol-core-coverage.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        columns = ["source_file", "instrumented_lines", "covered_lines",
                   "line_coverage_percent", "branches", "covered_branches",
                   "branch_coverage_percent"]
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(file_rows)
    with (output / "core-function-coverage.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        columns = ["source_file", "function", "instrumented_lines",
                   "line_coverage_percent", "covered"]
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(function_rows)

    if not any(row["covered_lines"] > 0
               for row in file_rows
               if row["source_file"] in CORE_FILES[:2]):
        raise SystemExit("协议核心代码（postgres.c/pqcomm.c）没有被覆盖")
    covered_names = {str(row["function"]) for row in function_rows
                     if row["covered"]}
    missing = sorted(set(CORE_FUNCTIONS[:5]) - covered_names)
    if missing:
        raise SystemExit("关键协议处理函数未执行：" + ", ".join(missing))
    (output / "coverage-core-summary.json").write_text(
        json.dumps({
            "files": file_rows,
            "functions": function_rows,
            "required_functions": list(CORE_FUNCTIONS[:5]),
            "required_functions_covered": sorted(
                set(CORE_FUNCTIONS[:5]) & covered_names),
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "core_files": len(file_rows),
        "covered_core_functions": sorted(covered_names),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
