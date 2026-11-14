#!/usr/bin/env python3
"""提取 AFLNet 状态、覆盖统计和 variable_paths 排查线索。"""

from __future__ import annotations

import json
import os
import pathlib
import sys


def parse_stats(path: pathlib.Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def main() -> int:
    fuzz_dir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/results/fuzz")
    afl_dir = fuzz_dir / "aflnet"
    stats_path = afl_dir / "fuzzer_stats"
    ipsm_path = afl_dir / "ipsm.dot"
    if not stats_path.is_file() or not ipsm_path.is_file() or ipsm_path.stat().st_size == 0:
        raise SystemExit("缺少 AFLNet 运行统计或非空 ipsm.dot 状态图")

    values = parse_stats(stats_path)
    variable_dir = afl_dir / "queue/.state/variable_behavior"
    variable_cases = []
    if variable_dir.is_dir():
        for path in sorted(variable_dir.iterdir()):
            item = {"name": path.name, "symlink": path.is_symlink()}
            if path.is_symlink():
                item["target"] = os.readlink(path)
            variable_cases.append(item)

    report = {
        "stats_file": str(stats_path),
        "ipsm_dot": str(ipsm_path),
        "queue_paths": values.get("paths_total"),
        "queue_variable_paths": values.get("variable_paths"),
        "queue_stability_percent": values.get("stability"),
        "bitmap_coverage_percent": values.get("bitmap_cvg"),
        "unique_crashes": values.get("unique_crashes"),
        "unique_hangs": values.get("unique_hangs"),
        "executions": values.get("execs_done"),
        "variable_behavior_directory": str(variable_dir),
        "variable_behavior_entries": variable_cases,
        "variable_paths_reported_by_fuzzer": "variable_paths" in values,
    }
    destination = fuzz_dir / "variable-paths.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if "variable_paths" not in values:
        raise RuntimeError("AFLNet fuzzer_stats 没有 variable_paths 统计字段")
    print(
        "AFLNet 状态统计："
        f"queue={report['queue_paths']}，variable_paths={report['queue_variable_paths']}，"
        f"stability={report['queue_stability_percent']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
