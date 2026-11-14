#!/usr/bin/env python3
"""Convert readable IRC command lists into exact CRLF wire-format seeds."""
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: prepare_seeds.py SEED_SOURCE_DIR OUTPUT_DIR", file=sys.stderr)
        return 2
    source, output = map(Path, sys.argv[1:])
    output.mkdir(parents=True, exist_ok=True)
    seeds = sorted(source.glob("*.txt"))
    if not seeds:
        print(f"no *.txt seed descriptions in {source}", file=sys.stderr)
        return 2
    for seed in seeds:
        commands = [line.rstrip("\r\n") for line in seed.read_text(encoding="utf-8").splitlines()]
        commands = [line for line in commands if line and not line.startswith("#")]
        if not commands:
            raise SystemExit(f"empty seed description: {seed}")
        if any("\r" in line or "\n" in line or "\x00" in line for line in commands):
            raise SystemExit(f"invalid line break/NUL in {seed}")
        payload = ("\r\n".join(commands) + "\r\n").encode("utf-8")
        (output / seed.stem).write_bytes(payload)
        print(f"seed={seed.stem} commands={len(commands)} bytes={len(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
