#!/usr/bin/env python3
"""Create and verify the standalone #54 archive without duplicating shared experiences."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path("/opt/benchmark")
DELIVERY = Path("/delivery")
ARCHIVE = DELIVERY / "54-YugabyteDB-Cassandra-Native-2026.1.3.0.zip"


def main() -> None:
    DELIVERY.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path == ARCHIVE:
            continue
        files.append(path)

    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(ARCHIVE) as bundle:
        broken = bundle.testzip()
        if broken:
            raise RuntimeError(f"ZIP integrity check failed at {broken}")
        names = set(bundle.namelist())
        for required in ("README.md", "ACCEPTANCE.md", "source-lock.json",
                         "results/yugabyte-fuzz-30m-20261112/fuzzer_stats",
                         "results/yugabyte-fuzz-30m-20261112/replay-validation/replay-summary.json",
                         "results/yugabyte-smoke-post-20261112/protocol-smoke.json"):
            if required not in names:
                raise RuntimeError(f"package missing required file {required}")
        if any(name.endswith("基准化经验库.md") for name in names):
            raise RuntimeError("central experience library must not be copied into protocol archives")
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256").write_text(
        f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    print(f"PASS: {ARCHIVE.name}, {len(files)} files, {ARCHIVE.stat().st_size} bytes, SHA256 {digest}")


if __name__ == "__main__":
    main()

