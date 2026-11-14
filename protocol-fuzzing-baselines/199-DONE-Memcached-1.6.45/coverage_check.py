#!/usr/bin/env python3
"""Require gcovr to show executed lines in core Memcached protocol handlers."""
from __future__ import annotations

import html.parser
import pathlib
import re
import sys


class TableRows(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[str] = []
        self.current: list[str] | None = None
        self.row_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            if self.current is None:
                self.current = []
            self.row_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.current is not None:
            self.row_depth -= 1
            if self.row_depth == 0:
                self.rows.append(" ".join(self.current))
                self.current = None

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current.append(data.strip())


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: coverage_check.py GCOVR_INDEX_HTML OUTPUT_TXT", file=sys.stderr)
        return 2
    report = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    parser = TableRows()
    parser.feed(report.read_text(encoding="utf-8", errors="replace"))
    required = ("memcached.c", "proto_text.c", "proto_parser.c", "items.c")
    findings = []
    for filename in required:
        matching = [row for row in parser.rows if filename in row]
        if not matching:
            raise SystemExit(f"FAIL: {filename} is missing from {report}")
        row = matching[0]
        percentages = re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*%", row)
        if not percentages or float(percentages[0]) <= 0:
            raise SystemExit(f"FAIL: no executed lines reported for {filename}: {row}")
        findings.append(f"{filename}: line_coverage={percentages[0]}%")
    output.write_text("\n".join(findings) + "\n", encoding="utf-8")
    print("PASS: core protocol/storage handlers have executed lines:")
    print("\n".join(findings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
