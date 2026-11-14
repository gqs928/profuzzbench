#!/usr/bin/env python3
"""Create and verify the standalone #55 archive without copying shared lessons."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
DELIVERY = Path(os.environ.get(
    "DELIVERY_DIR",
    ROOT.parent / "deliverables/12-protocol-baselines-2026-11-03-framework",
))
ARCHIVE = DELIVERY / "55-Apache-ZooKeeper-Jute-3.9.7.zip"


def main() -> None:
    DELIVERY.mkdir(parents=True, exist_ok=True)
    files = [p for p in sorted(ROOT.rglob("*"))
             if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(ARCHIVE) as bundle:
        broken = bundle.testzip()
        if broken:
            raise RuntimeError(f"ZIP integrity check failed at {broken}")
        names = set(bundle.namelist())
        for required in ("README.md", "ACCEPTANCE.md", "source-lock.json",
                         "zookeeper-parser-test.c",
                         "results/zookeeper-fuzz-30m-20261112/fuzzer_stats",
                         "results/zookeeper-fuzz-30m-20261112/fuzzer-deadline.json",
                         "results/zookeeper-fuzz-30m-20261112/replay-validation/replay-summary.json",
                         "results/zookeeper-smoke-postformal-20261112/protocol-smoke.json"):
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
