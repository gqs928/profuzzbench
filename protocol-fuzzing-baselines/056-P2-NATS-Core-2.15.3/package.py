#!/usr/bin/env python3
"""Build and verify the standalone #56 NATS benchmark archive."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
DELIVERY = Path(os.environ.get(
    "DELIVERY_DIR",
    str(ROOT.parent / "deliverables" / "12-protocol-baselines-2026-11-03-framework"),
))
ARCHIVE = DELIVERY / "56-NATS-Core-2.15.3.zip"
REQUIRED = (
    "README.md", "ACCEPTANCE.md", "PACKAGE-MANIFEST.md", "source-lock.json",
    "source-checksums.sha256", "aflnet-nats.patch", "aflnet-network-noforkserver.patch",
    "aflnet-network-config-terminator.patch",
    "nats_aflnet.inc", "nats-parser-test.c", "nats_client.py", "seeds-manifest.json",
    "results/nats-fuzz-30m-20261112-networkfix/fuzzer_stats",
    "results/nats-fuzz-30m-20261112-networkfix/fuzzer-deadline.json",
    "results/nats-fuzz-30m-20261112-networkfix/replay-validation/replay-summary.json",
    "results/nats-smoke-post-20261112/protocol-smoke.json",
    "results/nats-smoke-post-20261112/listener-closed.json",
)
RESULTS_TO_PACKAGE = (
    "results/nats-fuzz-30m-20261112-networkfix",
    "results/nats-smoke-post-20261112",
)


def main() -> None:
    missing = [rel for rel in REQUIRED if not (ROOT / rel).is_file()]
    if missing:
        raise RuntimeError(f"required package evidence missing: {missing}")
    DELIVERY.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(ROOT.rglob("*")):
        if (not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc"
                or path.name.endswith(".zip")):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("results/") and not any(
                rel == prefix or rel.startswith(prefix + "/")
                for prefix in RESULTS_TO_PACKAGE):
            continue
        if rel.startswith("results/") and "/" not in rel[len("results/"):]:
            if rel != "results/nats-smoke-post-20261112.server.log":
                continue
        files.append(path)
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(ARCHIVE) as bundle:
        broken = bundle.testzip()
        if broken:
            raise RuntimeError(f"ZIP integrity failure: {broken}")
        names = set(bundle.namelist())
        missing_inside = sorted(set(REQUIRED) - names)
        if missing_inside:
            raise RuntimeError(f"archive missing required paths: {missing_inside}")
        if any(name.endswith("基准化经验库.md") for name in names):
            raise RuntimeError("central experience library must not be duplicated in protocol ZIP")
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    checksum = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")
    checksum.write_text(f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    print(f"PASS: {ARCHIVE.name}, {len(files)} files, {ARCHIVE.stat().st_size} bytes, SHA256 {digest}")


if __name__ == "__main__":
    main()
