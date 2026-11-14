#!/usr/bin/env python3
"""Normalize CRLF line endings in UTF-8 text files from source archives."""

from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} SOURCE_DIR", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve(strict=True)
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    normalized = 0
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\r\n" not in data or b"\0" in data:
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            continue

        updated = data.replace(b"\r\n", b"\n")
        if updated != data:
            path.write_bytes(updated)
            normalized += 1

    print(f"Normalized CRLF in {normalized} UTF-8 text files under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
