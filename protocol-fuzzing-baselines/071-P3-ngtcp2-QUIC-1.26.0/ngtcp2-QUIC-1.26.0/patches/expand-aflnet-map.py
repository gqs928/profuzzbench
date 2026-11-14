#!/usr/bin/env python3
"""Expand AFLNet's legacy coverage map for the quiche cargo-afl target."""

from pathlib import Path
import sys

path = Path(sys.argv[1])
data = path.read_bytes()
old = b"#define MAP_SIZE_POW2       16"
new = b"#define MAP_SIZE_POW2       18"
old_count = data.count(old)
new_count = data.count(new)
if old_count == 1 and new_count == 0:
    data = data.replace(old, new, 1)
elif old_count == 0 and new_count == 1:
    pass
else:
    raise SystemExit(
        f"expected exactly one unmodified or expanded map-size definition in {path}"
    )
path.write_bytes(data)
