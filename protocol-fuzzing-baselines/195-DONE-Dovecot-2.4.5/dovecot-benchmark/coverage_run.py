#!/usr/bin/env python3
"""汇总 gcovr IMAP 源码覆盖和逐输入回放状态。"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

TARGET_PARTS = ("/src/imap-login/", "/src/imap/", "/src/lib-imap/")
KEY_FILES = (
    "imap-login-client.c",
    "imap-commands.c",
    "imap-client.c",
    "cmd-append.c",
    "cmd-fetch.c",
    "cmd-search.c",
    "cmd-select.c",
)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_gcovr(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    files: list[dict[str, Any]] = []
    for entry in document.get("files", []):
        filename = entry.get("file", "")
        normalized = "/" + filename.replace("\\", "/").lstrip("/")
        if any(part in normalized for part in TARGET_PARTS):
            files.append(entry)

    line_total = line_covered = branch_total = branch_covered = 0
    for entry in files:
        for line in entry.get("lines", []):
            line_total += 1
            line_covered += int(line.get("count", 0) > 0)
            for branch in line.get("branches", []):
                branch_total += 1
                branch_covered += int(branch.get("count", 0) > 0)
    summary = {
        "files": len(files),
        "line_total": line_total,
        "line_covered": line_covered,
        "line_percent": round(100.0 * line_covered / line_total, 2) if line_total else 0.0,
        "branch_total": branch_total,
        "branch_covered": branch_covered,
        "branch_percent": round(100.0 * branch_covered / branch_total, 2) if branch_total else 0.0,
        "function_total": 0,
        "function_covered": 0,
    }
    return summary


def read_gcov_functions(path: Path) -> list[dict[str, Any]]:
    """从 gcov 函数摘要日志读取核心函数的行执行比例。"""
    import re

    rows: list[dict[str, Any]] = []
    current_file = ""
    current_function = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("### gcov-source="):
            current_file = line.split("=", 1)[1].strip()
        elif line.startswith("### gcov-source-missing="):
            current_file = line.split("=", 1)[1].strip()
        elif line.startswith("Function '") and "'" in line[len("Function '") :]:
            current_function = line[len("Function '") :].split("'", 1)[0]
        elif current_function and line.startswith("Lines executed:"):
            match = re.search(r"Lines executed:([0-9.]+)%", line)
            if match:
                percent = float(match.group(1))
                rows.append(
                    {
                        "file": current_file,
                        "function": current_function,
                        "lines_executed_percent": percent,
                        "covered": int(percent > 0),
                    }
                )
            current_function = ""
    return rows


def read_replays(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/seed-replay.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        for record in result.get("records", []):
            rows.append(
                {
                    "seed": record.get("seed", ""),
                    "round": record.get("round", ""),
                    "status": record.get("status", ""),
                    "commands": record.get("commands", 0),
                    "timeouts": record.get("timeouts", 0),
                    "response_bytes": record.get("response_bytes", 0),
                    "response_states": record.get("response_states", ""),
                    "server_exit": record.get("server_exit", ""),
                    "elapsed_seconds": record.get("elapsed_seconds", 0),
                    "errors": record.get("errors", ""),
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 IMAP gcov 回放报告")
    parser.add_argument("gcovr_json", type=Path)
    parser.add_argument("replay_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("gcov_function_log", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary = read_gcovr(args.gcovr_json)
    functions = read_gcov_functions(args.gcov_function_log)
    summary["function_total"] = len(functions)
    summary["function_covered"] = sum(row["covered"] for row in functions)
    replay_rows = read_replays(args.replay_root)
    summary.update(
        {
            "replay_inputs": len(replay_rows),
            "replay_timeouts": sum(int(row["timeouts"]) for row in replay_rows),
            "replay_failed": sum(row["status"] != "PASS" for row in replay_rows),
            "replay_server_nonzero": sum(
                str(row["server_exit"]) not in ("0", "") for row in replay_rows
            ),
        }
    )
    function_rows = sorted(functions, key=lambda row: (row["file"], row["function"]))
    key_functions = [
        row for row in function_rows if Path(row["file"]).name in KEY_FILES
    ]
    key_rows = [row for row in key_functions if row["covered"]]
    summary["key_functions_total"] = len(key_functions)
    summary["key_functions_covered"] = len(key_rows)

    write_csv(
        args.output_dir / "coverage-summary.csv",
        [
            "files",
            "line_total",
            "line_covered",
            "line_percent",
            "branch_total",
            "branch_covered",
            "branch_percent",
            "function_total",
            "function_covered",
            "key_functions_total",
            "key_functions_covered",
            "replay_inputs",
            "replay_timeouts",
            "replay_failed",
            "replay_server_nonzero",
        ],
        [summary],
    )
    write_csv(
        args.output_dir / "coverage-functions.csv",
        ["file", "function", "lines_executed_percent", "covered"],
        function_rows,
    )
    write_csv(
        args.output_dir / "key-function-coverage.csv",
        ["file", "function", "lines_executed_percent", "covered"],
        key_rows,
    )
    write_csv(
        args.output_dir / "coverage-replay.csv",
        [
            "seed",
            "round",
            "status",
            "commands",
            "timeouts",
            "response_bytes",
            "response_states",
            "server_exit",
            "elapsed_seconds",
            "errors",
        ],
        replay_rows,
    )
    (args.output_dir / "coverage-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "IMAP 覆盖："
        f"行 {summary['line_covered']}/{summary['line_total']} "
        f"({summary['line_percent']}%)，"
        f"分支 {summary['branch_covered']}/{summary['branch_total']} "
        f"({summary['branch_percent']}%)，"
        f"关键函数 {summary['key_functions_covered']}/{summary['key_functions_total']}"
    )
    return 0 if (
        summary["line_covered"] > 0
        and summary["branch_total"] > 0
        and summary["key_functions_covered"] > 0
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
