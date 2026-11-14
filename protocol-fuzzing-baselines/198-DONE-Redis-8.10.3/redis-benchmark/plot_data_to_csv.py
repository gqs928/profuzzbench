#!/usr/bin/env python3
"""Convert AFLNet's plot_data samples into a reviewable coverage CSV."""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: plot_data_to_csv.py PLOT_DATA OUTPUT_CSV", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    rows = []
    header: list[str] | None = None
    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            header = [item.strip() for item in line[1:].split(",")]
            continue
        values = [item.strip() for item in line.split(",")]
        if header is None or len(values) != len(header):
            continue
        row = dict(zip(header, values))
        try:
            timestamp = int(row["unix_time"])
        except (KeyError, ValueError):
            continue
        rows.append({
            "unix_time": timestamp,
            "utc_time": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
            "cycles_done": row.get("cycles_done", ""),
            "paths_total": row.get("paths_total", ""),
            "pending_total": row.get("pending_total", ""),
            "bitmap_coverage_pct": row.get("map_size", ""),
            "unique_crashes": row.get("unique_crashes", ""),
            "unique_hangs": row.get("unique_hangs", ""),
            "max_depth": row.get("max_depth", ""),
            "execs_per_sec": row.get("execs_per_sec", ""),
        })
    if not rows:
        print(f"no AFLNet plot samples found in {source}", file=sys.stderr)
        return 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} time-series samples to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
