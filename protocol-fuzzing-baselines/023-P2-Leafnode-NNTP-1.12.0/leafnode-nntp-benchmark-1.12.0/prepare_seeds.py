#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: prepare_seeds.py INPUT_DIR OUTPUT_DIR")
source, output = map(Path, sys.argv[1:])
output.mkdir(parents=True, exist_ok=True)
for seed in sorted(source.glob("*.txt")):
    lines = [line.strip() for line in seed.read_text(encoding="ascii").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not lines or any("\r" in line or "\n" in line or "\x00" in line for line in lines):
        raise SystemExit(f"invalid seed: {seed}")
    data = ("\r\n".join(lines) + "\r\n").encode("ascii")
    (output / seed.stem).write_bytes(data)
    print(f"{seed.name}: {len(lines)} commands, {len(data)} bytes")
