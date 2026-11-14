#!/usr/bin/env python3
"""Convert the reviewed hexadecimal corpus into exact wire-format seed files."""
import pathlib
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: prepare_seeds.py HEX_SEED_DIR OUTPUT_DIR", file=sys.stderr)
        return 2
    source = pathlib.Path(sys.argv[1])
    destination = pathlib.Path(sys.argv[2])
    destination.mkdir(parents=True, exist_ok=True)
    for encoded in sorted(source.glob("seed-*.hex")):
        raw = "".join(encoded.read_text(encoding="ascii").split())
        data = bytes.fromhex(raw)
        if not data:
            raise ValueError(f"empty seed: {encoded.name}")
        (destination / encoded.stem).write_bytes(data)
    if not any(destination.glob("seed-*")):
        raise FileNotFoundError(f"no seed-*.hex files found in {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
