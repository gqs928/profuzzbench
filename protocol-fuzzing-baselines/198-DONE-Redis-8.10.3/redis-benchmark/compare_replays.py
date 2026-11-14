#!/usr/bin/env python3
"""Compare two clean Redis queue replays and their gcov summaries."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_replay(directory: Path) -> dict[str, dict[str, Any]]:
    report = read_json(directory / "replay" / "replay.json")
    return {row["input"]: row for row in report["results"]}


def parse_coverage(path: Path) -> dict[str, dict[str, int | float]]:
    text = path.read_text(encoding="utf-8")
    result: dict[str, dict[str, int | float]] = {}
    for key in ("lines", "branches"):
        match = re.search(rf"{key}:\s*([0-9.]+)%\s*\((\d+) out of (\d+)\)", text)
        if match:
            result[key] = {
                "percent": float(match.group(1)),
                "covered": int(match.group(2)),
                "total": int(match.group(3)),
            }
    return result


def read_core_functions(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as stream:
        return {row["function"]: row for row in csv.DictReader(stream)}


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: compare_replays.py ROUND1 ROUND2 OUTPUT_JSON", file=sys.stderr)
        return 2
    first, second, output = map(Path, sys.argv[1:])
    left, right = read_replay(first), read_replay(second)
    common = sorted(set(left) & set(right))
    mismatches = []
    mismatched_inputs: set[str] = set()
    for name in common:
        a, b = left[name], right[name]
        for key in ("input_sha256", "status", "response_states", "response_types",
                    "response_unparsed_tail_bytes"):
            if a.get(key) != b.get(key):
                mismatched_inputs.add(name)
                mismatches.append({"input": name, "field": key,
                                   "round1": a.get(key), "round2": b.get(key)})
    only_first = sorted(set(left) - set(right))
    only_second = sorted(set(right) - set(left))
    cov1 = parse_coverage(first / "coverage-summary.txt")
    cov2 = parse_coverage(second / "coverage-summary.txt")
    functions1 = read_core_functions(first / "core-functions.csv")
    functions2 = read_core_functions(second / "core-functions.csv")
    function_names = sorted(set(functions1) | set(functions2))
    function_mismatches = [
        {"function": name, "round1": functions1.get(name), "round2": functions2.get(name)}
        for name in function_names if functions1.get(name) != functions2.get(name)
    ]
    report = {
        "round1": str(first),
        "round2": str(second),
        "queue_inputs_round1": len(left),
        "queue_inputs_round2": len(right),
        "matched_queue_inputs": len(common),
        "missing_from_round2": only_first,
        "missing_from_round1": only_second,
        "response_state_sequence_matches": len(common) - len(mismatched_inputs),
        "response_state_mismatches": mismatches,
        "coverage_round1": cov1,
        "coverage_round2": cov2,
        "core_functions_round1": functions1,
        "core_functions_round2": functions2,
        "core_function_mismatches": function_mismatches,
        "overall_line_branch_counts_match": cov1 == cov2,
        "result": "pass" if not mismatches and not only_first and not only_second
                  and not function_mismatches and cov1 == cov2 else "qualified",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"queue response-state matches: {report['response_state_sequence_matches']}/{len(common)}; "
          f"core-function mismatches: {len(function_mismatches)}; "
          f"overall line/branch totals match: {report['overall_line_branch_counts_match']}; "
          f"result={report['result']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
