#!/usr/bin/env python3
"""Build and verify the standalone #57 FRRouting BGP archive."""
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
ARCHIVE = DELIVERY / "57-FRRouting-BGP-10.7.1.zip"
REQUIRED = (
    "README.md", "ACCEPTANCE.md", "PACKAGE-MANIFEST.md", "source-lock.json",
    "source-checksums.sha256", "Dockerfile", "compose.yaml", "bgpd.conf",
    "aflnet-bgp.patch", "aflnet-network-noforkserver.patch",
    "aflnet-network-config-terminator.patch", "bgp_aflnet.inc", "bgp-parser-test.c",
    "bgp_smoke.py", "seeds-manifest.json",
    "results/frr-bgp-fuzz-30m-20261112/fuzzer_stats",
    "results/frr-bgp-fuzz-30m-20261112/fuzzer-deadline.json",
    "results/frr-bgp-fuzz-30m-20261112/replay-validation/replay-summary.json",
    "results/frr-bgp-smoke-post-20261112/protocol-smoke.json",
    "results/frr-bgp-smoke-post-20261112/listener-closed.json",
)
RESULT_ROOTS = {
    "results/frr-bgp-fuzz-30m-20261112",
    "results/frr-bgp-smoke-post-20261112",
}


def main() -> None:
    checksum_path = ROOT / "source-checksums.sha256"
    source_files = []
    for path in sorted(ROOT.rglob("*")):
        if (not path.is_file() or "__pycache__" in path.parts
                or path.suffix == ".pyc" or path.name.endswith(".zip")):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative == "source-checksums.sha256" or relative.startswith(("results/", "build-logs/")):
            continue
        source_files.append(path)
    checksum_path.write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}\n"
        for path in source_files
    ), encoding="utf-8")
    missing = [rel for rel in REQUIRED if not (ROOT / rel).is_file()]
    if missing:
        raise RuntimeError(f"required package evidence missing: {missing}")
    DELIVERY.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(ROOT.rglob("*")):
        if (not path.is_file() or "__pycache__" in path.parts
                or path.suffix == ".pyc" or path.name.endswith(".zip")):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("results/") and not any(
                relative == root or relative.startswith(root + "/")
                for root in RESULT_ROOTS):
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
        for line in bundle.read("source-checksums.sha256").decode("utf-8").splitlines():
            expected, rel = line.split("  ", 1)
            if hashlib.sha256(bundle.read(rel)).hexdigest() != expected:
                raise RuntimeError(f"source checksum mismatch: {rel}")
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256").write_text(
        f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    print(f"PASS: {ARCHIVE.name}, {len(files)} files, {ARCHIVE.stat().st_size} bytes, SHA256 {digest}")


if __name__ == "__main__":
    main()
