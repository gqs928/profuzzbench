#!/usr/bin/env python3
"""Clear mutable NNTP spool state before a fresh AFLNet server process."""
from pathlib import Path
import shutil
import sys


def clear_contents(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return
    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: reset_spool.py LEAFNODE_PREFIX")
    spool = Path(sys.argv[1]) / "spool"
    spool.mkdir(parents=True, exist_ok=True)
    for child in spool.iterdir():
        if child.name == "message.id" and child.is_dir():
            for bucket in child.iterdir():
                if bucket.is_dir() and not bucket.is_symlink():
                    clear_contents(bucket)
                else:
                    bucket.unlink()
        elif child.is_dir() and not child.is_symlink():
            clear_contents(child)
        else:
            child.unlink()


if __name__ == "__main__":
    main()
