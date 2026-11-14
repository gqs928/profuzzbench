#!/usr/bin/env python3
"""把 AFLNet 的文本统计转成便于复核的双列 CSV。"""

import csv
import pathlib
import sys

source = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])
rows = []
for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
    if ":" not in line:
        continue
    key, value = line.split(":", 1)
    rows.append((key.strip(), value.strip()))
with destination.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.writer(stream)
    writer.writerow(("metric", "value"))
    writer.writerows(rows)
