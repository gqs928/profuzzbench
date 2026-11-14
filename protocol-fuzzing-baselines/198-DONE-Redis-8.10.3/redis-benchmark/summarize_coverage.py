#!/usr/bin/env python3
"""Extract selected Redis command-handler coverage from GCC gcov output."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
import re


CORE_FUNCTIONS = {
    "authCommand", "helloCommand", "pingCommand", "setCommand", "getCommand",
    "incrCommand", "hsetCommand", "hgetallCommand", "multiCommand",
    "execCommand", "clientCommand",
}
FUNCTION_SOURCES = {
    "authCommand": "acl.c",
    "helloCommand": "server.c",
    "pingCommand": "server.c",
    "setCommand": "t_string.c",
    "getCommand": "t_string.c",
    "incrCommand": "t_string.c",
    "hsetCommand": "t_hash.c",
    "hgetallCommand": "t_hash.c",
    "multiCommand": "multi.c",
    "execCommand": "multi.c",
    "clientCommand": "networking.c",
}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_coverage.py GCOV_OUTPUT OUTPUT_CSV", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    text = source.read_text(encoding="utf-8", errors="replace")
    rows: dict[str, dict[str, str]] = {}
    function = ""
    for line in text.splitlines():
        match = re.match(r"Function ['\"](.+?)['\"]", line)
        if match:
            function = match.group(1)
            continue
        match = re.match(r"Lines executed:\s*([0-9.]+)% of ([0-9]+)", line)
        if match and function in CORE_FUNCTIONS:
            rows[function] = {
                "function": function,
                "source_file": FUNCTION_SOURCES[function],
                "line_coverage_pct": match.group(1),
                "lines_in_function": match.group(2),
            }
    missing = sorted(CORE_FUNCTIONS - set(rows))
    if missing:
        print(f"gcov output did not contain core handlers: {', '.join(missing)}", file=sys.stderr)
        return 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    columns = ["function", "source_file", "line_coverage_pct", "lines_in_function"]
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for name in sorted(rows):
            writer.writerow(rows[name])
    print(f"wrote coverage for {len(rows)} Redis command handlers to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
