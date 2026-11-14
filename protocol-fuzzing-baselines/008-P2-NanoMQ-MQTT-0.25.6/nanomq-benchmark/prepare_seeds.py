#!/usr/bin/env python3
"""Write a deterministic MQTT seed corpus for NanoMQ/AFLNet."""

from __future__ import annotations

import sys
from pathlib import Path

from mqtt_packets import business_session, connect


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: prepare_seeds.py SOURCE_DIR OUTPUT_DIR", file=sys.stderr)
        return 2
    source, output = map(Path, sys.argv[1:])
    if not source.is_dir():
        print(f"seed source directory missing: {source}", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        print(f"seed output directory is not empty: {output}", file=sys.stderr)
        return 2

    seeds = {
        "connect-v311": connect(4),
        "business-v311": business_session(4),
        "business-v50": business_session(5, "nanomq-v5"),
        "bad-ping-flags": connect(4) + b"\xc1\x00",
        "truncated-remaining-length": b"\x30\x80",
    }
    for name, data in seeds.items():
        (output / name).write_bytes(data)
    print(f"created {len(seeds)} MQTT seeds in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
