#!/usr/bin/env python3
"""Require positive line coverage in designated core IRC handlers."""
import html
from pathlib import Path
import re
import sys


def line_coverage_for_source(report: str, source: str):
    """Read one gcovr 4.2 summary row using its exact detail-page href."""
    source_path = source.replace("\\", "/").strip("/")
    expected_href = "index." + source_path.replace("/", "_") + ".html"
    link = re.search(
        r"href\s*=\s*['\"]" + re.escape(expected_href) + r"['\"]",
        report,
        re.IGNORECASE,
    )
    if link is None:
        return None

    starts = list(re.finditer(r"<tr\b", report[:link.start()], re.IGNORECASE))
    if not starts:
        return 0.0
    row_start = starts[-1].start()

    # gcovr 4.2 places a nested table (and nested <tr> elements) inside the
    # coverage-bar cell. Find the matching close for the outer file row rather
    # than stopping at the first inner </tr>.
    depth = 0
    row_end = None
    for tag in re.finditer(r"</?tr\b[^>]*>", report[row_start:], re.IGNORECASE):
        if tag.group(0).startswith("</"):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            row_end = row_start + tag.end()
            break
    if row_end is None or row_end < link.end():
        return 0.0

    row_html = report[row_start:row_end]
    row_text = html.unescape(re.sub(r"<[^>]*>", " ", row_html))
    percentages = re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*%", row_text)
    return float(percentages[0]) if percentages else 0.0


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: coverage_check.py GCOVR_INDEX_HTML CORE_FILES_LIST", file=sys.stderr)
        return 2

    html_path, core_list = map(Path, sys.argv[1:])
    report = html_path.read_text(encoding="utf-8", errors="replace")
    required = [
        line.strip()
        for line in core_list.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    failed = []
    for source in required:
        coverage = line_coverage_for_source(report, source)
        if coverage is None:
            failed.append(f"{source}: absent from gcovr report")
        elif coverage <= 0:
            failed.append(f"{source}: line coverage is zero")
        else:
            print(f"PASS: {source}: line coverage={coverage:.1f}%")

    if failed:
        for error in failed:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: all designated core IRC handlers have executed lines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
